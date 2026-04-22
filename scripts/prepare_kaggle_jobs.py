from __future__ import annotations

import argparse
import re
from pathlib import Path

import pandas as pd


BASE_DIR = Path(__file__).resolve().parent.parent
DEFAULT_EXTERNAL_DIR = BASE_DIR / "data" / "external"
DEFAULT_OUTPUT_PATH = BASE_DIR / "data" / "raw" / "jobs.csv"

TARGET_COLUMNS = [
    "title",
    "company",
    "location",
    "category",
    "seniority",
    "description",
    "date_posted",
    "url",
]

ROLE_PATTERNS = {
    "machine learning": [
        "machine learning engineer",
        "ml engineer",
        "mlops engineer",
        "ai engineer",
        "applied scientist",
        "research scientist",
        "data scientist",
        "computer vision engineer",
        "nlp engineer",
        "llm engineer",
        "artificial intelligence engineer",
        "deep learning engineer",
        "ml platform engineer",
        "ai/ml engineer",
    ],
    "data engineering": [
        "data engineer",
        "analytics engineer",
        "etl engineer",
        "etl developer",
        "data platform engineer",
        "data warehouse engineer",
        "warehouse engineer",
        "big data engineer",
        "data infrastructure engineer",
        "data pipeline engineer",
        "data integration engineer",
        "bi engineer",
        "business intelligence engineer",
    ],
    "software engineering": [
        "software engineer",
        "backend engineer",
        "back-end engineer",
        "backend developer",
        "back-end developer",
        "platform engineer",
        "api engineer",
        "python engineer",
        "python developer",
        "full stack engineer",
        "full-stack engineer",
        "full stack developer",
        "full-stack developer",
        "web developer",
        "application developer",
        "devops engineer",
        "dev ops engineer",
        "site reliability engineer",
        "sre",
        "cloud engineer",
        "infrastructure engineer",
        "systems engineer",
        "solutions engineer",
        "integration engineer",
        "embedded engineer",
        "firmware engineer",
    ],
}

# Keywords used both for tech-title detection and fallback category inference
TECH_TITLE_KEYWORDS = [
    "engineer",
    "developer",
    "scientist",
    "machine learning",
    "ml ",
    "mlops",
    "data ",
    "analytics",
    "backend",
    "back-end",
    "software",
    "platform",
    "api",
    "python",
    "devops",
    "cloud",
    "infrastructure",
    "sre",
    "site reliability",
]

SENIORITY_RULES: list[tuple[list[str], str]] = [
    (["intern", "internship", "working student", "trainee"], "Intern"),
    (["principal"], "Principal"),
    (["staff engineer", r"\bstaff\b"], "Staff"),
    (["lead", "head of", "tech lead", "team lead"], "Lead"),
    (["senior", r"\bsr\b", r"\bsr\."], "Senior"),
    (["junior", r"\bjr\b", r"\bjr\."], "Junior"),
    (["mid-level", "mid level", "intermediate"], "Mid"),
]

def clean_text(value) -> str | None:
    if pd.isna(value):
        return None
    text = str(value).replace("\x00", " ").strip()
    if not text:
        return None
    return " ".join(text.split())


def normalize_location(value) -> str | None:
    return clean_text(value)


def normalize_date(series: pd.Series) -> pd.Series:
    """
    Parse timestamps robustly: try ms-epoch first, fall back to ISO strings.
    Returns a Series of datetime.date objects (tz-naive).
    """
    # Try millisecond epoch
    parsed = pd.to_datetime(series, errors="coerce", unit="ms", utc=True)
    # For rows that failed (NaT), retry as ISO/general string
    mask_nat = parsed.isna()
    if mask_nat.any():
        fallback = pd.to_datetime(series[mask_nat], errors="coerce", utc=True)
        parsed[mask_nat] = fallback
    return parsed.dt.tz_convert(None).dt.date


def normalize_seniority(
    value: str | None,
    title: str | None = None,
    description: str | None = None,
) -> str | None:
    parts = [clean_text(value), clean_text(title)]
    text = " ".join([p for p in parts if p]).lower()

    if not text and description:
        text = (clean_text(description) or "")[:400].lower()

    if not text:
        return None

    for tokens, label in SENIORITY_RULES:
        for token in tokens:
            if re.search(token, text):
                return label

    return None


# ---------------------------------------------------------------------------
# Category / tech-title helpers
# ---------------------------------------------------------------------------

def infer_category_from_title(title: str | None) -> str:
    title_text = (clean_text(title) or "").lower()
    for category, patterns in ROLE_PATTERNS.items():
        if any(pattern in title_text for pattern in patterns):
            return category
    return "other"


def is_tech_like_title(title: str | None) -> bool:
    title_text = (clean_text(title) or "").lower()
    return any(keyword in title_text for keyword in TECH_TITLE_KEYWORDS)


def read_csv_robust(path: Path, usecols: list[str] | None = None) -> pd.DataFrame:
    try:
        return pd.read_csv(path, usecols=usecols, low_memory=False)
    except Exception:
        return pd.read_csv(
            path,
            usecols=usecols,
            engine="python",
            on_bad_lines="skip",
            encoding_errors="replace",
        )


def load_postings(external_dir: Path) -> pd.DataFrame:
    postings_path = external_dir / "postings.csv"
    if not postings_path.exists():
        raise FileNotFoundError(f"Missing file: {postings_path}")

    usecols = [
        "job_id",
        "company_name",
        "title",
        "description",
        "location",
        "formatted_experience_level",
        "original_listed_time",
        "job_posting_url",
        "application_url",
        "skills_desc",
        "formatted_work_type",
        "work_type",
        "remote_allowed",
    ]
    df = read_csv_robust(postings_path, usecols=usecols)

    for col in usecols:
        if col not in df.columns:
            df[col] = None

    # Drop duplicate job_ids before any merge to prevent row explosion
    df = df.drop_duplicates(subset=["job_id"]).copy()

    return df


def load_job_skills(external_dir: Path) -> pd.DataFrame:
    job_skills_path = external_dir / "jobs" / "job_skills.csv"
    if not job_skills_path.exists():
        return pd.DataFrame(columns=["job_id", "skills_text"])

    usecols = ["job_id", "skill_abr"]
    skills = read_csv_robust(job_skills_path, usecols=usecols)

    if "job_id" not in skills.columns or "skill_abr" not in skills.columns:
        return pd.DataFrame(columns=["job_id", "skills_text"])

    skills["skill_abr"] = skills["skill_abr"].map(clean_text)
    skills = skills.dropna(subset=["job_id", "skill_abr"]).copy()

    grouped = (
        skills.groupby("job_id")["skill_abr"]
        .apply(lambda s: ", ".join(sorted(set(s))))
        .reset_index(name="skills_text")
    )
    return grouped


# ---------------------------------------------------------------------------
# Core pipeline
# ---------------------------------------------------------------------------

def _build_description(row: pd.Series) -> str | None:
    """Combine description, skills_desc, and skills_text into one field."""
    parts = []
    for col in ["description_base", "skills_desc", "skills_text"]:
        val = row.get(col)
        if isinstance(val, str) and val:
            parts.append(val)
    combined = "\n\n".join(parts).strip()
    return clean_text(combined) if combined else None


def _sort_bucket(df: pd.DataFrame) -> pd.DataFrame:
    """Sort a priority bucket: newest first, then company/title alphabetically."""
    return df.sort_values(
        by=["date_posted", "company", "title"],
        ascending=[False, True, True],
        na_position="last",
    ).copy()


def prepare_dataframe(external_dir: Path, max_rows: int) -> pd.DataFrame:
    postings = load_postings(external_dir)
    job_skills = load_job_skills(external_dir)

    df = postings.merge(job_skills, on="job_id", how="left")

    # --- Field normalisation ---
    df["title"] = df["title"].map(clean_text)
    df["company"] = df["company_name"].map(clean_text)
    df["location"] = df["location"].map(normalize_location)

    df["description_base"] = df["description"].map(clean_text)
    df["skills_desc"] = df["skills_desc"].map(clean_text)
    df["skills_text"] = df["skills_text"].map(clean_text)

    df["description"] = df.apply(_build_description, axis=1)

    df["url"] = df["job_posting_url"].map(clean_text)
    if "application_url" in df.columns:
        df["url"] = df["url"].fillna(df["application_url"].map(clean_text))

    df["date_posted"] = normalize_date(df["original_listed_time"])

    df["seniority"] = df.apply(
        lambda row: normalize_seniority(
            row.get("formatted_experience_level"),
            row.get("title"),
            row.get("description"),
        ),
        axis=1,
    )

    df["category"] = df["title"].map(infer_category_from_title)
    df["is_tech_like_title"] = df["title"].map(is_tech_like_title)

    df = df.dropna(subset=["title", "description", "url"]).copy()
    df = df[df["description"].str.len() >= 120].copy()
    df = df.drop_duplicates(subset=["url"]).copy()

    classified_tech_df = _sort_bucket(df[df["category"] != "other"].copy())
    fallback_tech_df = _sort_bucket(
        df[(df["category"] == "other") & df["is_tech_like_title"]].copy()
    )

    # DO NOT include remaining_df — it's all non-tech
    selected = pd.concat(
        [classified_tech_df, fallback_tech_df],
        ignore_index=True,
    ).drop_duplicates(subset=["url"])

    if len(selected) == 0:
        raise RuntimeError(
            "No tech jobs found. Check that postings.csv contains tech roles "
            "and that title patterns cover them."
        )

    selected = _sort_bucket(selected).head(max_rows)
    result = selected[TARGET_COLUMNS].reset_index(drop=True)
    return result


# ---------------------------------------------------------------------------
# CLI entry point
# ---------------------------------------------------------------------------

def main() -> None:
    parser = argparse.ArgumentParser(
        description="Prepare Kaggle LinkedIn job postings for JobScope."
    )
    parser.add_argument("--external-dir", type=str, default=str(DEFAULT_EXTERNAL_DIR))
    parser.add_argument("--output", type=str, default=str(DEFAULT_OUTPUT_PATH))
    parser.add_argument("--max-rows", type=int, default=800)
    args = parser.parse_args()

    external_dir = Path(args.external_dir)
    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    result = prepare_dataframe(external_dir=external_dir, max_rows=args.max_rows)
    result.to_csv(output_path, index=False)

    print(f"output_file={output_path}")
    print(f"rows={len(result)}")
    print("\ncategory_counts")
    print(result["category"].value_counts(dropna=False).to_string())
    print("\nseniority_counts")
    print(result["seniority"].fillna("None").value_counts(dropna=False).head(10).to_string())


if __name__ == "__main__":
    main()