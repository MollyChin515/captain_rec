import cv2
import signal
import os
from face_db import FaceDatabase
from recognizer import FaceRecognizer
from alert_manager import AlertManager
from monitor import AttendanceMonitor
import config


class AttendanceSystem:
    
    def __init__(self, work_set_name="Config/work_set.json"):
        print("="*60)
        print("船长在岗监控系统 v1.0")
        print("="*60)
        
        # 加载工作集配置
        from work_set_config import WorkSetConfig
        self.work_set_config = WorkSetConfig(work_set_name)
        
        # 初始化模块
        print("\n🔧 正在初始化系统...")
        self.db = FaceDatabase()
        self.recognizer = FaceRecognizer(self.db)
        
        # 创建告警管理器时传入工作集配置
        self.alert_manager = AlertManager(
            absent_threshold=config.Config.ABSENT_THRESHOLD,
            warning_cooldown=config.Config.WARNING_COOLDOWN,
            work_set_config=self.work_set_config  # 传入工作集配置
        )
        
        self.monitor = AttendanceMonitor(self.recognizer, self.alert_manager)
        
        self.running = True
        
        # 打印信息
        self._print_info()
        
        # 设置信号处理器
        signal.signal(signal.SIGINT, self._signal_handler)
    
    def _print_info(self):
        """打印系统信息"""
        captain_count = self.db.get_count()
        print(f"\n船长数据库: {captain_count} 张照片")
        print(f"识别阈值: {config.Config.THRESHOLD}")
        print(f"告警阈值: 连续 {config.Config.ABSENT_THRESHOLD} 次未检测到船长")
        print(f"冷却时间: {config.Config.WARNING_COOLDOWN} 秒 (避免重复告警)")
        print(f"截图保存目录: screenshots/")
    
    def _signal_handler(self, sig, frame):
        """处理Ctrl+C"""
        print("\n\n🛑 正在停止系统...")
        self.running = False
    
    def _open_video_source(self):
        """打开视频源"""
        source = self.work_set_config.get_video_source()
        
        if source == "0" or source == 0:
            print("正在打开摄像头...")
            cap = cv2.VideoCapture(0)
        else:
            print(f"正在打开视频流: {source}")
            cap = cv2.VideoCapture(source)
        
        if not cap.isOpened():
            print(f"无法打开视频源: {source}")
            return None
        
        return cap
    
    def _print_final_summary(self):
        """打印最终总结"""
        print("\n" + "="*60)
        print("📊 最终报告")
        print("="*60)
        
        summary = self.monitor.get_summary()
        
        if summary['is_captain_detected']:
            print(f"\n✅ 最终状态: 船长在岗")
        else:
            print(f"\n❌ 最终状态: 船长缺勤")
            print(f"   连续未检测次数: {summary['absent_counter']}")
        
        if summary['has_alerted']:
            print(f"⚠️  已发送缺勤告警")
        
        print(f"📸 截图保存位置: screenshots/")
        print("="*60)
    
    def run(self):
        """运行主循环"""
        # 检查是否有船长数据
        if self.db.get_count() == 0:
            print("\n❌ 错误: 没有船长照片！")
            print(f"请将船长照片放入 '{config.Config.TRAIN_FOLDER}' 文件夹")
            return
        
        # 打开视频源
        cap = self._open_video_source()
        if cap is None:
            return
        
        # 获取视频信息
        fps = cap.get(cv2.CAP_PROP_FPS)
        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        
        print(f"\n开始监控")
        print(f"视频信息: {total_frames} 帧, {fps:.1f} fps")
        print(f"告警条件: 连续 {config.Config.ABSENT_THRESHOLD} 次未检测到船长")
        print(f"⏹️按 Ctrl+C 停止程序")
        print("-"*50)
        
        frame_count = 0
        
        # 设置无头模式
        os.environ['QT_QPA_PLATFORM'] = 'offscreen'
        
        try:
            while self.running:
                ret, frame = cap.read()
                if not ret:
                    print("视频结束，重新开始...")
                    cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
                    self.monitor.reset_frame_counter()
                    continue
                
                frame_count += 1
                
                # 处理帧
                is_captain = self.monitor.process_frame(
                    frame, 
                    detect_interval=config.Config.DETECT_INTERVAL
                )
                
                # 定期打印状态
                self.monitor.print_status()
                
                # 进度显示（每100帧）
                if frame_count % 100 == 0:
                    captain_status = "✅ 在岗" if is_captain else "❌ 缺勤"
                    print(f"📊 进度: {frame_count}/{total_frames} 帧 | 船长: {captain_status}")
                
        except KeyboardInterrupt:
            print("\n\n👋 用户中断")
        finally:
            cap.release()
            self._print_final_summary()
