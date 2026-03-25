import mysql.connector

# DB Config
config = {
    'user': 'root',
    'password': 'root',  # Your password from settings.py
    'host': 'localhost',
}

try:
    # Connect to MySQL Server
    conn = mysql.connector.connect(**config)
    cursor = conn.cursor()
    
    # Reset Database
    print("Dropping old database...")
    cursor.execute("DROP DATABASE IF EXISTS medicare_db")
    
    print("Creating fresh database...")
    cursor.execute("CREATE DATABASE medicare_db")
    
    print("✅ Success! Database is empty and ready.")
    conn.close()

except mysql.connector.Error as err:
    print(f"❌ Error: {err}")