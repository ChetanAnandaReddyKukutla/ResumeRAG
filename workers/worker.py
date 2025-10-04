import os
import sys
from rq import Worker, Queue, Connection
from redis import Redis

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dotenv import load_dotenv

load_dotenv()


def process_resume_job(resume_id: str):
    """
    Background job to process resume
    
    For Phase 1, parsing is done synchronously, but this worker
    is scaffolded for future async processing
    """
    print(f"Processing resume: {resume_id}")
    # TODO: Implement async parsing
    return {"status": "completed", "resume_id": resume_id}


if __name__ == '__main__':
    redis_url = os.getenv("REDIS_URL", "redis://localhost:6379/0")
    redis_conn = Redis.from_url(redis_url)
    
    with Connection(redis_conn):
        worker = Worker(['default'])
        print("Worker started. Listening for jobs...")
        worker.work()
