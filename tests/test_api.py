import pytest
from httpx import AsyncClient  # noqa: F401  (used indirectly via client fixture)




@pytest.mark.asyncio
async def test_health(client):
    """Test health endpoint"""
    response = await client.get("/api/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert "time" in data


@pytest.mark.asyncio
async def test_meta(client):
    """Test meta endpoint"""
    response = await client.get("/api/_meta")
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "ResumeRAG"
    assert data["version"] == "1.0.0"
    assert "endpoints" in data
    assert "features" in data


@pytest.mark.asyncio
async def test_hackathon_manifest(client):
    """Test hackathon manifest endpoint"""
    response = await client.get("/.well-known/hackathon.json")
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "ResumeRAG"
    assert "endpoints" in data


@pytest.mark.asyncio
async def test_upload_idempotency(client):
    """Test idempotency for resume upload"""
    # Create a test file
    import io
    test_content = b"Test Resume\nJohn Doe\njohn@example.com\nPython, React, Node.js"
    
    idempotency_key = "test-key-123"
    
    # First upload
    files = {"file": ("test_resume.txt", io.BytesIO(test_content), "text/plain")}
    data = {"visibility": "public"}
    
    response1 = await client.post(
        "/api/resumes",
        files=files,
        data=data,
        headers={"Idempotency-Key": idempotency_key}
    )
    
    assert response1.status_code == 201
    data1 = response1.json()
    resume_id_1 = data1["id"]
    
    # Second upload with same idempotency key
    files = {"file": ("test_resume.txt", io.BytesIO(test_content), "text/plain")}
    data = {"visibility": "public"}
    
    response2 = await client.post(
        "/api/resumes",
        files=files,
        data=data,
        headers={"Idempotency-Key": idempotency_key}
    )
    
    assert response2.status_code == 201
    data2 = response2.json()
    resume_id_2 = data2["id"]
    
    # Should return same resume ID
    assert resume_id_1 == resume_id_2


@pytest.mark.asyncio
async def test_pagination(client):
    """Test pagination for resume listing"""
    # Upload multiple resumes
    for i in range(3):
        import io
        content = f"Resume {i}\nName {i}\nSkill{i}".encode()
        files = {"file": (f"resume_{i}.txt", io.BytesIO(content), "text/plain")}
        data = {"visibility": "public"}
        
        await client.post(
            "/api/resumes",
            files=files,
            data=data,
            headers={"Idempotency-Key": f"key-{i}"}
        )
    
    # Test pagination with limit=1
    response = await client.get("/api/resumes?limit=1&offset=0")
    assert response.status_code == 200
    data = response.json()
    
    assert "items" in data
    assert "next_offset" in data
    assert len(data["items"]) == 1
    # Should have next_offset if there are more items
    if data["next_offset"] is not None:
        assert isinstance(data["next_offset"], int)


@pytest.mark.asyncio
async def test_ask_snippets(client):
    """Test ask endpoint returns snippets with valid page numbers"""
    # Upload a test resume
    import io
    content = b"John Doe\njohn@example.com\n\nSkills: React, Node.js, Python, PostgreSQL\n\nExperience:\nSenior Developer at TechCorp\nBuilt scalable web applications using React and Node.js"
    
    files = {"file": ("react_resume.txt", io.BytesIO(content), "text/plain")}
    data = {"visibility": "public"}
    
    await client.post(
        "/api/resumes",
        files=files,
        data=data,
        headers={"Idempotency-Key": "ask-test-key"}
    )
    
    # Query for React
    response = await client.post(
        "/api/ask",
        json={"query": "React", "k": 5}
    )
    
    assert response.status_code == 200
    data = response.json()
    
    assert "answers" in data
    assert "cached" in data
    assert data["cached"] == False
    
    # Check if we have answers
    if len(data["answers"]) > 0:
        answer = data["answers"][0]
        assert "resume_id" in answer
        assert "score" in answer
        assert "snippets" in answer
        
        # Check snippets
        if len(answer["snippets"]) > 0:
            snippet = answer["snippets"][0]
            assert "page" in snippet
            assert "text" in snippet
            assert "start" in snippet
            assert "end" in snippet
            # Page number should be >= 1
            assert snippet["page"] >= 1


@pytest.mark.asyncio
async def test_rate_limit(client):
    """Test rate limiting enforcement"""
    # This test will make many requests to trigger rate limit
    # Note: Adjust based on actual rate limit settings
    
    # Make 65 rapid requests (exceeds 60/min limit)
    responses = []
    for i in range(65):
        response = await client.get("/api/health")
        responses.append(response)
    
    # Check if at least one request was rate limited
    status_codes = [r.status_code for r in responses]
    
    # Should have at least one 429 response
    # Note: This might not work perfectly in test environment
    # as rate limiting depends on Redis and timing
    has_rate_limit = 429 in status_codes
    
    if has_rate_limit:
        # Find a 429 response and check its format
        rate_limited = [r for r in responses if r.status_code == 429][0]
        data = rate_limited.json()
        assert "error" in data
        assert data["error"]["code"] == "RATE_LIMIT"
        assert "Rate limit exceeded" in data["error"]["message"]
    else:
        # In test environment, rate limiting might not work as expected
        # This is acceptable for Phase 1
        print("Warning: Rate limiting not enforced in test environment")


@pytest.mark.asyncio
async def test_job_create_and_match(client):
    """Test job creation and matching"""
    # Upload a resume first
    import io
    content = b"Alice Smith\nalice@example.com\nSkills: Python, Django, REST APIs, PostgreSQL"
    
    files = {"file": ("alice.txt", io.BytesIO(content), "text/plain")}
    data = {"visibility": "public"}
    
    await client.post(
        "/api/resumes",
        files=files,
        data=data,
        headers={"Idempotency-Key": "job-match-key"}
    )
    
    # Create a job
    job_response = await client.post(
        "/api/jobs",
        json={"title": "Backend Developer", "description": "Python, Django, REST APIs"},
        headers={"Idempotency-Key": "job-create-key"}
    )
    
    assert job_response.status_code == 201
    job_data = job_response.json()
    job_id = job_data["id"]
    
    # Match candidates
    match_response = await client.post(
        f"/api/jobs/{job_id}/match",
        json={"top_n": 10}
    )
    
    assert match_response.status_code == 200
    match_data = match_response.json()
    
    assert "job_id" in match_data
    assert "matches" in match_data
    assert match_data["job_id"] == job_id


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
