from __future__ import annotations

import argparse
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
        "machine learning",
        "ml engineer",
        "mlops",
        "ai engineer",
        "deep learning",
        "nlp engineer",
        "computer vision",
        "applied scientist",
        "llm",
    ],
    "data engineering": [
        "data engineer",
        "analytics engineer",
        "etl engineer",
        "data platform",
        "data warehouse",
        "warehouse engineer",
        "big data",
        "data infrastructure",
    ],
    "software engineering": [
        "backend engineer",
        "back-end engineer",
        "backend developer",
        "back-end developer",
        "software engineer",
        "platform engineer",
        "api engineer",
        "python developer",
        "python engineer",
        "full stack",
        "full-stack",
    ],
}


def clean_text(value) -> str | None:
    if pd.isna(value):
        return None
    text = str(value).replace("\x00", " ").strip()
    if not text:
        return None
    text = " ".join(text.split())
    return text


def normalize_location(value: str | None) -> str | None:
    value = clean_text(value)
    if not value:
        return None
    return value


def normalize_seniority(value: str | None, title: str | None = None) -> str | None:
    parts = [clean_text(value), clean_text(title)]
    text = " ".join([p for p in parts if p]).lower()

    if not text:
        return None

    if any(token in text for token in ["intern", "internship", "working student"]):
        return "Intern"
    if any(token in text for token in ["principal"]):
        return "Principal"
    if any(token in text for token in ["staff"]):
        return "Staff"
    if any(token in text for token in ["lead", "head of"]):
        return "Lead"
    if any(token in text for token in ["senior", "sr. ", " sr ", " sr,"]):
        return "Senior"
    if any(token in text for token in ["junior", "jr. ", " jr ", " jr,"]):
        return "Junior"
    if any(token in text for token in ["mid", "intermediate"]):
        return "Mid"

    return None


def infer_category(title: str | None, description: str | None, skills: str | None = None) -> str:
    text = " ".join(
        [part for part in [clean_text(title), clean_text(description), clean_text(skills)] if part]
    ).lower()

    for category, patterns in ROLE_PATTERNS.items():
        if any(pattern in text for pattern in patterns):
            return category

    return "other"


def normalize_date(series: pd.Series) -> pd.Series:
    parsed = pd.to_datetime(series, errors="coerce", unit="ms", utc=True)
    return parsed.dt.tz_convert(None).dt.date


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


def prepare_dataframe(external_dir: Path, max_rows: int) -> pd.DataFrame:
    postings = load_postings(external_dir)
    job_skills = load_job_skills(external_dir)

    df = postings.merge(job_skills, on="job_id", how="left")

    df["title"] = df["title"].map(clean_text)
    df["company"] = df["company_name"].map(clean_text)
    df["location"] = df["location"].map(normalize_location)

    df["description_base"] = df["description"].map(clean_text)
    df["skills_desc"] = df["skills_desc"].map(clean_text)
    df["skills_text"] = df["skills_text"].map(clean_text)

    df["description"] = (
        df["description_base"].fillna("")
        + "\n\n"
        + df["skills_desc"].fillna("")
        + "\n\n"
        + df["skills_text"].fillna("")
    ).str.strip()
    df["description"] = df["description"].map(clean_text)

    df["url"] = df["job_posting_url"].map(clean_text)
    if "application_url" in df.columns:
        df["url"] = df["url"].fillna(df["application_url"].map(clean_text))

    df["seniority"] = df.apply(
        lambda row: normalize_seniority(row.get("formatted_experience_level"), row.get("title")),
        axis=1,
    )

    df["date_posted"] = normalize_date(df["original_listed_time"])

    df["category"] = df.apply(
        lambda row: infer_category(row["title"], row["description"], row.get("skills_text")),
        axis=1,
    )

    df = df.dropna(subset=["title", "description", "url"]).copy()
    df = df[df["description"].str.len() >= 120].copy()
    df = df.drop_duplicates(subset=["url"]).copy()

    tech_df = df[df["category"] != "other"].copy()

    if len(tech_df) >= min(max_rows, 300):
        df = tech_df

    df = df.sort_values(
        by=["date_posted", "company", "title"],
        ascending=[False, True, True],
        na_position="last",
    ).head(max_rows)

    result = df[TARGET_COLUMNS].reset_index(drop=True)
    return result


def main() -> None:
    parser = argparse.ArgumentParser()
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