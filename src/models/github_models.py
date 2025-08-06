from typing import Optional, Dict, Any, List
from pydantic import BaseModel, Field
from datetime import datetime
from bson import ObjectId

class PyObjectId(ObjectId):
    @classmethod
    def __get_validators__(cls):
        yield cls.validate

    @classmethod
    def validate(cls, v):
        if not ObjectId.is_valid(v):
            raise ValueError("Invalid objectid")
        return ObjectId(v)

    @classmethod
    def __modify_schema__(cls, field_schema):
        field_schema.update(type="string")

class GitHubIntegration(BaseModel):
    id: PyObjectId = Field(default_factory=PyObjectId, alias="_id")
    github_user_id: int
    username: str
    email: Optional[str]
    access_token: str
    integration_status: str = "active"
    connection_timestamp: datetime
    last_sync: Optional[datetime]
    
    class Config:
        allow_population_by_field_name = True
        arbitrary_types_allowed = True
        json_encoders = {ObjectId: str}

class GitHubOrganization(BaseModel):
    id: PyObjectId = Field(default_factory=PyObjectId, alias="_id")
    github_id: int
    login: str
    name: Optional[str]
    description: Optional[str]
    url: str
    avatar_url: Optional[str]
    created_at: datetime
    updated_at: datetime
    user_id: int  # Reference to integrated user
    
    class Config:
        allow_population_by_field_name = True
        arbitrary_types_allowed = True
        json_encoders = {ObjectId: str}

class GitHubRepository(BaseModel):
    id: PyObjectId = Field(default_factory=PyObjectId, alias="_id")
    github_id: int
    name: str
    full_name: str
    description: Optional[str]
    private: bool
    owner_login: str
    owner_id: int
    html_url: str
    clone_url: str
    language: Optional[str]
    stargazers_count: int
    watchers_count: int
    forks_count: int
    open_issues_count: int
    default_branch: str
    created_at: datetime
    updated_at: datetime
    pushed_at: Optional[datetime]
    user_id: int
    
    class Config:
        allow_population_by_field_name = True
        arbitrary_types_allowed = True
        json_encoders = {ObjectId: str}

class GitHubCommit(BaseModel):
    id: PyObjectId = Field(default_factory=PyObjectId, alias="_id")
    sha: str
    message: str
    author_name: Optional[str]
    author_email: Optional[str]
    author_date: datetime
    committer_name: Optional[str]
    committer_email: Optional[str]
    committer_date: datetime
    html_url: str
    repository_id: int
    repository_name: str
    additions: Optional[int]
    deletions: Optional[int]
    total_changes: Optional[int]
    user_id: int
    
    class Config:
        allow_population_by_field_name = True
        arbitrary_types_allowed = True
        json_encoders = {ObjectId: str}

class GitHubPullRequest(BaseModel):
    id: PyObjectId = Field(default_factory=PyObjectId, alias="_id")
    github_id: int
    number: int
    title: str
    body: Optional[str]
    state: str
    user_login: str
    user_id: int
    assignee_login: Optional[str]
    assignee_id: Optional[int]
    html_url: str
    created_at: datetime
    updated_at: datetime
    closed_at: Optional[datetime]
    merged_at: Optional[datetime]
    head_ref: str
    base_ref: str
    repository_id: int
    repository_name: str
    integration_user_id: int
    
    class Config:
        allow_population_by_field_name = True
        arbitrary_types_allowed = True
        json_encoders = {ObjectId: str}

class GitHubIssue(BaseModel):
    id: PyObjectId = Field(default_factory=PyObjectId, alias="_id")
    github_id: int
    number: int
    title: str
    body: Optional[str]
    state: str
    user_login: str
    user_id: int
    assignee_login: Optional[str]
    assignee_id: Optional[int]
    labels: List[str] = []
    html_url: str
    created_at: datetime
    updated_at: datetime
    closed_at: Optional[datetime]
    repository_id: int
    repository_name: str
    integration_user_id: int
    
    class Config:
        allow_population_by_field_name = True
        arbitrary_types_allowed = True
        json_encoders = {ObjectId: str}

class GitHubChangelog(BaseModel):
    id: PyObjectId = Field(default_factory=PyObjectId, alias="_id")
    github_id: int
    event: str
    actor_login: str
    actor_id: int
    created_at: datetime
    issue_id: int
    issue_number: int
    repository_id: int
    repository_name: str
    integration_user_id: int
    
    class Config:
        allow_population_by_field_name = True
        arbitrary_types_allowed = True
        json_encoders = {ObjectId: str}

class GitHubUser(BaseModel):
    id: PyObjectId = Field(default_factory=PyObjectId, alias="_id")
    github_id: int
    login: str
    name: Optional[str]
    email: Optional[str]
    bio: Optional[str]
    avatar_url: Optional[str]
    html_url: str
    company: Optional[str]
    location: Optional[str]
    created_at: datetime
    updated_at: datetime
    public_repos: int
    public_gists: int
    followers: int
    following: int
    integration_user_id: int
    
    class Config:
        allow_population_by_field_name = True
        arbitrary_types_allowed = True
        json_encoders = {ObjectId: str}