# KBO Schedule Crawler

This project crawls KBO season game data from the official schedule endpoint, then builds a combined schedule workbook and a per-team workbook in `data/output`.

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

## Notes

- The crawler uses `https://www.koreabaseball.com/ws/Schedule.asmx/GetScheduleList` behind the schedule page.
- The review scoreboard data comes from `https://www.koreabaseball.com/ws/Schedule.asmx/GetScoreBoardScroll` with `type=3`, `leId=1`, `srId`, `seasonId`, and `gameId`.
- If you want team-specific data, pass `--team-id`.
