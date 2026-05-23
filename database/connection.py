import os
import pymysql
from dotenv import load_dotenv

load_dotenv()

def get_database_uri():
    db_user = os.getenv("DB_USER", "root")
    db_password = os.getenv("DB_PASSWORD", "")
    db_host = os.getenv("DB_HOST", "localhost")
    db_port = os.getenv("DB_PORT", "3306")
    db_name = os.getenv("DB_NAME", "alumni_db")
    sqlite_fallback = os.getenv("SQLITE_FALLBACK", "True").lower() == "true"

    # MySQL connection string
    mysql_uri = f"mysql+pymysql://{db_user}:{db_password}@{db_host}:{db_port}/{db_name}"

    # Verify if MySQL is running and accessible
    print(f"[*] Checking connection to MySQL server at {db_host}:{db_port}...")
    try:
        # Try a quick connection test with pymysql directly
        # Use a short timeout of 2 seconds so startup isn't blocked long
        connection = pymysql.connect(
            host=db_host,
            user=db_user,
            password=db_password,
            port=int(db_port),
            connect_timeout=2
        )
        
        # Connection succeeded. Let's make sure the database exists.
        with connection.cursor() as cursor:
            cursor.execute(f"CREATE DATABASE IF NOT EXISTS {db_name}")
        connection.close()
        
        print("[+] MySQL connection succeeded! Using MySQL database.")
        return mysql_uri
    except Exception as e:
        print(f"[-] MySQL connection failed: {e}")
        if sqlite_fallback:
            # Prepare directory for SQLite database
            base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            db_dir = os.path.join(base_dir, "database")
            os.makedirs(db_dir, exist_ok=True)
            db_path = os.path.join(db_dir, "alumni.db").replace("\\", "/")
            sqlite_uri = f"sqlite:///{db_path}"
            print(f"[!] Falling back to SQLite database at: {sqlite_uri}")
            return sqlite_uri
        else:
            print("[-] SQLite fallback is disabled. Re-raising MySQL connection error.")
            raise e
