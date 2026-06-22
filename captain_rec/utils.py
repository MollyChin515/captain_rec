# utils.py
from datetime import datetime

def send_warning(absent_employees, alert_type="absent"):
    """发送告警"""
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