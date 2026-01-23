from app.db import get_db_connection

def test_connection():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT 1")
    result = cursor.fetchone()

    cursor.close()
    conn.close()

    print("DB connection OK:", result)

if __name__ == "__main__":
    test_connection()