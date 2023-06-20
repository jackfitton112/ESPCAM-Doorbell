
import paho.mqtt.client as mqtt
import discord, datetime, time, threading, queue
import os, json, base64
from dotenv import load_dotenv
from datetime import datetime


load_dotenv()

#
# Discord
TOKEN = os.getenv("DISCORD_TOKEN")


# Create the queues
q = queue.Queue()
discord_q = queue.Queue()

#this program needs 3 threads
#1. mqtt thread
#2. discord thread
#3. interface thread

#mqtt thread
def mqtt_thread():

    def on_message(client, userdata, msg):
        print("mqtt message received")
        q.put(msg.payload)

    #on connect function
    def on_connect(client, userdata, flags, rc):
        print("mqtt connected")
        client.subscribe(MQTT_TOPIC)
    

    MQTT_BROKER = os.getenv("MQTT_BROKER")
    MQTT_PORT = 1883
    MQTT_KEEPALIVE = 60
    MQTT_TOPIC = "home/doorbell/yolo"

    print("mqtt thread started")
    client = mqtt.Client()
    client.connect(MQTT_BROKER, MQTT_PORT, MQTT_KEEPALIVE)
    client.on_message = on_message
    client.on_connect = on_connect

    client.loop_start()

#discord thread
def discord_thread():
    
    #setup discord client
    intents = discord.Intents.default()
    intents.members = True
    intents.presences = True
    intents.messages = True
    client = discord.Client(intents=intents)


    @client.event
    async def on_ready():
        #print("discord thread started")
        #start send message thread
        client.loop.create_task(send_messages())

    async def send_messages():
        await client.wait_until_ready()
        DISCORD_CHANNEL_ID = os.getenv("DISCORD_CHANNEL_ID")
        channel = client.get_channel(int(DISCORD_CHANNEL_ID))

        while True:

            if discord_q.empty():
                time.sleep(1)
                pass

            msg, file = discord_q.get()
            print(msg, file)
            file = discord.File(file, filename=file)
            await channel.send(msg, file=file)

            #delete file
            os.remove(file)

            #remove item from queue
            discord_q.task_done()

    client.run(TOKEN)

#interface thread
def interface_thread():

    #takes mqtt message and parses it into a discord message
    while True:
        if q.empty():
            time.sleep(1)
            pass

        msg = q.get()

        #load json
        msg = json.loads(msg)

        #get image
        img = msg["image"]
        img = base64.b64decode(img)

        #get timestamp
        timestamp = msg["time"].split(".")[0]

        #get detected
        detected = msg["detected"]

        #save image to temp folder

        #if /tmp/ doesn't exist, create it
        if not os.path.exists("./tmp/"):
            os.makedirs("./tmp/")

        #create filename
        filename = "./tmp/img-" + timestamp + ".jpg"

        #save image
        with open(filename, "wb") as f:
            f.write(img)

        #convert unix timestamp to datetime
        timestamp = datetime.utcfromtimestamp(int(timestamp)).strftime('%Y-%m-%d %H:%M:%S')

        msg = f"New Event Detected {str(detected)} at {timestamp}:"
        print(msg)

        discord_q.put((msg, filename))

        #remove task from queue
        q.task_done()


#start threads
t1 = threading.Thread(target=mqtt_thread).start()
t2 = threading.Thread(target=discord_thread).start()
t3 = threading.Thread(target=interface_thread).start()

while True:
    time.sleep(1)
    pass





