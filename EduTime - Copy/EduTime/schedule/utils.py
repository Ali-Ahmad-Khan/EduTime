# Simple helpers reused by generator & checker
from db_config import get_connection

def fetch_all(query: str, params: tuple = ()):
    conn = get_connection(); cur = conn.cursor()
    cur.execute(query, params)
    rows = cur.fetchall()
    cur.close(); conn.close()
    return rows
