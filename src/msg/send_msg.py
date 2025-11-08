import paho.mqtt.client as mqtt
import json, sys, time, atexit
from apscheduler.schedulers.background import BackgroundScheduler

from core.config import settings

MQTT_USR_NAME = settings.MQTT_USR_NAME
MQTT_USR_PWD = settings.MQTT_USR_PWD
MQTT_BROKER = settings.MQTT_BROKER

CHANNEL_ID = ""#聊天室ID
USER_ID = ""#UID
USER_MSG = ""#使用者訊息

def on_publish(client, userdata, mid, reason_code, properties):
    # reason_code and properties will only be present in MQTTv5. It's always unset in MQTTv3
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
    # Publish a message to the given topic with the given JSON payload
    msg_info = mqttc.publish(topic, json.dumps(msg), qos=qos)
    unacked_publish.add(msg_info.mid)
    print(f"Message {msg_info.mid} published")

def disconnect_mqtt():
    if mqttc:
        mqttc.loop_stop()
        mqttc.disconnect()
        print("MQTT disconnected.")

atexit.register(disconnect_mqtt)

MsgJson = {}
SendMsg = MsgJson.update({USER_ID: USER_MSG}) 

mqtt_publish(f"capstone/{CHANNEL_ID}", SendMsg, qos=1)