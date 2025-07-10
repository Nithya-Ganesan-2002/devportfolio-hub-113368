from typing import Dict, List, Optional
from datetime import datetime
from .models import UserProfile, Project, Tag

class InMemoryDB:
    """A naive in-memory 'database' for users, projects, tags, and likes."""

    def __init__(self):
        self.users: Dict[int, dict] = {}
        self.projects: Dict[int, dict] = {}
        self.tags: Dict[int, dict] = {}
        self.likes: Dict[int, set] = {}  # user_id -> set of liked project_ids
        self.user_email_map: Dict[str, int] = {}  # email to id
        self.user_username_map: Dict[str, int] = {}
        self.counter = {"users": 1, "projects": 1, "tags": 1}

        # Seed with demo tags
        for name in ["Python", "React", "Data Science", "AI", "Backend", "Frontend"]:
            self.create_tag(name)

    def create_tag(self, name: str) -> Tag:
        tid = self.counter["tags"]
        tag = {"id": tid, "name": name}
        self.tags[tid] = tag
        self.counter["tags"] += 1
        return Tag(**tag)

    def get_tag_by_id(self, tag_id: int) -> Optional[Tag]:
        tag = self.tags.get(tag_id)
        return Tag(**tag) if tag else None

    def list_tags(self) -> List[Tag]:
        return [Tag(**t) for t in self.tags.values()]

    def add_user(self, data: dict) -> UserProfile:
        uid = self.counter["users"]
        data["id"] = uid
        self.users[uid] = data
        self.user_email_map[data["email"]] = uid
        self.user_username_map[data["username"]] = uid
        self.counter["users"] += 1
        return UserProfile(**data)

    def get_user_by_email(self, email: str) -> Optional[dict]:
        uid = self.user_email_map.get(email)
        return self.users.get(uid)

    def get_user_by_id(self, user_id: int) -> Optional[dict]:
        return self.users.get(user_id)

    def get_user_by_username(self, username: str) -> Optional[dict]:
        uid = self.user_username_map.get(username)
        return self.users.get(uid)

    def update_user(self, user_id: int, data: dict) -> UserProfile:
        user = self.users.get(user_id)
        if not user:
            return None
        user.update({k: v for k, v in data.items() if v is not None})
        return UserProfile(**user)

    def add_project(self, user_id: int, data: dict) -> Project:
        pid = self.counter["projects"]
        tags_objs = [self.get_tag_by_id(tid) for tid in data["tags"] if self.get_tag_by_id(tid)]
        project = {
            "id": pid,
            "user_id": user_id,
            "title": data["title"],
            "description": data["description"],
            "repo_url": data.get("repo_url"),
            "live_demo_url": data.get("live_demo_url"),
            "thumbnail_url": data.get("thumbnail_url"),
            "tags": tags_objs,
            "created_at": datetime.utcnow(),
            "likes": 0
        }
        self.projects[pid] = project
        self.counter["projects"] += 1
        return Project(**project)

    def list_projects(self, tag_ids: Optional[List[int]]=None, user_id: Optional[int]=None) -> List[Project]:
        projects = [
            p for p in self.projects.values()
            if (not tag_ids or any(t.id in tag_ids for t in p["tags"])) and (user_id is None or p["user_id"] == user_id)
        ]
        return [Project(**p) for p in projects]

    def get_project_by_id(self, pid: int) -> Optional[Project]:
        p = self.projects.get(pid)
        return Project(**p) if p else None

    def like_project(self, user_id: int, project_id: int) -> int:
        if user_id not in self.likes:
            self.likes[user_id] = set()
        if project_id not in self.likes[user_id]:
            self.likes[user_id].add(project_id)
            # increment project likes
            self.projects[project_id]["likes"] += 1
        return self.projects[project_id]["likes"]

    def unlike_project(self, user_id: int, project_id: int) -> int:
        if user_id in self.likes and project_id in self.likes[user_id]:
            self.likes[user_id].remove(project_id)
            self.projects[project_id]["likes"] -= 1
        return self.projects[project_id]["likes"]

    def user_liked_projects(self, user_id: int) -> List[int]:
        return list(self.likes.get(user_id, set()))

DB = InMemoryDB()

