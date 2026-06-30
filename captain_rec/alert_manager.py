# alert_manager.py
import os
import cv2
import time
import numpy as np
from datetime import datetime
from PIL import Image, ImageDraw, ImageFont
from utils import send_warning, upload_event

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
                # 上报无人脸事件
                self._upload_alert_event('no_face')
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
                
                # 上报事件到服务器
                self._upload_alert_event('absent')
            else:
                # 还在冷却时间内，不告警
                remaining = self.warning_cooldown - time_since_last_warning
                print(f"⏰ 冷却中: {remaining:.0f} 秒后可再次告警")
        
        return triggered
    
    def _take_screenshot(self, employee_name, reason="absent"):
        """截图并添加中文标注"""
        if self.current_frame is None:
            return None
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        if reason == "absent":
            filename = f"{self.screenshot_dir}/employee_absent_{timestamp}.jpg"
            event_text = "值班人员未在岗"
        else:
            filename = f"{self.screenshot_dir}/no_face_detected_{timestamp}.jpg"
            event_text = "未检测到人脸"
        
        try:
            # 转换为PIL图像
            img_pil = Image.fromarray(cv2.cvtColor(self.current_frame, cv2.COLOR_BGR2RGB))
            draw = ImageDraw.Draw(img_pil)
            
            # 加载中文字体 - 尝试多个可能的字体路径
            possible_fonts = [
                # 项目字体目录
                os.path.join(os.path.dirname(__file__), "fonts", "wqy-microhei.ttf"),
                os.path.join(os.path.dirname(__file__), "fonts", "wqy-microhei.ttc"),
                os.path.join(os.path.dirname(__file__), "fonts", "NotoSansSC-Regular.otf"),
                # Linux 系统字体
                "/usr/share/fonts/truetype/wqy/wqy-microhei.ttc",
                "/usr/share/fonts/truetype/wqy/wqy-zenhei.ttc",
                "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc",
                "/usr/share/fonts/truetype/noto/NotoSansCJK-Regular.ttc",
                "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
                # WSL Windows 字体
                "/mnt/c/Windows/Fonts/msyh.ttc",
                "/mnt/c/Windows/Fonts/simhei.ttf",
                "/mnt/c/Windows/Fonts/simsun.ttc",
            ]
            
            font_path = None
            for path in possible_fonts:
                if os.path.exists(path):
                    font_path = path
                    print(f"✅ 使用字体: {path}")
                    break
            
            if font_path is None:
                print("⚠️ 未找到中文字体，使用默认字体")
            
            try:
                if font_path:
                    # 优化字体大小：标题更大，信息统一
                    font_title = ImageFont.truetype(font_path, 38)      # 告警标题
                    font_info = ImageFont.truetype(font_path, 26)       # 信息内容
                    font_time = ImageFont.truetype(font_path, 24)       # 时间戳
                else:
                    font_title = ImageFont.load_default()
                    font_info = ImageFont.load_default()
                    font_time = ImageFont.load_default()
            except Exception as e:
                print(f"⚠️ 字体加载失败: {e}，使用默认字体")
                font_title = ImageFont.load_default()
                font_info = ImageFont.load_default()
                font_time = ImageFont.load_default()
            
            # 获取配置信息
            camera_num = ""
            camera_locat = ""
            if self.work_set_config:
                camera_num = self.work_set_config.get_camera_num() or ""
                camera_locat = self.work_set_config.get_camera_locat() or ""
            
            # 文本换行函数
            def wrap_text(text, font, max_width):
                """将文本按最大宽度换行"""
                words = list(text)
                lines = []
                current_line = ""
                
                for char in words:
                    test_line = current_line + char
                    # 获取文本宽度
                    bbox = draw.textbbox((0, 0), test_line, font=font)
                    text_width = bbox[2] - bbox[0]
                    
                    if text_width <= max_width:
                        current_line = test_line
                    else:
                        if current_line:
                            lines.append(current_line)
                        current_line = char
                
                if current_line:
                    lines.append(current_line)
                
                return lines if lines else [text]
            
            # 准备文字内容 - 分层显示
            # 第一层：告警标题（醒目）
            title_text = f"⚠️ {event_text}"
            
            # 第二层：详细信息（清晰）
            info_lines = [
                f"摄像头编号: {camera_num}",
                f"监控位置: {camera_locat}",
            ]
            
            # 第三层：时间戳
            time_text = f"时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
            
            # 计算背景框尺寸
            padding = 20
            line_spacing = 35
            title_height = 50
            min_box_width = 500
            max_text_width = min_box_width - padding * 3  # 文本最大宽度
            
            # 对位置信息进行换行处理
            wrapped_info_lines = []
            for line in info_lines:
                if "监控位置" in line:
                    # 位置信息可能很长，进行换行
                    wrapped_lines = wrap_text(line, font_info, max_text_width)
                    wrapped_info_lines.extend(wrapped_lines)
                else:
                    wrapped_info_lines.append(line)
            
            # 重新计算高度
            info_height = len(wrapped_info_lines) * line_spacing
            time_height = 35
            total_height = title_height + info_height + time_height + padding * 3
            
            # 计算标题宽度
            title_bbox = draw.textbbox((0, 0), title_text, font=font_title)
            title_width = title_bbox[2] - title_bbox[0]
            
            # 计算时间戳宽度
            time_bbox = draw.textbbox((0, 0), time_text, font=font_time)
            time_width = time_bbox[2] - time_bbox[0]
            
            # 根据文本实际宽度计算框宽度
            max_text_width_actual = max(title_width, time_width, max_text_width)
            box_width = max(max_text_width_actual + padding * 3, min_box_width)
            
            # 绘制渐变背景框（更美观）
            # 外框：白色边框
            draw.rectangle(
                [(15, 15), (box_width + 15, total_height + 15)],
                fill=None,
                outline=(255, 255, 255),
                width=3
            )
            
            # 内框：半透明黑色背景
            draw.rectangle(
                [(18, 18), (box_width + 12, total_height + 12)],
                fill=(20, 20, 20, 200),
                outline=None
            )
            
            # 绘制标题（醒目的红色）
            draw.text((padding + 20, padding + 20), title_text, font=font_title, fill=(255, 80, 80))
            
            # 绘制分隔线
            y_line = padding + 20 + title_height + 5
            draw.line([(padding + 20, y_line), (box_width - padding, y_line)], fill=(100, 100, 100), width=1)
            
            # 绘制详细信息
            y_offset = y_line + 10
            for line in wrapped_info_lines:
                draw.text((padding + 20, y_offset), line, font=font_info, fill=(255, 255, 255))
                y_offset += line_spacing
            
            # 绘制时间戳（稍小的字体，灰色）
            draw.text((padding + 20, y_offset + 5), time_text, font=font_time, fill=(180, 180, 180))
            
            # 转换回OpenCV格式
            img_with_text = cv2.cvtColor(np.array(img_pil), cv2.COLOR_RGB2BGR)
            
        except Exception as e:
            print(f"⚠️ 绘制文字失败，使用默认方式: {e}")
            # 降级方案：使用OpenCV默认方式
            img_with_text = self.current_frame.copy()
            cv2.putText(img_with_text, f"ALERT: {event_text}", (10, 30),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)
            cv2.putText(img_with_text, datetime.now().strftime("%Y-%m-%d %H:%M:%S"), 
                       (10, 60), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)
        
        # 保存截图
        cv2.imwrite(filename, img_with_text)
        print(f"📸 截图已保存: {filename}")
        
        return filename
    
    def _upload_alert_event(self, alert_type="absent"):
        """上报告警事件到服务器
        
        Args:
            alert_type: 告警类型 ("absent" 或 "no_face")
        """
        if self.work_set_config is None:
            print("⚠️ 未配置工作集，跳过事件上报")
            return False
        
        if self.current_frame is None:
            print("⚠️ 无当前帧数据，跳过事件上报")
            return False
        
        try:
            # 获取配置信息
            camera_num = self.work_set_config.get_camera_num()
            camera_locat = self.work_set_config.get_camera_locat()
            upload_url = self.work_set_config.get_upload_url()
            
            if alert_type == "no_face":
                event_code = self.work_set_config.get_event_code_no_face()
                event_name = self.work_set_config.get_event_name_no_face()
            else:
                event_code = self.work_set_config.get_event_code_absent()
                event_name = self.work_set_config.get_event_name_absent()
            
            # 检查配置是否完整
            if not all([camera_num, camera_locat, upload_url]):
                print(f"⚠️ 配置不完整，跳过事件上报:")
                print(f"   camera_num: {camera_num}")
                print(f"   camera_locat: {camera_locat}")
                print(f"   upload_url: {upload_url}")
                return False
            
            print(f"\n📤 正在上报事件...")
            print(f"   摄像头: {camera_num}")
            print(f"   位置: {camera_locat}")
            print(f"   事件: {event_name} [{event_code}]")
            print(f"   URL: {upload_url}")
            
            # 调用上报函数
            success = upload_event(
                camera_num=camera_num,
                camera_locat=camera_locat,
                event_name=event_name,
                event_code=event_code,
                image_data=self.current_frame,
                upload_url=upload_url
            )
            
            if success:
                print(f"✅ 事件上报成功")
            else:
                print(f"❌ 事件上报失败")
            
            return success
            
        except Exception as e:
            print(f"❌ 事件上报异常: {e}")
            return False
    
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