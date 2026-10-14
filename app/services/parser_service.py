import io
import re
from pypdf import PdfReader

COMMON_TECH_SKILLS = [
    "Python", "JavaScript", "TypeScript", "React", "Node.js", "SQL", "PostgreSQL",
    "MongoDB", "Docker", "AWS", "Git", "FastAPI", "Tailwind CSS", "GraphQL",
    "Java", "C++", "HTML", "CSS", "Next.js", "Redis", "Linux", "Kubernetes"
]

def extract_skills_from_file(filename: str, content: bytes) -> list[str]:
    extracted_text = ""
    if filename.endswith(".pdf"):
        try:
            reader = PdfReader(io.BytesIO(content))
            for page in reader.pages:
                extracted_text += (page.extract_text() or "") + " "
        except Exception:
            extracted_text = ""
    else:
        try:
            extracted_text = content.decode("utf-8", errors="ignore")
        except Exception:
            extracted_text = ""

    extracted_skills = set()
    for skill in COMMON_TECH_SKILLS:
        pattern = r"\b" + re.escape(skill) + r"\b"
        if re.search(pattern, extracted_text, re.IGNORECASE):
            extracted_skills.add(skill)

    return sorted(list(extracted_skills))