
import threading
import time

import cv2
import mediapipe as mp
import numpy as np
from mediapipe.tasks import python
from mediapipe.tasks.python import vision
from streamlit_webrtc import VideoProcessorBase


class RehabHandTracker(VideoProcessorBase):
    def __init__(self, model_path):
        self.lock = threading.Lock()
        self.hand_detected = False
        self.repetitions = 0
        self.movement = "Waiting"
        self.status = "Waiting for camera"
        self.last_state = "open"
        self.last_count_time = 0.0
        self.landmarker = None

        try:
            options = vision.HandLandmarkerOptions(
                base_options=python.BaseOptions(
                    model_asset_path=str(model_path)
                ),
                running_mode=vision.RunningMode.VIDEO,
                num_hands=1,
                min_hand_detection_confidence=0.45,
                min_hand_presence_confidence=0.45,
                min_tracking_confidence=0.45,
            )
            self.landmarker = (
                vision.HandLandmarker.create_from_options(options)
            )
            self.status = "Hand model loaded"
        except Exception as exc:
            self.status = f"Model error: {exc}"

    def get_stats(self):
        with self.lock:
            return {
                "hand_detected": self.hand_detected,
                "repetitions": self.repetitions,
                "movement": self.movement,
                "status": self.status,
            }

    def recv(self, frame):
        image = frame.to_ndarray(format="bgr24")
        image = cv2.flip(image, 1)

        if self.landmarker is None:
            cv2.putText(
                image, "Hand model failed to load", (20, 40),
                cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2
            )
            return frame.from_ndarray(image, format="bgr24")

        try:
            rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
            mp_image = mp.Image(
                image_format=mp.ImageFormat.SRGB, data=rgb
            )
            result = self.landmarker.detect_for_video(
                mp_image, int(time.time() * 1000)
            )

            found = bool(result.hand_landmarks)
            with self.lock:
                self.hand_detected = found
                self.status = (
                    "Hand detected" if found
                    else "Show your hand to the camera"
                )

            if found:
                lm = result.hand_landmarks[0]
                h, w = image.shape[:2]
                pts = [
                    (int(p.x * w), int(p.y * h)) for p in lm
                ]
                links = [
                    (0,1),(1,2),(2,3),(3,4),
                    (0,5),(5,6),(6,7),(7,8),
                    (5,9),(9,10),(10,11),(11,12),
                    (9,13),(13,14),(14,15),(15,16),
                    (13,17),(17,18),(18,19),(19,20),(0,17),
                ]
                for a, b in links:
                    cv2.line(
                        image, pts[a], pts[b],
                        (210, 130, 255), 2, cv2.LINE_AA
                    )
                for x, y in pts:
                    cv2.circle(
                        image, (x, y), 5,
                        (95, 255, 215), -1, cv2.LINE_AA
                    )

                # Approximate open/closed hand state using
                # fingertip distance from the palm centre.
                palm = np.array([lm[9].x, lm[9].y])
                tips = [8, 12, 16, 20]
                bases = [5, 9, 13, 17]
                tip_dist = np.mean([
                    np.linalg.norm(
                        np.array([lm[t].x, lm[t].y]) - palm
                    ) for t in tips
                ])
                base_dist = np.mean([
                    np.linalg.norm(
                        np.array([lm[b].x, lm[b].y])
                        - np.array([lm[0].x, lm[0].y])
                    ) for b in bases
                ])
                state = (
                    "open" if tip_dist > base_dist * 0.78
                    else "closed"
                )

                now = time.time()
                if (
                    state == "open"
                    and self.last_state == "closed"
                    and now - self.last_count_time > 0.7
                ):
                    with self.lock:
                        self.repetitions += 1
                    self.last_count_time = now

                self.last_state = state
                self.movement = (
                    "Open hand" if state == "open" else "Flexed hand"
                )

                cv2.rectangle(image, (12, 12), (285, 78), (13, 23, 39), -1)
                cv2.putText(
                    image, "HAND TRACKING ACTIVE", (23, 37),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.55, (95, 255, 215), 2
                )
                cv2.putText(
                    image, f"State: {self.movement}", (23, 62),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1
                )
            else:
                self.last_state = "open"
                cv2.putText(
                    image, "Show your hand to the camera", (18, 40),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.65, (95, 255, 215), 2
                )

        except Exception as exc:
            with self.lock:
                self.status = f"Tracking error: {exc}"

        return frame.from_ndarray(image, format="bgr24")
