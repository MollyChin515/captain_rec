# monitor.py
import cv2
import time
from recognizer import FaceRecognizer
from alert_manager import AlertManager
from utils import print_captain_status

class AttendanceMonitor:
    """在岗监控类 - 简化版（只监控值班人员）"""
    
    def __init__(self, recognizer, alert_manager):
        """
        初始化监控器
        
        Args:
            recognizer: 人脸识别器实例
            alert_manager: 告警管理器实例
        """
        self.recognizer = recognizer
        self.alert_manager = alert_manager
        
        # 当前是否检测到值班人员
        self.is_captain_detected = False
        
        # 最后识别到的员工信息
        self.last_detected_employee = None  # {'name': str, 'employee_id': str, 'position': str}
        
        # 帧计数器
        self.frame_counter = 0
        
        # 状态输出控制
        self.last_status_time = time.time()
        self.update_interval = 30
    
    def process_frame(self, frame, detect_interval=10):
        """
        处理单帧图像
        
        Args:
            frame: 输入帧
            detect_interval: 检测间隔
            
        Returns:
            bool: 是否检测到值班人员
        """
        # 更新告警管理器的当前帧（用于截图）
        self.alert_manager.update_frame(frame)
        self.frame_counter += 1
        
        # 控制检测频率
        if self.frame_counter % detect_interval != 0:
            return self.is_captain_detected
        
        # 检测并识别人脸
        results = self.recognizer.detect_and_recognize(frame)

        # 更新值班人员检测状态
        self.is_captain_detected = False
        has_face = False
        detected_names = []  # 存储检测到的员工姓名
        
        for r in results:
            has_face = True
            if r['is_recognized']:
                # 识别到值班人员
                self.is_captain_detected = True
                detected_names.append(r['name'])
                # 存储最后识别到的员工信息
                self.last_detected_employee = {
                    'name': r['name'],
                    'employee_id': r['employee_id'],  # 工号
                    'position': r['position']
                }
                print(f"✅ 检测到: {r['name']} (工号:{r['employee_id']} 岗位:{r['position']} 相似度:{r['similarity']:.3f})")
                break  # 检测到一个值班人员就够了
        
        if has_face and not self.is_captain_detected:
            print(f"⚠️ 检测到未识别的人员")
        # 更新告警管理器
        alerted = self.alert_manager.update_detection(self.is_captain_detected, has_face)
        
        if alerted:
            self._send_alert()
        
        return self.is_captain_detected
    
    def _send_alert(self):
        """发送缺勤告警"""
        from utils import send_warning
        send_warning(["值班人员"])
    
    def print_status(self):
        """打印当前状态"""
        current_time = time.time()
        if current_time - self.last_status_time >= self.update_interval:
            status = self.alert_manager.get_status()
            
            print("\n" + "="*50)
            print(f"📊 当前状态")
            print("="*50)
            
            if self.is_captain_detected:
                print(f"✅ 值班人员状态: 在岗")
            elif status['captain_absent_counter'] >= status['threshold']:
                print(f"❌ 值班人员状态: 缺勤 (已达告警阈值)")
            else:
                print(f"⚠️ 值班人员状态: 检测中 ({status['captain_absent_counter']}/{status['threshold']})")
            
            print(f"   连续未检测: {status['captain_absent_counter']} 次")
            print(f"   告警阈值: {status['threshold']} 次")
            print(f"   画面无人脸: {status['no_face_counter']} 次")
            
            self.last_status_time = current_time
    
    def get_summary(self):
        """获取当前摘要"""
        status = self.alert_manager.get_status()
        return {
            'is_captain_detected': self.is_captain_detected,
            'absent_counter': status['captain_absent_counter'],
            'threshold': status['threshold'],
            'has_alerted': status['has_alerted'],
            'last_detected_employee': self.last_detected_employee
        }
    
    def reset_frame_counter(self):
        """重置帧计数器"""
        self.frame_counter = 0