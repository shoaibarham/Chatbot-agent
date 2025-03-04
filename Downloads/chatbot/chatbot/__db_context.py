import sqlite3

def get_db_context(self):
        """
        Connects to the SQLite database specified by db_path and retrieves
        all table names along with their column names.

            :param db_path: Path to the SQLite database file.
            :return: A dictionary where keys are table names and values are lists of column names.
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        db_context = {}
        try:
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
            tables = cursor.fetchall()

            for table in tables:
                table_name = table[0]
                if table_name == "sqlite_sequence":
                    continue

                cursor.execute(f"PRAGMA table_info({table_name});")
                columns = cursor.fetchall()
                column_names = [column[1] for column in columns]

                db_context[table_name] = column_names

        except sqlite3.Error as e:
            print(f"An error occurred: {e}")
        finally:
            conn.close()

        # convert dictionary to String
        db_context_str = str(db_context)
        print("db_context : " ,db_context_str)
        
        return db_context_str


if __name__ == "__main__":
    db_path = "gtfs.db"
    db_context = get_db_context(db_path)
    print(db_context)