import asyncio
import json
import uuid
from typing import List, Dict

from aiomqtt import Client, MqttError
from core.config import settings
from db.db_utils import get_pool

MQTT_USR_NAME = settings.MQTT_USR_NAME
MQTT_USR_PWD = settings.MQTT_USR_PWD
MQTT_BROKER = settings.MQTT_BROKER
MQTT_TOPIC = "TownPass/#"


async def save_message_to_db(channel_id: str, user_id: str, payload: dict):
    pool = await get_pool()
    async with pool.acquire() as conn:
        try:
            await conn.execute(
                """
                INSERT INTO messages (channel_id, uid, payload)
                VALUES ($1, $2, $3);
                """,
                channel_id,
                user_id,
                json.dumps(payload),
            )
            print(f"成功儲存訊息：Channel ID={channel_id}, User ID={user_id}")
        except Exception as e:
            print(f"資料庫儲存錯誤: {e}")


async def get_message_history(channel_id: str) -> List[Dict]:
    pool = await get_pool()
    async with pool.acquire() as conn:
        records = await conn.fetch(
            """
            SELECT uid, payload, timestamp
            FROM messages
            WHERE channel_id = $1
            ORDER BY timestamp ASC
            """,
            channel_id,
        )
        history = []
        for record in records:
            message_payload = json.loads(record["payload"]) if record["payload"] else {}
            history.append({
                "sender": record["uid"],
                "text": message_payload,
                "timestamp": record["timestamp"].isoformat(),
            })
        return history



async def handle_message(message):
    full_topic = str(message.topic)
    payload_str = message.payload.decode("utf-8")

    topic_parts = full_topic.split('/')
    if len(topic_parts) < 2 or topic_parts[0] != "TownPass":
        print(f"無法從主題 '{full_topic}' 提取 Channel ID")
        return

    channel_id_str = topic_parts[1]
    try:
        uuid.UUID(channel_id_str)
    except ValueError:
        print(f"Channel ID '{channel_id_str}' 無法轉換為 UUID")
        return

    try:
        user_msg_dict = json.loads(payload_str)
        if not isinstance(user_msg_dict, dict):
            print("Payload 解析後不是字典格式")
            return
    except json.JSONDecodeError:
        print(f"無法解析訊息載荷為 JSON: {payload_str}")
        return

    if not user_msg_dict:
        print("訊息載荷為空字典")
        return

    user_id = user_msg_dict["sender"]
    message_payload = user_msg_dict["text"]
    print(channel_id_str, user_id, message_payload)
    await save_message_to_db(channel_id_str, user_id, message_payload)


async def mqtt_listener():
    reconnect_interval = 5
    while True:
        try:
            # aiomqtt 的 Client 用法
            async with Client(MQTT_BROKER, username=MQTT_USR_NAME, password=MQTT_USR_PWD) as client:
                await client.subscribe(MQTT_TOPIC)
                print(f"已訂閱主題: {MQTT_TOPIC}")
                async for message in client.messages:
                    asyncio.create_task(handle_message(message))

        except MqttError as e:
            print(f"MQTT 錯誤: {e}, {reconnect_interval}秒後重試連線")
            await asyncio.sleep(reconnect_interval)



