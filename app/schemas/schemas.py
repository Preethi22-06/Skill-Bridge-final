from pydantic import BaseModel, EmailStr
from typing import List, Optional

class UserRegister(BaseModel):
    email: EmailStr
    password: str
    full_name: str

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class Token(BaseModel):
    access_token: str
    token_type: str
    user: dict

class SkillCreate(BaseModel):
    name: str
    proficiency: str

class SkillResponse(BaseModel):
    id: int
    name: str
    proficiency: str
    class Config:
        from_attributes = True

class ProfileUpdate(BaseModel):
    college: Optional[str] = ""
    degree: Optional[str] = ""
    academic_year: Optional[str] = ""
    career_goal: Optional[str] = "Full Stack Engineer"
    weekly_hours: Optional[int] = 10
    preferred_format: Optional[str] = "Interactive & Project-Based"

class SkillGapRequest(BaseModel):
    target_role: str