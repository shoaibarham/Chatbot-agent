import sqlite3

def get_db_context(db_path , query):
    """
    Test a Query
    """
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    db_context = {}
    try:
        cursor.execute(query)
        result = cursor.fetchall()
        print(result)

        

    except sqlite3.Error as e:
        print(f"An error occurred: {e}")
    finally:
        conn.close()

    # convert dictionary to String
    db_context_str = str(db_context)
    
    return db_context_str


if __name__ == "__main__":
    db_path = "gtfs.db"
    query = "SELECT * FROM routes JOIN dates_and_vessels ON routes.id = dates_and_vessels.route_id WHERE routes.origin_port_name = 'MILOS' AND routes.destination_port_name = 'PIRAEUS';"
    print(get_db_context(db_path , query))