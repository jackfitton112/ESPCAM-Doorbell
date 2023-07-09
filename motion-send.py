import os, time, json, base64, asyncio, aiohttp
import paho.mqtt.client as mqtt
from dotenv import load_dotenv

def loadFromEnv():

    #load the .env file using the dotenv library
    if load_dotenv == False:
        assert False, "Error loading .env file"

    #declare the global variables to be used in the script
    global MQTT_BROKER
    global MQTT_PORT
    global MOTION_EYE_URL
    global MQTT_USER
    global MQTT_PASS

    MQTT_BROKER = os.getenv("MQTT_BROKER") 
    MQTT_PORT = int(os.getenv("MQTT_PORT")) #Must be type cast to int for lib
    MOTION_EYE_URL = os.getenv("MOTION_EYE_URL")
    MQTT_USER = os.getenv("MQTT_USER")
    MQTT_PASS = os.getenv("MQTT_PASS")

    #check if the variables are set
    if (MQTT_BROKER == None or MQTT_PORT == None or MOTION_EYE_URL == None or 
        MQTT_USER == None or MQTT_PASS == None):

        assert False, "Error loading .env variables"

    return True

#load the variables from the .env file
loadFromEnv()

# Global variables, don't change these values
CAMERA_NAME = "front-door"
IMAGE_DIR_PATH = ""
MQTT_KEEPALIVE = 60
MQTT_TOPIC = "home/doorbell/motion"
MQTT_SUB_TOPIC = "home/doorbell/live"


# Create the MQTT client from the paho library 
# (https://github.com/eclipse/paho.mqtt.python)

MQTT_CLEAN_SESSION = True
MQTT_TRANSPORT = "tcp"
MQTT_RECONNECT_ON_NETWORK_LOSS = True
MQTT_RECONNECT_DELAY_SECS = 2
MQTT_PROTOCOL = mqtt.MQTTv5

# Create the MQTT client from the paho library using the settings above

client = mqtt.Client(clean_session=MQTT_CLEAN_SESSION, 
                     transport=MQTT_TRANSPORT, 
                     protocol=MQTT_PROTOCOL,
                     reconnect_delay=MQTT_RECONNECT_DELAY_SECS,
                     reconnect_delay_max=60,
                     reconnect_on_failure=MQTT_RECONNECT_ON_NETWORK_LOSS
                     )


     
# Connect to the MQTT broker using the settings above
client.connect(MQTT_BROKER, MQTT_PORT, MQTT_KEEPALIVE)


# This function gets called when the MQTT client is connected to the broker
async def on_connect(client, userdata, flags, rc):
    #if connection successful rc = 0
    if rc == 0:
        #subscribes to the "home/doorbell/live" topic
        client.subscribe(MQTT_SUB_TOPIC)
    else:
        #TODO: add logging / error handling
        # should attempt to reconnect 3 times then exit
        print("Connection failed")

# This function gets called every time a message is received from the MQTT broker on the subscribed topic
async def on_message(client, userdata, msg):

    # Get the message from the MQTT broker
    message = msg.payload.decode("utf-8")

    # If the message is "true" then get the images
    if message == "true":
        # Get the images from the motion eye server
        await get_images_http()

    else:
        # Return false as only interested in "true" messages
        # doesnt require a return but added for clarity
        return False




# Setup the callbacks for the MQTT client
client.on_connect = on_connect
client.on_message = on_message


# This is a function to capture the images from the motion eye server and return them as a base64 string
# it either returns a list of images or false if there are no images
def get_images() -> list / bool:
    # Get the list of images
    images = []

    # Check if the directory exists where the images are stored
    if os.path.isdir(IMAGE_DIR_PATH):
        # images are stored in sub directories, get the list of sub directories
        directories = os.listdir(IMAGE_DIR_PATH)
    else:
        assert False, "Error: IMAGE_DIR_PATH Directory does not exist"


    # if the directory is empty or only contains the .keep file then return false
    if len(directories) == 0 or (len(directories) == 1 and directories[0] == ".keep"):
        return False
    else:
        #remove the .keep file from the list
        directories.remove(".keep")



    # Loop through the files in the directory
    for directory in directories:

        #check the directory is not empty
        if len(os.listdir(IMAGE_DIR_PATH + directory)) == 0:
            continue

        # Get the list of images in the directory
        images = os.listdir(IMAGE_DIR_PATH + directory)

        # Loop through the files in the directory
        for image in images:
                
                #check file is an image
                if not (image.endswith(".jpg") or image.endswith(".png") or image.endswith(".jpeg")):
                    continue
                
                # Get the file path
                file_path = IMAGE_DIR_PATH + directory + "/" + image
                

                # Open the file and encode it as a base64 string
                with open(file_path, "rb") as image_file:
    
                    # Encode the file as base64
                    encoded_string = base64.b64encode(image_file.read())
    
                    # Add the image to the list
                    images.append(encoded_string)
    
                # Delete the file
                os.remove(file_path)

        # Delete the directory
        os.rmdir(IMAGE_DIR_PATH + directory)

    # Return the list of images as a base64 string
    return images


#This function sends the images to the MQTT broker as a json payload
def send_images(images: list) -> bool:
     
     # Check if the images are a list
    if not isinstance(images, list):
        #should never happen but added for safety
        assert False, "Error: Images must be a list" 

    # Loop through the images
    for image in images:
     
        # Create the payload
        payload = json.dumps({"time": time.time(), "camera": CAMERA_NAME, "image": image.decode("utf-8")})
     
        # Publish the payload
        client.publish(MQTT_TOPIC, payload, qos=2)
     
    # Return true
    return True

# This function gets the images directly
# from the motion eye server and sends them to the MQTT broker
# this is used when `live` is requested
async def get_images_http() -> bool:

    #TODO: This is currently blocking, need to make it async

    url = MOTION_EYE_URL + "/picture/1/current/"

    res = await aiohttp.get(url)


    if res.status_code == 200:

        encoded_string = base64.b64encode(res.content)

    else:
        # either the url is wrong or the server is down
        assert False, "Error: Could not get images from motion eye server, check the url"



    #publish the image to the mqtt broker on the "home/doorbell/motion" topic
    payload = json.dumps({"time": time.time(), "camera": CAMERA_NAME, "image": encoded_string.decode("utf-8")})

    # Publish the payload
    client.publish(MQTT_TOPIC, payload)

    return True

async def main() -> None:

    # Connect to the MQTT broker
    client.connect(MQTT_BROKER, MQTT_PORT, MQTT_KEEPALIVE)

    # Start the MQTT client loop
    client.loop_start()

    # Run the loop forever
    while True:
        #check if images are available
        images = get_images()

        if images:
            #send the images to the MQTT broker
            await send_images(images)
        else:
            #wait 1 second
            await asyncio.sleep(1)


# Run the main function
asyncio.run(main())
          

