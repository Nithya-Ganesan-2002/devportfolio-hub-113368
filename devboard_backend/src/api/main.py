from fastapi import FastAPI, HTTPException, status, Header, Depends, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer
from typing import List, Optional

from .models import (
    UserAuth, UserProfile, UserProfileCreate, UserProfileUpdate,
    Project, ProjectCreate, ProjectListResponse,
    TagFilterResponse, AuthResponse,
)
from .auth_utils import hash_password, verify_password, create_access_token, decode_access_token
from .datastore import DB

app = FastAPI(
    title="DevBoard API",
    description="Backend API for DevBoard: a developer portfolio and project hub (user profiles, project uploads, tag filtering, like system).",
    version="0.1.0",
    openapi_tags=[
        {"name": "auth", "description": "User authentication (signup, login)"},
        {"name": "profiles", "description": "Profile management"},
        {"name": "projects", "description": "Project uploads, listing, like system"},
        {"name": "filters", "description": "Tag filter and search"},
        {"name": "likes", "description": "Project like/unlike"},
        {"name": "public", "description": "Public views for portfolios/projects"},
    ]
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

bearer_scheme = HTTPBearer(auto_error=False)

def get_current_user(request: Request, authorization: Optional[str] = Header(None)) -> dict:
    """Extract and validate current user from Authorization Bearer token."""
    if not authorization or not authorization.lower().startswith("bearer "):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Missing or invalid auth token")
    token = authorization.split(" ", 1)[1]
    payload = decode_access_token(token)
    user_id = payload.get("sub")
    user = DB.get_user_by_id(user_id)
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found")
    return user

@app.get("/", summary="Health Check", tags=["public"])
def health_check():
    """Health check endpoint returns status."""
    return {"message": "Healthy"}

# ---------- AUTHENTICATION ----------

@app.post("/auth/signup", summary="Sign Up", tags=["auth"], response_model=AuthResponse)
def signup(user: UserAuth, profile: UserProfileCreate):
    """Register a new user with profile details."""
    if DB.get_user_by_email(user.email):
        raise HTTPException(status_code=400, detail="Email already registered")
    if DB.get_user_by_username(profile.username):
        raise HTTPException(status_code=400, detail="Username already taken")
    hashed_pw = hash_password(user.password)
    user_data = {
        "email": user.email,
        "password": hashed_pw,
        "name": profile.name,
        "username": profile.username,
        "bio": profile.bio,
        "avatar_url": profile.avatar_url
    }
    user_obj = DB.add_user(user_data)
    token = create_access_token({"sub": user_obj.id, "email": user_obj.email})
    return AuthResponse(access_token=token, user=user_obj)

@app.post("/auth/login", summary="Login", tags=["auth"], response_model=AuthResponse)
def login(user: UserAuth):
    """Authenticate a user and return an access token."""
    db_user = DB.get_user_by_email(user.email)
    if not db_user or not verify_password(user.password, db_user["password"]):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    user_obj = UserProfile(**db_user)
    token = create_access_token({"sub": user_obj.id, "email": user_obj.email})
    return AuthResponse(access_token=token, user=user_obj)

# ---------- PROFILE MANAGEMENT ----------

@app.get("/profile/me", summary="Get My Profile", tags=["profiles"], response_model=UserProfile)
def get_my_profile(current_user=Depends(get_current_user)):
    """Get the authenticated user's profile."""
    return UserProfile(**current_user)

@app.patch("/profile/me", summary="Edit My Profile", tags=["profiles"], response_model=UserProfile)
def edit_profile(update: UserProfileUpdate, current_user=Depends(get_current_user)):
    """Edit the authenticated user's profile (name, bio, avatar)."""
    updated = DB.update_user(current_user["id"], update.dict())
    return updated

# ---------- PROJECTS ----------

@app.post("/projects", summary="Upload New Project", tags=["projects"], response_model=Project)
def upload_project(project: ProjectCreate, current_user=Depends(get_current_user)):
    """Upload a new project for the authenticated user."""
    proj = DB.add_project(current_user["id"], project.dict())
    return proj

@app.get("/projects", summary="List Projects", tags=["projects"], response_model=ProjectListResponse)
def list_projects(
    tag: Optional[int] = None,
    user: Optional[str] = None,
    skip: int = 0,
    limit: int = 30,
):
    """List all projects, optionally filtered by tag or username."""
    tag_ids = [tag] if tag else []
    user_id = None
    if user:
        u = DB.get_user_by_username(user)
        if not u:
            raise HTTPException(404, "User not found")
        user_id = u["id"]
    projects = DB.list_projects(tag_ids=tag_ids or None, user_id=user_id)
    total = len(projects)
    return ProjectListResponse(projects=projects[skip: skip+limit], total=total)

@app.get("/projects/{project_id}", summary="Get Project Details", tags=["projects"], response_model=Project)
def get_project(project_id: int):
    """Get full information for a given project by its ID."""
    project = DB.get_project_by_id(project_id)
    if not project:
        raise HTTPException(404, "Project not found")
    return project

# ---------- TAG FILTERING ----------

@app.get("/tags", summary="List All Tags", tags=["filters"], response_model=TagFilterResponse)
def filter_tags():
    """List all project tags (for filtering/search)."""
    return TagFilterResponse(tags=DB.list_tags())

# ---------- LIKE SYSTEM ----------

@app.post("/projects/{project_id}/like", summary="Like Project", tags=["likes"], response_model=dict)
def like_project(project_id: int, current_user=Depends(get_current_user)):
    """Like a project (authenticated, only once per user)."""
    if not DB.get_project_by_id(project_id):
        raise HTTPException(404, "Project not found")
    likes = DB.like_project(current_user["id"], project_id)
    return {"likes": likes, "liked": True}

@app.post("/projects/{project_id}/unlike", summary="Unlike Project", tags=["likes"], response_model=dict)
def unlike_project(project_id: int, current_user=Depends(get_current_user)):
    """Unlike a project that was liked previously."""
    if not DB.get_project_by_id(project_id):
        raise HTTPException(404, "Project not found")
    likes = DB.unlike_project(current_user["id"], project_id)
    return {"likes": likes, "liked": False}

@app.get("/profile/me/likes", summary="My Liked Projects", tags=["likes"], response_model=List[int])
def my_liked_projects(current_user=Depends(get_current_user)):
    """List IDs of projects the authenticated user has liked."""
    return DB.user_liked_projects(current_user["id"])

# ---------- PUBLIC PROFILE/PUBLIC PROJECTS ----------

@app.get("/public/{username}", summary="Get Public Profile", tags=["public"], response_model=UserProfile)
def public_profile(username: str):
    """Get any user's public profile by username."""
    u = DB.get_user_by_username(username)
    if not u:
        raise HTTPException(404, "Profile not found")
    return UserProfile(**u)

@app.get("/public/{username}/projects", summary="List Public Projects", tags=["public"], response_model=ProjectListResponse)
def user_public_projects(username: str):
    """List public projects for a given username."""
    u = DB.get_user_by_username(username)
    if not u:
        raise HTTPException(404, "Profile not found")
    projects = DB.list_projects(user_id=u["id"])
    return ProjectListResponse(projects=projects, total=len(projects))
