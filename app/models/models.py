from sqlalchemy import Column, Integer, String, ForeignKey, Float, DateTime, JSON
from sqlalchemy.orm import relationship
from datetime import datetime
from ..database import Base

class User(Base):
    __tablename__ = "users"
    __table_args__ = {"extend_existing": True}

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    full_name = Column(String(255), nullable=False)
    role = Column(String(50), default="student")
    created_at = Column(DateTime, default=datetime.utcnow)

    profile = relationship("Profile", back_populates="user", uselist=False)
    skills = relationship("UserSkill", back_populates="user")
    curricula = relationship("Curriculum", back_populates="user")

class Profile(Base):
    __tablename__ = "profiles"
    __table_args__ = {"extend_existing": True}

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), unique=True)
    college = Column(String(255), default="")
    degree = Column(String(255), default="")
    academic_year = Column(String(50), default="")
    career_goal = Column(String(255), default="Full Stack Engineer")
    weekly_hours = Column(Integer, default=10)
    preferred_format = Column(String(100), default="Interactive & Project-Based")

    user = relationship("User", back_populates="profile")

class UserSkill(Base):
    __tablename__ = "user_skills"
    __table_args__ = {"extend_existing": True}

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    name = Column(String(100), nullable=False)
    proficiency = Column(String(50), default="Intermediate")

    user = relationship("User", back_populates="skills")

class JobRole(Base):
    __tablename__ = "job_roles"
    __table_args__ = {"extend_existing": True}

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(255), unique=True, nullable=False)
    industry = Column(String(100), default="Technology")
    required_skills = Column(JSON, default=list)

class MarketSkillDemand(Base):
    __tablename__ = "market_skill_demand"
    __table_args__ = {"extend_existing": True}

    id = Column(Integer, primary_key=True, index=True)
    skill_name = Column(String(100), unique=True, nullable=False)
    demand_score = Column(Float, default=85.0)
    growth_rate = Column(String(20), default="+18% YoY")
    category = Column(String(100), default="Software Engineering")

class Curriculum(Base):
    __tablename__ = "curricula"
    __table_args__ = {"extend_existing": True}

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    title = Column(String(255), nullable=False)
    target_role = Column(String(255), nullable=False)
    match_percentage = Column(Float, default=0.0)
    generated_by = Column(String(50), default="deterministic")
    modules = Column(JSON, default=list)
    created_at = Column(DateTime, default=datetime.utcnow)

    user = relationship("User", back_populates="curricula")