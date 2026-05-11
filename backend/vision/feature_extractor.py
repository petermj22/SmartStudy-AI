"""
Module: feature_extractor.py
Purpose: Extract facial features from MediaPipe landmarks:
         EAR, MAR, Head Pose, Gaze, Brow metrics.
Author: SmartStudy Team
Version: 1.0.0
"""

from __future__ import annotations

import time
from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple

import cv2
import numpy as np
from loguru import logger

from backend.vision.face_detector import DetectionResult, FaceDetector


@dataclass
class FaceFeatures:
    """Complete set of extracted facial features."""

    # Eye features
    left_ear: float = 0.3
    right_ear: float = 0.3
    avg_ear: float = 0.3
    ear_variance: float = 0.0

    # Mouth features
    mar: float = 0.3
    yawn_detected: float = 0.0

    # Head pose (degrees)
    head_pitch: float = 0.0
    head_yaw: float = 0.0
    head_roll: float = 0.0

    # Gaze
    gaze_x: float = 0.0
    gaze_y: float = 0.0

    # Micro-expressions
    brow_raise: float = 0.0
    eye_squint: float = 0.0

    # Derived (computed externally and merged in)
    gaze_stability: float = 1.0
    blink_rate: float = 15.0
    blink_duration_avg: float = 0.15
    eye_closure_ratio: float = 0.0
    head_movement_magnitude: float = 0.0
    head_stability: float = 1.0
    ear_trend: float = 0.0
    ear_mean: float = 0.3
    ear_std: float = 0.0
    time_of_day: float = 12.0
    session_duration: float = 0.0
    time_since_break: float = 0.0
    cumulative_fatigue_score: float = 0.0

    # Metadata
    face_detected: bool = True
    extraction_time_ms: float = 0.0

    def to_dict(self) -> Dict[str, float]:
        """Convert to flat dict for ML inference."""
        return {
            "avg_ear": self.avg_ear, "left_ear": self.left_ear,
            "right_ear": self.right_ear, "ear_variance": self.ear_variance,
            "mar": self.mar, "yawn_detected": self.yawn_detected,
            "head_pitch": self.head_pitch, "head_yaw": self.head_yaw,
            "head_roll": self.head_roll, "gaze_x": self.gaze_x,
            "gaze_y": self.gaze_y, "gaze_stability": self.gaze_stability,
            "blink_rate": self.blink_rate,
            "blink_duration_avg": self.blink_duration_avg,
            "eye_closure_ratio": self.eye_closure_ratio,
            "head_movement_magnitude": self.head_movement_magnitude,
            "head_stability": self.head_stability,
            "ear_trend": self.ear_trend, "ear_mean": self.ear_mean,
            "ear_std": self.ear_std, "brow_raise": self.brow_raise,
            "eye_squint": self.eye_squint,
            "time_of_day": self.time_of_day,
            "session_duration": self.session_duration,
            "time_since_break": self.time_since_break,
            "cumulative_fatigue_score": self.cumulative_fatigue_score,
        }


class FeatureExtractor:
    """
    Extracts physiological attention features from MediaPipe landmarks.
    All computations vectorized with NumPy. Target: <5ms per frame.
    """

    EAR_CLOSED_THRESHOLD: float = 0.21
    EAR_DROWSY_THRESHOLD: float = 0.25
    MAR_YAWN_THRESHOLD: float = 0.60

    def __init__(self, face_detector: Optional[FaceDetector] = None) -> None:
        self._detector = face_detector or FaceDetector()
        self._dist_coeffs = np.zeros((4, 1), dtype=np.float64)
        logger.debug("FeatureExtractor initialized")

    def extract(self, detection: DetectionResult) -> Optional[FaceFeatures]:
        """Extract all features from a DetectionResult."""
        if not detection.detected or detection.landmarks is None:
            return None

        t0 = time.perf_counter()
        lm = detection.landmarks
        features = FaceFeatures()

        # 1. Eye Aspect Ratios
        features.left_ear = self._compute_ear(lm, FaceDetector.LEFT_EYE_INDICES)
        features.right_ear = self._compute_ear(lm, FaceDetector.RIGHT_EYE_INDICES)
        features.avg_ear = (features.left_ear + features.right_ear) / 2.0
        features.ear_variance = float(np.var([features.left_ear, features.right_ear]))
        features.eye_closure_ratio = float(features.avg_ear < self.EAR_CLOSED_THRESHOLD)

        # 2. Mouth Aspect Ratio
        features.mar = self._compute_mar(lm)
        features.yawn_detected = float(features.mar > self.MAR_YAWN_THRESHOLD)

        # 3. Head pose estimation
        pitch, yaw, roll = self._estimate_head_pose(
            lm, detection.image_width, detection.image_height,
        )
        features.head_pitch = pitch
        features.head_yaw = yaw
        features.head_roll = roll

        # 4. Gaze direction (iris-based)
        gaze_x, gaze_y = self._compute_gaze(lm, detection.has_iris)
        features.gaze_x = gaze_x
        features.gaze_y = gaze_y

        # 5. Micro-expressions
        features.brow_raise = self._compute_brow_raise(lm)
        features.eye_squint = float(1.0 - features.avg_ear)

        features.extraction_time_ms = (time.perf_counter() - t0) * 1000
        features.face_detected = True
        return features

    def _compute_ear(self, landmarks: np.ndarray, eye_indices: List[int]) -> float:
        """
        Compute Eye Aspect Ratio (EAR).
        Formula: (||p2-p6|| + ||p3-p5||) / (2 * ||p1-p4||)
        Reference: Soukupová & Čech, 2016
        """
        pts = landmarks[eye_indices]
        v1 = float(np.linalg.norm(pts[1, :2] - pts[5, :2]))
        v2 = float(np.linalg.norm(pts[2, :2] - pts[4, :2]))
        h = float(np.linalg.norm(pts[0, :2] - pts[3, :2]))
        if h < 1e-6:
            return 0.3
        return (v1 + v2) / (2.0 * h)

    def _compute_mar(self, landmarks: np.ndarray) -> float:
        """Compute Mouth Aspect Ratio for yawn detection."""
        pts = landmarks[FaceDetector.MOUTH_INDICES]
        v1 = float(np.linalg.norm(pts[1, :2] - pts[5, :2]))
        v2 = float(np.linalg.norm(pts[2, :2] - pts[4, :2]))
        h = float(np.linalg.norm(pts[0, :2] - pts[3, :2]))
        if h < 1e-6:
            return 0.3
        return (v1 + v2) / (2.0 * h)

    def _estimate_head_pose(
        self, landmarks: np.ndarray, img_width: int, img_height: int,
    ) -> Tuple[float, float, float]:
        """Estimate head pose using PnP. Returns (pitch, yaw, roll) in degrees."""
        image_points = landmarks[FaceDetector.HEAD_POSE_INDICES, :2].astype(np.float64)
        camera_matrix = self._detector.get_camera_matrix(img_width, img_height)

        success, rotation_vec, translation_vec = cv2.solvePnP(
            FaceDetector.HEAD_MODEL_3D_POINTS, image_points,
            camera_matrix, self._dist_coeffs, flags=cv2.SOLVEPNP_ITERATIVE,
        )
        if not success:
            return 0.0, 0.0, 0.0

        rotation_mat, _ = cv2.Rodrigues(rotation_vec)
        pose_mat = cv2.hconcat((rotation_mat, translation_vec))
        _, _, _, _, _, _, euler_angles = cv2.decomposeProjectionMatrix(pose_mat)
        pitch, yaw, roll = euler_angles.flatten()[:3]

        return (
            float(np.clip(pitch, -90, 90)),
            float(np.clip(yaw, -90, 90)),
            float(np.clip(roll, -90, 90)),
        )

    def _compute_gaze(
        self, landmarks: np.ndarray, has_iris: bool,
    ) -> Tuple[float, float]:
        """Estimate gaze direction from iris positions."""
        if not has_iris or landmarks.shape[0] < 478:
            return 0.0, 0.0

        left_iris_center = landmarks[FaceDetector.LEFT_IRIS_INDICES].mean(axis=0)
        right_iris_center = landmarks[FaceDetector.RIGHT_IRIS_INDICES].mean(axis=0)

        left_eye_pts = landmarks[FaceDetector.LEFT_EYE_INDICES]
        right_eye_pts = landmarks[FaceDetector.RIGHT_EYE_INDICES]

        left_eye_center = left_eye_pts.mean(axis=0)
        right_eye_center = right_eye_pts.mean(axis=0)

        left_eye_width = float(np.linalg.norm(left_eye_pts[0, :2] - left_eye_pts[3, :2]))
        right_eye_width = float(np.linalg.norm(right_eye_pts[0, :2] - right_eye_pts[3, :2]))

        left_offset = (left_iris_center[:2] - left_eye_center[:2])
        right_offset = (right_iris_center[:2] - right_eye_center[:2])

        if left_eye_width > 0:
            left_offset = left_offset / left_eye_width
        if right_eye_width > 0:
            right_offset = right_offset / right_eye_width

        avg_offset = (left_offset + right_offset) / 2.0
        return (
            float(np.clip(avg_offset[0], -1, 1)),
            float(np.clip(avg_offset[1], -1, 1)),
        )

    def _compute_brow_raise(self, landmarks: np.ndarray) -> float:
        """Compute normalized brow raise distance."""
        left_brow = landmarks[FaceDetector.LEFT_BROW_INDICES].mean(axis=0)
        right_brow = landmarks[FaceDetector.RIGHT_BROW_INDICES].mean(axis=0)
        left_eye_center = landmarks[FaceDetector.LEFT_EYE_INDICES].mean(axis=0)
        right_eye_center = landmarks[FaceDetector.RIGHT_EYE_INDICES].mean(axis=0)

        left_dist = float(np.linalg.norm(left_brow[:2] - left_eye_center[:2]))
        right_dist = float(np.linalg.norm(right_brow[:2] - right_eye_center[:2]))
        avg_dist = (left_dist + right_dist) / 2.0

        # Face height in 68-point: chin is 8, top of nose bridge is 27
        if landmarks.shape[0] == 68:
            face_height = float(np.linalg.norm(landmarks[27, :2] - landmarks[8, :2])) * 1.5
        else:
            face_height = float(np.linalg.norm(landmarks[10, :2] - landmarks[152, :2]))
            
        if face_height > 0:
            avg_dist /= face_height
        return float(np.clip(avg_dist, 0, 1))
