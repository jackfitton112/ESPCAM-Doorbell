
import paho.mqtt.client as mqtt
import discord, datetime, time, threading, queue
import sys, os, json, base64
from dotenv import load_dotenv

load_dotenv()

# MQTT
MQTT_BROKER = os.getenv("MQTT_BROKER")
MQTT_PORT = os.getenv("MQTT_PORT")
MQTT_KEEPALIVE = 60
MQTT_TOPIC = "home/doorbell/yolo"

# Discord
TOKEN = os.getenv("DISCORD_TOKEN")


# Create the queues
q = queue.Queue()
discord_q = queue.Queue()

#declare mqtt callback functions
def on_connect(client, userdata, flags, rc):
    #if successful, rc = 0
    if rc == 0:
        pass
    else:
        print("Connection Failed")

def on_message(client, userdata, msg):
    if msg.topic == MQTT_TOPIC:
        q.put(msg.payload.decode("utf-8"))


#declare discord callback functions
def process_img():
    #data comes in as a json string with the following format:
    #{"time": UNIX_TIMESTAMP, "image": BASE64_IMG, "detected": LIST_OF_DETECTED_OBJECTS}

    while True:

        if q.empty():
            time.sleep(1)
            continue

        data = q.get()

        #convert the json string into a python dictionary
        data = json.loads(data)

        #convert time into dd/mm/yy - hh:mm:ss
        img_time = data[data].split(".")[0]
        img_time = datetime.datetime.fromtimestamp(int(img)).strftime("%d/%m/%y - %H:%M:%S")
        image = data["image"]

        #base64 decode the image
        image = base64.b64decode(image)

        detected = data["detected"]

        if len(detected) == 0:
            return False
        
        #if discord-tmp doesn't exist, create it
        if not os.path.exists("discord-tmp"):
            os.mkdir("./discord-tmp")

        filename = "./discord-tmp/discord-" + str(img_time) + ".jpg"
        
        #save the image to a file
        with open("./discord-tmp/image.jpg", "wb") as f:
            f.write(image)


        output = {"time": img_time, "detected": detected, "file": filename}
        discord_q.put(output)

def send_message(TOKEN):

    intents = discord.Intents.all()
    intents.members = True
    intents.presences = True
    intents.messages = True
    client = discord.Client(intents=intents)

    client.run(TOKEN)

    async def send(msg, file):
        channel = client.get_channel(1111814648862343241)
        await channel.send(msg, file=file)

    while True:
        if discord_q.empty():
            time.sleep(1)
            continue

        data = discord_q.get()

        #get the image file
        file = discord.File(data["file"], filename="image.jpg")

        #get the time
        time = data["time"]

        #get the detected objects
        detected = data["detected"]

        #create the message
        msg = "Detected: " + str(detected) + "\nTime: " + str(time)

        #send the message
        client.loop.create_task(send(msg, file))


# Create the MQTT client
mqtt_client = mqtt.Client()
mqtt_client.connect(MQTT_BROKER, MQTT_PORT, MQTT_KEEPALIVE)
mqtt_client.subscribe(MQTT_TOPIC)

# Set the MQTT callbacks
mqtt_client.on_connect = on_connect
mqtt_client.on_message = on_message


#spawn thread
process_thread = threading.Thread(target=process_img).start()
send_thread = threading.Thread(target=send_message, args=(TOKEN,)).start()

#start the mqtt loop
mqtt_client.loop_start()













