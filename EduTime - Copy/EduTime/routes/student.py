from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from utils.auth import student_required
from db_config import get_connection
from utils.helpers import get_degrees_with_semesters
from logic.instructor_logic import ensure_ali_ahmad_khan_exists

student_bp = Blueprint('student', __name__, url_prefix='/student')

@student_bp.route('/home')
@student_required
def home():
    conn = get_connection(); cur = conn.cursor()
    
    # Ensure Ali Ahmad Khan exists
    ensure_ali_ahmad_khan_exists()
    
    # Get student information
    student_id = session['user_id']
    
    # Get all degrees for timetable viewing
    degrees = get_degrees_with_semesters()
    
    # Get instructors for appointment scheduling
    cur.execute("""
        SELECT u.User_ID, u.Name, COALESCE(d.Name, 'Unknown Department') as DepartmentName
        FROM UserAccount u
        LEFT JOIN Instructor i ON u.User_ID = i.User_ID
        LEFT JOIN Department d ON i.Department_ID = d.Department_ID
        WHERE u.Role = 'INSTRUCTOR'
        ORDER BY u.Name
    """)
    instructors = cur.fetchall()
    
    # Debug: Print instructors to console
    print("Available Instructors for Appointments:")
    for instructor in instructors:
        print(f"ID: {instructor[0]}, Name: {instructor[1]}, Department: {instructor[2]}")
    
    # Special debug for Ali Ahmad Khan
    cur.execute("SELECT * FROM UserAccount WHERE Name = 'Ali Ahmad Khan'")
    ali_info = cur.fetchone()
    if ali_info:
        print(f"Ali Ahmad Khan found in UserAccount: {ali_info}")
        
        cur.execute("SELECT * FROM Instructor WHERE User_ID = %s", (ali_info[0],))
        ali_instructor = cur.fetchone()
        print(f"Ali Ahmad Khan instructor record: {ali_instructor}")
    else:
        print("Ali Ahmad Khan not found in UserAccount!")
    
    # Get student's appointments
    cur.execute("""
        SELECT a.Appointment_ID, u.Name as InstructorName, a.ApptDate, 
               a.StartTime, a.EndTime, a.Purpose, a.Status
        FROM Appointment a
        JOIN Instructor i ON i.Instructor_ID = a.Instructor_ID
        JOIN UserAccount u ON u.User_ID = i.User_ID
        WHERE a.Student_ID = %s
        ORDER BY a.Status, a.ApptDate, a.StartTime
    """, (student_id,))
    appointments = cur.fetchall()
    
    cur.close(); conn.close()
    
    return render_template('student/home.html',
                          student_name=session['name'],
                          degrees=degrees,
                          instructors=instructors,
                          appointments=appointments)

@student_bp.route('/appointments/request', methods=['POST'])
@student_required
def request_appointment():
    student_id = session['user_id']
    instructor_id = request.form.get('instructor_id', type=int)
    appt_date = request.form.get('appt_date', '')
    start_time = request.form.get('start_time', '')
    end_time = request.form.get('end_time', '')
    purpose = request.form.get('purpose', '')
    
    if not instructor_id or not appt_date or not start_time or not end_time:
        flash('Please fill in all required fields', 'error')
        return redirect(url_for('student.home'))
    
    conn = get_connection(); cur = conn.cursor()
    
    # Check if instructor_id exists in Instructor table
    cur.execute("SELECT 1 FROM Instructor WHERE Instructor_ID = %s", (instructor_id,))
    instructor_exists = cur.fetchone() is not None
    
    # If the instructor doesn't exist in the Instructor table but exists in UserAccount
    if not instructor_exists:
        print(f"Instructor {instructor_id} not found in Instructor table. Checking UserAccount...")
        
        # Check if it's a User_ID from UserAccount
        cur.execute("SELECT 1 FROM UserAccount WHERE User_ID = %s AND Role = 'INSTRUCTOR'", (instructor_id,))
        is_instructor_user = cur.fetchone() is not None
        
        if is_instructor_user:
            print(f"User {instructor_id} is an instructor in UserAccount but not in Instructor table. Adding...")
            
            # Find a department
            cur.execute("SELECT Department_ID FROM Department LIMIT 1")
            dept_result = cur.fetchone()
            
            if dept_result:
                dept_id = dept_result[0]
                
                # Add to Instructor table
                try:
                    cur.execute("""
                        INSERT INTO Instructor (Instructor_ID, User_ID, Department_ID)
                        VALUES (%s, %s, %s)
                    """, (instructor_id, instructor_id, dept_id))
                    conn.commit()
                    print(f"Added User {instructor_id} to Instructor table successfully")
                except Exception as e:
                    print(f"Error adding to Instructor table: {str(e)}")
                    flash('Error processing instructor. Please try again later.', 'error')
                    return redirect(url_for('student.home'))
            else:
                flash('No departments available for instructor assignment', 'error')
                return redirect(url_for('student.home'))
        else:
            flash('Invalid instructor selected', 'error')
            return redirect(url_for('student.home'))
    
    # Insert appointment
    cur.execute("""
        INSERT INTO Appointment 
        (Student_ID, Instructor_ID, ApptDate, StartTime, EndTime, Purpose, Status)
        VALUES (%s, %s, %s, %s, %s, %s, 'PENDING')
    """, (student_id, instructor_id, appt_date, start_time, end_time, purpose))
    
    conn.commit()
    cur.close(); conn.close()
    
    flash('Appointment request submitted successfully', 'success')
    return redirect(url_for('student.home'))

@student_bp.route('/appointments/respond', methods=['POST'])
@student_required
def respond_to_appointment():
    student_id = session['user_id']
    appointment_id = request.form.get('appointment_id', type=int)
    response = request.form.get('response', '')
    
    if not appointment_id or not response:
        flash('Invalid request', 'error')
        return redirect(url_for('student.home'))
    
    conn = get_connection(); cur = conn.cursor()
    
    # Verify this appointment belongs to this student
    cur.execute("""
        SELECT 1 FROM Appointment 
        WHERE Appointment_ID = %s AND Student_ID = %s AND Status = 'COUNTER_PROPOSED'
    """, (appointment_id, student_id))
    
    if not cur.fetchone():
        flash('Appointment not found or does not belong to you', 'error')
        cur.close(); conn.close()
        return redirect(url_for('student.home'))
    
    # Update appointment status
    if response == 'accept':
        cur.execute("""
            UPDATE Appointment SET Status = 'CONFIRMED'
            WHERE Appointment_ID = %s
        """, (appointment_id,))
        flash('Counter proposal accepted', 'success')
    elif response == 'reject':
        cur.execute("""
            UPDATE Appointment SET Status = 'REJECTED'
            WHERE Appointment_ID = %s
        """, (appointment_id,))
        flash('Counter proposal rejected', 'success')
    
    conn.commit()
    cur.close(); conn.close()
    
    return redirect(url_for('student.home')) 