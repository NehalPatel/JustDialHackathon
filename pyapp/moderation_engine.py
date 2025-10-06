from typing import Dict, List, Tuple
from datetime import datetime
import json
from .video_analyzer import VideoAnalyzer

class ModerationEngine:
    """
    Core moderation engine that processes video analysis results
    and makes approve/reject decisions with detailed reasoning.
    """
    
    def __init__(self):
        self.video_analyzer = VideoAnalyzer()
        self.decision_history = []
    
    def moderate_video(self, video_path: str, config: Dict = None) -> Dict:
        """
        Main moderation function that analyzes a video and makes a decision.
        
        Args:
            video_path: Path to the video file
            config: Configuration dictionary with sensitivity settings
            
        Returns:
            Dictionary containing moderation decision and detailed analysis
        """
        if config is None:
            config = self._get_default_moderation_config()
        
        # Perform comprehensive video analysis
        analysis_results = self.video_analyzer.analyze_video(video_path, config)
        
        # Make moderation decision
        decision_result = self._make_moderation_decision(analysis_results, config)
        
        # Combine results
        moderation_result = {
            "video_path": video_path,
            "decision": decision_result["decision"],
            "confidence": decision_result["confidence"],
            "reasoning": decision_result["reasoning"],
            "violations": decision_result["violations"],
            "analysis_details": analysis_results,
            "config_used": config,
            "processed_at": datetime.now().isoformat(),
            "processing_time": decision_result.get("processing_time", 0)
        }
        
        # Store in decision history
        self.decision_history.append(moderation_result)
        
        return moderation_result
    
    def _make_moderation_decision(self, analysis: Dict, config: Dict) -> Dict:
        """
        Make approve/reject decision based on analysis results and configuration.
        """
        start_time = datetime.now()
        
        violations = []
        reasoning_parts = []
        overall_risk_score = 0.0
        
        # Check nudity violations
        nudity_result = self._check_nudity_violation(analysis.get("nudity_analysis", {}), config)
        if nudity_result["violation"]:
            violations.append(nudity_result)
            reasoning_parts.append(nudity_result["reason"])
            overall_risk_score += nudity_result["severity_score"]
        
        # Check copyright violations
        copyright_result = self._check_copyright_violation(analysis.get("copyright_analysis", {}), config)
        if copyright_result["violation"]:
            violations.append(copyright_result)
            reasoning_parts.append(copyright_result["reason"])
            overall_risk_score += copyright_result["severity_score"]
        
        # Check fraud violations
        fraud_result = self._check_fraud_violation(analysis.get("fraud_analysis", {}), config)
        if fraud_result["violation"]:
            violations.append(fraud_result)
            reasoning_parts.append(fraud_result["reason"])
            overall_risk_score += fraud_result["severity_score"]
        
        # Check technical quality issues
        technical_result = self._check_technical_violations(analysis.get("technical_analysis", {}), config)
        if technical_result["violation"]:
            violations.append(technical_result)
            reasoning_parts.append(technical_result["reason"])
            overall_risk_score += technical_result["severity_score"]
        
        # Make final decision
        decision = "rejected" if violations else "approved"
        confidence = self._calculate_confidence(overall_risk_score, violations)
        
        # Generate human-readable reasoning
        if decision == "rejected":
            reasoning = f"Video rejected due to: {'; '.join(reasoning_parts)}"
        else:
            reasoning = "Video approved - all content checks passed within acceptable thresholds"
        
        processing_time = (datetime.now() - start_time).total_seconds()
        
        return {
            "decision": decision,
            "confidence": confidence,
            "reasoning": reasoning,
            "violations": violations,
            "overall_risk_score": overall_risk_score,
            "processing_time": processing_time
        }
    
    def _check_nudity_violation(self, nudity_analysis: Dict, config: Dict) -> Dict:
        """Check if nudity analysis indicates a violation."""
        if "error" in nudity_analysis:
            return {"violation": False, "reason": "Nudity analysis failed"}
        
        score = nudity_analysis.get("overall_score", 0.0)
        category = nudity_analysis.get("category", "none")
        sensitivity = config.get("nudity_sensitivity", "moderate")
        
        # Define thresholds based on sensitivity
        thresholds = {
            "lenient": 0.8,
            "moderate": 0.6,
            "strict": 0.4
        }
        
        threshold = thresholds.get(sensitivity, 0.6)
        
        if score >= threshold:
            detections = nudity_analysis.get("detections", [])
            timestamps = [f"{d['timestamp']:.1f}s" for d in detections[:3]]  # Show first 3
            
            reason = f"Nudity detected (score: {score:.2f}, category: {category})"
            if timestamps:
                reason += f" at timestamps: {', '.join(timestamps)}"
            
            return {
                "violation": True,
                "type": "nudity",
                "reason": reason,
                "score": score,
                "category": category,
                "severity_score": min(score * 1.5, 1.0),
                "timestamps": [d['timestamp'] for d in detections]
            }
        
        return {"violation": False}
    
    def _check_copyright_violation(self, copyright_analysis: Dict, config: Dict) -> Dict:
        """Check if copyright analysis indicates a violation."""
        if "error" in copyright_analysis:
            return {"violation": False, "reason": "Copyright analysis failed"}
        
        score = copyright_analysis.get("overall_score", 0.0)
        threshold = config.get("copyright_threshold", 60) / 100.0
        
        if score >= threshold:
            potential_sources = copyright_analysis.get("potential_sources", [])
            audio_score = copyright_analysis.get("audio_analysis", {}).get("score", 0)
            visual_score = copyright_analysis.get("visual_analysis", {}).get("score", 0)
            
            reason = f"Copyright infringement detected (score: {score:.2f})"
            
            if audio_score > visual_score:
                reason += f" - primarily audio content (score: {audio_score:.2f})"
            else:
                reason += f" - primarily visual content (score: {visual_score:.2f})"
            
            if potential_sources:
                reason += f". Potential sources: {', '.join(potential_sources[:2])}"
            
            return {
                "violation": True,
                "type": "copyright",
                "reason": reason,
                "score": score,
                "severity_score": score,
                "potential_sources": potential_sources,
                "audio_score": audio_score,
                "visual_score": visual_score
            }
        
        return {"violation": False}
    
    def _check_fraud_violation(self, fraud_analysis: Dict, config: Dict) -> Dict:
        """Check if fraud analysis indicates a violation."""
        if "error" in fraud_analysis:
            return {"violation": False, "reason": "Fraud analysis failed"}
        
        score = fraud_analysis.get("score", 0.0)
        sensitivity = config.get("fraud_sensitivity", "moderate")
        
        # Define thresholds based on sensitivity
        thresholds = {
            "lenient": 0.8,
            "moderate": 0.6,
            "strict": 0.4
        }
        
        threshold = thresholds.get(sensitivity, 0.6)
        
        if score >= threshold:
            indicators = fraud_analysis.get("indicators", [])
            fraud_types = fraud_analysis.get("fraud_types", [])
            
            reason = f"Fraudulent content detected (score: {score:.2f})"
            
            if fraud_types:
                reason += f" - types: {', '.join(fraud_types)}"
            
            if indicators:
                reason += f". Indicators: {', '.join(indicators[:3])}"  # Show first 3
            
            return {
                "violation": True,
                "type": "fraud",
                "reason": reason,
                "score": score,
                "severity_score": score * 1.2,  # Fraud is considered more severe
                "indicators": indicators,
                "fraud_types": fraud_types
            }
        
        return {"violation": False}
    
    def _check_technical_violations(self, technical_analysis: Dict, config: Dict) -> Dict:
        """Check for technical quality violations."""
        if "error" in technical_analysis:
            return {"violation": False, "reason": "Technical analysis failed"}
        
        violations = []
        
        if technical_analysis.get("is_blurry", False):
            violations.append("video is too blurry")
        
        if technical_analysis.get("is_too_dark", False):
            violations.append("video is too dark")
        
        if technical_analysis.get("is_too_bright", False):
            violations.append("video is overexposed")
        
        quality_rating = technical_analysis.get("quality_rating", "good")
        if quality_rating == "poor" and config.get("reject_poor_quality", False):
            violations.append("poor technical quality")
        
        if violations:
            reason = f"Technical quality issues: {', '.join(violations)}"
            return {
                "violation": True,
                "type": "technical",
                "reason": reason,
                "severity_score": 0.3,  # Technical issues are less severe
                "quality_rating": quality_rating,
                "issues": violations
            }
        
        return {"violation": False}
    
    def _calculate_confidence(self, risk_score: float, violations: List[Dict]) -> float:
        """Calculate confidence level for the moderation decision."""
        if not violations:
            # High confidence for approved videos
            return min(0.9 + (1 - risk_score) * 0.1, 1.0)
        
        # For rejected videos, confidence depends on severity and number of violations
        base_confidence = 0.7
        severity_bonus = min(risk_score * 0.2, 0.2)
        violation_bonus = min(len(violations) * 0.05, 0.1)
        
        return min(base_confidence + severity_bonus + violation_bonus, 1.0)
    
    def get_moderation_statistics(self) -> Dict:
        """Get statistics about moderation decisions."""
        if not self.decision_history:
            return {
                "total_processed": 0,
                "approved": 0,
                "rejected": 0,
                "approval_rate": 0.0,
                "rejection_rate": 0.0,
                "violation_breakdown": {},
                "average_processing_time": 0.0
            }
        
        total = len(self.decision_history)
        approved = sum(1 for d in self.decision_history if d["decision"] == "approved")
        rejected = total - approved
        
        # Count violation types
        violation_counts = {}
        processing_times = []
        
        for decision in self.decision_history:
            processing_times.append(decision.get("processing_time", 0))
            
            for violation in decision.get("violations", []):
                violation_type = violation.get("type", "unknown")
                violation_counts[violation_type] = violation_counts.get(violation_type, 0) + 1
        
        return {
            "total_processed": total,
            "approved": approved,
            "rejected": rejected,
            "approval_rate": approved / total,
            "rejection_rate": rejected / total,
            "violation_breakdown": violation_counts,
            "average_processing_time": sum(processing_times) / len(processing_times) if processing_times else 0,
            "last_updated": datetime.now().isoformat()
        }
    
    def get_recent_decisions(self, limit: int = 10) -> List[Dict]:
        """Get recent moderation decisions."""
        return self.decision_history[-limit:] if self.decision_history else []
    
    def _get_default_moderation_config(self) -> Dict:
        """Get default moderation configuration."""
        return {
            "nudity_sensitivity": "moderate",
            "copyright_threshold": 60,
            "fraud_sensitivity": "strict",
            "reject_poor_quality": False,
            "blur_faces": True,
            "blur_violence": True,
            "auto_approve_threshold": 0.1,  # Auto-approve if risk score below this
            "auto_reject_threshold": 0.8    # Auto-reject if risk score above this
        }
    
    def update_config(self, new_config: Dict) -> Dict:
        """Update moderation configuration."""
        current_config = self._get_default_moderation_config()
        current_config.update(new_config)
        return current_config
    
    def export_decisions(self, format: str = "json") -> str:
        """Export decision history in specified format."""
        if format.lower() == "json":
            return json.dumps(self.decision_history, indent=2)
        else:
            raise ValueError(f"Unsupported export format: {format}")
    
    def clear_history(self):
        """Clear decision history."""
        self.decision_history = []