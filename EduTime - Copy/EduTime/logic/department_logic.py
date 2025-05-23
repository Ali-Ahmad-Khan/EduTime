from db_config import get_connection

def get_or_create_department(prefix: str, full_name: str = None) -> int:
    conn = get_connection(); cur = conn.cursor()
    cur.execute("SELECT Department_ID FROM Department WHERE Prefix=%s", (prefix,))
    row = cur.fetchone()
    if row:
        dept_id = row[0]
    else:
        cur.execute(
            "INSERT INTO Department (Prefix, Name) VALUES (%s,%s)",
            (prefix, full_name or f"{prefix} Dept")
        )
        dept_id = cur.lastrowid
        conn.commit()
    cur.close(); conn.close()
    return dept_id

def delete_department(dept_id: int) -> None:
    """
    Delete a department. All associated data will be automatically deleted
    through ON DELETE CASCADE constraints defined in the database.
    """
    conn = get_connection(); cur = conn.cursor()
    
    # Delete the department - all related entities will cascade-delete
    cur.execute("DELETE FROM Department WHERE Department_ID = %s", (dept_id,))
    
    conn.commit()
    cur.close()
    conn.close()
