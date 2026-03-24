import re
from pipeline.skill_dict import SKILL_PATTERNS


def extract_skills(text: str) -> list[str]:
    if not text:
        return []

    text = text.lower()
    found = []

    for skill, patterns in SKILL_PATTERNS.items():
        for pattern in patterns:
            if re.search(pattern, text):
                found.append(skill)
                break

    return sorted(set(found))