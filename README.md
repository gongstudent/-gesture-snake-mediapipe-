# 基于 MediaPipe + OpenCV 的交互贪吃蛇

## 环境与运行
- conda activate env_mediapipe
- pip install -r requirements.txt
- python main.py

## 主要文件
- main.py：入口，整合相机、手势检测与渲染
- config.py：统一配置（分辨率、颜色、手势常量）
- camera_manager.py：摄像头初始化与取帧
- hand_detector.py：手势检测（支持 solutions / tasks 后端），含边缘填充、ROI 回退、亮度增强
- snake_game.py：游戏逻辑（无尽模式、只记录分数）
- game_ui.py：UI 渲染（全屏模式、暂停居中分数）

## 控制说明
- 手指指向移动（显示十字准星）
- 按 q 第一次：暂停并居中显示分数
- 再次按 q：退出
- 按 r：重新开始

## 模型（可选）
- 若使用 MediaPipe Tasks Hand Landmarker：
  - 将 hand_landmarker.task 放在项目根目录或 models/ 目录下皆可
  - 在 config.py 设置 HAND_BACKEND = "TASKS"；TASKS_MODEL_PATH 可留空或自定义路径
  - pip 安装 mediapipe>=0.10.21

## 发行与忽略
- 见 .gitignore，已忽略二进制模型、缓存与生成文件
