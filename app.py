from flask import Flask, render_template, request, redirect, url_for, flash, jsonify
import sqlite3
from datetime import datetime, timedelta
import os
from werkzeug.utils import secure_filename
from PIL import Image
import cv2
import numpy as np
import pytz
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'your-secret-key-here')  # Use environment variable in production
app.config['UPLOAD_FOLDER'] = 'static/uploads'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size

# Ensure upload directory exists
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

# Custom template filter for date formatting
@app.template_filter('format_datetime')
def format_datetime(value):
    """Format datetime to show clean date and time without microseconds and timezone"""
    if isinstance(value, str):
        try:
            # Parse the datetime string
            dt = datetime.fromisoformat(value.replace('Z', '+00:00'))
        except:
            return value
    else:
        dt = value
    
    # Convert to Istanbul timezone for display
    istanbul_tz = pytz.timezone('Europe/Istanbul')
    if dt.tzinfo is None:
        dt = istanbul_tz.localize(dt)
    else:
        dt = dt.astimezone(istanbul_tz)
    
    # Format without microseconds and timezone info
    return dt.strftime('%Y-%m-%d %H:%M:%S')

@app.template_filter('format_date')
def format_date(value):
    """Format datetime to show only the date"""
    if isinstance(value, str):
        try:
            # Parse the datetime string
            dt = datetime.fromisoformat(value.replace('Z', '+00:00'))
        except:
            return value
    else:
        dt = value
    
    # Convert to Istanbul timezone for display
    istanbul_tz = pytz.timezone('Europe/Istanbul')
    if dt.tzinfo is None:
        dt = istanbul_tz.localize(dt)
    else:
        dt = dt.astimezone(istanbul_tz)
    
    # Format to show only date
    return dt.strftime('%Y-%m-%d')

# Database configuration
DATABASE_PATH = os.environ.get('DATABASE_PATH', 'tennis_matches.db')

# Database initialization
def init_db():
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()
    
    # Players table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS players (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL UNIQUE,
            photo_filename TEXT DEFAULT NULL,
            age INTEGER DEFAULT NULL,
            height INTEGER DEFAULT NULL,
            weight INTEGER DEFAULT NULL,
            bio TEXT DEFAULT '',
            created_date DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Matches table (updated)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS matches (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            date DATETIME DEFAULT CURRENT_TIMESTAMP,
            player1_id INTEGER NOT NULL,
            player2_id INTEGER NOT NULL,
            sets TEXT NOT NULL,
            winner_id INTEGER,
            match_note TEXT DEFAULT '',
            FOREIGN KEY (player1_id) REFERENCES players (id),
            FOREIGN KEY (player2_id) REFERENCES players (id),
            FOREIGN KEY (winner_id) REFERENCES players (id)
        )
    ''')
    
    # Player statistics table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS player_stats (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            match_id INTEGER NOT NULL,
            player_id INTEGER NOT NULL,
            backhand INTEGER DEFAULT NULL,
            forehand INTEGER DEFAULT NULL,
            service INTEGER DEFAULT NULL,
            style INTEGER DEFAULT NULL,
            overall FLOAT DEFAULT NULL,
            player_note TEXT DEFAULT '',
            FOREIGN KEY (match_id) REFERENCES matches (id),
            FOREIGN KEY (player_id) REFERENCES players (id)
        )
    ''')
    
    conn.commit()
    conn.close()

def get_db_connection():
    conn = sqlite3.connect(DATABASE_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def allowed_file(filename):
    ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def crop_and_resize_image(image_path, crop_data=None, size=(200, 200)):
    """Crop image to specified area and resize"""
    try:
        with Image.open(image_path) as img:
            # Convert to RGB if necessary
            if img.mode in ('RGBA', 'P'):
                img = img.convert('RGB')
            
            # If crop data is provided, use it
            if crop_data:
                x = int(crop_data['x'])
                y = int(crop_data['y'])
                width = int(crop_data['width'])
                height = int(crop_data['height'])
                
                # Crop to specified area
                img_cropped = img.crop((x, y, x + width, y + height))
            else:
                # Default center crop to square
                width, height = img.size
                if width > height:
                    left = (width - height) // 2
                    top = 0
                    right = left + height
                    bottom = height
                else:
                    left = 0
                    top = (height - width) // 2
                    right = width
                    bottom = top + width
                
                img_cropped = img.crop((left, top, right, bottom))
            
            # Resize to target size
            img_resized = img_cropped.resize(size, Image.Resampling.LANCZOS)
            
            # Save the processed image
            img_resized.save(image_path, 'JPEG', quality=85)
            return True
    except Exception as e:
        print(f"Error processing image: {e}")
        return False

def detect_faces(image_path):
    """Detect faces in image for cropping suggestions"""
    try:
        # Load the image
        img = cv2.imread(image_path)
        if img is None:
            return []
        
        # Convert to RGB
        rgb_img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        
        # Load face cascade
        face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
        
        # Convert to grayscale for face detection
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        
        # Detect faces
        faces = face_cascade.detectMultiScale(gray, 1.1, 4)
        
        face_suggestions = []
        for (x, y, w, h) in faces:
            # Add some padding around the face
            padding = int(max(w, h) * 0.3)
            x = max(0, x - padding)
            y = max(0, y - padding)
            w = min(img.shape[1] - x, w + 2 * padding)
            h = min(img.shape[0] - y, h + 2 * padding)
            
            # Make it square
            size = max(w, h)
            x = max(0, x - (size - w) // 2)
            y = max(0, y - (size - h) // 2)
            
            face_suggestions.append({
                'x': x,
                'y': y,
                'width': min(size, img.shape[1] - x),
                'height': min(size, img.shape[0] - y)
            })
        
        return face_suggestions
    except Exception as e:
        print(f"Error detecting faces: {e}")
        return []

def parse_sets_input(sets_data):
    """Parse sets input from form data"""
    sets = []
    set_num = 1
    
    while f'set{set_num}_p1' in sets_data and f'set{set_num}_p2' in sets_data:
        p1_score = sets_data.get(f'set{set_num}_p1', '').strip()
        p2_score = sets_data.get(f'set{set_num}_p2', '').strip()
        
        if p1_score and p2_score:
            try:
                p1_int = int(p1_score)
                p2_int = int(p2_score)
                sets.append(f"{p1_int}-{p2_int}")
            except ValueError:
                continue
        
        set_num += 1
    
    return ','.join(sets) if sets else None

def calculate_match_result(sets, player1_name, player2_name):
    """Calculate match result from set scores"""
    sets_list = sets.split(',')
    player1_sets = 0
    player2_sets = 0
    
    for set_score in sets_list:
        p1_score, p2_score = map(int, set_score.split('-'))
        if p1_score > p2_score:
            player1_sets += 1
        else:
            player2_sets += 1
    
    return {
        'player1_sets': player1_sets,
        'player2_sets': player2_sets,
        'result': f"{player1_sets}-{player2_sets}",
        'winner': player1_name if player1_sets > player2_sets else player2_name
    }

def calculate_match_score(sets_str, player1_id, player2_id, winner_id):
    """Calculate match score from set results"""
    if not sets_str:
        return "0-0"
    
    sets = sets_str.split(',')
    player1_sets = 0
    player2_sets = 0
    
    for set_score in sets:
        set_score = set_score.strip()
        if '-' in set_score:
            try:
                p1_score, p2_score = map(int, set_score.split('-'))
                if p1_score > p2_score:
                    player1_sets += 1
                elif p2_score > p1_score:
                    player2_sets += 1
            except ValueError:
                continue
    
    return f"{player1_sets}-{player2_sets}"

def calculate_overall_rating(backhand, forehand, service, style):
    """Calculate overall average from individual ratings"""
    ratings = [r for r in [backhand, forehand, service, style] if r is not None]
    if ratings:
        return round(sum(ratings) / len(ratings), 1)
    return None

def can_edit_match(match_date):
    """Check if match can still be edited (within 3 hours) using Istanbul time"""
    istanbul_tz = pytz.timezone('Europe/Istanbul')
    
    if isinstance(match_date, str):
        # Handle string dates
        match_datetime = datetime.fromisoformat(match_date.replace('Z', '+00:00'))
        if match_datetime.tzinfo is None:
            match_datetime = istanbul_tz.localize(match_datetime)
        else:
            match_datetime = match_datetime.astimezone(istanbul_tz)
    else:
        # Handle datetime objects
        if match_date.tzinfo is None:
            # Naive datetime - assume it's already in Istanbul time
            match_datetime = istanbul_tz.localize(match_date)
        else:
            # Timezone-aware datetime - convert to Istanbul time
            match_datetime = match_date.astimezone(istanbul_tz)
    
    # Get current Istanbul time
    current_istanbul_time = datetime.now(istanbul_tz)
    time_diff = current_istanbul_time - match_datetime
    return time_diff < timedelta(hours=3)

@app.route('/')
def home():
    conn = get_db_connection()
    matches = conn.execute('''
        SELECT m.*, 
               p1.name as player1_name, p1.photo_filename as player1_photo,
               p2.name as player2_name, p2.photo_filename as player2_photo,
               winner.name as winner_name
        FROM matches m
        JOIN players p1 ON m.player1_id = p1.id
        JOIN players p2 ON m.player2_id = p2.id
        LEFT JOIN players winner ON m.winner_id = winner.id
        ORDER BY m.date DESC
    ''').fetchall()
    
    # Calculate match scores and get overall ratings for each player in matches
    player_overalls = {}
    matches_with_scores = []
    
    for match in matches:
        # Calculate match score
        match_score = calculate_match_score(match['sets'], match['player1_id'], match['player2_id'], match['winner_id'])
        
        # Convert row to dict and add match score
        match_dict = dict(match)
        match_dict['match_score'] = match_score
        
        # Add editable status and time remaining
        match_dict['is_editable'] = can_edit_match(match['date'])
        if match_dict['is_editable']:
            # Calculate time remaining for editing (in minutes for testing) using Istanbul time
            istanbul_tz = pytz.timezone('Europe/Istanbul')
            
            if isinstance(match['date'], str):
                match_datetime = datetime.fromisoformat(match['date'].replace('Z', '+00:00'))
                if match_datetime.tzinfo is None:
                    match_datetime = istanbul_tz.localize(match_datetime)
                else:
                    match_datetime = match_datetime.astimezone(istanbul_tz)
            else:
                if match['date'].tzinfo is None:
                    # Naive datetime - assume it's already in Istanbul time
                    match_datetime = istanbul_tz.localize(match['date'])
                else:
                    # Timezone-aware datetime - convert to Istanbul time
                    match_datetime = match['date'].astimezone(istanbul_tz)
            
            current_istanbul_time = datetime.now(istanbul_tz)
            time_diff = current_istanbul_time - match_datetime
            hours_remaining = 3 - time_diff.total_seconds() / 3600
            match_dict['hours_remaining'] = max(0, hours_remaining)
        else:
            match_dict['hours_remaining'] = 0
            
        matches_with_scores.append(match_dict)
        
        # Get overall ratings
        for player_id in [match['player1_id'], match['player2_id']]:
            if player_id not in player_overalls:
                overall_result = conn.execute('''
                    SELECT overall FROM player_stats 
                    WHERE player_id = ? AND overall IS NOT NULL
                    ORDER BY id DESC LIMIT 1
                ''', (player_id,)).fetchone()
                player_overalls[player_id] = overall_result['overall'] if overall_result else None
    
    conn.close()
    
    return render_template('home.html', matches=matches_with_scores, player_overalls=player_overalls)

@app.route('/players')
def players():
    conn = get_db_connection()
    players = conn.execute('''
        SELECT p.*, 
               COUNT(m.id) as total_matches,
               COUNT(CASE WHEN m.winner_id = p.id THEN 1 END) as wins
        FROM players p
        LEFT JOIN matches m ON (m.player1_id = p.id OR m.player2_id = p.id)
        GROUP BY p.id
        ORDER BY p.name
    ''').fetchall()
    conn.close()
    
    return render_template('players.html', players=players)

@app.route('/add_player', methods=['GET', 'POST'])
def add_player():
    if request.method == 'POST':
        name = request.form['name'].strip()
        age = request.form.get('age')
        height = request.form.get('height')
        weight = request.form.get('weight')
        bio = request.form.get('bio', '').strip()
        
        if not name:
            flash('Player name is required', 'error')
            return render_template('add_player.html')
        
        # Convert numeric fields
        age = int(age) if age and age.isdigit() else None
        height = int(height) if height and height.isdigit() else None
        weight = int(weight) if weight and weight.isdigit() else None
        
        # Handle photo upload
        photo_filename = None
        if 'photo' in request.files:
            file = request.files['photo']
            if file and file.filename and allowed_file(file.filename):
                photo_filename = secure_filename(file.filename)
                # Add timestamp to avoid conflicts
                photo_filename = f"{datetime.now().strftime('%Y%m%d_%H%M%S')}_{photo_filename}"
                file_path = os.path.join(app.config['UPLOAD_FOLDER'], photo_filename)
                file.save(file_path)
                
                # Check for crop data
                crop_data = None
                if request.form.get('crop_data'):
                    import json
                    crop_data = json.loads(request.form.get('crop_data'))
                
                # Crop and resize the image
                if crop_and_resize_image(file_path, crop_data):
                    flash('Photo processed successfully', 'success')
                else:
                    flash('Photo uploaded but processing failed', 'warning')
        
        try:
            # Get current Istanbul time for the player creation
            istanbul_tz = pytz.timezone('Europe/Istanbul')
            current_istanbul_time = datetime.now(istanbul_tz)
            
            conn = get_db_connection()
            conn.execute('''
                INSERT INTO players (name, photo_filename, age, height, weight, bio, created_date)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (name, photo_filename, age, height, weight, bio, current_istanbul_time))
            conn.commit()
            conn.close()
            
            flash('Player added successfully!', 'success')
            return redirect(url_for('players'))
            
        except sqlite3.IntegrityError:
            flash('Player name already exists', 'error')
    
    return render_template('add_player.html')

@app.route('/add_match', methods=['GET', 'POST'])
def add_match():
    conn = get_db_connection()
    players = conn.execute('SELECT * FROM players ORDER BY name').fetchall()
    
    if len(players) < 2:
        flash('You need at least 2 players to create a match. Please add players first.', 'error')
        return redirect(url_for('add_player'))
    
    if request.method == 'POST':
        player1_id = request.form['player1_id']
        player2_id = request.form['player2_id']
        
        if player1_id == player2_id:
            flash('Please select different players', 'error')
            return render_template('add_match.html', players=players)
        
        # Parse sets from individual inputs
        sets = parse_sets_input(request.form)
        
        if not sets:
            flash('Please enter at least one complete set', 'error')
            return render_template('add_match.html', players=players)
        
        # Get player names for result calculation
        player1 = conn.execute('SELECT name FROM players WHERE id = ?', (player1_id,)).fetchone()
        player2 = conn.execute('SELECT name FROM players WHERE id = ?', (player2_id,)).fetchone()
        
        try:
            result = calculate_match_result(sets, player1['name'], player2['name'])
            winner_id = player1_id if result['player1_sets'] > result['player2_sets'] else player2_id
            
            # Get current Istanbul time for the match
            istanbul_tz = pytz.timezone('Europe/Istanbul')
            current_istanbul_time = datetime.now(istanbul_tz)
            
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO matches (date, player1_id, player2_id, sets, winner_id)
                VALUES (?, ?, ?, ?, ?)
            ''', (current_istanbul_time, player1_id, player2_id, sets, winner_id))
            
            match_id = cursor.lastrowid
            conn.commit()
            conn.close()
            
            flash('Match added successfully!', 'success')
            return redirect(url_for('match_detail', match_id=match_id))
            
        except ValueError:
            flash('Invalid set scores', 'error')
    
    conn.close()
    return render_template('add_match.html', players=players)

@app.route('/match/<int:match_id>')
def match_detail(match_id):
    conn = get_db_connection()
    match = conn.execute('''
        SELECT m.*, 
               p1.name as player1_name, p1.photo_filename as player1_photo,
               p2.name as player2_name, p2.photo_filename as player2_photo,
               winner.name as winner_name
        FROM matches m
        JOIN players p1 ON m.player1_id = p1.id
        JOIN players p2 ON m.player2_id = p2.id
        LEFT JOIN players winner ON m.winner_id = winner.id
        WHERE m.id = ?
    ''', (match_id,)).fetchone()
    
    if not match:
        flash('Match not found', 'error')
        return redirect(url_for('home'))
    
    # Get player statistics for this match
    player_stats = conn.execute('''
        SELECT ps.*, p.name as player_name
        FROM player_stats ps
        JOIN players p ON ps.player_id = p.id
        WHERE ps.match_id = ?
    ''', (match_id,)).fetchall()
    
    conn.close()
    
    # Convert to dict for easier template access
    stats_dict = {}
    for stat in player_stats:
        stats_dict[stat['player_id']] = stat
    
    editable = can_edit_match(match['date'])
    
    # Calculate time remaining for editing
    match_dict = dict(match)
    if editable:
        istanbul_tz = pytz.timezone('Europe/Istanbul')
        
        if isinstance(match['date'], str):
            match_datetime = datetime.fromisoformat(match['date'].replace('Z', '+00:00'))
            if match_datetime.tzinfo is None:
                match_datetime = istanbul_tz.localize(match_datetime)
            else:
                match_datetime = match_datetime.astimezone(istanbul_tz)
        else:
            if match['date'].tzinfo is None:
                # Naive datetime - assume it's already in Istanbul time
                match_datetime = istanbul_tz.localize(match['date'])
            else:
                # Timezone-aware datetime - convert to Istanbul time
                match_datetime = match['date'].astimezone(istanbul_tz)
        
        current_istanbul_time = datetime.now(istanbul_tz)
        time_diff = current_istanbul_time - match_datetime
        hours_remaining = 3 - time_diff.total_seconds() / 3600
        match_dict['hours_remaining'] = max(0, hours_remaining)
    else:
        match_dict['hours_remaining'] = 0
    
    return render_template('match_detail.html', match=match_dict, player_stats=stats_dict, editable=editable)

@app.route('/edit_match/<int:match_id>', methods=['POST'])
def edit_match(match_id):
    conn = get_db_connection()
    match = conn.execute('''
        SELECT * FROM matches WHERE id = ?
    ''', (match_id,)).fetchone()
    
    if not match:
        flash('Match not found', 'error')
        return redirect(url_for('home'))
    
    if not can_edit_match(match['date']):
        flash('Cannot edit match after 3 hours', 'error')
        return redirect(url_for('match_detail', match_id=match_id))
    
    # Update match note
    match_note = request.form.get('match_note', '')
    conn.execute('UPDATE matches SET match_note = ? WHERE id = ?', (match_note, match_id))
    
    # Update player statistics
    for player_id in [match['player1_id'], match['player2_id']]:
        backhand = request.form.get(f'backhand_{player_id}')
        forehand = request.form.get(f'forehand_{player_id}')
        service = request.form.get(f'service_{player_id}')
        style = request.form.get(f'style_{player_id}')
        player_note = request.form.get(f'player_note_{player_id}', '')
        
        # Convert to integers or None
        backhand = int(backhand) if backhand and backhand.isdigit() else None
        forehand = int(forehand) if forehand and forehand.isdigit() else None
        service = int(service) if service and service.isdigit() else None
        style = int(style) if style and style.isdigit() else None
        
        # Calculate overall rating
        overall = calculate_overall_rating(backhand, forehand, service, style)
        
        # Insert or update player stats
        conn.execute('''
            INSERT OR REPLACE INTO player_stats 
            (match_id, player_id, backhand, forehand, service, style, overall, player_note)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', (match_id, player_id, backhand, forehand, service, style, overall, player_note))
    
    conn.commit()
    conn.close()
    
    flash('Match updated successfully!', 'success')
    return redirect(url_for('match_detail', match_id=match_id))

@app.route('/crop_image', methods=['POST'])
def crop_image():
    """Handle image cropping with coordinates"""
    try:
        data = request.get_json()
        filename = data.get('filename')
        crop_data = data.get('cropData')
        
        if not filename or not crop_data:
            return jsonify({'success': False, 'error': 'Missing data'})
        
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        
        if not os.path.exists(file_path):
            return jsonify({'success': False, 'error': 'File not found'})
        
        # Apply cropping
        success = crop_and_resize_image(file_path, crop_data)
        
        if success:
            return jsonify({'success': True})
        else:
            return jsonify({'success': False, 'error': 'Failed to process image'})
            
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/detect_faces/<filename>')
def detect_faces_route(filename):
    """Detect faces in uploaded image"""
    try:
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        
        if not os.path.exists(file_path):
            return jsonify({'success': False, 'error': 'File not found'})
        
        faces = detect_faces(file_path)
        return jsonify({'success': True, 'faces': faces})
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/edit_player/<int:player_id>', methods=['GET', 'POST'])
def edit_player(player_id):
    conn = get_db_connection()
    player = conn.execute('SELECT * FROM players WHERE id = ?', (player_id,)).fetchone()
    
    if not player:
        flash('Player not found', 'error')
        return redirect(url_for('players'))
    
    if request.method == 'POST':
        name = request.form['name'].strip()
        age = request.form.get('age')
        height = request.form.get('height')
        weight = request.form.get('weight')
        bio = request.form.get('bio', '').strip()
        
        if not name:
            flash('Player name is required', 'error')
            return render_template('edit_player.html', player=player)
        
        # Convert numeric fields
        age = int(age) if age and age.isdigit() else None
        height = int(height) if height and height.isdigit() else None
        weight = int(weight) if weight and weight.isdigit() else None
        
        # Handle photo upload
        photo_filename = player['photo_filename']
        if 'photo' in request.files:
            file = request.files['photo']
            if file and file.filename and allowed_file(file.filename):
                # Delete old photo if exists
                if photo_filename:
                    old_path = os.path.join(app.config['UPLOAD_FOLDER'], photo_filename)
                    if os.path.exists(old_path):
                        os.remove(old_path)
                
                photo_filename = secure_filename(file.filename)
                photo_filename = f"{datetime.now().strftime('%Y%m%d_%H%M%S')}_{photo_filename}"
                file_path = os.path.join(app.config['UPLOAD_FOLDER'], photo_filename)
                file.save(file_path)
                
                # Check for crop data
                crop_data = None
                if request.form.get('crop_data'):
                    import json
                    crop_data = json.loads(request.form.get('crop_data'))
                
                if crop_and_resize_image(file_path, crop_data):
                    flash('Photo processed successfully', 'success')
                else:
                    flash('Photo uploaded but processing failed', 'warning')
        
        try:
            conn.execute('''
                UPDATE players 
                SET name = ?, photo_filename = ?, age = ?, height = ?, weight = ?, bio = ?
                WHERE id = ?
            ''', (name, photo_filename, age, height, weight, bio, player_id))
            conn.commit()
            conn.close()
            
            flash('Player updated successfully!', 'success')
            return redirect(url_for('players'))
            
        except sqlite3.IntegrityError:
            flash('Player name already exists', 'error')
    
    conn.close()
    return render_template('edit_player.html', player=player)

@app.route('/delete_player/<int:player_id>', methods=['POST'])
def delete_player(player_id):
    conn = get_db_connection()
    
    # Check if player has matches
    matches = conn.execute('''
        SELECT COUNT(*) as count FROM matches 
        WHERE player1_id = ? OR player2_id = ?
    ''', (player_id, player_id)).fetchone()
    
    if matches['count'] > 0:
        flash(f'Cannot delete player. They have {matches["count"]} matches recorded.', 'error')
        conn.close()
        return redirect(url_for('players'))
    
    # Get player info for photo deletion
    player = conn.execute('SELECT * FROM players WHERE id = ?', (player_id,)).fetchone()
    
    if player:
        # Delete photo file if exists
        if player['photo_filename']:
            photo_path = os.path.join(app.config['UPLOAD_FOLDER'], player['photo_filename'])
            if os.path.exists(photo_path):
                os.remove(photo_path)
        
        # Delete player
        conn.execute('DELETE FROM players WHERE id = ?', (player_id,))
        conn.commit()
        flash('Player deleted successfully!', 'success')
    else:
        flash('Player not found', 'error')
    
    conn.close()
    return redirect(url_for('players'))

@app.route('/delete_match/<int:match_id>', methods=['POST'])
def delete_match(match_id):
    conn = get_db_connection()
    
    # Delete player stats first (foreign key constraint)
    conn.execute('DELETE FROM player_stats WHERE match_id = ?', (match_id,))
    
    # Delete match
    result = conn.execute('DELETE FROM matches WHERE id = ?', (match_id,))
    
    if result.rowcount > 0:
        conn.commit()
        flash('Match deleted successfully!', 'success')
    else:
        flash('Match not found', 'error')
    
    conn.close()
    return redirect(url_for('home'))

if __name__ == '__main__':
    init_db()
    # Debug mode should be False in production
    debug_mode = os.environ.get('FLASK_ENV') == 'development'
    app.run(debug=debug_mode)
