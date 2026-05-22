# 船长在岗监控系统功能测试说明

基于人脸识别的船长在岗状态实时监控系统，当船长离开监控区域时自动发送告警。

## 功能特点

- 实时检测船长在岗状态
- 基于 InsightFace 的高精度人脸识别
- 灵活的配置参数（阈值、间隔、冷却时间）
- 支持 RTSP 视频流
- 告警时自动截图

## 快速开始

### 1. 环境安装

```bash
# 创建虚拟环境
python3 -m venv venv
source venv/bin/activate  # Linux/Mac

# 安装依赖
pip install -r requirements.txt
```

### 2. 上传船长照片

将船长照片放入 `train_folder/` 目录：

```
train_folder/
├── 张三.jpg
├── 李四.jpg
└── 王五.jpg
```

**说明：**
- 文件名即为船长姓名
- 无需任何特殊后缀或配置文件
- 支持格式：`.jpg`, `.jpeg`, `.png`, `.bmp`
- 建议照片清晰、正面、光照良好

### 3. 配置 RTSP 地址

编辑 `captain_rec/Config/work_set.json`：

  "rtsp_url": "rtsp://10.143.216.131:8554/usb_cam",


### 4. 运行程序

```bash
cd captain_rec
python main.py
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
人脸数据库（train_folder/） → 只包含船长照片
              ↓
        实时人脸识别
              ↓
   识别到任何人 → 都是船长 ✓
   未识别到人   → 船长缺勤  ⚠️
```

### 告警触发条件

1. 连续 `ABSENT_THRESHOLD` 次（默认5次）未检测到船长
2. 且已过告警冷却时间（默认300秒）

### 状态流程

```
检测到船长 → is_captain_detected = True → 重置计数器
连续未检测 → absent_counter++ → 达到阈值 → 触发告警
```

## 常见问题

### Q1: 如何添加新的船长？

直接将照片放入 `train_folder/`，文件名为船长姓名。

### Q2: RTSP 连接超时怎么办？

1. 检查网络连通性：`ping <RTSP_IP>`
2. 测试视频流：`ffplay <rtsp_url>`
3. 检查 RTSP 服务是否运行
4. 调整 `config.py` 中的 `CAP_PROP_FPS` 参数

### Q3: 如何调整识别灵敏度？

修改 `config.py` 中的 `THRESHOLD` 值：
- 增大：提高识别率，但可能误识别
- 减小：降低误识别，但可能漏检

### Q4: 如何测试程序功能？

1. 准备测试视频或 RTSP 流
2. 上传测试照片到 `train_folder/`
3. 运行程序，观察控制台输出
4. 检查告警日志和截图

## 技术栈

- **人脸识别**: InsightFace + ONNX Runtime
- **视频处理**: OpenCV
- **配置管理**: JSON
- **告警**: HTTP POST 请求


## 注意事项

1. **照片质量**: 确保照片清晰、正面、光照良好
2. **网络稳定**: RTSP 流需要稳定的网络环境
3. **告警配置**: 确保 `local_url_skills` 服务器正常运行
4. **性能优化**: 根据服务器性能调整 `DETECT_INTERVAL`
