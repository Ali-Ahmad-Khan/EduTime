from db_config import get_connection

def insert_single_course(degree_id: int, semester_id: int,
                         name: str, credits: int, is_lab: bool):
    conn = get_connection()
    cur  = conn.cursor()
    cur.execute("""
        INSERT INTO Course (Degree_ID, Semester_ID, Name, CreditHours, IsLab)
        VALUES (%s,%s,%s,%s,%s)
    """, (degree_id, semester_id, name, credits, is_lab))
    conn.commit()
    cur.close()
    conn.close()

def insert_bulk_courses(degree_id: int, semester_id: int, courses: list[dict]):
    """
    courses = [{"name":..., "credits":..., "is_lab":...}, ...]
    """
    conn = get_connection()
    cur  = conn.cursor()
    for c in courses:
        cur.execute("""
            INSERT INTO Course (Degree_ID, Semester_ID, Name, CreditHours, IsLab)
            VALUES (%s,%s,%s,%s,%s)
        """, (degree_id, semester_id, c["name"], c["credits"], c["is_lab"]))
    conn.commit()
    cur.close()
    conn.close()

def delete_course(course_id: int):
        conn = get_connection()
        cur = conn.cursor()
        cur.execute("DELETE FROM Course WHERE Course_ID=%s", (course_id,))
        conn.commit();
        cur.close();
        conn.close()

