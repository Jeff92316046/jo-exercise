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
