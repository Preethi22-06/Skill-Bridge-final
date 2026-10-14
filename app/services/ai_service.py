import json
from typing import List, Dict, Any
from ..core.config import settings

def generate_curriculum(existing_skills: List[str], missing_skills: List[str], target_role: str, weekly_hours: int) -> Dict[str, Any]:
    if not settings.GEMINI_API_KEY:
        modules = []
        for idx, skill in enumerate(missing_skills, 1):
            modules.append({
                "module_id": idx,
                "title": f"Mastering {skill} for {target_role}",
                "description": f"Comprehensive deep dive into {skill} covering industry best practices and practical architectures.",
                "estimated_hours": max(4, int(20 / max(1, len(missing_skills)))),
                "skills_covered": [skill],
                "practical_exercises": [f"Build an end-to-end mini project implementing {skill}."],
                "resources": [
                    {
                        "title": f"Official {skill} Core Documentation & Guide",
                        "provider": "Open Source Community",
                        "url": f"https://www.google.com/search?q={skill}+official+docs",
                        "free": True
                    }
                ],
                "completed": False
            })

        return {
            "title": f"Accelerated Micro-Credential: {target_role}",
            "target_role": target_role,
            "generated_by": "deterministic",
            "estimated_weeks": max(2, len(missing_skills)),
            "modules": modules
        }

    try:
        import urllib.request
        prompt = (
            f"Generate a structured micro-credential roadmap for target role '{target_role}'. "
            f"Existing skills: {existing_skills}. Missing skills: {missing_skills}. "
            f"Weekly hours available: {weekly_hours}. Return strict valid JSON with keys: "
            f"'title', 'modules' (list of objects with 'module_id', 'title', 'description', 'estimated_hours', 'skills_covered', 'practical_exercises', 'resources')."
        )
        url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={settings.GEMINI_API_KEY}"
        headers = {"Content-Type": "application/json"}
        payload = json.dumps({"contents": [{"parts": [{"text": prompt}]}]}).encode("utf-8")
        req = urllib.request.Request(url, data=payload, headers=headers, method="POST")
        with urllib.request.urlopen(req) as resp:
            data = json.loads(resp.read().decode())
            text = data["candidates"][0]["content"]["parts"][0]["text"]
            clean = text.replace("```json", "").replace("```", "").strip()
            res = json.loads(clean)
            res["generated_by"] = "ai"
            return res
    except Exception:
        return generate_curriculum(existing_skills, missing_skills, target_role, weekly_hours)