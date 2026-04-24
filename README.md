# Free Job Application Agent (No Subscription)

This project gives you a **free, self-hosted daily job agent** that:

1. Pulls fresh remote jobs from a public API.
2. Filters jobs using your preferred role, keywords, and location.
3. Scores each job against your profile.
4. Generates a tailored cover letter draft for each matched job.
5. Tracks what has already been processed so you do not duplicate work.
6. Exports a daily CSV report you can review or use to apply quickly.

> Important: fully automatic submission across every job board is usually blocked by logins, captchas, anti-bot checks, and ToS restrictions. This tool focuses on everything **up to** submission and gives you a high-speed daily pipeline.

---

## Quick start

```bash
cp profile.example.json profile.json
python3 agent.py --profile profile.json --limit 40
```

A report will be written to `output/`.

---

## Daily automation (free)

Use cron to run every morning at 8:00 AM:

```bash
crontab -e
```

Add:

```cron
0 8 * * * cd /workspace/kumar && /usr/bin/python3 agent.py --profile profile.json --limit 50 >> logs/daily.log 2>&1
```

---

## Profile configuration

Edit `profile.json`:

- `target_roles`: role titles you want.
- `must_have_keywords`: required keywords.
- `nice_to_have_keywords`: optional bonus keywords.
- `blocked_keywords`: jobs to skip.
- `locations`: preferred locations.
- `resume_summary`: reused in tailored cover letter generation.

---

## Outputs

- `output/jobs_YYYYMMDD.csv`: scored jobs with apply links.
- `data/seen_jobs.json`: job IDs already processed.

---

## Notes

- This starter currently uses Remotive's public remote jobs API.
- If outbound API access is blocked, it automatically falls back to `sample_jobs.json` for local testing.
- You can extend the same structure with LinkedIn, Greenhouse, Lever, Workday, etc.
- For safety and account health, keep human review before submitting.
