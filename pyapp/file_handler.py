"""
File Handler Module for Video Auto-Moderation System
Handles video file uploads, storage, validation, and management
"""

import os
import shutil
import hashlib
import mimetypes
from pathlib import Path
from typing import Dict, List, Optional, Tuple
import magic
from datetime import datetime
import json

class FileHandler:
    """Handles file operations for video uploads and storage"""
    
    def __init__(self, upload_dir: str = "uploads", processed_dir: str = "processed"):
        self.upload_dir = Path(upload_dir)
        self.processed_dir = Path(processed_dir)
        self.temp_dir = Path("temp")
        
        # Create directories if they don't exist
        self.upload_dir.mkdir(exist_ok=True)
        self.processed_dir.mkdir(exist_ok=True)
        self.temp_dir.mkdir(exist_ok=True)
        
        # Supported video formats
        self.supported_formats = {
            'video/mp4': ['.mp4'],
            'video/quicktime': ['.mov'],
            'video/x-msvideo': ['.avi'],
            'video/x-ms-wmv': ['.wmv'],
            'video/x-matroska': ['.mkv'],
            'video/x-flv': ['.flv'],
            'video/webm': ['.webm']
        }
        
        # File size limits (in bytes)
        self.max_file_size = 500 * 1024 * 1024  # 500MB
        self.min_file_size = 1024  # 1KB
        
    def validate_file(self, file_path: str) -> Dict:
        """
        Validate uploaded video file
        
        Args:
            file_path: Path to the file to validate
            
        Returns:
            Dict with validation results
        """
        try:
            file_path = Path(file_path)
            
            if not file_path.exists():
                return {
                    'valid': False,
                    'error': 'File does not exist',
                    'details': {}
                }
            
            # Check file size
            file_size = file_path.stat().st_size
            if file_size > self.max_file_size:
                return {
                    'valid': False,
                    'error': f'File too large. Maximum size: {self._format_size(self.max_file_size)}',
                    'details': {'size': file_size}
                }
            
            if file_size < self.min_file_size:
                return {
                    'valid': False,
                    'error': f'File too small. Minimum size: {self._format_size(self.min_file_size)}',
                    'details': {'size': file_size}
                }
            
            # Check file type using python-magic
            try:
                mime_type = magic.from_file(str(file_path), mime=True)
            except:
                # Fallback to mimetypes
                mime_type, _ = mimetypes.guess_type(str(file_path))
            
            if not mime_type or not any(mime_type.startswith(fmt) for fmt in self.supported_formats.keys()):
                return {
                    'valid': False,
                    'error': f'Unsupported file format: {mime_type}',
                    'details': {'mime_type': mime_type}
                }
            
            # Check file extension
            file_extension = file_path.suffix.lower()
            valid_extensions = []
            for fmt, exts in self.supported_formats.items():
                valid_extensions.extend(exts)
            
            if file_extension not in valid_extensions:
                return {
                    'valid': False,
                    'error': f'Invalid file extension: {file_extension}',
                    'details': {'extension': file_extension}
                }
            
            return {
                'valid': True,
                'details': {
                    'size': file_size,
                    'mime_type': mime_type,
                    'extension': file_extension,
                    'filename': file_path.name
                }
            }
            
        except Exception as e:
            return {
                'valid': False,
                'error': f'Validation error: {str(e)}',
                'details': {}
            }
    
    def save_uploaded_file(self, file_data, original_filename: str) -> Dict:
        """
        Save uploaded file to storage
        
        Args:
            file_data: File data (bytes or file-like object)
            original_filename: Original filename from upload
            
        Returns:
            Dict with save results including file_id and path
        """
        try:
            # Generate unique filename
            file_id = self._generate_file_id(original_filename)
            file_extension = Path(original_filename).suffix.lower()
            safe_filename = f"{file_id}{file_extension}"
            
            # Save to upload directory
            file_path = self.upload_dir / safe_filename
            
            # Handle different types of file_data
            if hasattr(file_data, 'read'):
                # File-like object
                with open(file_path, 'wb') as f:
                    shutil.copyfileobj(file_data, f)
            elif isinstance(file_data, bytes):
                # Bytes data
                with open(file_path, 'wb') as f:
                    f.write(file_data)
            else:
                # Assume it's a path to temporary file
                shutil.move(str(file_data), str(file_path))
            
            # Validate the saved file
            validation = self.validate_file(str(file_path))
            if not validation['valid']:
                # Remove invalid file
                file_path.unlink(missing_ok=True)
                return {
                    'success': False,
                    'error': validation['error'],
                    'file_id': None
                }
            
            # Create metadata
            metadata = {
                'file_id': file_id,
                'original_filename': original_filename,
                'safe_filename': safe_filename,
                'file_path': str(file_path),
                'file_size': validation['details']['size'],
                'mime_type': validation['details']['mime_type'],
                'upload_time': datetime.now().isoformat(),
                'checksum': self._calculate_checksum(file_path)
            }
            
            # Save metadata
            self._save_metadata(file_id, metadata)
            
            return {
                'success': True,
                'file_id': file_id,
                'file_path': str(file_path),
                'metadata': metadata
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': f'Failed to save file: {str(e)}',
                'file_id': None
            }
    
    def get_file_info(self, file_id: str) -> Optional[Dict]:
        """Get file information by file_id"""
        try:
            metadata_path = self.upload_dir / f"{file_id}.json"
            if metadata_path.exists():
                with open(metadata_path, 'r') as f:
                    return json.load(f)
            return None
        except Exception:
            return None
    
    def delete_file(self, file_id: str) -> bool:
        """Delete file and its metadata"""
        try:
            metadata = self.get_file_info(file_id)
            if not metadata:
                return False
            
            # Delete file
            file_path = Path(metadata['file_path'])
            file_path.unlink(missing_ok=True)
            
            # Delete metadata
            metadata_path = self.upload_dir / f"{file_id}.json"
            metadata_path.unlink(missing_ok=True)
            
            # Delete from processed directory if exists
            processed_file = self.processed_dir / metadata['safe_filename']
            processed_file.unlink(missing_ok=True)
            
            return True
            
        except Exception:
            return False
    
    def move_to_processed(self, file_id: str) -> bool:
        """Move file to processed directory after successful moderation"""
        try:
            metadata = self.get_file_info(file_id)
            if not metadata:
                return False
            
            source_path = Path(metadata['file_path'])
            dest_path = self.processed_dir / metadata['safe_filename']
            
            if source_path.exists():
                shutil.move(str(source_path), str(dest_path))
                
                # Update metadata
                metadata['file_path'] = str(dest_path)
                metadata['processed_time'] = datetime.now().isoformat()
                self._save_metadata(file_id, metadata)
                
                return True
            
            return False
            
        except Exception:
            return False
    
    def cleanup_temp_files(self, max_age_hours: int = 24) -> int:
        """Clean up temporary files older than specified hours"""
        try:
            cleaned = 0
            current_time = datetime.now()
            
            for file_path in self.temp_dir.glob('*'):
                if file_path.is_file():
                    file_age = current_time - datetime.fromtimestamp(file_path.stat().st_mtime)
                    if file_age.total_seconds() > (max_age_hours * 3600):
                        file_path.unlink()
                        cleaned += 1
            
            return cleaned
            
        except Exception:
            return 0
    
    def get_storage_stats(self) -> Dict:
        """Get storage statistics"""
        try:
            upload_size = sum(f.stat().st_size for f in self.upload_dir.glob('*') if f.is_file())
            processed_size = sum(f.stat().st_size for f in self.processed_dir.glob('*') if f.is_file())
            temp_size = sum(f.stat().st_size for f in self.temp_dir.glob('*') if f.is_file())
            
            upload_count = len([f for f in self.upload_dir.glob('*.json')])
            processed_count = len([f for f in self.processed_dir.glob('*') if f.suffix != '.json'])
            
            return {
                'upload_directory': {
                    'size': upload_size,
                    'size_formatted': self._format_size(upload_size),
                    'file_count': upload_count
                },
                'processed_directory': {
                    'size': processed_size,
                    'size_formatted': self._format_size(processed_size),
                    'file_count': processed_count
                },
                'temp_directory': {
                    'size': temp_size,
                    'size_formatted': self._format_size(temp_size)
                },
                'total_size': upload_size + processed_size + temp_size,
                'total_size_formatted': self._format_size(upload_size + processed_size + temp_size)
            }
            
        except Exception:
            return {}
    
    def list_files(self, directory: str = 'upload', limit: int = 100) -> List[Dict]:
        """List files in specified directory"""
        try:
            if directory == 'upload':
                dir_path = self.upload_dir
            elif directory == 'processed':
                dir_path = self.processed_dir
            else:
                return []
            
            files = []
            metadata_files = list(dir_path.glob('*.json'))[:limit]
            
            for metadata_file in metadata_files:
                try:
                    with open(metadata_file, 'r') as f:
                        metadata = json.load(f)
                        files.append(metadata)
                except Exception:
                    continue
            
            return sorted(files, key=lambda x: x.get('upload_time', ''), reverse=True)
            
        except Exception:
            return []
    
    def _generate_file_id(self, filename: str) -> str:
        """Generate unique file ID"""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        hash_input = f"{filename}_{timestamp}_{os.urandom(8).hex()}"
        file_hash = hashlib.md5(hash_input.encode()).hexdigest()[:12]
        return f"{timestamp}_{file_hash}"
    
    def _calculate_checksum(self, file_path: Path) -> str:
        """Calculate MD5 checksum of file"""
        try:
            hash_md5 = hashlib.md5()
            with open(file_path, "rb") as f:
                for chunk in iter(lambda: f.read(4096), b""):
                    hash_md5.update(chunk)
            return hash_md5.hexdigest()
        except Exception:
            return ""
    
    def _save_metadata(self, file_id: str, metadata: Dict):
        """Save file metadata"""
        metadata_path = self.upload_dir / f"{file_id}.json"
        with open(metadata_path, 'w') as f:
            json.dump(metadata, f, indent=2)
    
    def _format_size(self, size_bytes: int) -> str:
        """Format file size in human readable format"""
        if size_bytes == 0:
            return "0 B"
        
        size_names = ["B", "KB", "MB", "GB", "TB"]
        i = 0
        while size_bytes >= 1024 and i < len(size_names) - 1:
            size_bytes /= 1024.0
            i += 1
        
        return f"{size_bytes:.1f} {size_names[i]}"
    
    def create_backup(self, backup_dir: str) -> Dict:
        """Create backup of all files and metadata"""
        try:
            backup_path = Path(backup_dir)
            backup_path.mkdir(exist_ok=True)
            
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            backup_name = f"video_moderation_backup_{timestamp}"
            full_backup_path = backup_path / backup_name
            
            # Create backup directory structure
            full_backup_path.mkdir(exist_ok=True)
            (full_backup_path / "uploads").mkdir(exist_ok=True)
            (full_backup_path / "processed").mkdir(exist_ok=True)
            
            # Copy files
            upload_files = 0
            processed_files = 0
            
            for file_path in self.upload_dir.glob('*'):
                if file_path.is_file():
                    shutil.copy2(file_path, full_backup_path / "uploads")
                    upload_files += 1
            
            for file_path in self.processed_dir.glob('*'):
                if file_path.is_file():
                    shutil.copy2(file_path, full_backup_path / "processed")
                    processed_files += 1
            
            # Create backup info
            backup_info = {
                'backup_time': datetime.now().isoformat(),
                'upload_files': upload_files,
                'processed_files': processed_files,
                'backup_path': str(full_backup_path)
            }
            
            with open(full_backup_path / "backup_info.json", 'w') as f:
                json.dump(backup_info, f, indent=2)
            
            return {
                'success': True,
                'backup_path': str(full_backup_path),
                'info': backup_info
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }