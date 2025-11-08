import asyncpg
from datetime import datetime
from typing import AsyncGenerator, Optional, List, Dict, Any
from datetime import datetime, timezone
from core.config import settings


_pool: Optional[asyncpg.Pool] = None


# =========================================================
# 連線池（使用 Settings）
# =========================================================


async def get_pool() -> asyncpg.Pool:
    """
    懶人初始化連線池，確保全程只建一個 pool。
    設定來源同 session.py: 使用 core.config.settings
    """
    global _pool
    if _pool is None:
        _pool = await asyncpg.create_pool(
            user=settings.POSTGRES_USERNAME,
            password=settings.POSTGRES_PASSWORD,
            database=settings.POSTGRES_DB,
            host=settings.POSTGRES_SERVER,
            port=settings.POSTGRES_PORT,
            min_size=1,
            max_size=10,
        )
    return _pool

async def get_db() -> AsyncGenerator[asyncpg.Connection, None]:
    if _pool is None:
        raise RuntimeError(
            "Database pool is not initialized. Call init_db_pool() first."
        )
    async with _pool.acquire() as connection:
        async with connection.transaction():
            yield connection

# =========================================================
# 初始化：若尚未建表則執行 schema.sql
# =========================================================


async def init_db(schema_path: str = "schema.sql"):
    """
    啟動服務時呼叫一次：
    - 若 public.centers 不存在，視為尚未初始化 -> 執行 schema.sql
    - 若已存在，略過（避免重複 CREATE TABLE 失敗）

    🔹連線設定改為沿用 Settings（透過 get_pool）
    """
    pool = await get_pool()
    async with pool.acquire() as conn:
        exists_row = await conn.fetchrow(
            """
            SELECT EXISTS (
                SELECT 1 FROM information_schema.tables
                WHERE table_schema = 'public' AND table_name = 'centers'
            ) AS exists;
            """
        )
        if not exists_row["exists"]:
            # asyncpg.execute 可一次吃多個 statement（有分號也可以）
            await conn.execute("""
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE TYPE sport_type AS ENUM (
    '羽球',
    '籃球',
    '桌球',
    '撞球',
    '壁球',
    '高爾夫'
);

CREATE TYPE event_status AS ENUM (
    'open',
    'full',
    'cancelled',
    'closed'
);

-- 運動中心主表：名稱 + 經緯度
CREATE TABLE centers (
    id SERIAL PRIMARY KEY,
    name VARCHAR(50) NOT NULL UNIQUE,
    latitude  DOUBLE PRECISION NOT NULL,
    longitude DOUBLE PRECISION NOT NULL
);

-- 使用者（發起人 / 參加者）
CREATE TABLE users (
    uid UUID PRIMARY KEY
);

-- 合法「球種 × 場館」清單
-- 只允許 (sport, center_id) 在這裡出現的組合被拿去開團
CREATE TABLE allowed_pairs (
    sport     sport_type NOT NULL,
    center_id INT        NOT NULL,
    PRIMARY KEY (sport, center_id),
    CONSTRAINT fk_allowed_center
        FOREIGN KEY (center_id)
        REFERENCES centers (id)
        ON UPDATE CASCADE
        ON DELETE CASCADE
);

-- 揪團活動
CREATE TABLE events (
    uid UUID PRIMARY KEY DEFAULT uuid_generate_v4(),

    sport sport_type  NOT NULL,
    center_id INT     NOT NULL,
    start_time TIMESTAMPTZ NOT NULL,
    end_time TIMESTAMPTZ NOT NULL,  

    capacity INT NOT NULL
        CHECK (capacity > 1 AND capacity <= 100),

    status event_status NOT NULL DEFAULT 'open',

    organizer_uid UUID NOT NULL,
    created_at   TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    -- 場館關聯
    CONSTRAINT fk_events_center
        FOREIGN KEY (center_id)
        REFERENCES centers (id)
        ON UPDATE CASCADE
        ON DELETE RESTRICT,

    -- 發起人關聯
    CONSTRAINT fk_events_organizer
        FOREIGN KEY (organizer_uid)
        REFERENCES users (uid)
        ON UPDATE CASCADE
        ON DELETE RESTRICT,

    -- (sport, center_id) 必須是 allowed_pairs 中的合法組合
    CONSTRAINT fk_events_allowed_pair
        FOREIGN KEY (sport, center_id)
        REFERENCES allowed_pairs (sport, center_id)
        ON UPDATE CASCADE
        ON DELETE RESTRICT,

    -- 同一發起人、同一開始時間、同一場館、同一球種 只能開一團
    CONSTRAINT uq_event_unique_slot
        UNIQUE (organizer_uid, start_time, center_id, sport)
);

-- 活動參加者表：記錄誰參加了哪個活動
CREATE TABLE participants (
    event_uid UUID NOT NULL,
    user_uid UUID NOT NULL,

    PRIMARY KEY (event_uid, user_uid),

    -- 關聯到 events 表
    CONSTRAINT fk_participants_event
        FOREIGN KEY (event_uid)
        REFERENCES events (uid)
        ON UPDATE CASCADE
        ON DELETE CASCADE,

    -- 關聯到 users 表
    CONSTRAINT fk_participants_user
        FOREIGN KEY (user_uid)
        REFERENCES users (uid)
        ON UPDATE CASCADE
        ON DELETE CASCADE
);

-- 初始資料：centers
INSERT INTO centers (name, latitude, longitude) VALUES
('中正',  25.0385225, 121.5167618),
('內湖',  25.0781635, 121.5746265),
('北投',  25.1164633, 121.5098119),
('大安',  25.0207438, 121.5431821),
('大同',  25.0653758, 121.5136244),
('士林',  25.0894274, 121.5189874),
('萬華',  25.0474624, 121.5042924),
('文山',  24.9970192, 121.55688),
('信義',  25.0317033, 121.5641931),
('中山',  25.0548481, 121.51877);

INSERT INTO allowed_pairs (sport, center_id)
SELECT '羽球', id FROM centers WHERE name IN
('中正','內湖','北投','大安','大同','士林','萬華','文山','信義','中山');

INSERT INTO allowed_pairs (sport, center_id)
SELECT '籃球', id FROM centers WHERE name IN
('中正','內湖','大安','大同','士林','信義');

INSERT INTO allowed_pairs (sport, center_id)
SELECT '桌球', id FROM centers WHERE name IN
('中正','內湖','北投','大安','大同','士林','萬華','文山','信義');

INSERT INTO allowed_pairs (sport, center_id)
SELECT '撞球', id FROM centers WHERE name IN
('內湖','北投','大安','文山');

INSERT INTO allowed_pairs (sport, center_id)
SELECT '壁球', id FROM centers WHERE name IN
('內湖','大安','信義');

INSERT INTO allowed_pairs (sport, center_id)
SELECT '高爾夫', id FROM centers WHERE name IN
('萬華');

CREATE TABLE channels (
    channel_id UUID PRIMARY KEY
        REFERENCES events(uid)
        ON UPDATE CASCADE
        ON DELETE CASCADE,
    channel_name VARCHAR(255) NOT NULL UNIQUE,
    is_active BOOLEAN DEFAULT TRUE
);

CREATE TABLE messages (
    channel_id UUID NOT NULL,
    uid UUID NOT NULL,
    payload JSONB NOT NULL,
    timestamp TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_channel
        FOREIGN KEY (channel_id)
        REFERENCES channels(channel_id)
        ON DELETE CASCADE
);
                               """)


# =========================================================
# 共用小工具
# =========================================================


async def _ensure_user(conn: asyncpg.Connection, user_uid: str):
    await conn.execute(
        "INSERT INTO users (uid) VALUES ($1) ON CONFLICT (uid) DO NOTHING;",
        user_uid,
    )


# =========================================================
# 查詢：球種 / 場館 / 合法組合
# =========================================================


async def get_sports() -> List[str]:
    """
    取得目前有設定合法組合的球類列表。
    回傳範例: ["羽球", "籃球", "桌球", ...]
    """
    pool = await get_pool()
    async with pool.acquire() as conn:
        rows = await conn.fetch(
            """
            SELECT DISTINCT sport
            FROM allowed_pairs
            ORDER BY sport;
            """
        )
        return [r["sport"] for r in rows]


async def get_centers() -> List[Dict[str, Any]]:
    """
    取得所有運動中心。
    回傳為 list[dict]，例:
    [
        {"id": 1, "name": "中正", "latitude": 25.0, "longitude": 121.5},
        ...
    ]
    """
    pool = await get_pool()
    async with pool.acquire() as conn:
        rows = await conn.fetch(
            """
            SELECT id, name, latitude, longitude
            FROM centers
            ORDER BY id;
            """
        )
        return [dict(r) for r in rows]


async def get_allowed_pairs_grouped() -> List[Dict[str, Any]]:
    """
    取得合法 (球種 × 場館) 清單，合併成每種球類對應的場館名稱清單。
    回傳範例：
    [
        {"sport": "羽球",
         "centers": ["中正", "內湖", "北投", "大安", "大同", "士林", "萬華", "文山", "信義", "中山"]},
        {"sport": "籃球", "centers": ["中正", "內湖", "北投"]},
        ...
    ]
    """
    pool = await get_pool()
    async with pool.acquire() as conn:
        rows = await conn.fetch(
            """
            SELECT ap.sport,
                   array_agg(c.name ORDER BY c.name) AS centers
            FROM allowed_pairs ap
            JOIN centers c ON ap.center_id = c.id
            GROUP BY ap.sport
            ORDER BY ap.sport;
            """
        )
        return [{"sport": r["sport"], "centers": list(r["centers"])} for r in rows]


# =========================================================
# 建立揪團
# =========================================================


async def create_event(
    user_uid: str,
    sport: str,
    center_id: int,
    start_time: datetime,
    end_time: datetime, 
    capacity: int,
) -> Dict[str, Any]:
    """
    建立揪團活動：
    - 檢查 (sport, center_id) 是否在 allowed_pairs
    - 自動建立 user（如果不存在）
    - 自動讓發起人加入 participants

    回傳: 新建立活動的資料(dict)
    不合法則丟出 ValueError（給上層 API 轉成 4xx）
    """
    pool = await get_pool()
    async with pool.acquire() as conn:
        async with conn.transaction():
            allowed = await conn.fetchrow(
                """
                SELECT 1 FROM allowed_pairs
                WHERE sport = $1 AND center_id = $2;
                """,
                sport,
                center_id,
            )
            if not allowed:
                raise ValueError("非法的球種與場館組合")

            await _ensure_user(conn, user_uid)

            event = await conn.fetchrow(
                """
                INSERT INTO events (sport, center_id, start_time, end_time, capacity, organizer_uid)
                VALUES ($1, $2, $3, $4, $5, $6)
                RETURNING uid, sport, center_id, start_time, end_time,
                          capacity, status, organizer_uid, created_at;
                """,
                sport,
                center_id,
                start_time,
                end_time,
                capacity,
                user_uid,
            )

            await conn.execute(
                """
                INSERT INTO participants (event_uid, user_uid)
                VALUES ($1, $2)
                ON CONFLICT DO NOTHING;
                """,
                event["uid"],
                user_uid,
            )

            return {"uid": str(event["uid"])}


# =========================================================
# 報名揪團
# =========================================================


async def join_event(user_uid: str, event_uid: str) -> Dict[str, Any]:
    """
    報名揪團：
    回傳:
    {
        "event_uid": str,
        "user_uid": str,
        "status": "joined" / "already_joined" / "full" / "closed" / "not_found"
    }
    """
    pool = await get_pool()
    async with pool.acquire() as conn:
        async with conn.transaction():
            await _ensure_user(conn, user_uid)

            event = await conn.fetchrow(
                """
                SELECT uid, capacity, status
                FROM events
                WHERE uid = $1
                FOR UPDATE;
                """,
                event_uid,
            )
            if event is None:
                return {"event_uid": event_uid, "user_uid": user_uid, "status": "not_found"}

            if event["status"] not in ("open", "full"):
                return {
                    "event_uid": event_uid,
                    "user_uid": user_uid,
                    "status": "closed",
                }

            exists = await conn.fetchrow(
                """
                SELECT 1 FROM participants
                WHERE event_uid = $1 AND user_uid = $2;
                """,
                event_uid,
                user_uid,
            )
            if exists:
                return {
                    "event_uid": event_uid,
                    "user_uid": user_uid,
                    "status": "already_joined",
                }

            cnt_row = await conn.fetchrow(
                """
                SELECT COUNT(*)::int AS cnt
                FROM participants
                WHERE event_uid = $1;
                """,
                event_uid,
            )
            current = cnt_row["cnt"]

            if current >= event["capacity"]:
                if event["status"] != "full":
                    await conn.execute(
                        "UPDATE events SET status = 'full' WHERE uid = $1;",
                        event_uid,
                    )
                return {
                    "event_uid": event_uid,
                    "user_uid": user_uid,
                    "status": "full",
                }

            await conn.execute(
                """
                INSERT INTO participants (event_uid, user_uid)
                VALUES ($1, $2)
                ON CONFLICT DO NOTHING;
                """,
                event_uid,
                user_uid,
            )

            new_cnt_row = await conn.fetchrow(
                """
                SELECT COUNT(*)::int AS cnt
                FROM participants
                WHERE event_uid = $1;
                """,
                event_uid,
            )
            new_cnt = new_cnt_row["cnt"]
            if new_cnt >= event["capacity"]:
                await conn.execute(
                    "UPDATE events SET status = 'full' WHERE uid = $1;",
                    event_uid,
                )

            return {
                "event_uid": event_uid,
                "user_uid": user_uid,
                "status": "joined",
            }


# =========================================================
# 取消揪團（取消活動）
# =========================================================


async def cancel_event(event_uid: str):

    pool = await get_pool()
    async with pool.acquire() as conn:
        async with conn.transaction():
            result = await conn.execute(
                """
                DELETE FROM events
                WHERE uid = $1;
                """,
                event_uid,
            )
            # asyncpg.execute 會回傳類似 "DELETE 1" 或 "DELETE 0"
            deleted = result.startswith("DELETE 1")
            
async def get_user_active_events(user_uid: str) -> List[Dict[str, Any]]:
    """
    取得某個使用者「正在進行」的活動列表。
    規則：
    - 有出現在 participants
    - 活動狀態不是 cancelled / closed
    - end_time 未過期（過期的已在這裡被刪除）
    """
    pool = await get_pool()
    async with pool.acquire() as conn:
        await _cleanup_expired_events(conn)

        rows = await conn.fetch(
            """
            SELECT
                e.uid,
                e.sport,
                e.center_id,
                c.name AS center_name,
                e.start_time,
                e.end_time,
                e.capacity,
                e.status,
                e.organizer_uid
            FROM events e
            JOIN participants p
                ON p.event_uid = e.uid
            LEFT JOIN centers c
                ON c.id = e.center_id
            WHERE
                p.user_uid = $1
                AND e.status NOT IN ('cancelled', 'closed')
            ORDER BY e.start_time;
            """,
            user_uid,
        )
        return [dict(r) for r in rows]


async def get_all_active_events() -> List[Dict[str, Any]]:
    """
    取得所有「正在進行」的活動列表。
    規則：
    - 狀態不是 cancelled / closed
    - end_time 未過期（過期的已在這裡被刪除）
    """
    pool = await get_pool()
    async with pool.acquire() as conn:
        # 先清掉已過期活動
        await _cleanup_expired_events(conn)

        rows = await conn.fetch(
            """
            SELECT
                e.uid,
                e.sport,
                e.center_id,
                c.name AS center_name,
                e.start_time,
                e.end_time,
                e.capacity,
                e.status,
                e.organizer_uid
            FROM events e
            LEFT JOIN centers c
                ON c.id = e.center_id
            WHERE
                e.status NOT IN ('cancelled', 'closed')
            ORDER BY e.start_time;
            """
        )
        return [dict(r) for r in rows]


async def _cleanup_expired_events(conn: asyncpg.Connection):
    """
    刪除已經結束的活動：
    - 條件：end_time <= 現在時間 (NOW)
    - 依賴外鍵 ON DELETE CASCADE，自動清掉 participants / channels / messages
    """
    await conn.execute(
        """
        DELETE FROM events
        WHERE end_time <= NOW();
        """
    )

async def leave_event(user_uid: str, event_uid: str) -> bool:
    """
    使用者退出活動。
    - 如果使用者有參加 -> 刪除 participants 紀錄。
    - 若活動原本為 full 且退出後未滿，改回 open。
    - 若使用者沒參加，回傳 False。
    """
    pool = await get_pool()
    async with pool.acquire() as conn:
        async with conn.transaction():
            # 檢查是否參加
            exists = await conn.fetchval(
                "SELECT 1 FROM participants WHERE user_uid = $1 AND event_uid = $2;",
                user_uid,
                event_uid,
            )
            if not exists:
                return False

            # 刪除參加者
            await conn.execute(
                "DELETE FROM participants WHERE user_uid = $1 AND event_uid = $2;",
                user_uid,
                event_uid,
            )
            # 若原本為 full，改回 open
            await conn.execute(
                """
                UPDATE events
                SET status = 'open'
                WHERE uid = $1 AND status = 'full';
                """,
                event_uid,
            )

            return True
