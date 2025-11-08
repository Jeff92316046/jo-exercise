import paho.mqtt.client as mqtt
import json, sys, time, atexit
from apscheduler.schedulers.background import BackgroundScheduler
import uuid

from core.config import settings

MQTT_USR_NAME = settings.MQTT_USR_NAME
MQTT_USR_PWD = settings.MQTT_USR_PWD
MQTT_BROKER = settings.MQTT_BROKER

CHANNEL_ID = "a1b2c3d4-e5f6-7890-1234-567890abcdef"
USER_ID = "f0e9d8c7-b6a5-4321-fedc-ba9876543210"
USER_MSG = "Hello, this is a test message."

def is_valid_uuid(uuid_str, version=4):
    try:
        val = uuid.UUID(uuid_str, version=version)
        return str(val) == uuid_str
    except ValueError:
        return False

def on_publish(client, userdata, mid, reason_code, properties):
    try:
        userdata.remove(mid)
    except KeyError:
        print("on_publish() is called with a mid not present in unacked_publish")

unacked_publish = set()
mqttc = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
mqttc.on_publish = on_publish

mqttc.user_data_set(unacked_publish)
mqttc.username_pw_set(MQTT_USR_NAME, MQTT_USR_PWD)
mqttc.connect(MQTT_BROKER, 1883)
mqttc.loop_start()

def mqtt_publish(topic, msg, qos=1):
    if not is_valid_uuid(CHANNEL_ID):
        print(f"發佈失敗: CHANNEL_ID '{CHANNEL_ID}' 不是有效的 UUID 格式。")
        return
    
    if USER_ID and not is_valid_uuid(USER_ID):
        print(f"發佈失敗: USER_ID '{USER_ID}' 不是有效的 UUID 格式。")
        return

    msg_info = mqttc.publish(topic, json.dumps(msg), qos=qos)
    unacked_publish.add(msg_info.mid)
    print(f"Message {msg_info.mid} published to topic {topic} with payload: {msg}")

def disconnect_mqtt():
    if mqttc:
        mqttc.loop_stop()
        mqttc.disconnect()
        print("MQTT disconnected.")

atexit.register(disconnect_mqtt)

MsgJson = {}
MsgJson[USER_ID] = USER_MSG
SendMsg = MsgJson

mqtt_publish(f"capstone/{CHANNEL_ID}", SendMsg, qos=1)

while len(unacked_publish) > 0:
    time.sleep(0.1)