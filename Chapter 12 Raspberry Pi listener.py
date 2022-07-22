#!/usr/bin/python3

import sys
import signal
import time
import json
from time import sleep
from random import randint

from AWSIoTPythonSDK.MQTTLib import AWSIoTMQTTClient

createMQTTClient = AWSIoTMQTTClient("MyThing")
createMQTTClient.configureEndpoint('abcedf12345-ats.iot.us-east-1.amazonaws.com', 443)

# Check these certificate names
createMQTTClient.configureCredentials("/home/pi/MyThing/certs/AmazonRootCA1.pem", "/home/pi/MyThing/certs/MyThing-private.pem.key", "/home/pi/MyThing/certs/MyThing-certificate.pem.crt")

createMQTTClient.configureOfflinePublishQueueing(-1)  # Infinite offline Publish queueing
createMQTTClient.configureDrainingFrequency(2)  # Draining: 2 Hz
createMQTTClient.configureConnectDisconnectTimeout(10)  # 10 sec
createMQTTClient.configureMQTTOperationTimeout(5)  # 5 sec

createMQTTClient.connect()
print("Connected")

def unsubscribe_topics():
    """Unbsubscribes from AWS IoT topics before exiting
    """
    print("Unsubscribing")

    topics = [
        '/myPi'
    ]

    for topic in topics:
        createMQTTClient.unsubscribe(topic)

# Interrupt Handler useful to break out of the script
def interrupt_handler(signum, frame):
    unsubscribe_topics()
    sys.exit("Exited and unsubscribed")

# Custom MQTT message callbacks
def driveCallback(client, userdata, message):
    print(f"Received {message.payload} from {message.topic}")
    payload = json.loads(message.payload)
    command = payload['directive']
    print(f"Processing command: {command}")
    
    if command == "hello":
          print("hello")
    else:
        print("Command not found")

# Subscribe to topics
createMQTTClient.subscribe("/myPi", 1, driveCallback)
print("Listening on /myPi")

while True:
    signal.signal(signal.SIGINT, interrupt_handler)
    time.sleep(1)

unsubscribe_topics()
