from db_config import get_connection

# --------- ADD instructor ------------------------------------------------
def insert_instructor(full_name: str, email: str, dept_prefix: str):
    from logic.department_logic import get_or_create_department
    
    # Get the department ID by prefix
    conn = get_connection(); cur = conn.cursor()
    cur.execute("SELECT Department_ID FROM Department WHERE Prefix = %s", (dept_prefix,))
    result = cur.fetchone()
    
    if result:
        dept_id = result[0]
    else:
        # Department doesn't exist
        cur.close(); conn.close()
        return None, f"Department with prefix '{dept_prefix}' not found"
    
    # Check if email already exists
    cur.execute("SELECT 1 FROM UserAccount WHERE Email = %s", (email,))
    if cur.fetchone():
        cur.close(); conn.close()
        return None, "Email already registered"
    
    # UserAccount
    cur.execute("""
        INSERT INTO UserAccount (Name, Email, Role, PasswordHash)
        VALUES (%s,%s,'INSTRUCTOR','hashed')
    """, (full_name, email))
    user_id = cur.lastrowid
    
    # Instructor
    cur.execute("""
        INSERT INTO Instructor (Instructor_ID, User_ID, Department_ID)
        VALUES (%s,%s,%s)
    """, (user_id, user_id, dept_id))
    conn.commit(); cur.close(); conn.close()
    
    # Send welcome email
    try:
        from utils.email import send_welcome_email
        email_sent = send_welcome_email(email, 'INSTRUCTOR')
        if not email_sent:
            print(f"Warning: Failed to send welcome email to {email}")
    except Exception as e:
        print(f"Error sending welcome email: {str(e)}")
    
    return user_id, "Instructor created successfully"



# --------- DELETE instructor --------------------------------------------
def delete_instructor(instructor_id: int):
    conn = get_connection(); cur = conn.cursor()
    
    # First get the User_ID from the Instructor table
    cur.execute("SELECT User_ID FROM Instructor WHERE Instructor_ID=%s", (instructor_id,))
    result = cur.fetchone()
    
    if result:
        user_id = result[0]
        
        # Delete from Instructor table first
        cur.execute("DELETE FROM Instructor WHERE Instructor_ID=%s", (instructor_id,))
        
        # Then delete from UserAccount table
        cur.execute("DELETE FROM UserAccount WHERE User_ID=%s", (user_id,))
        
        conn.commit()
    
    cur.close(); conn.close()


# --------- ASSIGN courses -----------------------------------------------
def assign_course(instructor_id: int, course_id: int):
    conn = get_connection(); cur = conn.cursor()
    cur.execute("""
        INSERT IGNORE INTO Teaches (Instructor_ID, Course_ID)
        VALUES (%s,%s)
    """, (instructor_id, course_id))
    conn.commit(); cur.close(); conn.close()

# --------- GET instructor -----------------------------------------------
def get_instructor(instructor_id: int):
    conn = get_connection(); cur = conn.cursor()
    cur.execute("""
        SELECT i.Instructor_ID, u.Name, u.Email, d.Prefix, d.Name
        FROM Instructor i
        JOIN UserAccount u ON u.User_ID = i.User_ID
        JOIN Department d ON d.Department_ID = i.Department_ID
        WHERE i.Instructor_ID = %s
    """, (instructor_id,))
    result = cur.fetchone()
    cur.close(); conn.close()
    return result

# --------- GET ALL instructors ------------------------------------------
def get_all_instructors():
    conn = get_connection(); cur = conn.cursor()
    cur.execute("""
        SELECT i.Instructor_ID, u.Name, u.Email, d.Prefix, d.Name
        FROM Instructor i
        JOIN UserAccount u ON u.User_ID = i.User_ID
        JOIN Department d ON d.Department_ID = i.Department_ID
        ORDER BY u.Name
    """)
    result = cur.fetchall()
    cur.close(); conn.close()
    return result

# --------- Check and add Ali Ahmad Khan if not exist -----------------------
def ensure_ali_ahmad_khan_exists():
    conn = get_connection(); cur = conn.cursor()
    
    # Check if Ali Ahmad Khan exists in UserAccount
    cur.execute("SELECT User_ID FROM UserAccount WHERE Name = 'Ali Ahmad Khan'")
    user_result = cur.fetchone()
    
    if user_result:
        user_id = user_result[0]
        print(f"Found Ali Ahmad Khan in UserAccount with ID {user_id}")
        
        # Check if he exists in Instructor table
        cur.execute("SELECT Instructor_ID FROM Instructor WHERE User_ID = %s", (user_id,))
        instructor_result = cur.fetchone()
        
        if not instructor_result:
            # He exists in UserAccount but not in Instructor - add him to Instructor table
            print(f"Ali Ahmad Khan exists as user but not as instructor. Adding to Instructor table.")
            
            # Find a department
            cur.execute("SELECT Department_ID FROM Department LIMIT 1")
            dept_result = cur.fetchone()
            
            if dept_result:
                dept_id = dept_result[0]
                
                # Insert as instructor, using the existing user_id
                cur.execute("""
                    INSERT INTO Instructor (Instructor_ID, User_ID, Department_ID)
                    VALUES (%s, %s, %s)
                """, (user_id, user_id, dept_id))
                
                conn.commit()
                print(f"Added Ali Ahmad Khan to Instructor table with ID {user_id}")
                
                # Verify the entry was added
                cur.execute("SELECT * FROM Instructor WHERE User_ID = %s", (user_id,))
                print(f"Verification: {cur.fetchone()}")
                
                return True
            else:
                print("Could not add Ali Ahmad Khan as instructor: No departments found")
                return False
        else:
            print(f"Ali Ahmad Khan already exists as instructor with ID {instructor_result[0]}")
            return True
    else:
        # Ali Ahmad Khan doesn't exist in UserAccount - create him
        # Find a department for Ali Ahmad Khan
        cur.execute("SELECT Department_ID, Prefix FROM Department LIMIT 1")
        dept_result = cur.fetchone()
        
        if dept_result:
            dept_id = dept_result[0]
            dept_prefix = dept_result[1]
            
            # Insert Ali Ahmad Khan as user - using ID 37 if available
            try:
                cur.execute("""
                    INSERT INTO UserAccount (User_ID, Name, Email, Role, PasswordHash)
                    VALUES (37, 'Ali Ahmad Khan', 'akhan.bsai2@seecs.edu.pk', 'INSTRUCTOR', 'ef92b778bafe771e89245b89ecbc08a44a4e166c0665991188')
                """)
                user_id = 37
            except Exception as e:
                # If ID 37 is already taken, let MySQL auto-increment
                print(f"Could not use ID 37: {str(e)}")
                cur.execute("""
                    INSERT INTO UserAccount (Name, Email, Role, PasswordHash)
                    VALUES ('Ali Ahmad Khan', 'akhan.bsai2@seecs.edu.pk', 'INSTRUCTOR', 'ef92b778bafe771e89245b89ecbc08a44a4e166c0665991188')
                """)
                user_id = cur.lastrowid
            
            # Insert as instructor
            cur.execute("""
                INSERT INTO Instructor (Instructor_ID, User_ID, Department_ID)
                VALUES (%s, %s, %s)
            """, (user_id, user_id, dept_id))
            
            conn.commit()
            print(f"Added Ali Ahmad Khan as user and instructor with ID {user_id}")
            return True
        else:
            print("Could not add Ali Ahmad Khan: No departments found")
            return False
    
    cur.close(); conn.close()
