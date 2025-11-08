import paho.mqtt.client as mqtt
import json

from core.config import settings

MQTT_USR_NAME = settings.MQTT_USR_NAME
MQTT_USR_PWD = settings.MQTT_USR_PWD
MQTT_BROKER = settings.MQTT_BROKER

CHANNEL_ID = ""#聊天室ID

subToppic = f"TownPass/{CHANNEL_ID}"

def on_subcribe(client, userdata, mid, reason_code_list, properties):
    if reason_code_list[0].is_failure:
        print(f"Broker 拒絕了您的訂閱: {reason_code_list[0]}")
    else:
        print(f"Broker 授予的 QoS: {reason_code_list[0].value}")
        
    #初次訂閱後查詢資料庫並同步歷史聊天紀錄

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
    if len(topic_parts) >= 2 and topic_parts[0] == "TownPass":
        channel_id = topic_parts[1]
    else:
        print(f"無法從主題 '{full_topic}' 提取 channel_id，請檢查主題格式。")
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
        print("訊息字典為空。")
        return

    # 提取 user_id 和 message
    user_id = list(user_msg_dict.keys())[0]
    chat_message = user_msg_dict[user_id]

    
    # 您的資料儲存部分
    # database insert (user_id, channel_id, time)
    
    
    # 這裡將是您準備傳送到前端的資料
    
    message_data = {
        "channel_id": channel_id,
        "user_id": user_id,
        "message": chat_message
    }
    
    print("--- 接收到新的聊天訊息 ---")
    print(f"聊天室 ID: {message_data['channel_id']}")
    print(f"用戶 ID: {message_data['user_id']}")
    print(f"訊息內容: {message_data['message']}")
    print("----------------------------")


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