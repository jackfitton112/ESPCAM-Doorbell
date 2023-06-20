# ESPCAM-Doorbell

## THIS PROJECT IS STILL UNDER DEVELOPMENT AND IS NOT COMPLETE
---

![Raw image from MotionEye](images/raw.png)
![YOLO output image](images/detected.png)

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

#### `motion-send.py`
 has some config options that need setting. it is recommended to run this on the same device as motioneye runs on as it will be able to access the images directly. 

 The config options are:

   - MQTT_BROKER
   - IMG_DIR_PATH

#### `yolo-process.py`

This script is used to process the images from motioneye and send them to the discord bot. It is recommended to run this on a proper PC / Server as it is quite resource intensive.

The config options are:

   - MQTT_BROKER


#### `discord-bot.py`

TO BE COMPLETED


 




