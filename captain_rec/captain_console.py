# captain_console.py
"""
船长管理命令行工具
用法:
    python captain_console.py list          # 列出所有船长
    python captain_console.py add 张三       # 添加船长
    python captain_console.py remove 张三    # 移除船长
    python captain_console.py reload         # 重新加载
    python captain_console.py sync           # 从照片文件夹同步（标识_captain）
"""

import sys
import argparse
from pathlib import Path
from captain_manager import CaptainManager
import config

def main():
    parser = argparse.ArgumentParser(description='船长管理工具')
    parser.add_argument('command', choices=['list', 'add', 'remove', 'reload', 'sync'], 
                       help='操作命令')
    parser.add_argument('name', nargs='?', help='船长姓名（add/remove时需要）')
    
    args = parser.parse_args()
    
    # 初始化管理器
    manager = CaptainManager(config.Config.TRAIN_FOLDER, config.Config.CAPTAINS_FILE)
    
    if args.command == 'list':
        manager.print_info()
    
    elif args.command == 'add':
        if not args.name:
            print("❌ 请指定要添加的船长姓名")
            sys.exit(1)
        manager.add_captain(args.name)
        manager.print_info()
    
    elif args.command == 'remove':
        if not args.name:
            print("❌ 请指定要移除的船长姓名")
            sys.exit(1)
        manager.remove_captain(args.name)
        manager.print_info()
    
    elif args.command == 'reload':
        manager.reload()
        manager.print_info()
    
    elif args.command == 'sync':
        print("🔄 从照片文件夹同步（文件名包含 _captain 自动添加为船长）")
        # 这里会重新加载，自动识别 _captain 后缀
        manager.reload()
        manager.print_info()

if __name__ == "__main__":
    main()