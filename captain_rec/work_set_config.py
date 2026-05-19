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
    
    def get_event_code(self) -> str:
        """获取事件编码"""
        return self._config.get("event_code", "")
    
    def get_event_name(self) -> str:
        """获取事件名称"""
        return self._config.get("event_name", "")
    
    def get_receiver_url(self) -> str:
        """获取接收端URL"""
        return self._config.get("local_url_skills", "")
    
    def get_camera_num(self) -> str:
        """获取摄像头编号（从event_code提取）"""
        event_code = self.get_event_code()
        if '-' in event_code:
            return event_code.split('-')[0]
        return ""
    
    def get_camera_location(self) -> str:
        """获取摄像头位置（从event_name提取）"""
        return self.get_event_name()
    
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
