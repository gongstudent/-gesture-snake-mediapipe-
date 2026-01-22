import cv2
import config
import time

class CameraManager:
    def __init__(self):
        self.cap = None
        self.width = config.CAMERA_WIDTH
        self.height = config.CAMERA_HEIGHT
        self.is_running = False

    def start(self):
        """Initialize and start the camera."""
        try:
            # Try index 0 first, then 1 if 0 fails
            self.cap = cv2.VideoCapture(0, cv2.CAP_DSHOW)  # Use DirectShow backend on Windows
            if not self.cap.isOpened():
                print("Warning: Camera 0 not found. Trying Camera 1...")
                self.cap = cv2.VideoCapture(1, cv2.CAP_DSHOW)
                
            if not self.cap.isOpened():
                raise RuntimeError("Could not open any camera.")

            # Set resolution
            self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, self.width)
            self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, self.height)
            
            # Check if resolution was set correctly
            actual_width = self.cap.get(cv2.CAP_PROP_FRAME_WIDTH)
            actual_height = self.cap.get(cv2.CAP_PROP_FRAME_HEIGHT)
            print(f"Camera initialized: {int(actual_width)}x{int(actual_height)}")
            
            # Give camera time to warm up and read a few test frames
            print("Warming up camera...")
            for i in range(5):
                ret, frame = self.cap.read()
                if ret:
                    break
                time.sleep(0.1)
            
            if not ret:
                print("Warning: Could not read test frame, but continuing...")
            else:
                print("Camera ready!")
            
            self.is_running = True
            return True
        except Exception as e:
            print(f"Error starting camera: {e}")
            self.is_running = False
            return False

    def read_frame(self):
        """Read a frame from the camera."""
        if not self.is_running or self.cap is None:
            return None

        ret, frame = self.cap.read()
        if not ret:
            print("Error: Could not read frame.")
            return None

        # Flip horizontally for mirror effect (intuitive for gaming)
        frame = cv2.flip(frame, 1)
        return frame

    def release(self):
        """Release camera resources."""
        if self.cap:
            self.cap.release()
            self.cap = None
        self.is_running = False
        print("Camera released.")
