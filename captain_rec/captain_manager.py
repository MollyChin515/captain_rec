# captain_manager.py
import json
import os
from pathlib import Path
from datetime import datetime
from typing import List, Set

class CaptainManager:
    """船长信息管理器 - 支持动态更新"""
    
    def __init__(self, train_folder: str, captains_file: str):
        self.train_folder = Path(train_folder)
        self.captains_file = Path(captains_file)
        self.captains: Set[str] = set()  # 船长姓名集合
        self._load_captains()
    
    def _load_captains(self):
        """加载船长名单（优先从配置文件，然后从文件夹同步）"""
        # 1. 尝试从配置文件加载
        if self.captains_file.exists():
            try:
                with open(self.captains_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self.captains = set(data.get('captains', []))
                print(f"📋 从配置文件加载船长名单: {len(self.captains)}人")
            except Exception as e:
                print(f"⚠️ 加载配置文件失败: {e}")
                self.captains = set()
        
        # 2. 从 train 文件夹同步（新增照片自动添加）
        self._sync_from_folder()
        
        # 3. 保存更新后的名单
        self._save_captains()
    
    def _sync_from_folder(self):
        """从 train 文件夹同步船长名单"""
        if not self.train_folder.exists():
            return
        
        # 获取所有图片文件名（不含扩展名）
        extensions = {'.jpg', '.jpeg', '.png', '.bmp'}
        folder_names = set()
        
        for ext in extensions:
            for f in self.train_folder.glob(f"*{ext}"):
                folder_names.add(f.stem)
            for f in self.train_folder.glob(f"*{ext.upper()}"):
                folder_names.add(f.stem)
        
        # 新照片默认不是船长，需要手动确认或通过标志文件识别
        # 方案1: 如果有 captains.json 则保留原有名单，新照片需要手动添加
        # 方案2: 通过文件名前缀 "_captain" 标识，如 "张三_captain.jpg"
        
        # 检查是否有带 _captain 后缀的照片
        auto_captains = {name.replace('_captain', '') for name in folder_names if '_captain' in name}
        
        if auto_captains:
            print(f"📷 发现自动标识的船长照片: {auto_captains}")
            self.captains.update(auto_captains)
        
        print(f"📁 训练文件夹中共有 {len(folder_names)} 张照片")
    
    def _save_captains(self):
        """保存船长名单到配置文件"""
        data = {
            'captains': list(self.captains),
            'last_updated': datetime.now().isoformat(),
            'total_count': len(self.captains)
        }
        
        with open(self.captains_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        
        print(f"💾 船长名单已保存: {self.captains_file} ({len(self.captains)}人)")
    
    def add_captain(self, name: str) -> bool:
        """添加船长"""
        if name not in self.captains:
            self.captains.add(name)
            self._save_captains()
            print(f"✅ 已添加船长: {name}")
            return True
        return False
    
    def remove_captain(self, name: str) -> bool:
        """移除船长"""
        if name in self.captains:
            self.captains.remove(name)
            self._save_captains()
            print(f"❌ 已移除船长: {name}")
            return True
        return False
    
    def is_captain(self, name: str) -> bool:
        """判断是否是船长"""
        return name in self.captains
    
    def get_all_captains(self) -> List[str]:
        """获取所有船长姓名列表"""
        return sorted(list(self.captains))
    
    def get_captain_count(self) -> int:
        """获取船长数量"""
        return len(self.captains)
    
    def reload(self):
        """重新加载船长名单"""
        print("🔄 重新加载船长名单...")
        self._load_captains()
    
    def print_info(self):
        """打印船长信息"""
        print("\n" + "="*50)
        print("👨‍✈️ 船长名单")
        print("="*50)
        if self.captains:
            for i, name in enumerate(sorted(self.captains), 1):
                print(f"  {i}. {name}")
        else:
            print("  ⚠️ 暂无船长，请添加船长照片或配置")
        print(f"\n总计: {len(self.captains)} 人")
        print("="*50)
    
    def get_unknown_employees(self, all_employees: List[str]) -> List[str]:
        """获取非船长的普通员工"""
        return [emp for emp in all_employees if emp not in self.captains]# config.py


