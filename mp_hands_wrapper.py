"""
MediaPipe Hands wrapper for compatibility with MediaPipe 0.10+
Uses the tasks vision API
"""
import cv2
import numpy as np
from mediapipe.tasks import python
from mediapipe.tasks.python import vision


class HandsWrapper:
    """Wrapper to provide solutions-like API for MediaPipe 0.10+"""
    
    # Hand connections for drawing
    HAND_CONNECTIONS = frozenset([
        (0, 1), (1, 2), (2, 3), (3, 4),  # Thumb
        (0, 5), (5, 6), (6, 7), (7, 8),  # Index
        (5, 9), (9, 10), (10, 11), (11, 12),  # Middle
        (9, 13), (13, 14), (14, 15), (15, 16),  # Ring
        (13, 17), (17, 18), (18, 19), (19, 20),  # Pinky
        (0, 17)  # Palm
    ])
    
    def __init__(self, static_image_mode=False, max_num_hands=2,
                 min_detection_confidence=0.5, min_tracking_confidence=0.5):
        """Initialize hands detector with same params as old API"""
        import os
        import urllib.request
        
        # Download model if not exists
        model_path = 'hand_landmarker.task'
        if not os.path.exists(model_path):
            print("Downloading hand landmark model...")
            model_url = 'https://storage.googleapis.com/mediapipe-models/hand_landmarker/hand_landmarker/float16/latest/hand_landmarker.task'
            try:
                urllib.request.urlretrieve(model_url, model_path)
                print("Model downloaded successfully")
            except Exception as e:
                print(f"Failed to download model: {e}")
                raise
        
        # Use MediaPipe tasks vision API with VIDEO mode
        base_options = python.BaseOptions(model_asset_path=model_path)
        options = vision.HandLandmarkerOptions(
            base_options=base_options,
            running_mode=vision.RunningMode.VIDEO,  # Use VIDEO mode for better performance
            num_hands=max_num_hands,
            min_hand_detection_confidence=min_detection_confidence,
            min_hand_presence_confidence=min_tracking_confidence,
            min_tracking_confidence=min_tracking_confidence
        )
        
        self.detector = vision.HandLandmarker.create_from_options(options)
        self.frame_counter = 0
    
    def process(self, image):
        """Process an RGB image and return hand landmarks"""
        # Convert numpy array to MediaPipe Image
        import mediapipe as mp
        mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=image)
        
        # Detect hands (use frame timestamp for video mode)
        self.frame_counter += 1
        timestamp_ms = self.frame_counter * 33  # Assume ~30fps
        result = self.detector.detect_for_video(mp_image, timestamp_ms)
        
        # Convert result to solutions-like format
        class Results:
            def __init__(self):
                self.multi_hand_landmarks = None
                self.multi_hand_world_landmarks = None
                self.multi_handedness = None
        
        results = Results()
        
        if result.hand_landmarks:
            # Convert to landmark list format
            results.multi_hand_landmarks = []
            for hand_landmarks in result.hand_landmarks:
                # Create a simple object to hold landmarks
                class LandmarkList:
                    def __init__(self):
                        self.landmark = []
                
                landmark_list = LandmarkList()
                for landmark in hand_landmarks:
                    class Landmark:
                        def __init__(self, x, y, z):
                            self.x = x
                            self.y = y
                            self.z = z
                    
                    landmark_list.landmark.append(Landmark(landmark.x, landmark.y, landmark.z))
                results.multi_hand_landmarks.append(landmark_list)
        
        return results
    
    def close(self):
        """Cleanup resources"""
        if hasattr(self, 'detector'):
            self.detector.close()


class DrawingUtils:
    """Drawing utilities for hand landmarks"""
    
    @staticmethod
    def draw_landmarks(image, landmark_list, connections=None,
                      landmark_drawing_spec=None, connection_drawing_spec=None):
        """Draw hand landmarks on image"""
        if landmark_list is None:
            return
        
        if connections is None:
            connections = HandsWrapper.HAND_CONNECTIONS
        
        # Default drawing specs
        if landmark_drawing_spec is None:
            landmark_color = (0, 0, 255)  # Red
            landmark_thickness = 2
            landmark_circle_radius = 2
        else:
            landmark_color = landmark_drawing_spec.color
            landmark_thickness = landmark_drawing_spec.thickness
            landmark_circle_radius = landmark_drawing_spec.circle_radius
        
        if connection_drawing_spec is None:
            connection_color = (0, 255, 0)  # Green
            connection_thickness = 2
        else:
            connection_color = connection_drawing_spec.color
            connection_thickness = connection_drawing_spec.thickness
        
        # Get image dimensions
        h, w, _ = image.shape
        
        # Convert landmarks to pixel coordinates
        points = []
        for landmark in landmark_list.landmark:
            x = int(landmark.x * w)
            y = int(landmark.y * h)
            points.append((x, y))
        
        # Draw connections
        if connections:
            for connection in connections:
                start_idx, end_idx = connection
                if start_idx < len(points) and end_idx < len(points):
                    cv2.line(image, points[start_idx], points[end_idx],
                            connection_color, connection_thickness)
        
        # Draw landmarks
        for point in points:
            cv2.circle(image, point, landmark_circle_radius,
                      landmark_color, landmark_thickness)


# Create module-level objects to mimic solutions API
class Hands:
    """Class to mimic mp.solutions.hands.Hands"""
    def __init__(self, **kwargs):
        self._hands = HandsWrapper(**kwargs)
    
    def process(self, image):
        return self._hands.process(image)
    
    def close(self):
        self._hands.close()
    
    # Add class attribute for connections
    HAND_CONNECTIONS = HandsWrapper.HAND_CONNECTIONS


# Module-level instances
hands = type('hands', (), {
    'Hands': Hands,
    'HAND_CONNECTIONS': HandsWrapper.HAND_CONNECTIONS
})()

drawing_utils = DrawingUtils()
