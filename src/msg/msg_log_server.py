import paho.mqtt.client as mqtt
import time, json
import asyncio # 引入 asyncio

from core.config import settings

MQTT_USR_NAME = settings.MQTT_USR_NAME
MQTT_USR_PWD = settings.MQTT_USR_PWD
MQTT_BROKER = settings.MQTT_BROKER

import asyncpg
from core.config import settings
from db.init_db import create_all_tables
from typing import AsyncGenerator

_db_pool: asyncpg.Pool | None = None

async def init_db_pool():
    global _db_pool
    _db_pool = await asyncpg.create_pool(
        user=settings.POSTGRES_USERNAME,
        password=settings.POSTGRES_PASSWORD,
        database=settings.POSTGRES_DB,
        host=settings.POSTGRES_SERVER,
        port=settings.POSTGRES_PORT,
        min_size=1,
        max_size=10,
    )
    async with _db_pool.acquire() as conn:
        await conn.execute(
            """
            CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
            """,
        )
        await create_all_tables(conn)


async def get_db() -> AsyncGenerator[asyncpg.Connection, None]:
    if _db_pool is None:
        raise RuntimeError(
            "Database pool is not initialized. Call init_db_pool() first."
        )
    async with _db_pool.acquire() as connection:
        async with connection.transaction():
            yield connection

async def save_message_to_db(channel_id: int, user_id: str, payload: dict):
    async for conn in get_db():
        try:
            await conn.execute(
                """
                INSERT INTO messages (channel_id, user_id, payload)
                VALUES ($1, $2, $3);
                """,
                channel_id,
                user_id,
                json.dumps(payload),
            )
            print(f"成功儲存訊息：Channel ID={channel_id}, User ID={user_id}")
        except asyncpg.exceptions.ForeignKeyViolationError:
            print(f"錯誤：Channel ID {channel_id} 不存在於 channels 表中，無法儲存訊息。")
        except Exception as e:
            print(f"資料庫儲存錯誤: {e}")
        finally:
            break


subToppic = f"TownPass/#"

def on_subcribe(client, userdata, mid, reason_code_list, properties):
    if reason_code_list[0].is_failure:
        print(f"Broker 拒絕了您的訂閱: {reason_code_list[0]}")
    else:
        print(f"Broker 授予的 QoS: {reason_code_list[0].value}")

def on_unsubcribe(client, userdata, mid, reason_code_list, properties):
    if len(reason_code_list) == 0 or not reason_code_list[0].is_failure:
        print("取消訂閱成功 (若在 MQTTv3 收到 SUBACK 則成功)")
    else:
        print(f"Broker 回覆失敗: {reason_code_list[0]}")
    client.disconnect()

def on_connect(client, userdata, flags, reason_code, properties):
    if reason_code.is_failure:
        print(f"連接失敗: {reason_code}。loop_forever() 將重試連接")
        print(f"訂閱主題: {subToppic}")
    else:
        client.subscribe(subToppic)

def on_disconnect(client, userdata, rc):
    print(f"與 Broker 斷開連接，原因代碼: {rc}")


def on_message(client, userdata, message):
    full_topic = message.topic

    payload_str = message.payload.decode('utf-8')

    topic_parts = full_topic.split('/')
    channel_id = None

    channel_id_str = None
    if len(topic_parts) >= 2 and topic_parts[0] == "TownPass":
        channel_id_str = topic_parts[1]
    else:
        print(f"無法從主題 '{full_topic}' 提取 terminal_id，請檢查主題格式。")
        return
    
    user_msg_dict = None
    try:
        user_msg_dict = json.loads(payload_str)
        if not isinstance(user_msg_dict, dict):
            print("Payload 解析後不是字典格式。")
            return
    except json.JSONDecodeError:
        print(f"無法解析訊息載荷為 JSON: {payload_str}")
        return
    
    try:
        channel_id_int = int(channel_id_str)
    except ValueError:
        print(f"Channel ID '{channel_id_str}' 無法轉換為整數。")
        return
    
    # 從字典中提取 user_id 和 message
    # 假設字典中只有一組 {user_id: message}
    if not user_msg_dict:
        print("訊息載荷為空字典。")
        return

    # 取得第一個（也是唯一一個）鍵值對
    user_id = list(user_msg_dict.keys())[0]
    message_payload = user_msg_dict[user_id]
    
    # 執行非同步資料庫儲存操作
    # 為了在同步的 on_message 中執行非同步的 asyncpg 程式碼，我們使用 asyncio.run()
    try:
        asyncio.run(save_message_to_db(channel_id_int, user_id, message_payload))
    except RuntimeError as e:
        if "no running event loop" in str(e):
             print("請確保在執行 mqttc.loop_forever() 之前，事件循環已初始化。")
        else:
            print(f"非同步執行錯誤: {e}")


async def main():
    await init_db_pool()

    mqttc = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
    mqttc.on_connect = on_connect
    mqttc.on_disconnect = on_disconnect
    mqttc.on_message = on_message
    mqttc.on_subscribe = on_subcribe
    mqttc.on_unsubscribe = on_unsubcribe

    mqttc.user_data_set([])
    mqttc.username_pw_set(MQTT_USR_NAME, MQTT_USR_PWD)
    mqttc.connect(MQTT_BROKER)

    mqttc.loop_forever()

if __name__ == "__main__":
    asyncio.run(main())