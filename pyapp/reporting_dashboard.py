"""
Reporting Dashboard for Video Auto-Moderation System
Provides analytics, metrics, and reporting capabilities
"""

import json
import sqlite3
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple
from pathlib import Path
import logging
from collections import defaultdict, Counter
import statistics

class ReportingDashboard:
    """Comprehensive reporting and analytics dashboard"""
    
    def __init__(self, db_path: str = "moderation.db"):
        self.db_path = db_path
        self.logger = logging.getLogger(__name__)
        
        # Initialize analytics database
        self._init_analytics_db()
    
    def _init_analytics_db(self):
        """Initialize analytics database tables"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Analytics events table
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS analytics_events (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        event_type TEXT NOT NULL,
                        event_data TEXT,
                        timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                        session_id TEXT,
                        user_agent TEXT,
                        ip_address TEXT
                    )
                ''')
                
                # Performance metrics table
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS performance_metrics (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        metric_name TEXT NOT NULL,
                        metric_value REAL NOT NULL,
                        metric_unit TEXT,
                        timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                        context TEXT
                    )
                ''')
                
                # System health table
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS system_health (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        cpu_usage REAL,
                        memory_usage REAL,
                        disk_usage REAL,
                        active_processes INTEGER,
                        timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
                    )
                ''')
                
                conn.commit()
                
        except Exception as e:
            self.logger.error(f"Failed to initialize analytics database: {e}")
    
    def get_overview_stats(self, days: int = 30) -> Dict[str, Any]:
        """Get overview statistics for the dashboard"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Date range
                end_date = datetime.now()
                start_date = end_date - timedelta(days=days)
                
                # Total videos processed
                cursor.execute('''
                    SELECT COUNT(*) FROM video_results 
                    WHERE created_at >= ? AND created_at <= ?
                ''', (start_date.isoformat(), end_date.isoformat()))
                total_videos = cursor.fetchone()[0]
                
                # Approved vs rejected
                cursor.execute('''
                    SELECT decision, COUNT(*) FROM video_results 
                    WHERE created_at >= ? AND created_at <= ?
                    GROUP BY decision
                ''', (start_date.isoformat(), end_date.isoformat()))
                
                decision_counts = dict(cursor.fetchall())
                approved = decision_counts.get('approved', 0)
                rejected = decision_counts.get('rejected', 0)
                
                # Average confidence
                cursor.execute('''
                    SELECT AVG(confidence) FROM video_results 
                    WHERE created_at >= ? AND created_at <= ?
                ''', (start_date.isoformat(), end_date.isoformat()))
                avg_confidence = cursor.fetchone()[0] or 0
                
                # Processing time statistics
                cursor.execute('''
                    SELECT processing_time FROM video_results 
                    WHERE created_at >= ? AND created_at <= ? AND processing_time IS NOT NULL
                ''', (start_date.isoformat(), end_date.isoformat()))
                
                processing_times = [row[0] for row in cursor.fetchall()]
                avg_processing_time = statistics.mean(processing_times) if processing_times else 0
                
                # Violation types
                cursor.execute('''
                    SELECT violations FROM video_results 
                    WHERE created_at >= ? AND created_at <= ? AND violations IS NOT NULL
                ''', (start_date.isoformat(), end_date.isoformat()))
                
                violation_counter = Counter()
                for row in cursor.fetchall():
                    try:
                        violations = json.loads(row[0])
                        for violation in violations:
                            violation_counter[violation] += 1
                    except (json.JSONDecodeError, TypeError):
                        continue
                
                return {
                    "period_days": days,
                    "total_videos": total_videos,
                    "approved": approved,
                    "rejected": rejected,
                    "approval_rate": (approved / total_videos * 100) if total_videos > 0 else 0,
                    "avg_confidence": round(avg_confidence, 2),
                    "avg_processing_time": round(avg_processing_time, 2),
                    "top_violations": dict(violation_counter.most_common(5)),
                    "daily_breakdown": self._get_daily_breakdown(start_date, end_date)
                }
                
        except Exception as e:
            self.logger.error(f"Failed to get overview stats: {e}")
            return {}
    
    def get_detailed_analytics(self, days: int = 30) -> Dict[str, Any]:
        """Get detailed analytics data"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                end_date = datetime.now()
                start_date = end_date - timedelta(days=days)
                
                # Confidence distribution
                cursor.execute('''
                    SELECT confidence FROM video_results 
                    WHERE created_at >= ? AND created_at <= ?
                ''', (start_date.isoformat(), end_date.isoformat()))
                
                confidences = [row[0] for row in cursor.fetchall()]
                confidence_distribution = self._calculate_distribution(confidences, bins=10)
                
                # Processing time distribution
                cursor.execute('''
                    SELECT processing_time FROM video_results 
                    WHERE created_at >= ? AND created_at <= ? AND processing_time IS NOT NULL
                ''', (start_date.isoformat(), end_date.isoformat()))
                
                processing_times = [row[0] for row in cursor.fetchall()]
                time_distribution = self._calculate_distribution(processing_times, bins=8)
                
                # File size analysis
                cursor.execute('''
                    SELECT file_size FROM video_results 
                    WHERE created_at >= ? AND created_at <= ? AND file_size IS NOT NULL
                ''', (start_date.isoformat(), end_date.isoformat()))
                
                file_sizes = [row[0] for row in cursor.fetchall()]
                size_distribution = self._calculate_size_distribution(file_sizes)
                
                # Hourly activity pattern
                hourly_activity = self._get_hourly_activity(start_date, end_date)
                
                # Detection accuracy metrics
                accuracy_metrics = self._calculate_accuracy_metrics(start_date, end_date)
                
                return {
                    "confidence_distribution": confidence_distribution,
                    "processing_time_distribution": time_distribution,
                    "file_size_distribution": size_distribution,
                    "hourly_activity": hourly_activity,
                    "accuracy_metrics": accuracy_metrics,
                    "trend_analysis": self._get_trend_analysis(start_date, end_date)
                }
                
        except Exception as e:
            self.logger.error(f"Failed to get detailed analytics: {e}")
            return {}
    
    def get_performance_metrics(self, hours: int = 24) -> Dict[str, Any]:
        """Get system performance metrics"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                end_time = datetime.now()
                start_time = end_time - timedelta(hours=hours)
                
                # Get performance metrics
                cursor.execute('''
                    SELECT metric_name, metric_value, timestamp FROM performance_metrics 
                    WHERE timestamp >= ? AND timestamp <= ?
                    ORDER BY timestamp DESC
                ''', (start_time.isoformat(), end_time.isoformat()))
                
                metrics_data = defaultdict(list)
                for metric_name, value, timestamp in cursor.fetchall():
                    metrics_data[metric_name].append({
                        "value": value,
                        "timestamp": timestamp
                    })
                
                # Calculate statistics for each metric
                performance_stats = {}
                for metric_name, values in metrics_data.items():
                    metric_values = [item["value"] for item in values]
                    if metric_values:
                        performance_stats[metric_name] = {
                            "current": metric_values[0],
                            "average": statistics.mean(metric_values),
                            "min": min(metric_values),
                            "max": max(metric_values),
                            "count": len(metric_values),
                            "trend": self._calculate_trend(metric_values)
                        }
                
                # System health data
                cursor.execute('''
                    SELECT cpu_usage, memory_usage, disk_usage, active_processes, timestamp 
                    FROM system_health 
                    WHERE timestamp >= ? AND timestamp <= ?
                    ORDER BY timestamp DESC
                ''', (start_time.isoformat(), end_time.isoformat()))
                
                health_data = cursor.fetchall()
                
                return {
                    "performance_metrics": performance_stats,
                    "system_health": self._process_health_data(health_data),
                    "alerts": self._generate_performance_alerts(performance_stats)
                }
                
        except Exception as e:
            self.logger.error(f"Failed to get performance metrics: {e}")
            return {}
    
    def get_violation_analysis(self, days: int = 30) -> Dict[str, Any]:
        """Get detailed violation analysis"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                end_date = datetime.now()
                start_date = end_date - timedelta(days=days)
                
                # Get all violations
                cursor.execute('''
                    SELECT violations, confidence, decision, created_at FROM video_results 
                    WHERE created_at >= ? AND created_at <= ? AND violations IS NOT NULL
                ''', (start_date.isoformat(), end_date.isoformat()))
                
                violation_data = []
                for violations_json, confidence, decision, created_at in cursor.fetchall():
                    try:
                        violations = json.loads(violations_json)
                        violation_data.append({
                            "violations": violations,
                            "confidence": confidence,
                            "decision": decision,
                            "created_at": created_at
                        })
                    except (json.JSONDecodeError, TypeError):
                        continue
                
                # Analyze violations
                violation_stats = defaultdict(lambda: {
                    "count": 0,
                    "avg_confidence": 0,
                    "rejection_rate": 0,
                    "confidences": []
                })
                
                for item in violation_data:
                    for violation in item["violations"]:
                        stats = violation_stats[violation]
                        stats["count"] += 1
                        stats["confidences"].append(item["confidence"])
                        if item["decision"] == "rejected":
                            stats["rejection_rate"] += 1
                
                # Calculate final statistics
                for violation, stats in violation_stats.items():
                    if stats["confidences"]:
                        stats["avg_confidence"] = statistics.mean(stats["confidences"])
                        stats["rejection_rate"] = (stats["rejection_rate"] / stats["count"]) * 100
                    del stats["confidences"]  # Remove raw data
                
                # Violation trends over time
                violation_trends = self._get_violation_trends(violation_data, days)
                
                return {
                    "violation_statistics": dict(violation_stats),
                    "violation_trends": violation_trends,
                    "severity_analysis": self._analyze_violation_severity(violation_data),
                    "correlation_analysis": self._analyze_violation_correlations(violation_data)
                }
                
        except Exception as e:
            self.logger.error(f"Failed to get violation analysis: {e}")
            return {}
    
    def generate_report(self, report_type: str = "comprehensive", days: int = 30) -> Dict[str, Any]:
        """Generate comprehensive report"""
        try:
            report_data = {
                "report_type": report_type,
                "generated_at": datetime.now().isoformat(),
                "period_days": days,
                "overview": self.get_overview_stats(days),
                "analytics": self.get_detailed_analytics(days),
                "violations": self.get_violation_analysis(days),
                "performance": self.get_performance_metrics(24),
                "recommendations": self._generate_recommendations(days)
            }
            
            return report_data
            
        except Exception as e:
            self.logger.error(f"Failed to generate report: {e}")
            return {}
    
    def export_report(self, report_data: Dict[str, Any], export_path: str, format_type: str = "json") -> bool:
        """Export report to file"""
        try:
            export_file = Path(export_path)
            export_file.parent.mkdir(parents=True, exist_ok=True)
            
            if format_type.lower() == "json":
                with open(export_file, 'w') as f:
                    json.dump(report_data, f, indent=2, default=str)
            else:
                # Could add CSV, PDF export here
                return False
            
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to export report: {e}")
            return False
    
    def log_analytics_event(self, event_type: str, event_data: Dict[str, Any] = None, 
                           session_id: str = None, user_agent: str = None, ip_address: str = None):
        """Log analytics event"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                cursor.execute('''
                    INSERT INTO analytics_events 
                    (event_type, event_data, session_id, user_agent, ip_address)
                    VALUES (?, ?, ?, ?, ?)
                ''', (
                    event_type,
                    json.dumps(event_data) if event_data else None,
                    session_id,
                    user_agent,
                    ip_address
                ))
                
                conn.commit()
                
        except Exception as e:
            self.logger.error(f"Failed to log analytics event: {e}")
    
    def log_performance_metric(self, metric_name: str, metric_value: float, 
                              metric_unit: str = None, context: str = None):
        """Log performance metric"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                cursor.execute('''
                    INSERT INTO performance_metrics 
                    (metric_name, metric_value, metric_unit, context)
                    VALUES (?, ?, ?, ?)
                ''', (metric_name, metric_value, metric_unit, context))
                
                conn.commit()
                
        except Exception as e:
            self.logger.error(f"Failed to log performance metric: {e}")
    
    def _get_daily_breakdown(self, start_date: datetime, end_date: datetime) -> List[Dict[str, Any]]:
        """Get daily breakdown of video processing"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                cursor.execute('''
                    SELECT DATE(created_at) as date, decision, COUNT(*) 
                    FROM video_results 
                    WHERE created_at >= ? AND created_at <= ?
                    GROUP BY DATE(created_at), decision
                    ORDER BY date
                ''', (start_date.isoformat(), end_date.isoformat()))
                
                daily_data = defaultdict(lambda: {"approved": 0, "rejected": 0, "total": 0})
                
                for date, decision, count in cursor.fetchall():
                    daily_data[date][decision] = count
                    daily_data[date]["total"] += count
                
                return [
                    {"date": date, **data} 
                    for date, data in sorted(daily_data.items())
                ]
                
        except Exception:
            return []
    
    def _calculate_distribution(self, values: List[float], bins: int = 10) -> List[Dict[str, Any]]:
        """Calculate distribution of values"""
        if not values:
            return []
        
        try:
            min_val, max_val = min(values), max(values)
            bin_size = (max_val - min_val) / bins
            
            distribution = []
            for i in range(bins):
                bin_start = min_val + i * bin_size
                bin_end = bin_start + bin_size
                
                count = sum(1 for v in values if bin_start <= v < bin_end)
                if i == bins - 1:  # Include max value in last bin
                    count = sum(1 for v in values if bin_start <= v <= bin_end)
                
                distribution.append({
                    "range": f"{bin_start:.1f}-{bin_end:.1f}",
                    "count": count,
                    "percentage": (count / len(values)) * 100
                })
            
            return distribution
            
        except Exception:
            return []
    
    def _calculate_size_distribution(self, file_sizes: List[int]) -> List[Dict[str, Any]]:
        """Calculate file size distribution"""
        if not file_sizes:
            return []
        
        try:
            # Define size ranges in bytes
            ranges = [
                (0, 10*1024*1024, "< 10MB"),
                (10*1024*1024, 50*1024*1024, "10-50MB"),
                (50*1024*1024, 100*1024*1024, "50-100MB"),
                (100*1024*1024, 250*1024*1024, "100-250MB"),
                (250*1024*1024, 500*1024*1024, "250-500MB"),
                (500*1024*1024, float('inf'), "> 500MB")
            ]
            
            distribution = []
            total_files = len(file_sizes)
            
            for min_size, max_size, label in ranges:
                count = sum(1 for size in file_sizes if min_size <= size < max_size)
                distribution.append({
                    "range": label,
                    "count": count,
                    "percentage": (count / total_files) * 100
                })
            
            return distribution
            
        except Exception:
            return []
    
    def _get_hourly_activity(self, start_date: datetime, end_date: datetime) -> List[Dict[str, Any]]:
        """Get hourly activity pattern"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                cursor.execute('''
                    SELECT strftime('%H', created_at) as hour, COUNT(*) 
                    FROM video_results 
                    WHERE created_at >= ? AND created_at <= ?
                    GROUP BY strftime('%H', created_at)
                    ORDER BY hour
                ''', (start_date.isoformat(), end_date.isoformat()))
                
                hourly_data = {f"{i:02d}": 0 for i in range(24)}
                
                for hour, count in cursor.fetchall():
                    hourly_data[hour] = count
                
                return [
                    {"hour": hour, "count": count} 
                    for hour, count in hourly_data.items()
                ]
                
        except Exception:
            return []
    
    def _calculate_accuracy_metrics(self, start_date: datetime, end_date: datetime) -> Dict[str, float]:
        """Calculate detection accuracy metrics"""
        # This would require manual review data for true accuracy calculation
        # For now, return confidence-based metrics
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                cursor.execute('''
                    SELECT confidence, decision FROM video_results 
                    WHERE created_at >= ? AND created_at <= ?
                ''', (start_date.isoformat(), end_date.isoformat()))
                
                results = cursor.fetchall()
                
                if not results:
                    return {}
                
                high_confidence = sum(1 for conf, _ in results if conf >= 80)
                medium_confidence = sum(1 for conf, _ in results if 60 <= conf < 80)
                low_confidence = sum(1 for conf, _ in results if conf < 60)
                
                total = len(results)
                
                return {
                    "high_confidence_rate": (high_confidence / total) * 100,
                    "medium_confidence_rate": (medium_confidence / total) * 100,
                    "low_confidence_rate": (low_confidence / total) * 100,
                    "avg_confidence": statistics.mean([conf for conf, _ in results])
                }
                
        except Exception:
            return {}
    
    def _get_trend_analysis(self, start_date: datetime, end_date: datetime) -> Dict[str, Any]:
        """Analyze trends over time"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Weekly trends
                cursor.execute('''
                    SELECT strftime('%Y-%W', created_at) as week, 
                           COUNT(*) as total,
                           AVG(confidence) as avg_confidence,
                           SUM(CASE WHEN decision = 'approved' THEN 1 ELSE 0 END) as approved
                    FROM video_results 
                    WHERE created_at >= ? AND created_at <= ?
                    GROUP BY strftime('%Y-%W', created_at)
                    ORDER BY week
                ''', (start_date.isoformat(), end_date.isoformat()))
                
                weekly_data = []
                for week, total, avg_conf, approved in cursor.fetchall():
                    weekly_data.append({
                        "week": week,
                        "total": total,
                        "avg_confidence": avg_conf,
                        "approval_rate": (approved / total) * 100 if total > 0 else 0
                    })
                
                return {
                    "weekly_trends": weekly_data,
                    "trend_direction": self._calculate_trend_direction(weekly_data)
                }
                
        except Exception:
            return {}
    
    def _calculate_trend_direction(self, data: List[Dict[str, Any]]) -> Dict[str, str]:
        """Calculate trend direction for metrics"""
        if len(data) < 2:
            return {}
        
        try:
            # Calculate trends for different metrics
            trends = {}
            
            for metric in ["total", "avg_confidence", "approval_rate"]:
                values = [item[metric] for item in data if metric in item]
                if len(values) >= 2:
                    if values[-1] > values[0]:
                        trends[metric] = "increasing"
                    elif values[-1] < values[0]:
                        trends[metric] = "decreasing"
                    else:
                        trends[metric] = "stable"
            
            return trends
            
        except Exception:
            return {}
    
    def _calculate_trend(self, values: List[float]) -> str:
        """Calculate simple trend direction"""
        if len(values) < 2:
            return "stable"
        
        try:
            recent_avg = statistics.mean(values[:len(values)//3]) if len(values) >= 3 else values[0]
            older_avg = statistics.mean(values[-len(values)//3:]) if len(values) >= 3 else values[-1]
            
            if recent_avg > older_avg * 1.1:
                return "increasing"
            elif recent_avg < older_avg * 0.9:
                return "decreasing"
            else:
                return "stable"
                
        except Exception:
            return "stable"
    
    def _process_health_data(self, health_data: List[Tuple]) -> Dict[str, Any]:
        """Process system health data"""
        if not health_data:
            return {}
        
        try:
            cpu_values = [row[0] for row in health_data if row[0] is not None]
            memory_values = [row[1] for row in health_data if row[1] is not None]
            disk_values = [row[2] for row in health_data if row[2] is not None]
            
            return {
                "cpu": {
                    "current": cpu_values[0] if cpu_values else 0,
                    "average": statistics.mean(cpu_values) if cpu_values else 0,
                    "max": max(cpu_values) if cpu_values else 0
                },
                "memory": {
                    "current": memory_values[0] if memory_values else 0,
                    "average": statistics.mean(memory_values) if memory_values else 0,
                    "max": max(memory_values) if memory_values else 0
                },
                "disk": {
                    "current": disk_values[0] if disk_values else 0,
                    "average": statistics.mean(disk_values) if disk_values else 0,
                    "max": max(disk_values) if disk_values else 0
                }
            }
            
        except Exception:
            return {}
    
    def _generate_performance_alerts(self, performance_stats: Dict[str, Any]) -> List[Dict[str, str]]:
        """Generate performance alerts based on metrics"""
        alerts = []
        
        try:
            # Check for high resource usage
            for metric_name, stats in performance_stats.items():
                if "cpu" in metric_name.lower() and stats.get("current", 0) > 80:
                    alerts.append({
                        "type": "warning",
                        "message": f"High CPU usage detected: {stats['current']:.1f}%"
                    })
                
                if "memory" in metric_name.lower() and stats.get("current", 0) > 85:
                    alerts.append({
                        "type": "warning",
                        "message": f"High memory usage detected: {stats['current']:.1f}%"
                    })
                
                if "processing_time" in metric_name.lower() and stats.get("average", 0) > 300:
                    alerts.append({
                        "type": "info",
                        "message": f"Processing time is above average: {stats['average']:.1f}s"
                    })
            
            return alerts
            
        except Exception:
            return []
    
    def _get_violation_trends(self, violation_data: List[Dict], days: int) -> Dict[str, List[Dict]]:
        """Get violation trends over time"""
        try:
            # Group by date
            daily_violations = defaultdict(lambda: defaultdict(int))
            
            for item in violation_data:
                date = item["created_at"][:10]  # Extract date part
                for violation in item["violations"]:
                    daily_violations[date][violation] += 1
            
            # Convert to trend format
            trends = defaultdict(list)
            for date in sorted(daily_violations.keys()):
                for violation, count in daily_violations[date].items():
                    trends[violation].append({
                        "date": date,
                        "count": count
                    })
            
            return dict(trends)
            
        except Exception:
            return {}
    
    def _analyze_violation_severity(self, violation_data: List[Dict]) -> Dict[str, Any]:
        """Analyze violation severity patterns"""
        try:
            severity_analysis = {}
            
            # Group by confidence levels
            high_conf = [item for item in violation_data if item["confidence"] >= 80]
            medium_conf = [item for item in violation_data if 60 <= item["confidence"] < 80]
            low_conf = [item for item in violation_data if item["confidence"] < 60]
            
            severity_analysis["high_confidence"] = {
                "count": len(high_conf),
                "rejection_rate": sum(1 for item in high_conf if item["decision"] == "rejected") / len(high_conf) * 100 if high_conf else 0
            }
            
            severity_analysis["medium_confidence"] = {
                "count": len(medium_conf),
                "rejection_rate": sum(1 for item in medium_conf if item["decision"] == "rejected") / len(medium_conf) * 100 if medium_conf else 0
            }
            
            severity_analysis["low_confidence"] = {
                "count": len(low_conf),
                "rejection_rate": sum(1 for item in low_conf if item["decision"] == "rejected") / len(low_conf) * 100 if low_conf else 0
            }
            
            return severity_analysis
            
        except Exception:
            return {}
    
    def _analyze_violation_correlations(self, violation_data: List[Dict]) -> Dict[str, Any]:
        """Analyze correlations between different violations"""
        try:
            # Find common violation combinations
            violation_combinations = Counter()
            
            for item in violation_data:
                violations = sorted(item["violations"])
                if len(violations) > 1:
                    # Create combinations of violations
                    for i in range(len(violations)):
                        for j in range(i + 1, len(violations)):
                            combo = f"{violations[i]} + {violations[j]}"
                            violation_combinations[combo] += 1
            
            return {
                "common_combinations": dict(violation_combinations.most_common(10)),
                "multi_violation_rate": sum(1 for item in violation_data if len(item["violations"]) > 1) / len(violation_data) * 100 if violation_data else 0
            }
            
        except Exception:
            return {}
    
    def _generate_recommendations(self, days: int) -> List[Dict[str, str]]:
        """Generate recommendations based on analysis"""
        recommendations = []
        
        try:
            overview = self.get_overview_stats(days)
            
            # Approval rate recommendations
            approval_rate = overview.get("approval_rate", 0)
            if approval_rate < 50:
                recommendations.append({
                    "type": "warning",
                    "category": "moderation",
                    "message": "Low approval rate detected. Consider reviewing moderation sensitivity settings."
                })
            elif approval_rate > 90:
                recommendations.append({
                    "type": "info",
                    "category": "moderation",
                    "message": "Very high approval rate. Consider increasing detection sensitivity if needed."
                })
            
            # Processing time recommendations
            avg_processing_time = overview.get("avg_processing_time", 0)
            if avg_processing_time > 180:
                recommendations.append({
                    "type": "warning",
                    "category": "performance",
                    "message": "High average processing time. Consider optimizing video analysis pipeline."
                })
            
            # Confidence recommendations
            avg_confidence = overview.get("avg_confidence", 0)
            if avg_confidence < 70:
                recommendations.append({
                    "type": "info",
                    "category": "accuracy",
                    "message": "Lower average confidence scores. Consider model retraining or threshold adjustments."
                })
            
            return recommendations
            
        except Exception:
            return []