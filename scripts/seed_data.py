#!/usr/bin/env python3
"""
Seed script to create test users and upload seed resumes
"""
import os
import sys
import asyncio
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'api'))

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from dotenv import load_dotenv

from app.models import User, Resume, ResumeStatus, ResumeVisibility, UserRole
from sqlalchemy import select
from app.routers.auth import hash_password
from app.services import parsing, embedding, indexing
from app.utilS import generate_id

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL", "postgresql+asyncpg://postgres:postgres@localhost:5432/resumerag")


async def seed_database():
    """Seed database with test users and resumes"""
    print("Starting database seed...")
    
    # Create engine and session
    engine = create_async_engine(DATABASE_URL, echo=False)
    AsyncSessionLocal = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    
    async with AsyncSessionLocal() as db:
        try:
            # Create users
            print("\nCreating users...")
            
            users_data = [
                {
                    "email": "recruiter@example.com",
                    "password": "Recruiter@123",
                    "role": UserRole.RECRUITER
                },
                {
                    "email": "alice@example.com",
                    "password": "Alice@123",
                    "role": UserRole.USER
                },
                {
                    "email": "bob@example.com",
                    "password": "Bob@123",
                    "role": UserRole.USER
                }
            ]
            
            created_users = []
            for user_data in users_data:
                # Check if user already exists
                result = await db.execute(select(User).where(User.email == user_data["email"]))
                existing = result.scalar_one_or_none()
                if existing:
                    print(f"  Skipping existing user: {existing.email}")
                    created_users.append(existing)
                    continue

                user = User(
                    id=f"user_{generate_id()}",
                    email=user_data["email"],
                    password_hash=hash_password(user_data["password"]),
                    role=user_data["role"]
                )
                db.add(user)
                created_users.append(user)
                print(f"  Created user: {user.email} (role: {user.role.value})")
            
            await db.commit()
            
            # Upload seed resumes
            print("\nUploading seed resumes...")
            
            seed_resumes_dir = Path(__file__).parent.parent / "infra" / "seed-resumes"
            resume_files = [
                ("alice_resume.txt", created_users[1].id),  # Alice's resume
                ("bob_resume.txt", created_users[2].id),    # Bob's resume
                ("carol_resume.txt", None),                  # Carol (no user account)
            ]
            
            for filename, owner_id in resume_files:
                file_path = seed_resumes_dir / filename
                
                if not file_path.exists():
                    print(f"  Warning: {filename} not found, skipping...")
                    continue
                
                # Compute file hash
                file_hash = parsing.compute_file_hash(str(file_path))
                
                # Create upload directory
                upload_dir = Path(os.getcwd()) / "uploads"
                upload_dir.mkdir(exist_ok=True)
                
                # Copy file to uploads directory
                resume_id = f"resume_{generate_id()}"
                dest_path = upload_dir / f"{resume_id}.txt"
                
                with open(file_path, 'r') as src, open(dest_path, 'w') as dst:
                    dst.write(src.read())
                
                # Parse resume
                print(f"  Parsing {filename}...")
                parse_result = parsing.parse_resume(str(dest_path), filename)
                
                # Check if resume with same file_hash already ingested
                existing_resume = None
                if file_hash:
                    from sqlalchemy import select as _select
                    res_q = await db.execute(_select(Resume).where(Resume.file_hash == file_hash))
                    existing_resume = res_q.scalar_one_or_none()
                if existing_resume:
                    print(f"  Skipping existing resume {filename} (already ingested)")
                    resume_id = existing_resume.id
                else:
                    # Create resume record
                    resume = Resume(
                        id=resume_id,
                        owner_id=owner_id,
                        filename=filename,
                        status=ResumeStatus.COMPLETED,
                        visibility=ResumeVisibility.PUBLIC,
                        size_bytes=file_path.stat().st_size,
                        file_hash=file_hash,
                        parsing_hash=parse_result.parsing_hash,
                        parsed_metadata=parse_result.metadata,
                        file_path=str(dest_path)
                    )
                    db.add(resume)
                    await db.flush()
                
                # Create chunks with embeddings
                # Only insert chunks if this is a new resume
                if not existing_resume:
                    print(f"  Creating chunks for {filename}...")
                    chunks = embedding.chunk_resume_by_pages(parse_result)
                    await indexing.insert_resume_chunks(db, resume_id, chunks)
                    print(f"  ✓ Uploaded {filename} ({len(chunks)} chunks)")
            
            await db.commit()
            
            print("\n✓ Database seeded successfully!")
            print("\nCreated users:")
            print("  - recruiter@example.com / Recruiter@123 (recruiter)")
            print("  - alice@example.com / Alice@123 (user)")
            print("  - bob@example.com / Bob@123 (user)")
            print("\nUploaded resumes:")
            print("  - alice_resume.txt (owner: alice)")
            print("  - bob_resume.txt (owner: bob)")
            print("  - carol_resume.txt (no owner)")
            
        except Exception as e:
            print(f"\n✗ Error seeding database: {e}")
            import traceback
            traceback.print_exc()
            await db.rollback()
            raise
        finally:
            await db.close()
    
    await engine.dispose()


if __name__ == "__main__":
    asyncio.run(seed_database())
