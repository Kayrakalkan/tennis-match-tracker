#!/usr/bin/env python3
"""
Database migration script to upgrade from old to new schema
"""
import sqlite3
import os
from datetime import datetime

def migrate_database():
    db_path = 'tennis_matches.db'
    backup_path = f'tennis_matches_backup_{datetime.now().strftime("%Y%m%d_%H%M%S")}.db'
    
    print("Starting database migration...")
    
    # Create backup
    if os.path.exists(db_path):
        print(f"Creating backup: {backup_path}")
        os.system(f'cp {db_path} {backup_path}')
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Check if we need to migrate
    try:
        cursor.execute("SELECT player1_id FROM matches LIMIT 1")
        print("Database is already up to date!")
        conn.close()
        return
    except sqlite3.OperationalError:
        print("Old database detected, starting migration...")
    
    # Create new tables
    print("Creating players table...")
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS players (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL UNIQUE,
            photo_filename TEXT DEFAULT NULL,
            created_date DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Check if old matches table exists and has data
    try:
        old_matches = cursor.execute("SELECT * FROM matches").fetchall()
        print(f"Found {len(old_matches)} old matches to migrate")
        
        if old_matches:
            # Create default players
            print("Creating default players...")
            cursor.execute("INSERT OR IGNORE INTO players (name) VALUES (?)", ("Player 1",))
            cursor.execute("INSERT OR IGNORE INTO players (name) VALUES (?)", ("Player 2",))
            
            # Get player IDs
            player1_id = cursor.execute("SELECT id FROM players WHERE name = ?", ("Player 1",)).fetchone()[0]
            player2_id = cursor.execute("SELECT id FROM players WHERE name = ?", ("Player 2",)).fetchone()[0]
        
        # Rename old matches table
        print("Backing up old matches table...")
        cursor.execute("ALTER TABLE matches RENAME TO matches_old")
        
    except sqlite3.OperationalError:
        print("No old matches table found")
        old_matches = []
    
    # Create new matches table
    print("Creating new matches table...")
    cursor.execute('''
        CREATE TABLE matches (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            date DATETIME DEFAULT CURRENT_TIMESTAMP,
            player1_id INTEGER NOT NULL,
            player2_id INTEGER NOT NULL,
            sets TEXT NOT NULL,
            winner_id INTEGER,
            note TEXT DEFAULT '',
            FOREIGN KEY (player1_id) REFERENCES players (id),
            FOREIGN KEY (player2_id) REFERENCES players (id),
            FOREIGN KEY (winner_id) REFERENCES players (id)
        )
    ''')
    
    # Create player_stats table
    print("Creating player_stats table...")
    cursor.execute('''
        CREATE TABLE player_stats (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            match_id INTEGER NOT NULL,
            player_id INTEGER NOT NULL,
            backhand INTEGER DEFAULT NULL,
            forehand INTEGER DEFAULT NULL,
            service INTEGER DEFAULT NULL,
            style INTEGER DEFAULT NULL,
            overall FLOAT DEFAULT NULL,
            FOREIGN KEY (match_id) REFERENCES matches (id),
            FOREIGN KEY (player_id) REFERENCES players (id)
        )
    ''')
    
    # Migrate old data if exists
    if old_matches:
        print("Migrating old matches...")
        for old_match in old_matches:
            # Calculate winner based on old result
            result = old_match[3]  # assuming result column was at index 3
            if result and '-' in result:
                p1_sets, p2_sets = map(int, result.split('-'))
                winner_id = player1_id if p1_sets > p2_sets else player2_id
            else:
                winner_id = player1_id  # default to player 1
            
            # Insert into new matches table
            cursor.execute('''
                INSERT INTO matches (date, player1_id, player2_id, sets, winner_id, note)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (old_match[1], player1_id, player2_id, old_match[2], winner_id, old_match[4] or ''))
            
            new_match_id = cursor.lastrowid
            
            # Migrate player stats if they exist
            if len(old_match) > 5:  # if old stats exist
                # Create stats for player 1 using old data
                cursor.execute('''
                    INSERT INTO player_stats (match_id, player_id, backhand, forehand, service, style, overall)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                ''', (new_match_id, player1_id, old_match[5], old_match[6], old_match[7], old_match[8], old_match[9]))
        
        print(f"Migrated {len(old_matches)} matches")
    
    # Create default players if none exist
    player_count = cursor.execute("SELECT COUNT(*) FROM players").fetchone()[0]
    if player_count == 0:
        print("Creating default players...")
        cursor.execute("INSERT INTO players (name) VALUES (?)", ("You",))
        cursor.execute("INSERT INTO players (name) VALUES (?)", ("Your Uncle",))
    
    conn.commit()
    conn.close()
    
    print("Migration completed successfully!")
    print("You can now start the application.")

if __name__ == "__main__":
    migrate_database()
