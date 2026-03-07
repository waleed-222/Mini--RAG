import hashlib
import json
from sqlalchemy import select, delete
from datetime import datetime, timedelta
from models.db_schemes.minirag.schemes.celery_task_executions import CeleryTaskExecution


class IdempotencyManager:
    
    def __init__(self, db_client, db_engine):
        self.db_client = db_client
        self.db_engine = db_engine
        
    def create_args_hash(self, task_name:str, task_args: dict):
        
        comapined_data={
            **task_args,
            "task_name":task_name
        }
        
        json_string= json.dumps(comapined_data , sort_keys=True, default=str)
        
        return hashlib.sha256(json_string.encode()).hexdigest()
    
    async def create_task_record(self, task_name:str, task_args:dict, celery_task_id:str =None) ->CeleryTaskExecution:
        """Create new task execution record."""
        args_hash = self.create_args_hash(task_name,task_args)
        
        task_record = CeleryTaskExecution(
            task_name = task_name,
            task_args_hash=args_hash,
            task_args = task_args,
            celery_task_id = celery_task_id,
            status = "PENDING",
            started_at = datetime.utcnow()
        )
        
        session = self.db_client()

        try:
            session.add(task_record)
            await session.commit()
            await session.refresh(task_record)
            return task_record
        finally:
            await session.close()
    
    
    async def update_task_status(self, execution_id:int, status:str, result:dict = None):
        """Update task status and results."""
          
        session= self.db_client()
        try:
            task_record = await session.get(CeleryTaskExecution,execution_id)
            if task_record:
                task_record.status = status
                if result:
                    task_record.result = result
                if status in ['SUCCESS', "FAILURE"]:
                    task_record.complete_at = datetime.utcnow()
                await session.commit()
        finally:
            await session.close()
                 
                 
    async def get_existing_task(self, task_name:str, task_args:dict,
                                celery_task_id:str) -> CeleryTaskExecution:
        """Check if  task with same name and args already exists."""
        args_hash = self.create_args_hash(task_name,task_args)
        
        session= self.db_client()
        try:
            stmt= select(CeleryTaskExecution).where(
                CeleryTaskExecution.celery_task_id ==celery_task_id,
                CeleryTaskExecution.task_name == task_name,
                CeleryTaskExecution.task_args_hash == args_hash
            )
            result= await session.execute(stmt)
            return result.scalar_one_or_none()
        finally:
            await session.close()
        
    
    async def should_execute_task(self, task_name:str, task_args:dict,
                                    celery_task_id:str,
                                    task_time_limit:int=600) -> tuple[bool, CeleryTaskExecution]:
        """
        Check if task should be executed or return existing result.
        Returns (should_execute, existing_task_or_none) 
        """
        
        existing_task = await self.get_existing_task(task_name,task_args, celery_task_id)
        
        if not existing_task:
            return True, None
        
         # Don't execute if task is already completed successfully 
        if existing_task.status == 'SUCCESS':
            return False, existing_task
        
        # Don't execute if task is  pending or running
        if existing_task.status in ['STARTED','PENDING','RETRY']:
            if existing_task.started_at:
                time_elapsed = (datetime.utcnow() - existing_task.started_at).total_seconds()
                time_gap =60 #60 seconds grace period
                if time_elapsed > (task_time_limit + time_gap):
                    return True, existing_task # Task stuck, allow re-execution
            return False, existing_task # Task still running within time limit
        
        # Re-execute if previous task failed 
        return True, existing_task  
    
    async def cleanup_old_tasks(self, time_rentention:int=86400)->int:
        """
        Delete old task records older than time_rentention seconds.
        Returns:
            Number of deleted records
        """
        
        cutoff_time = datetime.utcnow() - timedelta(seconds=time_rentention)
        
        session =self.db_client()
        
        try:
            stmt = delete(CeleryTaskExecution).where(
                CeleryTaskExecution.created_at < cutoff_time
            )
            result = await session.execute(stmt)
            await session.commit()
            return result.rowcount
        finally:
            await session.close()