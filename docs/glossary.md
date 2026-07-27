# DevStation Glossary — Everything we've done so far

---

## 1. Python / Environment

### `py`
Official Python launcher on Windows. Replaces `python` when the executable isn't in the PATH.

```powershell
py --version              # shows installed version
py -m pip install package # installs a package via pip
py -m uvicorn ...         # runs uvicorn as a module
```

### `pip`
Python package manager. Downloads and installs libraries listed in `requirements.txt` or passed directly.

```bash
pip install fastapi               # installs a single package
pip install -r requirements.txt   # installs everything listed in the file
```

When `pip` isn't in the PATH, use `py -m pip` (invokes pip as a Python module).

### `requirements.txt`
Plain text file listing the project's Python dependencies, one per line.

```
fastapi
uvicorn[standard]
sqlalchemy
pydantic-settings
```

The `[standard]` after `uvicorn` is an "extra" — it installs optional dependencies (in this case, hot reload support and better performance).

---

## 2. FastAPI

### What it is
Python framework for building REST APIs. Automatically generates interactive documentation (Swagger UI).

### `FastAPI()`
Creates the main application instance.

```python
from fastapi import FastAPI

app = FastAPI(title="DevStation API", version="0.1.0")
```

- `title` — API name (shown in Swagger)
- `version` — API version
- The variable **must** be called `app` because that's what uvicorn looks for in `app.main:app`

### `@app.get("/path")`
Decorator that registers a function to respond to HTTP GET requests at that path.

```python
@app.get("/health")
def health_check():
    return {"status": "healthy"}
```

Other HTTP methods:
- `@app.post("/path")` — create a resource
- `@app.patch("/path")` — partially update
- `@app.delete("/path")` — delete

### `APIRouter()`
Groups related routes in a separate file. Then registered in `app` via `include_router`.

```python
# in routers/snippets.py
from fastapi import APIRouter
router = APIRouter()

@router.get("/")
def list_snippets():
    ...

# in main.py
app.include_router(snippets.router, prefix="/api/snippets", tags=["snippets"])
```

- `prefix` — prepends a prefix to all routes in the router (e.g. `/` becomes `/api/snippets/`)
- `tags` — groups endpoints in the Swagger UI

### `response_model`
Defines the JSON format the API returns. FastAPI validates and serializes automatically.

```python
@router.get("/", response_model=list[SnippetResponse])
def list_snippets():
    ...
```

### `status_code`
Defines the HTTP status code returned by the endpoint.

```python
@router.post("/", status_code=201)   # 201 = Created
@router.delete("/", status_code=204) # 204 = No Content
```

### `Depends()`
Dependency injection. FastAPI calls the function passed in, grabs the return value, and injects it as a parameter.

```python
from fastapi import Depends

def get_db():
    db = SessionLocal()
    try:
        yield db      # delivers the session to the endpoint
    finally:
        db.close()    # closes it when the endpoint finishes

@router.get("/")
def list_snippets(db: Session = Depends(get_db)):
    # db is already a ready-to-use session
    ...
```

The `yield` is what makes this a generator — it "pauses" at the delivery, waits for the endpoint to finish, and then runs the `finally` block.

### `HTTPException`
HTTP error that FastAPI converts into a JSON response.

```python
from fastapi import HTTPException

raise HTTPException(status_code=404, detail="Snippet not found")
# returns: {"detail": "Snippet not found"} with status 404
```

### `lifespan`
Function that runs when the API starts up and shuts down. Used for setup (creating tables) and cleanup.

```python
from contextlib import asynccontextmanager

@asynccontextmanager
async def lifespan(app: FastAPI):
    # STARTUP: runs when the API boots
    Base.metadata.create_all(bind=engine)
    yield
    # SHUTDOWN: runs when the API stops (empty for now)

app = FastAPI(lifespan=lifespan)
```

Everything before `yield` is startup. Everything after is shutdown.

---

## 3. SQLAlchemy (ORM)

### What it is
ORM (Object-Relational Mapping) — translates Python classes into database tables. You manipulate objects, SQLAlchemy generates the SQL.

### `create_engine()`
Creates the database connection.

```python
from sqlalchemy import create_engine

engine = create_engine("sqlite:///./devstation.db")
```

The string is a connection URL. Formats:
- SQLite: `sqlite:///./filename.db`
- PostgreSQL: `postgresql://user:password@host:port/database`

The `connect_args={"check_same_thread": False}` is only needed for SQLite (it doesn't allow multi-threaded access by default).

### `sessionmaker()`
Session factory. A session is a "conversation" with the database — you run queries, add objects, and at the end commit or rollback.

```python
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)
```

- `bind=engine` — binds to the database
- `autoflush=False` — doesn't automatically send queries before each read
- `autocommit=False` — requires explicit `db.commit()` to save

### `DeclarativeBase`
Parent class for all models. Every class that inherits from it becomes a table.

```python
from sqlalchemy.orm import DeclarativeBase

class Base(DeclarativeBase):
    pass
```

### Model (class → table)
Each class inheriting from `Base` becomes a database table.

```python
class Snippet(Base):
    __tablename__ = "snippets"               # table name in the database

    id: Mapped[int] = mapped_column(primary_key=True)
    title: Mapped[str] = mapped_column(String(200))
    code: Mapped[str] = mapped_column(Text)
```

- `__tablename__` — table name in SQL
- `Mapped[str]` — Python type (used by the editor/type checker)
- `mapped_column(String(200))` — SQL type (VARCHAR(200))
- `primary_key=True` — primary key, auto-increments
- `server_default=func.now()` — default value generated by the database (current timestamp)
- `onupdate=func.now()` — auto-updates when the record changes

### Column types

| SQLAlchemy | SQL | Usage |
|---|---|---|
| `String(n)` | `VARCHAR(n)` | short text with limit |
| `Text` | `TEXT` | unlimited text |
| `DateTime` | `DATETIME` | date and time |

### Database operations

```python
# Create
snippet = Snippet(title="my snippet", code="print('hi')", language="python")
db.add(snippet)       # adds to the session
db.commit()           # saves to the database
db.refresh(snippet)   # reloads from the database (gets the generated id)

# Read
db.query(Snippet).all()                          # all records
db.query(Snippet).order_by(Snippet.updated_at.desc()).all()  # sorted
db.get(Snippet, 1)                               # by id

# Delete
db.delete(snippet)
db.commit()
```

### `Base.metadata.create_all(bind=engine)`
Creates all tables in the database based on the defined models. Only creates what doesn't exist — never overwrites.

---

## 4. Pydantic

### What it is
Data validation library. In the API context, it defines the format of incoming and outgoing JSONs.

### Schema vs Model
- **Model** (SQLAlchemy) = database table
- **Schema** (Pydantic) = JSON format in the API

They're separate because not everything in the database should appear in the API (and vice versa).

### `BaseModel`
Parent class for schemas. Each attribute becomes a JSON field.

```python
from pydantic import BaseModel

class SnippetCreate(BaseModel):       # input JSON (POST)
    title: str                         # required
    code: str                          # required
    language: str                      # required
    tags: str | None = ""              # optional, defaults to ""
    description: str | None = ""       # optional, defaults to ""
```

- `str` — required field
- `str | None = ""` — optional field with default value
- FastAPI validates automatically: if a required field is missing, it returns 422

### `model_config = {"from_attributes": True}`
Allows Pydantic to read attributes from a SQLAlchemy object (instead of requiring a dictionary).

```python
class SnippetResponse(BaseModel):
    id: int
    title: str
    ...
    model_config = {"from_attributes": True}
```

Without this, FastAPI can't convert database results into JSON.

### `.model_dump()`
Converts a Pydantic schema into a Python dictionary.

```python
data = SnippetCreate(title="test", code="x", language="py")
data.model_dump()
# {"title": "test", "code": "x", "language": "py", "tags": "", "description": ""}
```

Used with `**` to create the model: `Snippet(**data.model_dump())`.

---

## 5. Uvicorn

### What it is
ASGI server that runs the FastAPI application. It's the "waiter" that receives HTTP requests and passes them to your API for processing.

```bash
py -m uvicorn app.main:app --reload
```

- `app.main:app` — path in the format `module:variable`
  - `app.main` → file `app/main.py`
  - `:app` → variable `app` inside the file (the FastAPI instance)
- `--reload` — auto-restarts when you save a file (development only)
- `--host 0.0.0.0` — accepts connections from any IP (required inside a container)
- `--port 8000` — port the API listens on

---

## 6. Project structure

```
apps/api/
├── app/                    ← main Python package
│   ├── __init__.py         ← marks the folder as a Python package
│   ├── main.py             ← entrypoint — creates FastAPI, registers routers
│   ├── core/               ← configuration and infrastructure
│   │   ├── config.py       ← Settings (environment variables)
│   │   ├── database.py     ← engine, session, Base, get_db
│   │   └── metrics.py      ← Prometheus counters (future phase)
│   ├── models/             ← SQLAlchemy classes (database tables)
│   │   └── models.py       ← Snippet, Note, Link
│   ├── routers/            ← endpoints grouped by resource
│   │   └── snippets.py     ← Snippet CRUD
│   ├── schemas/            ← Pydantic schemas (JSON formats)
│   │   └── schemas.py      ← SnippetCreate, SnippetResponse
│   └── services/           ← business logic (future)
├── tests/                  ← automated tests
├── Dockerfile              ← recipe for building the Docker image
├── requirements.txt        ← production dependencies
└── requirements-dev.txt    ← development dependencies (pytest, ruff)
```

### `__init__.py`
A file (usually empty) that marks a folder as a "Python package". Without it, Python won't recognize the folder as importable. That's why every folder inside `app/` needs one.

### pydantic-settings (`Settings`)
Reads environment variables automatically. The attribute name becomes the variable name (case-insensitive).

```python
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    database_url: str = "sqlite:///./devstation.db"

settings = Settings()
```

If a `DATABASE_URL` environment variable exists, it overrides the default value. This is essential for Docker: the same code runs locally (SQLite) and in a container (PostgreSQL) without changing anything — you just swap the environment variable.

---

## 7. Docker (next step)

### `Dockerfile`
Step-by-step recipe for building an image (a snapshot of the environment).

```dockerfile
FROM python:3.12-slim       # base image
WORKDIR /app                # working directory inside the container
COPY requirements.txt .     # copy dependencies first (cache)
RUN pip install -r requirements.txt  # install them
COPY app/ app/              # copy the code
EXPOSE 8000                 # document the port
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

| Instruction | What it does |
|---|---|
| `FROM` | Sets the base image (OS + runtime) |
| `WORKDIR` | Creates and enters a directory inside the container |
| `COPY` | Copies files from your machine into the image |
| `RUN` | Runs a command during build (install packages, compile) |
| `EXPOSE` | Documents which port the container uses (doesn't actually open it) |
| `CMD` | Default command when the container starts |

### Why copy `requirements.txt` before the code?
Docker builds images in layers. If a layer hasn't changed, Docker reuses the cache. Copying dependencies first means that when you only change code, Docker skips package installation (the slowest layer).

---

## 8. Cross-cutting concepts

### REST API
HTTP-based communication pattern. Each URL represents a resource, and HTTP methods define the action:

| Method | Action | Example |
|---|---|---|
| `GET` | Read | `GET /api/snippets/` — list all |
| `POST` | Create | `POST /api/snippets/` — create new |
| `PATCH` | Partial update | `PATCH /api/snippets/1` — edit fields |
| `DELETE` | Delete | `DELETE /api/snippets/1` — remove |

### Swagger UI
Graphical interface auto-generated by FastAPI at `/docs`. Lets you test all endpoints without writing code or using curl.

### ORM (Object-Relational Mapping)
Pattern that maps Python classes ↔ SQL tables. Instead of writing `INSERT INTO snippets (title) VALUES ('test')`, you do `db.add(Snippet(title="test"))`.

### Dependency injection
Pattern where a function receives its resources ready-made instead of creating them. In FastAPI, `Depends(get_db)` injects a database session — the endpoint doesn't need to know how to create or close the connection.

### Generator (`yield`)
A function that "pauses" at the delivery and continues afterward. In `get_db()`, `yield` delivers the session, waits for the endpoint to finish, and then runs the `finally` block to close the connection.

```python
def get_db():
    db = SessionLocal()
    try:
        yield db       # pauses here — delivers db to the endpoint
    finally:
        db.close()     # continues here — closes the connection
```
---
 
## Docker — Commands
 
### `docker build`
Builds an image from a Dockerfile.
 
```powershell
docker build -t devstation-api .
```
 
- `-t devstation-api` — tags the image with a name (like a label)
- `.` — build context (the current directory). Docker sends everything in this folder to the build engine, which is why `.dockerignore` matters
### `docker run`
Creates and starts a container from an image.
 
```powershell
docker run -p 8000:8000 devstation-api
```
 
- `-p 8000:8000` — port mapping in the format `host:container`. The left side is your machine, the right side is inside the container. Without this, the container runs but you can't reach it from your browser
### `docker ps`
Lists running containers.
 
```powershell
docker ps        # running containers only
docker ps -a     # all containers (including stopped)
```
 
### `docker stop`
Stops a running container.
 
```powershell
docker stop <container_id>
```
 
### `docker logs`
Shows the output of a container (what it printed to the terminal).
 
```powershell
docker logs <container_id>
docker logs -f <container_id>   # -f = follow (like tail -f)
```
 
### `docker images`
Lists all images on your machine.
 
```powershell
docker images
```
 
### `docker rm` / `docker rmi`
Removes containers and images.
 
```powershell
docker rm <container_id>     # remove a stopped container
docker rmi devstation-api    # remove an image
```
 
---
 
## Docker — Concepts
 
### Image vs Container
An **image** is a snapshot — a frozen package with the OS, runtime, dependencies, and your code. A **container** is a running instance of that image. Same relationship as a class and an object: the image is the blueprint, the container is the live thing.
 
### Build context
The folder you pass to `docker build` (the `.` at the end). Docker sends this entire folder to the daemon. That's why `.dockerignore` exists — to exclude files you don't want inside the image (like `__pycache__`, `.git`, `node_modules`).
 
### `.dockerignore`
Works like `.gitignore` but for Docker builds. Files listed here are excluded from the build context.
 
```
__pycache__
*.pyc
.venv
.pytest_cache
tests
```
 
It lives next to the `Dockerfile`, always.
 
### Layers and cache
Each instruction in a Dockerfile (`FROM`, `COPY`, `RUN`) creates a layer. Docker caches layers — if nothing changed in that step, it skips it on the next build. That's why we structure the Dockerfile like this:
 
```dockerfile
COPY requirements.txt .        # layer 1: rarely changes
RUN pip install -r requirements.txt  # layer 2: skipped if requirements.txt didn't change
COPY app/ app/                  # layer 3: changes often (your code)
```
 
If you copy everything at once, changing one line of code invalidates the pip install cache and Docker reinstalls all packages — wasting minutes every build.
 
### Port mapping (`-p`)
Containers are isolated. A process inside a container listening on port 8000 is invisible to your machine unless you map it.
 
```
-p 8000:8000    → localhost:8000 on your machine → port 8000 in the container
-p 3000:8000    → localhost:3000 on your machine → port 8000 in the container
```
 
### Container is a clean environment
The container knows nothing about your machine. It doesn't have your globally installed Python packages, your PATH, or your files. Only what's explicitly in the Dockerfile exists inside it. That's why `requirements.txt` must list every dependency — the `pip install` you ran locally doesn't carry over.
 
### `--host 0.0.0.0`
When uvicorn runs with `--host 0.0.0.0`, it accepts connections from any network interface. Without it, uvicorn only listens on `127.0.0.1` (localhost inside the container), which means your machine can't reach it even with port mapping. This flag is required inside containers but not needed when running locally.
 
---
 
## Lessons learned
 
### "ModuleNotFoundError inside Docker"
If it works locally but fails in the container, the dependency is installed on your machine but missing from `requirements.txt`. The fix is always: add it to `requirements.txt` and rebuild.
 
### "Not Found" on `/`
The API only responds to registered routes. If there's no `@app.get("/")`, accessing `/` returns 404. This isn't an error — it means the API is running. Hit `/health` or `/docs` instead.
 
### Docker Desktop must be running
The `docker` command is just a CLI client. It talks to the Docker daemon (engine), which runs inside Docker Desktop. If Desktop isn't open, every command fails with "failed to connect to the docker API". Start the app, wait for the whale icon to stabilize, then retry.
 
---
 
## Docker Compose
 
### What it is
A tool that lets you define and run multiple containers together. Instead of running several `docker run` commands manually, you describe everything in a single `docker-compose.yml` file and start it all with one command.
 
### `docker-compose.yml`
YAML file that defines your entire local environment: which services to run, how they connect, what ports to expose, and where to store data.
 
```yaml
services:
  api:
    build:
      context: ./apps/api
    ports:
      - "8000:8000"
    environment:
      - DATABASE_URL=postgresql://devstation:changeme@db:5432/devstation
    depends_on:
      db:
        condition: service_healthy
 
  db:
    image: postgres:16-alpine
    environment:
      - POSTGRES_USER=devstation
      - POSTGRES_PASSWORD=changeme
      - POSTGRES_DB=devstation
    volumes:
      - pgdata:/var/lib/postgresql/data
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U devstation"]
      interval: 5s
      timeout: 3s
      retries: 5
 
volumes:
  pgdata:
```
 
### Key directives
 
| Directive | What it does |
|---|---|
| `services` | Top-level block that lists all containers |
| `build.context` | Path to the folder containing the Dockerfile |
| `image` | Uses a pre-built image from Docker Hub instead of building |
| `ports` | Maps `host:container` ports (same as `docker run -p`) |
| `environment` | Sets environment variables inside the container |
| `depends_on` | Controls startup order between services |
| `volumes` | Mounts persistent storage or host directories |
| `healthcheck` | Defines how Docker checks if the service is alive |
 
### `depends_on` with `condition: service_healthy`
Controls startup order. Without a condition, Docker just starts services in order but doesn't wait for them to be ready. With `service_healthy`, Docker waits until the dependency's healthcheck passes before starting the dependent service.
 
```yaml
depends_on:
  db:
    condition: service_healthy
# API won't start until Postgres healthcheck passes
```
 
### `healthcheck`
Tells Docker how to verify a service is working, not just running. Docker runs the test command at regular intervals.
 
```yaml
healthcheck:
  test: ["CMD-SHELL", "pg_isready -U devstation"]  # command to run
  interval: 5s      # check every 5 seconds
  timeout: 3s       # fail if no response in 3 seconds
  retries: 5        # mark as unhealthy after 5 consecutive failures
```
 
For the API, we use curl against the `/health` endpoint:
```yaml
healthcheck:
  test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
```
 
The repeating `GET /health` lines you see in the logs every 10 seconds — that's Docker running the healthcheck automatically.
 
### `volumes`
Persistent storage. Without volumes, all data inside a container is lost when the container stops. A named volume keeps data across restarts.
 
```yaml
services:
  db:
    volumes:
      - pgdata:/var/lib/postgresql/data   # named volume mapped to Postgres data dir
 
volumes:
  pgdata:   # declares the named volume
```
 
- `pgdata` is the volume name (you choose it)
- `/var/lib/postgresql/data` is where Postgres stores its files inside the container
- The `volumes:` block at the bottom (same level as `services:`) declares the volume so Docker creates and manages it
Test it: create a snippet, stop everything with `Ctrl+C`, run `docker compose up` again, list snippets — the data is still there.
 
### `environment`
Sets environment variables inside the container. These override defaults in your code.
 
```yaml
environment:
  - DATABASE_URL=postgresql://devstation:changeme@db:5432/devstation
```
 
This is how the same code runs with SQLite locally and PostgreSQL in Docker — `pydantic-settings` reads `DATABASE_URL` from the environment and overrides the default in `config.py`.
 
### Service names as hostnames
In the connection URL `postgresql://devstation:changeme@db:5432/devstation`, the `db` in the middle is not an IP address — it's the service name from the compose file. Docker Compose creates an internal network and lets containers find each other by service name. The API container calls `db` and Docker resolves it to the Postgres container's IP automatically.
 
---
 
## Docker Compose — Commands
 
### `docker compose up`
Starts all services defined in the compose file.
 
```powershell
docker compose up            # starts and shows logs in the terminal
docker compose up -d         # starts in detached mode (background)
docker compose up --build    # rebuilds images before starting
```
 
### `docker compose down`
Stops and removes all containers.
 
```powershell
docker compose down          # stops containers, keeps volumes
docker compose down -v       # stops containers AND deletes volumes (data is lost)
```
 
### `docker compose logs`
Shows output from all containers.
 
```powershell
docker compose logs          # all logs
docker compose logs api      # logs from a specific service
docker compose logs -f       # follow (live tail)
```
 
### `docker compose ps`
Lists the status of all compose services.
 
```powershell
docker compose ps
```
 
---
 
## Concepts reinforced
 
### `build` vs `image`
Two ways to define a service:
- `build: ./path` — Docker builds the image from a Dockerfile in that path
- `image: postgres:16-alpine` — Docker pulls a ready-made image from Docker Hub
Your API uses `build` (custom code). Postgres uses `image` (official, no customization needed).
 
### Internal networking
Docker Compose creates a private network for all services. Containers communicate using service names as hostnames. The outside world can only reach containers through mapped ports.
 
```
Your browser → localhost:8000 → (port mapping) → API container
                                                      ↓
                                               (internal network)
                                                      ↓
                                               DB container:5432
```
 
### `psycopg2-binary`
Python driver for PostgreSQL. SQLAlchemy needs it to talk to Postgres. When we switched from SQLite to PostgreSQL, we added this to `requirements.txt`. "Binary" means it comes pre-compiled — no need to install C libraries.
 
### `connect_args` removal
The `connect_args={"check_same_thread": False}` in `database.py` was a SQLite-only workaround. PostgreSQL handles concurrent connections natively, so we removed it when switching databases.
 
---
 
## Lessons learned
 
### "Port is already allocated"
A container from a previous `docker run` was still using port 8000. Fix: `docker ps` to find it, `docker stop <id>` to stop it, then retry. Always check running containers before starting new ones.
 
### Stop the right container
`docker ps` shows all running containers. Read the `NAMES` or `IMAGE` column to identify which one to stop. Stopping the wrong container (like the database instead of the old API) doesn't free the port.
 
---
 
## GitHub Actions
 
### What it is
GitHub's built-in CI/CD platform. It runs automated tasks (workflows) in response to events in your repository — like pushing code or opening a pull request. The machines that run your code are called **runners** (Linux VMs hosted by GitHub).
 
### Workflow file
A YAML file inside `.github/workflows/` that defines what to run and when. GitHub automatically detects and runs any `.yml` file in this directory.
 
```yaml
name: CI
 
on:
  push:
    branches: [main]
  pull_request:
    branches: [main]
```
 
- `name` — label shown in the Actions tab
- `on` — the event that triggers the workflow
- `push: branches: [main]` — runs when code is pushed to the main branch
- `pull_request: branches: [main]` — runs when a PR targets main
### Jobs
Independent units of work that run on separate machines. Each job gets a fresh Linux VM with nothing pre-installed.
 
```yaml
jobs:
  lint:
    runs-on: ubuntu-latest
    steps:
      ...
 
  test:
    runs-on: ubuntu-latest
    needs: lint
    steps:
      ...
```
 
- `runs-on: ubuntu-latest` — the runner OS (a fresh Ubuntu VM)
- `needs: lint` — this job only runs if `lint` succeeds. Without `needs`, jobs run in parallel
### Steps
Individual commands inside a job. They run sequentially — if one fails, the rest are skipped.
 
```yaml
steps:
  - uses: actions/checkout@v4
 
  - uses: actions/setup-python@v5
    with:
      python-version: "3.12"
 
  - name: Install ruff
    run: pip install ruff
 
  - name: Lint API
    run: ruff check apps/api/
```
 
### `uses`
Runs a pre-built action from the GitHub marketplace. Think of it as calling a reusable function someone else wrote.
 
| Action | What it does |
|---|---|
| `actions/checkout@v4` | Clones your repository into the runner |
| `actions/setup-python@v5` | Installs a specific Python version |
 
The `@v4` is the version of the action — like a tag or release.
 
### `run`
Executes a shell command directly on the runner.
 
```yaml
- name: Install dependencies
  run: pip install -r requirements.txt
 
- name: Run multiple commands
  run: |
    pip install -r requirements.txt
    pip install -r requirements-dev.txt
```
 
The `|` (pipe) allows multiple commands in sequence. Each line runs as a separate command.
 
### `with`
Passes configuration to an action.
 
```yaml
- uses: actions/setup-python@v5
  with:
    python-version: "3.12"
```
 
### `working-directory`
Changes the directory before running a command. Equivalent to `cd` before each step.
 
```yaml
- name: Run tests
  working-directory: apps/api
  run: pytest -v
```
 
Without this, commands run from the repository root.
 
### `name`
A label for the step — shows up in the Actions UI so you can identify what each step does when reading logs.
 
---
 
## Tools used in the pipeline
 
### Ruff
A fast Python linter written in Rust. Checks code for errors, style violations, and import ordering.
 
```bash
ruff check .          # check for errors
ruff check --fix .    # auto-fix what it can (imports, newlines)
```
 
Configured via `ruff.toml`:
 
```toml
line-length = 100
target-version = "py312"
 
[lint]
select = ["E", "F", "I", "W"]
```
 
| Rule | What it checks |
|---|---|
| `E` | PEP 8 style errors (line length, whitespace) |
| `F` | Pyflakes errors (unused imports, undefined names) |
| `I` | Import sorting (isort rules) |
| `W` | Warnings (missing newlines, trailing whitespace) |
 
### pytest
Python testing framework. Discovers and runs test files automatically.
 
```bash
pytest -v    # -v = verbose (shows each test name and result)
```
 
Conventions:
- Test files: `test_*.py` or `*_test.py`
- Test functions: `def test_something():`
- Assertions: `assert expression` — fails the test if expression is False
### TestClient (FastAPI)
A fake HTTP client that sends requests to your API without starting a real server.
 
```python
from fastapi.testclient import TestClient
from app.main import app
 
client = TestClient(app)
 
def test_health_check():
    response = client.get("/health")
    assert response.status_code == 200
```
 
No `uvicorn`, no port, no browser — it calls the API directly in memory.
 
---
 
## Support files
 
### `requirements-dev.txt`
Development-only dependencies. Kept separate from `requirements.txt` so production images don't include testing and linting tools.
 
```
ruff
pytest
httpx
```
 
- `httpx` — HTTP client required by FastAPI's TestClient internally
### `conftest.py`
pytest's configuration file. Runs before any test. We use it to add the project root to the Python path so `from app.main import app` works in CI.
 
```python
import sys
from pathlib import Path
 
sys.path.insert(0, str(Path(__file__).parent))
```
 
This is needed because the CI runner starts pytest from the `apps/api/` directory, but Python doesn't automatically know that `app` is a package inside it. Locally it works because uvicorn adds the directory to the path — pytest doesn't.
 
### `ruff.toml`
Ruff configuration file. Lives in `apps/api/` (next to the code it lints). Controls which rules to enforce and formatting preferences.
 
---
 
## Concepts
 
### CI (Continuous Integration)
The practice of automatically verifying every code change. When you push, the CI pipeline runs linters and tests. If anything fails, you know immediately — before the bad code reaches production.
 
The workflow: **push → lint → test → pass/fail**. No human has to remember to run the tests. The machine does it every time.
 
### Pipeline
A sequence of automated steps that run in order. In our case: lint first, then test (because there's no point testing code that doesn't even pass the linter).
 
### Green build
When all jobs pass. The green checkmark on the commit in GitHub means the code is verified. A red X means something failed — click it to see the logs and find out what broke.
 
---
 
## Lessons learned
 
### "ModuleNotFoundError: No module named 'app'" in CI
The test worked locally but failed in CI because the Python path was different. Fix: add `conftest.py` with `sys.path.insert`. The CI runner is a clean machine — it knows nothing about your local setup.
 
### Trailing newlines
Most linters expect files to end with a newline character. It's a Unix convention. When creating files on Windows, editors sometimes skip it. Fix: run `ruff check --fix .` before every commit.
 
### Pre-commit habit
Before every `git commit`, run:
```bash
ruff check --fix .    # auto-fix
ruff check .          # verify
pytest -v             # run tests
```
If all three pass locally, the CI will pass too. Catching errors before pushing saves time and keeps the commit history clean.
 
---
 
## Kubernetes — What it is
 
A container orchestrator. Docker runs containers — Kubernetes manages them: decides where they run, restarts them if they crash, scales them up or down, and handles networking between them. Think of Docker as a single musician and Kubernetes as the conductor of the orchestra.
 
In production, Kubernetes runs on real servers in the cloud. Locally, we use **kind** to simulate that environment inside Docker.
 
---
 
## Architecture — How the pieces fit
 
```
Your machine (Windows)
  └── Docker Desktop
        └── kind-node (container pretending to be a server)
              └── Kubernetes
                    ├── pod: api
                    └── pod: db
```
 
The kind-node is not Docker-inside-Docker. It's a Docker container simulating a Linux server, and Kubernetes inside it uses **containerd** (a different container runtime) to manage pods. In the cloud, the kind-node would be a real server.
 
---
 
## Tools
 
### `kind` (Kubernetes IN Docker)
Creates a local Kubernetes cluster using Docker containers as nodes.
 
```powershell
kind create cluster --name devstation    # create a cluster
kind delete cluster --name devstation    # delete it
kind load docker-image myapp:latest --name devstation  # load a local image into the cluster
```
 
The `kind load` step is important: the kind cluster has its own image registry, separate from Docker Desktop. If you don't load the image, Kubernetes can't find it.
 
### `kubectl` (Kubernetes CLI)
The command-line tool for talking to Kubernetes. Every interaction with the cluster goes through it.
 
```powershell
kubectl cluster-info       # show cluster connection details
kubectl get nodes          # list the servers in the cluster
kubectl get pods           # list running pods
kubectl get services       # list services
kubectl apply -f file.yaml # create or update resources from a manifest
kubectl delete -f file.yaml # delete resources defined in a manifest
kubectl logs -l app=api    # show logs from pods with label app=api
kubectl port-forward service/api 8000:8000  # tunnel traffic to a service
```
 
---
 
## Core concepts
 
### Pod
The smallest unit in Kubernetes. A pod wraps one or more containers and gives them a shared network and storage. In practice, most pods run a single container.
 
You don't create pods directly — you create Deployments, and Kubernetes creates the pods for you.
 
```powershell
kubectl get pods
# NAME                   READY   STATUS    RESTARTS   AGE
# api-6b55c847b4-fdx64   1/1     Running   0          5m
# db-7fddfdd557-b68gw    1/1     Running   0          5m
```
 
- `READY 1/1` — 1 container running out of 1 expected
- `STATUS Running` — the pod is alive
- `RESTARTS` — how many times Kubernetes restarted the pod (happens automatically on crashes)
### Deployment
Tells Kubernetes "I want N copies of this container running at all times." If a pod crashes, the Deployment creates a new one automatically.
 
```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: api
  labels:
    app: api
spec:
  replicas: 1
  selector:
    matchLabels:
      app: api
  template:
    metadata:
      labels:
        app: api
    spec:
      containers:
        - name: api
          image: devstation-api:latest
          imagePullPolicy: Never
          ports:
            - containerPort: 8000
          env:
            - name: DATABASE_URL
              value: postgresql://devstation:changeme@db:5432/devstation
```
 
### Deployment — field by field
 
| Field | What it does |
|---|---|
| `apiVersion: apps/v1` | Which Kubernetes API to use for this resource |
| `kind: Deployment` | The type of resource you're creating |
| `metadata.name` | Name of this Deployment |
| `metadata.labels` | Key-value tags for organizing and selecting resources |
| `spec.replicas` | How many pod copies to run (1 = single instance) |
| `spec.selector.matchLabels` | How the Deployment finds its pods (must match template labels) |
| `spec.template` | The pod blueprint — what to run inside each replica |
| `spec.template.metadata.labels` | Labels on the pod (must match selector) |
| `spec.template.spec.containers` | List of containers in the pod |
| `containers[].image` | Docker image to use |
| `containers[].imagePullPolicy: Never` | Don't try to download the image — use the local one loaded via `kind load` |
| `containers[].ports` | Ports the container listens on |
| `containers[].env` | Environment variables passed to the container |
 
### Service
Gives pods a stable network address. Pods are ephemeral — they get random names and IPs that change on every restart. A Service provides a fixed DNS name that other pods can use.
 
```yaml
apiVersion: v1
kind: Service
metadata:
  name: db
spec:
  selector:
    app: db
  ports:
    - port: 5432
      targetPort: 5432
```
 
| Field | What it does |
|---|---|
| `metadata.name` | The DNS name other pods use to reach this service (`db` becomes the hostname) |
| `spec.selector` | Which pods this Service routes traffic to (matches pod labels) |
| `ports[].port` | Port the Service listens on |
| `ports[].targetPort` | Port on the actual pod container |
 
This is why `DATABASE_URL` uses `@db:5432` — `db` is the Service name, and Kubernetes resolves it to the Postgres pod's IP automatically. Same concept as Docker Compose service names, but managed by Kubernetes DNS.
 
### Labels and selectors
The glue that connects everything. Labels are key-value pairs on resources. Selectors filter resources by their labels.
 
```
Deployment (selector: app=api) ──finds──> Pods (label: app=api)
Service    (selector: app=db)  ──routes──> Pods (label: app=db)
```
 
If the labels don't match the selector, Kubernetes can't connect the pieces and nothing works.
 
---
 
## The `---` separator
 
In YAML, `---` separates multiple documents in one file. We use it to put a Deployment and a Service in the same file:
 
```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: api
spec:
  ...
---
apiVersion: v1
kind: Service
metadata:
  name: api
spec:
  ...
```
 
`kubectl apply -f` reads both and creates both resources.
 
---
 
## Commands used
 
### `kubectl apply -f`
Creates or updates resources from a YAML file. If the resource already exists, it updates it. If not, it creates it.
 
```powershell
kubectl apply -f k8s/base/api/deployment.yaml
# deployment.apps/api created
# service/api created
```
 
### `kubectl get pods`
Lists all pods and their status.
 
### `kubectl logs`
Shows the stdout of a pod (what it printed to the terminal). Useful for debugging.
 
```powershell
kubectl logs -l app=api         # logs from pods with label app=api
kubectl logs -l app=api -f      # follow (live tail)
kubectl logs api-6b55c847b4-fdx64  # logs from a specific pod by name
```
 
### `kubectl port-forward`
Creates a tunnel from your machine to a Service or Pod inside the cluster. Required because the cluster network is isolated — your browser can't reach pods directly.
 
```powershell
kubectl port-forward service/api 8000:8000
```
 
- `service/api` — forward to the Service named "api"
- `8000:8000` — local port 8000 → service port 8000
- The command runs in the foreground — keep the terminal open while using it
---
 
## Docker Compose vs Kubernetes
 
| | Docker Compose | Kubernetes |
|---|---|---|
| **Config file** | `docker-compose.yml` | YAML manifests in `k8s/` |
| **Runs on** | Single machine | Cluster of machines |
| **Restart on crash** | Only if configured | Automatic (Deployments) |
| **Scaling** | Manual (`replicas` in compose) | `kubectl scale` or autoscaler |
| **Networking** | Service names as hostnames | Service names as DNS, same idea |
| **Storage** | Docker volumes | PersistentVolumeClaims |
| **Use case** | Local development | Staging and production |
 
You'll keep using Docker Compose for local dev (it's faster) and Kubernetes for anything beyond that.
 
---
 
## Lessons learned
 
### API crashed before the database was ready
The API pod started and tried to connect to Postgres, but the database pod was still being created (`ContainerCreating`). Kubernetes automatically restarted the API pod — after 2 restarts, the database was ready and the API connected successfully. This is expected behavior: Kubernetes doesn't have `depends_on` like Docker Compose, so pods need to handle transient connection failures gracefully.
 
### `imagePullPolicy: Never`
Without this, Kubernetes tries to pull the image from Docker Hub (the public registry). Since `devstation-api:latest` only exists locally (loaded via `kind load`), the pull fails. Setting `Never` tells Kubernetes to use the image already present in the node.
