import pymysql
import os
from dotenv import load_dotenv
from urllib.parse import urlparse

load_dotenv()

# Parse the database URI
uri = os.getenv('DATABASE_URI')
result = urlparse(uri)

# Extract connection details
username = result.username
password = result.password
host = result.hostname
port = result.port or 3306
dbname = result.path[1:] # Remove leading slash

print(f"Connecting to MySQL server at {host} to create database '{dbname}'...")

try:
    # Connect without selecting a database
    connection = pymysql.connect(
        host=host,
        user=username,
        password=password,
        port=port
    )
    
    cursor = connection.cursor()
    cursor.execute(f"CREATE DATABASE IF NOT EXISTS {dbname}")
    print(f"Database '{dbname}' created successfully (or already existed).")
    
    cursor.close()
    connection.close()
    
except Exception as e:
    print(f"Error creating database: {e}")
