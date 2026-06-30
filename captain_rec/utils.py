# utils.py
import io
import json
import time
import hashlib
from datetime import datetime
from PIL import Image
import requests


def generate_md5(text: str) -> str:
    """生成MD5哈希值"""
    md5 = hashlib.md5()
    md5.update(text.encode(encoding='utf-8'))
    return md5.hexdigest()


def get_timestamp() -> int:
    """获取当前时间戳（毫秒）"""
    return int(time.time() * 1000)


def upload_event(camera_num: str, camera_locat: str, event_name: str, 
                 event_code: str, image_data, upload_url: str) -> bool:
    """上报事件到服务器
    
    Args:
        camera_num: 摄像头编号
        camera_locat: 摄像头位置描述
        event_name: 事件名称
        event_code: 事件编码
        image_data: 图像数据 (numpy array)
        upload_url: 上报URL
    
    Returns:
        bool: 上报是否成功
    """
    cur_time = get_timestamp()
    event_num = generate_md5(event_code + str(cur_time))
    
    # 构建事件数据
    event_data = {
        "cameraNum": camera_num,
        "cameraLocat": camera_locat,
        "eventName": event_name,
        "occTime": cur_time,
        "pcNum": 1,
        "pcModel": "YOLO11",
        "cameraState": 1,
        "eventCode": event_code,
        "handleTime": int(time.time() * 10),
        "detectionResult": [[0.134, 0.256, 0.145, 0.457]],
        "eventNum": event_num
    }
    
    # 将numpy图像转换为字节流
    try:
        image = Image.fromarray(image_data)
        buffer = io.BytesIO()
        image.save(buffer, format='JPEG')
        buffer.seek(0)
    except Exception as e:
        print(f"图像转换失败: {e}")
        return False
    
    # 构建上传文件
    pic_name = f"{event_num}.jpg"
    files = {
        'file': (pic_name, buffer, 'image/jpeg'),
        'data': (None, json.dumps(event_data), 'application/json')
    }
    
    try:
        response = requests.post(url=upload_url, files=files, timeout=10)
        
        if response.status_code == 200:
            response_data = response.json()
            if response_data.get("code") == 200:
                print(f"✅ 事件上报成功: {event_name} [{event_code}]")
                return True
            else:
                print(f"❌ 事件上报失败: {response_data.get('msg')}")
        else:
            print(f"❌ 事件上报失败: HTTP {response.status_code}")
    except Exception as e:
        print(f"❌ 事件上报异常: {e}")
    
    return False


def send_warning(absent_employees, alert_type="absent"):
    """发送告警（仅打印日志，不实际上报）"""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    print("\n" + "="*50)
    print(f"🔔 告警通知 [{timestamp}]")
    print("="*50)
    
    if alert_type == "no_face":
        print(f"告警: 画面无人脸")
    else:
        print(f"⚠️ 告警: 值班人员缺勤！")
        print(f"   请立即检查值班人员是否在岗")
    
    print("="*50 + "\n")
    
    # 写入日志
    with open("warning_log.txt", "a", encoding="utf-8") as f:
        if alert_type == "no_face":
            f.write(f"{timestamp} - 画面无人脸告警\n")
        else:
            f.write(f"{timestamp} - 值班人员缺勤告警\n")
    
    return True

def print_captain_status(is_detected, absent_counter, threshold):
    """打印值班人员状态"""
    if is_detected:
        print(f"✅ 值班人员在岗")
    else:
        print(f"❌ 值班人员缺勤 (连续 {absent_counter}/{threshold} 次)")