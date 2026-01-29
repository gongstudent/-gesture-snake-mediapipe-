import cv2
import numpy as np
import config

class GameUI:
    def __init__(self):
        pass

    def draw(self, frame, game, gesture_info, finger_pos=None):
        """
        在画面上绘制游戏状态。
        :param frame: 摄像头画面
        :param game: SnakeGame 实例
        :param gesture_info: 手势信息元组 (手势名称, 置信度) 或仅手势名称
        :param finger_pos: 归一化的手指位置 (x, y) 范围 0-1
        """
        # 1. 无棋盘背景 - 全屏游戏
        # 蛇可以在屏幕任何位置移动
        start_x = 0
        start_y = 0

        # 2. 绘制蛇 - 全屏坐标
        if game.snake:
            # 使用全屏坐标以平滑像素模式绘制
            for i, (px, py) in enumerate(game.snake):
                # 计算颜色渐变
                ratio = i / max(1, len(game.snake) - 1)
                color = (
                    int(config.SNAKE_BODY_COLOR_START[0] * (1 - ratio) + config.SNAKE_BODY_COLOR_END[0] * ratio),
                    int(config.SNAKE_BODY_COLOR_START[1] * (1 - ratio) + config.SNAKE_BODY_COLOR_END[1] * ratio),
                    int(config.SNAKE_BODY_COLOR_START[2] * (1 - ratio) + config.SNAKE_BODY_COLOR_END[2] * ratio)
                )
                
                if i == 0:  # 蛇头
                    color = config.SNAKE_HEAD_COLOR
                    radius = 10
                else:
                    radius = 8
                
                # 直接使用坐标 (全屏)
                screen_x = int(px)
                screen_y = int(py)
                cv2.circle(frame, (screen_x, screen_y), radius, color, -1)
                
                # 在节段之间绘制连接线以获得平滑外观
                if i > 0:
                    prev_px, prev_py = game.snake[i - 1]
                    screen_prev_x = int(prev_px)
                    screen_prev_y = int(prev_py)
                    cv2.line(frame, (screen_prev_x, screen_prev_y), (screen_x, screen_y), color, 12, lineType=cv2.LINE_AA)

        # 3. 绘制食物 - 全屏坐标
        if game.food:
            fx, fy = game.food
            # 直接使用坐标 (全屏)
            px = int(fx)
            py = int(fy)
            # 绘制食物圆形
            cv2.circle(frame, (px, py), 10, config.FOOD_COLOR, -1)
            cv2.circle(frame, (px, py), 12, (255, 255, 255), 2)  # 白色轮廓

        # 4. 绘制信息栏 (顶部)
        self._draw_text(frame, f"Score: {game.score}", (30, 60), 1.2, config.TEXT_COLOR)

        # 5. 绘制手势信息 (底部) - 简化版
        if game.state == "RUNNING":
            self._draw_text(frame, "Point finger to move", (30, config.CAMERA_HEIGHT - 30), 0.9, config.COLOR_YELLOW)
        
        # 绘制手指位置指示器
        if finger_pos and game.state == "RUNNING":
            # 将归一化坐标转换为全屏像素坐标
            fx = int(finger_pos[0] * config.CAMERA_WIDTH)
            fy = int(finger_pos[1] * config.CAMERA_HEIGHT)
            # 绘制准星
            cv2.circle(frame, (fx, fy), 6, (0, 255, 255), 2)
            cv2.line(frame, (fx - 10, fy), (fx + 10, fy), (0, 255, 255), 1)
            cv2.line(frame, (fx, fy - 10), (fx, fy + 10), (0, 255, 255), 1)
        
        # 6. 游戏结束 / 开始屏幕
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
