# signalCore

ERRCS (Emergency Responder Radio Coverage System) engineering SaaS for Pacific DAS. Engineers upload building plan PDFs, the system auto-classifies the building, determines AHJ requirements, places antennas, computes link budgets, and generates a ready-to-submit AHJ packet plus a client-facing bid proposal.

## Stack

| Layer | Technology |
|---|---|
| API | Python 3.12, FastAPI, SQLAlchemy 2.0 (async), Alembic, PostgreSQL (asyncpg) |
| PDF Processing | pdfplumber (extraction), reportlab (generation), pypdf (assembly) |
| Geometry / RF | shapely, numpy |
| Auth | Auth0 JWT bearer — Engineer auto-provisioned on first request |
| File Storage | AWS S3 (uploaded plans + generated output packets) |
| Frontend | Next.js 15 (App Router), TypeScript, Tailwind CSS, shadcn/ui |
| Tests | pytest, pytest-asyncio, httpx (async test client) |
| Local infra | Docker Compose |
| Prod target | Render (API), Vercel (frontend) |

## Commands

```bash
# Backend (run from api/)
cd api
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000

# Run tests
cd api && pytest

# Alembic migrations (run from api/)
cd api
alembic revision --autogenerate -m "PascalCaseName"
alembic upgrade head

# Frontend (run from web/)
cd web && npx tsc --noEmit       # typecheck
cd web && npm run build          # full Next.js build
cd web && npm run dev            # local dev on :3000

# Local dev (everything at once)
docker compose up --build        # starts API (:8000), web (:3000), PostgreSQL (:5432)

# API docs (when running locally)
# http://localhost:8000/docs      (Swagger)
# http://localhost:8000/redoc     (ReDoc)
```

Migrations run automatically on startup (`alembic upgrade head` called in lifespan) — no manual apply step in dev.

## Project Structure

```
api/
  app/
    main.py              # FastAPI app factory, lifespan, middleware
    routers/             # Route handlers (projects, ahj, packets, share)
    models/              # SQLAlchemy ORM models
    services/            # Business logic (classifier, ahj, engine dispatch, drawing gen)
    core/                # Auth helpers, config, S3 client, result types
    engines/             # Building-type engines: single_floor, multi_floor, high_rise, parking, healthcare
    drawings/            # PDF generators: equipment, riser, overlay
  tests/
  alembic/
  requirements.txt
  Dockerfile
web/
  src/
    app/                 # Next.js App Router pages
    components/          # React components (projects/, packets/, shared/)
    lib/                 # api.ts, actions.ts, utils.ts
    types/index.ts       # TypeScript interfaces matching API response schemas
    middleware.ts        # Auth0 session middleware
infra/
  docker-compose.yml
  .env.example
.claude/
  settings.local.json
  hooks/verify-build.sh  # PostToolUse: pytest or tsc after every edit
```

## API Modules

| Module | Entities | Routes |
|---|---|---|
| Projects | Project, Floor | /api/projects |
| AHJ | AHJProfile | /api/ahj |
| Packets | SubmittalPacket | /api/packets |
| Presentation | ShareableLink | /api/share/:token |

## Code Conventions

### Models (app/models/)

- UUID `id` as primary key (`server_default=text("gen_random_uuid()")`)
- `created_at` / `updated_at` with `server_default=func.now()`
- Relationships at bottom; use `Mapped[list[T]]` typing

```python
class Project(Base):
    __tablename__ = "projects"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, server_default=text("gen_random_uuid()"))
    engineer_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("engineers.id"), nullable=False)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    address: Mapped[str | None] = mapped_column(String(500))
    created_at: Mapped[datetime] = mapped_column(server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(server_default=func.now(), onupdate=func.now())

    # Relationships
    engineer: Mapped["Engineer"] = relationship(back_populates="projects")
    packets: Mapped[list["SubmittalPacket"]] = relationship(back_populates="project", cascade="all, delete-orphan")
```

### Schemas (app/schemas/ — Pydantic v2)

- Three models per entity: `CreateFooSchema`, `UpdateFooSchema`, `FooSchema` (response)
- Use `model_config = ConfigDict(from_attributes=True)` on response schemas

```python
class CreateProjectSchema(BaseModel):
    name: str
    address: str | None = None

class UpdateProjectSchema(BaseModel):
    name: str | None = None
    address: str | None = None

class ProjectSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    engineer_id: uuid.UUID
    name: str
    address: str | None
    created_at: datetime
```

### Result[T] (app/core/result.py)

All service methods return `Result[T]`. Discriminated union — never raise for flow control.

```python
# Variants
Result.ok(value)
Result.not_found("Project {id} not found")
Result.validation_error("Name is required")   # or list[str]
Result.failure("Failed to create project")
Result.forbidden("Not your resource")
Result.conflict("Project already exists")

# Usage in router
result = await project_service.create(engineer_id, dto)
return result.to_response()   # maps to appropriate HTTP status
```

### Services (app/services/)

- Constructor injection via FastAPI `Depends`
- Validate → call repo/DB → map to schema → return Result
- Wrap DB calls in try/except; log and return `Result.failure` on exception

```python
class ProjectService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create(self, engineer_id: UUID, dto: CreateProjectSchema) -> Result[ProjectSchema]:
        if not dto.name.strip():
            return Result.validation_error("Name is required")
        try:
            project = Project(engineer_id=engineer_id, name=dto.name, address=dto.address)
            self.db.add(project)
            await self.db.commit()
            await self.db.refresh(project)
            logger.info("Created project %s", project.id)
            return Result.ok(ProjectSchema.model_validate(project))
        except Exception as e:
            logger.exception("Error creating project for engineer %s", engineer_id)
            return Result.failure("Failed to create project")
```

### Routers (app/routers/)

- APIRouter per domain, prefix `/api/foos`, tag `foos`
- Always resolve engineer identity first; raise 401 if missing
- Ownership check before mutating: `if resource.engineer_id != engineer.id: raise HTTPException(403)`

```python
router = APIRouter(prefix="/api/projects", tags=["projects"])

@router.post("/", response_model=ProjectSchema, status_code=201)
async def create_project(
    dto: CreateProjectSchema,
    engineer: Engineer = Depends(get_current_engineer),
    service: ProjectService = Depends(get_project_service),
):
    result = await service.create(engineer.id, dto)
    return result.to_response()
```

Register in main.py: `app.include_router(projects_router)`

### ERRCS Engine Conventions

- Each engine lives in `app/engines/<type>.py` and inherits from `BaseEngine`
- `BaseEngine.run(output_path: str) -> dict` produces the overlay PDF and returns stats
- Engines are stateless per run; receive `R_OFFICE`, `R_WAREHOUSE`, `BDA_OUTPUT_dBm` from dispatcher
- Geometry uses `shapely` polygons; antenna coverage modeled as circles clipped to floor polygon

### Alembic Migration Naming

Use descriptive snake_case matching what changed: `add_projects_table`, `add_address_to_projects`, `add_shareable_links`. Timestamp prefix is auto-generated.

### Frontend Conventions

- Types in `web/src/types/index.ts` — plain TypeScript interfaces matching API response schemas
- API calls in `web/src/lib/api.ts` — async functions, fetch with session token
- Server actions in `web/src/lib/actions.ts`
- Components colocated with their page when page-specific, in `components/` when shared
- Auth0 session via `@auth0/nextjs-auth0`; middleware in `middleware.ts` protects all routes except `/share/:token` and `/api/auth/*`

## Architecture Decisions

- **Modular monolith** — seamed by domain (Projects / AHJ / Packets / Presentation). Could extract engines to a worker queue later.
- **Multi-tenancy** — each Engineer sees only their own projects. Enforced at service level (`engineer_id` filter on all queries) and router level (ownership check before mutate).
- **Engineer auto-provisioning** — `get_current_engineer` dep creates an Engineer row on first authenticated request using the Auth0 `sub` claim.
- **S3 for files** — uploaded PDFs and generated output packets stored in S3. DB stores S3 keys only.
- **Async-first** — FastAPI + asyncpg + SQLAlchemy async throughout. No sync DB calls.
- **Snapshots for shareable links** — `ShareableLink.snapshot_data` stores a JSON blob of the packet at share time. Client link always shows the state at time of sharing.
- **No exceptions for flow control** — services use `Result[T]`. Exceptions are only for unexpected failures, caught and converted to `Result.failure`.

## ERRCS Domain Glossary

| Term | Meaning |
|---|---|
| AHJ | Authority Having Jurisdiction — the fire department or fire marshal that approves the system |
| ERRCS | Emergency Responder Radio Coverage System |
| BDA | Bi-Directional Amplifier — the signal booster hardware |
| Link budget | Calculation of signal gain/loss from donor antenna → BDA → splitter tree → omni antenna |
| Tapper | Passive RF coupler that splits signal at calibrated loss (e.g., CO-E05NI = 5 dB tap) |
| Submittal packet | AHJ deliverable: ERRC-1.01 Equipment Schedule + ERRC-1.03 Riser Diagram + floor plan overlay |
| R_OFFICE / R_WH | Antenna coverage radius (feet) for office-density vs. warehouse-density spaces |
| n factor | Path loss exponent — higher = more signal attenuation per distance doubling |
| CFC §510 | California Fire Code section governing ERRCS |
| NFPA 1225 | National standard for emergency responder communications enhancement systems |

## What's Not Built Yet

- **Bid proposal generation** — scope TBD; planned after core submittal packet is deployed
- **Stripe / subscription billing** — no payment code; planned
- **Email notifications** — not yet implemented
- **Proper AHJ database** — currently a hardcoded Python dict; needs to move to PostgreSQL with admin UI

## Environment Variables

| Variable | Description |
|---|---|
| `DATABASE_URL` | PostgreSQL async connection string (`postgresql+asyncpg://...`) |
| `AUTH0_DOMAIN` | Auth0 tenant URL |
| `AUTH0_AUDIENCE` | Auth0 API identifier |
| `AUTH0_CLIENT_ID` | Auth0 client ID for the web app |
| `AWS_ACCESS_KEY_ID` / `AWS_SECRET_ACCESS_KEY` | S3 credentials |
| `S3_BUCKET` | S3 bucket name for file storage |
| `WEB_URL` | Frontend origin for CORS |
| `API_URL` | API base URL used by the frontend |

## Hooks (Auto-configured)

`PostToolUse` hook fires after every Edit/Write:
- Files under `api/` → `cd api && python -m pytest --tb=short -q` (or just `python -m py_compile <file>` for speed)
- Files under `web/` → `npx tsc --noEmit`
- Build failure → error fed back immediately; fix before moving on
