from pathlib import Path

class Config:
    # 路径配置
    TRAIN_FOLDER = "train_folder"              # 员工照片文件夹（文件名=员工姓名）
    DATABASE_FILE = "face_db.pkl"       # 人脸数据库文件
    CAPTAINS_FILE = "captains.json"     # 船长名单配置文件
    
    # 识别参数 
    THRESHOLD = 0.65                    # 人脸匹配阈值（0.65-0.75）
    DETECT_INTERVAL = 30                # 每隔多少帧检测一次（性能优化）
    
    # 在岗检查参数 
    CHECK_INTERVAL = 60                 # 检查间隔（秒）
    ABSENT_THRESHOLD = 5                # 连续多少次未检测到才算缺勤
    WARNING_COOLDOWN = 300              # 警告冷却时间（秒
    
    # 模型配置
    FACE_ANALYSIS_NAME = 'buffalo_l'
    USE_GPU = False                     # 是否使用GPU
    
    @classmethod
    def get_providers(cls):
        """获取推理后端"""
        if cls.USE_GPU:
            return ['CUDAExecutionProvider', 'CPUExecutionProvider']
        return ['CPUExecutionProvider']
    
    @classmethod
    def get_ctx_id(cls):
        """获取设备ID"""
        return 0 if cls.USE_GPU else -1
    
    @classmethod
    def ensure_directories(cls):
        """确保必要的文件夹存在"""
        Path(cls.TRAIN_FOLDER).mkdir(exist_ok=True)