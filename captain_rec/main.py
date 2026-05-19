# main.py
import config
from attendance_system import AttendanceSystem
from work_set_config import parse_work_set_args


def main():
    """主函数"""
    config.Config.ensure_directories()
    
    # 解析命令行参数
    work_set_path = parse_work_set_args()
    if work_set_path:
        print(f"📂 使用工作集配置: {work_set_path}")
    else:
        work_set_path = "Config/work_set.json"
        print(f"📂 使用默认工作集配置: {work_set_path}")
    
    system = AttendanceSystem(work_set_path)
    system.run()


if __name__ == "__main__":
    main()