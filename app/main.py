from fastapi import FastAPI, Depends, HTTPException, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from jose import JWTError, jwt
from fastapi.security import OAuth2PasswordBearer

from .database import engine, Base, get_db
from .core.config import settings
from .core.security import get_password_hash, verify_password, create_access_token
from .models.models import User, Profile, UserSkill, JobRole, MarketSkillDemand, Curriculum
from .schemas.schemas import UserRegister, UserLogin, Token, SkillCreate, SkillResponse, SkillGapRequest
from .services.ai_service import generate_curriculum
from .services.parser_service import extract_skills_from_file

Base.metadata.create_all(bind=engine)

app = FastAPI(title="SkillBridge AI API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="api/auth/login")

def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)) -> User:
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        email: str = payload.get("sub")
        if email is None:
            raise HTTPException(status_code=401, detail="Invalid token")
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid authorization credentials")
    
    user = db.query(User).filter(User.email == email).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user

@app.on_event("startup")
def seed_market_data():
    db = next(get_db())
    if not db.query(JobRole).first():
        roles = [
            JobRole(title="Full Stack Engineer", industry="Technology", required_skills=["React", "TypeScript", "Python", "FastAPI", "PostgreSQL", "Docker", "Git"]),
            JobRole(title="Frontend Developer", industry="Technology", required_skills=["React", "TypeScript", "JavaScript", "HTML", "CSS", "Tailwind CSS", "Git"]),
            JobRole(title="Backend Developer", industry="Technology", required_skills=["Python", "FastAPI", "SQL", "PostgreSQL", "Docker", "AWS", "Redis"]),
            JobRole(title="DevOps Engineer", industry="Technology", required_skills=["Docker", "Kubernetes", "AWS", "Linux", "Python", "Git"])
        ]
        db.add_all(roles)

    if not db.query(MarketSkillDemand).first():
        demands = [
            MarketSkillDemand(skill_name="React", demand_score=94.5, growth_rate="+22% YoY"),
            MarketSkillDemand(skill_name="Python", demand_score=97.0, growth_rate="+31% YoY"),
            MarketSkillDemand(skill_name="TypeScript", demand_score=91.0, growth_rate="+28% YoY"),
            MarketSkillDemand(skill_name="Docker", demand_score=88.5, growth_rate="+15% YoY"),
            MarketSkillDemand(skill_name="PostgreSQL", demand_score=86.0, growth_rate="+12% YoY"),
            MarketSkillDemand(skill_name="FastAPI", demand_score=82.0, growth_rate="+38% YoY"),
        ]
        db.add_all(demands)
    db.commit()

@app.get("/api/health")
def health_check():
    return {"status": "healthy", "service": "SkillBridge AI API"}

@app.post("/api/auth/register", response_model=Token)
def register(user_data: UserRegister, db: Session = Depends(get_db)):
    if db.query(User).filter(User.email == user_data.email).first():
        raise HTTPException(status_code=400, detail="Email already registered")
    
    new_user = User(
        email=user_data.email,
        hashed_password=get_password_hash(user_data.password),
        full_name=user_data.full_name
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    profile = Profile(user_id=new_user.id)
    db.add(profile)
    db.commit()

    token = create_access_token(data={"sub": new_user.email})
    return {"access_token": token, "token_type": "bearer", "user": {"id": new_user.id, "email": new_user.email, "full_name": new_user.full_name, "role": new_user.role}}

@app.post("/api/auth/login", response_model=Token)
def login(login_data: UserLogin, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == login_data.email).first()
    if not user or not verify_password(login_data.password, user.hashed_password):
        raise HTTPException(status_code=401, detail="Invalid email or password")
    
    token = create_access_token(data={"sub": user.email})
    return {"access_token": token, "token_type": "bearer", "user": {"id": user.id, "email": user.email, "full_name": user.full_name, "role": user.role}}

@app.get("/api/auth/me")
def get_me(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    profile = db.query(Profile).filter(Profile.user_id == user.id).first()
    skills = db.query(UserSkill).filter(UserSkill.user_id == user.id).all()
    return {
        "id": user.id,
        "email": user.email,
        "full_name": user.full_name,
        "role": user.role,
        "profile": profile,
        "skills": [{"id": s.id, "name": s.name, "proficiency": s.proficiency} for s in skills]
    }

@app.post("/api/skills", response_model=SkillResponse)
def add_skill(skill: SkillCreate, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    existing = db.query(UserSkill).filter(UserSkill.user_id == user.id, UserSkill.name.ilike(skill.name)).first()
    if existing:
        existing.proficiency = skill.proficiency
        db.commit()
        return existing

    new_skill = UserSkill(user_id=user.id, name=skill.name, proficiency=skill.proficiency)
    db.add(new_skill)
    db.commit()
    db.refresh(new_skill)
    return new_skill

@app.delete("/api/skills/{skill_id}")
def delete_skill(skill_id: int, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    skill = db.query(UserSkill).filter(UserSkill.id == skill_id, UserSkill.user_id == user.id).first()
    if not skill:
        raise HTTPException(status_code=404, detail="Skill not found")
    db.delete(skill)
    db.commit()
    return {"message": "Skill deleted successfully"}

@app.post("/api/resume/upload")
async def upload_resume(file: UploadFile = File(...), user: User = Depends(get_current_user)):
    content = await file.read()
    skills = extract_skills_from_file(file.filename, content)
    return {"filename": file.filename, "extracted_skills": skills}

@app.get("/api/market/trends")
def get_market_trends(db: Session = Depends(get_db)):
    trends = db.query(MarketSkillDemand).all()
    roles = db.query(JobRole).all()
    return {
        "skills": [{"name": t.skill_name, "score": t.demand_score, "growth": t.growth_rate} for t in trends],
        "roles": [{"title": r.title, "industry": r.industry, "required_skills": r.required_skills} for r in roles]
    }

@app.post("/api/gap-analysis")
def perform_gap_analysis(req: SkillGapRequest, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    role = db.query(JobRole).filter(JobRole.title == req.target_role).first()
    if not role:
        raise HTTPException(status_code=404, detail="Target job role not found")

    user_skills = [s.name.lower() for s in db.query(UserSkill).filter(UserSkill.user_id == user.id).all()]
    required = role.required_skills

    matched = [s for s in required if s.lower() in user_skills]
    missing = [s for s in required if s.lower() not in user_skills]

    match_pct = round((len(matched) / len(required)) * 100, 1) if required else 0

    return {
        "target_role": req.target_role,
        "match_percentage": match_pct,
        "matched_skills": matched,
        "missing_skills": missing,
        "total_required": len(required)
    }

@app.post("/api/curriculum/generate")
def create_curriculum(req: SkillGapRequest, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    role = db.query(JobRole).filter(JobRole.title == req.target_role).first()
    if not role:
        raise HTTPException(status_code=404, detail="Role not found")

    user_skills = [s.name for s in db.query(UserSkill).filter(UserSkill.user_id == user.id).all()]
    missing = [s for s in role.required_skills if s.lower() not in [u.lower() for u in user_skills]]
    
    profile = db.query(Profile).filter(Profile.user_id == user.id).first()
    hours = profile.weekly_hours if profile else 10

    data = generate_curriculum(user_skills, missing, req.target_role, hours)
    
    match_pct = round(((len(role.required_skills) - len(missing)) / len(role.required_skills)) * 100, 1)
    new_curriculum = Curriculum(
        user_id=user.id,
        title=data.get("title", f"{req.target_role} Curriculum"),
        target_role=req.target_role,
        match_percentage=match_pct,
        generated_by=data.get("generated_by", "deterministic"),
        modules=data.get("modules", [])
    )
    db.add(new_curriculum)
    db.commit()
    db.refresh(new_curriculum)
    return new_curriculum

@app.get("/api/curriculum/latest")
def get_latest_curriculum(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    curr = db.query(Curriculum).filter(Curriculum.user_id == user.id).order_by(Curriculum.id.desc()).first()
    return curr or {}