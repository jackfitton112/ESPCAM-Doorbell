# ESPCAM-Doorbell

![python Version 3.8.10](https://img.shields.io/badge/python_version-3.11.4-blue)
![GitHub](https://img.shields.io/github/license/jackfitton112/ESPCAM-Doorbell)
![GitHub last commit](https://img.shields.io/github/last-commit/jackfitton112/ESPCAM-Doorbell)
![GitHub issues](https://img.shields.io/github/issues/jackfitton112/ESPCAM-Doorbell)
![GitHub pull requests](https://img.shields.io/github/issues-pr/jackfitton112/ESPCAM-Doorbell)
![GitHub Repo stars](https://img.shields.io/github/stars/jackfitton112/ESPCAM-Doorbell?style=social)

---

## About

This project came about after wanting a Ring style doorbell, there are four main issues with Ring doorbells:

- They are expensive
- They are not open source
- They are not customisable
- They send your data to Amazon

Not wanting a big tech firm to have pictures of me on their server I decided to make my own doorbell. This project is fully self hosted and although a network is required to run it, it does not require an internet connection and can be run on an air gapped network (I have not tested this but it should work).


### Hardware Requirements
For this project you will need:
- ESP32-CAM (I used the AI-Thinker model) ~£10 on [Amazon](https://www.amazon.co.uk/XTVTX-ESP32-CAM-Bluetooth-ESP32-CAM-MB-compatible/dp/B093GSCBWJ/ref=asc_df_B093GSCBWJ/?tag=googshopuk-21&linkCode=df0&hvadid=499333556330&hvpos=&hvnetw=g&hvrand=3810417733538846907&hvpone=&hvptwo=&hvqmt=&hvdev=c&hvdvcmdl=&hvlocint=&hvlocphy=9046521&hvtargid=pla-1304281846791&psc=1)

- Camera Housing (I used a electrical junction box) ~£4 at [ScrewFix](https://www.screwfix.com/p/british-general-ip55-weatherproof-outdoor-enclosure-75-x-53-x-85mm/33991?)

- Computer / SBC to run MQTT, MotionEye (I used a Orange Pi 3 LTS) ~£35 on [AliExpress](https://www.aliexpress.com/item/1005005554787211.html)

- A PC to run YOLOv3 (I used my Dell PowerEdge R810 but you can use the same SBC as above)

> Diagrams and schematics can be found in the `hardware` folder (coming soon)

### Software Requirements

- [MotionEye](https://github.com/motioneye-project/motioneye) - For motion detection (I used a docker container on my Orange Pi)

- An MQTT Client (I used [Mosquitto](https://mosquitto.org/)) - For communication between the scripts as this allowed for other people to use the data for their own projects within the house

- [Python3](https://www.python.org/downloads/) - the YOLO Libary uses Python3, it is recommended to use the `requirements.txt` to install the required packages as openCV currently has dependancy issues with Python3.9

- yolov3.weights - this is the pretrained model data, it should be put in `./utils` and can be downloaded from [here](https://pjreddie.com/media/files/yolov3.weights)


## Installation

All of the config required is a .env file, this should be placed in the root directory of the project. The .env file should contain the following:

```
DISCORD_TOKEN= <YOUR DISCORD BOT TOKEN>
DISCORD_CHANNEL_ID= <YOUR DISCORD CHANNEL ID>
IMAGE_DIR_PATH= <MOTION EYE SAVE DIR >
MOTION_EYE_URL= <MOTION EYE URL>
MQTT_BROKER= <YOUR BROKER IP / HOSTNAME>
MQTT_PORT= <YOUR BROKER PORT>
MQTT_USER= <YOUR BROKER USER>
MQTT_PASS= <YOUR BROKER PASSWORD>
```
> a sample .env file is provided in the repo

to run the project you will need to run the following command:

```shell
nohup python3 yolo-process.py > /dev/null &;
nohup python3 motion-send.py > /dev/null &;
nohup python3 discord-bot.py > /dev/null &
```

#### `discord-bot.py`

> This script is tempermental and needs updating to use asyncio instead of threading.
> I'm in the process of updating this script when I have time.

This script runs the discord bot, it gets the messages from MQTT and converts them into a discord message, it also sends the images to discord. 

see below an example of the discord bot in action:

![Discord bot in action](/images/discord.png)


#### TODO:

> This project is still a work in progress and I am still working on it when I have time. Please feel free to contribute to the project if you have any ideas or want to help out.

- [x] make !live work in `motion-send.py` asyincronously
- [x] remove threading (very inefficent) and replace with asyncio in `motion-send.py`
- [ ] remove threading (very inefficent) and replace with asyncio in `discord-bot.py`
- [ ] remove threading (very inefficent) and replace with asyncio in `yolo-process.py`
- [ ] make all python files conform to PEP8
- [ ] update YOLO version to v5-8 (currently v3)
- [ ] rewrite `README.md` to be more user friendly and include a setup guide
- [ ] dockerise the project to make it easier to deploy
- [ ] add hardware diagrams and schematics to `hardware` folder




