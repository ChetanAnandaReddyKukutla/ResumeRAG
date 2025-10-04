import os
from rq import Worker, Queue, Connection
from redis import Redis


def start_worker():
    """Start RQ worker to process background jobs"""
    redis_url = os.getenv("REDIS_URL", "redis://localhost:6379/0")
    redis_conn = Redis.from_url(redis_url)
    
    with Connection(redis_conn):
        worker = Worker(['default'])
        worker.work()


if __name__ == '__main__':
    start_worker()
