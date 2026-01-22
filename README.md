# 基于 MediaPipe + OpenCV 的交互贪吃蛇

## 项目简介
“交互手势贪吃蛇”是一款通过摄像头实时识别手势来控制贪吃蛇的轻量项目。指尖所指即蛇头移动，OK 手势开始游戏，按下 q 第一次暂停并在屏幕中央显示分数，再按 q 退出。项目支持 MediaPipe solutions 与 MediaPipe Tasks 两种后端，并针对边缘识别进行了鲁棒性增强（检测图像复制边缘填充、基于上帧的 ROI 回退、CLAHE 亮度增强），在大窗口全屏渲染下依然保持顺滑体验。游戏为无尽模式，只记录分数，不设上限。

### 特色亮点
- 实时手势控制（指尖定位驱动蛇移动）
- 双后端可选（solutions 0.8.x / tasks 0.10+），接口兼容
- 边缘鲁棒性增强（填充、ROI 回退、CLAHE），边界处识别更稳
- 全屏 UI 与抗锯齿连线，蛇尾平滑跟随
- 无尽模式，仅分数累计，玩法更简洁

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

## 关键词
- opencv, mediapipe, hand-tracking, gesture-control, snake, game, tasks, solutions
