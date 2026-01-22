import cv2
import numpy as np
import config

class GameUI:
    def __init__(self):
        pass

    def draw(self, frame, game, gesture_info, finger_pos=None):
        """
        Draw the game state onto the frame.
        :param frame: The camera frame
        :param game: The SnakeGame instance
        :param gesture_info: Tuple (gesture_name, confidence) or just gesture name
        :param finger_pos: Normalized finger position (x, y) in 0-1 range
        """
        # 1. No game board background - full screen gameplay
        # Snake can move anywhere on the screen
        start_x = 0
        start_y = 0

        # 2. Draw Snake - Full screen coordinates
        if game.snake:
            # Draw in smooth pixel mode with full screen coordinates
            for i, (px, py) in enumerate(game.snake):
                # Calculate color gradient
                ratio = i / max(1, len(game.snake) - 1)
                color = (
                    int(config.SNAKE_BODY_COLOR_START[0] * (1 - ratio) + config.SNAKE_BODY_COLOR_END[0] * ratio),
                    int(config.SNAKE_BODY_COLOR_START[1] * (1 - ratio) + config.SNAKE_BODY_COLOR_END[1] * ratio),
                    int(config.SNAKE_BODY_COLOR_START[2] * (1 - ratio) + config.SNAKE_BODY_COLOR_END[2] * ratio)
                )
                
                if i == 0:  # Head
                    color = config.SNAKE_HEAD_COLOR
                    radius = 10
                else:
                    radius = 8
                
                # Use coordinates directly (full screen)
                screen_x = int(px)
                screen_y = int(py)
                cv2.circle(frame, (screen_x, screen_y), radius, color, -1)
                
                # Draw connecting lines between segments for smooth appearance
                if i > 0:
                    prev_px, prev_py = game.snake[i - 1]
                    screen_prev_x = int(prev_px)
                    screen_prev_y = int(prev_py)
                    cv2.line(frame, (screen_prev_x, screen_prev_y), (screen_x, screen_y), color, 12, lineType=cv2.LINE_AA)

        # 3. Draw Food - Full screen coordinates
        if game.food:
            fx, fy = game.food
            # Use coordinates directly (full screen)
            px = int(fx)
            py = int(fy)
            # Draw circle for food
            cv2.circle(frame, (px, py), 10, config.FOOD_COLOR, -1)
            cv2.circle(frame, (px, py), 12, (255, 255, 255), 2)  # White outline

        # 4. Draw Info Bar (Top)
        self._draw_text(frame, f"Score: {game.score}", (30, 60), 1.2, config.TEXT_COLOR)

        # 5. Draw Gesture Info (Bottom) - simplified
        if game.state == "RUNNING":
            self._draw_text(frame, "Point finger to move", (30, config.CAMERA_HEIGHT - 30), 0.9, config.COLOR_YELLOW)
        
        # Draw finger position indicator
        if finger_pos and game.state == "RUNNING":
            # Convert normalized coordinates to pixel coordinates on full screen
            fx = int(finger_pos[0] * config.CAMERA_WIDTH)
            fy = int(finger_pos[1] * config.CAMERA_HEIGHT)
            # Draw crosshair
            cv2.circle(frame, (fx, fy), 6, (0, 255, 255), 2)
            cv2.line(frame, (fx - 10, fy), (fx + 10, fy), (0, 255, 255), 1)
            cv2.line(frame, (fx, fy - 10), (fx, fy + 10), (0, 255, 255), 1)
        
        # 6. Game Over / Start Screen
        if game.state == "STOPPED":
            self._draw_centered_text(frame, "SNAKE GAME", -80, 3.0, config.COLOR_GREEN)
            self._draw_centered_text(frame, "OK Gesture to Start", -10, 1.4, config.COLOR_WHITE)
            self._draw_centered_text(frame, "Point with Finger to Move Snake", 50, 1.1, config.COLOR_YELLOW)
            self._draw_centered_text(frame, "Press Q to Pause, Q again to Quit", 100, 1.0, config.COLOR_WHITE)
        elif game.state == "PAUSED":
            self._draw_centered_text(frame, f"Score: {game.score}", 0, 2.2, config.COLOR_YELLOW)

    def _draw_text(self, frame, text, pos, scale, color, thickness=2):
        cv2.putText(frame, text, pos, cv2.FONT_HERSHEY_SIMPLEX, scale, color, thickness)

    def _draw_centered_text(self, frame, text, y_offset, scale, color, thickness=2):
        text_size = cv2.getTextSize(text, cv2.FONT_HERSHEY_SIMPLEX, scale, thickness)[0]
        text_x = (config.CAMERA_WIDTH - text_size[0]) // 2
        text_y = (config.CAMERA_HEIGHT + text_size[1]) // 2 + y_offset
        cv2.putText(frame, text, (text_x, text_y), cv2.FONT_HERSHEY_SIMPLEX, scale, color, thickness)
