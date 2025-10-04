import os


def get_upload_dir() -> str:
    """Get or create upload directory"""
    upload_dir = os.path.join(os.getcwd(), "uploads")
    os.makedirs(upload_dir, exist_ok=True)
    return upload_dir


def generate_id(prefix: str = "") -> str:
    """Generate a unique ID with optional prefix"""
    import uuid
    unique_id = uuid.uuid4().hex[:16]
    return f"{prefix}{unique_id}" if prefix else unique_id
