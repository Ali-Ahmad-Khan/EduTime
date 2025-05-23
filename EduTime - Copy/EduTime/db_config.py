import mysql.connector
from mysql.connector import Error

def get_connection():
    """Get a connection to the database with error handling"""
    try:
        return mysql.connector.connect(
            host='localhost',
            user='root',
            password='Ali.ak711',
            database='edutime_final'
        )
    except Error as e:
        print(f"Error connecting to MySQL database: {e}")
        raise
