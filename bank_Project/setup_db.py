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

from main import app, db

print("Creating database tables...")
with app.app_context():
    db.create_all()
print("Database tables created successfully.")
