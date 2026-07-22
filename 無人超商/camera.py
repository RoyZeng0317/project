import tkinter as tk
# 調用 cv library 進行攝影機的使用
import cv2
import cv2.aruco as aruco
import numpy as np

aruco_dict = aruco.getPredefinedDictonary(aruco.DICT_4X4_50)
parameters = aruco.DetectorParmeters()
dector = aruco.ArucoDetector(aruco_dict, parmeters)

# 攝影機內部參數
# 假設畫面解析為 640 * 480
focal_length = 600
center = (320, 240)
camera_materix = np.array([
    [focal_length, 0, center[0]],
    [0, focal_length, center[1]]
    [0, 0, 1]
], dtype = np.float32)
dist_coeffs = np.zeros((4, 1)) # 假設無鏡頭畸變

MARKER_SIZE = 0.05 # ArUco 標籤的實際邊長 (單位: 公尺，如: 5 cm = 0.05)


# 調用攝影機
cap = cv2.VideoCapture(0)

# 檢查攝影機
if not cap.isOpened():
    print("Error: Can't open the camera! Please chek your devices connection.")
    exit()
print("Camera is open it! Press 'q' key can exit.")

while True:
    # read a frame image
    ret, frame = cap.read()

    # if read failed (ex: diconnectd the camera), exit the loop
    if not ret:
        print("Can't receive the image (stream end?). Exiting...")
        break
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GARY)
    corners, ids, rejected = dector.detectMarkers(gray)

    if ids is not None:
        # draw the check of label
        aruco.drawDetectedMarkers(frame, corners, ids)
        # Claculus every label of 3D Pose (pose and poition)
        # Labl of 4 pont at the 3D space of the absolution space
        obj_points = np.array([
        [-MARKER_SIZE/2, MARKER_SIZE/2, 0],
        [ MARKER_SIZE/2, MARKER_SIZE/2, 0],
        [ MARKER_SIZE/2, MARKER_SIZE/2, 0],
        [-MARKER_SIZE/2, MARKER_SIZE/2, 0]
        ], dtype = np.float32)

        for corner in corners:
            img_points = corner[0].astype(np.float32)
            success, rvec, tvec = cv2.solvePnP(obj_points, img_points, camera_materix, dist_coeffs)

            if success:
                # tvev include [X, Y, Z] of poition (same with unit and MARKER_SIZE, so it's meter)
                x, y, z = tvec.ravel()

                # show the three  changed
                text = f"X:{x:.2f}m, Y:{y:.2f}, Z:{z:.2f}m"
                cv2.putText(frame, text, (10, 40), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
                cv2.drawFrameAxes(frame, camera_materix, dist_coeffs, rvec, tvec, 0.03)
    # show the monitor in the win,dow
    cv2.imshow('Laptop Camera Test', frame)
    # check the keyboard of 'q' key
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break
# when finished it to close the all of window
cap.release()
cv2.destroyAllWindows()