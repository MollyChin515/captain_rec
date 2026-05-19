# face_db.py
import cv2
import pickle
import numpy as np
from pathlib import Path
from datetime import datetime
from insightface.app import FaceAnalysis
import config

class FaceDatabase:
    
    def __init__(self):
        self.train_folder = Path(config.Config.TRAIN_FOLDER)
        self.db_file = config.Config.DATABASE_FILE
        self.threshold = config.Config.THRESHOLD
        self.config = config.Config
        # 初始化模型
        self.app = FaceAnalysis(
            name=config.Config.FACE_ANALYSIS_NAME,
            providers=config.Config.get_providers()
        )
        self.app.prepare(ctx_id=config.Config.get_ctx_id())
        
        # 数据库
        self.embeddings = {}      # {name: embedding}
        self.file_hashes = {}     # {filename: modify_time}
        
        # 加载或构建数据库
        self._load_or_build()
    
    def _extract_embedding(self, image_path):
        img = cv2.imread(image_path)
        if img is None:
            return None
        
        faces = self.app.get(img)
        if len(faces) == 0:
            return None
        
        return faces[0].embedding
    
    def _get_image_files(self):
        extensions = {'.jpg', '.jpeg', '.png', '.bmp'}
        files = []
        for ext in extensions:
            files.extend(self.train_folder.glob(f"*{ext}"))
            files.extend(self.train_folder.glob(f"*{ext.upper()}"))
        return files
    
    def _load_or_build(self):
        if Path(self.db_file).exists():
            print(f"📁 加载已有数据库: {self.db_file}")
            try:
                with open(self.db_file, 'rb') as f:
                    data = pickle.load(f)
                    self.embeddings = data.get('embeddings', {})
                    self.file_hashes = data.get('file_hashes', {})
                print(f"✅ 已加载 {len(self.embeddings)} 名员工")
                self._check_updates()
                return
            except Exception as e:
                print(f"⚠️ 加载失败: {e}")
        
        # 构建新数据库
        self._build_database()
    
    def _check_updates(self):
        current_files = self._get_image_files()
        new_files = []
        
        for f in current_files:
            if f.name not in self.file_hashes:
                new_files.append(f)
        
        if new_files:
            print(f"📷 发现 {len(new_files)} 张新照片，正在更新数据库...")
            self._add_new_faces(new_files)
            self._save()
    
    def _add_new_faces(self, files):
        for f in files:
            name = f.stem  # 文件名作为员工姓名
            embedding = self._extract_embedding(str(f))
            
            if embedding is not None:
                self.embeddings[name] = embedding
                self.file_hashes[f.name] = f.stat().st_mtime
                print(f"  ✓ 已添加: {name}")
            else:
                print(f"  ⚠️ 未检测到人脸: {f.name}")
    
    def _build_database(self):
        if not self.train_folder.exists():
            print(f"⚠️ 训练文件夹不存在: {self.train_folder}")
            return
        
        files = self._get_image_files()
        if not files:
            print(f"⚠️ 训练文件夹中没有图片")
            return
        
        print(f"📷 发现 {len(files)} 张员工照片，正在构建数据库...")
        
        for f in files:
            name = f.stem
            embedding = self._extract_embedding(str(f))
            
            if embedding is not None:
                self.embeddings[name] = embedding
                self.file_hashes[f.name] = f.stat().st_mtime
                print(f"  ✓ 已加载: {name}")
            else:
                print(f"  ⚠️ 未检测到人脸: {f.name}")
        
        print(f"✅ 数据库构建完成，共 {len(self.embeddings)} 名员工")
        self._save()
    
    def _save(self):
        data = {
            'embeddings': self.embeddings,
            'file_hashes': self.file_hashes,
            'created_at': datetime.now().isoformat()
        }
        with open(self.db_file, 'wb') as f:
            pickle.dump(data, f)
        print(f"💾 数据库已保存: {self.db_file}")
    
    def recognize(self, face_embedding):
        if not self.embeddings:
            return None, 0.0
        
        best_name = None
        best_sim = 0.0
        
        for name, emb in self.embeddings.items():
            # 余弦相似度
            sim = np.dot(face_embedding, emb) / (
                np.linalg.norm(face_embedding) * np.linalg.norm(emb)
            )
            
            if sim > best_sim:
                best_sim = sim
                best_name = name
        
        if best_sim >= self.threshold:
            return best_name, best_sim
        return None, best_sim
    
    def get_all_employees(self):
        return list(self.embeddings.keys())
    
    def get_count(self):
        return len(self.embeddings)