import mysql.connector
import hashlib
import time
import sys

# Configuration
DB_CONFIG = {
    'host': 'localhost',
    'user': 'root',
    'password': 'Ali.ak711',
    'database': 'edutime_final'
}

# Helper function to execute a query with error handling and retry
def execute_query(query, params=None, connection=None, commit=True, retry_count=3, close_conn=False):
    """Execute a query with error handling and retry logic"""
    conn = connection
    new_connection = False
    
    if conn is None:
        try:
            conn = mysql.connector.connect(**DB_CONFIG)
            new_connection = True
        except mysql.connector.Error as err:
            print(f"❌ Error establishing database connection: {err}")
            return False, None
    
    try:
        cursor = conn.cursor()
        
        for attempt in range(retry_count):
            try:
                if params:
                    cursor.execute(query, params)
                else:
                    cursor.execute(query)
                
                if commit:
                    conn.commit()
                
                last_row_id = cursor.lastrowid
                cursor.close()
                
                if close_conn or new_connection:
                    conn.close()
                    conn = None
                
                return True, last_row_id if last_row_id else None
            
            except mysql.connector.Error as err:
                print(f"⚠️ Error executing query (attempt {attempt+1}/{retry_count}): {err}")
                
                if attempt < retry_count - 1:
                    print(f"Retrying in 1 second...")
                    time.sleep(1)
                    if new_connection and conn:
                        try:
                            conn.close()
                            conn = mysql.connector.connect(**DB_CONFIG)
                        except:
                            pass
                else:
                    print(f"❌ Failed after {retry_count} attempts")
                    if conn and (close_conn or new_connection):
                        conn.close()
                    return False, None
    
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        if conn and (close_conn or new_connection):
            conn.close()
        return False, None
    
    return True, None

def initialize_sample_data():
    """Initialize the database with sample data"""
    print("Initializing database with sample data...")
    
    # Create a connection to use throughout the process
    try:
        conn = mysql.connector.connect(**DB_CONFIG)
        print("✅ Connected to database successfully")
    except mysql.connector.Error as err:
        print(f"❌ Error connecting to database: {err}")
        return False
    
    try:
        # 1. Create departments
        print("\nCreating departments...")
        depts = [
            ('CS', 'Computer Science'),
            ('EE', 'Electrical Engineering'),
            ('BBA', 'Business Administration')
        ]
        
        dept_ids = {}
        for prefix, name in depts:
            success, dept_id = execute_query(
                "INSERT INTO Department (Prefix, Name) VALUES (%s, %s)",
                (prefix, name),
                connection=conn
            )
            if success and dept_id:
                dept_ids[prefix] = dept_id
                print(f"  ✓ {prefix} - {name}")
            else:
                print(f"  ✗ Failed to create department: {prefix}")
                return False
        
        # 2. Create rooms for each department
        print("\nCreating classrooms and labs...")
        for prefix, dept_id in dept_ids.items():
            # Create 2 classrooms and 1 lab per department
            rooms = [
                (f"{prefix}-101", "CLASSROOM", dept_id),
                (f"{prefix}-102", "CLASSROOM", dept_id),
                (f"{prefix}-LAB1", "LAB", dept_id)
            ]
            
            for room_number, room_type, dept_id in rooms:
                success, _ = execute_query(
                    "INSERT INTO Classroom (RoomNumber, RoomType, Department_ID) VALUES (%s, %s, %s)",
                    (room_number, room_type, dept_id),
                    connection=conn
                )
                if success:
                    print(f"  ✓ {room_number} ({room_type})")
                else:
                    print(f"  ✗ Failed to create room: {room_number}")
                    return False
        
        # 3. Create degrees for each department
        print("\nCreating degrees...")
        degrees = [
            ('BS Computer Science', dept_ids['CS'], 8),
            ('BE Electrical Engineering', dept_ids['EE'], 8),
            ('BBA', dept_ids['BBA'], 8)
        ]
        
        degree_ids = {}
        for degree_name, dept_id, num_semesters in degrees:
            success, degree_id = execute_query(
                "INSERT INTO Degree (Name, Department_ID) VALUES (%s, %s)",
                (degree_name, dept_id),
                connection=conn
            )
            
            if success and degree_id:
                degree_ids[degree_name] = degree_id
                print(f"  ✓ {degree_name}")
                
                # Create semesters for this degree
                for sem_no in range(1, num_semesters + 1):
                    success, sem_id = execute_query(
                        "INSERT INTO Semester (Degree_ID, Semester_No) VALUES (%s, %s)",
                        (degree_id, sem_no),
                        connection=conn
                    )
                    
                    if not success:
                        print(f"  ✗ Failed to create semester {sem_no} for {degree_name}")
                        return False
            else:
                print(f"  ✗ Failed to create degree: {degree_name}")
                return False
        
        # 4. Create courses for the first few semesters of CS degree
        print("\nCreating courses...")
        cs_degree_id = degree_ids['BS Computer Science']
        
        # Get semester IDs for CS degree
        cursor = conn.cursor()
        cursor.execute(
            "SELECT Semester_ID, Semester_No FROM Semester WHERE Degree_ID = %s ORDER BY Semester_No",
            (cs_degree_id,)
        )
        semesters = {sem_no: sem_id for sem_id, sem_no in cursor.fetchall()}
        cursor.close()
        
        # Sample courses for first 2 semesters
        courses = [
            # Semester 1
            ('Programming Fundamentals', cs_degree_id, semesters[1], 3, False),
            ('Calculus I', cs_degree_id, semesters[1], 3, False),
            ('Physics I', cs_degree_id, semesters[1], 3, False),
            ('Physics Lab', cs_degree_id, semesters[1], 1, True),
            
            # Semester 2
            ('Data Structures', cs_degree_id, semesters[2], 3, False),
            ('Calculus II', cs_degree_id, semesters[2], 3, False),
            ('Digital Logic Design', cs_degree_id, semesters[2], 3, False),
            ('Digital Logic Lab', cs_degree_id, semesters[2], 1, True)
        ]
        
        course_ids = []
        for course_name, degree_id, semester_id, credits, is_lab in courses:
            success, course_id = execute_query(
                """
                INSERT INTO Course (Name, Degree_ID, Semester_ID, CreditHours, IsLab)
                VALUES (%s, %s, %s, %s, %s)
                """,
                (course_name, degree_id, semester_id, credits, is_lab),
                connection=conn
            )
            
            if success and course_id:
                course_ids.append(course_id)
                print(f"  ✓ {course_name}")
            else:
                print(f"  ✗ Failed to create course: {course_name}")
                return False
        
        # 5. Create users of different roles
        print("\nCreating users...")
        
        # Admin user
        admin_password = hashlib.sha256("admin123".encode()).hexdigest()
        success, admin_id = execute_query(
            """
            INSERT INTO UserAccount (Name, Email, Role, PasswordHash)
            VALUES (%s, %s, %s, %s)
            """,
            ("Administrator", "admin@edutime.com", "ADMIN", admin_password),
            connection=conn
        )
        
        if success and admin_id:
            execute_query(
                "INSERT INTO Administrator (Admin_ID, User_ID) VALUES (%s, %s)",
                (admin_id, admin_id),
                connection=conn
            )
            print(f"  ✓ Administrator (admin@edutime.com / admin123)")
        else:
            print(f"  ✗ Failed to create admin user")
            return False
        
        # Instructor users
        instructors = [
            ("John Smith", "john@edutime.com", dept_ids['CS']),
            ("Emma Johnson", "emma@edutime.com", dept_ids['EE']),
            ("Michael Brown", "michael@edutime.com", dept_ids['BBA'])
        ]
        
        instructor_ids = []
        for name, email, dept_id in instructors:
            password = hashlib.sha256("password123".encode()).hexdigest()
            success, user_id = execute_query(
                """
                INSERT INTO UserAccount (Name, Email, Role, PasswordHash)
                VALUES (%s, %s, %s, %s)
                """,
                (name, email, "INSTRUCTOR", password),
                connection=conn
            )
            
            if success and user_id:
                success, _ = execute_query(
                    "INSERT INTO Instructor (Instructor_ID, User_ID, Department_ID) VALUES (%s, %s, %s)",
                    (user_id, user_id, dept_id),
                    connection=conn
                )
                
                if success:
                    instructor_ids.append(user_id)
                    print(f"  ✓ Instructor: {name} ({email} / password123)")
                else:
                    print(f"  ✗ Failed to create instructor record for {name}")
                    return False
            else:
                print(f"  ✗ Failed to create instructor user: {name}")
                return False
        
        # Student users
        students = [
            ("Alice Johnson", "alice@edutime.com"),
            ("Bob Williams", "bob@edutime.com"),
            ("Charlie Davis", "charlie@edutime.com")
        ]
        
        for name, email in students:
            password = hashlib.sha256("student123".encode()).hexdigest()
            success, user_id = execute_query(
                """
                INSERT INTO UserAccount (Name, Email, Role, PasswordHash)
                VALUES (%s, %s, %s, %s)
                """,
                (name, email, "STUDENT", password),
                connection=conn
            )
            
            if success and user_id:
                success, _ = execute_query(
                    "INSERT INTO Student (Student_ID, User_ID) VALUES (%s, %s)",
                    (user_id, user_id),
                    connection=conn
                )
                
                if success:
                    print(f"  ✓ Student: {name} ({email} / student123)")
                else:
                    print(f"  ✗ Failed to create student record for {name}")
                    return False
            else:
                print(f"  ✗ Failed to create student user: {name}")
                return False
        
        # 6. Assign courses to instructors
        print("\nAssigning courses to instructors...")
        cs_instructor = instructor_ids[0]  # John Smith
        
        for course_id in course_ids:
            success, _ = execute_query(
                "INSERT INTO Teaches (Instructor_ID, Course_ID) VALUES (%s, %s)",
                (cs_instructor, course_id),
                connection=conn
            )
            
            if not success:
                print(f"  ✗ Failed to assign course {course_id} to instructor")
                return False
        
        print(f"  ✓ Assigned {len(course_ids)} courses to John Smith")
        
        # 7. Create time slots
        print("\nCreating time slots...")
        days = ['MON', 'TUE', 'WED', 'THU', 'FRI']
        time_ranges = [
            (1, '09:00', '09:50'),
            (2, '10:00', '10:50'),
            (3, '11:00', '11:50'),
            (4, '12:00', '12:50'),
            (6, '14:00', '14:50'),
            (7, '15:00', '15:50'),
            (8, '16:00', '16:50')
        ]
        
        for day in days:
            for slot_no, start_time, end_time in time_ranges:
                success, _ = execute_query(
                    """
                    INSERT INTO TimeSlot (Day, Slot_No, StartTime, EndTime)
                    VALUES (%s, %s, %s, %s)
                    """,
                    (day, slot_no, start_time, end_time),
                    connection=conn
                )
                
                if not success:
                    print(f"  ✗ Failed to create time slot: {day} {start_time}-{end_time}")
                    return False
        
        print(f"  ✓ Created {len(days) * len(time_ranges)} time slots")
        
        print("\n✅ Database initialization complete!")
        print("\nYou can now log in with the following accounts:")
        print("  Admin: admin@edutime.com / admin123")
        print("  Instructor: john@edutime.com / password123")
        print("  Student: alice@edutime.com / student123")
        
        return True
        
    except Exception as e:
        print(f"❌ Unexpected error during initialization: {e}")
        return False
    finally:
        if conn:
            conn.close()

# Main execution
if __name__ == "__main__":
    print("EduTime Database Initialization Tool")
    print("-----------------------------------")
    
    if len(sys.argv) > 1 and sys.argv[1] == "--confirm":
        initialize_sample_data()
    else:
        print("⚠️ This script will add sample data to the edutime_final database.")
        print("Make sure you have already run reset_database.py to create a clean database.")
        print("To proceed, run the script with the --confirm flag:")
        print("  python EduTime/initialize_database.py --confirm") 