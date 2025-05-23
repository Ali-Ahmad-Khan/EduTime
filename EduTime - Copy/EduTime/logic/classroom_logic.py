from db_config import get_connection
from logic.department_logic import get_or_create_department


from db_config import get_connection

def generate_classrooms_for_existing(department_id: int, prefix: str, num_rooms: int, room_type: str):
    """
    Creates rooms with Department_ID already provided.
    Prefix is still used for naming the RoomNumber (e.g., CS-CR-01)
    Checks for existing rooms and starts numbering from the highest existing number
    """
    conn = get_connection(); cur = conn.cursor()
    
    # Determine the room prefix pattern
    if room_type == 'CLASSROOM':
        if "CR" in prefix:
            pattern = f"{prefix}-%"
        else:
            pattern = f"{prefix}-CR-%"
    else:  # LAB
        if "LAB" in prefix:
            pattern = f"{prefix}-%"
        else:
            pattern = f"{prefix}-LAB-%"
    
    # Get the highest existing room number for this pattern
    cur.execute("""
        SELECT RoomNumber
        FROM Classroom
        WHERE Department_ID = %s AND RoomType = %s AND RoomNumber LIKE %s
        ORDER BY RoomNumber DESC
        LIMIT 1
    """, (department_id, room_type, pattern))
    
    result = cur.fetchone()
    
    # Determine the starting number
    start_num = 1
    if result:
        # Extract the number from the room number
        room_num = result[0]
        # Find the last digits in the room number
        import re
        match = re.search(r'(\d+)$', room_num)
        if match:
            start_num = int(match.group(1)) + 1
    
    # Create the new rooms
    for i in range(start_num, start_num + num_rooms):
        # Format the room number
        if room_type == 'CLASSROOM':
            if "CR" in prefix:
                room_num = f"{prefix}-{i:02}"
            else:
                room_num = f"{prefix}-CR-{i:02}"
        else:  # LAB
            if "LAB" in prefix:
                room_num = f"{prefix}-{i:02}"
            else:
                room_num = f"{prefix}-LAB-{i:02}"
        
        cur.execute("""
            INSERT INTO Classroom (RoomNumber, RoomType, Department_ID)
            VALUES (%s, %s, %s)
        """, (room_num, room_type, department_id))

    conn.commit(); cur.close(); conn.close()

def delete_room(room_id: int):
    conn = get_connection()
    cur  = conn.cursor()
    cur.execute("DELETE FROM Classroom WHERE Room_ID=%s", (room_id,))
    conn.commit(); cur.close(); conn.close()
