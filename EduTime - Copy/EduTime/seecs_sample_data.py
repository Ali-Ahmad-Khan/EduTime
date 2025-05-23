import mysql.connector
import hashlib
import random
import string
import sys

# Configuration
DB_CONFIG = {
    'host': 'localhost',
    'user': 'root',
    'password': 'Ali.ak711',
    'database': 'edutime_final'
}

def execute_query(query, params=None, connection=None, commit=True):
    """Execute a query with error handling"""
    conn = connection
    if conn is None:
        conn = mysql.connector.connect(**DB_CONFIG)
    
    cursor = conn.cursor()
    try:
        cursor.execute(query, params)
        last_id = cursor.lastrowid
        
        if commit:
            conn.commit()
        
        return True, last_id
    except Exception as e:
        print(f"Error executing query: {e}")
        return False, None
    finally:
        cursor.close()

def random_name():
    """Generate a random instructor name"""
    first_names = [
        "Ahmed", "Muhammad", "Ali", "Fatima", "Aisha", "Sara", 
        "Hassan", "Zainab", "Omar", "Noor", "Ibrahim", "Layla"
    ]
    last_names = [
        "Khan", "Ahmed", "Ali", "Siddiqui", "Malik", "Shah", 
        "Qureshi", "Chaudhry", "Iqbal", "Raza", "Sheikh", "Aziz"
    ]
    
    prefix = random.choice(["Dr.", "Prof.", "Mr.", "Ms."])
    return f"{prefix} {random.choice(first_names)} {random.choice(last_names)}"

def random_email(name):
    """Generate a random email based on name"""
    parts = name.lower().split()
    username = parts[-1] + "." + "".join([p[0] for p in parts[1:-1]])
    return f"{username}@seecs.edu.pk"

def initialize_seecs_data():
    """Initialize database with SEECS AI sample data"""
    print("Initializing SEECS sample data...")
    
    try:
        conn = mysql.connector.connect(**DB_CONFIG)
        print("✅ Connected to database")
        
        # 1. Create SEECS department
        print("\nCreating SEECS department...")
        success, dept_id = execute_query(
            "INSERT INTO Department (Prefix, Name) VALUES (%s, %s)",
            ("SE", "School of Electrical Engineering and Computer Science"),
            connection=conn
        )
        if not success:
            print("❌ Failed to create SEECS department")
            return False
        print(f"✓ Created SEECS department (ID: {dept_id})")
        
        # 2. Create rooms
        print("\nCreating classrooms and labs...")
        rooms = [
            ("C1", "CLASSROOM", dept_id),
            ("C2", "CLASSROOM", dept_id),
            ("C3", "CLASSROOM", dept_id),
            ("LAB1", "LAB", dept_id),
            ("LAB2", "LAB", dept_id),
            ("LAB3", "LAB", dept_id),
        ]
        
        room_ids = {}
        for room_num, room_type, dept_id in rooms:
            success, room_id = execute_query(
                "INSERT INTO Classroom (RoomNumber, RoomType, Department_ID) VALUES (%s, %s, %s)",
                (room_num, room_type, dept_id),
                connection=conn
            )
            if success:
                room_ids[room_num] = room_id
                print(f"✓ Created {room_type} {room_num}")
            else:
                print(f"❌ Failed to create {room_type} {room_num}")
        
        # 3. Create AI degree
        print("\nCreating AI degree...")
        success, degree_id = execute_query(
            "INSERT INTO Degree (Name, Department_ID) VALUES (%s, %s)",
            ("BS Artificial Intelligence", dept_id),
            connection=conn
        )
        
        if not success:
            print("❌ Failed to create AI degree")
            return False
        
        print(f"✓ Created BS Artificial Intelligence degree (ID: {degree_id})")
        
        # Create 8 semesters for the degree
        semester_ids = {}
        for sem_no in range(1, 9):
            success, sem_id = execute_query(
                "INSERT INTO Semester (Degree_ID, Semester_No) VALUES (%s, %s)",
                (degree_id, sem_no),
                connection=conn
            )
            if success:
                semester_ids[sem_no] = sem_id
                print(f"✓ Created semester {sem_no}")
            else:
                print(f"❌ Failed to create semester {sem_no}")
        
        # 4. Create random instructors
        print("\nCreating instructors...")
        instructor_names = []
        for _ in range(6):
            name = random_name()
            instructor_names.append(name)
        
        instructor_ids = {}
        for name in instructor_names:
            email = random_email(name)
            password = hashlib.sha256("password123".encode()).hexdigest()
            
            success, user_id = execute_query(
                "INSERT INTO UserAccount (Name, Email, Role, PasswordHash) VALUES (%s, %s, %s, %s)",
                (name, email, "INSTRUCTOR", password),
                connection=conn
            )
            
            if success:
                success, _ = execute_query(
                    "INSERT INTO Instructor (Instructor_ID, User_ID, Department_ID) VALUES (%s, %s, %s)",
                    (user_id, user_id, dept_id),
                    connection=conn
                )
                
                if success:
                    instructor_ids[name] = user_id
                    print(f"✓ Created instructor: {name} ({email})")
                else:
                    print(f"❌ Failed to create instructor record for {name}")
            else:
                print(f"❌ Failed to create user for instructor: {name}")
        
        # 5. Create courses from the images
        print("\nCreating courses...")
        
        # Semester 1 courses
        semester1_courses = [
            {"name": "Fundamentals of Computer Programming", "credits": 3, "lab": 1},
            {"name": "Calculus & Analytical Geometry", "credits": 3, "lab": 0},
            {"name": "Discrete Mathematics", "credits": 3, "lab": 0},
            {"name": "Functional English", "credits": 3, "lab": 0},
            {"name": "Application of Information & Communication Technologies", "credits": 2, "lab": 1}
        ]
        
        # Semester 2 courses
        semester2_courses = [
            {"name": "Database Systems", "credits": 3, "lab": 1},
            {"name": "Object Oriented Programming", "credits": 3, "lab": 1},
            {"name": "Linear Algebra", "credits": 3, "lab": 0},
            {"name": "Multivariable Calculus", "credits": 3, "lab": 0},
            {"name": "Digital Logic Design", "credits": 2, "lab": 1}
        ]
        
        # Semester 3 courses
        semester3_courses = [
            {"name": "Probability & Statistics", "credits": 3, "lab": 0},
            {"name": "Information Security", "credits": 2, "lab": 1},
            {"name": "Islamic Studies", "credits": 2, "lab": 0},
            {"name": "Data Structures & Algorithms", "credits": 3, "lab": 1},
            {"name": "Artificial Intelligence", "credits": 2, "lab": 1},
            {"name": "Computer Networks", "credits": 2, "lab": 1}
        ]
        
        # Semester 4 courses
        semester4_courses = [
            {"name": "Introduction to Data Science", "credits": 2, "lab": 1},
            {"name": "Applied Physics", "credits": 2, "lab": 1},
            {"name": "Expository Writing", "credits": 3, "lab": 0},
            {"name": "Computer Organization and Assembly Language", "credits": 2, "lab": 1},
            {"name": "Advanced Statistics", "credits": 2, "lab": 1}
        ]
        
        # Semester 5 courses
        semester5_courses = [
            {"name": "Introduction To Management", "credits": 2, "lab": 0},
            {"name": "Operating Systems", "credits": 2, "lab": 1},
            {"name": "Data Mining", "credits": 2, "lab": 1},
            {"name": "Data Visualization", "credits": 2, "lab": 1}
        ]
        
        # Organize all courses by semester
        all_courses_by_semester = {
            1: semester1_courses,
            2: semester2_courses,
            3: semester3_courses,
            4: semester4_courses,
            5: semester5_courses
        }
        
        # Create all courses
        for semester_no, courses in all_courses_by_semester.items():
            print(f"\nCreating Semester {semester_no} courses:")
            semester_id = semester_ids[semester_no]
            
            for course_data in courses:
                course_name = course_data["name"]
                credits = course_data["credits"]
                has_lab = course_data["lab"] == 1
                
                # Create the theory course
                success, course_id = execute_query(
                    """
                    INSERT INTO Course (Name, Degree_ID, Semester_ID, CreditHours, IsLab)
                    VALUES (%s, %s, %s, %s, %s)
                    """,
                    (course_name, degree_id, semester_id, credits, False),
                    connection=conn
                )
                
                if success:
                    print(f"✓ Created course: {course_name}")
                    
                    # Assign a random instructor to the course
                    instructor_name = random.choice(list(instructor_ids.keys()))
                    instructor_id = instructor_ids[instructor_name]
                    
                    success, _ = execute_query(
                        "INSERT INTO Teaches (Instructor_ID, Course_ID) VALUES (%s, %s)",
                        (instructor_id, course_id),
                        connection=conn
                    )
                    
                    if not success:
                        print(f"❌ Failed to assign instructor to {course_name}")
                    
                    # If the course has a lab component, create it too
                    if has_lab:
                        lab_name = f"{course_name} (Lab)"
                        success, lab_id = execute_query(
                            """
                            INSERT INTO Course (Name, Degree_ID, Semester_ID, CreditHours, IsLab)
                            VALUES (%s, %s, %s, %s, %s)
                            """,
                            (lab_name, degree_id, semester_id, 1, True),
                            connection=conn
                        )
                        
                        if success:
                            print(f"✓ Created lab: {lab_name}")
                            
                            # Assign the same instructor to the lab
                            success, _ = execute_query(
                                "INSERT INTO Teaches (Instructor_ID, Course_ID) VALUES (%s, %s)",
                                (instructor_id, lab_id),
                                connection=conn
                            )
                            
                            if not success:
                                print(f"❌ Failed to assign instructor to {lab_name}")
                        else:
                            print(f"❌ Failed to create lab: {lab_name}")
                else:
                    print(f"❌ Failed to create course: {course_name}")
        
        # 6. Create time slots
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
                    print(f"❌ Failed to create time slot: {day} {start_time}-{end_time}")
        
        # Create admin account
        print("\nCreating admin account...")
        admin_password = hashlib.sha256("admin123".encode()).hexdigest()
        success, admin_id = execute_query(
            """
            INSERT INTO UserAccount (Name, Email, Role, PasswordHash)
            VALUES (%s, %s, %s, %s)
            """,
            ("SEECS Admin", "admin@seecs.edu.pk", "ADMIN", admin_password),
            connection=conn
        )
        
        if success:
            print(f"✓ Created admin: admin@seecs.edu.pk / admin123")
        else:
            print(f"❌ Failed to create admin account")
        
        print("\n✅ SEECS sample data initialization complete!")
        print("\nYou can now log in with:")
        print("  Admin: admin@seecs.edu.pk / admin123")
        print("\nInstructors:")
        for name, user_id in instructor_ids.items():
            email = random_email(name)
            print(f"  {name}: {email} / password123")
            
        return True
        
    except Exception as e:
        print(f"❌ Error during initialization: {e}")
        return False
    finally:
        if conn:
            conn.close()

if __name__ == "__main__":
    print("EduTime - SEECS AI Sample Data Initialization")
    print("--------------------------------------------")
    
    if len(sys.argv) > 1 and sys.argv[1] == "--force":
        initialize_seecs_data()
    else:
        print("⚠️ This script will add SEECS Artificial Intelligence sample data to the edutime_final database.")
        print("Make sure you have already run reset_database.py to create a clean database.")
        print("To proceed, run the script with the --force flag:")
        print("  python EduTime/seecs_sample_data.py --force") 