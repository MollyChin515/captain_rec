"""工作集配置管理器"""
import json
import argparse
import os


class WorkSetConfig:
    """工作集配置管理类
    
    负责读取和访问单个视频流的专用配置
    """
    
    def __init__(self, work_set_path: str = None):
        """初始化工作集配置
        
        Args:
            work_set_path: work_set.json文件路径，默认为Config/work_set.json
        """
        if work_set_path is None:
            work_set_path = os.path.join(
                os.path.dirname(__file__),
                "Config",
                "work_set.json"
            )
        
        self.config_path = work_set_path
        self._config = self._load_config()
    
    def _load_config(self) -> dict:
        """加载配置文件"""
        with open(self.config_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    
    def get_video_source(self) -> str:
        """获取视频流URL"""
        return self._config.get("rtsp_url", "")
    
    def get_camera_num(self) -> str:
        """获取摄像头编号"""
        return self._config.get("camera_num", "")
    
    def get_camera_locat(self) -> str:
        """获取摄像头位置描述"""
        return self._config.get("camera_locat", "")
    
    def get_event_code_absent(self) -> str:
        """获取缺勤事件编码"""
        return self._config.get("event_code_absent", "2-006")
    
    def get_event_name_absent(self) -> str:
        """获取缺勤事件名称"""
        return self._config.get("event_name_absent", "驾驶室离岗检测")
    
    def get_event_code_no_face(self) -> str:
        """获取无人脸事件编码"""
        return self._config.get("event_code_no_face", "2-006")
    
    def get_event_name_no_face(self) -> str:
        """获取无人脸事件名称"""
        return self._config.get("event_name_no_face", "驾驶室离岗检测")
    
    def get_upload_url(self) -> str:
        """获取上报URL"""
        return self._config.get("upload_url", "")
    
    def get_local_url(self) -> str:
        """获取本地接收端URL"""
        return self._config.get("local_url", "")
    
    def reload(self):
        """重新加载配置文件"""
        self._config = self._load_config()


def parse_work_set_args() -> str:
    """解析命令行参数，返回work_set文件路径
    
    使用方法:
        python main.py --work_set Config/work_set_1.json
    
    Returns:
        work_set文件路径
    """
    parser = argparse.ArgumentParser()
    parser.add_argument(
        '--work_set',
        type=str,
        default=None,
        help='工作集配置文件路径'
    )
    args = parser.parse_args()
    return args.work_set
