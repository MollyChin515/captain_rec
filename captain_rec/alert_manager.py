# alert_manager.py
import os
import cv2
import time
from datetime import datetime
from utils import send_warning

class AlertManager:
    """告警管理类 - 简化版（只关心值班人员是否在岗）"""
    
    def __init__(self, absent_threshold=5, warning_cooldown=300, work_set_config=None):
        """
        初始化告警管理器
        
        Args:
            absent_threshold: 缺勤告警阈值（连续多少次未检测到值班人员）
            warning_cooldown: 警告冷却时间（秒），避免重复告警
            work_set_config: 工作集配置对象（可选）
        """
        self.absent_threshold = absent_threshold
        self.warning_cooldown = warning_cooldown
        self.work_set_config = work_set_config
        
        # 值班人员连续未检测到的次数
        self.captain_absent_counter = 0
        
        # 画面中连续无人脸的次数
        self.no_face_counter = 0
        
        # 上次警告时间（用于冷却）
        self.last_warning_time = 0
        
        # 是否已经告警（避免重复告警）
        self.has_alerted = False
        
        # 创建截图保存目录
        self.screenshot_dir = "screenshots"
        os.makedirs(self.screenshot_dir, exist_ok=True)
        
        # 当前帧（用于截图）
        self.current_frame = None
        
        print(f"📸 告警管理器初始化完成")
        print(f"   - 截图目录: {self.screenshot_dir}")
        print(f"   - 告警阈值: 连续 {absent_threshold} 次未检测到值班人员")
        print(f"   - 冷却时间: {warning_cooldown} 秒")
    
    def update_frame(self, frame):
        """更新当前帧（用于截图）"""
        self.current_frame = frame.copy() if frame is not None else None
    
    def update_detection(self, is_captain_detected, has_face):
        """
        更新检测结果，返回是否触发告警
        
        Args:
            is_captain_detected: 是否检测到值班人员
            has_face: 是否检测到人脸（任何人脸）
            
        Returns:
            bool: 是否触发了告警
        """
        triggered = False
        current_time = time.time()
        
        # 1. 更新值班人员的连续检测计数
        if is_captain_detected:
            # 检测到值班人员，重置计数
            if self.captain_absent_counter >= self.absent_threshold:
                print(f"✅ 值班人员已回到岗位 (连续缺勤已结束)")
                self.has_alerted = False  # 重置告警标志
            self.captain_absent_counter = 0
        else:
            # 未检测到值班人员，增加计数
            self.captain_absent_counter += 1
            print(f"⚠️ 未检测到值班人员 - 连续次数: {self.captain_absent_counter}")
        
        # 2. 更新无人脸检测计数
        if not has_face:
            self.no_face_counter += 1
            if self.no_face_counter == self.absent_threshold:
                print(f"⚠️ 警告: 画面已连续 {self.no_face_counter} 次未检测到任何人脸!")
                self._take_screenshot(None, 'no_face')
        else:
            if self.no_face_counter >= self.absent_threshold:
                print(f"✅ 重新检测到人脸")
            self.no_face_counter = 0
        
        # 3. 检查是否需要告警（值班人员缺勤）
        # 条件：达到阈值 且 未在冷却时间内 且 还未告警过
        if (self.captain_absent_counter >= self.absent_threshold and 
            not self.has_alerted):
            
            # 检查冷却时间
            time_since_last_warning = current_time - self.last_warning_time
            if time_since_last_warning >= self.warning_cooldown:
                # 触发告警
                triggered = True
                self.has_alerted = True
                self.last_warning_time = current_time
                
                print(f"\n⚠️⚠️⚠️ 告警: 值班人员缺勤！")
                print(f"    已连续 {self.captain_absent_counter} 次未检测到值班人员")
                print(f"    距上次告警: {time_since_last_warning:.0f} 秒")
                
                # 截图保存
                self._take_screenshot('值班人员', 'absent')
            else:
                # 还在冷却时间内，不告警
                remaining = self.warning_cooldown - time_since_last_warning
                print(f"⏰ 冷却中: {remaining:.0f} 秒后可再次告警")
        
        return triggered
    
    def _take_screenshot(self, employee_name, reason="absent"):
        if self.current_frame is None:
            return None
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        if reason == "absent":
            filename = f"{self.screenshot_dir}/employee_absent_{timestamp}.jpg"
            caption = f"ALERT: Employee is ABSENT for {self.absent_threshold} times"
        else:
            filename = f"{self.screenshot_dir}/no_face_detected_{timestamp}.jpg"
            caption = f"ALERT: No face detected for {self.absent_threshold} times"
        
        # 在图片上添加文字标注
        img_with_text = self.current_frame.copy()
        cv2.putText(img_with_text, caption, (10, 30),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)
        cv2.putText(img_with_text, datetime.now().strftime("%Y-%m-%d %H:%M:%S"), 
                   (10, 60), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)
        
        # 保存截图
        cv2.imwrite(filename, img_with_text)
        print(f"📸 截图已保存: {filename}")
        
        return filename
    
    def get_status(self):
        """获取当前状态"""
        current_time = time.time()
        time_since_last = current_time - self.last_warning_time if self.last_warning_time > 0 else float('inf')
        
        return {
            'captain_absent_counter': self.captain_absent_counter,
            'no_face_counter': self.no_face_counter,
            'threshold': self.absent_threshold,
            'has_alerted': self.has_alerted,
            'last_warning_time': self.last_warning_time,
            'cooldown': self.warning_cooldown,
            'cooldown_remaining': max(0, self.warning_cooldown - time_since_last) if self.has_alerted else 0
        }
    
    def reset(self):
        """重置所有计数器"""
        self.captain_absent_counter = 0
        self.no_face_counter = 0
        self.has_alerted = False
        # 注意：不重置 last_warning_time，保持冷却记录
        print("🔄 告警计数器已重置")