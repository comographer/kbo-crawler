# KBO Schedule Crawler

This project crawls KBO regular-season and postseason game data from the official schedule endpoint, then builds separate schedule and per-team workbooks in `data/output`.

## Run

```bash
python src/main.py --year 2026 --months 1-12
```

To create or refresh the fixed 2015-2025 history snapshot, then build and push the combined output with the live 2026 crawl:

```bash
python src/main.py --refresh-history --daily --year 2026 --push
```

For the daily update, crawl only 2026 and merge it with the fixed 2015-2025 snapshot:

```bash
python src/main.py --daily --year 2026 --push
```

The daily command updates both competitions. Postseason data uses KBO series IDs `3,4,5,7` by default and is kept separate from regular-season standings and magic-number calculations.

To create or refresh only the fixed 2015-2025 postseason snapshot:

```bash
python src/main.py --daily --year 2026 --refresh-postseason-history
```

## Scheduled daily update

GitHub Actions runs the daily update every day at 23:55 KST (14:55 UTC):

- Workflow: `.github/workflows/daily-update.yml`
- Schedule: `55 14 * * *`
- Manual run: GitHub repository `Actions` > `Daily KBO update` > `Run workflow`
- Permissions: the workflow uses `contents: write` with the repository `GITHUB_TOKEN`

Before crawling, `--push` fetches the remote branch and fast-forwards when possible. If only generated-data commits have diverged, it merges the remote history before refreshing the data. It stops before crawling when source or configuration changes are uncommitted.

You can also narrow the crawl to a smaller range while testing:

```bash
python src/main.py --year 2026 --months 6
```

## Dashboard

```bash
.venv\Scripts\python.exe -m streamlit run src/dashboard.py
```

For Streamlit Community Cloud, deploy this repository with:

- Branch: `main`
- Main file path: `streamlit_app.py`
- App URL: https://comographer-kbo-crawler-srcdashboard-zm9vgo.streamlit.app/

After the first Cloud deployment, running the crawler with `--push` updates GitHub and triggers Streamlit Cloud to refresh the app from the latest commit.

## Output

- `data/output/kbo_schedule.xlsx` for the combined schedule data
- `data/output/kbo_team_sheets.xlsx` for one sheet per team plus a `Total` sheet
- `data/output/kbo_schedule_history_2015_2025.xlsx` for the fixed 2015-2025 history used by `--daily`
- `data/raw/YYYY/schedule_YYYY_MM.json` for each crawled month
- `data/output/kbo_postseason_schedule.xlsx` for the combined postseason schedule
- `data/output/kbo_postseason_team_sheets.xlsx` for postseason team rows
- `data/output/kbo_postseason_history_2015_2025.xlsx` for the fixed postseason history used by `--daily`
- `data/raw/YYYY/postseason/postseason_YYYY_MM.json` for postseason schedule responses

## Notes

- The crawler uses `https://www.koreabaseball.com/ws/Schedule.asmx/GetScheduleList` behind the schedule page.
- The review scoreboard data comes from `https://www.koreabaseball.com/ws/Schedule.asmx/GetScoreBoardScroll` with `type=3`, `leId=1`, `srId`, `seasonId`, and `gameId`.
- Postseason records preserve KBO series ID, round, round order, series game code, and game number.
- If you want team-specific data, pass `--team-id`.
