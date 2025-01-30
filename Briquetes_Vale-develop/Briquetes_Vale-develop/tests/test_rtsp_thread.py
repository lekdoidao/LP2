import cv2
import time
import threading
import queue
import cv2, queue, threading, time

# bufferless VideoCapture
class VideoCapture:
    def __init__(self, name):
        self.cap = cv2.VideoCapture(name)
        self.q = queue.Queue()
        self.lock = threading.Lock()
        self.running = True  # Flag to indicate if the thread should keep running
        self.t = threading.Thread(target=self._reader)
        self.t.daemon = True
        self.t.start()

    def _reader(self):
        while self.running:
            ret, frame = self.cap.read()
            if not ret:
                break
            if not self.q.empty():
                try:
                    self.q.get_nowait()   # Discard previous frame
                except queue.Empty:
                    pass
            self.q.put(frame)
            self.state=ret

    def read(self):
        return self.q.get(),self.state

    def stop(self):
        self.running = False
        self.t.join()  # Wait for the thread to exit


def main():
    vs = VideoCapture("rtsp://172.19.145.77:8080/h264_ulaw.sdp")
    start_time2 = time.time()
    frame_rate = 35
    fps = 0
    cv2.namedWindow("Live Stream", cv2.WINDOW_NORMAL)
    
    while True:
        frame,success = vs.read()
        start_time = time.time()
        if not success:
            break

        loop_time = time.time() - start_time
        delay = max(1, int((1 / frame_rate - loop_time) * 1000))
        key = cv2.waitKey(delay) & 0xFF

        if key == ord('q'):
            break

        loop_time2 = time.time() - start_time
        if loop_time2 > 0:
            fps = 0.9 * fps + 0.1 / loop_time2
            print(fps)
        cv2.putText(frame, f"FPS: {fps:.2f}", (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 0), 2, cv2.LINE_AA)
        cv2.imshow("Live Stream", frame)
    
    total_time = time.time() - start_time2
    print("Total time taken:", total_time, "seconds")

    cv2.destroyAllWindows()
    vs.cap.release()

if __name__ == "__main__":
    main()