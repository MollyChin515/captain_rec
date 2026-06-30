import random
import datetime

from workflow.conf import *

image_path = "pic/"


def getCameraTool():
    cameraNum = random.choice(list(camera_name.keys()))
    cameraLocat = camera_name[cameraNum]
    eventCode = random.choice(list(algorithm_name.keys()))
    eventName = algorithm_name[eventCode]
    return cameraNum, cameraLocat, eventName, eventCode


def getTimestampTool():
    now = datetime.datetime.now()
    return int(now.timestamp())


def getPcNum():
    return random.randint(1, 2)


def getPic():
    pic_list = ["pic_1.jpg", "pic_2.jpg", "pic_3.png"]
    pic_name = random.choice(pic_list)
    path = image_path + pic_name
    with open(path, 'rb') as file:
        image_data = file.read()
    return image_data, pic_name

def getPicPath():
    pic_list = ["pic_1.jpg", "pic_2.jpg", "pic_3.png"]
    return image_path + random.choice(pic_list)

def getPeopleNum():
    boardersNum = random.randint(1, 30)
    disembarkersNum = random.randint(1, 30)
    return boardersNum, disembarkersNum

def getServerIP():
    ServerIP1 = "192.168.127.12"
    ServerIP2 = "192.168.127.13"
    ipList = [ServerIP1, ServerIP2]
    return random.choice(ipList)

def getState():
    return random.randint(0, 1)

if __name__ == '__main__':
    print(getTimestampTool())
