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
        """Start the detection thread."""
        self.is_running = True
        self.thread = threading.Thread(target=self._detection_loop, daemon=True)
        self.thread.start()

    def stop(self):
        """Stop the detection thread."""
        self.is_running = False
        if self.thread:
            self.thread.join()

    def update_frame(self, frame):
        """Update the frame for the detection thread to process."""
        if frame is None:
            return
        
        # Resize for performance optimization as requested
        small_frame = cv2.resize(frame, (config.DETECTION_WIDTH, config.DETECTION_HEIGHT))
        pad = getattr(config, "DETECTION_PAD", 0)
        if pad and pad > 0:
            small_frame = cv2.copyMakeBorder(
                small_frame, pad, pad, pad, pad, cv2.BORDER_REPLICATE
            )
        
        with self.lock:
            self.frame_to_process = small_frame

    def get_results(self):
        """Get the latest detection results."""
        with self.lock:
            return self.latest_result, self.latest_gesture
    
    def get_finger_position(self):
        """Get the index finger tip position for direct control (normalized 0-1)."""
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
        """Recognize gesture based on landmarks."""
        # Get coordinates
        h, w = config.DETECTION_HEIGHT, config.DETECTION_WIDTH
        lm_list = []
        for id, lm in enumerate(landmarks.landmark):
            cx, cy = int(lm.x * w), int(lm.y * h)
            lm_list.append([cx, cy])

        if not lm_list:
            return config.GESTURE_NONE

        # Fingers state (0: Thumb, 1: Index, 2: Middle, 3: Ring, 4: Pinky)
        fingers = []

        # Thumb (Check x position relative to IP joint depending on handedness is complex)
        # Simplified: Check if tip is far from index base (MCP)
        # Better: Check if tip x is to the left/right of IP x. 
        # Assuming right hand (mirror) or general "sticking out"
        # Let's use a simpler heuristic: distance from wrist vs IP distance?
        # Standard way: Tip x < IP x (Right Hand, palm facing camera)
        # Since we flipped the image, it behaves like a mirror. 
        # Let's stick to simple geometry.
        
        # Thumb: Compare Tip (4) with IP (3)
        # But for direction control, we assume "Pointing"
        
        # Let's check vertical fingers (Index, Middle, Ring, Pinky)
        # Tip y < PIP y means finger is UP
        tips = [8, 12, 16, 20]
        pips = [6, 10, 14, 18]
        
        for i in range(4):
            if lm_list[tips[i]][1] < lm_list[pips[i]][1]:
                fingers.append(1)
            else:
                fingers.append(0)
        
        # Thumb (id 4) logic:
        # Check if thumb tip is to the side of MCP (2).
        # We need to know handedness or just use distance from Index MCP (5).
        # If distance(4, 5) > threshold?
        # Let's count thumb as open if tip is far from palm center (0 or 9).
        thumb_tip = lm_list[4]
        index_mcp = lm_list[5]
        # Simple Euclidean distance
        dist_thumb_index = ((thumb_tip[0]-index_mcp[0])**2 + (thumb_tip[1]-index_mcp[1])**2)**0.5
        # Normalize by wrist-index_mcp length
        ref_len = ((lm_list[0][0]-lm_list[5][0])**2 + (lm_list[0][1]-lm_list[5][1])**2)**0.5
        
        thumb_up = 0
        if dist_thumb_index > ref_len * 0.5: # Heuristic
            thumb_up = 1
        
        total_fingers = fingers.count(1) + thumb_up
        
        # 1. Quit: All 5 fingers
        if total_fingers == 5:
            return config.GESTURE_QUIT
        
        # 2. Pause: Fist (0 fingers)
        if total_fingers == 0:
            return config.GESTURE_PAUSE
        
        # 3. Restart: OK (Thumb and Index touching, others up)
        # Check distance between Thumb Tip (4) and Index Tip (8)
        dist_ok = ((lm_list[4][0]-lm_list[8][0])**2 + (lm_list[4][1]-lm_list[8][1])**2)**0.5
        if dist_ok < ref_len * 0.3 and fingers[1] == 1 and fingers[2] == 1 and fingers[3] == 1: 
            # Note: fingers list corresponds to Index, Middle, Ring, Pinky.
            # fingers[0] is Index. fingers[1] is Middle.
            # OK gesture: Thumb+Index circle, Middle/Ring/Pinky UP.
            # So fingers should be [0, 1, 1, 1] roughly (Index might be counted as down if curled)
            # Actually, in OK sign, Index tip is down/touching thumb.
            return config.GESTURE_RESTART

        # Refined OK check:
        # Index tip (8) close to Thumb tip (4)
        # Middle (12), Ring (16), Pinky (20) are UP.
        if dist_ok < ref_len * 0.3 and fingers[1] == 1 and fingers[2] == 1 and fingers[3] == 1:
             return config.GESTURE_RESTART

        # 4. Direction Control: Two fingers (Index + Middle)
        # Condition: Index (8) and Middle (12) are UP. Ring and Pinky are DOWN.
        if fingers[0] == 1 and fingers[1] == 1 and fingers[2] == 0 and fingers[3] == 0:
            # Check orientation
            # Vector from MCP (5, 9) to Tip (8, 12)
            # Average the tips and MCPs
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
        
        # Fallback single finger pointing (just in case user uses one finger)
        if fingers[0] == 1 and fingers[1] == 0 and fingers[2] == 0 and fingers[3] == 0:
             # Similar logic
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
