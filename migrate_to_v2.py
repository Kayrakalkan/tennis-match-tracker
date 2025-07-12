#!/usr/bin/env python3
"""
Database migration script to add new columns
"""
import sqlite3

def migrate_to_v2():
    print("Starting migration to v2 (adding personal details and notes)...")
    
    conn = sqlite3.connect('tennis_matches.db')
    cursor = conn.cursor()
    
    # Add new columns to players table
    try:
        cursor.execute("ALTER TABLE players ADD COLUMN age INTEGER DEFAULT NULL")
        print("Added age column to players table")
    except sqlite3.OperationalError:
        print("Age column already exists")
    
    try:
        cursor.execute("ALTER TABLE players ADD COLUMN height INTEGER DEFAULT NULL")
        print("Added height column to players table")
    except sqlite3.OperationalError:
        print("Height column already exists")
    
    try:
        cursor.execute("ALTER TABLE players ADD COLUMN weight INTEGER DEFAULT NULL")
        print("Added weight column to players table")
    except sqlite3.OperationalError:
        print("Weight column already exists")
    
    try:
        cursor.execute("ALTER TABLE players ADD COLUMN bio TEXT DEFAULT ''")
        print("Added bio column to players table")
    except sqlite3.OperationalError:
        print("Bio column already exists")
    
    # Update matches table column name
    try:
        cursor.execute("ALTER TABLE matches ADD COLUMN match_note TEXT DEFAULT ''")
        print("Added match_note column to matches table")
    except sqlite3.OperationalError:
        print("Match_note column already exists")
    
    # Add player_note to player_stats table
    try:
        cursor.execute("ALTER TABLE player_stats ADD COLUMN player_note TEXT DEFAULT ''")
        print("Added player_note column to player_stats table")
    except sqlite3.OperationalError:
        print("Player_note column already exists")
    
    conn.commit()
    conn.close()
    
    print("Migration to v2 completed successfully!")

if __name__ == "__main__":
    migrate_to_v2()
