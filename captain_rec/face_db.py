# face_db.py
import cv2
import pickle
import numpy as np
import hashlib
import json
import threading
from pathlib import Path
from datetime import datetime
from insightface.app import FaceAnalysis
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
import config


class PhotoFolderHandler(FileSystemEventHandler):
    """照片文件夹变化处理器"""
    
    def __init__(self, face_db):
        self.face_db = face_db
        self._debounce_timer = None
        self._lock = threading.Lock()
    
    def on_any_event(self, event):
        """任何文件变化事件"""
        # 只处理图片文件
        if event.is_directory:
            return
        if not event.src_path.lower().endswith(('.jpg', '.jpeg', '.png', '.bmp')):
            return
        
        # 防抖：延迟执行，避免频繁触发
        with self._lock:
            if self._debounce_timer:
                self._debounce_timer.cancel()
            self._debounce_timer = threading.Timer(2.0, self._do_update)
            self._debounce_timer.start()
    
    def _do_update(self):
        """执行更新"""
        print("\n🔄 检测到照片变化，正在更新数据库...")
        self.face_db._check_updates()
        print("✅ 数据库更新完成\n")


class FaceDatabase:
    
    def __init__(self):
        self.train_folder = Path(config.Config.TRAIN_FOLDER)
        self.db_file = config.Config.DATABASE_FILE
        self.employee_info_file = Path(__file__).parent / 'employee_info.json'
        self.external_employee_file = self.train_folder / 'employees.json'  # 外部导入的员工信息
        self.threshold = config.Config.THRESHOLD
        self.config = config.Config
        # 初始化模型
        self.app = FaceAnalysis(
            name=config.Config.FACE_ANALYSIS_NAME,
            providers=config.Config.get_providers()
        )
        self.app.prepare(ctx_id=config.Config.get_ctx_id())
        
        # 数据库
        self.embeddings = {}      # {employee_id: embedding}
        self.file_hashes = {}     # {filename: modify_time}
        self.employee_info = {}   # {employee_id: {'name': str, 'position': str}}
        
        # 文件监控
        self._observer = None
        
        # 加载员工信息
        self._load_employee_info()
        
        # 加载或构建数据库
        self._load_or_build()
    
    def _load_employee_info(self):
        """从外部JSON文件加载员工信息"""
        # 优先从外部导入的 employees.json 读取
        if self.external_employee_file.exists():
            try:
                with open(self.external_employee_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    # employees.json 格式: {"001张语晴": {"employee_id": "2", "name": "张语晴", "employee_number": "001", "position": "算法工程师", ...}}
                    for folder_name, emp_data in data.items():
                        employee_number = emp_data.get('employee_number', '')
                        employee_id = emp_data.get('employee_id', '')
                        if employee_number:
                            self.employee_info[employee_number] = {
                                'name': emp_data.get('name', ''),
                                'position': emp_data.get('position', '未知岗位'),
                                'employee_id': employee_id
                            }
                    print(f"📋 已从外部文件加载 {len(self.employee_info)} 名员工信息")
                    return
            except Exception as e:
                print(f"⚠️ 从外部文件加载员工信息失败: {e}")
        
        # 如果外部文件不存在，从缓存文件读取
        if self.employee_info_file.exists():
            try:
                with open(self.employee_info_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    # 将employees列表转换为字典，以employee_number为键
                    for emp in data.get('employees', []):
                        employee_number = emp.get('employee_number')
                        if employee_number:
                            self.employee_info[employee_number] = {
                                'name': emp.get('name', ''),
                                'position': emp.get('position', '未知岗位'),
                                'employee_id': emp.get('employee_id', '')
                            }
                print(f"📋 已从缓存加载 {len(self.employee_info)} 名员工信息")
            except Exception as e:
                print(f"⚠️ 加载员工信息失败: {e}")
    
    def _save_employee_info(self):
        """保存员工信息到JSON缓存文件"""
        try:
            employees_list = []
            for employee_number, info in self.employee_info.items():
                employees_list.append({
                    'employee_number': employee_number,
                    'name': info['name'],
                    'position': info['position'],
                    'employee_id': info.get('employee_id', '')
                })
            
            data = {
                'employees': employees_list,
                'last_updated': datetime.now().isoformat(),
                'total_count': len(employees_list)
            }
            
            with open(self.employee_info_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"⚠️ 保存员工信息失败: {e}")
    
    def _extract_embedding(self, image_path):
        img = cv2.imread(image_path)
        if img is None:
            return None
        
        faces = self.app.get(img)
        if len(faces) == 0:
            return None
        
        return faces[0].embedding
    
    def _compute_person_hash(self, photo_list):
        """
        计算某个人的所有照片的组合hash
        基于文件路径和修改时间
        """
        hash_str = ""
        for photo in sorted(photo_list, key=lambda x: str(x)):
            # 使用文件路径和修改时间生成hash
            mtime = photo.stat().st_mtime
            hash_str += f"{photo}:{mtime}"
        
        return hashlib.md5(hash_str.encode()).hexdigest()
    
    def _parse_folder_name(self, folder_name):
        """
        解析文件夹名称，提取工号和姓名
        文件夹格式: "工号姓名" 或 "工号_姓名" 或 "工号-姓名"
        例如: "001张三", "001_张三", "001-张三"
        """
        # 尝试不同的分隔符
        for sep in ['', '_', '-']:
            if sep:
                parts = folder_name.split(sep, 1)
                if len(parts) == 2:
                    employee_id, name = parts
                    return employee_id, name
        
        # 如果没有分隔符，尝试从开头提取数字作为工号
        import re
        match = re.match(r'^(\d+)(.+)$', folder_name)
        if match:
            employee_id = match.group(1)
            name = match.group(2)
            return employee_id, name
        
        # 无法解析，使用整个名称作为工号和姓名
        return folder_name, folder_name
    
    def _add_or_update_person(self, employee_id, name, position, photo_list, is_new=True):
        """
        添加或更新一个人员
        
        Args:
            employee_id: 员工工号
            name: 员工姓名
            position: 员工岗位
            photo_list: 照片列表
            is_new: 是否是新员工
        """
        embeddings = []
        valid_count = 0
        
        for photo in photo_list:
            embedding = self._extract_embedding(str(photo))
            if embedding is not None:
                embeddings.append(embedding)
                valid_count += 1
        
        if embeddings:
            # 计算平均特征向量
            avg_embedding = np.mean(embeddings, axis=0)
            self.embeddings[employee_id] = avg_embedding
            
            # 保存员工信息
            self.employee_info[employee_id] = {
                'name': name,
                'position': position,
                'employee_id': employee_id
            }
            
            # 计算该人的组合hash
            person_hash = self._compute_person_hash(photo_list)
            self.file_hashes[f"{employee_id}_folder"] = person_hash
            
            action = "已添加" if is_new else "已更新"
            print(f"  ✓ {action}: {employee_id}{name} - {position} ({valid_count}张照片)")
            return True
        else:
            print(f"  ⚠️ 未检测到人脸: {employee_id}{name}")
            return False
    
    def _get_image_files(self):
        """递归扫描所有子文件夹中的图片文件"""
        extensions = {'.jpg', '.jpeg', '.png', '.bmp'}
        files = []
        # 使用 **/*.jpg 递归扫描所有子文件夹
        for ext in extensions:
            files.extend(self.train_folder.glob(f"**/*{ext}"))
            files.extend(self.train_folder.glob(f"**/*{ext.upper()}"))
        return files
    
    def _load_or_build(self):
        if Path(self.db_file).exists():
            print(f"📁 加载已有数据库: {self.db_file}")
            try:
                with open(self.db_file, 'rb') as f:
                    data = pickle.load(f)
                    self.embeddings = data.get('embeddings', {})
                    self.file_hashes = data.get('file_hashes', {})
                    # 加载保存的员工信息（如果存在）
                    saved_employee_info = data.get('employee_info', {})
                    if saved_employee_info:
                        self.employee_info.update(saved_employee_info)
                print(f"✅ 已加载 {len(self.embeddings)} 名员工")
                self._check_updates()
                return
            except Exception as e:
                print(f"⚠️ 加载失败: {e}")
        
        # 构建新数据库
        self._build_database()
    
    def _check_updates(self):
        """检查更新，支持文件夹结构的增删检测和照片变化检测"""
        current_files = self._get_image_files()
        
        # 按人员分组当前所有照片
        current_persons = {}
        for f in current_files:
            if f.parent != self.train_folder:
                # 子文件夹：文件夹名格式为"工号姓名"
                folder_name = f.parent.name
                employee_id, name = self._parse_folder_name(folder_name)
                key = f"{employee_id}_folder"
            else:
                # 根目录文件：使用文件名
                employee_id, name = self._parse_folder_name(f.stem)
                key = f.name
            
            if key not in current_persons:
                current_persons[key] = {
                    'employee_id': employee_id,
                    'name': name,
                    'photos': []
                }
            current_persons[key]['photos'].append(f)
        
        # 检测新增的人员
        new_persons = []
        for key in current_persons.keys():
            if key not in self.file_hashes:
                new_persons.append(key)
        
        # 检测删除的人员
        deleted_persons = []
        for key in list(self.file_hashes.keys()):
            if key not in current_persons:
                deleted_persons.append(key)
        
        # 检测现有人员的照片变化
        updated_persons = []
        for key, person_data in current_persons.items():
            if key in self.file_hashes and key not in new_persons:
                # 计算当前照片的组合hash
                current_hash = self._compute_person_hash(person_data['photos'])
                if current_hash != self.file_hashes[key]:
                    updated_persons.append(key)
        
        # 处理新增人员
        if new_persons:
            total_photos = sum(len(current_persons[k]['photos']) for k in new_persons)
            print(f"📷 发现 {len(new_persons)} 个新人员，共 {total_photos} 张照片，正在添加...")
            for key in new_persons:
                person_data = current_persons[key]
                employee_id = person_data['employee_id']
                name = person_data['name']
                # 如果员工信息中已有该员工，使用保存的岗位；否则使用默认岗位
                position = self.employee_info.get(employee_id, {}).get('position', '未知岗位')
                self._add_or_update_person(employee_id, name, position, person_data['photos'], is_new=True)
        
        # 处理更新的人员（照片变化）
        if updated_persons:
            total_photos = sum(len(current_persons[k]['photos']) for k in updated_persons)
            print(f"🔄 检测到 {len(updated_persons)} 个人员的照片已变化，共 {total_photos} 张照片，正在重新计算...")
            for key in updated_persons:
                person_data = current_persons[key]
                employee_id = person_data['employee_id']
                name = person_data['name']
                position = self.employee_info.get(employee_id, {}).get('position', '未知岗位')
                self._add_or_update_person(employee_id, name, position, person_data['photos'], is_new=False)
        
        # 处理删除人员
        if deleted_persons:
            print(f"🗑️  检测到 {len(deleted_persons)} 个人员已删除，正在移除...")
            for key in deleted_persons:
                if key in self.file_hashes:
                    # 获取员工工号
                    if key.endswith("_folder"):
                        employee_id = key.replace("_folder", "")
                    else:
                        employee_id = Path(key).stem
                    
                    if employee_id in self.embeddings:
                        info = self.employee_info.get(employee_id, {})
                        name = info.get('name', employee_id)
                        del self.embeddings[employee_id]
                        if employee_id in self.employee_info:
                            del self.employee_info[employee_id]
                        print(f"  ✗ 已移除: {employee_id}{name}")
                    del self.file_hashes[key]
        
        if new_persons or updated_persons or deleted_persons:
            self._save()
            self._save_employee_info()
    
    def _add_new_faces(self, files):
        """处理新增的人脸照片，支持文件夹结构"""
        # 按文件夹分组
        folder_photos = {}
        for f in files:
            # 如果图片在子文件夹中，文件夹名格式为"工号姓名"
            if f.parent != self.train_folder:
                folder_name = f.parent.name
                employee_id, name = self._parse_folder_name(folder_name)
            else:
                employee_id, name = self._parse_folder_name(f.stem)
            
            key = employee_id
            if key not in folder_photos:
                folder_photos[key] = {
                    'employee_id': employee_id,
                    'name': name,
                    'photos': []
                }
            folder_photos[key]['photos'].append(f)
        
        # 对每个人处理他们的所有照片
        for key, person_data in folder_photos.items():
            employee_id = person_data['employee_id']
            name = person_data['name']
            position = self.employee_info.get(employee_id, {}).get('position', '未知岗位')
            self._add_or_update_person(employee_id, name, position, person_data['photos'], is_new=True)
    
    def _build_database(self):
        """构建数据库，支持文件夹结构"""
        if not self.train_folder.exists():
            print(f"⚠️ 训练文件夹不存在: {self.train_folder}")
            return
        
        files = self._get_image_files()
        if not files:
            print(f"⚠️ 训练文件夹中没有图片")
            return
        
        print(f"📷 发现 {len(files)} 张员工照片，正在构建数据库...")
        
        # 按文件夹分组
        folder_photos = {}
        for f in files:
            # 如果图片在子文件夹中，文件夹名格式为"工号姓名"
            if f.parent != self.train_folder:
                folder_name = f.parent.name
                employee_id, name = self._parse_folder_name(folder_name)
            else:
                employee_id, name = self._parse_folder_name(f.stem)
            
            key = employee_id
            if key not in folder_photos:
                folder_photos[key] = {
                    'employee_id': employee_id,
                    'name': name,
                    'photos': []
                }
            folder_photos[key]['photos'].append(f)
        
        # 对每个人处理他们的所有照片
        for key, person_data in folder_photos.items():
            employee_id = person_data['employee_id']
            name = person_data['name']
            position = self.employee_info.get(employee_id, {}).get('position', '未知岗位')
            self._add_or_update_person(employee_id, name, position, person_data['photos'], is_new=True)
        
        print(f"✅ 数据库构建完成，共 {len(self.embeddings)} 名员工")
        self._save()
        self._save_employee_info()
    
    def _save(self):
        data = {
            'embeddings': self.embeddings,
            'file_hashes': self.file_hashes,
            'employee_info': self.employee_info,
            'created_at': datetime.now().isoformat()
        }
        with open(self.db_file, 'wb') as f:
            pickle.dump(data, f)
        print(f"💾 数据库已保存: {self.db_file}")
    
    def recognize(self, face_embedding):
        """
        识别人脸
        
        Returns:
            tuple: (employee_id, name, position, similarity)
        """
        if not self.embeddings:
            return None, None, None, 0.0
        
        best_employee_id = None
        best_sim = 0.0
        
        for employee_id, emb in self.embeddings.items():
            # 余弦相似度
            sim = np.dot(face_embedding, emb) / (
                np.linalg.norm(face_embedding) * np.linalg.norm(emb)
            )
            
            if sim > best_sim:
                best_sim = sim
                best_employee_id = employee_id
        
        if best_sim >= self.threshold:
            # 获取员工信息
            info = self.employee_info.get(best_employee_id, {})
            name = info.get('name', best_employee_id)
            position = info.get('position', '未知岗位')
            return best_employee_id, name, position, best_sim
        return None, None, None, best_sim
    
    def get_all_employees(self):
        """获取所有员工信息"""
        employees = []
        for employee_id in self.embeddings.keys():
            info = self.employee_info.get(employee_id, {})
            employees.append({
                'employee_id': employee_id,
                'name': info.get('name', employee_id),
                'position': info.get('position', '未知岗位')
            })
        return employees
    
    def get_count(self):
        return len(self.embeddings)
    
    def start_watch(self):
        """启动文件夹监控"""
        if self._observer is not None:
            return
        self._observer = Observer()
        handler = PhotoFolderHandler(self)
        self._observer.schedule(handler, str(self.train_folder), recursive=True)
        self._observer.start()
        print(f"👀 已启动文件夹监控: {self.train_folder}")
    
    def stop_watch(self):
        """停止文件夹监控"""
        if self._observer is not None:
            self._observer.stop()
            self._observer.join()
            self._observer = None
            print("🛑 已停止文件夹监控")