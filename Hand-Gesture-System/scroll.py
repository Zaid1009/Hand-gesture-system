import math
import cv2
import mediapipe as mp
import mouse
import time


class GestureDetector:
    def __init__(self):
        self.mpHands = mp.solutions.hands  # init mediapipe mpHands
        self.hands = self.mpHands.Hands(static_image_mode=False, max_num_hands=1, min_detection_confidence=0.5,
                                        min_tracking_confidence=0.5)  # init medipipe hand
        self.fingerTipLmNumDef = [4, 8, 12, 16, 20]  # init hand finger tips land mark numbers
        self.savedCursor = (0, 0)  # init last valid cursor position
        self.cTime = time.time()  # init previous click time to current time
        self.pTime = time.time()  # init previous time to current click time
        self.cTimeScroll = time.time()  # init previous c time to current scroll time
        self.pTimeScroll = time.time()  # init previous time to current scroll time
        self.xCal = 70  # init x coordinate cursor calibration
        self.yCal = 100  # init y coordinate cursor calibration
        self.detectInterval = 650  # init detect interval
        self.xScreenRes = 1920  # main monitor x resolution
        self.yScreenRes = 1080  # main monitor y resolution


def main():
    # init video caputre of webcam
    cap = cv2.VideoCapture(0)
    # init the gesture detector
    detector = GestureDetector()
    # init click detector
    clickDetector = 2
    # init scroll detector
    scrollDetector = 2
    # init cursor
    savedCursor = (0, 0)
    # start frame grabbing
    while True:
        success, img = cap.read()
        # resize to native screen resolution
        img = cv2.resize(img, (detector.xScreenRes, detector.yScreenRes), interpolation=cv2.INTER_AREA)
        # flip image to enable controlaqs
        img = cv2.flip(img, 1)

        # start hand detection
        detector.results = detector.hands.process(cv2.cvtColor(img, cv2.COLOR_BGR2RGB))
        landMarkListDetected = []
        if detector.results.multi_hand_landmarks:
            scr_heigth, scr_width, _ = img.shape
            # iterate over the hands
            for handLms in detector.results.multi_hand_landmarks:
                # iterate over landmarks
                for lmNum, lmCoord in enumerate(handLms.landmark):
                    normX, normY, normZ = int(lmCoord.x * scr_width), int(lmCoord.y * scr_heigth), int(lmCoord.z)
                    landMarkListDetected.append([normX, normY, normZ])

        # validate detection
        if landMarkListDetected:
            # detect fingers up
            fingersDetected = []
            cursor = 0, 0
            fingersDetected.append(0)  # thumb
            for tipLmNum in range(1, 5):  # remaining fingers
                if landMarkListDetected[detector.fingerTipLmNumDef[tipLmNum]][1] < \
                        landMarkListDetected[detector.fingerTipLmNumDef[tipLmNum] - 2][1]:
                    fingersDetected.append(1)
                    if tipLmNum == 1:  # cursor finger
                        cursor = landMarkListDetected[detector.fingerTipLmNumDef[tipLmNum]][0], \
                                 landMarkListDetected[detector.fingerTipLmNumDef[tipLmNum]][1]
                else:
                    fingersDetected.append(0)  # finger not up

            # print cursor location point
            cv2.circle(img, cursor, 5, (0, 0, 255), cv2.FILLED)

            # print cursor position text coordinates
            (outputTextWidth, outputTextHeight), _ = cv2.getTextSize(f'{int(cursor[0]), int(cursor[1])}',
                                                                     cv2.FONT_HERSHEY_PLAIN, 1, 1)
            outputRectX1, outputRectY1, outputRectX2, outputRectY2 = cursor[0] + 5, cursor[1] + 35, cursor[
                0] + outputTextWidth + 35, cursor[1] - outputTextHeight + 5
            cv2.rectangle(img, (outputRectX1, outputRectY1), (outputRectX2, outputRectY2), (255, 0, 0), cv2.FILLED)
            cv2.putText(img, f'{int(cursor[0]), int(cursor[1])}', (cursor[0] + 20, cursor[1] + 20),
                        cv2.FONT_HERSHEY_PLAIN, 1, (255, 255, 255), 1)

            # detect mouse movement
            if fingersDetected == [0, 1, 0, 0, 0]:  # if point finger is 1
                # detect mouse click
                lengthFinger = math.hypot(landMarkListDetected[8][0] - landMarkListDetected[7][0],
                                          landMarkListDetected[8][1] - landMarkListDetected[7][1])
                print(lengthFinger)
                if lengthFinger >= 50:
                    mouse.move(cursor[0] + detector.xCal, cursor[1] + detector.yCal, absolute=True, duration=0.1)
                    savedCursor = (cursor[0] + detector.xCal, cursor[1] + detector.yCal)
                if clickDetector == 2 and scrollDetector == 2:  # start new double click detection
                    cTime = time.time()  # get the current time
                    clickDetector -= 1  # next state
            elif fingersDetected == [0, 0, 0, 0, 0]:
                if clickDetector == 1 and scrollDetector == 2:  # first dobule click detected
                    mouse.move(savedCursor[0], savedCursor[1], absolute=True, duration=0.1)
                    pTime = time.time()  # get the current time
                    frameTime = cTime - pTime  # calculate the time difference between the current and previous frame
                    if frameTime <= detector.detectInterval:  # check interval is valid
                        clickDetector -= 1  # click done
                        mouse.click('left')  # left button click
                        print("left")
                    clickDetector = 2  # reset click state
            print(" ")
            # detect scrolling
            if fingersDetected == [0, 1, 1, 0, 0]:  # if two finger detected
                # calculate two finger length
                lengthFingerOne = math.hypot(landMarkListDetected[8][0] - landMarkListDetected[7][0],
                                             landMarkListDetected[8][1] - landMarkListDetected[7][1])
                lengthFingerTwo = math.hypot(landMarkListDetected[12][0] - landMarkListDetected[12][0],
                                             landMarkListDetected[12][1] - landMarkListDetected[12][1])
                if scrollDetector == 2 and clickDetector == 2:  # start new scroll detection
                    cTimeScroll = time.time()  # get the current time
                    scrollDetector -= 1  # next state
            elif fingersDetected == [0, 0, 0, 0, 0]:
                if scrollDetector == 1 and clickDetector == 2:  # scrolling detected detected
                    pTimeScroll = time.time()  # get the current time
                    frameTimeScroll = cTimeScroll - pTimeScroll  # calculate the time difference between the current and previous frame
                    if frameTimeScroll <= detector.detectInterval:  # check interval is valid
                        scrollDetector -= 1  # click done
                        mouse.wheel(-10)  # scroll down
                        print("scroll down")
                    scrollDetector = 2  # reset scroll state
            print(" ")
        cv2.imshow("Image", img)
        cv2.waitKey(1)


if __name__ == "__main__":
    main()