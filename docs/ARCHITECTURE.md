# ResumeRAG Architecture

## Overview

ResumeRAG is a production-grade RAG (Retrieval-Augmented Generation) system designed for semantic resume search and intelligent job-candidate matching. The architecture follows modern best practices with separation of concerns, scalability, security, and observability at its core.

## System Architecture

```mermaid
graph TB
    subgraph "Frontend Layer"
        FE[React + Vite Frontend<br/>Tailwind CSS]
    end
    
    subgraph "API Layer"
        API[FastAPI Application]
        MW1[Request ID Middleware]
        MW2[Logging Middleware]
        MW3[Rate Limit Middleware]
        CORS[CORS Middleware]
        
        API --> MW1
        MW1 --> MW2
        MW2 --> MW3
        MW3 --> CORS
    end
    
    subgraph "Business Logic Layer"
        AUTH[Auth Service<br/>JWT + Refresh Tokens]
        PARSE[Parsing Service<br/>PDF/DOCX/TXT]
        EMBED[Embedding Service<br/>Deterministic SHA256]
        INDEX[Indexing Service<br/>Vector Operations]
        SEARCH[Search Service<br/>RAG Query]
        MATCH[Job Matching Service]
        PII[PII Service<br/>Encryption + Redaction]
        AUDIT[Audit Service<br/>Access Logging]
    end
    
    subgraph "Data Layer"
        PG[(PostgreSQL 14<br/>+ pgvector)]
        REDIS[(Redis<br/>Cache + Queue)]
        S3[S3/MinIO<br/>File Storage]
    end
    
    subgraph "Observability Layer"
        PROM[Prometheus<br/>Metrics]
        OTEL[OpenTelemetry<br/>Traces]
        GRAF[Grafana<br/>Dashboards]
    end
    
    subgraph "Background Workers"
        WORKER[RQ Workers<br/>Async Jobs]
    end
    
    FE -->|HTTPS| API
    
    API --> AUTH
    API --> PARSE
    API --> EMBED
    API --> INDEX
    API --> SEARCH
    API --> MATCH
    API --> PII
    API --> AUDIT
    
    AUTH --> PG
    AUTH --> REDIS
    PARSE --> S3
    EMBED --> PG
    INDEX --> PG
    SEARCH --> PG
    MATCH --> PG
    PII --> PG
    AUDIT --> PG
    
    API -->|Enqueue| REDIS
    REDIS --> WORKER
    WORKER --> PARSE
    WORKER --> EMBED
    
    API -->|Metrics| PROM
    API -->|Traces| OTEL
    PROM --> GRAF
    OTEL --> GRAF
    
    MW2 -->|Structured Logs| OTEL
```

## Data Flow

### Resume Upload Flow

```mermaid
sequenceDiagram
    participant User
    participant Frontend
    participant API
    participant Auth
    participant Upload Security
    participant Parser
    participant Embedder
    participant Database
    participant S3
    participant Queue
    
    User->>Frontend: Upload resume file
    Frontend->>API: POST /api/resumes (multipart)
    
    API->>Auth: Verify JWT token
    Auth-->>API: User validated
    
    API->>Upload Security: Validate file (size, type, malware)
    Upload Security-->>API: File safe
    
    API->>S3: Store original file
    S3-->>API: File URL
    
    API->>Database: Create Resume record (status=PENDING)
    Database-->>API: Resume ID
    
    API->>Parser: Parse file content
    Parser-->>API: Extracted text + metadata
    
    API->>Embedder: Generate embeddings (SHA256)
    Embedder-->>API: Vector embeddings
    
    API->>Database: Store chunks + embeddings
    Database-->>API: Success
    
    API->>Database: Update Resume (status=COMPLETED)
    API-->>Frontend: Resume ID + status
    Frontend-->>User: Upload success
```

### Semantic Search Flow

```mermaid
sequenceDiagram
    participant User
    participant Frontend
    participant API
    participant Auth
    participant Embedder
    participant Indexing
    participant Database
    participant PII Service
    
    User->>Frontend: Enter search query
    Frontend->>API: POST /api/ask
    
    API->>Auth: Verify JWT token
    Auth-->>API: User validated
    
    API->>Embedder: Generate query embedding
    Embedder-->>API: Query vector
    
    API->>Indexing: Vector similarity search
    Indexing->>Database: pgvector <-> query
    Database-->>Indexing: Top N chunks + scores
    Indexing-->>API: Ranked results
    
    API->>Database: Fetch resume metadata
    Database-->>API: Resume details
    
    API->>PII Service: Redact PII (based on role)
    PII Service-->>API: Redacted results
    
    API-->>Frontend: Search results + snippets
    Frontend-->>User: Display results
```

### Job Matching Flow

```mermaid
sequenceDiagram
    participant User
    participant Frontend
    participant API
    participant Database
    participant Matcher
    participant Indexing
    
    User->>Frontend: Create job + requirements
    Frontend->>API: POST /api/jobs
    
    API->>Database: Store job
    Database-->>API: Job ID
    
    User->>Frontend: Request candidate matches
    Frontend->>API: POST /api/jobs/{id}/match
    
    API->>Database: Fetch job requirements
    Database-->>API: Requirements list
    
    API->>Database: Fetch all resumes
    Database-->>API: Resume list
    
    loop For each resume
        API->>Indexing: Search for requirement in resume
        Indexing-->>API: Matching snippets
        
        API->>Matcher: Calculate match score
        Matcher-->>API: Score + evidence
    end
    
    API->>Matcher: Rank candidates by score
    Matcher-->>API: Top N matches
    
    API-->>Frontend: Match results + evidence
    Frontend-->>User: Display candidates
```

## Component Details

### 1. Frontend (React + Vite)

**Purpose**: User interface for resume management and search

**Key Features**:
- Modern React 18 with hooks
- Vite for fast development and builds
- Tailwind CSS for responsive design
- Client-side routing (React Router)
- JWT token management
- File upload with progress
- Real-time search results

**Pages**:
- `/upload` - Resume upload interface
- `/search` - Semantic search with filters
- `/jobs` - Job creation and management
- `/candidate/:id` - Detailed candidate view

### 2. API Layer (FastAPI)

**Purpose**: RESTful API backend with business logic

**Middleware Stack** (execution order):
1. `CORSMiddleware` - Cross-origin resource sharing
2. `RequestIDMiddleware` - Generate/propagate request IDs
3. `StructuredLoggingMiddleware` - JSON logging with PII masking
4. `RateLimitMiddleware` - 60 requests/min/user

**Routers**:
- `/api/auth` - Authentication (register, login, refresh)
- `/api/resumes` - Resume CRUD operations
- `/api/ask` - Semantic search endpoint
- `/api/jobs` - Job management and matching
- `/api/admin` - Admin operations (PII logs, queue status)
- `/api/meta` - Health check and metadata

**Key Design Decisions**:
- **Idempotency**: All POST creates require `Idempotency-Key` header
- **Rate Limiting**: Redis-backed, per-user limits
- **Async/Await**: Full async support for I/O operations
- **Dependency Injection**: FastAPI's DI for database sessions
- **Exception Handling**: Global handlers with structured error responses

### 3. Services Layer

#### Authentication Service (`auth.py`)
- JWT access tokens (15 min expiry)
- Refresh tokens (7 day expiry, rotation on use)
- Password hashing (bcrypt)
- Account lockout (5 failed attempts = 15 min lockout)

#### Parsing Service (`parsing.py`)
- PDF extraction (pdfminer.six)
- DOCX extraction (python-docx)
- TXT support
- ZIP archive handling
- Metadata extraction (title, author, creation date)

#### Embedding Service (`embedding.py`)
- Deterministic SHA256-based embeddings
- 1536-dimensional vectors (OpenAI compatibility)
- Text chunking (800 chars, 200 overlap)
- Normalization to unit length

#### Indexing Service (`indexing.py`)
- Vector storage in PostgreSQL (pgvector)
- L2 distance similarity (`<->` operator)
- Bulk insert for chunks
- Efficient search with HNSW index

#### PII Service (`pii.py`)
- Fernet encryption (AES-128-CBC)
- Field-level encryption for sensitive data
- Role-based redaction (user/recruiter/admin)
- Regex-based PII detection (email, phone, SSN)

#### Auditing Service (`auditing.py`)
- PII access logging
- User action tracking
- Timestamp + IP + user context
- Queryable audit trail

### 4. Data Layer

#### PostgreSQL + pgvector

**Tables**:
- `users` - User accounts (email, password hash, role)
- `resumes` - Resume metadata (filename, status, owner)
- `resume_chunks` - Text chunks with embeddings (vector column)
- `jobs` - Job postings (title, description, requirements)
- `refresh_tokens` - JWT refresh token storage
- `pii_store` - Encrypted PII data
- `pii_access_log` - PII access audit trail
- `idempotency_keys` - Request deduplication
- `ask_cache` - Query result caching

**Indexes**:
- HNSW index on `resume_chunks.embedding` for fast vector search
- B-tree indexes on foreign keys and common query fields
- Unique constraints on email, idempotency keys

#### Redis

**Uses**:
- Rate limiting (sliding window counters)
- RQ job queue for background tasks
- Session storage (future use)
- Query result caching

### 5. Observability

#### Structured Logging
- JSON format logs
- Request ID propagation
- PII masking in log messages
- Log levels: INFO (requests), WARNING (4xx), ERROR (5xx)

#### Prometheus Metrics
- HTTP metrics: request count, duration, status codes
- Business metrics: uploads, searches, matches
- Queue metrics: pending, failed, processing
- Error metrics: by type (validation, auth, internal)

#### OpenTelemetry Tracing
- Automatic FastAPI instrumentation
- Manual spans for key operations
- OTLP exporter to collector
- Request context propagation

## Security Architecture

### Authentication Flow

```mermaid
sequenceDiagram
    participant Client
    participant API
    participant Database
    participant Redis
    
    Client->>API: POST /api/auth/login
    API->>Database: Verify credentials
    Database-->>API: User found
    
    API->>API: Generate access token (15 min)
    API->>API: Generate refresh token (7 days)
    API->>Database: Store refresh token
    
    API-->>Client: {access_token, refresh_token}
    
    Note over Client: Store tokens securely
    
    Client->>API: Request with access token
    API->>API: Verify JWT signature
    API-->>Client: Response
    
    Note over Client: Access token expires
    
    Client->>API: POST /api/auth/refresh
    API->>Database: Validate refresh token
    Database-->>API: Token valid
    
    API->>API: Generate new access token
    API->>API: Rotate refresh token
    API->>Database: Store new refresh token
    API->>Database: Invalidate old refresh token
    
    API-->>Client: {access_token, refresh_token}
```

### PII Encryption

```mermaid
graph LR
    A[Plain PII Data] -->|Fernet Encrypt| B[Encrypted Data]
    B -->|Store| C[(Database)]
    C -->|Retrieve| D[Encrypted Data]
    D -->|Fernet Decrypt| E[Plain PII Data]
    E -->|Role-Based Redaction| F[Redacted/Full Data]
    F -->|Return| G[User/Recruiter/Admin]
```

**Encrypted Fields**:
- User email
- Resume metadata (name, contact info)
- Job descriptions (if containing PII)

**Encryption Key Management**:
- `FERNET_KEY` environment variable
- Must be 32 URL-safe base64-encoded bytes
- Recommended: AWS Secrets Manager / Azure Key Vault

## Scalability Considerations

### Horizontal Scaling

**API Tier**:
- Stateless design (no session state in memory)
- Multiple API instances behind load balancer
- Sticky sessions not required

**Worker Tier**:
- Multiple RQ workers can process queue concurrently
- Redis queue as coordination point
- Auto-scaling based on queue depth

**Database Tier**:
- PostgreSQL read replicas for search queries
- Write operations to primary
- Connection pooling (SQLAlchemy async)

### Performance Optimization

**Caching Strategy**:
- Query results cached in `ask_cache` table
- Idempotency responses cached for 24 hours
- Rate limit counters in Redis (fast in-memory)

**Database Optimization**:
- HNSW index for vector similarity (O(log n) search)
- Partial indexes on frequently filtered columns
- Bulk insert for resume chunks (one transaction)

**Async I/O**:
- All database operations use asyncpg
- Non-blocking request handling
- Uvicorn with multiple workers

## Deployment Architecture

### Production Environment

```mermaid
graph TB
    subgraph "CDN"
        CF[Cloudflare/CDN]
    end
    
    subgraph "Frontend Hosting (Vercel)"
        FE1[Frontend Instance 1]
        FE2[Frontend Instance 2]
    end
    
    subgraph "API Hosting (Render/Railway)"
        LB[Load Balancer]
        API1[API Instance 1]
        API2[API Instance 2]
        API3[API Instance 3]
    end
    
    subgraph "Background Workers"
        W1[Worker 1]
        W2[Worker 2]
    end
    
    subgraph "Data Services"
        PG[(PostgreSQL<br/>Managed)]
        REDIS[(Redis<br/>Managed)]
        S3[(S3/MinIO)]
    end
    
    subgraph "Observability"
        PROM[Prometheus]
        GRAF[Grafana]
        OTEL[OTEL Collector]
    end
    
    CF --> FE1
    CF --> FE2
    
    FE1 --> LB
    FE2 --> LB
    
    LB --> API1
    LB --> API2
    LB --> API3
    
    API1 --> PG
    API2 --> PG
    API3 --> PG
    
    API1 --> REDIS
    API2 --> REDIS
    API3 --> REDIS
    
    API1 --> S3
    API2 --> S3
    API3 --> S3
    
    REDIS --> W1
    REDIS --> W2
    
    W1 --> PG
    W2 --> PG
    
    API1 --> PROM
    API2 --> PROM
    API3 --> PROM
    
    API1 --> OTEL
    API2 --> OTEL
    API3 --> OTEL
    
    PROM --> GRAF
    OTEL --> GRAF
```

## Technology Decisions

### Why FastAPI?
- **Performance**: ASGI-based, async support, benchmarks comparable to Node.js
- **Developer Experience**: Auto-generated OpenAPI docs, type hints, dependency injection
- **Ecosystem**: Rich plugin ecosystem (SQLAlchemy, Alembic, Pydantic)

### Why PostgreSQL + pgvector?
- **Unified Storage**: Store structured data + vectors in one database
- **ACID Transactions**: Consistency guarantees for relational data
- **pgvector Extension**: Efficient vector similarity search with HNSW index
- **Maturity**: Battle-tested, rich tooling, managed services available

### Why Deterministic Embeddings (SHA256)?
- **Reproducibility**: Same text always produces same embedding
- **No API Costs**: No external calls to OpenAI/Cohere
- **Fast**: Hash computation is very fast (< 1ms)
- **Privacy**: All computation local, no data sent to third parties
- **Trade-off**: Lower semantic quality vs. transformer models, but sufficient for demo

### Why Redis for Queue?
- **In-Memory Performance**: Fast job enqueue/dequeue
- **RQ Integration**: Simple Python library, easy to use
- **Durability**: Optional persistence (RDB/AOF)
- **Monitoring**: Rich introspection tools

## Database Schema (ER Diagram)

```mermaid
erDiagram
    USERS ||--o{ RESUMES : owns
    USERS ||--o{ JOBS : creates
    USERS ||--o{ REFRESH_TOKENS : has
    USERS ||--o{ PII_ACCESS_LOG : performs
    
    RESUMES ||--|{ RESUME_CHUNKS : contains
    RESUMES }o--|| PII_STORE : "has encrypted data"
    
    JOBS ||--o{ JOB_REQUIREMENTS : has
    
    USERS {
        string id PK
        string email UK
        string password_hash
        string full_name
        string role
        int failed_login_attempts
        datetime locked_until
        datetime created_at
    }
    
    RESUMES {
        string id PK
        string owner_id FK
        string filename
        string file_path
        string status
        string visibility
        json parsed_metadata
        string parsing_hash
        datetime uploaded_at
    }
    
    RESUME_CHUNKS {
        string id PK
        string resume_id FK
        int page
        int start_offset
        int end_offset
        text text
        vector embedding
    }
    
    JOBS {
        string id PK
        string creator_id FK
        string title
        text description
        json requirements
        datetime created_at
    }
    
    REFRESH_TOKENS {
        string id PK
        string user_id FK
        string token_hash UK
        boolean is_revoked
        datetime expires_at
        datetime created_at
    }
    
    PII_STORE {
        string id PK
        string entity_type
        string entity_id
        string field_name
        binary encrypted_value
        datetime created_at
    }
    
    PII_ACCESS_LOG {
        string id PK
        string user_id FK
        string entity_type
        string entity_id
        string field_name
        string access_type
        datetime accessed_at
    }
```

## Future Architecture Enhancements

### Phase 4+ (Potential)

1. **GraphQL API** - For flexible client queries
2. **WebSocket Support** - Real-time search result updates
3. **Multi-Tenancy** - Organization-level isolation
4. **ML Model Integration** - Upgrade to transformer-based embeddings
5. **Full-Text Search** - PostgreSQL full-text for keyword search
6. **Recommendation Engine** - Job recommendations for candidates
7. **Analytics Dashboard** - Usage metrics and insights
8. **Mobile Apps** - React Native or Flutter clients

---

## References

- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [pgvector GitHub](https://github.com/pgvector/pgvector)
- [OpenTelemetry Python](https://opentelemetry.io/docs/instrumentation/python/)
- [Prometheus Best Practices](https://prometheus.io/docs/practices/)

---

_Last updated: October 4, 2025_
