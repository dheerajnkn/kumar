from __future__ import annotations

import argparse
import csv
import datetime as dt
import json
from pathlib import Path
from typing import Any
from urllib.request import Request, urlopen
from urllib.error import URLError


REMOTIVE_API = "https://remotive.com/api/remote-jobs"
SEEN_PATH = Path("data/seen_jobs.json")
OUTPUT_DIR = Path("output")


def load_profile(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def load_seen_ids() -> set[str]:
    if not SEEN_PATH.exists():
        return set()
    with SEEN_PATH.open("r", encoding="utf-8") as f:
        data = json.load(f)
    return set(data)


def save_seen_ids(seen_ids: set[str]) -> None:
    SEEN_PATH.parent.mkdir(parents=True, exist_ok=True)
    with SEEN_PATH.open("w", encoding="utf-8") as f:
        json.dump(sorted(seen_ids), f, indent=2)


def normalize(s: str) -> str:
    return (s or "").strip().lower()


def fetch_jobs(limit: int) -> list[dict[str, Any]]:
    req = Request(REMOTIVE_API, headers={"User-Agent": "job-agent/1.0"})
    try:
        with urlopen(req, timeout=20) as response:
            payload = json.loads(response.read().decode("utf-8"))
    except URLError:
        with Path("sample_jobs.json").open("r", encoding="utf-8") as fallback:
            payload = json.load(fallback)
    jobs = payload.get("jobs", [])
    return jobs[:limit]


def score_job(job: dict[str, Any], profile: dict[str, Any]) -> int:
    title = normalize(job.get("title", ""))
    company = normalize(job.get("company_name", ""))
    category = normalize(job.get("category", ""))
    location = normalize(job.get("candidate_required_location", ""))
    description = normalize(job.get("description", ""))

    text = " ".join([title, company, category, location, description])

    for blocked in profile.get("blocked_keywords", []):
        if normalize(blocked) in text:
            return -999

    score = 0

    for role in profile.get("target_roles", []):
        if normalize(role) in title:
            score += 25

    for kw in profile.get("must_have_keywords", []):
        if normalize(kw) in text:
            score += 15
        else:
            score -= 20

    for kw in profile.get("nice_to_have_keywords", []):
        if normalize(kw) in text:
            score += 5

    for loc in profile.get("locations", []):
        if normalize(loc) in location:
            score += 10

    return score


def generate_cover_letter(job: dict[str, Any], profile: dict[str, Any]) -> str:
    return (
        f"Hello {job.get('company_name', 'Hiring Team')},\n\n"
        f"I am excited to apply for the {job.get('title', 'role')} position. "
        f"My background aligns well with your needs: {profile.get('resume_summary', '')}\n\n"
        "I would love to discuss how I can contribute from day one.\n\n"
        "Thank you for your consideration."
    )


def pick_jobs(jobs: list[dict[str, Any]], profile: dict[str, Any], seen_ids: set[str]) -> list[dict[str, Any]]:
    selected: list[dict[str, Any]] = []
    for job in jobs:
        job_id = str(job.get("id"))
        if job_id in seen_ids:
            continue

        score = score_job(job, profile)
        if score < 0:
            continue

        selected.append(
            {
                "id": job_id,
                "date": job.get("publication_date", ""),
                "company": job.get("company_name", ""),
                "title": job.get("title", ""),
                "location": job.get("candidate_required_location", ""),
                "salary": job.get("salary", ""),
                "url": job.get("url", ""),
                "score": score,
                "cover_letter": generate_cover_letter(job, profile),
            }
        )
    return sorted(selected, key=lambda j: j["score"], reverse=True)


def write_csv(rows: list[dict[str, Any]]) -> Path:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    stamp = dt.datetime.utcnow().strftime("%Y%m%d")
    output_path = OUTPUT_DIR / f"jobs_{stamp}.csv"

    with output_path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=[
                "id",
                "date",
                "company",
                "title",
                "location",
                "salary",
                "url",
                "score",
                "cover_letter",
            ],
        )
        writer.writeheader()
        writer.writerows(rows)

    return output_path


def run(profile_path: Path, limit: int, min_score: int) -> Path:
    profile = load_profile(profile_path)
    seen_ids = load_seen_ids()

    jobs = fetch_jobs(limit=limit)
    selected = pick_jobs(jobs, profile, seen_ids)
    selected = [row for row in selected if int(row["score"]) >= min_score]

    for row in selected:
        seen_ids.add(row["id"])

    out = write_csv(selected)
    save_seen_ids(seen_ids)
    return out


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Daily free job application agent")
    parser.add_argument("--profile", type=Path, required=True, help="Path to profile JSON")
    parser.add_argument("--limit", type=int, default=60, help="Max API jobs to inspect")
    parser.add_argument("--min-score", type=int, default=20, help="Minimum score to include")
    return parser.parse_args()


if __name__ == "__main__":
    args = parse_args()
    output = run(profile_path=args.profile, limit=args.limit, min_score=args.min_score)
    print(f"Wrote: {output}")
