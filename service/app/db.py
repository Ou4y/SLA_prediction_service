import mysql.connector
import os

def get_db_connection():
    return mysql.connector.connect(
        host=os.getenv("MYSQL_HOST", "localhost"),
        user=os.getenv("MYSQL_USER", "opsmind"),
        password=os.getenv("MYSQL_PASSWORD", "opsmind"),
        database=os.getenv("MYSQL_DATABASE", "opsmind_ai")
    )