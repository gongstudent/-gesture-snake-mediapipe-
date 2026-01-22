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
        # Initialize snake with pixel coordinates in center of screen
        center_x = config.CAMERA_WIDTH // 2
        center_y = config.CAMERA_HEIGHT // 2
        # Create initial snake body segments
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
        if self.state == "RUNNING":
            self.state = "PAUSED"
        elif self.state == "PAUSED":
            self.state = "RUNNING"

    def stop_game(self):
        self.state = "STOPPED"

    def update_difficulty(self):
        self.difficulty = "INFINITE"
        self.speed = config.DIFFICULTY_LEVELS["EASY"]

    def spawn_food(self):
        # Spawn food at random pixel position on full screen
        while True:
            x = random.randint(20, config.CAMERA_WIDTH - 20)
            y = random.randint(20, config.CAMERA_HEIGHT - 20)
            # Check if too close to snake head
            if self.snake:
                head_x, head_y = self.snake[0]
                dist = ((x - head_x) ** 2 + (y - head_y) ** 2) ** 0.5
                if dist > 50:  # At least 50 pixels away
                    self.food = (x, y)
                    break
            else:
                self.food = (x, y)
                break
    

    def process_gesture(self, gesture):
        # No quit gesture - use keyboard only
        
        if self.state == "STOPPED" or self.state == "GAME_OVER":
            if gesture == config.GESTURE_RESTART:
                self.start_game()
        
        elif self.state == "RUNNING":
            # No pause - only running or game over
            pass
                
        return None

    def change_direction(self, new_dir):
        # Prevent 180 degree turns
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
            # Direct control: smooth continuous movement
            if self.target_position is not None:
                self.move_smooth()
        else:
            # Gesture control: move at fixed intervals
            current_time = time.time() * 1000
            if current_time - self.last_move_time >= self.speed:
                self.move()
                self.last_move_time = current_time
    
    def set_target_position(self, normalized_x, normalized_y):
        """Set target position from normalized coordinates (0-1) for entire screen."""
        # Convert normalized coordinates to full screen pixel coordinates
        pixel_x = normalized_x * config.CAMERA_WIDTH
        pixel_y = normalized_y * config.CAMERA_HEIGHT
        
        # No clamping - allow full screen movement
        self.target_position = (pixel_x, pixel_y)
    
    def move_smooth(self):
        """Snake head directly follows finger position."""
        if not self.target_position or not self.snake:
            return
        
        # Directly set head to finger position
        new_head_x, new_head_y = self.target_position
        
        # Endless mode: no self-collision game over
        
        # Update snake body - follow the head
        new_snake = [(new_head_x, new_head_y)]
        
        # Each segment follows the one in front of it
        for i in range(1, len(self.snake)):
            prev_x, prev_y = new_snake[i - 1]
            curr_x, curr_y = self.snake[i]
            
            # Calculate distance to previous segment
            dx = prev_x - curr_x
            dy = prev_y - curr_y
            dist = (dx ** 2 + dy ** 2) ** 0.5
            
            # Move towards previous segment if too far
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
        
        # Check food collision
        if self.food:
            fx, fy = self.food
            dist_to_food = ((new_head_x - fx) ** 2 + (new_head_y - fy) ** 2) ** 0.5
            if dist_to_food < 15:  # Collision radius for food
                self.score += 10
                self.update_difficulty()
                # Add new segment at the tail
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

        # Check collisions
        if (head_x < 0 or head_x >= config.GRID_WIDTH or
            head_y < 0 or head_y >= config.GRID_HEIGHT or
            (head_x, head_y) in self.snake):
            self.game_over()
            return

        # Move snake
        new_head = (head_x, head_y)
        self.snake.insert(0, new_head)

        # Check food
        if new_head == self.food:
            self.score += 10 # +1 length, +10 score? Prompt says +1 length, score +?. Let's assume +10.
            self.update_difficulty()
            self.spawn_food()
        else:
            self.snake.pop()

    def game_over(self):
        self.state = "GAME_OVER"
