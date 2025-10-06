import cv2
import numpy as np
import os
import hashlib
import json
from datetime import datetime
from typing import Dict, List, Tuple, Optional
from moviepy.editor import VideoFileClip
from PIL import Image
# import tensorflow as tf
# from transformers import pipeline

class VideoAnalyzer:
    """
    Comprehensive video analysis system for content moderation.
    Detects nudity, copyright infringement, fraud, and inappropriate content.
    """
    
    def __init__(self):
        self.nudity_threshold = 0.7
        self.copyright_threshold = 0.6
        self.fraud_threshold = 0.8
        self.supported_formats = ['.mp4', '.mov', '.avi', '.wmv', '.mkv', '.flv']
        
        # Initialize ML models (using lightweight alternatives for demo)
        self.text_classifier = None
        self.image_classifier = None
        self._initialize_models()
    
    def _initialize_models(self):
        """Initialize machine learning models for content analysis."""
        try:
            # For demo purposes, using simple rule-based analysis
            # In production, you would load actual ML models here
            self.text_classifier = None
            self.image_classifier = None
            print("Models initialized (demo mode)")
        except Exception as e:
            print(f"Warning: Could not initialize models: {e}")
            self.text_classifier = None
    
    def analyze_video(self, video_path: str, config: Dict = None) -> Dict:
        """
        Main analysis function that processes a video file.
        
        Args:
            video_path: Path to the video file
            config: Configuration dictionary with sensitivity settings
            
        Returns:
            Dictionary containing analysis results
        """
        if config is None:
            config = self._get_default_config()
        
        results = {
            "file_info": self._get_file_info(video_path),
            "nudity_analysis": self._analyze_nudity(video_path, config),
            "copyright_analysis": self._analyze_copyright(video_path, config),
            "fraud_analysis": self._analyze_fraud(video_path, config),
            "blur_analysis": self._analyze_blur_requirements(video_path, config),
            "technical_analysis": self._analyze_technical_quality(video_path),
            "timestamp": datetime.now().isoformat()
        }
        
        return results
    
    def _get_file_info(self, video_path: str) -> Dict:
        """Extract basic file information."""
        try:
            clip = VideoFileClip(video_path)
            file_size = os.path.getsize(video_path)
            
            # Generate file hash for duplicate detection
            with open(video_path, 'rb') as f:
                file_hash = hashlib.md5(f.read()).hexdigest()
            
            info = {
                "filename": os.path.basename(video_path),
                "duration": clip.duration,
                "fps": clip.fps,
                "resolution": f"{clip.w}x{clip.h}",
                "file_size": file_size,
                "file_hash": file_hash,
                "format": os.path.splitext(video_path)[1].lower()
            }
            
            clip.close()
            return info
            
        except Exception as e:
            return {"error": f"Could not extract file info: {str(e)}"}
    
    def _analyze_nudity(self, video_path: str, config: Dict) -> Dict:
        """
        Analyze video for nudity content using computer vision.
        """
        try:
            cap = cv2.VideoCapture(video_path)
            total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
            fps = cap.get(cv2.CAP_PROP_FPS)
            
            # Sample frames at regular intervals
            sample_interval = max(1, total_frames // 30)  # Sample ~30 frames
            nudity_detections = []
            max_nudity_score = 0.0
            
            for frame_num in range(0, total_frames, sample_interval):
                cap.set(cv2.CAP_PROP_POS_FRAMES, frame_num)
                ret, frame = cap.read()
                
                if not ret:
                    continue
                
                # Simple skin detection algorithm
                nudity_score = self._detect_skin_content(frame)
                timestamp = frame_num / fps
                
                if nudity_score > 0.3:  # Threshold for potential nudity
                    nudity_detections.append({
                        "timestamp": timestamp,
                        "score": nudity_score,
                        "frame_number": frame_num
                    })
                
                max_nudity_score = max(max_nudity_score, nudity_score)
            
            cap.release()
            
            # Categorize nudity type based on score
            nudity_category = self._categorize_nudity(max_nudity_score)
            
            return {
                "overall_score": max_nudity_score,
                "category": nudity_category,
                "detections": nudity_detections,
                "frames_analyzed": len(range(0, total_frames, sample_interval)),
                "sensitivity_level": config.get("nudity_sensitivity", "moderate")
            }
            
        except Exception as e:
            return {"error": f"Nudity analysis failed: {str(e)}"}
    
    def _detect_skin_content(self, frame) -> float:
        """
        Simple skin detection algorithm using HSV color space.
        Returns a score between 0 and 1 indicating skin content.
        """
        # Convert to HSV
        hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
        
        # Define skin color range in HSV
        lower_skin = np.array([0, 20, 70], dtype=np.uint8)
        upper_skin = np.array([20, 255, 255], dtype=np.uint8)
        
        # Create mask for skin pixels
        skin_mask = cv2.inRange(hsv, lower_skin, upper_skin)
        
        # Calculate percentage of skin pixels
        total_pixels = frame.shape[0] * frame.shape[1]
        skin_pixels = cv2.countNonZero(skin_mask)
        skin_percentage = skin_pixels / total_pixels
        
        # Apply additional heuristics
        # Check for large connected skin regions (potential nudity indicator)
        contours, _ = cv2.findContours(skin_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        large_skin_regions = sum(1 for contour in contours if cv2.contourArea(contour) > 1000)
        
        # Combine metrics
        base_score = min(skin_percentage * 2, 1.0)  # Scale skin percentage
        region_bonus = min(large_skin_regions * 0.1, 0.3)  # Bonus for large regions
        
        return min(base_score + region_bonus, 1.0)
    
    def _categorize_nudity(self, score: float) -> str:
        """Categorize nudity based on detection score."""
        if score < 0.3:
            return "none"
        elif score < 0.5:
            return "suggestive"
        elif score < 0.7:
            return "partial"
        else:
            return "explicit"
    
    def _analyze_copyright(self, video_path: str, config: Dict) -> Dict:
        """
        Analyze video for potential copyright infringement.
        """
        try:
            # Audio fingerprinting for music detection
            audio_analysis = self._analyze_audio_copyright(video_path)
            
            # Visual content analysis
            visual_analysis = self._analyze_visual_copyright(video_path)
            
            # Combine scores
            overall_score = max(audio_analysis.get("score", 0), visual_analysis.get("score", 0))
            
            return {
                "overall_score": overall_score,
                "audio_analysis": audio_analysis,
                "visual_analysis": visual_analysis,
                "potential_sources": self._identify_potential_sources(video_path),
                "confidence": min(overall_score * 1.2, 1.0)
            }
            
        except Exception as e:
            return {"error": f"Copyright analysis failed: {str(e)}"}
    
    def _analyze_audio_copyright(self, video_path: str) -> Dict:
        """Analyze audio track for copyrighted music."""
        try:
            # Extract audio features
            clip = VideoFileClip(video_path)
            if clip.audio is None:
                return {"score": 0.0, "reason": "No audio track"}
            
            # Simple audio analysis - in production, this would use audio fingerprinting
            audio_array = clip.audio.to_soundarray()
            clip.close()
            
            # Analyze audio characteristics
            if len(audio_array.shape) > 1:
                audio_mono = np.mean(audio_array, axis=1)
            else:
                audio_mono = audio_array
            
            # Simple heuristics for music detection
            # Check for consistent rhythm patterns, frequency distribution, etc.
            score = self._detect_music_patterns(audio_mono)
            
            return {
                "score": score,
                "duration": len(audio_mono) / 22050,  # Assuming 22050 Hz sample rate
                "has_music": score > 0.5
            }
            
        except Exception as e:
            return {"score": 0.0, "error": str(e)}
    
    def _detect_music_patterns(self, audio_data) -> float:
        """Simple music detection based on audio characteristics."""
        try:
            # Calculate basic audio features
            rms_energy = np.sqrt(np.mean(audio_data**2))
            zero_crossing_rate = np.mean(np.abs(np.diff(np.sign(audio_data))))
            
            # Simple heuristic: music typically has higher energy and lower ZCR
            music_score = min(rms_energy * 10, 1.0) * (1 - min(zero_crossing_rate, 1.0))
            
            return music_score
            
        except Exception:
            return 0.0
    
    def _analyze_visual_copyright(self, video_path: str) -> Dict:
        """Analyze visual content for copyrighted material."""
        try:
            cap = cv2.VideoCapture(video_path)
            total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
            
            # Sample frames for logo/watermark detection
            sample_interval = max(1, total_frames // 20)
            logo_detections = 0
            
            for frame_num in range(0, total_frames, sample_interval):
                cap.set(cv2.CAP_PROP_POS_FRAMES, frame_num)
                ret, frame = cap.read()
                
                if not ret:
                    continue
                
                # Simple logo/watermark detection
                if self._detect_logos_watermarks(frame):
                    logo_detections += 1
            
            cap.release()
            
            # Calculate score based on logo detections
            frames_analyzed = len(range(0, total_frames, sample_interval))
            logo_ratio = logo_detections / max(frames_analyzed, 1)
            
            return {
                "score": min(logo_ratio * 2, 1.0),
                "logo_detections": logo_detections,
                "frames_analyzed": frames_analyzed
            }
            
        except Exception as e:
            return {"score": 0.0, "error": str(e)}
    
    def _detect_logos_watermarks(self, frame) -> bool:
        """Simple logo/watermark detection."""
        # Convert to grayscale
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        
        # Look for text-like regions (potential watermarks)
        # This is a simplified approach - production would use OCR and template matching
        edges = cv2.Canny(gray, 50, 150)
        contours, _ = cv2.findContours(edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        # Count small rectangular regions (potential logos/watermarks)
        logo_candidates = 0
        for contour in contours:
            area = cv2.contourArea(contour)
            if 100 < area < 5000:  # Size range for typical logos
                x, y, w, h = cv2.boundingRect(contour)
                aspect_ratio = w / h
                if 0.5 < aspect_ratio < 3.0:  # Reasonable aspect ratio
                    logo_candidates += 1
        
        return logo_candidates > 3  # Threshold for logo detection
    
    def _identify_potential_sources(self, video_path: str) -> List[str]:
        """Identify potential copyright sources (simplified)."""
        # In production, this would use content ID databases
        filename = os.path.basename(video_path).lower()
        
        potential_sources = []
        
        # Simple keyword matching
        movie_keywords = ['movie', 'film', 'cinema', 'trailer', 'clip']
        music_keywords = ['song', 'music', 'audio', 'track', 'album']
        tv_keywords = ['episode', 'series', 'show', 'tv']
        
        for keyword in movie_keywords:
            if keyword in filename:
                potential_sources.append(f"Movie content (keyword: {keyword})")
        
        for keyword in music_keywords:
            if keyword in filename:
                potential_sources.append(f"Music content (keyword: {keyword})")
        
        for keyword in tv_keywords:
            if keyword in filename:
                potential_sources.append(f"TV content (keyword: {keyword})")
        
        return potential_sources
    
    def _analyze_fraud(self, video_path: str, config: Dict) -> Dict:
        """
        Analyze video for fraudulent content.
        """
        try:
            # Extract text from video frames (OCR)
            extracted_text = self._extract_text_from_video(video_path)
            
            # Analyze text for fraud indicators
            fraud_indicators = self._detect_fraud_patterns(extracted_text)
            
            # Calculate overall fraud score
            fraud_score = len(fraud_indicators) * 0.2  # Each indicator adds 0.2 to score
            fraud_score = min(fraud_score, 1.0)
            
            return {
                "score": fraud_score,
                "indicators": fraud_indicators,
                "extracted_text": extracted_text[:500],  # Limit text length
                "fraud_types": self._categorize_fraud_types(fraud_indicators)
            }
            
        except Exception as e:
            return {"error": f"Fraud analysis failed: {str(e)}"}
    
    def _extract_text_from_video(self, video_path: str) -> str:
        """Extract text from video frames using OCR."""
        try:
            cap = cv2.VideoCapture(video_path)
            total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
            
            extracted_text = ""
            sample_interval = max(1, total_frames // 10)  # Sample 10 frames
            
            for frame_num in range(0, total_frames, sample_interval):
                cap.set(cv2.CAP_PROP_POS_FRAMES, frame_num)
                ret, frame = cap.read()
                
                if not ret:
                    continue
                
                # Simple text detection (in production, use pytesseract)
                gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
                
                # Look for text-like regions
                # This is simplified - real OCR would be more sophisticated
                text_regions = self._detect_text_regions(gray)
                extracted_text += " " + " ".join(text_regions)
            
            cap.release()
            return extracted_text.strip()
            
        except Exception:
            return ""
    
    def _detect_text_regions(self, gray_frame) -> List[str]:
        """Simple text region detection (placeholder for OCR)."""
        # This is a placeholder - in production, use pytesseract or similar
        # For demo purposes, return empty list
        return []
    
    def _detect_fraud_patterns(self, text: str) -> List[str]:
        """Detect fraud patterns in extracted text."""
        fraud_indicators = []
        text_lower = text.lower()
        
        # Common fraud keywords
        fraud_keywords = [
            'free money', 'get rich quick', 'guaranteed income', 'work from home',
            'click here', 'limited time', 'act now', 'urgent', 'congratulations',
            'you have won', 'claim your prize', 'no risk', 'easy money',
            'investment opportunity', 'double your money', 'bitcoin', 'cryptocurrency'
        ]
        
        for keyword in fraud_keywords:
            if keyword in text_lower:
                fraud_indicators.append(f"Suspicious keyword: {keyword}")
        
        # Check for excessive use of capital letters
        if len(text) > 0:
            caps_ratio = sum(1 for c in text if c.isupper()) / len(text)
            if caps_ratio > 0.3:
                fraud_indicators.append("Excessive use of capital letters")
        
        # Check for multiple exclamation marks
        if text.count('!') > 3:
            fraud_indicators.append("Excessive exclamation marks")
        
        return fraud_indicators
    
    def _categorize_fraud_types(self, indicators: List[str]) -> List[str]:
        """Categorize types of fraud detected."""
        fraud_types = []
        
        for indicator in indicators:
            if any(keyword in indicator.lower() for keyword in ['money', 'income', 'rich', 'investment']):
                fraud_types.append("Financial fraud")
            elif any(keyword in indicator.lower() for keyword in ['prize', 'won', 'congratulations']):
                fraud_types.append("Prize scam")
            elif any(keyword in indicator.lower() for keyword in ['click', 'link', 'urgent']):
                fraud_types.append("Phishing attempt")
        
        return list(set(fraud_types))  # Remove duplicates
    
    def _analyze_blur_requirements(self, video_path: str, config: Dict) -> Dict:
        """
        Analyze video for content that requires blurring.
        """
        try:
            cap = cv2.VideoCapture(video_path)
            total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
            fps = cap.get(cv2.CAP_PROP_FPS)
            
            blur_regions = []
            sample_interval = max(1, total_frames // 20)
            
            for frame_num in range(0, total_frames, sample_interval):
                cap.set(cv2.CAP_PROP_POS_FRAMES, frame_num)
                ret, frame = cap.read()
                
                if not ret:
                    continue
                
                timestamp = frame_num / fps
                
                # Detect faces (potential PII)
                faces = self._detect_faces(frame)
                if faces:
                    blur_regions.append({
                        "timestamp": timestamp,
                        "reason": "Personal identifiable information (faces)",
                        "regions": faces,
                        "severity": "medium"
                    })
                
                # Detect violence indicators
                violence_score = self._detect_violence(frame)
                if violence_score > 0.5:
                    blur_regions.append({
                        "timestamp": timestamp,
                        "reason": "Violent content",
                        "score": violence_score,
                        "severity": "high"
                    })
            
            cap.release()
            
            return {
                "requires_blur": len(blur_regions) > 0,
                "blur_regions": blur_regions,
                "total_regions": len(blur_regions)
            }
            
        except Exception as e:
            return {"error": f"Blur analysis failed: {str(e)}"}
    
    def _detect_faces(self, frame) -> List[Dict]:
        """Detect faces in frame using OpenCV."""
        try:
            # Load face cascade classifier
            face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
            
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            faces = face_cascade.detectMultiScale(gray, 1.1, 4)
            
            face_regions = []
            for (x, y, w, h) in faces:
                face_regions.append({
                    "x": int(x),
                    "y": int(y),
                    "width": int(w),
                    "height": int(h)
                })
            
            return face_regions
            
        except Exception:
            return []
    
    def _detect_violence(self, frame) -> float:
        """Simple violence detection based on color and motion patterns."""
        try:
            # Convert to HSV for better color analysis
            hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
            
            # Detect red regions (potential blood/violence indicator)
            lower_red1 = np.array([0, 50, 50])
            upper_red1 = np.array([10, 255, 255])
            lower_red2 = np.array([170, 50, 50])
            upper_red2 = np.array([180, 255, 255])
            
            mask1 = cv2.inRange(hsv, lower_red1, upper_red1)
            mask2 = cv2.inRange(hsv, lower_red2, upper_red2)
            red_mask = mask1 + mask2
            
            red_percentage = cv2.countNonZero(red_mask) / (frame.shape[0] * frame.shape[1])
            
            # Simple heuristic: high red content might indicate violence
            violence_score = min(red_percentage * 5, 1.0)
            
            return violence_score
            
        except Exception:
            return 0.0
    
    def _analyze_technical_quality(self, video_path: str) -> Dict:
        """Analyze technical quality of the video."""
        try:
            cap = cv2.VideoCapture(video_path)
            
            # Sample a few frames for quality analysis
            total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
            sample_frames = min(10, total_frames)
            
            blur_scores = []
            brightness_scores = []
            
            for i in range(sample_frames):
                frame_num = (total_frames // sample_frames) * i
                cap.set(cv2.CAP_PROP_POS_FRAMES, frame_num)
                ret, frame = cap.read()
                
                if not ret:
                    continue
                
                # Calculate blur score
                gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
                blur_score = cv2.Laplacian(gray, cv2.CV_64F).var()
                blur_scores.append(blur_score)
                
                # Calculate brightness
                brightness = np.mean(gray)
                brightness_scores.append(brightness)
            
            cap.release()
            
            avg_blur = np.mean(blur_scores) if blur_scores else 0
            avg_brightness = np.mean(brightness_scores) if brightness_scores else 0
            
            return {
                "blur_score": avg_blur,
                "brightness_score": avg_brightness,
                "quality_rating": self._rate_quality(avg_blur, avg_brightness),
                "is_blurry": avg_blur < 100,  # Threshold for blur detection
                "is_too_dark": avg_brightness < 50,
                "is_too_bright": avg_brightness > 200
            }
            
        except Exception as e:
            return {"error": f"Technical analysis failed: {str(e)}"}
    
    def _rate_quality(self, blur_score: float, brightness: float) -> str:
        """Rate overall video quality."""
        if blur_score < 50:
            return "poor"
        elif blur_score < 150:
            return "fair"
        elif blur_score < 300:
            return "good"
        else:
            return "excellent"
    
    def _get_default_config(self) -> Dict:
        """Get default configuration settings."""
        return {
            "nudity_sensitivity": "moderate",
            "copyright_threshold": 60,
            "fraud_sensitivity": "strict",
            "blur_faces": True,
            "blur_violence": True
        }