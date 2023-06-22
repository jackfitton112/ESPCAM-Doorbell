# ESPCAM-Doorbell

![python Version 3.8.10](https://img.shields.io/badge/python_version-3.11.4-blue)
![GitHub](https://img.shields.io/github/license/jackfitton112/ESPCAM-Doorbell)


---

## Introduction

This project is a doorbell that uses a ESP32-CAM to detect people and send a notification to your phone. It uses YOLOv3 to detect objects when motion is detected.

The goal is to have a discord bot notify you when someone is at your door. The bot will first send a message and then an image of the person at the door.


### Hardware Requirements
For this project you will need:
- ESP32-CAM (I used the AI-Thinker model) ~£10 on [Amazon](https://www.amazon.co.uk/XTVTX-ESP32-CAM-Bluetooth-ESP32-CAM-MB-compatible/dp/B093GSCBWJ/ref=asc_df_B093GSCBWJ/?tag=googshopuk-21&linkCode=df0&hvadid=499333556330&hvpos=&hvnetw=g&hvrand=3810417733538846907&hvpone=&hvptwo=&hvqmt=&hvdev=c&hvdvcmdl=&hvlocint=&hvlocphy=9046521&hvtargid=pla-1304281846791&psc=1)

- Camera Housing (I used a electrical junction box) ~£4 at [ScrewFix](https://www.screwfix.com/p/british-general-ip55-weatherproof-outdoor-enclosure-75-x-53-x-85mm/33991?)

- Computer / SBC to run MQTT, MotionEye (I used a Orange Pi 3 LTS) ~£35 on [AliExpress](https://www.aliexpress.com/item/1005005554787211.html)

- A PC to run YOLOv7 (I used my Dell PowerEdge R810 but you can use a Raspberry Pi 4 (it will take a while though)) 

### Software Requirements

- [MotionEye](https://github.com/motioneye-project/motioneye) - For motion detection (I used a docker container on my Orange Pi)

- An MQTT Client (I used [Mosquitto](https://mosquitto.org/)) - For communication between the scripts as this allowed for other people to use the data for their own projects within the house

- [Python3](https://www.python.org/downloads/) - the YOLO Libary uses Python3, it is recommended to use the `requirements.txt` to install the required packages as openCV currently has dependancy issues with Python3.9

- yolov3.weights - this is the pretrained model data, it should be put in `./utils` and can be downloaded from [here](https://pjreddie.com/media/files/yolov3.weights)


## Installation

All of the config required is a .env file, this should be placed in the root directory of the project. The .env file should contain the following:

```shell
DISCORD_TOKEN= <YOUR DISCORD BOT TOKEN>
MQTT_BROKER= <YOUR BROKER IP / HOSTNAME>
MQTT_PORT= <YOUR BROKER PORT>
IMAGE_DIR_PATH= <MOTION EYE SAVE DIR >
```
> a sample .env file is provided in the repo

to run the project you will need to run the following command:

```shell
nohup python3 yolo-process.py > /dev/null &;
nohup python3 motion-send.py > /dev/null &;
nohup python3 discord-bot.py > /dev/null &
```


#### `discord-bot.py`

This script runs the discord bot, it gets the messages from MQTT and converts them into a discord message, it also sends the images to discord. 

see below an example of the discord bot in action:

![Discord bot in action](/images/discord.png)




 




