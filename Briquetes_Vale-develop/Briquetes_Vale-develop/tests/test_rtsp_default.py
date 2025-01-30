import cv2
import time

path = "rtsp://172.19.145.77:8080/h264_ulaw.sdp"

def main():
    # Open the video file
    vs = cv2.VideoCapture(path)  
    start_time2 = time.time()
    # Check if the video file opened successfully
    if not vs.isOpened():
        print("Error: Unable to open video file")
        return

    # Set desired frame rate (e.g., 15 fps)
    frame_rate =35
    fps=0
    # Get the frame rate (FPS) of the video
    fpso = vs.get(cv2.CAP_PROP_FPS)
    print(fpso)
    #vs.set(cv2.CAP_PROP_BUFFERSIZE, 0)
    # Create a named window
    cv2.namedWindow("frame", cv2.WINDOW_NORMAL)
    while True:
        # Grab a frame at a time
        ret, frame = vs.read()
        start_time = time.time()
        if not ret:
            break  # Break the loop if there are no more frames

        # Resize and display the frame on the screen
        frame = cv2.resize(frame, (800, 800))

        # Calculate FPS if loopTime is non-zero
        loopTime = time.time() - start_time

        # Adjust frame rate based on processing time
        delay = max(1, int((1 / frame_rate - loopTime) * 1000))
        key = cv2.waitKey(delay) & 0xFF

        # Wait for the user to hit 'q' for quit
        if key == ord('q'):
            break
        
        # Calculate FPS if loopTime is non-zero
        loopTime2 = time.time() - start_time
        if loopTime2 > 0:
            fps = 0.9*fps+.1 / loopTime2
            print("FPS:", fps)
        
        # Display FPS on the frame
        cv2.putText(frame, f"FPS: {fps}", (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 0), 2, cv2.LINE_AA)
  
        # Display the frame
        cv2.imshow("frame", frame)
    # Clean up and we're outta here.

    etime=time.time()-start_time2
    print(etime)
    cv2.destroyAllWindows()
    vs.release()

if __name__ == "__main__":
    main()