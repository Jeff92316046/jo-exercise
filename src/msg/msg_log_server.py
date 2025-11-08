import paho.mqtt.client as mqtt
import time, json
import asyncio
import uuid

from core.config import settings

MQTT_USR_NAME = settings.MQTT_USR_NAME
MQTT_USR_PWD = settings.MQTT_USR_PWD
MQTT_BROKER = settings.MQTT_BROKER

import asyncpg
from core.config import settings
from typing import AsyncGenerator
from db.db_utils import get_db

async def save_message_to_db(channel_id: str, user_id: str, payload: dict):
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

    channel_id_str = None
    if len(topic_parts) >= 2 and topic_parts[0] == "TownPass":
        channel_id_str = topic_parts[1]
    else:
        print(f"無法從主題 '{full_topic}' 提取 Channel ID，請檢查主題格式。")
        return

    try:
        uuid.UUID(channel_id_str)
    except ValueError:
        print(f"Channel ID '{channel_id_str}' 無法轉換為有效的 UUID 格式。")
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
    
    if not user_msg_dict:
        print("訊息載荷為空字典。")
        return

    user_id = list(user_msg_dict.keys())[0]
    message_payload = user_msg_dict[user_id]
    
    try:
        asyncio.run(save_message_to_db(channel_id_str, user_id, message_payload))
    except RuntimeError as e:
        if "no running event loop" in str(e):
             print("請確保在執行 mqttc.loop_forever() 之前，事件循環已初始化。")
        else:
            print(f"非同步執行錯誤: {e}")

async def get_message_history(channel_id: str, limit: int = 100):
    async for conn in get_db():
        try:
            records = await conn.fetch(
                """
                SELECT user_id, payload, created_at
                FROM messages
                WHERE channel_id = $1
                ORDER BY created_at DESC
                LIMIT $2;
                """,
                channel_id,
                limit,
            )
            
            history = []
            for record in records:
                message_payload = json.loads(record["payload"]) if record["payload"] else {}
                
                history.append(
                    {
                        "user_id": record["user_id"],
                        "message_content": message_payload, 
                        "timestamp": record["created_at"].isoformat(),
                    }
                )
            
            return history
        except Exception as e:
            print(f"資料庫檢索錯誤: {e}")
            return []
        finally:
            break

def mqtt_init():
    mqttc = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
    mqttc.on_connect = on_connect
    mqttc.on_disconnect = on_disconnect
    mqttc.on_message = on_message
    mqttc.on_subscribe = on_subcribe
    mqttc.on_unsubscribe = on_unsubcribe

    mqttc.user_data_set([])
    mqttc.username_pw_set(MQTT_USR_NAME, MQTT_USR_PWD)
    mqttc.connect(MQTT_BROKER)

    mqttc.loop_start()
    return mqttc