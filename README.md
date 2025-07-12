# 🎾 Tennis Match Tracker

A web application to track tennis matches between players, including scores, player profiles, and individual performance statistics with Istanbul timezone support.

## Features

- **Player Management**: Add players with profile photos and track their statistics
- **Home Page**: View all matches with player photos, set scores, and winners
- **Add Match**: Select two players and enter set scores with automatic winner determination
- **Match Details**: Add notes and rate both players' performance on 4 criteria (Backhand, Forehand, Service, Playing Style)
- **Player Statistics**: Track wins, total matches, and win rates for each player
- **3-Hour Edit Window**: Matches can only be edited within 3 hours of creation
- **Photo Upload**: Upload profile photos for players with crop functionality (PNG, JPG, JPEG, GIF supported)
- **Istanbul Timezone**: All times displayed in Istanbul timezone (Europe/Istanbul)
- **Responsive Design**: Works on desktop and mobile devices

## Installation

1. Make sure you have Python 3.7+ installed
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

## Running the Application

### Development
1. Start the Flask development server:
   ```bash
   python app.py
   ```

2. Open your browser and go to `http://localhost:5000`

### Production (Local Testing)
```bash
gunicorn wsgi:application
```

## Usage

### Adding Players
1. Go to "Players" in the navigation
2. Click "Add New Player"
3. Enter player name and optionally upload a profile photo
4. Use the crop tool to adjust profile photos
5. View player statistics including total matches, wins, and win rate

### Adding a Match
1. Click "Add Match" in the navigation (requires at least 2 players)
2. Select Player 1 and Player 2 from dropdowns
3. Enter set scores for each set (e.g., Set 1: 6-3, Set 2: 6-4)
4. The system automatically determines the winner based on sets won

### Rating Players
1. Click "View Details" on any match card
2. Add notes about the match
3. Rate each player's performance on 4 criteria (0-10 scale):
   - Backhand
   - Forehand
   - Service
   - Playing Style
4. The system calculates individual overall ratings for each player

### Editing Restrictions
- Matches can only be edited within 3 hours of creation
- After 3 hours, all data becomes read-only
- Time remaining is displayed on match cards and detail pages

## Database

The application uses SQLite with three main tables:

### Players Table
- `id`: Auto-increment primary key
- `name`: Player name (unique)
- `photo_filename`: Profile photo filename
- `age`, `height`, `weight`: Optional player information
- `bio`: Player biography
- `created_date`: Account creation timestamp

### Matches Table
- `id`: Auto-increment primary key
- `date`: Match creation timestamp (Istanbul timezone)
- `player1_id`, `player2_id`: References to players
- `sets`: Set scores (e.g., "6-3,6-4")
- `winner_id`: Reference to winning player
- `match_note`: Notes about the match

### Player Stats Table
- `id`: Auto-increment primary key
- `match_id`: Reference to match
- `player_id`: Reference to player
- `backhand`, `forehand`, `service`, `style`: Performance ratings (0-10)
- `overall`: Average of all ratings
- `player_note`: Notes about individual player performance

## Deployment

### Render Deployment

1. **Create a Render Account**: Sign up at [render.com](https://render.com)

2. **Connect Your Repository**: 
   - Push your code to GitHub
   - Connect your GitHub repository to Render

3. **Environment Variables** (Set in Render Dashboard):
   ```
   SECRET_KEY=your-very-secure-random-secret-key
   DATABASE_PATH=/opt/render/project/src/tennis_matches.db
   ```

4. **Deploy Settings**:
   - Build Command: `pip install -r requirements.txt`
   - Start Command: `gunicorn wsgi:application`
   - Python Version: 3.11

5. **Persistent Storage**: 
   - Add a persistent disk for database storage
   - Mount path: `/opt/render/project/src`

### Manual Deployment Steps

1. **Prepare Environment Variables**:
   ```bash
   export SECRET_KEY="your-very-secure-secret-key"
   export DATABASE_PATH="/path/to/tennis_matches.db"
   ```

2. **Install Dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

3. **Initialize Database**:
   ```bash
   python -c "from app import init_db; init_db()"
   ```

4. **Start Production Server**:
   ```bash
   gunicorn wsgi:application
   ```

### Files for Deployment

- `requirements.txt`: Python dependencies
- `Procfile`: Process file for deployment platforms
- `wsgi.py`: WSGI entry point
- `render.yaml`: Render-specific configuration
- `.env.example`: Example environment variables
- `.gitignore`: Files to exclude from version control

## Environment Variables

| Variable | Description | Required | Default |
|----------|-------------|----------|---------|
| `SECRET_KEY` | Flask secret key for sessions | Yes | - |
| `DATABASE_PATH` | Path to SQLite database file | No | `tennis_matches.db` |
| `PORT` | Server port | No | `5000` |

## Development

### Project Structure
```
tennismatchtracker/
├── app.py              # Main Flask application
├── wsgi.py             # WSGI entry point
├── requirements.txt    # Python dependencies
├── Procfile           # Process file for deployment
├── render.yaml        # Render configuration
├── templates/         # HTML templates
│   ├── base.html
│   ├── home.html
│   ├── players.html
│   ├── add_player.html
│   ├── edit_player.html
│   ├── add_match.html
│   └── match_detail.html
├── static/            # Static files
│   ├── style.css      # Main stylesheet
│   ├── crop.js        # Image cropping functionality
│   └── uploads/       # User uploaded photos
└── tennis_matches.db  # SQLite database
```

### Key Features Implementation

- **Timezone Handling**: All dates use Istanbul timezone (Europe/Istanbul)
- **Image Processing**: Automatic face detection and cropping for profile photos
- **Time-based Editing**: 3-hour window for match editing with countdown display
- **Responsive Design**: CSS Grid and Flexbox for modern layouts
- **Player Statistics**: Automatic calculation of ratings and win percentages

## Future Enhancements

- Statistical visualizations
- Performance trend graphs
- Export to CSV/PDF
- Match statistics and analytics
- Tournament bracket system
- Email notifications for match results

## License

This project is open source and available under the MIT License.
