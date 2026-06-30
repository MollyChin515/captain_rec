import io
import json
import random
import time
import threading
from PIL import Image

import cv2
import requests
import hashlib
from workflow.tool import *
from workflow.conf import *


def generate_md5(text):
    md5 = hashlib.md5()
    md5.update(text.encode(encoding='utf-8'))
    return md5.hexdigest()

def CalcMD5(filepath):
  with open(filepath,'rb') as f:
    md5obj = hashlib.md5()
    md5obj.update(f.read())
    hash = md5obj.hexdigest()
    # print(hash)
    return hash

# 上传事件的函数
def upload_event(camera_num, cameraLocat, eventName, eventCode, delay, image_data, to_url):
    # 模拟摄像头编号和其他信息
    camera_data_template = {
        "cameraLocat": "船舱 1001",
        "pcNum": 1,
        "pcModel": "YOLO11",
        "cameraState": 1,
        "eventPic": "",
        "detectionResult": [[random.random() for _ in range(4)] for _ in range(2)],  # 随机生成检测结果
    }
    event_data = camera_data_template.copy()  # 拷贝摄像头数据模板
    cur_time = getTimestampTool()
    #报文格式
    event_data.update({
        "cameraNum": camera_num,
        "cameraLocat": cameraLocat,
        "eventName": eventName,
        "occTime": cur_time,# + int(time.time()*10)
        "pcNum": getPcNum(),#非必须项，可保持默认
        "pcModel": "YOLO11",#非必须项，可保持默认
        "cameraState": 1,
        "eventCode": eventCode,
        "handleTime": int(time.time()*10),
        "detectionResult": [
            [0.134, 0.256, 0.145, 0.457],
            [0.134, 0.256, 0.145, 0.457]
        ],#非必须项，可保持默认
        "eventNum": generate_md5(eventCode + str(cur_time))
    })

    image = Image.fromarray(image_data)
    # 创建一个字节流对象
    buffer = io.BytesIO()
    # 将图像保存到字节流对象中，指定格式为JPEG
    image.save(buffer, format='JPEG')
    # 获取字节流对象的内容
    image_bytes = buffer.getvalue()
    # 将字节流对象重置到开始位置，以便再次读取
    buffer.seek(0)

    # files = {'file': open(file_path, 'rb')}
    pic_name = event_data["eventNum"] + ".jpg"
    files = {'file': (pic_name, buffer, 'image/jpeg')}
    # files = {'file': (None, json.dumps(event_data), 'application/json')}
    # 模拟上传延迟
    time.sleep(delay)
    print(event_data)
    # 发送POST请求到指定的上传URL
    files["data"] = (None, json.dumps(event_data), 'application/json')
    # response = requests.post(upload_url_skills, files=files, json=event_data)
    response = requests.post(url=to_url, files=files)
    print("Sending abnormal request")

    # 检查响应
    if response.status_code == 200:
        response_data = response.json()
        if response_data["code"] == 200:
            print(f"摄像头 {camera_num} 事件 {eventCode} 上传成功: {eventName}")
        else:
            print(f"摄像头 {camera_num} 事件 {eventCode} 上传失败: {response_data.get('msg')}")
    else:
        print(f"摄像头 {camera_num} 事件 {eventCode} 上传失败: 请求错误 {response.status_code}")


def upload_event1(camera_num, cameraLocat, eventName, eventCode, delay, image_data, end_str, to_url):
    # 模拟摄像头编号和其他信息
    camera_data_template = {
        "cameraLocat": "船舱 1001",
        "pcNum": 1,
        "pcModel": "YOLO11",
        "cameraState": 1,
        "eventPic": "",
        "detectionResult": [[random.random() for _ in range(4)] for _ in range(2)],  # 随机生成检测结果
    }
    event_data = camera_data_template.copy()  # 拷贝摄像头数据模板
    cur_time = getTimestampTool()
    #报文格式
    event_data.update({
        "cameraNum": camera_num,
        "cameraLocat": cameraLocat,
        "eventName": eventName,
        "occTime": cur_time,# + int(time.time()*10)
        "pcNum": getPcNum(),#非必须项，可保持默认
        "pcModel": "YOLO11",#非必须项，可保持默认
        "cameraState": 1,
        "eventCode": eventCode,
        "handleTime": int(time.time()*10),
        "detectionResult": [
            [0.134, 0.256, 0.145, 0.457],
            [0.134, 0.256, 0.145, 0.457]
        ],#非必须项，可保持默认
        "eventNum": generate_md5(eventCode + str(cur_time))
    })

    image = Image.fromarray(image_data)
    # 创建一个字节流对象
    buffer = io.BytesIO()
    # 将图像保存到字节流对象中，指定格式为JPEG
    image.save(buffer, format='JPEG')
    # 获取字节流对象的内容
    image_bytes = buffer.getvalue()
    # 将字节流对象重置到开始位置，以便再次读取
    buffer.seek(0)

    # files = {'file': open(file_path, 'rb')}
    pic_name = event_data["eventNum"] + '_' + end_str + ".jpg"
    files = {'file': (pic_name, buffer, 'image/jpeg')}
    # files = {'file': (None, json.dumps(event_data), 'application/json')}
    # 模拟上传延迟
    time.sleep(delay)
    print(event_data)
    # 发送POST请求到指定的上传URL
    files["data"] = (None, json.dumps(event_data), 'application/json')
    # response = requests.post(upload_url_skills, files=files, json=event_data)
    response = requests.post(url=to_url, files=files)
    print("Sending abnormal request")

    # 检查响应
    if response.status_code == 200:
        response_data = response.json()
        if response_data["code"] == 200:
            print(f"摄像头 {camera_num} 事件 {eventCode} 上传成功: {eventName}")
        else:
            print(f"摄像头 {camera_num} 事件 {eventCode} 上传失败: {response_data.get('msg')}")
    else:
        print(f"摄像头 {camera_num} 事件 {eventCode} 上传失败: 请求错误 {response.status_code}")
    return event_data["eventNum"] + '_' + end_str

# 摄像头事件上传的线程函数
def camera_event_thread(camera_num, delay, image_data, to_url):
    # 每个摄像头上传启用的事件
    for eventCode in list(algorithm_name.keys()):
        cameraLocat = camera_name[camera_num]
        eventName = algorithm_name[eventCode]
        upload_event(camera_num, cameraLocat, eventName, eventCode, delay, image_data, to_url)

        #疲劳驾驶
        upload_event('984TC000', '位置：驾控台，驾驶室，984TC000，变焦2.8-12mm，172.17.26.200', "驾驶室疲劳驾驶检测", "2-005", 0.0, image_data, upload_url_skills)

if __name__ == '__main__':
    # #重新排列报文
    # camera_name_resort = dict()
    # for key, value in camera_name.items():
    #     value1 = value.split('，')
    #     value2 = value1[2] + '，' + value1[3] + '，' + value1[0] + '，' + value1[1] + '，' + value1[4]
    #     camera_name_resort[key] = value2

    #从硬盘读取
    pic_name = "0000000000000000.jpg"
    file_path = "./" + pic_name
    with open(file_path, 'rb') as file:
        buffer = file.read()

    #从numpy读取
    # buffer = io.BytesIO()
    # image_np.save(buffer, format='JPEG')
    # image_bytes = buffer.getvalue()
    # buffer.seek(0)

    #测试单线上报
    buffer = cv2.imread(pic_name)
    for i in range(1):
        cv2.waitKey(100)
        upload_event('984TC000', '位置：驾驶室，984TC000，172.17.26.200', "联调测试", "2-005", 0.0, buffer,
                     'http://10.143.208.16:8099/api/behavior/abnormal')

    # # 创建线程并启动
    # threads = []
    # for i in range(8):
    #     # random_number = random.choice([i for i in range(1, 125)])
    #     # camera_num = f"984TC{(int(random_number)+1):03}"  # 模拟摄像头编号
    #     camera_num = random.choice(list(camera_name.keys()))
    #     thread = threading.Thread(target=camera_event_thread, args=(camera_num, delay, buffer, upload_url_skills))
    #     threads.append(thread)
    #     thread.start()
    # # 等待所有线程完成
    # for thread in threads:
    #     thread.join()#非必须项，可保持默认
