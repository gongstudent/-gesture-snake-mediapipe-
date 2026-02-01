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
        """初始化并启动摄像头。"""
        try:
            # 首先尝试索引 0，如果失败则尝试 1
            self.cap = cv2.VideoCapture(0, cv2.CAP_DSHOW)  # 在 Windows 上使用 DirectShow 后端
            if not self.cap.isOpened():
                print("警告：未找到摄像头 0。正在尝试摄像头 1...")
                self.cap = cv2.VideoCapture(1, cv2.CAP_DSHOW)
                
            if not self.cap.isOpened():
                raise RuntimeError("无法打开任何摄像头。")

            # 设置分辨率
            self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, self.width)
            self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, self.height)
            
            # 检查分辨率是否设置正确
            actual_width = self.cap.get(cv2.CAP_PROP_FRAME_WIDTH)
            actual_height = self.cap.get(cv2.CAP_PROP_FRAME_HEIGHT)
            print(f"摄像头已初始化：{int(actual_width)}x{int(actual_height)}")
            
            # 给摄像头预热时间并读取几帧测试帧
            print("正在预热摄像头...")
            for i in range(5):
                ret, frame = self.cap.read()
                if ret:
                    break
                time.sleep(0.1)
            
            if not ret:
                print("警告：无法读取测试帧，但继续执行...")
            else:
                print("摄像头就绪！")
            
            self.is_running = True
            return True
        except Exception as e:
            print(f"启动摄像头时出错：{e}")
            self.is_running = False
            return False

    def read_frame(self):
        """从摄像头读取一帧。"""
        if not self.is_running or self.cap is None:
            return None

        ret, frame = self.cap.read()
        if not ret:
            print("错误：无法读取帧。")
            return None

        # 水平翻转以获得镜像效果（对游戏更直观）
        frame = cv2.flip(frame, 1)
        return frame

    def release(self):
        """释放摄像头资源。"""
        self.is_running = False
        
        if self.cap:
            # 先停止读取
            if self.cap.isOpened():
                self.cap.release()
            self.cap = None
            
        # 确保销毁所有 OpenCV 窗口
        cv2.destroyAllWindows()
        
        # 给系统一点时间完全释放资源
        time.sleep(0.1)
        
        print("摄像头已释放。")
