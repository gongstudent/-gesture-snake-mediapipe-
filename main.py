import cv2
import time
import sys
import config
from camera_manager import CameraManager
from hand_detector import HandDetector
from snake_game import SnakeGame
from game_ui import GameUI

def main():
    # 1. Initialize Components
    print("Initializing Game...")
    
    camera = CameraManager()
    if not camera.start():
        print("Failed to start camera. Exiting.")
        return

    detector = HandDetector()
    detector.start()
    
    game = SnakeGame()
    ui = GameUI()
    
    print("Game Initialized. Starting Main Loop...")
    print("Controls: Point with finger to move | OK gesture to start | Q to quit")

    cv2.namedWindow(config.WINDOW_NAME, cv2.WINDOW_NORMAL)
    cv2.resizeWindow(config.WINDOW_NAME, config.CAMERA_WIDTH, config.CAMERA_HEIGHT)

    prev_time = 0
    q_pressed_once = False
    
    try:
        while True:
            # 2. Frame Capture
            frame = camera.read_frame()
            if frame is None:
                break

            # 3. Gesture Detection
            detector.update_frame(frame)
            results, gesture = detector.get_results()
            finger_pos = detector.get_finger_position()
            
            # Optional: Visualize detection area or landmarks
            if config.GESTURE_CONFIDENCE_THRESHOLD > 0:
                detector.draw_landmarks(frame, results)

            # 4. Game Logic
            # Only keyboard quit, no gesture quit
            
            # Update target position if finger is detected
            if finger_pos and game.state == "RUNNING":
                game.set_target_position(finger_pos[0], finger_pos[1])
                
            game.process_gesture(gesture)
            game.update()

            # 5. Rendering
            ui.draw(frame, game, gesture, finger_pos)

            # 6. Display
            # FPS Calculation
            curr_time = time.time()
            fps = 1 / (curr_time - prev_time) if prev_time > 0 else 0
            prev_time = curr_time
            cv2.putText(frame, f"FPS: {int(fps)}", (10, 20), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 1)

            cv2.imshow(config.WINDOW_NAME, frame)

            # Keyboard Controls
            key = cv2.waitKey(1) & 0xFF
            if key == ord('q'):
                if not q_pressed_once:
                    q_pressed_once = True
                    print("Paused (press 'q' again to exit).")
                    if game.state == "RUNNING":
                        game.pause_game()
                    continue
                else:
                    print("Exiting game...")
                    break
            
            # Debug: R key to restart
            if key == ord('r'):
                game.start_game()

    except KeyboardInterrupt:
        print("Interrupted by user.")
    except Exception as e:
        print(f"An error occurred: {e}")
        import traceback
        traceback.print_exc()
    finally:
        # Cleanup
        detector.stop()
        camera.release()
        cv2.destroyAllWindows()
        print("Resources released. Game Closed.")

if __name__ == "__main__":
    main()
