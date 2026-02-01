from flask import Flask, render_template, Response, send_from_directory
from flask_socketio import SocketIO, emit
from flask_cors import CORS
import cv2
import time
import threading
import config
from camera_manager import CameraManager
from hand_detector import HandDetector
from snake_game import SnakeGame

app = Flask(__name__, static_folder='static', template_folder='static')
app.config['SECRET_KEY'] = 'gesture-snake-secret-key'
CORS(app)
socketio = SocketIO(app, cors_allowed_origins="*", async_mode='threading')

# 全局游戏实例
camera = None
detector = None
game = None
game_thread = None
is_running = False

def initialize_game():
    """初始化游戏组件"""
    global camera, detector, game
    
    print("正在初始化游戏组件...")
    camera = CameraManager()
    if not camera.start():
        print("启动摄像头失败！")
        return False
    
    detector = HandDetector()
    detector.start()
    
    game = SnakeGame()
    print("游戏组件初始化完成")
    return True

def generate_frames():
    """生成视频帧（MJPEG 流）"""
    global camera, detector, game, is_running
    
    prev_time = 0
    
    while is_running and camera is not None:
        frame = camera.read_frame()
        if frame is None:
            if not is_running:
                break
            continue
        
        # 手势检测
        detector.update_frame(frame)
        results, gesture = detector.get_results()
        finger_pos = detector.get_finger_position()
        
        # 可视化手部关键点（可选）
        if config.GESTURE_CONFIDENCE_THRESHOLD > 0:
            detector.draw_landmarks(frame, results)
        
        # 绘制手指准星
        if finger_pos and game.state == "RUNNING":
            fx = int(finger_pos[0] * config.CAMERA_WIDTH)
            fy = int(finger_pos[1] * config.CAMERA_HEIGHT)
            # 简单的准星（前端也会绘制，这里仅用于调试）
            # cv2.circle(frame, (fx, fy), 10, (0, 255, 255), 2)
        
        # FPS 显示
        curr_time = time.time()
        fps = 1 / (curr_time - prev_time) if prev_time > 0 else 0
        prev_time = curr_time
        cv2.putText(frame, f"FPS: {int(fps)}", (10, 30), 
                   cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
        
        # 编码为 JPEG
        ret, buffer = cv2.imencode('.jpg', frame, [cv2.IMWRITE_JPEG_QUALITY, 85])
        if not ret:
            continue
        
        frame_bytes = buffer.tobytes()
        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + frame_bytes + b'\r\n')

def game_loop():
    """游戏逻辑主循环（独立线程）"""
    global game, detector, socketio
    
    q_pressed_once = False
    
    print("游戏循环已启动")
    print("控制：用手指指向移动 | OK手势开始游戏 | R键重新开始 | Q键暂停/退出")
    
    while is_running:
        if game is None or detector is None:
            time.sleep(0.1)
            continue
        
        # 获取手势信息
        results, gesture = detector.get_results()
        finger_pos = detector.get_finger_position()
        
        # 处理暂停状态下OK手势恢复游戏
        if game.state == "PAUSED" and gesture == "RESTART":  # OK手势
            game.resume_game()
            q_pressed_once = False
            print("游戏已恢复！")
        
        # 如果检测到手指，更新目标位置
        if finger_pos and game.state == "RUNNING":
            game.set_target_position(finger_pos[0], finger_pos[1])
        
        game.process_gesture(gesture)
        game.update()
        
        # 发送游戏状态到前端
        game_state = {
            'state': game.state,
            'score': game.score,
            'snake': [(x/config.CAMERA_WIDTH, y/config.CAMERA_HEIGHT) for x, y in game.snake] if game.snake else [],
            'food': (game.food[0]/config.CAMERA_WIDTH, game.food[1]/config.CAMERA_HEIGHT) if game.food else None,
            'gesture': gesture,
            'finger_pos': finger_pos,
            'difficulty': game.difficulty
        }
        
        socketio.emit('game_state', game_state, namespace='/')
        
        # 控制循环频率（60 FPS）
        time.sleep(1/60)

@app.route('/')
def index():
    """提供前端页面"""
    return send_from_directory('static', 'index.html')

@app.route('/video_feed')
def video_feed():
    """视频流端点"""
    return Response(generate_frames(),
                   mimetype='multipart/x-mixed-replace; boundary=frame')

@socketio.on('connect')
def handle_connect():
    """客户端连接"""
    print('客户端已连接')
    emit('connection_response', {'status': 'connected'})

@socketio.on('disconnect')
def handle_disconnect():
    """客户端断开"""
    print('客户端已断开')

@socketio.on('game_action')
def handle_game_action(data):
    """处理游戏操作"""
    global game
    
    action = data.get('action')
    print(f"收到游戏操作: {action}")
    
    if action == 'restart':
        game.start_game()
    elif action == 'pause':
        game.pause_game()
    elif action == 'resume':
        game.resume_game()
    elif action == 'exit':
        game.stop_game()

def cleanup():
    """清理资源"""
    global is_running, camera, detector, game_thread
    
    print("\n正在停止服务...")
    is_running = False
    
    # 等待游戏线程结束
    if game_thread and game_thread.is_alive():
        print("等待游戏线程结束...")
        game_thread.join(timeout=2.0)
    
    # 停止检测器
    if detector:
        print("正在停止手势检测...")
        detector.stop()
        detector = None
    
    # 释放摄像头
    if camera:
        print("正在释放摄像头...")
        camera.release()
        camera = None
    
    print("资源已释放")
    
    # 强制退出程序
    import os
    import sys
    print("正在关闭服务器...")
    sys.stdout.flush()
    os._exit(0)

if __name__ == '__main__':
    try:
        # 初始化游戏
        if not initialize_game():
            exit(1)
        
        # 启动游戏循环线程
        is_running = True
        game_thread = threading.Thread(target=game_loop, daemon=True)
        game_thread.start()
        
        # 启动 Flask 服务器
        print("正在启动 Web 服务器...")
        print("请在浏览器访问: http://localhost:5000")
        print("按 Ctrl+C 停止服务器")
        socketio.run(app, host='0.0.0.0', port=5000, debug=False, allow_unsafe_werkzeug=True)
        
    except KeyboardInterrupt:
        print("\n\n用户中断")
    except Exception as e:
        print(f"发生错误：{e}")
        import traceback
        traceback.print_exc()
    finally:
        cleanup()

