from pydantic import BaseModel, EmailStr, Field
from typing import List, Optional
from datetime import datetime

# PUBLIC_INTERFACE
class UserAuth(BaseModel):
    """Schema for user authentication payload (signup/login)."""
    email: EmailStr
    password: str = Field(..., min_length=6, description="User password (min 6 chars)")

# PUBLIC_INTERFACE
class UserProfileBase(BaseModel):
    """Base schema for user profile common fields."""
    name: str = Field(..., description="Full name of the user")
    username: str = Field(..., description="Unique username (handle)")
    bio: Optional[str] = Field(None, description="Short user bio/about")
    avatar_url: Optional[str] = Field(None, description="User profile avatar/image URL")

# PUBLIC_INTERFACE
class UserProfileCreate(UserProfileBase):
    """Schema for creating a user profile."""

# PUBLIC_INTERFACE
class UserProfile(UserProfileBase):
    """Schema for returning user profile data."""
    id: int
    email: EmailStr

    class Config:
        orm_mode = True

# PUBLIC_INTERFACE
class UserProfileUpdate(BaseModel):
    """Schema for editing a user profile."""
    name: Optional[str]
    bio: Optional[str]
    avatar_url: Optional[str]

# PUBLIC_INTERFACE
class Tag(BaseModel):
    """Schema for project tags."""
    id: int
    name: str

    class Config:
        orm_mode = True

# PUBLIC_INTERFACE
class ProjectBase(BaseModel):
    """Base schema for project common fields."""
    title: str = Field(..., description="Project title")
    description: str = Field(..., description="Project description")
    tags: List[int] = Field(default_factory=list, description="List of tag IDs")
    repo_url: Optional[str] = Field(None, description="URL to code repository")
    live_demo_url: Optional[str] = Field(None, description="URL for live demo (if any)")
    thumbnail_url: Optional[str] = Field(None, description="Thumbnail or cover image")

# PUBLIC_INTERFACE
class ProjectCreate(ProjectBase):
    """Schema for uploading/creating a new project."""

# PUBLIC_INTERFACE
class Project(ProjectBase):
    """Schema for returning project data."""
    id: int
    user_id: int
    created_at: datetime
    likes: int
    tags: List[Tag] = []

    class Config:
        orm_mode = True

# PUBLIC_INTERFACE
class ProjectLike(BaseModel):
    """Schema for like/unlike action."""
    project_id: int

# PUBLIC_INTERFACE
class TagFilterResponse(BaseModel):
    """Schema for tag filter results."""
    tags: List[Tag]

# PUBLIC_INTERFACE
class ProjectListResponse(BaseModel):
    """Schema for paginated project list."""
    projects: List[Project]
    total: int

# PUBLIC_INTERFACE
class AuthResponse(BaseModel):
    """Schema returned after authentication."""
    access_token: str
    token_type: str = "bearer"
    user: UserProfile

