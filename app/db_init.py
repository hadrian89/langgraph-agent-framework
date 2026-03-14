import os

import psycopg2

DB_NAME = os.getenv("DB_NAME", "agentic_ai")

try:
    conn = psycopg2.connect(
        dbname="agentic_ai", user="postgres", password="postgres", host="localhost"
    )
    conn.autocommit = True

    cur = conn.cursor()

    cur.execute(f"CREATE DATABASE {DB_NAME};")

except Exception:
    print("Database already exists")

finally:
    conn.close()
