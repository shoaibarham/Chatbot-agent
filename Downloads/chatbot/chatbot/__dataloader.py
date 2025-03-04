import sqlite3
import json

# Connect to (or create) the SQLite database
conn = sqlite3.connect('gtfs.db')
cursor = conn.cursor()

# Create the tables
cursor.execute('''
    CREATE TABLE IF NOT EXISTS routes (
        route_id INTEGER PRIMARY KEY AUTOINCREMENT,
        route_number TEXT,
        company TEXT,
        company_code TEXT,
        origin_port_code TEXT,
        origin_port_name TEXT,
        destination_port_code TEXT,
        destination_port_name TEXT,
        departure_time TEXT,
        arrival_time TEXT,
        origin_port_stop INTEGER,
        destination_port_stop INTEGER,
        departure_offset INTEGER,
        arrival_offset INTEGER,
        duration INTEGER
    )
''')

cursor.execute('''
    CREATE TABLE IF NOT EXISTS dates_and_vessels (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        route_id INTEGER,
        schedule_date TEXT,
        vessel TEXT,
        FOREIGN KEY (route_id) REFERENCES routes(id)
    )
''')

cursor.execute('''
    CREATE TABLE IF NOT EXISTS vessels_and_prices (
        route_id INTEGER,
        vessel TEXT ,
        price INTEGER,
        PRIMARY KEY (route_id, vessel),
        FOREIGN KEY (route_id) REFERENCES routes(id)
    )
''')

# Load JSON data from file
with open('GTFS_data_v1.json', 'r') as f:
    data = json.load(f)

# Insert data into tables
for item in data:
    # Insert main route information
    cursor.execute('''
        INSERT INTO routes (
            route_number, company, company_code, origin_port_code, origin_port_name, 
            destination_port_code, destination_port_name, departure_time, arrival_time, 
            origin_port_stop, destination_port_stop, departure_offset, arrival_offset, duration
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', (
        item.get('route_id'),
        item.get('company'),
        item.get('company_code'),
        item.get('origin_port'),
        str(item.get('origin_port_code')).upper(),
        item.get('destination_port'),
        str(item.get('destination_port_code')).upper(),
        item.get('departure_time'),
        item.get('arrival_time'),
        item.get('origin_port_stop'),
        item.get('destination_port_stop'),
        item.get('departure_offset'),
        item.get('arrival_offset'),
        item.get('duration')
    ))
    
    # Get the auto-generated id for this route
    route_db_id = cursor.lastrowid

    # Insert each date and vessel mapping
    for schedule_date, vessel in item.get('dates_and_vessels', {}).items():
        cursor.execute('''
            INSERT INTO dates_and_vessels (route_id, schedule_date, vessel)
            VALUES (?, ?, ?)
        ''', (route_db_id, schedule_date, vessel))
    
    # Insert each vessel and price mapping
    # skip if unique constraint fails
    try:
        for vessel, price in item.get('vessels_and_prices', {}).items():
            cursor.execute('''
                INSERT INTO vessels_and_prices (route_id, vessel, price)
                VALUES (?, ?, ?)
            ''', (route_db_id, vessel, price))
    except sqlite3.IntegrityError:
        pass

# Commit the changes and close the connection
conn.commit()
conn.close()

print("Data loaded successfully into the database.")
