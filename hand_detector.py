import cv2
import numpy as np
import threading
import copy
import time
import config
import os
from collections import deque, Counter

# Use wrapper for MediaPipe 0.10+ compatibility
try:
    import mediapipe as mp
    mp_hands = mp.solutions.hands
    mp_drawing = mp.solutions.drawing_utils
except (AttributeError, ImportError):
    # MediaPipe 0.10+ doesn't have solutions, use our wrapper
    import mp_hands_wrapper as mp
    mp_hands = mp.hands
    mp_drawing = mp.drawing_utils

class HandDetector:
    def __init__(self):
        self.backend = getattr(config, "HAND_BACKEND", "SOLUTIONS")
        self.is_tasks = False
        self.hands = None
        self.mp_draw = None
        self.prev_bbox = None  # (x, y, w, h) in detection (no-pad) coordinates
        self.latest_finger_norm = None  # normalized (0-1) in detection (no-pad)
        if self.backend == "TASKS":
            try:
                from mediapipe.tasks.python.vision import HandLandmarker, HandLandmarkerOptions, RunningMode
                from mediapipe.tasks.python.core import BaseOptions
                import mediapipe as mp_core
                # Resolve model path from multiple locations
                cfg_path = getattr(config, "TASKS_MODEL_PATH", "")
                candidates = []
                if cfg_path:
                    candidates.append(cfg_path)
                candidates += ["models/hand_landmarker.task", "hand_landmarker.task"]
                model_path = None
                for p in candidates:
                    p_abs = p if os.path.isabs(p) else os.path.join(os.getcwd(), p)
                    if os.path.exists(p_abs):
                        model_path = p_abs
                        break
                if model_path:
                    base_options = BaseOptions(model_asset_path=model_path)
                    options = HandLandmarkerOptions(base_options=base_options, num_hands=1, running_mode=RunningMode.VIDEO)
                    self.tasks_landmarker = HandLandmarker.create_from_options(options)
                    self.is_tasks = True
                    self.mp_core = mp_core
                else:
                    self.is_tasks = False
            except Exception:
                self.is_tasks = False
        if not self.is_tasks:
            self.mp_hands = mp_hands
            self.hands = mp_hands.Hands(
                static_image_mode=False,
                max_num_hands=1,
                min_detection_confidence=config.GESTURE_CONFIDENCE_THRESHOLD,
                min_tracking_confidence=0.5
            )
            self.mp_draw = mp_drawing
        
        # Threading support
        self.frame_to_process = None
        self.latest_result = None
        self.latest_gesture = config.GESTURE_NONE
        self.is_running = False
        self.thread = None
        self.lock = threading.Lock()
        
        # Smoothing
        self.gesture_history = deque(maxlen=5) # Keep last 5 frames for smoothing

    def start(self):
        """启动检测线程。"""
        self.is_running = True
        self.thread = threading.Thread(target=self._detection_loop, daemon=True)
        self.thread.start()

    def stop(self):
        """停止检测线程。"""
        self.is_running = False
        if self.thread:
            self.thread.join()

    def update_frame(self, frame):
        """更新检测线程处理的帧。"""
        if frame is None:
            return
        
        # 按需调整大小以进行性能优化
        small_frame = cv2.resize(frame, (config.DETECTION_WIDTH, config.DETECTION_HEIGHT))
        pad = getattr(config, "DETECTION_PAD", 0)
        if pad and pad > 0:
            small_frame = cv2.copyMakeBorder(
                small_frame, pad, pad, pad, pad, cv2.BORDER_REPLICATE
            )
        
        with self.lock:
            self.frame_to_process = small_frame

    def get_results(self):
        """获取最新的检测结果。"""
        with self.lock:
            return self.latest_result, self.latest_gesture
    
    def get_finger_position(self):
        """获取用于直接控制的食指指尖位置（归一化 0-1）。"""
        with self.lock:
            if self.latest_finger_norm is not None:
                return self.latest_finger_norm
            if not self.is_tasks and self.latest_result and self.latest_result.multi_hand_landmarks:
                hand_landmarks = self.latest_result.multi_hand_landmarks[0]
                index_tip = hand_landmarks.landmark[8]
                pad = getattr(config, "DETECTION_PAD", 0)
                w_pad = config.DETECTION_WIDTH + 2 * pad
                h_pad = config.DETECTION_HEIGHT + 2 * pad
                x_px = index_tip.x * w_pad - pad
                y_px = index_tip.y * h_pad - pad
                x_norm = max(0.0, min(1.0, x_px / config.DETECTION_WIDTH))
                y_norm = max(0.0, min(1.0, y_px / config.DETECTION_HEIGHT))
                return (x_norm, y_norm)
            return None

    def _detection_loop(self):
        while self.is_running:
            frame = None
            with self.lock:
                if self.frame_to_process is not None:
                    frame = self.frame_to_process.copy()
                    self.frame_to_process = None # Consume the frame
            
            if frame is None:
                time.sleep(0.01) # Avoid busy waiting
                continue

            pad = getattr(config, "DETECTION_PAD", 0)
            w_pad = config.DETECTION_WIDTH + 2 * pad
            h_pad = config.DETECTION_HEIGHT + 2 * pad
            roi_enable = True
            roi_expand = 1.8
            roi_min = 100

            if self.is_tasks:
                frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                mp_image = self.mp_core.Image(image_format=self.mp_core.ImageFormat.SRGB, data=frame_rgb)
                ts = int(time.time() * 1000)
                result = self.tasks_landmarker.detect_for_video(mp_image, ts)
                gesture = config.GESTURE_NONE
                if result and result.hand_landmarks:
                    for lm in result.hand_landmarks:
                        gesture = self._recognize_gesture_tasks(lm)
                        # update finger norm from index tip
                        idx = lm[8]
                        x_px = idx.x * w_pad - pad
                        y_px = idx.y * h_pad - pad
                        self.latest_finger_norm = (
                            max(0.0, min(1.0, x_px / config.DETECTION_WIDTH)),
                            max(0.0, min(1.0, y_px / config.DETECTION_HEIGHT)),
                        )
                        # update bbox
                        xs = [(p.x * w_pad - pad) for p in lm]
                        ys = [(p.y * h_pad - pad) for p in lm]
                        x0 = max(0, int(min(xs)))
                        y0 = max(0, int(min(ys)))
                        x1 = min(config.DETECTION_WIDTH, int(max(xs)))
                        y1 = min(config.DETECTION_HEIGHT, int(max(ys)))
                        self.prev_bbox = (x0, y0, max(roi_min, x1 - x0), max(roi_min, y1 - y0))
                self.gesture_history.append(gesture)
                smoothed = Counter(self.gesture_history).most_common(1)[0][0]
                with self.lock:
                    self.latest_result = result
                    self.latest_gesture = smoothed
                # ROI fallback when no hand found
                if (not result or not result.hand_landmarks) and roi_enable and self.prev_bbox:
                    x, y, w, h = self.prev_bbox
                    cx = x + w // 2
                    cy = y + h // 2
                    w2 = int(max(roi_min, w * roi_expand))
                    h2 = int(max(roi_min, h * roi_expand))
                    x0 = max(0, cx - w2 // 2)
                    y0 = max(0, cy - h2 // 2)
                    x1 = min(config.DETECTION_WIDTH, x0 + w2)
                    y1 = min(config.DETECTION_HEIGHT, y0 + h2)
                    # crop from padded frame
                    roi = frame[y0 + pad:y1 + pad, x0 + pad:x1 + pad]
                    roi_rgb = cv2.cvtColor(self._enhance_roi(roi), cv2.COLOR_BGR2RGB)
                    mp_roi = self.mp_core.Image(image_format=self.mp_core.ImageFormat.SRGB, data=roi_rgb)
                    ts = int(time.time() * 1000)
                    r2 = self.tasks_landmarker.detect_for_video(mp_roi, ts)
                    if r2 and r2.hand_landmarks:
                        lm = r2.hand_landmarks[0]
                        idx = lm[8]
                        x_global = x0 + int(idx.x * (x1 - x0))
                        y_global = y0 + int(idx.y * (y1 - y0))
                        self.latest_finger_norm = (
                            max(0.0, min(1.0, x_global / config.DETECTION_WIDTH)),
                            max(0.0, min(1.0, y_global / config.DETECTION_HEIGHT)),
                        )
                        xs = [x0 + int(p.x * (x1 - x0)) for p in lm]
                        ys = [y0 + int(p.y * (y1 - y0)) for p in lm]
                        x0b = max(0, min(xs))
                        y0b = max(0, min(ys))
                        x1b = min(config.DETECTION_WIDTH, max(xs))
                        y1b = min(config.DETECTION_HEIGHT, max(ys))
                        self.prev_bbox = (x0b, y0b, max(roi_min, x1b - x0b), max(roi_min, y1b - y0b))
            else:
                frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                results = self.hands.process(frame_rgb)
                gesture = config.GESTURE_NONE
                if results.multi_hand_landmarks:
                    for hand_landmarks in results.multi_hand_landmarks:
                        gesture = self._recognize_gesture(hand_landmarks)
                        # update finger norm and bbox
                        index_tip = hand_landmarks.landmark[8]
                        x_px = index_tip.x * w_pad - pad
                        y_px = index_tip.y * h_pad - pad
                        self.latest_finger_norm = (
                            max(0.0, min(1.0, x_px / config.DETECTION_WIDTH)),
                            max(0.0, min(1.0, y_px / config.DETECTION_HEIGHT)),
                        )
                        xs = []
                        ys = []
                        for p in hand_landmarks.landmark:
                            xs.append(p.x * w_pad - pad)
                            ys.append(p.y * h_pad - pad)
                        x0 = max(0, int(min(xs)))
                        y0 = max(0, int(min(ys)))
                        x1 = min(config.DETECTION_WIDTH, int(max(xs)))
                        y1 = min(config.DETECTION_HEIGHT, int(max(ys)))
                        self.prev_bbox = (x0, y0, max(roi_min, x1 - x0), max(roi_min, y1 - y0))
                self.gesture_history.append(gesture)
                smoothed_gesture = Counter(self.gesture_history).most_common(1)[0][0]
                with self.lock:
                    self.latest_result = results
                    self.latest_gesture = smoothed_gesture
                # ROI fallback
                if (not results or not results.multi_hand_landmarks) and roi_enable and self.prev_bbox:
                    x, y, w, h = self.prev_bbox
                    cx = x + w // 2
                    cy = y + h // 2
                    w2 = int(max(roi_min, w * roi_expand))
                    h2 = int(max(roi_min, h * roi_expand))
                    x0 = max(0, cx - w2 // 2)
                    y0 = max(0, cy - h2 // 2)
                    x1 = min(config.DETECTION_WIDTH, x0 + w2)
                    y1 = min(config.DETECTION_HEIGHT, y0 + h2)
                    roi = frame[y0 + pad:y1 + pad, x0 + pad:x1 + pad]
                    roi_rgb = cv2.cvtColor(self._enhance_roi(roi), cv2.COLOR_BGR2RGB)
                    r2 = self.hands.process(roi_rgb)
                    if r2 and r2.multi_hand_landmarks:
                        hl = r2.multi_hand_landmarks[0]
                        idx = hl.landmark[8]
                        x_global = x0 + int(idx.x * (x1 - x0))
                        y_global = y0 + int(idx.y * (y1 - y0))
                        self.latest_finger_norm = (
                            max(0.0, min(1.0, x_global / config.DETECTION_WIDTH)),
                            max(0.0, min(1.0, y_global / config.DETECTION_HEIGHT)),
                        )
                        xs = [x0 + int(p.x * (x1 - x0)) for p in hl.landmark]
                        ys = [y0 + int(p.y * (y1 - y0)) for p in hl.landmark]
                        x0b = max(0, min(xs))
                        y0b = max(0, min(ys))
                        x1b = min(config.DETECTION_WIDTH, max(xs))
                        y1b = min(config.DETECTION_HEIGHT, max(ys))
                        self.prev_bbox = (x0b, y0b, max(roi_min, x1b - x0b), max(roi_min, y1b - y0b))

    def _recognize_gesture(self, landmarks):
        """基于关键点识别手势。"""
        # 获取坐标
        h, w = config.DETECTION_HEIGHT, config.DETECTION_WIDTH
        lm_list = []
        for id, lm in enumerate(landmarks.landmark):
            cx, cy = int(lm.x * w), int(lm.y * h)
            lm_list.append([cx, cy])

        if not lm_list:
            return config.GESTURE_NONE

        # 手指状态 (0: 拇指, 1: 食指, 2: 中指, 3: 无名指, 4: 小指)
        fingers = []

        # 拇指 (检查 x 坐标相对于 IP 关节的位置，这取决于惯用手，比较复杂)
        # 简化版：检查指尖是否远离食指基部 (MCP)
        # 更好：检查指尖 x 是在 IP x 的左边还是右边。
        # 假设右手 (镜像) 或一般 "伸出"
        # 让我们使用一个更简单的启发式方法：距离手腕 vs IP 距离？
        # 标准方式：指尖 x < IP x (右手，手掌面向摄像头)
        # 因为我们翻转了图像，所以它表现得像镜子。
        # 让我们坚持简单的几何学。
        
        # 拇指：比较指尖 (4) 和 IP (3)
        # 但对于方向控制，我们假设 "指向"
        
        # 让我们检查垂直手指 (食指、中指、无名指、小指)
        # 指尖 y < PIP y 意味着手指是向上的
        tips = [8, 12, 16, 20]
        pips = [6, 10, 14, 18]
        
        for i in range(4):
            if lm_list[tips[i]][1] < lm_list[pips[i]][1]:
                fingers.append(1)
            else:
                fingers.append(0)
        
        # 拇指 (id 4) 逻辑：
        # 检查拇指指尖是否在 MCP (2) 的侧面。
        # 我们需要知道惯用手或者仅使用与食指 MCP (5) 的距离。
        # 如果 distance(4, 5) > threshold?
        # 如果指尖远离手掌中心 (0 或 9)，我们就算拇指是张开的。
        thumb_tip = lm_list[4]
        index_mcp = lm_list[5]
        # 简单的欧几里得距离
        dist_thumb_index = ((thumb_tip[0]-index_mcp[0])**2 + (thumb_tip[1]-index_mcp[1])**2)**0.5
        # 通过 手腕-食指MCP 长度进行归一化
        ref_len = ((lm_list[0][0]-lm_list[5][0])**2 + (lm_list[0][1]-lm_list[5][1])**2)**0.5
        
        thumb_up = 0
        if dist_thumb_index > ref_len * 0.5: # 启发式
            thumb_up = 1
        
        total_fingers = fingers.count(1) + thumb_up
        
        # 1. 退出：所有5个手指
        if total_fingers == 5:
            return config.GESTURE_QUIT
        
        # 2. 暂停：握拳 (0个手指)
        if total_fingers == 0:
            return config.GESTURE_PAUSE
        
        # 3. 重启：OK (拇指和食指接触，其他手指向上)
        # 检查拇指指尖 (4) 和食指指尖 (8) 之间的距离
        dist_ok = ((lm_list[4][0]-lm_list[8][0])**2 + (lm_list[4][1]-lm_list[8][1])**2)**0.5
        if dist_ok < ref_len * 0.3 and fingers[1] == 1 and fingers[2] == 1 and fingers[3] == 1: 
            # 注意：fingers 列表对应食指、中指、无名指、小指。
            # fingers[0] 是食指。fingers[1] 是中指。
            # OK 手势：拇指+食指圆圈，中指/无名指/小指向上。
            # 所以 fingers 应该是 [0, 1, 1, 1] 大致 (如果食指卷曲可能被算作向下)
            # 实际上，在 OK 手势中，食指指尖是向下/接触拇指的。
            return config.GESTURE_RESTART

        # 改进的 OK 检查：
        # 食指指尖 (8) 靠近拇指指尖 (4)
        # 中指 (12)、无名指 (16)、小指 (20) 向上。
        if dist_ok < ref_len * 0.3 and fingers[1] == 1 and fingers[2] == 1 and fingers[3] == 1:
             return config.GESTURE_RESTART

        # 4. 方向控制：两个手指 (食指 + 中指)
        # 条件：食指 (8) 和中指 (12) 向上。无名指和小指向下。
        if fingers[0] == 1 and fingers[1] == 1 and fingers[2] == 0 and fingers[3] == 0:
            # 检查方向
            # 从 MCP (5, 9) 到指尖 (8, 12) 的向量
            # 平均指尖和 MCP
            avg_tip_x = (lm_list[8][0] + lm_list[12][0]) / 2
            avg_tip_y = (lm_list[8][1] + lm_list[12][1]) / 2
            avg_mcp_x = (lm_list[5][0] + lm_list[9][0]) / 2
            avg_mcp_y = (lm_list[5][1] + lm_list[9][1]) / 2
            
            dx = avg_tip_x - avg_mcp_x
            dy = avg_tip_y - avg_mcp_y
            
            if abs(dx) > abs(dy):
                return config.GESTURE_RIGHT if dx > 0 else config.GESTURE_LEFT
            else:
                return config.GESTURE_DOWN if dy > 0 else config.GESTURE_UP
        
        # 回退单指指向 (以防用户仅使用一个手指)
        if fingers[0] == 1 and fingers[1] == 0 and fingers[2] == 0 and fingers[3] == 0:
             # 类似逻辑
             dx = lm_list[8][0] - lm_list[5][0]
             dy = lm_list[8][1] - lm_list[5][1]
             if abs(dx) > abs(dy):
                return config.GESTURE_RIGHT if dx > 0 else config.GESTURE_LEFT
             else:
                return config.GESTURE_DOWN if dy > 0 else config.GESTURE_UP
        
        return config.GESTURE_NONE

    def draw_landmarks(self, frame, results):
        pad = getattr(config, "DETECTION_PAD", 0)
        w_pad = config.DETECTION_WIDTH + 2 * pad
        h_pad = config.DETECTION_HEIGHT + 2 * pad
        sx = config.CAMERA_WIDTH / float(config.DETECTION_WIDTH)
        sy = config.CAMERA_HEIGHT / float(config.DETECTION_HEIGHT)
        if self.is_tasks:
            if results and getattr(results, "hand_landmarks", None):
                for lm in results.hand_landmarks:
                    pts = []
                    for p in lm:
                        x_px = p.x * w_pad - pad
                        y_px = p.y * h_pad - pad
                        x_cam = int(max(0, min(config.CAMERA_WIDTH - 1, x_px * sx)))
                        y_cam = int(max(0, min(config.CAMERA_HEIGHT - 1, y_px * sy)))
                        pts.append((x_cam, y_cam))
                        cv2.circle(frame, (x_cam, y_cam), 3, (0, 255, 255), -1)
        else:
            if results and results.multi_hand_landmarks:
                for hand_landmarks in results.multi_hand_landmarks:
                    pts = []
                    for p in hand_landmarks.landmark:
                        x_px = p.x * w_pad - pad
                        y_px = p.y * h_pad - pad
                        x_cam = int(max(0, min(config.CAMERA_WIDTH - 1, x_px * sx)))
                        y_cam = int(max(0, min(config.CAMERA_HEIGHT - 1, y_px * sy)))
                        pts.append((x_cam, y_cam))
                        cv2.circle(frame, (x_cam, y_cam), 3, (0, 255, 255), -1)

    def _recognize_gesture_tasks(self, lm_list_norm):
        pad = getattr(config, "DETECTION_PAD", 0)
        w_pad = config.DETECTION_WIDTH + 2 * pad
        h_pad = config.DETECTION_HEIGHT + 2 * pad
        lm_list = []
        for lm in lm_list_norm:
            x_px = lm.x * w_pad - pad
            y_px = lm.y * h_pad - pad
            x_px = max(0, min(config.DETECTION_WIDTH - 1, int(x_px)))
            y_px = max(0, min(config.DETECTION_HEIGHT - 1, int(y_px)))
            lm_list.append([x_px, y_px])
        if not lm_list:
            return config.GESTURE_NONE
        tips = [8, 12, 16, 20]
        pips = [6, 10, 14, 18]
        fingers = []
        for i in range(4):
            fingers.append(1 if lm_list[tips[i]][1] < lm_list[pips[i]][1] else 0)
        thumb_tip = lm_list[4]
        index_mcp = lm_list[5]
        dist_thumb_index = ((thumb_tip[0]-index_mcp[0])**2 + (thumb_tip[1]-index_mcp[1])**2)**0.5
        ref_len = ((lm_list[0][0]-lm_list[5][0])**2 + (lm_list[0][1]-lm_list[5][1])**2)**0.5
        thumb_up = 1 if dist_thumb_index > ref_len * 0.5 else 0
        total = fingers.count(1) + thumb_up
        if total == 5:
            return config.GESTURE_QUIT
        if total == 0:
            return config.GESTURE_PAUSE
        dist_ok = ((lm_list[4][0]-lm_list[8][0])**2 + (lm_list[4][1]-lm_list[8][1])**2)**0.5
        if dist_ok < ref_len * 0.3 and fingers[1] == 1 and fingers[2] == 1 and fingers[3] == 1:
            return config.GESTURE_RESTART
        if fingers[0] == 1 and fingers[1] == 1 and fingers[2] == 0 and fingers[3] == 0:
            avg_tip_x = (lm_list[8][0] + lm_list[12][0]) / 2
            avg_tip_y = (lm_list[8][1] + lm_list[12][1]) / 2
            avg_mcp_x = (lm_list[5][0] + lm_list[9][0]) / 2
            avg_mcp_y = (lm_list[5][1] + lm_list[9][1]) / 2
            dx = avg_tip_x - avg_mcp_x
            dy = avg_tip_y - avg_mcp_y
            if abs(dx) > abs(dy):
                return config.GESTURE_RIGHT if dx > 0 else config.GESTURE_LEFT
            else:
                return config.GESTURE_DOWN if dy > 0 else config.GESTURE_UP
        if fingers[0] == 1 and fingers[1] == 0 and fingers[2] == 0 and fingers[3] == 0:
            dx = lm_list[8][0] - lm_list[5][0]
            dy = lm_list[8][1] - lm_list[5][1]
            if abs(dx) > abs(dy):
                return config.GESTURE_RIGHT if dx > 0 else config.GESTURE_LEFT
            else:
                return config.GESTURE_DOWN if dy > 0 else config.GESTURE_UP
        return config.GESTURE_NONE

    def _enhance_roi(self, roi_bgr):
        try:
            ycrcb = cv2.cvtColor(roi_bgr, cv2.COLOR_BGR2YCrCb)
            y, cr, cb = cv2.split(ycrcb)
            clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
            y = clahe.apply(y)
            ycrcb = cv2.merge((y, cr, cb))
            return cv2.cvtColor(ycrcb, cv2.COLOR_YCrCb2BGR)
        except Exception:
            return roi_bgr
