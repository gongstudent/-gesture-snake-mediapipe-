import cv2

# ======================
# 显示设置 / Display Settings
# ======================
WINDOW_NAME = "Gesture Snake Game"
CAMERA_WIDTH = 1280
CAMERA_HEIGHT = 720
GAME_WIDTH = 640
GAME_HEIGHT = 640
GAME_OFFSET_X = (CAMERA_WIDTH - GAME_WIDTH) // 2
GAME_OFFSET_Y = (CAMERA_HEIGHT - GAME_HEIGHT) // 2

# 手势识别分辨率 (为了性能优化)
DETECTION_WIDTH = 320
DETECTION_HEIGHT = 180
DETECTION_PAD = 24
HAND_BACKEND = "SOLUTIONS"
TASKS_MODEL_PATH = "models/hand_landmarker.task"

# ======================
# 颜色定义 (BGR格式) / Colors (BGR)
# ======================
COLOR_WHITE = (255, 255, 255)
COLOR_BLACK = (0, 0, 0)
COLOR_RED = (0, 0, 255)
COLOR_GREEN = (0, 255, 0)
COLOR_BLUE = (255, 0, 0)
COLOR_YELLOW = (0, 255, 255)
COLOR_PURPLE = (128, 0, 128)
COLOR_GRAY = (128, 128, 128)

# 贪吃蛇颜色
SNAKE_HEAD_COLOR = (0, 255, 0)       # 绿色
SNAKE_BODY_COLOR_START = (0, 200, 0) # 渐变起始
SNAKE_BODY_COLOR_END = (0, 100, 0)   # 渐变结束
FOOD_COLOR = (0, 0, 255)             # 红色

# UI颜色
TEXT_COLOR = (255, 255, 255)
BORDER_COLOR = (255, 255, 255)
OVERLAY_COLOR = (0, 0, 0, 128) # 半透明黑色 (需特殊处理)

# ======================
# 游戏设置 / Game Settings
# ======================
GRID_SIZE = 20
GRID_WIDTH = GAME_WIDTH // GRID_SIZE
GRID_HEIGHT = GAME_HEIGHT // GRID_SIZE

INITIAL_SNAKE_LENGTH = 3

# 难度等级 (刷新间隔 ms)
DIFFICULTY_LEVELS = {
    "EASY": 100,
    "MEDIUM": 70,
    "HARD": 50
}
DIFFICULTY_THRESHOLDS = {
    "MEDIUM": 50,  # 分数达到50进入中等
    "HARD": 150    # 分数达到150进入困难
}

# ======================
# 手势定义 / Gestures
# ======================
GESTURE_NONE = "NONE"
GESTURE_UP = "UP"
GESTURE_DOWN = "DOWN"
GESTURE_LEFT = "LEFT"
GESTURE_RIGHT = "RIGHT"
GESTURE_PAUSE = "PAUSE"     # 握拳
GESTURE_RESTART = "RESTART" # OK
GESTURE_QUIT = "QUIT"       # 五指张开

# 手势置信度阈值
GESTURE_CONFIDENCE_THRESHOLD = 0.7
