# 🐍 交互手势贪吃蛇 (Gesture Snake MediaPipe)

**用手指“指向”控制贪吃蛇，实时摄像头交互零延迟！**
**Control the Snake with your finger "pointing", real-time camera interaction with zero latency!**

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![MediaPipe](https://img.shields.io/badge/MediaPipe-Solutions%2FTasks-orange)](https://developers.google.com/mediapipe)

> 💡 **提示**：建议在光线充足的环境下游玩，以获得最佳手势识别体验。
> 💡 **Tip**: Playing in a well-lit environment is recommended for the best gesture recognition experience.

---


## 📖 项目简介 (Introduction)

“交互手势贪吃蛇”是一款通过摄像头实时识别手势来控制贪吃蛇的轻量级 Python 游戏项目。不同于传统的键盘控制，本项目利用 MediaPipe 强大的手部关键点检测能力，实现了**指尖所指即蛇头移动**的直观交互体验。

"Gesture Snake" is a lightweight Python game project that controls a snake by recognizing hand gestures in real-time through a camera. Unlike traditional keyboard controls, this project leverages MediaPipe's powerful hand landmark detection to achieve an intuitive interaction where **the snake head moves exactly where your fingertip points**.

游戏设计为**无尽模式**，没有生命限制，旨在挑战更高的分数。
The game is designed as an **Endless Mode** with no life limits, aiming to challenge for higher scores.

### ✨ 特色亮点 (Features)
- **🌐 现代化 Web 架构 (Modern Web Architecture)**：前后端分离，Flask + SocketIO 后端，Glassmorphism UI 前端。 (Separated backend and frontend, Flask + SocketIO backend, Glassmorphism UI frontend.)
- **🎨 玻璃拟态设计 (Glassmorphism UI)**：半透明深色卡片，毛玻璃效果，流畅动画。 (Semi-transparent dark cards, frosted glass effects, smooth animations.)
- **⚡ 零延迟手势交互 (Zero-Latency Interaction)**：指尖定位驱动蛇移动，顺滑跟手。 (Fingertip positioning drives snake movement, smooth and responsive.)
- **🔧 双后端支持 (Dual Backend Support)**：兼容 MediaPipe Solutions (0.8.x) 与 MediaPipe Tasks (0.10+)。 (Compatible with both MediaPipe Solutions and Tasks.)
- **🎯 边缘鲁棒性增强 (Enhanced Edge Robustness)**：采用图像边缘填充、ROI 回退机制与 CLAHE 亮度增强。 (Uses image padding, ROI fallback, and CLAHE brightness enhancement.)
- **🎮 简洁无尽玩法 (Simple Endless Gameplay)**：专注得分，OK 手势开始，👊 握拳暂停。 (Focus on scoring, OK gesture to start, fist to pause.)

---

## 🌐 Web 架构说明 (Web Architecture)

本项目已重构为**现代 Web 应用架构**，实现 UI 层与 Python 逻辑层的完全分离。

### 核心核心 (Core Features)
- **后端 (Backend)**: Flask + Flask-SocketIO 负责视频流处理和游戏逻辑。
- **前端 (Frontend)**: HTML5 Canvas + Glassmorphism CSS + Socket.IO Client 负责 UI 渲染。
- **通信 (Communication)**: WebSocket 实时推送游戏状态 (60 FPS)，MJPEG 流传输视频背景。

### 架构优势 (Architecture Benefits)
| 特性 | OpenCV 原版 | Web 版 |
|------|------------|--------|
| **UI 渲染** | 锯齿严重，受限于 `cv2.putText` | **高清平滑**，浏览器原生渲染 |
| **设计风格** | 简陋，仅基本线条 | **Glassmorphism** 玻璃拟态，渐变光效 |
| **动画效果** | 无 | **流畅过渡**，CSS 脉冲/呼吸特效 |
| **解耦** | UI与逻辑强耦合 | **前后端分离**，易于维护和扩展 |

### 技术栈 (Tech Stack)
- **依赖 (Deps)**: `Flask`, `Flask-SocketIO`, `Flask-CORS`, `eventlet`, `opencv-python`, `mediapipe`
- **前端 (Web)**: Vanilla JS, Socket.IO Client, HTML5, CSS3 Variables


---

## 🌐 Web 演示版 (Web Demo - No Install)

本项目已提供纯前端移植版本，基于 MediaPipe JS 实现，**零延迟、免安装、即点即玩**！
This project provides a pure frontend ported version based on MediaPipe JS. **Zero latency, no installation, play instantly!**

### 在线体验 (Play Online)
1. 本项目已配置 GitHub Pages 支持。 (GitHub Pages is configured.)
2. 直接访问项目的 GitHub Pages 地址即可。 (Visit the project's GitHub Pages link directly.)

*(注：Web 版完全运行在本地浏览器中，不会上传任何视频数据)*
*(Note: The Web version runs entirely in your local browser and does not upload any video data.)*

---

## 🚀 快速启动 (Quick Start)

### 1. 环境准备 (Prerequisites)
确保已安装 Python 3.8+。
Ensure Python 3.8+ is installed.

```bash
# 创建虚拟环境 (Create virtual environment)
conda create -n env_mediapipe python=3.10
conda activate env_mediapipe

# 安装所有依赖 (Install all dependencies)
pip install -r requirements.txt
```

### 2. 运行游戏 (Run Game)

**方式一：使用启动脚本 (Windows)**
```bash
start_web.bat
```

**方式二：命令行 (Command Line)**
```bash
python app.py
```

启动后，在浏览器访问：**http://localhost:5000**

### 3. 一键体验 Tasks 后端（可选）(Try Tasks Backend - Optional)
如果你想体验更新、更稳的 MediaPipe Tasks 模型：
If you want to experience the newer, more stable MediaPipe Tasks model:

```bash
# 1. 安装新版依赖 (Install new dependencies)
# 注意：tasks 依赖已包含在 requirements.txt 中，无需额外安装
# Note: tasks dependencies are already included in requirements.txt

# 2. 自动下载模型并运行 (Download model and run)
python download_model.py
python app.py
```
*(运行 `download_model.py` 会自动下载 `hand_landmarker.task` 并配置后端)*
*(Running `download_model.py` will automatically download `hand_landmarker.task` and configure the backend.)*

---

## 📂 目录结构 (Directory Structure)

```text
gesture-snake-mediapipe/
├── app.py                  # Flask Web 应用入口 (Web application entry)
├── static/
│   └── index.html          # 前端页面 (Frontend page with Glassmorphism UI)
├── config.py               # 全局配置：分辨率、颜色、后端开关 (Configuration)
├── camera_manager.py       # 摄像头管理：初始化与帧读取 (Camera management)
├── hand_detector.py        # 核心检测：封装 Solutions/Tasks 双后端、鲁棒性增强算法 (Core detection)
├── snake_game.py           # 游戏逻辑：状态机、无尽模式分数管理 (Game logic)
├── mp_hands_wrapper.py     # 兼容层：适配旧版 MediaPipe 接口 (Compatibility layer)
├── download_model.py       # 脚本：自动下载 Tasks 模型 (Model downloader)
├── start_web.bat           # Windows 快速启动脚本 (Quick start script for Windows)
├── requirements.txt        # 所有依赖（含 Web）(All dependencies including web)
├── requirements.tasks.txt  # Tasks 后端依赖 (Tasks backend deps)
├── README.md               # 项目文档 (Documentation)
├── README_WEB.md           # Web 版详细说明 (Web version guide)
├── LICENSE                 # 开源许可证 (License)
├── models/                 # 模型存放目录 (Model directory)
│   └── README.md
├── docs/                   # Web 演示版 (GitHub Pages) (Web Demo)
│   ├── index.html
│   ├── script.js
│   └── style.css
└── assets/                 # 演示素材目录 (截图/GIF) (Assets)
```

---

## 🎮 控制说明 (Controls)

- **移动 (Move)**：伸出食指指向屏幕，蛇头将跟随手指移动。 (Point with your index finger; the snake follows your fingertip.)
- **开始 (Start)**：对着摄像头做 👌 **OK 手势**。 (Make an 👌 **OK gesture** to the camera.)
- **暂停 (Pause)**：👊 **握拳**暂停游戏，显示当前分数。 (👊 **Fist** to pause; score is shown.)
- **恢复 (Resume)**：暂停时再做 👌 **OK 手势**恢复游戏。 (Make 👌 **OK gesture** again while paused to resume.)

- **重开 (Restart)**：游戏结束时，按下 **`R`** 键或做 👌 **OK 手势**重新开始。 (Press **`R`** key or make 👌 **OK gesture** when game over to restart.)

---

## 🗺️ 未来计划 (Roadmap)

- [ ] **多手势支持**：支持左/右手切换控制。 (Multi-gesture support: Left/Right hand switching.)
- [ ] **多人对战**：本地双人同屏竞技模式。 (Multiplayer: Local co-op/competitive mode.)
- [ ] **道具系统**：增加加速、减速、无敌等趣味道具。 (Item system: Speed up, slow down, invincibility.)
- [x] **Web 移植**：使用 MediaPipe JS 移植到浏览器运行 (已完成)。 (Web port: Ported to browser using MediaPipe JS - Completed.)

---

## 📄 License

本项目采用 [MIT License](LICENSE) 开源。欢迎 Fork 与 Star！🌟
This project is open-sourced under the [MIT License](LICENSE). Fork and Star are welcome! 🌟

---

## 🏷️ 关键词 (Keywords)
`opencv` `mediapipe` `hand-tracking` `gesture-control` `snake-game` `computer-vision` `python`
