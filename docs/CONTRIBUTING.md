# Contributing to ResumeRAG

Thank you for your interest in contributing to ResumeRAG! This guide will help you get started.

## 📋 Table of Contents

- [Code of Conduct](#code-of-conduct)
- [Getting Started](#getting-started)
- [Development Workflow](#development-workflow)
- [Coding Standards](#coding-standards)
- [Testing Requirements](#testing-requirements)
- [Pull Request Process](#pull-request-process)
- [Issue Guidelines](#issue-guidelines)

---

## Code of Conduct

### Our Standards

- Be respectful and inclusive
- Welcome newcomers and help them learn
- Focus on what is best for the community
- Show empathy towards other community members

### Unacceptable Behavior

- Harassment, discrimination, or offensive comments
- Trolling, insulting, or derogatory remarks
- Publishing others' private information
- Other conduct which could reasonably be considered inappropriate

---

## Getting Started

### Prerequisites

- **Python 3.11+** for backend development
- **Node.js 18+** for frontend development
- **Docker & Docker Compose** for local services
- **Git** for version control
- **Code editor** (VS Code recommended with Python + Prettier extensions)

### Fork and Clone

```bash
# Fork the repository on GitHub
# Then clone your fork
git clone https://github.com/YOUR_USERNAME/ResumeRAG.git
cd ResumeRAG

# Add upstream remote
git remote add upstream https://github.com/ORIGINAL_OWNER/ResumeRAG.git
```

### Environment Setup

```bash
# Copy environment template
cp infra/env.example infra/.env

# Edit with your local configuration
nano infra/.env
```

### Start Development Environment

```bash
# Start all services
docker-compose -f infra/docker-compose.yml up -d

# Run migrations
cd api
alembic upgrade head

# Seed test data (optional)
python scripts/seed_data.py
```

### Install Development Dependencies

**Backend**:
```bash
cd api
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
pip install -r requirements-extra.txt  # Dev dependencies
```

**Frontend**:
```bash
cd frontend
npm install
```

---

## Development Workflow

### 1. Create a Branch

Use descriptive branch names with prefixes:

```bash
# Features
git checkout -b feat/add-resume-tagging

# Bug fixes
git checkout -b fix/upload-timeout-error

# Documentation
git checkout -b docs/update-api-reference

# Refactoring
git checkout -b refactor/optimize-vector-search
```

### 2. Make Changes

- Write code following our [Coding Standards](#coding-standards)
- Add tests for new features
- Update documentation as needed
- Keep commits focused and atomic

### 3. Run Tests Locally

**Backend**:
```bash
cd api
pytest -v
pytest --cov=app --cov-report=html  # With coverage
```

**Frontend**:
```bash
cd frontend
npm run test
npm run lint
```

**E2E Tests**:
```bash
npm run test:e2e
```

### 4. Commit Changes

Use [Conventional Commits](https://www.conventionalcommits.org/):

```bash
# Format: <type>(<scope>): <description>

# Examples:
git commit -m "feat(api): add resume tagging endpoint"
git commit -m "fix(frontend): resolve upload progress bug"
git commit -m "docs(readme): update deployment instructions"
git commit -m "test(api): add tests for job matching"
git commit -m "refactor(services): optimize embedding generation"
```

**Types**:
- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation changes
- `test`: Adding or updating tests
- `refactor`: Code refactoring
- `style`: Formatting changes
- `perf`: Performance improvements
- `chore`: Maintenance tasks

### 5. Push and Create PR

```bash
# Push to your fork
git push origin feat/your-feature

# Create Pull Request on GitHub
# Fill out the PR template completely
```

---

## Coding Standards

### Python (Backend)

**Style Guide**: Follow [PEP 8](https://pep8.org/)

**Formatting**:
```bash
# Use Black for formatting
black app/ tests/

# Use isort for imports
isort app/ tests/
```

**Type Hints**:
```python
# Always use type hints
def process_resume(resume_id: str, user: User) -> ResumeResponse:
    ...

# For complex types
from typing import List, Optional, Dict, Any

def search(query: str, filters: Optional[Dict[str, Any]] = None) -> List[Result]:
    ...
```

**Docstrings**:
```python
def vector_search(query: str, limit: int = 10) -> List[Result]:
    """
    Perform vector similarity search
    
    Args:
        query: Search query text
        limit: Maximum number of results (default: 10)
    
    Returns:
        List of search results with scores
    
    Raises:
        ValueError: If query is empty
    """
    ...
```

**Async/Await**:
```python
# Use async for I/O operations
async def get_resume(db: AsyncSession, resume_id: str) -> Resume:
    result = await db.execute(select(Resume).where(Resume.id == resume_id))
    return result.scalar_one_or_none()
```

### JavaScript/React (Frontend)

**Style Guide**: Follow [Airbnb JavaScript Style Guide](https://github.com/airbnb/javascript)

**Formatting**:
```bash
# Use Prettier
npm run format

# Lint
npm run lint
```

**Components**:
```jsx
// Use functional components with hooks
import { useState, useEffect } from 'react';

export function ResumeCard({ resume, onSelect }) {
  const [isHovered, setIsHovered] = useState(false);
  
  // Handle side effects
  useEffect(() => {
    // ...
  }, [resume.id]);
  
  return (
    <div className="...">
      {/* ... */}
    </div>
  );
}

// PropTypes or TypeScript
ResumeCard.propTypes = {
  resume: PropTypes.object.isRequired,
  onSelect: PropTypes.func
};
```

**Naming Conventions**:
- Components: `PascalCase` (e.g., `ResumeCard.jsx`)
- Hooks: `camelCase` with `use` prefix (e.g., `useAuth.js`)
- Utilities: `camelCase` (e.g., `formatDate.js`)

### SQL/Database

**Migrations**:
```python
# Use Alembic for migrations
# Create new migration
alembic revision -m "add_resume_tags_table"

# Write upgrade and downgrade functions
def upgrade():
    op.create_table(
        'resume_tags',
        sa.Column('id', sa.String(), primary_key=True),
        sa.Column('resume_id', sa.String(), sa.ForeignKey('resumes.id')),
        sa.Column('tag', sa.String(), nullable=False),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now())
    )

def downgrade():
    op.drop_table('resume_tags')
```

**Queries**:
```python
# Use SQLAlchemy ORM when possible
result = await db.execute(
    select(Resume)
    .where(Resume.owner_id == user_id)
    .order_by(Resume.uploaded_at.desc())
    .limit(10)
)

# Use raw SQL for complex vector queries
query = text("""
    SELECT id, embedding <-> :query AS distance
    FROM resume_chunks
    ORDER BY distance
    LIMIT :limit
""")
```

---

## Testing Requirements

### Test Coverage

- **Minimum**: 80% coverage for new code
- **Target**: 90%+ overall coverage
- All new features must include tests

### Test Types

**Unit Tests** (`tests/test_*.py`):
```python
import pytest
from app.services.embedding import hash_embedding

def test_hash_embedding_deterministic():
    """Embedding should be deterministic"""
    text = "Python engineer"
    emb1 = hash_embedding(text)
    emb2 = hash_embedding(text)
    assert emb1 == emb2

@pytest.mark.asyncio
async def test_create_resume(db_session, test_user):
    """Should create resume with valid data"""
    resume = await create_resume(
        db=db_session,
        owner_id=test_user.id,
        filename="test.pdf"
    )
    assert resume.status == ResumeStatus.PENDING
```

**Integration Tests**:
```python
from fastapi.testclient import TestClient

def test_upload_resume_endpoint(client: TestClient, auth_headers):
    """Test resume upload flow"""
    response = client.post(
        "/api/resumes",
        headers=auth_headers,
        files={"file": ("resume.pdf", b"content")},
        data={"visibility": "private"}
    )
    assert response.status_code == 201
    assert "id" in response.json()
```

**E2E Tests** (`tests/e2e/*.spec.js`):
```javascript
test('user can upload and search resumes', async ({ page }) => {
  await page.goto('/upload');
  await page.setInputFiles('input[type="file"]', 'test-resume.pdf');
  await page.click('button[type="submit"]');
  await expect(page.locator('.success-message')).toBeVisible();
  
  await page.goto('/search');
  await page.fill('input[name="query"]', 'Python developer');
  await page.click('button[type="submit"]');
  await expect(page.locator('.search-result')).toHaveCount.greaterThan(0);
});
```

### Running Tests

```bash
# All tests
pytest

# Specific test file
pytest tests/test_embedding.py

# Specific test function
pytest tests/test_embedding.py::test_hash_embedding_deterministic

# With coverage
pytest --cov=app --cov-report=html
```

---

## Pull Request Process

### Before Submitting

✅ **Checklist**:
- [ ] Code follows style guidelines
- [ ] Tests added for new features
- [ ] All tests pass locally
- [ ] Documentation updated (README, API docs, etc.)
- [ ] Commits follow conventional commit format
- [ ] Branch is up-to-date with main
- [ ] No merge conflicts

### PR Template

When creating a PR, fill out the template completely:

```markdown
## Summary
Brief description of changes

## Type of Change
- [ ] Feature (new functionality)
- [ ] Fix (bug fix)
- [ ] Docs (documentation update)
- [ ] Refactor (code improvement, no functionality change)
- [ ] Test (adding or updating tests)

## Changes Made
- Detailed list of changes
- What was added/modified/removed

## Testing
- How was this tested?
- What test cases were added?

## Screenshots (if applicable)
Before | After images

## Checklist
- [ ] Tests pass
- [ ] Lint checks pass
- [ ] Documentation updated
- [ ] Breaking changes documented
```

### Review Process

1. **Automated Checks**: CI must pass (tests, lint, security scan)
2. **Code Review**: At least 1 approval from maintainer
3. **Discussion**: Address reviewer comments
4. **Approval**: Once approved, maintainer will merge

### After Merge

- Delete your feature branch
- Update your local main:
  ```bash
  git checkout main
  git pull upstream main
  ```

---

## Issue Guidelines

### Before Creating an Issue

1. **Search existing issues** to avoid duplicates
2. **Check documentation** - might already be covered
3. **Try latest version** - bug might be fixed

### Issue Types

**Bug Report**:
```markdown
**Describe the bug**
Clear description of what's wrong

**To Reproduce**
Steps to reproduce:
1. Go to '...'
2. Click on '....'
3. See error

**Expected behavior**
What should happen

**Environment**
- OS: [e.g., macOS 13]
- Browser: [e.g., Chrome 120]
- Version: [e.g., v1.0.0]

**Logs/Screenshots**
Any relevant error messages
```

**Feature Request**:
```markdown
**Problem Statement**
What problem does this solve?

**Proposed Solution**
How should it work?

**Alternatives Considered**
Other approaches you've thought about

**Additional Context**
Any other relevant information
```

### Issue Labels

- `bug`: Something isn't working
- `enhancement`: New feature or request
- `documentation`: Improvements to docs
- `good first issue`: Good for newcomers
- `help wanted`: Extra attention needed
- `question`: Further information requested
- `wontfix`: Will not be worked on

---

## Development Tips

### Debugging

**Backend**:
```python
# Add print debugging
import logging
logger = logging.getLogger(__name__)
logger.debug(f"Resume ID: {resume_id}")

# Use pdb for interactive debugging
import pdb; pdb.set_trace()

# Or use VS Code debugger (launch.json configured)
```

**Frontend**:
```javascript
// Console logging
console.log('Resume data:', resume);

// React DevTools
// Use browser extension for component inspection

// Network tab
// Inspect API calls in browser DevTools
```

### Performance Profiling

```python
# Profile slow functions
import cProfile
import pstats

profiler = cProfile.Profile()
profiler.enable()
# ... code to profile ...
profiler.disable()
stats = pstats.Stats(profiler)
stats.sort_stats('cumulative')
stats.print_stats(10)
```

### Database Migrations

```bash
# Create migration
alembic revision -m "description"

# Preview SQL
alembic upgrade head --sql

# Rollback
alembic downgrade -1
```

---

## Questions?

- **Documentation**: Check [ARCHITECTURE.md](./ARCHITECTURE.md) and [DEPLOYMENT.md](./DEPLOYMENT.md)
- **Discussions**: Use GitHub Discussions for questions
- **Chat**: Join our Discord/Slack (link in README)
- **Email**: contact@resumerag.example.com

---

## License

By contributing, you agree that your contributions will be licensed under the MIT License.

---

Thank you for contributing to ResumeRAG! 🎉

_Last updated: October 4, 2025_
