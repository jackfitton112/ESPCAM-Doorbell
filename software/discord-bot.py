
import paho.mqtt.client as mqtt
import discord, datetime, time, threading, queue
import os, json, base64
from dotenv import load_dotenv
from datetime import datetime
import asyncio
import io


load_dotenv()

# Get the environment variables
try:
    TOKEN = os.getenv("DISCORD_TOKEN")
    MQTT_BROKER = os.getenv("MQTT_BROKER")
    MQTT_PORT = int(os.getenv("MQTT_PORT"))
    DISCORD_CHANNEL_ID = os.getenv("DISCORD_CHANNEL_ID")
    MQTT_YOLO_TOPIC = "home/doorbell/yolo"
except:
    print("Error getting environment variables")
    exit(1)



#setup inbound queue
mqtt_queue = queue.Queue()
#setup outbound queue
discord_queue = queue.Queue()



def mqtt_send():

    #terminating thread, send live message to MQTT broker and then stop thread

    #setup the MQTT client
    client = mqtt.Client()

    #connect to the MQTT broker
    client.connect(MQTT_BROKER, MQTT_PORT, 60)

    #send the live message
    client.publish("home/doorbell/live", "true")

    #stop the MQTT loop
    client.loop_stop()

    #exit the thread
    exit()


def mqtt_listen():

    #setup callbacks
    def on_connect(client, userdata, flags, rc):
        print("Connected to MQTT broker with result code "+str(rc))
        client.subscribe(MQTT_YOLO_TOPIC)

    def on_message(client, userdata, msg):
        #put the message in the queue
        try:
            mqtt_queue.put(msg.payload.decode("utf-8"))


        except:
            pass


    #setup the MQTT client
    client = mqtt.Client()
    client.on_connect = on_connect
    client.on_message = on_message

    #connect to the MQTT broker
    client.connect(MQTT_BROKER, MQTT_PORT, 60)

    #start the MQTT loop
    client.loop_start()

def queue_handler():

    #take message from mqtt queue, decode it, and put it in the discord queue

    while True:

        if mqtt_queue.empty():
            time.sleep(0.1)
            pass

        #get the message from the queue
        msg = mqtt_queue.get()
        msg = json.loads(msg)

        #message is a json string, decode it to image, time, detected
        try:
            msgimg = base64.b64decode(msg["image"])
            msgtime = msg["time"]
            msgdetected = msg["detected"]

        except:
            print("Error decoding MQTT message")

        output = [msgimg, msgtime, msgdetected]

        #put the message in the discord queue
        discord_queue.put(output)

        #mark the message as done
        mqtt_queue.task_done()
        
def discord_send():

    #setup the discord client
    print("Starting discord client")
    client = discord.Client(intents=discord.Intents.all())

    #setup the discord event
    @client.event
    async def on_ready():
        print("Logged in as {0.user}".format(client))
        client.loop.create_task(main_loop())

    @client.event
    async def on_message(message):
        if message.author == client.user:
            return

        if message.content.startswith("!live"):
            await message.channel.send("Getting live image...")

            #check thread is not already running
            try:
                t4 = threading.Thread(target=mqtt_send).start()
            except:
                pass




        
        
    #run a non blocking loop to send the messages
    async def send_message():

        while True:

            if discord_queue.empty():
                return

            
            #get the message from the queue
            msgimg, msgtime, msgdetected = discord_queue.get()

            msgtime = int(msgtime.split(".")[0])

            date = datetime.fromtimestamp(msgtime).strftime("%d-%m-%Y %H:%M:%S")

            #create the discord message
            msg = (f"Event Detected: {msgdetected} @ {date}")
            
            image_fp = io.BytesIO(msgimg)

            # Create the discord File object
            img = discord.File(fp=image_fp, filename="image.jpg")


            #send the message
            channel = client.get_channel(int(DISCORD_CHANNEL_ID))

            await channel.send(msg, file=img)

            #mark the message as done
            discord_queue.task_done()
            

    #create a loop that is non blocking and runs every second
    async def main_loop():
        while True:
            await send_message()
            await asyncio.sleep(1)



    #connect to the discord server
    client.run(TOKEN)


t1 = threading.Thread(target=mqtt_listen).start()
t2 = threading.Thread(target=queue_handler).start()
t3 = threading.Thread(target=discord_send).start()


while True:
    time.sleep(1)