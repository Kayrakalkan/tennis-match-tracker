# 🎾 Tennis Match Tracker

## Project Name
Tennis Match Tracker

## Purpose
To build a simple web application that allows me to keep track of tennis matches played with my uncle, including the scores and subjective evaluations of each match.

## Target User
Just me — no login or user system required. The app will be used for personal tracking.

## Technologies

- **Backend:** Python (Flask)
- **Frontend:** HTML + CSS (basic forms and layouts)
- **Database:** SQLite (file-based)
- **Deployment Platform:** Render

## Core Features

### Home Page

- Displays a list of all previously added matches.
- Each match card includes:
  - Date of the match
  - Set scores (e.g., `6-3`, `6-4`)
  - Overall result (e.g., `2-0`, `2-1`)
  - Average (overall) score based on player evaluation

### Add New Match

- Only set scores will be entered (e.g., `6-4`, `4-6`, `6-3`)
- The system will automatically calculate the overall match result (`2-0`, `2-1`)
- No additional input is required at this stage

### Match Detail Page

- Notes about the opponent can be added
- The following 4 criteria are rated (0–10 scale):
  - Backhand
  - Forehand
  - Service
  - Playing Style
- An **overall** average score is calculated based on the four ratings
- After **24 hours** from the match creation time, no further edits are allowed

## Data Structure

### Table: `matches`

| Field       | Type     | Description                            |
|-------------|----------|----------------------------------------|
| id          | INTEGER  | Auto-increment ID                      |
| date        | DATETIME | Match creation timestamp               |
| sets        | TEXT     | Set scores (e.g., `6-3,6-4`)           |
| result      | TEXT     | Calculated overall result (`2-0`)      |
| note        | TEXT     | Notes about the match/opponent         |
| backhand    | INTEGER  | 0–10 rating                            |
| forehand    | INTEGER  | 0–10 rating                            |
| service     | INTEGER  | 0–10 rating                            |
| style       | INTEGER  | 0–10 rating                            |
| overall     | FLOAT    | Average score based on ratings         |

## Future Features (Planned)

- Statistical visualizations (e.g., backhand improvement over time)
- Performance trend graphs (Chart.js integration)
- Export to .csv

## Timeline (Estimated)

- [ ] Set up project structure
- [ ] Implement home page with match listing
- [ ] Add match entry form
- [ ] Add match detail page with rating system
- [ ] Enforce 24-hour edit restriction
- [ ] Basic CSS styling
- [ ] Deploy to Render
