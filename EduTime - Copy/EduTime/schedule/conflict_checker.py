from db_config import get_connection

"""
    Quick DB check: returns True if no conflict for given slot.
"""

def all_slots_free(room_id: int, instructor_id: int,
                       semester_id: int, slot_ids: list[int]) -> bool:
        conn = get_connection();
        cur = conn.cursor()
        placeholders = ",".join(["%s"] * len(slot_ids))
        cur.execute(f"""
            SELECT 1
            FROM ClassSchedule
            WHERE TimeSlot_ID IN ({placeholders})
              AND (Room_ID = %s OR Instructor_ID = %s OR Semester_ID = %s)
            LIMIT 1
        """, (*slot_ids, room_id, instructor_id, semester_id))
        conflict = cur.fetchone() is not None
        cur.close();
        conn.close()
        return not conflict
