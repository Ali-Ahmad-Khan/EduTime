from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from utils.auth import admin_required
from db_config import get_connection
from logic.classroom_logic import generate_classrooms_for_existing, delete_room
from logic.degree_logic import insert_degree_with_semesters, delete_degree
from logic.course_logic import insert_bulk_courses, delete_course
from logic.instructor_logic import insert_instructor, delete_instructor, assign_course
from logic.department_logic import delete_department
from utils.helpers import render_selection_page

admin_bp = Blueprint('admin', __name__, url_prefix='/admin')

@admin_bp.route('/')
@admin_required
def home():
    return render_template('admin/home.html')

@admin_bp.route('/manage/departments', methods=['GET', 'POST'])
@admin_required
def manage_departments():
    if request.method == 'POST':
        prefix = request.form.get('prefix', '').strip().upper()
        name = request.form.get('name', '').strip()
        num_classrooms = request.form.get('num_classrooms', type=int, default=0)
        num_labs = request.form.get('num_labs', type=int, default=0)
        
        if prefix and name:
            try:
                conn = get_connection(); cur = conn.cursor()
                # Insert department
                cur.execute("INSERT INTO Department (Prefix, Name) VALUES (%s, %s)", (prefix, name))
                dept_id = cur.lastrowid
                conn.commit()
                cur.close(); conn.close()
                
                flash(f'Department {name} ({prefix}) added successfully', 'success')
                
                # Create venues if requested
                if num_classrooms > 0:
                    generate_classrooms_for_existing(dept_id, prefix, num_classrooms, 'CLASSROOM')
                    flash(f'Added {num_classrooms} classrooms for {prefix}', 'success')
                
                if num_labs > 0:
                    generate_classrooms_for_existing(dept_id, prefix, num_labs, 'LAB')
                    flash(f'Added {num_labs} labs for {prefix}', 'success')
                
            except Exception as e:
                flash(f'Error adding department: {str(e)}', 'error')
        else:
            flash('Department prefix and name are required', 'error')
            
        return redirect(url_for('admin.manage_departments'))
    
    conn = get_connection(); cur = conn.cursor()
    cur.execute("SELECT Department_ID, Prefix, Name FROM Department")
    departments = cur.fetchall()
    cur.close(); conn.close()
    return render_template('admin/manage_departments.html', departments=departments)

@admin_bp.post('/delete/dept/<int:dept_id>')
@admin_required
def delete_department_route(dept_id):
    delete_department(dept_id)
    flash('Department deleted successfully', 'success')
    return redirect(url_for('admin.manage_departments'))

@admin_bp.route('/api/semesters/<int:degree_id>')
@admin_required
def get_degree_semesters(degree_id):
    conn = get_connection(); cur = conn.cursor()
    cur.execute("""
        SELECT Semester_ID, Semester_No
        FROM Semester
        WHERE Degree_ID = %s
        ORDER BY Semester_No
    """, (degree_id,))
    semesters = [{'id': row[0], 'number': row[1]} for row in cur.fetchall()]
    cur.close(); conn.close()
    return jsonify(semesters)

@admin_bp.route('/setup/venues', methods=['GET', 'POST'])
@admin_required
def setup_venues():
    if request.method == 'POST':
        dept_id = request.form.get('department_id', type=int)
        room_prefix = request.form.get('room_prefix', '')
        num_rooms = request.form.get('num_rooms', type=int)
        room_type = request.form.get('room_type', '')
        
        if dept_id and num_rooms and room_type:
            # If room_prefix is not provided, get it from the department
            if not room_prefix:
                conn = get_connection(); cur = conn.cursor()
                cur.execute("SELECT Prefix FROM Department WHERE Department_ID = %s", (dept_id,))
                result = cur.fetchone()
                cur.close(); conn.close()
                
                if result:
                    room_prefix = result[0]
            
            # Generate the classrooms
            generate_classrooms_for_existing(dept_id, room_prefix, num_rooms, room_type)
            flash(f'{num_rooms} {room_type.lower()} rooms created successfully', 'success')
            return redirect(url_for('admin.manage_venues'))
        else:
            flash('Please fill in all required fields', 'error')
    
    # Get departments for the dropdown
    conn = get_connection(); cur = conn.cursor()
    cur.execute("SELECT Department_ID, Prefix, Name FROM Department ORDER BY Name")
    departments = cur.fetchall()
    cur.close(); conn.close()
    
    return render_template('admin/setup_venues.html', departments=departments)

@admin_bp.route('/manage/venues')
@admin_required
def manage_venues():
    conn = get_connection(); cur = conn.cursor()
    
    # Get departments with venue counts
    cur.execute("""
        SELECT d.Department_ID, d.Prefix, d.Name,
               COUNT(CASE WHEN r.RoomType = 'CLASSROOM' THEN 1 END) AS ClassroomCount,
               COUNT(CASE WHEN r.RoomType = 'LAB' THEN 1 END) AS LabCount
        FROM Department d
        LEFT JOIN Classroom r ON r.Department_ID = d.Department_ID
        GROUP BY d.Department_ID
        ORDER BY d.Name
    """)
    departments = cur.fetchall()
    
    # Join with Department to get department name for all venues
    cur.execute("""
        SELECT r.Room_ID, r.RoomNumber, r.RoomType, d.Name as DeptName, d.Department_ID
        FROM Classroom r
        JOIN Department d ON d.Department_ID = r.Department_ID
        ORDER BY d.Name, r.RoomType, r.RoomNumber
    """)
    rooms = cur.fetchall()
    cur.close(); conn.close()
    
    return render_template('admin/manage_venues.html', 
                          departments=departments,
                          rooms=rooms)

@admin_bp.post('/delete/room/<int:room_id>')
@admin_required
def delete_room_route(room_id):
    delete_room(room_id)
    flash('Room deleted successfully', 'success')
    return redirect(url_for('admin.manage_venues'))

@admin_bp.route('/setup/degrees', methods=['GET', 'POST'])
@admin_required
def setup_degrees():
    # ── POST: create degree + semesters ─────────────────────────────────────
    if request.method == 'POST':
        dept_id = request.form.get('department_id', type=int)
        degree_name = request.form.get('degree_name', '').strip()
        num_semesters = request.form.get('num_semesters', type=int)
        
        if dept_id and degree_name and num_semesters:
            try:
                conn = get_connection(); cur = conn.cursor()
                
                # Get department info
                cur.execute("SELECT Department_ID, Prefix FROM Department WHERE Department_ID = %s", (dept_id,))
                dept_result = cur.fetchone()
                
                if dept_result:
                    # Insert degree with semesters
                    cur.execute("INSERT INTO Degree (Name, Department_ID) VALUES (%s, %s)", 
                              (degree_name, dept_id))
                    degree_id = cur.lastrowid
                    
                    # Insert semesters
                    for sem_no in range(1, num_semesters + 1):
                        cur.execute("INSERT INTO Semester (Degree_ID, Semester_No) VALUES (%s, %s)", 
                                  (degree_id, sem_no))
                    
                    conn.commit()
                    flash(f'Degree "{degree_name}" with {num_semesters} semesters created successfully', 'success')
                else:
                    flash('Department not found', 'error')
                
                cur.close(); conn.close()
            except Exception as e:
                flash(f'Error creating degree: {str(e)}', 'error')
            
            return redirect(url_for('admin.manage_degrees'))
        else:
            flash('Please fill in all required fields', 'error')
    
    return render_selection_page('admin/setup_degrees.html')

@admin_bp.route('/manage/degrees')
@admin_required
def manage_degrees():
    conn = get_connection(); cur = conn.cursor()
    
    # Get degrees with their department and semester count
    cur.execute("""
        SELECT d.Degree_ID, d.Name, dp.Name as DeptName, dp.Prefix,
               COUNT(s.Semester_ID) as SemesterCount
        FROM Degree d
        JOIN Department dp ON dp.Department_ID = d.Department_ID
        LEFT JOIN Semester s ON s.Degree_ID = d.Degree_ID
        GROUP BY d.Degree_ID
        ORDER BY dp.Name, d.Name
    """)
    degrees = cur.fetchall()
    
    # For each degree, get course count
    for i, degree in enumerate(degrees):
        degree_id = degree[0]
        cur.execute("""
            SELECT COUNT(c.Course_ID)
            FROM Course c
            WHERE c.Degree_ID = %s
        """, (degree_id,))
        course_count = cur.fetchone()[0]
        degrees[i] = degrees[i] + (course_count,)
    
    cur.close(); conn.close()
    
    return render_template('admin/manage_degrees.html', degrees=degrees)

@admin_bp.post('/delete/degree/<int:degree_id>')
@admin_required
def delete_degree_route(degree_id):
    delete_degree(degree_id)
    flash('Degree deleted successfully', 'success')
    return redirect(url_for('admin.manage_degrees'))

@admin_bp.route('/setup/courses', methods=['GET', 'POST'])
@admin_required
def setup_courses():
    if request.method == 'POST':
        degree_id = request.form.get('degree_id', type=int)
        semester_id = request.form.get('semester_id', type=int)
        
        # Process course data
        course_names = request.form.getlist('course_name[]')
        course_credits = request.form.getlist('course_credits[]')
        has_labs = request.form.getlist('has_lab[]')  # Will contain values for checked boxes only
        
        if degree_id and semester_id and course_names and course_credits:
            courses = []
            
            # Process each course
            for i in range(len(course_names)):
                if course_names[i].strip():  # Skip empty course names
                    # Get credit hours
                    credits = int(course_credits[i]) if i < len(course_credits) else 3
                    
                    # Add the lecture course
                    courses.append({
                        "name": course_names[i],
                        "credits": credits,
                        "is_lab": False
                    })
                    
                    # Check if this course has a lab
                    course_index = str(i)
                    if course_index in has_labs or str(1) in has_labs:
                        # Add the lab course with 1 credit hour
                        courses.append({
                            "name": f"{course_names[i]} Lab",
                            "credits": 1,
                            "is_lab": True
                        })
            
            if courses:
                insert_bulk_courses(degree_id, semester_id, courses)
                flash(f'{len(courses)} courses added successfully', 'success')
                return redirect(url_for('admin.manage_courses'))
            else:
                flash('No valid courses provided', 'error')
        else:
            flash('Please fill in all required fields', 'error')
    
    # Get departments for the dropdown
    conn = get_connection(); cur = conn.cursor()
    cur.execute("SELECT Department_ID, Prefix, Name FROM Department ORDER BY Name")
    departments = cur.fetchall()
    
    # Get all degrees with their department IDs
    cur.execute("""
        SELECT d.Degree_ID, d.Name, dp.Prefix, d.Department_ID
        FROM Degree d
        JOIN Department dp ON dp.Department_ID = d.Department_ID
        ORDER BY dp.Name, d.Name
    """)
    degrees = cur.fetchall()
    cur.close(); conn.close()
    
    return render_template('admin/setup_courses.html', 
                          departments=departments,
                          degrees=degrees)

@admin_bp.route('/manage/courses')
@admin_required
def manage_courses():
    conn = get_connection(); cur = conn.cursor()
    
    # Get all departments for filtering
    cur.execute("SELECT Department_ID, Prefix, Name FROM Department ORDER BY Name")
    departments = cur.fetchall()
    
    # Get all degrees with their department IDs for filtering
    cur.execute("""
        SELECT d.Degree_ID, d.Name, dp.Prefix, d.Department_ID
        FROM Degree d
        JOIN Department dp ON dp.Department_ID = d.Department_ID
        ORDER BY dp.Name, d.Name
    """)
    degrees = cur.fetchall()
    
    # Get all courses with their degree and semester info
    cur.execute("""
        SELECT c.Course_ID, c.Name, c.CreditHours, c.IsLab,
               d.Name as DegreeName, s.Semester_No, dp.Prefix,
               COUNT(t.Instructor_ID) as InstructorCount,
               dp.Department_ID, d.Degree_ID
        FROM Course c
        JOIN Degree d ON d.Degree_ID = c.Degree_ID
        JOIN Semester s ON s.Semester_ID = c.Semester_ID
        JOIN Department dp ON dp.Department_ID = d.Department_ID
        LEFT JOIN Teaches t ON t.Course_ID = c.Course_ID
        GROUP BY c.Course_ID
        ORDER BY dp.Prefix, d.Name, s.Semester_No, c.Name
    """)
    courses = cur.fetchall()
    
    cur.close(); conn.close()
    
    return render_template('admin/manage_courses.html', 
                          courses=courses,
                          departments=departments,
                          degrees=degrees)

@admin_bp.post('/delete/course/<int:course_id>')
@admin_required
def delete_course_route(course_id):
    delete_course(course_id)
    flash('Course deleted successfully', 'success')
    return redirect(url_for('admin.manage_courses'))

@admin_bp.route('/setup/instructors', methods=['GET', 'POST'])
@admin_required
def setup_instructors():
    if request.method == 'POST':
        name = request.form.get('name', '')
        email = request.form.get('email', '')
        dept_prefix = request.form.get('dept_prefix', '')
        
        if name and email and dept_prefix:
            instructor_id, message = insert_instructor(name, email, dept_prefix)
            if instructor_id:
                flash(f'Instructor {name} added successfully. An email has been sent for account setup.', 'success')
            else:
                flash(message, 'error')
            return redirect(url_for('admin.manage_instructors'))
        else:
            flash('Please fill in all required fields', 'error')
    
    return render_selection_page('admin/setup_instructors.html')

@admin_bp.route('/manage/instructors')
@admin_required
def manage_instructors():
    conn = get_connection(); cur = conn.cursor()
    
    # Get all instructors with their department info
    cur.execute("""
        SELECT i.Instructor_ID, u.Name, u.Email, d.Name as DeptName, d.Prefix
        FROM Instructor i
        JOIN UserAccount u ON u.User_ID = i.User_ID
        JOIN Department d ON d.Department_ID = i.Department_ID
        ORDER BY d.Name, u.Name
    """)
    instructors = cur.fetchall()
    
    # For each instructor, get course count
    for i, instructor in enumerate(instructors):
        instructor_id = instructor[0]
        cur.execute("""
            SELECT COUNT(t.Course_ID)
            FROM Teaches t
            WHERE t.Instructor_ID = %s
        """, (instructor_id,))
        course_count = cur.fetchone()[0]
        
        # Check if the instructor has completed registration
        cur.execute("""
            SELECT PasswordHash != 'hashed'
            FROM UserAccount
            WHERE User_ID = %s
        """, (instructor_id,))
        registration_completed = cur.fetchone()[0]
        
        instructors[i] = instructors[i] + (course_count, registration_completed)
    
    cur.close(); conn.close()
    
    return render_template('admin/manage_instructors.html', instructors=instructors)

@admin_bp.post('/delete/instructor/<int:instructor_id>')
@admin_required
def delete_instructor_route(instructor_id):
    delete_instructor(instructor_id)
    flash('Instructor deleted successfully', 'success')
    return redirect(url_for('admin.manage_instructors'))

@admin_bp.route('/setup/assign-courses', methods=['GET', 'POST'])
@admin_required
def assign_courses():
    if request.method == 'POST':
        instructor_id = request.form.get('instructor_id', type=int)
        course_ids = request.form.getlist('course_ids')
        course_id = request.form.get('course_id', type=int)
        
        if instructor_id and course_ids:
            for course_id in course_ids:
                assign_course(instructor_id, int(course_id))
            
            flash(f'{len(course_ids)} courses assigned successfully', 'success')
            return redirect(url_for('admin.manage_instructors'))
        elif instructor_id and course_id:
            assign_course(instructor_id, course_id)
            flash('Course assigned successfully', 'success')
            return redirect(url_for('admin.manage_courses'))
        else:
            flash('Please select an instructor and at least one course', 'error')
    
    # Get all instructors
    conn = get_connection(); cur = conn.cursor()
    cur.execute("""
        SELECT i.Instructor_ID, u.Name, d.Name as DeptName, d.Prefix
        FROM Instructor i
        JOIN UserAccount u ON u.User_ID = i.User_ID
        JOIN Department d ON d.Department_ID = i.Department_ID
        ORDER BY d.Name, u.Name
    """)
    instructors = cur.fetchall()
    
    # Get all courses
    cur.execute("""
        SELECT c.Course_ID, c.Name, c.CreditHours, c.IsLab,
               d.Name as DegreeName, s.Semester_No, dp.Prefix,
               d.Department_ID
        FROM Course c
        JOIN Degree d ON d.Degree_ID = c.Degree_ID
        JOIN Semester s ON s.Semester_ID = c.Semester_ID
        JOIN Department dp ON dp.Department_ID = d.Department_ID
        ORDER BY dp.Prefix, d.Name, s.Semester_No, c.Name
    """)
    all_courses = cur.fetchall()
    
    # If instructor is selected, get their department and already assigned courses
    selected_instructor_id = request.args.get('instructor_id', type=int)
    instructor_dept_id = None
    assigned_course_ids = []
    instructor = None
    
    if selected_instructor_id:
        cur.execute("""
            SELECT i.Instructor_ID, u.Name, u.Email, d.Name, d.Prefix
            FROM Instructor i
            JOIN UserAccount u ON u.User_ID = i.User_ID
            JOIN Department d ON d.Department_ID = i.Department_ID
            WHERE i.Instructor_ID = %s
        """, (selected_instructor_id,))
        instructor = cur.fetchone()
        
        if instructor:
            cur.execute("""
                SELECT d.Department_ID
                FROM Instructor i
                JOIN Department d ON d.Department_ID = i.Department_ID
                WHERE i.Instructor_ID = %s
            """, (selected_instructor_id,))
            row = cur.fetchone()
            if row:
                instructor_dept_id = row[0]
            
            cur.execute("""
                SELECT t.Course_ID
                FROM Teaches t
                WHERE t.Instructor_ID = %s
            """, (selected_instructor_id,))
            assigned_course_ids = [row[0] for row in cur.fetchall()]
    
    # If course is selected, get its details and assigned instructor
    selected_course_id = request.args.get('course_id', type=int)
    course = None
    assigned_instructor_id = None
    available_instructors = []
    
    if selected_course_id:
        cur.execute("""
            SELECT c.Course_ID, c.Name, c.CreditHours, c.IsLab,
                   d.Name, s.Semester_No, dp.Prefix, dp.Department_ID
            FROM Course c
            JOIN Degree d ON d.Degree_ID = c.Degree_ID
            JOIN Semester s ON s.Semester_ID = c.Semester_ID
            JOIN Department dp ON dp.Department_ID = d.Department_ID
            WHERE c.Course_ID = %s
        """, (selected_course_id,))
        course = cur.fetchone()
        
        if course:
            # Get department ID from course
            dept_id = course[7]
            
            # Get instructors from this department
            cur.execute("""
                SELECT i.Instructor_ID, u.Name, u.Email, d.Name, d.Prefix
                FROM Instructor i
                JOIN UserAccount u ON u.User_ID = i.User_ID
                JOIN Department d ON d.Department_ID = i.Department_ID
                WHERE d.Department_ID = %s
                ORDER BY u.Name
            """, (dept_id,))
            available_instructors = cur.fetchall()
            
            # Check if course is already assigned
            cur.execute("""
                SELECT t.Instructor_ID
                FROM Teaches t
                WHERE t.Course_ID = %s
                LIMIT 1
            """, (selected_course_id,))
            row = cur.fetchone()
            if row:
                assigned_instructor_id = row[0]
    
    # Filter courses for selected instructor
    available_courses = []
    if instructor_dept_id:
        available_courses = [c for c in all_courses if c[7] == instructor_dept_id]
    
    cur.close(); conn.close()
    
    return render_template('admin/assign_courses.html',
                          instructors=instructors,
                          all_courses=all_courses,
                          selected_instructor_id=selected_instructor_id,
                          instructor_dept_id=instructor_dept_id,
                          assigned_course_ids=assigned_course_ids,
                          instructor=instructor,
                          course=course,
                          available_instructors=available_instructors,
                          available_courses=available_courses,
                          assigned_instructor_id=assigned_instructor_id)

@admin_bp.route('/setup/initial-data')
@admin_required
def setup_initial_data():
    """Quick setup of initial data for testing"""
    from logic.department_logic import get_or_create_department
    
    # Create departments
    cs_id = get_or_create_department('CS', 'Computer Science')
    ee_id = get_or_create_department('EE', 'Electrical Engineering')
    
    # Create degrees with semesters - passing dept_id directly
    cs_degree_id = insert_degree_with_semesters(cs_id, 'BS Computer Science', 8)
    ee_degree_id = insert_degree_with_semesters(ee_id, 'BS Electrical Engineering', 8)
    
    # Get semester IDs
    conn = get_connection(); cur = conn.cursor()
    cur.execute("SELECT Semester_ID FROM Semester WHERE Degree_ID = %s AND Semester_No = 1", (cs_degree_id,))
    cs_sem1_id = cur.fetchone()[0]
    
    cur.execute("SELECT Semester_ID FROM Semester WHERE Degree_ID = %s AND Semester_No = 1", (ee_degree_id,))
    ee_sem1_id = cur.fetchone()[0]
    
    # Create sample courses
    cs_courses = [
        {"name": "Programming Fundamentals", "credits": 3, "is_lab": False},
        {"name": "Programming Fundamentals Lab", "credits": 1, "is_lab": True},
        {"name": "Calculus I", "credits": 3, "is_lab": False},
        {"name": "Digital Logic Design", "credits": 3, "is_lab": False},
        {"name": "Digital Logic Design Lab", "credits": 1, "is_lab": True}
    ]
    
    ee_courses = [
        {"name": "Circuit Analysis", "credits": 3, "is_lab": False},
        {"name": "Circuit Analysis Lab", "credits": 1, "is_lab": True},
        {"name": "Calculus I", "credits": 3, "is_lab": False},
        {"name": "Engineering Drawing", "credits": 2, "is_lab": True}
    ]
    
    insert_bulk_courses(cs_degree_id, cs_sem1_id, cs_courses)
    insert_bulk_courses(ee_degree_id, ee_sem1_id, ee_courses)
    
    # Create classrooms
    generate_classrooms_for_existing(cs_id, 'CS', 5, 'CLASSROOM')
    generate_classrooms_for_existing(cs_id, 'CS', 3, 'LAB')
    generate_classrooms_for_existing(ee_id, 'EE', 5, 'CLASSROOM')
    generate_classrooms_for_existing(ee_id, 'EE', 3, 'LAB')
    
    # Create instructors
    insert_instructor('John Smith', 'john.smith@example.com', 'CS')
    insert_instructor('Jane Doe', 'jane.doe@example.com', 'EE')
    
    cur.close(); conn.close()
    
    flash('Initial test data created successfully', 'success')
    return redirect(url_for('admin.home'))

@admin_bp.route('/venues/by-department/<int:dept_id>')
@admin_required
def venues_by_department(dept_id):
    conn = get_connection(); cur = conn.cursor()
    
    # Get department info
    cur.execute("SELECT Department_ID, Prefix, Name FROM Department WHERE Department_ID = %s", (dept_id,))
    department = cur.fetchone()
    
    if not department:
        flash('Department not found', 'error')
        return redirect(url_for('admin.manage_venues'))
    
    # Get venues for this department
    cur.execute("""
        SELECT r.Room_ID, r.RoomNumber, r.RoomType
        FROM Classroom r
        WHERE r.Department_ID = %s
        ORDER BY r.RoomType, r.RoomNumber
    """, (dept_id,))
    rooms = cur.fetchall()
    
    cur.close(); conn.close()
    
    return render_template('admin/venues_by_department.html', 
                          department=department,
                          rooms=rooms)

@admin_bp.route('/venues/add/<int:dept_id>', methods=['POST'])
@admin_required
def add_venues_to_department(dept_id):
    num_rooms = request.form.get('num_rooms', type=int, default=1)
    room_type = request.form.get('room_type', '')
    
    # Validate input
    if not num_rooms or num_rooms < 1 or not room_type:
        flash('Invalid input. Please specify number of rooms and room type.', 'error')
        return redirect(url_for('admin.venues_by_department', dept_id=dept_id))
    
    # Get department prefix
    conn = get_connection(); cur = conn.cursor()
    cur.execute("SELECT Prefix FROM Department WHERE Department_ID = %s", (dept_id,))
    result = cur.fetchone()
    cur.close(); conn.close()
    
    if not result:
        flash('Department not found', 'error')
        return redirect(url_for('admin.manage_venues'))
    
    prefix = result[0]
    
    # Generate rooms
    generate_classrooms_for_existing(dept_id, prefix, num_rooms, room_type)
    
    flash(f'Added {num_rooms} {room_type.lower()} venues to department', 'success')
    return redirect(url_for('admin.venues_by_department', dept_id=dept_id)) 