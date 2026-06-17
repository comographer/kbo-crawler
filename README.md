# KBO Schedule Crawler

This project crawls KBO 2026 season game data from the official schedule endpoint, then builds a season workbook and a per-team workbook in `data/output`.

## Run

```bash
python src/main.py --year 2026 --months 1-12
```

To commit the regenerated data files and push them to GitHub after a successful crawl:

```bash
python src/main.py --year 2026 --months 1-12 --push
```

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

After the first Cloud deployment, running the crawler with `--push` updates GitHub and triggers Streamlit Cloud to refresh the app from the latest commit.

## Output

- `data/output/kbo_schedule_2026.xlsx` for the season-level schedule data
- `data/output/kbo_team_sheets_2026.xlsx` for one sheet per team
- `data/raw/2026/schedule_2026_MM.json` for each crawled month

## Notes

- The crawler uses `https://www.koreabaseball.com/ws/Schedule.asmx/GetScheduleList` behind the schedule page.
- The review scoreboard data comes from `https://www.koreabaseball.com/ws/Schedule.asmx/GetScoreBoardScroll` with `type=3`, `leId=1`, `srId`, `seasonId`, and `gameId`.
- If you want team-specific data, pass `--team-id`.
