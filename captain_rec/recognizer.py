# recognizer.py
import cv2
import numpy as np
from face_db import FaceDatabase

class FaceRecognizer:
    """人脸识别器"""
    
    def __init__(self, database):
        self.db = database
        self.app = database.app  # 复用模型
    
    def detect_and_recognize(self, frame):
        """检测并识别帧中的所有脸，返回识别结果列表"""
        faces = self.app.get(frame)
        results = []
        
        for face in faces:
            bbox = face.bbox.astype(int)
            employee_id, name, position, similarity = self.db.recognize(face.embedding)
            
            results.append({
                'bbox': bbox,
                'employee_id': employee_id,
                'name': name,
                'position': position,
                'similarity': similarity,
                'is_recognized': employee_id is not None
            })
        
        return results
    
    def draw_results(self, frame, results):
        """在帧上绘制识别结果"""
        for r in results:
            bbox = r['bbox']
            
            if r['is_recognized']:
                color = (0, 255, 0)  # 绿色 - 识别成功
                label = f"{r['position']}: {r['employee_id']}{r['name']} ({r['similarity']:.2f})"
            else:
                color = (0, 0, 255)  # 红色 - 未识别
                label = f"Unknown ({r['similarity']:.2f})"
            
            # 绘制框
            cv2.rectangle(frame, (bbox[0], bbox[1]), (bbox[2], bbox[3]), color, 2)
            
            # 绘制标签
            label_size = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, 0.6, 2)[0]
            cv2.rectangle(frame, 
                        (bbox[0], bbox[1] - label_size[1] - 10),
                        (bbox[0] + label_size[0], bbox[1]),
                        color, -1)
            cv2.putText(frame, label, (bbox[0], bbox[1] - 5),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)
        
        return frame
