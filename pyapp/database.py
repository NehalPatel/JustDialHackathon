import sqlite3
import json
import os
from datetime import datetime
from typing import List, Dict, Optional
import threading

class VideoDatabase:
    """
    Database manager for video moderation results using SQLite.
    """
    
    def __init__(self, db_path: str = "moderation.db"):
        self.db_path = db_path
        self.lock = threading.Lock()
        self._init_database()
    
    def _init_database(self):
        """Initialize the database with required tables."""
        with self.lock:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Create video_results table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS video_results (
                    id TEXT PRIMARY KEY,
                    original_filename TEXT NOT NULL,
                    file_path TEXT,
                    file_size INTEGER,
                    content_type TEXT,
                    watermark TEXT,
                    decision TEXT NOT NULL,
                    confidence REAL,
                    reasoning TEXT,
                    violations TEXT,  -- JSON string
                    analysis_results TEXT,  -- JSON string
                    processing_time REAL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # Create configuration table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS moderation_config (
                    id INTEGER PRIMARY KEY,
                    config_data TEXT NOT NULL,  -- JSON string
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # Create indexes for better performance
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_decision ON video_results(decision)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_created_at ON video_results(created_at)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_confidence ON video_results(confidence)')
            
            conn.commit()
            conn.close()
    
    def store_result(self, result: Dict) -> bool:
        """Store a video analysis result in the database."""
        try:
            with self.lock:
                conn = sqlite3.connect(self.db_path)
                cursor = conn.cursor()
                
                cursor.execute('''
                    INSERT OR REPLACE INTO video_results 
                    (id, original_filename, file_path, file_size, content_type, watermark,
                     decision, confidence, reasoning, violations, analysis_results, 
                     processing_time, created_at, updated_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    result.get('file_id'),
                    result.get('original_filename'),
                    result.get('video_path'),
                    result.get('file_size'),
                    result.get('content_type'),
                    result.get('watermark'),
                    result.get('decision'),
                    result.get('confidence'),
                    result.get('reasoning'),
                    json.dumps(result.get('violations', [])),
                    json.dumps(result.get('analysis_results', {})),
                    result.get('processing_time'),
                    result.get('timestamp', datetime.now().isoformat()),
                    datetime.now().isoformat()
                ))
                
                conn.commit()
                conn.close()
                return True
                
        except Exception as e:
            print(f"Error storing result: {e}")
            return False
    
    def get_result_by_id(self, file_id: str) -> Optional[Dict]:
        """Retrieve a specific result by file ID."""
        try:
            with self.lock:
                conn = sqlite3.connect(self.db_path)
                cursor = conn.cursor()
                
                cursor.execute('''
                    SELECT * FROM video_results WHERE id = ?
                ''', (file_id,))
                
                row = cursor.fetchone()
                conn.close()
                
                if row:
                    return self._row_to_dict(cursor, row)
                return None
                
        except Exception as e:
            print(f"Error retrieving result: {e}")
            return None
    
    def get_results(self, decision_filter: Optional[str] = None, 
                   limit: int = 50, offset: int = 0) -> List[Dict]:
        """Get results with optional filtering."""
        try:
            with self.lock:
                conn = sqlite3.connect(self.db_path)
                cursor = conn.cursor()
                
                query = 'SELECT * FROM video_results'
                params = []
                
                if decision_filter:
                    query += ' WHERE decision = ?'
                    params.append(decision_filter)
                
                query += ' ORDER BY created_at DESC LIMIT ? OFFSET ?'
                params.extend([limit, offset])
                
                cursor.execute(query, params)
                rows = cursor.fetchall()
                conn.close()
                
                return [self._row_to_dict(cursor, row) for row in rows]
                
        except Exception as e:
            print(f"Error retrieving results: {e}")
            return []
    
    def get_all_results(self) -> List[Dict]:
        """Get all results from the database."""
        return self.get_results(limit=1000)
    
    def delete_result(self, file_id: str) -> bool:
        """Delete a specific result from the database."""
        try:
            with self.lock:
                conn = sqlite3.connect(self.db_path)
                cursor = conn.cursor()
                
                cursor.execute('DELETE FROM video_results WHERE id = ?', (file_id,))
                
                conn.commit()
                conn.close()
                return True
                
        except Exception as e:
            print(f"Error deleting result: {e}")
            return False
    
    def clear_all_results(self) -> bool:
        """Clear all results from the database."""
        try:
            with self.lock:
                conn = sqlite3.connect(self.db_path)
                cursor = conn.cursor()
                
                cursor.execute('DELETE FROM video_results')
                
                conn.commit()
                conn.close()
                return True
                
        except Exception as e:
            print(f"Error clearing results: {e}")
            return False
    
    def get_statistics(self) -> Dict:
        """Get database statistics."""
        try:
            with self.lock:
                conn = sqlite3.connect(self.db_path)
                cursor = conn.cursor()
                
                # Total count
                cursor.execute('SELECT COUNT(*) FROM video_results')
                total_count = cursor.fetchone()[0]
                
                # Decision counts
                cursor.execute('''
                    SELECT decision, COUNT(*) 
                    FROM video_results 
                    GROUP BY decision
                ''')
                decision_counts = dict(cursor.fetchall())
                
                # Average confidence by decision
                cursor.execute('''
                    SELECT decision, AVG(confidence) 
                    FROM video_results 
                    WHERE confidence IS NOT NULL
                    GROUP BY decision
                ''')
                avg_confidence = dict(cursor.fetchall())
                
                # Recent activity (last 24 hours)
                cursor.execute('''
                    SELECT COUNT(*) 
                    FROM video_results 
                    WHERE created_at >= datetime('now', '-1 day')
                ''')
                recent_count = cursor.fetchone()[0]
                
                conn.close()
                
                return {
                    'total_videos': total_count,
                    'decision_counts': decision_counts,
                    'average_confidence': avg_confidence,
                    'recent_activity': recent_count
                }
                
        except Exception as e:
            print(f"Error getting statistics: {e}")
            return {}
    
    def store_config(self, config: Dict) -> bool:
        """Store moderation configuration."""
        try:
            with self.lock:
                conn = sqlite3.connect(self.db_path)
                cursor = conn.cursor()
                
                # Clear existing config and insert new one
                cursor.execute('DELETE FROM moderation_config')
                cursor.execute('''
                    INSERT INTO moderation_config (config_data, created_at, updated_at)
                    VALUES (?, ?, ?)
                ''', (
                    json.dumps(config),
                    datetime.now().isoformat(),
                    datetime.now().isoformat()
                ))
                
                conn.commit()
                conn.close()
                return True
                
        except Exception as e:
            print(f"Error storing config: {e}")
            return False
    
    def get_config(self) -> Optional[Dict]:
        """Get current moderation configuration."""
        try:
            with self.lock:
                conn = sqlite3.connect(self.db_path)
                cursor = conn.cursor()
                
                cursor.execute('''
                    SELECT config_data FROM moderation_config 
                    ORDER BY updated_at DESC LIMIT 1
                ''')
                
                row = cursor.fetchone()
                conn.close()
                
                if row:
                    return json.loads(row[0])
                return None
                
        except Exception as e:
            print(f"Error retrieving config: {e}")
            return None
    
    def _row_to_dict(self, cursor, row) -> Dict:
        """Convert a database row to a dictionary."""
        columns = [description[0] for description in cursor.description]
        result = dict(zip(columns, row))
        
        # Parse JSON fields
        if result.get('violations'):
            try:
                result['violations'] = json.loads(result['violations'])
            except:
                result['violations'] = []
        
        if result.get('analysis_results'):
            try:
                result['analysis_results'] = json.loads(result['analysis_results'])
            except:
                result['analysis_results'] = {}
        
        return result
    
    def backup_database(self, backup_path: str) -> bool:
        """Create a backup of the database."""
        try:
            with self.lock:
                # Simple file copy for SQLite
                import shutil
                shutil.copy2(self.db_path, backup_path)
                return True
                
        except Exception as e:
            print(f"Error creating backup: {e}")
            return False
    
    def get_database_info(self) -> Dict:
        """Get database information and health status."""
        try:
            with self.lock:
                conn = sqlite3.connect(self.db_path)
                cursor = conn.cursor()
                
                # Get database size
                cursor.execute("SELECT page_count * page_size as size FROM pragma_page_count(), pragma_page_size()")
                db_size = cursor.fetchone()[0]
                
                # Get table info
                cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
                tables = [row[0] for row in cursor.fetchall()]
                
                conn.close()
                
                return {
                    'database_path': self.db_path,
                    'database_size_bytes': db_size,
                    'tables': tables,
                    'status': 'healthy'
                }
                
        except Exception as e:
            return {
                'database_path': self.db_path,
                'status': 'error',
                'error': str(e)
            }