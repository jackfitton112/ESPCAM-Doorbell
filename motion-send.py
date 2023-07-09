import os
import paho.mqtt.client as mqtt
import time
import json
import base64
from dotenv import load_dotenv
import requests

load_dotenv()


# MQTT settings
try:
    MQTT_BROKER = os.getenv("MQTT_BROKER")
    MQTT_PORT = int(os.getenv("MQTT_PORT"))
    MOTION_EYE_URL = os.getenv("MOTION_EYE_URL")
except:
    print("Error getting environment variables")
    exit(1)

# TODO: add optional auth for mqtt
MQTT_KEEPALIVE = 60
MQTT_TOPIC = "home/doorbell/motion"
MQTT_SUB_TOPIC = "home/doorbell/live"
#MQTT_USERNAME = "mqtt"
#MQTT_PASSWORD = "mqtt"

    # Create the MQTT client
client = mqtt.Client()
     
    # Connect to the MQTT broker
client.connect(MQTT_BROKER, MQTT_PORT, MQTT_KEEPALIVE)


# This function gets called when the MQTT client is connected to the broker
def on_connect(client, userdata, flags, rc):
    #if connection successful rc = 0
    if rc == 0:
        #subscribes to the "home/doorbell/live" topic
        client.subscribe(MQTT_SUB_TOPIC)
    else:
        print("Connection failed")

# This function gets called every time a message is received from the MQTT broker on the subscribed topic
def on_message(client, userdata, msg):

    
    
    # Get the message from the MQTT broker
    message = msg.payload.decode("utf-8")

    # If the message is "true" then get the images
    if message == "true":
        # Get the images from the motion eye server
        get_images_http()




# Setup the callbacks for the MQTT client
client.on_connect = on_connect
client.on_message = on_message
     

# Script settings - TODO: move to env / ToF
CAMERA_NAME = "front-door"
IMAGE_DIR_PATH = ""

def get_images():
    # Get the list of images
    images = []
    try:
        dirs = os.listdir(IMAGE_DIR_PATH)

    except:
        return False

    if len(dirs) == 0:
        return False

    # Loop through the files in the directory
    for directory in dirs:

        if directory == ".keep":
            continue

        # Get the list of files in the directory
        files = os.listdir(IMAGE_DIR_PATH + directory)

        # Loop through the files in the directory
        for file in files:
                
                # Get the file path
                file_path = IMAGE_DIR_PATH + directory + "/" + file
                print(file_path)
    
                # Open the file
                with open(file_path, "rb") as image_file:
    
                    # Encode the file as base64
                    encoded_string = base64.b64encode(image_file.read())
    
                    # Add the image to the list
                    images.append(encoded_string)
    
                # Delete the file
                os.remove(file_path)

        os.rmdir(IMAGE_DIR_PATH + directory)

    # Return the list of images
    return images

def send_images(images):
     

    # Loop through the images
    for image in images:
     
        # Create the payload
        payload = json.dumps({"time": time.time(), "camera": CAMERA_NAME, "image": image.decode("utf-8")})
     
        # Publish the payload
        client.publish(MQTT_TOPIC, payload)
     
    # Return true
    return True

def get_images_http():

    #TODO: This is currently blocking, need to make it async

    url = MOTION_EYE_URL + "/picture/1/current/"

    res = requests.get(url)


    if res.status_code == 200:

        encoded_string = base64.b64encode(res.content)

    else:

        return False



    #publish the image
    payload = json.dumps({"time": time.time(), "camera": CAMERA_NAME, "image": encoded_string.decode("utf-8")})

    # Publish the payload
    client.publish(MQTT_TOPIC, payload)

    return True



    



#FIXME: all of this below needs fixing, should be async and not blocking
client.loop_start()

while True:
     
    data = get_images()

    if data != False:
         send_images(data)
         
    time.sleep(1)
          

