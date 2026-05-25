import sys
import os
import pymysql
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database.connection import get_database_uri

uri = get_database_uri()
# Format: mysql+pymysql://root:@localhost:3306/alumni_db
if "mysql+pymysql://" in uri:
    parts = uri.split("mysql+pymysql://")[1]
    # root:@localhost:3306/alumni_db
    user_pass, host_port_db = parts.split("@")
    user = user_pass.split(":")[0]
    password = user_pass.split(":")[1] if ":" in user_pass else ""
    host_port, db_name = host_port_db.split("/")
    host = host_port.split(":")[0]
    port = int(host_port.split(":")[1]) if ":" in host_port else 3306

    connection = pymysql.connect(host=host, user=user, password=password, port=port, database=db_name)
    with connection.cursor() as cursor:
        # Add to alumni
        try:
            cursor.execute("ALTER TABLE alumni ADD COLUMN is_email_verified BOOLEAN DEFAULT FALSE;")
            cursor.execute("ALTER TABLE alumni ADD COLUMN email_verification_token VARCHAR(100) DEFAULT NULL;")
            cursor.execute("ALTER TABLE alumni ADD COLUMN email_verification_otp VARCHAR(6) DEFAULT NULL;")
            print("Added email verification columns to alumni table.")
        except Exception as e:
            print(f"Alumni table alteration error (might already exist): {e}")
            
        # Add to students
        try:
            cursor.execute("ALTER TABLE students ADD COLUMN is_email_verified BOOLEAN DEFAULT FALSE;")
            cursor.execute("ALTER TABLE students ADD COLUMN email_verification_token VARCHAR(100) DEFAULT NULL;")
            cursor.execute("ALTER TABLE students ADD COLUMN email_verification_otp VARCHAR(6) DEFAULT NULL;")
            cursor.execute("ALTER TABLE students ADD COLUMN job_location VARCHAR(100) DEFAULT NULL;")
            print("Added email verification and job_location columns to students table.")
        except Exception as e:
            print(f"Students table alteration error (might already exist): {e}")

    connection.commit()
    connection.close()
    print("Database altered successfully!")
else:
    print("Using SQLite. No alteration needed as create_all handles creation.")
