from db_config import get_connection
from logic.department_logic import get_or_create_department


def insert_degree_with_semesters(dept_id: int, degree_name: str, num_semesters: int):
    """
    Inserts a degree under a department using department ID.
    Automatically adds n semesters to that degree.
    """
    conn = get_connection(); cur = conn.cursor()

    # Insert Degree
    cur.execute("""
        INSERT INTO Degree (Name, Department_ID)
        VALUES (%s, %s)
    """, (degree_name, dept_id))
    degree_id = cur.lastrowid

    # Insert Semesters
    for sem_no in range(1, num_semesters + 1):
        cur.execute("""
            INSERT INTO Semester (Degree_ID, Semester_No)
            VALUES (%s, %s)
        """, (degree_id, sem_no))

    conn.commit(); cur.close(); conn.close()
    return degree_id


def delete_degree(degree_id: int):
    """
    Deletes a degree and cascades to its semesters and courses
    """
    conn = get_connection(); cur = conn.cursor()
    cur.execute("DELETE FROM Degree WHERE Degree_ID=%s", (degree_id,))
    conn.commit(); cur.close(); conn.close()
