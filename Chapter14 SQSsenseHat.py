# Raspberry Pi SQS sense hat queue program
# John Allwork
# 27 Jun 22
# reads sqs message and sets sense hat 'fire'
"""

No aws_credentials.py or access or secret needed
REGION_NAME="eu-west-1"  (check your region)
SQS_QUEUE="https://sqs.eu-west-1.amazonaws.com/123456787654321/senseHatQueue"

"""

import time
import datetime
import boto3
import json
import colorsys

from sense_hat import SenseHat

red = (255, 0, 0)
colour = red

sense = SenseHat()
def fire(powerState, colour):
    # pass on/off,
    # colour (RGB)
    if powerState  == "on":
        sense.clear(colour[0], colour[1], colour[2])
    else:
        sense.clear(0, 0, 0)

from botocore.config import Config

# set your region here
my_config = Config(
    region_name = 'eu-west-1',
    signature_version = 'v4',
    retries = {
        'max_attempts': 3,
        'mode': 'standard'
    }
)

sqs = boto3.resource('sqs', config=my_config)
#change 'senseHatQueue' if queue has a different name
queue = sqs.get_queue_by_name(QueueName='senseHatQueue')

def get_sqs_msg(queue):
    json_msg = ""
    for message in queue.receive_messages():
        json_msg = json.loads(message.body)
        print("***** SQS message ***")
        print(json_msg)
        message.delete()
    return json_msg

#hsv_to_rgb
def hsv2rgb(hsv):
    # receives hsv - which is sent by Alexa
    #green = "{'hue': 120.0, 'saturation': 1.0, 'brightness': 1.0}"
    h = hsv["hue"]
    h=h/360
    s = hsv["saturation"]
    v = hsv["brightness"]
    r, g, b =  colorsys.hsv_to_rgb(h, s, v)    # 0-1 f.p. values
    colour=[0,0,0]
    colour[0] = int(r*255)
    colour[1] = int(g*255)
    colour[2] = int(b*255)
    return (colour)

def main():
    print("Can't start a fire without a spark")
    powerState = "on"
    colour = red
    # colour = (255,0,0)
    fire(powerState, colour)
    while True:
        fire(powerState, colour)
        time.sleep(1)
        msg_text = get_sqs_msg(queue)
        if "namespace" in msg_text:
           print(msg_text["namespace"])
                      
           if msg_text["namespace"] == "Alexa.PowerController":              
               colour = red
               if msg_text["value"] == "ON":
                   print("Power on")
                   powerState = "on"
                   colour = red
                   fire(powerState, colour)
               else:
                   print("Power off")
                   powerState = "off"
                   colour = (0,0,0)
                   fire(powerState, colour)

           if msg_text["namespace"] == "Alexa.ColorController":
               powerState = "on"
               colour = msg_text["value"]
               print (colour)
               colour = hsv2rgb(colour)
               fire(powerState, colour)   

        else:
           # no new message, send last command
           fire(powerState, colour)

if __name__ == '__main__':
    main()
