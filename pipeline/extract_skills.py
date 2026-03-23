from pipeline.skill_dict import SKILL_KEYWORDS


def extract_skills(text: str) -> list[str]:
    if not text:
        return []

    found = []

    for skill, keywords in SKILL_KEYWORDS.items():
        for keyword in keywords:
            if keyword in text:
                found.append(skill)
                break

    return sorted(set(found))