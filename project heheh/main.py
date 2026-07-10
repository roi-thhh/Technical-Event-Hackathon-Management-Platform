"""
main.py — FastAPI application for the Hackathon Management Platform.
"""

import os
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import RedirectResponse
from pydantic import BaseModel, Field
from contextlib import asynccontextmanager

from database import get_db, hash_password, init_db, seed_db


# ---------------------------------------------------------------------------
# Lifespan: initialize and seed the database on startup
# ---------------------------------------------------------------------------
@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    seed_db()
    yield


app = FastAPI(
    title="Hackathon Management Platform",
    description="A lightweight backend API for managing hackathon teams, submissions, and evaluations.",
    version="1.0.0",
    lifespan=lifespan,
)

# ---------------------------------------------------------------------------
# CORS — allow frontend requests from any origin (dev convenience)
# ---------------------------------------------------------------------------
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---------------------------------------------------------------------------
# Static files — serve the frontend HTML pages
# ---------------------------------------------------------------------------
STATIC_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "static")
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")


# ---------------------------------------------------------------------------
# Root redirect → login page
# ---------------------------------------------------------------------------
@app.get("/")
def root():
    """Redirect to the login page."""
    return RedirectResponse(url="/static/login.html")


# ---------------------------------------------------------------------------
# Pydantic request/response models
# ---------------------------------------------------------------------------
class LoginRequest(BaseModel):
    username: str
    password: str


class LoginResponse(BaseModel):
    user_id: int
    role: str
    team_id: int | None


class EvaluateRequest(BaseModel):
    team_id: int
    judge_id: int
    score: int = Field(..., ge=1, le=10)
    feedback: str


class SubmitRequest(BaseModel):
    team_id: int
    github_link: str


class RegisterRequest(BaseModel):
    username: str
    password: str
    role: str = "participant"
    team_name: str | None = None


class PublishRequest(BaseModel):
    team_id: int
    judge_id: int


# ---------------------------------------------------------------------------
# POST /register
# ---------------------------------------------------------------------------
@app.post("/register")
def register(body: RegisterRequest):
    """Register a new user. Participants can optionally create/join a team."""
    # Validate role
    if body.role not in ("admin", "judge", "participant"):
        raise HTTPException(status_code=400, detail="Role must be 'admin', 'judge', or 'participant'")

    conn = get_db()
    cursor = conn.cursor()

    # Check if username already exists
    cursor.execute("SELECT user_id FROM Users WHERE username = ?", (body.username,))
    if cursor.fetchone() is not None:
        conn.close()
        raise HTTPException(status_code=409, detail="Username already taken")

    team_id = None

    # Handle team for participants
    if body.role == "participant" and body.team_name:
        team_name = body.team_name.strip()
        # Try to find existing team
        cursor.execute("SELECT team_id FROM Teams WHERE team_name = ?", (team_name,))
        existing = cursor.fetchone()
        if existing:
            team_id = existing["team_id"]
        else:
            # Create new team
            cursor.execute(
                "INSERT INTO Teams (team_name, submission_status) VALUES (?, 'pending')",
                (team_name,),
            )
            team_id = cursor.lastrowid

    # Insert user
    cursor.execute(
        "INSERT INTO Users (username, password_hash, role, team_id) VALUES (?, ?, ?, ?)",
        (body.username, hash_password(body.password), body.role, team_id),
    )
    user_id = cursor.lastrowid
    conn.commit()
    conn.close()

    return {
        "message": "Account created successfully",
        "user_id": user_id,
        "role": body.role,
        "team_id": team_id,
    }


# ---------------------------------------------------------------------------
# POST /login
# ---------------------------------------------------------------------------
@app.post("/login", response_model=LoginResponse)
def login(body: LoginRequest):
    """Authenticate a user and return their role and team_id."""
    conn = get_db()
    cursor = conn.cursor()

    cursor.execute(
        "SELECT user_id, role, team_id FROM Users WHERE username = ? AND password_hash = ?",
        (body.username, hash_password(body.password)),
    )
    user = cursor.fetchone()
    conn.close()

    if user is None:
        raise HTTPException(status_code=401, detail="Invalid username or password")

    return LoginResponse(user_id=user["user_id"], role=user["role"], team_id=user["team_id"])


# ---------------------------------------------------------------------------
# GET /admin/dashboard
# ---------------------------------------------------------------------------
@app.get("/admin/dashboard")
def admin_dashboard():
    """Return all teams and their submission statuses."""
    conn = get_db()
    cursor = conn.cursor()

    cursor.execute("SELECT team_id, team_name, github_link, submission_status FROM Teams")
    teams = [dict(row) for row in cursor.fetchall()]
    conn.close()

    return {"teams": teams}


# ---------------------------------------------------------------------------
# GET /judge/dashboard
# ---------------------------------------------------------------------------
@app.get("/judge/dashboard")
def judge_dashboard():
    """Return only teams whose submission_status is 'submitted'."""
    conn = get_db()
    cursor = conn.cursor()

    cursor.execute(
        "SELECT team_id, team_name, github_link, submission_status FROM Teams WHERE submission_status = ?",
        ("submitted",),
    )
    teams = [dict(row) for row in cursor.fetchall()]
    conn.close()

    return {"teams": teams}


# ---------------------------------------------------------------------------
# POST /judge/evaluate
# ---------------------------------------------------------------------------
@app.post("/judge/evaluate")
def judge_evaluate(body: EvaluateRequest):
    """Insert an evaluation for a team."""
    conn = get_db()
    cursor = conn.cursor()

    # Verify team exists
    cursor.execute("SELECT team_id FROM Teams WHERE team_id = ?", (body.team_id,))
    if cursor.fetchone() is None:
        conn.close()
        raise HTTPException(status_code=404, detail=f"Team with id {body.team_id} not found")

    # Verify judge exists and has the 'judge' role
    cursor.execute("SELECT user_id FROM Users WHERE user_id = ? AND role = ?", (body.judge_id, "judge"))
    if cursor.fetchone() is None:
        conn.close()
        raise HTTPException(status_code=404, detail=f"Judge with id {body.judge_id} not found")

    cursor.execute(
        "INSERT INTO Evaluations (team_id, judge_id, score, feedback) VALUES (?, ?, ?, ?)",
        (body.team_id, body.judge_id, body.score, body.feedback),
    )
    conn.commit()
    evaluation_id = cursor.lastrowid
    conn.close()

    return {"message": "Evaluation submitted successfully", "evaluation_id": evaluation_id}


# ---------------------------------------------------------------------------
# POST /participant/submit
# ---------------------------------------------------------------------------
@app.post("/participant/submit")
def participant_submit(body: SubmitRequest):
    """Update a team's github_link and set submission_status to 'submitted'."""
    conn = get_db()
    cursor = conn.cursor()

    # Verify team exists
    cursor.execute("SELECT team_id FROM Teams WHERE team_id = ?", (body.team_id,))
    if cursor.fetchone() is None:
        conn.close()
        raise HTTPException(status_code=404, detail=f"Team with id {body.team_id} not found")

    cursor.execute(
        "UPDATE Teams SET github_link = ?, submission_status = 'submitted' WHERE team_id = ?",
        (body.github_link, body.team_id),
    )
    conn.commit()
    conn.close()

    return {"message": "Submission recorded successfully", "team_id": body.team_id}


# ---------------------------------------------------------------------------
# GET /teams
# ---------------------------------------------------------------------------
@app.get("/teams")
def get_all_teams():
    """Return all teams and their submission statuses."""
    conn = get_db()
    cursor = conn.cursor()

    cursor.execute("SELECT team_id, team_name, github_link, submission_status FROM Teams")
    teams = [dict(row) for row in cursor.fetchall()]
    conn.close()

    return {"teams": teams}


# ---------------------------------------------------------------------------
# GET /teams/{team_id}/members
# ---------------------------------------------------------------------------
@app.get("/teams/{team_id}/members")
def get_team_members(team_id: int):
    """Return all members for a specific team."""
    conn = get_db()
    cursor = conn.cursor()

    cursor.execute("SELECT user_id, username, role FROM Users WHERE team_id = ?", (team_id,))
    members = [dict(row) for row in cursor.fetchall()]
    conn.close()

    return {"members": members}


# ---------------------------------------------------------------------------
# POST /judge/publish
# ---------------------------------------------------------------------------
@app.post("/judge/publish")
def judge_publish(body: PublishRequest):
    """Mark a team's grades as published."""
    conn = get_db()
    cursor = conn.cursor()

    # Verify team exists
    cursor.execute("SELECT team_id FROM Teams WHERE team_id = ?", (body.team_id,))
    if cursor.fetchone() is None:
        conn.close()
        raise HTTPException(status_code=404, detail=f"Team with id {body.team_id} not found")

    # Verify judge exists and has the 'judge' role
    cursor.execute("SELECT user_id FROM Users WHERE user_id = ? AND role = ?", (body.judge_id, "judge"))
    if cursor.fetchone() is None:
        conn.close()
        raise HTTPException(status_code=404, detail=f"Judge with id {body.judge_id} not found")

    cursor.execute(
        "UPDATE Teams SET grades_published = 1 WHERE team_id = ?",
        (body.team_id,)
    )
    conn.commit()
    conn.close()

    return {"message": "Grades published successfully", "team_id": body.team_id}


# ---------------------------------------------------------------------------
# GET /participant/grades/{team_id}
# ---------------------------------------------------------------------------
@app.get("/participant/grades/{team_id}")
def get_participant_grades(team_id: int):
    """Fetch grades and feedback for a team if published."""
    conn = get_db()
    cursor = conn.cursor()

    cursor.execute("SELECT grades_published FROM Teams WHERE team_id = ?", (team_id,))
    team = cursor.fetchone()
    if not team:
        conn.close()
        raise HTTPException(status_code=404, detail="Team not found")

    if not team["grades_published"]:
        conn.close()
        return {"published": False, "evaluations": []}

    cursor.execute("SELECT score, feedback FROM Evaluations WHERE team_id = ?", (team_id,))
    evaluations = [dict(row) for row in cursor.fetchall()]
    conn.close()

    return {"published": True, "evaluations": evaluations}
