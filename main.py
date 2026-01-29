import cv2
import time
import sys
import config
from camera_manager import CameraManager
from hand_detector import HandDetector
from snake_game import SnakeGame
from game_ui import GameUI

def main():
    # 1. 初始化组件
    print("正在初始化游戏...")
    
    camera = CameraManager()
    if not camera.start():
        print("启动摄像头失败。正在退出。")
        return

    detector = HandDetector()
    detector.start()
    
    game = SnakeGame()
    ui = GameUI()
    
    print("游戏已初始化。正在启动主循环...")
    print("控制：手指指向移动 | OK手势开始 | Q键退出")

    cv2.namedWindow(config.WINDOW_NAME, cv2.WINDOW_NORMAL)
    cv2.resizeWindow(config.WINDOW_NAME, config.CAMERA_WIDTH, config.CAMERA_HEIGHT)

    prev_time = 0
    q_pressed_once = False
    
    try:
        while True:
            # 2. 帧捕获
            frame = camera.read_frame()
            if frame is None:
                break

            # 3. 手势检测
            detector.update_frame(frame)
            results, gesture = detector.get_results()
            finger_pos = detector.get_finger_position()
            
            # 可选：可视化检测区域或关键点
            if config.GESTURE_CONFIDENCE_THRESHOLD > 0:
                detector.draw_landmarks(frame, results)

            # 4. 游戏逻辑
            # 仅键盘退出，无手势退出
            
            # 如果检测到手指，更新目标位置
            if finger_pos and game.state == "RUNNING":
                game.set_target_position(finger_pos[0], finger_pos[1])
                
            game.process_gesture(gesture)
            game.update()

            # 5. 渲染
            ui.draw(frame, game, gesture, finger_pos)

            # 6. 显示
            # FPS 计算
            curr_time = time.time()
            fps = 1 / (curr_time - prev_time) if prev_time > 0 else 0
            prev_time = curr_time
            cv2.putText(frame, f"FPS: {int(fps)}", (10, 20), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 1)

            cv2.imshow(config.WINDOW_NAME, frame)

            # 键盘控制
            key = cv2.waitKey(1) & 0xFF
            if key == ord('q'):
                if not q_pressed_once:
                    q_pressed_once = True
                    print("已暂停（再次按 'q' 退出）。")
                    if game.state == "RUNNING":
                        game.pause_game()
                    continue
                else:
                    print("正在退出游戏...")
                    break
            
            # 调试：R 键重置
            if key == ord('r'):
                game.start_game()

    except KeyboardInterrupt:
        print("用户中断。")
    except Exception as e:
        print(f"发生错误：{e}")
        import traceback
        traceback.print_exc()
    finally:
        # 清理
        detector.stop()
        camera.release()
        cv2.destroyAllWindows()
        print("资源已释放。游戏已关闭。")

if __name__ == "__main__":
    main()
