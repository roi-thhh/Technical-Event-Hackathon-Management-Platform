"""
main.py — FastAPI application for the Hackathon Management Platform.
"""

import os
import uuid
import shutil
from fastapi import FastAPI, HTTPException, UploadFile, File
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
    # Ensure static/uploads exists
    upload_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "static", "uploads")
    os.makedirs(upload_dir, exist_ok=True)
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
    event_id: int | None


class EvaluateRequest(BaseModel):
    team_id: int
    judge_id: int
    score: int = Field(..., ge=1, le=10)
    feedback: str


class SubmitRequest(BaseModel):
    team_id: int
    github_link: str
    project_description: str | None = None
    screenshot: str | None = None


class RegisterRequest(BaseModel):
    username: str
    password: str
    role: str = "participant"
    team_name: str | None = None
    invite_code: str | None = None  # Admin event code or Judge invite code
    event_code: str | None = None   # Participant event code


class PublishRequest(BaseModel):
    team_id: int
    judge_id: int


class ProfileRequest(BaseModel):
    user_id: int
    full_name: str | None = None
    email: str | None = None
    phone: str | None = None
    college: str | None = None
    address: str | None = None
    linkedin: str | None = None
    github: str | None = None


class OrganizerSettingsRequest(BaseModel):
    event_id: int
    event_name: str
    team_size_limit: int
    submissions_open: bool
    countdown_end: str
    grades_published: bool


class EventCreateRequest(BaseModel):
    event_name: str
    max_team_size: int
    countdown_end: str | None = None
    created_by: int


class EventJoinRequest(BaseModel):
    user_id: int
    event_code: str


class TransferLeadershipRequest(BaseModel):
    leader_id: int
    new_leader_id: int


# ---------------------------------------------------------------------------
# POST /register
# ---------------------------------------------------------------------------
@app.post("/register")
def register(body: RegisterRequest):
    """Register a new user. Scopes user and team by event/judge invite codes."""
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
    event_id = None
    is_lead = 0

    if body.role == "admin":
        if body.invite_code:
            cursor.execute("SELECT event_id FROM Events WHERE event_code = ?", (body.invite_code.strip().upper(),))
            event_row = cursor.fetchone()
            if not event_row:
                conn.close()
                raise HTTPException(status_code=400, detail="Invalid Event Code")
            event_id = event_row["event_id"]
    
    elif body.role == "judge":
        if not body.invite_code:
            conn.close()
            raise HTTPException(status_code=400, detail="Judge registration requires an Invite Code")
        cursor.execute("SELECT event_id FROM Events WHERE judge_invite_code = ?", (body.invite_code.strip().upper(),))
        event_row = cursor.fetchone()
        if not event_row:
            conn.close()
            raise HTTPException(status_code=400, detail="Invalid Judge Invite Code")
        event_id = event_row["event_id"]

    elif body.role == "participant":
        code_to_check = body.event_code or body.invite_code
        if not code_to_check:
            conn.close()
            raise HTTPException(status_code=400, detail="Participant registration requires an Event Code")
        
        cursor.execute("SELECT event_id, max_team_size FROM Events WHERE event_code = ?", (code_to_check.strip().upper(),))
        event_row = cursor.fetchone()
        if not event_row:
            conn.close()
            raise HTTPException(status_code=400, detail="Invalid Event Code")
        event_id = event_row["event_id"]
        max_size = event_row["max_team_size"]

        if body.team_name:
            team_name = body.team_name.strip()
            # Find existing team *inside this event*
            cursor.execute("SELECT team_id FROM Teams WHERE team_name = ? AND event_id = ?", (team_name, event_id))
            existing = cursor.fetchone()
            if existing:
                team_id = existing["team_id"]
                # Enforce team size limit
                cursor.execute("SELECT COUNT(*) FROM Users WHERE team_id = ?", (team_id,))
                member_count = cursor.fetchone()[0]
                if member_count >= max_size:
                    conn.close()
                    raise HTTPException(
                        status_code=400,
                        detail=f"Team '{team_name}' has reached its limit of {max_size} members."
                    )
            else:
                # Create new team for this event
                cursor.execute(
                    "INSERT INTO Teams (team_name, submission_status, event_id) VALUES (?, 'pending', ?)",
                    (team_name, event_id),
                )
                team_id = cursor.lastrowid
                is_lead = 1

    # Insert user
    cursor.execute(
        "INSERT INTO Users (username, password_hash, role, team_id, event_id, is_lead) VALUES (?, ?, ?, ?, ?, ?)",
        (body.username, hash_password(body.password), body.role, team_id, event_id, is_lead),
    )
    user_id = cursor.lastrowid
    conn.commit()
    conn.close()

    return {
        "message": "Account created successfully",
        "user_id": user_id,
        "role": body.role,
        "team_id": team_id,
        "event_id": event_id
    }


@app.post("/login", response_model=LoginResponse)
def login(body: LoginRequest):
    """Authenticate a user and return their role, team_id and event_id."""
    conn = get_db()
    cursor = conn.cursor()

    cursor.execute(
        "SELECT user_id, role, team_id, event_id FROM Users WHERE username = ? AND password_hash = ?",
        (body.username, hash_password(body.password)),
    )
    user = cursor.fetchone()
    conn.close()

    if user is None:
        raise HTTPException(status_code=401, detail="Invalid username or password")

    return LoginResponse(
        user_id=user["user_id"],
        role=user["role"],
        team_id=user["team_id"],
        event_id=user["event_id"]
    )


# ---------------------------------------------------------------------------
# POST /upload
# ---------------------------------------------------------------------------
@app.post("/upload")
async def upload_files(files: list[UploadFile] = File(...)):
    """Save uploaded screenshot files to the local static uploads folder and return their URLs."""
    saved_paths = []
    upload_dir = os.path.join(STATIC_DIR, "uploads")
    for file in files:
        file_ext = os.path.splitext(file.filename)[1]
        unique_filename = f"{uuid.uuid4()}{file_ext}"
        file_path = os.path.join(upload_dir, unique_filename)
        
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
            
        saved_paths.append(f"/static/uploads/{unique_filename}")
        
    return {"urls": saved_paths}


# ---------------------------------------------------------------------------
# GET /admin/dashboard
# ---------------------------------------------------------------------------
@app.get("/admin/dashboard")
def admin_dashboard(event_id: int | None = None):
    """Return all teams and their submission statuses, filtered by event_id."""
    import json
    conn = get_db()
    cursor = conn.cursor()

    if event_id:
        cursor.execute("SELECT team_id, team_name, github_link, project_description, screenshot, submission_status FROM Teams WHERE event_id = ?", (event_id,))
    else:
        cursor.execute("SELECT team_id, team_name, github_link, project_description, screenshot, submission_status FROM Teams")
    teams = []
    for row in cursor.fetchall():
        t = dict(row)
        screenshot_val = t.get("screenshot")
        if screenshot_val:
            try:
                t["screenshots"] = json.loads(screenshot_val)
            except Exception:
                t["screenshots"] = [screenshot_val]
        else:
            t["screenshots"] = []
        teams.append(t)
    conn.close()

    return {"teams": teams}


# ---------------------------------------------------------------------------
# GET /judge/dashboard
# ---------------------------------------------------------------------------
@app.get("/judge/dashboard")
def judge_dashboard(event_id: int | None = None):
    """Return only teams whose submission_status is 'submitted' and belong to event_id."""
    import json
    conn = get_db()
    cursor = conn.cursor()

    if event_id:
        cursor.execute(
            "SELECT team_id, team_name, github_link, project_description, screenshot, submission_status FROM Teams WHERE submission_status = ? AND event_id = ?",
            ("submitted", event_id),
        )
    else:
        cursor.execute(
            "SELECT team_id, team_name, github_link, project_description, screenshot, submission_status FROM Teams WHERE submission_status = ?",
            ("submitted",),
        )
    teams = []
    for row in cursor.fetchall():
        t = dict(row)
        screenshot_val = t.get("screenshot")
        if screenshot_val:
            try:
                t["screenshots"] = json.loads(screenshot_val)
            except Exception:
                t["screenshots"] = [screenshot_val]
        else:
            t["screenshots"] = []
        teams.append(t)
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
    """Update a team's submission details and set submission_status to 'submitted'."""
    conn = get_db()
    cursor = conn.cursor()

    # Verify team exists
    cursor.execute("SELECT team_id, event_id FROM Teams WHERE team_id = ?", (body.team_id,))
    team_row = cursor.fetchone()
    if team_row is None:
        conn.close()
        raise HTTPException(status_code=404, detail=f"Team with id {body.team_id} not found")

    event_id = team_row["event_id"]

    # Enforce submissions open check
    if event_id:
        cursor.execute("SELECT submissions_open FROM Events WHERE event_id = ?", (event_id,))
        evt_row = cursor.fetchone()
        sub_open = evt_row["submissions_open"] if evt_row else 1
    else:
        sub_open = 1

    if not sub_open:
        conn.close()
        raise HTTPException(status_code=400, detail="Submissions are currently closed by the organizer.")

    cursor.execute(
        "UPDATE Teams SET github_link = ?, project_description = ?, screenshot = ?, submission_status = 'submitted' WHERE team_id = ?",
        (body.github_link, body.project_description, body.screenshot, body.team_id),
    )
    conn.commit()
    conn.close()

    return {"message": "Submission recorded successfully", "team_id": body.team_id}


# ---------------------------------------------------------------------------
# GET /teams
# ---------------------------------------------------------------------------
@app.get("/teams")
def get_all_teams(event_id: int | None = None):
    """Return all teams and their submission statuses, optionally filtered by event_id."""
    import json
    conn = get_db()
    cursor = conn.cursor()

    if event_id:
        cursor.execute("SELECT team_id, team_name, github_link, project_description, screenshot, submission_status FROM Teams WHERE event_id = ?", (event_id,))
    else:
        cursor.execute("SELECT team_id, team_name, github_link, project_description, screenshot, submission_status FROM Teams")
    teams = []
    for row in cursor.fetchall():
        t = dict(row)
        screenshot_val = t.get("screenshot")
        if screenshot_val:
            try:
                t["screenshots"] = json.loads(screenshot_val)
            except Exception:
                t["screenshots"] = [screenshot_val]
        else:
            t["screenshots"] = []
        teams.append(t)
    conn.close()

    return {"teams": teams}


# ---------------------------------------------------------------------------
# GET /teams/{team_id}
# ---------------------------------------------------------------------------
@app.get("/teams/{team_id}")
def get_team_by_id(team_id: int):
    """Return a single team's details by ID."""
    import json
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT team_id, team_name, github_link, project_description, screenshot, submission_status FROM Teams WHERE team_id = ?",
        (team_id,)
    )
    team = cursor.fetchone()
    conn.close()
    if team is None:
        raise HTTPException(status_code=404, detail="Team not found")
    
    team_dict = dict(team)
    screenshot_val = team_dict.get("screenshot")
    if screenshot_val:
        try:
            team_dict["screenshots"] = json.loads(screenshot_val)
        except Exception:
            team_dict["screenshots"] = [screenshot_val]
    else:
        team_dict["screenshots"] = []
    return team_dict


# ---------------------------------------------------------------------------
# GET /teams/{team_id}/members
# ---------------------------------------------------------------------------
@app.get("/teams/{team_id}/members")
def get_team_members(team_id: int):
    """Return all members for a specific team."""
    conn = get_db()
    cursor = conn.cursor()

    cursor.execute("SELECT user_id, username, role, is_lead FROM Users WHERE team_id = ?", (team_id,))
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
    """Fetch grades and feedback for a team if published and consensus met."""
    conn = get_db()
    cursor = conn.cursor()

    # Get team details
    cursor.execute("SELECT grades_published, event_id FROM Teams WHERE team_id = ?", (team_id,))
    team = cursor.fetchone()
    if not team:
        conn.close()
        raise HTTPException(status_code=404, detail="Team not found")

    event_id = team["event_id"]
    if not event_id:
        conn.close()
        return {"published": False, "reason": "Team is not associated with any event.", "evaluations": []}

    # Consensus Rule: Count total judges registered for this event
    cursor.execute("SELECT COUNT(*) FROM Users WHERE role = 'judge' AND event_id = ?", (event_id,))
    total_judges = cursor.fetchone()[0]

    # Count how many evaluations are submitted for this team
    cursor.execute("SELECT COUNT(DISTINCT judge_id) FROM Evaluations WHERE team_id = ?", (team_id,))
    evaluated_judges = cursor.fetchone()[0]

    if total_judges == 0:
        conn.close()
        return {"published": False, "reason": "No judges have registered for this event yet.", "evaluations": []}

    if evaluated_judges < total_judges:
        conn.close()
        return {
            "published": False,
            "reason": f"Evaluations are still in progress by the judges ({evaluated_judges}/{total_judges} completed).",
            "evaluations": []
        }

    # Fetch event grades publication settings
    cursor.execute("SELECT grades_published FROM Events WHERE event_id = ?", (event_id,))
    evt_row = cursor.fetchone()
    global_pub = evt_row["grades_published"] if evt_row else 0

    if not team["grades_published"] and not global_pub:
        conn.close()
        return {"published": False, "reason": "Grades have not been published by the organizer yet.", "evaluations": []}

    cursor.execute("SELECT score, feedback FROM Evaluations WHERE team_id = ?", (team_id,))
    evaluations = [dict(row) for row in cursor.fetchall()]
    conn.close()

    return {"published": True, "evaluations": evaluations}


# ---------------------------------------------------------------------------
# GET /participant/profile/{user_id}
# ---------------------------------------------------------------------------
@app.get("/participant/profile/{user_id}")
def get_profile(user_id: int):
    """Fetch profile details for a user."""
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT user_id, username, full_name, email, phone, college, address, linkedin, github FROM Users WHERE user_id = ?",
        (user_id,)
    )
    user = cursor.fetchone()
    conn.close()
    if user is None:
        raise HTTPException(status_code=404, detail="User not found")
    return dict(user)


# ---------------------------------------------------------------------------
# POST /participant/profile
# ---------------------------------------------------------------------------
@app.post("/participant/profile")
def update_profile(body: ProfileRequest):
    """Update profile details for a user."""
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute(
        """
        UPDATE Users 
        SET full_name = ?, email = ?, phone = ?, college = ?, address = ?, linkedin = ?, github = ?
        WHERE user_id = ?
        """,
        (body.full_name, body.email, body.phone, body.college, body.address, body.linkedin, body.github, body.user_id)
    )
    conn.commit()
    conn.close()
    return {"message": "Profile updated successfully"}


# ---------------------------------------------------------------------------
# GET /public/settings
# ---------------------------------------------------------------------------
@app.get("/public/settings")
def get_public_settings(event_id: int | None = None):
    """Retrieve basic public system configurations for an event."""
    conn = get_db()
    cursor = conn.cursor()
    if not event_id:
        # Get first event
        cursor.execute("SELECT event_id, event_name, max_team_size, countdown_end, submissions_open, grades_published FROM Events ORDER BY event_id LIMIT 1")
    else:
        cursor.execute("SELECT event_id, event_name, max_team_size, countdown_end, submissions_open, grades_published FROM Events WHERE event_id = ?", (event_id,))
    row = cursor.fetchone()
    conn.close()
    if not row:
        return {
            "event_name": "No Event Configured",
            "team_size_limit": 4,
            "submissions_open": "false",
            "countdown_end": "",
            "grades_published": "false"
        }
    return {
        "event_id": row["event_id"],
        "event_name": row["event_name"],
        "team_size_limit": row["max_team_size"],
        "submissions_open": "true" if row["submissions_open"] else "false",
        "countdown_end": row["countdown_end"] or "",
        "grades_published": "true" if row["grades_published"] else "false"
    }


# ---------------------------------------------------------------------------
# GET /organizer/settings
# ---------------------------------------------------------------------------
@app.get("/organizer/settings")
def get_organizer_settings(event_id: int):
    """Retrieve all organizer configs for an event."""
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT event_id, event_name, max_team_size, countdown_end, submissions_open, grades_published, event_code, judge_invite_code FROM Events WHERE event_id = ?", (event_id,))
    row = cursor.fetchone()
    conn.close()
    if not row:
        raise HTTPException(status_code=404, detail="Event not found")
    return {
        "event_id": row["event_id"],
        "event_name": row["event_name"],
        "team_size_limit": row["max_team_size"],
        "submissions_open": "true" if row["submissions_open"] else "false",
        "countdown_end": row["countdown_end"] or "",
        "grades_published": "true" if row["grades_published"] else "false",
        "event_code": row["event_code"],
        "judge_invite_code": row["judge_invite_code"]
    }


# ---------------------------------------------------------------------------
# POST /organizer/settings
# ---------------------------------------------------------------------------
@app.post("/organizer/settings")
def save_organizer_settings(body: OrganizerSettingsRequest):
    """Update event organizer parameters."""
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute(
        """
        UPDATE Events 
        SET event_name = ?, max_team_size = ?, submissions_open = ?, countdown_end = ?, grades_published = ?
        WHERE event_id = ?
        """,
        (body.event_name, body.team_size_limit, 1 if body.submissions_open else 0, body.countdown_end, 1 if body.grades_published else 0, body.event_id)
    )
    conn.commit()
    conn.close()
    return {"message": "Settings updated successfully"}


# ---------------------------------------------------------------------------
# POST /organizer/create-event
# ---------------------------------------------------------------------------
@app.post("/organizer/create-event")
def create_event(body: EventCreateRequest):
    """Create a new event, generating organizer and judge invite codes."""
    conn = get_db()
    cursor = conn.cursor()
    
    import random
    import string
    def gen_code(length=6):
        return ''.join(random.choices(string.ascii_uppercase + string.digits, k=length))
    
    event_code = gen_code(6)
    judge_code = "JDG-" + gen_code(4)
    
    while True:
        cursor.execute("SELECT event_id FROM Events WHERE event_code = ?", (event_code,))
        if not cursor.fetchone():
            break
        event_code = gen_code(6)
        
    while True:
        cursor.execute("SELECT event_id FROM Events WHERE judge_invite_code = ?", (judge_code,))
        if not cursor.fetchone():
            break
        judge_code = "JDG-" + gen_code(4)
        
    cursor.execute(
        """
        INSERT INTO Events (event_name, event_code, judge_invite_code, max_team_size, countdown_end, created_by)
        VALUES (?, ?, ?, ?, ?, ?)
        """,
        (body.event_name, event_code, judge_code, body.max_team_size, body.countdown_end, body.created_by)
    )
    event_id = cursor.lastrowid
    
    # Associate creator organizer with this event
    cursor.execute("UPDATE Users SET event_id = ? WHERE user_id = ?", (event_id, body.created_by))
    
    conn.commit()
    conn.close()
    return {
        "event_id": event_id,
        "event_name": body.event_name,
        "event_code": event_code,
        "judge_invite_code": judge_code
    }


# ---------------------------------------------------------------------------
# POST /organizer/join-event
# ---------------------------------------------------------------------------
@app.post("/organizer/join-event")
def join_event(body: EventJoinRequest):
    """Add an organizer to an existing event via event code."""
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT event_id, event_name FROM Events WHERE event_code = ?", (body.event_code.strip().upper(),))
    row = cursor.fetchone()
    if not row:
        conn.close()
        raise HTTPException(status_code=400, detail="Invalid Event Code")
        
    event_id = row["event_id"]
    cursor.execute("UPDATE Users SET event_id = ? WHERE user_id = ?", (event_id, body.user_id))
    conn.commit()
    conn.close()
    return {
        "message": "Successfully joined the event",
        "event_id": event_id,
        "event_name": row["event_name"]
    }


# ---------------------------------------------------------------------------
# GET /organizer/evaluations/{event_id}
# ---------------------------------------------------------------------------
@app.get("/organizer/evaluations/{event_id}")
def get_organizer_evaluations(event_id: int):
    """Retrieve all judge scores and feedback matrix for this event."""
    conn = get_db()
    cursor = conn.cursor()
    
    cursor.execute("SELECT team_id, team_name FROM Teams WHERE event_id = ?", (event_id,))
    teams = [dict(r) for r in cursor.fetchall()]
    
    cursor.execute("SELECT user_id, username FROM Users WHERE role = 'judge' AND event_id = ?", (event_id,))
    judges = [dict(r) for r in cursor.fetchall()]
    
    cursor.execute(
        """
        SELECT e.evaluation_id, e.team_id, e.judge_id, e.score, e.feedback, u.username as judge_name
        FROM Evaluations e
        JOIN Users u ON e.judge_id = u.user_id
        WHERE e.team_id IN (SELECT team_id FROM Teams WHERE event_id = ?)
        """,
        (event_id,)
    )
    evaluations = [dict(r) for r in cursor.fetchall()]
    
    conn.close()
    return {
        "teams": teams,
        "judges": judges,
        "evaluations": evaluations
    }


# ---------------------------------------------------------------------------
# POST /participant/transfer-leadership
# ---------------------------------------------------------------------------
@app.post("/participant/transfer-leadership")
def transfer_leadership(body: TransferLeadershipRequest):
    """Swap the team lead user flag to another team member."""
    conn = get_db()
    cursor = conn.cursor()
    
    cursor.execute("SELECT team_id, is_lead FROM Users WHERE user_id = ?", (body.leader_id,))
    lead_user = cursor.fetchone()
    if not lead_user or not lead_user["is_lead"]:
        conn.close()
        raise HTTPException(status_code=403, detail="Only the team leader can transfer leadership")
        
    team_id = lead_user["team_id"]
    
    cursor.execute("SELECT user_id FROM Users WHERE user_id = ? AND team_id = ?", (body.new_leader_id, team_id))
    new_lead_user = cursor.fetchone()
    if not new_lead_user:
        conn.close()
        raise HTTPException(status_code=400, detail="New leader must belong to the same team")
        
    cursor.execute("UPDATE Users SET is_lead = 0 WHERE user_id = ?", (body.leader_id,))
    cursor.execute("UPDATE Users SET is_lead = 1 WHERE user_id = ?", (body.new_leader_id,))
    
    conn.commit()
    conn.close()
    return {"message": "Team leadership transferred successfully"}
