# 🐍 交互手势贪吃蛇 (Gesture Snake MediaPipe)

**用手指“指向”控制贪吃蛇，实时摄像头交互零延迟！**

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![MediaPipe](https://img.shields.io/badge/MediaPipe-Solutions%2FTasks-orange)](https://developers.google.com/mediapipe)

> 💡 **提示**：建议在光线充足的环境下游玩，以获得最佳手势识别体验。

---

## 📺 演示效果

*(此处建议插入 15-30 秒的游戏演示 GIF，展示流畅的指尖控制与无尽模式体验)*

<!-- <img src="assets/demo.gif" width="600" alt="Game Demo"> -->

## 📸 游戏截图

| 游戏运行 | 暂停菜单 | 手势准星 |
|:---:|:---:|:---:|
| *(请补充运行截图)* | *(请补充暂停截图)* | *(请补充准星特写)* |
| <!-- <img src="assets/screenshot_game.jpg" width="200"> --> | <!-- <img src="assets/screenshot_pause.jpg" width="200"> --> | <!-- <img src="assets/screenshot_crosshair.jpg" width="200"> --> |

---

## 📖 项目简介

“交互手势贪吃蛇”是一款通过摄像头实时识别手势来控制贪吃蛇的轻量级 Python 游戏项目。不同于传统的键盘控制，本项目利用 MediaPipe 强大的手部关键点检测能力，实现了**指尖所指即蛇头移动**的直观交互体验。

游戏设计为**无尽模式**，没有生命限制，旨在挑战更高的分数。

### ✨ 特色亮点
- **零延迟手势交互**：指尖定位驱动蛇移动，顺滑跟手。
- **双后端支持**：兼容 MediaPipe Solutions (0.8.x) 与 MediaPipe Tasks (0.10+)。
- **边缘鲁棒性增强**：采用图像边缘填充、ROI 回退机制与 CLAHE 亮度增强，有效解决手部移出画面边缘时的抖动丢失问题。
- **沉浸式视觉体验**：全屏 UI 设计，抗锯齿蛇身连线，平滑尾部跟随算法。
- **简洁无尽玩法**：专注得分，OK 手势开始，Q 键暂停/退出。

---

## 🌐 Web 演示版 (无需安装)

本项目已提供纯前端移植版本，基于 MediaPipe JS 实现，**零延迟、免安装、即点即玩**！

### 在线体验
1. 本项目已配置 GitHub Pages 支持。
2. 直接访问项目的 GitHub Pages 地址即可（需在设置中开启）。
3. 或在本地进入 `docs/` 目录运行。

*(注：Web 版完全运行在本地浏览器中，不会上传任何视频数据)*

---

## 🚀 快速启动

### 1. 环境准备
确保已安装 Python 3.8+ 与 Conda（可选）。

```bash
# 创建虚拟环境
conda create -n env_mediapipe python=3.10
conda activate env_mediapipe

# 安装基础依赖
pip install -r requirements.txt
```

### 2. 运行游戏
```bash
python main.py
```

### 3. 一键体验 Tasks 后端（推荐）
如果你想体验更新、更稳的 MediaPipe Tasks 模型：

```bash
# 1. 安装新版依赖
pip install -r requirements.tasks.txt

# 2. 自动下载模型并运行
python download_model.py
python main.py
```
*(运行 `download_model.py` 会自动下载 `hand_landmarker.task` 并配置后端)*

---

## 📂 目录结构

```text
gesture-snake-mediapipe/
├── main.py                 # 程序入口：整合相机、检测与渲染
├── config.py               # 全局配置：分辨率、颜色、后端开关
├── camera_manager.py       # 摄像头管理：初始化与帧读取
├── hand_detector.py        # 核心检测：封装 Solutions/Tasks 双后端、鲁棒性增强算法
├── snake_game.py           # 游戏逻辑：状态机、无尽模式分数管理
├── game_ui.py              # UI渲染：全屏绘制、抗锯齿、信息HUD
├── mp_hands_wrapper.py     # 兼容层：适配旧版 MediaPipe 接口
├── download_model.py       # 脚本：自动下载 Tasks 模型
├── requirements.txt        # 基础依赖 (Solutions 后端)
├── requirements.tasks.txt  # 进阶依赖 (Tasks 后端)
├── README.md               # 项目文档
├── LICENSE                 # 开源许可证
├── models/                 # 模型存放目录
│   └── README.md
├── docs/                   # Web 演示版 (GitHub Pages)
│   ├── index.html
│   ├── script.js
│   └── style.css
└── assets/                 # 演示素材目录 (截图/GIF)
```

---

## 🎮 控制说明

- **移动**：伸出食指，屏幕会出现十字准星，蛇头将跟随准星移动。
- **开始**：对着摄像头做 👌 **OK 手势**。
- **暂停**：按下键盘 **`Q`** 键，屏幕居中显示当前分数。
- **退出**：在暂停状态下再次按下 **`Q`** 键。
- **重开**：游戏结束或暂停时，按下 **`R`** 键。

---

## 🗺️ 未来计划 (Roadmap)

- [ ] **多手势支持**：支持左/右手切换控制。
- [ ] **多人对战**：本地双人同屏竞技模式。
- [ ] **道具系统**：增加加速、减速、无敌等趣味道具。
- [x] **Web 移植**：使用 MediaPipe JS 移植到浏览器运行 (已完成)。

---

## 📄 License

本项目采用 [MIT License](LICENSE) 开源。欢迎 Fork 与 Star！🌟

---

## 🏷️ 关键词
`opencv` `mediapipe` `hand-tracking` `gesture-control` `snake-game` `computer-vision` `python`
