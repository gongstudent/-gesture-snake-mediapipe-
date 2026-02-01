import random
import time
import config

class SnakeGame:
    def __init__(self):
        self.state = "STOPPED" # STOPPED, RUNNING, PAUSED, GAME_OVER
        self.snake = []  # Will store pixel coordinates instead of grid
        self.direction = config.GESTURE_RIGHT
        self.next_direction = config.GESTURE_RIGHT
        self.food = None
        self.score = 0
        self.difficulty = "EASY"
        self.speed = config.DIFFICULTY_LEVELS["EASY"]
        self.last_move_time = 0
        
        # Direct control mode - smooth movement
        self.control_mode = "DIRECT"  # "DIRECT" or "GESTURE"
        self.target_position = None  # Target pixel position (x, y)
        self.move_speed = 2  # Pixels per frame (slower = 1-3, faster = 5-10)
        self.segment_distance = 10  # Distance between body segments
        self.tail_smooth = 0.35
        
    def start_game(self):
        # 使用屏幕中心像素坐标初始化蛇
        center_x = config.CAMERA_WIDTH // 2
        center_y = config.CAMERA_HEIGHT // 2
        # 创建初始蛇身节段
        self.snake = [
            (center_x, center_y),
            (center_x - self.segment_distance, center_y),
            (center_x - self.segment_distance * 2, center_y)
        ]
        self.direction = config.GESTURE_RIGHT
        self.next_direction = config.GESTURE_RIGHT
        self.score = 0
        self.update_difficulty()
        self.spawn_food()
        self.state = "RUNNING"
        self.last_move_time = time.time() * 1000
        self.target_position = (center_x, center_y)

    def pause_game(self):
        """暂停游戏"""
        if self.state == "RUNNING":
            self.state = "PAUSED"

    def stop_game(self):
        self.state = "STOPPED"

    def update_difficulty(self):
        self.difficulty = "INFINITE"
        self.speed = config.DIFFICULTY_LEVELS["EASY"]

    def spawn_food(self):
        # 在全屏随机像素位置生成食物
        while True:
            x = random.randint(20, config.CAMERA_WIDTH - 20)
            y = random.randint(20, config.CAMERA_HEIGHT - 20)
            # 检查是否离蛇头太近
            if self.snake:
                head_x, head_y = self.snake[0]
                dist = ((x - head_x) ** 2 + (y - head_y) ** 2) ** 0.5
                if dist > 50:  # 至少距离50像素
                    self.food = (x, y)
                    break
            else:
                self.food = (x, y)
                break
    

    def resume_game(self):
        """恢复游戏"""
        if self.state == "PAUSED":
            self.state = "RUNNING"
    
    def process_gesture(self, gesture):
        """处理手势输入"""
        
        if self.state == "STOPPED" or self.state == "GAME_OVER":
            # OK手势：开始游戏
            if gesture == config.GESTURE_RESTART:
                self.start_game()
        
        elif self.state == "RUNNING":
            # 握拳手势：暂停游戏
            if gesture == config.GESTURE_PAUSE:
                self.pause_game()
        
        elif self.state == "PAUSED":
            # OK手势：恢复游戏
            if gesture == config.GESTURE_RESTART:
                self.resume_game()
                
        return None
    


    def change_direction(self, new_dir):
        # 防止180度掉头
        opposites = {
            config.GESTURE_UP: config.GESTURE_DOWN,
            config.GESTURE_DOWN: config.GESTURE_UP,
            config.GESTURE_LEFT: config.GESTURE_RIGHT,
            config.GESTURE_RIGHT: config.GESTURE_LEFT
        }
        if new_dir != opposites.get(self.direction):
            self.next_direction = new_dir

    def update(self):
        if self.state != "RUNNING":
            return
        
        if self.control_mode == "DIRECT":
            # 直接控制：平滑连续移动
            if self.target_position is not None:
                self.move_smooth()
        else:
            # 手势控制：按固定间隔移动
            current_time = time.time() * 1000
            if current_time - self.last_move_time >= self.speed:
                self.move()
                self.last_move_time = current_time
    
    def set_target_position(self, normalized_x, normalized_y):
        """根据归一化坐标(0-1)设置全屏目标位置。"""
        # 将归一化坐标转换为全屏像素坐标
        pixel_x = normalized_x * config.CAMERA_WIDTH
        pixel_y = normalized_y * config.CAMERA_HEIGHT
        
        # 不进行限制 - 允许全屏移动
        self.target_position = (pixel_x, pixel_y)
    
    def move_smooth(self):
        """蛇头直接跟随手指位置。"""
        if not self.target_position or not self.snake:
            return
        
        # 直接将蛇头设置为手指位置（无延迟，更贴近手指）
        new_head_x, new_head_y = self.target_position
        
        # 无尽模式：无自身碰撞游戏结束
        
        # 更新蛇身 - 跟随蛇头
        new_snake = [(new_head_x, new_head_y)]
        
        # 每个节段跟随其前一个节段
        for i in range(1, len(self.snake)):
            prev_x, prev_y = new_snake[i - 1]
            curr_x, curr_y = self.snake[i]
            
            # 计算到前一个节段的距离
            dx = prev_x - curr_x
            dy = prev_y - curr_y
            dist = (dx ** 2 + dy ** 2) ** 0.5
            
            # 如果太远则向前一个节段移动
            if dist > self.segment_distance:
                ratio = self.segment_distance / dist if dist != 0 else 0
                target_x = prev_x - dx * ratio
                target_y = prev_y - dy * ratio
                new_x = curr_x + (target_x - curr_x) * self.tail_smooth
                new_y = curr_y + (target_y - curr_y) * self.tail_smooth
                new_snake.append((new_x, new_y))
            else:
                new_snake.append((curr_x, curr_y))
        
        self.snake = new_snake
        
        # 检查食物碰撞
        if self.food:
            fx, fy = self.food
            dist_to_food = ((new_head_x - fx) ** 2 + (new_head_y - fy) ** 2) ** 0.5
            if dist_to_food < 15:  # 食物碰撞半径
                self.score += 10
                self.update_difficulty()
                # 在尾部添加新节段
                tail_x, tail_y = self.snake[-1]
                if len(self.snake) > 1:
                    prev_tail_x, prev_tail_y = self.snake[-2]
                    dx = tail_x - prev_tail_x
                    dy = tail_y - prev_tail_y
                    dist = (dx ** 2 + dy ** 2) ** 0.5
                    if dist > 0:
                        new_tail_x = tail_x + (dx / dist) * self.segment_distance
                        new_tail_y = tail_y + (dy / dist) * self.segment_distance
                    else:
                        new_tail_x = tail_x
                        new_tail_y = tail_y
                else:
                    new_tail_x = tail_x - self.segment_distance
                    new_tail_y = tail_y
                self.snake.append((new_tail_x, new_tail_y))
                self.spawn_food()

    def move(self):
        self.direction = self.next_direction
        head_x, head_y = self.snake[0]
        
        if self.direction == config.GESTURE_UP:
            head_y -= 1
        elif self.direction == config.GESTURE_DOWN:
            head_y += 1
        elif self.direction == config.GESTURE_LEFT:
            head_x -= 1
        elif self.direction == config.GESTURE_RIGHT:
            head_x += 1

        # 检查碰撞
        if (head_x < 0 or head_x >= config.GRID_WIDTH or
            head_y < 0 or head_y >= config.GRID_HEIGHT or
            (head_x, head_y) in self.snake):
            self.game_over()
            return

        # 移动蛇
        new_head = (head_x, head_y)
        self.snake.insert(0, new_head)

        # 检查食物
        if new_head == self.food:
            self.score += 10 # +1 length, +10 score? Prompt says +1 length, score +?. Let's assume +10.
            self.update_difficulty()
            self.spawn_food()
        else:
            self.snake.pop()

    def game_over(self):
        self.state = "GAME_OVER"
