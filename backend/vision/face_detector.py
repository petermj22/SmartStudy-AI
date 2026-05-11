"""
Module: face_detector.py
Purpose: MediaPipe-based face mesh detection with 468+10 iris landmarks.
         Optimized for real-time processing with minimal overhead.
Author: SmartStudy Team
Version: 1.0.0

Dependencies:
    - mediapipe>=0.10.8
    - numpy>=1.24.3
    - opencv-python>=4.8.1
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import List, Optional

import cv2
import numpy as np
from loguru import logger
import os

@dataclass
class DetectionResult:
    """Container for face detection results."""

    detected: bool
    landmarks: Optional[np.ndarray] = None
    normalized_landmarks: Optional[np.ndarray] = None
    image_width: int = 0
    image_height: int = 0
    detection_confidence: float = 0.0

    @property
    def has_iris(self) -> bool:
        return False # LBF does not provide iris landmarks


class FaceDetector:
    """
    Production face detector using OpenCV Haar Cascade + LBF Landmarks.
    Fully compatible with Python 3.14 where MediaPipe wheels are broken.
    Extracts 68 facial landmarks.
    """

    # Eye landmarks (6 points each for EAR calculation)
    LEFT_EYE_INDICES: List[int] = [36, 37, 38, 39, 40, 41]
    RIGHT_EYE_INDICES: List[int] = [42, 43, 44, 45, 46, 47]

    # Iris landmarks (not available in 68-point, left empty)
    LEFT_IRIS_INDICES: List[int] = []
    RIGHT_IRIS_INDICES: List[int] = []

    # Mouth landmarks (6 points for MAR)
    MOUTH_INDICES: List[int] = [48, 54, 51, 57, 62, 66]

    # Head pose key points for solvePnP
    HEAD_POSE_INDICES: List[int] = [30, 8, 36, 45, 48, 54]

    # Brow landmarks
    LEFT_BROW_INDICES: List[int] = [17, 18, 19, 20, 21]
    RIGHT_BROW_INDICES: List[int] = [22, 23, 24, 25, 26]

    # 3D canonical face model points (mm) for PnP
    HEAD_MODEL_3D_POINTS: np.ndarray = np.array([
        (0.0, 0.0, 0.0),          # Nose tip (30)
        (0.0, -63.6, -12.5),      # Chin (8)
        (-43.3, 32.7, -26.0),     # Left eye corner (36)
        (43.3, 32.7, -26.0),      # Right eye corner (45)
        (-28.9, -28.9, -24.1),    # Left mouth corner (48)
        (28.9, -28.9, -24.1),     # Right mouth corner (54)
    ], dtype=np.float64)

    def __init__(
        self,
        min_detection_confidence: float = 0.5,
        min_tracking_confidence: float = 0.5,
        max_num_faces: int = 1,
        refine_landmarks: bool = True,
        performance_mode: bool = False,
    ) -> None:
        self._min_detection_confidence = min_detection_confidence
        self._max_num_faces = max_num_faces
        
        self.face_cascade = cv2.CascadeClassifier('haarcascade_frontalface_default.xml')
        self.facemark = cv2.face.createFacemarkLBF()
        try:
            self.facemark.loadModel('lbfmodel.yaml')
        except Exception as e:
            logger.error(f"Failed to load LBF model: {e}")
        
        logger.debug(f"FaceDetector (OpenCV LBF) initialized (Performance Mode: {performance_mode})")

    def detect(self, rgb_frame: np.ndarray) -> DetectionResult:
        """
        Detect face and extract landmarks from an RGB frame.
        """
        gray = cv2.cvtColor(rgb_frame, cv2.COLOR_RGB2GRAY)
        h, w = gray.shape[:2]

        faces = self.face_cascade.detectMultiScale(
            gray, scaleFactor=1.1, minNeighbors=5, minSize=(100, 100)
        )

        if len(faces) == 0:
            return DetectionResult(detected=False)
            
        # Get the largest face
        faces = sorted(faces, key=lambda f: f[2]*f[3], reverse=True)
        face_box = faces[0]

        ok, landmarks_collection = self.facemark.fit(gray, np.array([face_box]))
        if not ok or landmarks_collection is None:
            return DetectionResult(detected=False)

        pts = landmarks_collection[0][0] # shape (68, 2)
        
        # Add z-dimension (fake 0.0) to match the previous shape (N, 3)
        landmarks = np.zeros((68, 3), dtype=np.float32)
        landmarks[:, :2] = pts

        normalized = landmarks.copy()
        normalized[:, 0] /= w
        normalized[:, 1] /= h
        
        # We don't have true Z, but that's fine since we only use X,Y for EAR/MAR
        # and PnP uses only X,Y of image points anyway.

        return DetectionResult(
            detected=True,
            landmarks=landmarks,
            normalized_landmarks=normalized,
            image_width=w,
            image_height=h,
            detection_confidence=self._min_detection_confidence,
        )

    def draw_landmarks(
        self, frame: np.ndarray, result: DetectionResult,
        draw_eyes: bool = True, draw_iris: bool = True,
    ) -> np.ndarray:
        """Draw landmarks on frame for visualization."""
        if not result.detected or result.landmarks is None:
            return frame

        output = frame.copy()
        landmarks = result.landmarks

        if draw_eyes:
            for indices, color in [
                (self.LEFT_EYE_INDICES, (0, 255, 0)),
                (self.RIGHT_EYE_INDICES, (0, 255, 0)),
            ]:
                pts = landmarks[indices][:, :2].astype(np.int32)
                cv2.polylines(output, [pts], True, color, 1, cv2.LINE_AA)

        return output

    def get_camera_matrix(self, image_width: int, image_height: int) -> np.ndarray:
        """Compute camera intrinsic matrix for PnP."""
        focal_length = image_width
        center = (image_width / 2, image_height / 2)
        return np.array([
            [focal_length, 0, center[0]],
            [0, focal_length, center[1]],
            [0, 0, 1],
        ], dtype=np.float64)

    def close(self) -> None:
        pass

    def __enter__(self) -> "FaceDetector":
        return self

    def __exit__(self, *args: object) -> None:
        self.close()
