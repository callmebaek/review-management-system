"""
Task Manager for Background Jobs
MongoDB-based task queue for handling long-running operations
"""

from datetime import datetime, timedelta
from typing import Dict, Optional
import uuid
from utils.db import get_db


class TaskManager:
    """Manage background tasks using MongoDB"""
    
    def __init__(self):
        self.db = get_db()
        self.collection = self.db.tasks if self.db is not None else None
    
    def create_task(self, task_type: str, user_id: str, params: Dict) -> str:
        """
        Create a new background task
        
        Args:
            task_type: Type of task ('review_load', 'reply_post', etc.)
            user_id: User ID for multi-account support
            params: Task parameters (place_id, load_count, etc.)
        
        Returns:
            task_id: Unique task ID
        """
        task_id = str(uuid.uuid4())
        
        task = {
            '_id': task_id,
            'type': task_type,
            'user_id': user_id,
            'params': params,
            'status': 'pending',
            'progress': {
                'current': 0,
                'total': params.get('load_count', 0),
                'message': '대기 중...'
            },
            'result': None,
            'error': None,
            'created_at': datetime.utcnow(),
            'updated_at': datetime.utcnow(),
            'started_at': None,
            'completed_at': None
        }
        
        if self.collection:
            self.collection.insert_one(task)
            print(f"✅ Task created: {task_id} ({task_type})")
        
        return task_id
    
    def update_task_status(self, task_id: str, status: str, **kwargs):
        """Update task status and other fields"""
        update_fields = {
            'status': status,
            'updated_at': datetime.utcnow()
        }
        
        if status == 'processing' and 'started_at' not in kwargs:
            update_fields['started_at'] = datetime.utcnow()
        
        if status in ['completed', 'failed']:
            update_fields['completed_at'] = datetime.utcnow()
        
        # Add any additional fields
        update_fields.update(kwargs)
        
        if self.collection:
            self.collection.update_one(
                {'_id': task_id},
                {'$set': update_fields}
            )
            print(f"🔄 Task {task_id}: {status}")
    
    def update_progress(self, task_id: str, current: int, message: str):
        """Update task progress"""
        if self.collection:
            self.collection.update_one(
                {'_id': task_id},
                {
                    '$set': {
                        'progress.current': current,
                        'progress.message': message,
                        'updated_at': datetime.utcnow()
                    }
                }
            )
    
    def get_task(self, task_id: str) -> Optional[Dict]:
        """Get task by ID"""
        if self.collection:
            task = self.collection.find_one({'_id': task_id})
            return task
        return None
    
    def set_result(self, task_id: str, result: any):
        """Set task result"""
        if self.collection:
            self.collection.update_one(
                {'_id': task_id},
                {
                    '$set': {
                        'result': result,
                        'updated_at': datetime.utcnow()
                    }
                }
            )
    
    def set_error(self, task_id: str, error: str):
        """Set task error"""
        if self.collection:
            self.collection.update_one(
                {'_id': task_id},
                {
                    '$set': {
                        'error': error,
                        'status': 'failed',
                        'completed_at': datetime.utcnow(),
                        'updated_at': datetime.utcnow()
                    }
                }
            )
    
    def cleanup_old_tasks(self, days: int = 7):
        """Delete tasks older than X days"""
        if self.collection:
            cutoff = datetime.utcnow() - timedelta(days=days)
            result = self.collection.delete_many({
                'created_at': {'$lt': cutoff}
            })
            print(f"🗑️ Cleaned up {result.deleted_count} old tasks")


# Singleton instance
task_manager = TaskManager()

