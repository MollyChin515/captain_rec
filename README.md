# 驾驶台值班人员监控系统

基于人脸识别的驾驶台值班人员实时监控系统，当值班人员离开监控区域时自动发送告警。

## 功能特点

- 实时检测驾驶台值班人员在岗状态
- 支持多岗位人员监控（船长、大副、二副、三副等）
- 基于 InsightFace 的高精度人脸识别
- 每人支持多张照片特征融合，提高识别准确率
- 灵活的配置参数（阈值、间隔、冷却时间）
- 支持 RTSP 视频流和本地摄像头
- 告警时自动截图保存，支持中文标注
- 截图包含摄像头编号、位置、时间等详细信息

## 快速开始

### 1. 环境安装

```bash
# 创建虚拟环境
python3 -m venv venv
source venv/bin/activate  # Linux/Mac

# 安装依赖
pip install -r requirements.txt

# 安装中文字体（用于截图标注）
sudo apt-get install fonts-wqy-microhei  # Ubuntu/Debian
# 或
sudo yum install wqy-microhei-fonts      # CentOS/RHEL
```

**字体说明：**
- 系统会自动查找 `captain_rec/fonts/wqy-microhei.ttf` 字体文件
- 如果字体文件不存在，截图标注将使用 OpenCV 默认字体（不支持中文）

### 2. 导入值班人员数据

值班人员照片和岗位信息由外部程序导入到 `train_folder/` 目录：

```
train_folder/
├── employees.json           # 员工完整信息（自动生成）
├── positions.json           # 岗位代码映射（自动生成）
├── employee_numbers.json    # 员工ID映射（自动生成）
├── 001张语晴/               # 文件夹：工号+姓名
│   ├── photo1.jpg
│   └── photo2.jpeg
└── 002李四/
    └── photo1.jpg
```

**自动生成的配置文件：**

`employees.json` - 员工完整信息：
```json
{
  "001张语晴": {
    "employee_id": "2",
    "name": "张语晴",
    "employee_number": "001",
    "position": "算法工程师",
    "position_code": "00001",
    "photos": [
      {"filename": "photo1.jpg", "upload_time": "2026-06-15T13:57:08"},
      {"filename": "photo2.jpeg", "upload_time": "2026-06-15T13:57:20"}
    ]
  }
}
```

`positions.json` - 岗位代码映射：
```json
{
  "算法工程师": "00001",
  "船长": "00002",
  "大副": "00003"
}
```

**说明：**
- 文件夹名格式：`工号姓名`（如 `001张语晴`）
- 支持格式：`.jpg`, `.jpeg`, `.png`, `.bmp`
- 多张照片会自动融合特征，提高识别准确率
- 员工信息由外部程序管理，无需手动配置

### 4. 配置视频源

编辑 `captain_rec/Config/work_set.json`：

```json
{
  "rtsp_url": "rtsp://10.143.216.131:8554/usb_cam",
  "event_code": "CAM001-驾驶台",
  "event_name": "驾驶台监控",
  "local_url_skills": "http://your-server/alert"
}
```

**视频源配置：**
- RTSP 流：`rtsp://ip:port/stream`
- 本地摄像头：`0`（默认摄像头）
- 视频文件：`/path/to/video.mp4`

### 5. 运行程序

```bash
cd captain_rec
python main.py
```

**指定配置文件运行：**

```bash
python main.py --work_set Config/work_set_2.json
```

## 配置说明

### 核心参数（`config.py`）

| 参数 | 默认值 | 说明 |
|------|--------|------|
| `THRESHOLD` | 0.65 | 人脸识别相似度阈值（0-1） |
| `DETECT_INTERVAL` | 30 | 检测间隔（帧数），降低CPU占用 |
| `ABSENT_THRESHOLD` | 5 | 连续未检测到N次触发告警 |
| `WARNING_COOLDOWN` | 300 | 告警冷却时间（秒） |

### 工作集配置（`Config/work_set.json`）

| 字段 | 说明 |
|------|------|
| `rtsp_url` | RTSP 视频流地址 |
| `event_code` | 告警事件代码 |
| `event_name` | 告警事件名称 |
| `local_url_skills` | 告警接收服务器地址 |

## 监控逻辑

### 核心原理

```
人脸数据库（train_folder/） → 包含所有值班人员照片
              ↓
        实时人脸识别
              ↓
   识别到值班人员 → 在岗 ✓
   未识别到人员   → 缺勤 ⚠️
   识别到陌生人   → 未授权人员 ⚠️
```

### 告警触发条件

1. 连续 `ABSENT_THRESHOLD` 次（默认5次）未检测到值班人员
2. 且已过告警冷却时间（默认300秒）

### 状态流程

```
检测到值班人员 → 重置计数器
连续未检测     → absent_counter++ → 达到阈值 → 触发告警
检测到陌生人   → 记录日志（不触发告警）
```

### 多照片特征融合

系统支持为每个人上传多张照片，自动融合特征：

- **简单平均**：所有照片特征向量取平均
- **加权平均**：根据人脸检测质量（det_score）加权平均
- **优势**：提高识别准确率，适应不同光照、角度

## 常见问题

### Q1: 如何添加新的值班人员？

通过外部程序导入员工信息和照片到 `train_folder/`，系统会自动检测并更新数据库。

### Q2: 如何更新人员照片？

通过外部程序添加或删除照片，系统会自动检测变化并更新数据库。

### Q3: RTSP 连接超时怎么办？

1. 检查网络连通性：`ping <RTSP_IP>`
2. 测试视频流：`ffplay <rtsp_url>`
3. 检查 RTSP 服务是否运行
4. 调整 `config.py` 中的 `CAP_PROP_FPS` 参数

### Q4: 如何调整识别灵敏度？

修改 `config.py` 中的 `THRESHOLD` 值：
- 增大（如 0.70）：降低误识别，但可能漏检
- 减小（如 0.60）：提高识别率，但可能误识别

### Q5: 多张照片如何提高识别准确率？

系统会自动融合多张照片的特征：
- 覆盖不同光照条件
- 覆盖不同拍摄角度
- 提高特征向量的代表性

### Q6: 员工信息存储在哪里？

员工信息存储在 `train_folder/employees.json`，由外部程序管理，包含：
- 员工ID、姓名、工号
- 岗位信息和岗位代码
- 照片列表和上传时间

## 技术栈

- **人脸识别**: InsightFace + ONNX Runtime
- **视频处理**: OpenCV
- **配置管理**: JSON
- **告警**: HTTP POST 请求

## 项目结构

```
captain_rec/
├── main.py              # 程序入口
├── config.py            # 全局配置
├── face_db.py           # 人脸数据库管理
├── recognizer.py        # 人脸识别器
├── monitor.py           # 在岗监控器
├── alert_manager.py     # 告警管理器（支持中文截图标注）
├── attendance_system.py # 考勤系统主类
├── work_set_config.py   # 工作集配置管理
├── utils.py             # 工具函数
├── employee_info.json    # 员工岗位信息缓存
├── Config/
│   └── work_set.json    # 工作集配置
├── fonts/               # 中文字体文件目录
│   └── wqy-microhei.ttf # 文泉驿微米黑字体
├── train_folder/        # 员工照片目录（外部程序导入）
│   ├── employees.json       # 员工完整信息
│   ├── positions.json       # 岗位代码映射
│   ├── employee_numbers.json # 员工ID映射
│   └── 001张语晴/           # 员工照片文件夹
├── screenshots/         # 告警截图保存
└── uploads/             # 上传文件目录
```

## 注意事项

1. **数据导入**: 员工照片和信息由外部程序导入到 `train_folder/`，请勿手动修改
2. **照片质量**: 确保照片清晰、正面、光照良好，建议每人 2-3 张照片
3. **网络稳定**: RTSP 流需要稳定的网络环境
4. **告警配置**: 确保 `local_url_skills` 服务器正常运行
5. **性能优化**: 根据服务器性能调整 `DETECT_INTERVAL`
6. **隐私保护**: 照片和特征数据仅用于值班监控，请妥善保管
7. **中文字体**: 截图标注需要中文字体支持，请确保 `captain_rec/fonts/wqy-microhei.ttf` 存在

## 截图标注说明

告警截图会自动添加中文标注信息，包括：

- 🚨 **告警类型**: "值班人员未在岗" 或 "未检测到人脸"
- 📍 **摄像头编号**: 从配置文件读取
- 📍 **位置信息**: 从配置文件读取
- ⏰ **时间戳**: 告警发生的具体时间

标注采用半透明黑色背景框，确保文字在各种背景下都清晰可见。
