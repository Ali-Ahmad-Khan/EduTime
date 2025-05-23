from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from utils.auth import instructor_required
from db_config import get_connection
from utils.helpers import get_degrees_with_semesters

instructor_bp = Blueprint('instructor', __name__, url_prefix='/instructor')

@instructor_bp.route('/home')
@instructor_required
def home():
    conn = get_connection(); cur = conn.cursor()
    
    # Get instructor information
    instructor_id = session['user_id']
    cur.execute("""
        SELECT i.Department_ID, d.Name, d.Prefix 
        FROM Instructor i
        JOIN Department d ON d.Department_ID = i.Department_ID
        WHERE i.Instructor_ID = %s
    """, (instructor_id,))
    dept_info = cur.fetchone()
    
    # Get courses taught by this instructor
    cur.execute("""
        SELECT c.Course_ID, c.Name, d.Name as DegreeName, s.Semester_No
        FROM Teaches t
        JOIN Course c ON c.Course_ID = t.Course_ID
        JOIN Semester s ON s.Semester_ID = c.Semester_ID
        JOIN Degree d ON d.Degree_ID = c.Degree_ID
        WHERE t.Instructor_ID = %s
        ORDER BY d.Name, s.Semester_No, c.Name
    """, (instructor_id,))
    courses = cur.fetchall()
    
    # Get pending appointments
    cur.execute("""
        SELECT a.Appointment_ID, u.Name as StudentName, a.ApptDate, 
               a.StartTime, a.EndTime, a.Purpose, a.Status
        FROM Appointment a
        JOIN Student s ON s.Student_ID = a.Student_ID
        JOIN UserAccount u ON u.User_ID = s.User_ID
        WHERE a.Instructor_ID = %s AND a.Status = 'PENDING'
        ORDER BY a.ApptDate, a.StartTime
    """, (instructor_id,))
    pending_appointments = cur.fetchall()
    
    # Get upcoming confirmed appointments
    cur.execute("""
        SELECT a.Appointment_ID, u.Name as StudentName, a.ApptDate, 
               a.StartTime, a.EndTime, a.Purpose
        FROM Appointment a
        JOIN Student s ON s.Student_ID = a.Student_ID
        JOIN UserAccount u ON u.User_ID = s.User_ID
        WHERE a.Instructor_ID = %s AND a.Status = 'CONFIRMED'
              AND (a.ApptDate > CURDATE() OR 
                   (a.ApptDate = CURDATE() AND a.StartTime >= CURTIME()))
        ORDER BY a.ApptDate, a.StartTime
    """, (instructor_id,))
    upcoming_appointments = cur.fetchall()
    
    cur.close(); conn.close()
    
    return render_template('instructor/home.html',
                          instructor_name=session['name'],
                          department=dept_info,
                          courses=courses,
                          pending_appointments=pending_appointments,
                          upcoming_appointments=upcoming_appointments)

@instructor_bp.route('/schedules')
@instructor_required
def view_schedules():
    instructor_id = session['user_id']
    conn = get_connection(); cur = conn.cursor()
    
    # Get instructor's department
    cur.execute("""
        SELECT d.Department_ID, d.Name, d.Prefix 
        FROM Instructor i
        JOIN Department d ON d.Department_ID = i.Department_ID
        WHERE i.Instructor_ID = %s
    """, (instructor_id,))
    dept_info = cur.fetchone()
    
    # Get all courses taught by this instructor
    cur.execute("""
        SELECT c.Course_ID, c.Name, d.Degree_ID, d.Name as DegreeName, 
               s.Semester_ID, s.Semester_No
        FROM Teaches t
        JOIN Course c ON c.Course_ID = t.Course_ID
        JOIN Semester s ON s.Semester_ID = c.Semester_ID
        JOIN Degree d ON d.Degree_ID = c.Degree_ID
        WHERE t.Instructor_ID = %s
        ORDER BY d.Name, s.Semester_No, c.Name
    """, (instructor_id,))
    courses = cur.fetchall()
    
    # Get unique degrees and semesters from the instructor's courses
    degrees = {}
    for _, _, degree_id, degree_name, semester_id, semester_no in courses:
        if degree_id not in degrees:
            degrees[degree_id] = {
                'name': degree_name,
                'semesters': set()
            }
        degrees[degree_id]['semesters'].add(semester_no)
    
    # Convert sets to sorted lists
    for degree_id in degrees:
        degrees[degree_id]['semesters'] = sorted(list(degrees[degree_id]['semesters']))
    
    # Get instructor's schedule
    cur.execute("""
        SELECT cs.Schedule_ID, c.Name as CourseName, c.IsLab,
               r.RoomNumber, ts.Day, ts.Slot_No, ts.StartTime, ts.EndTime,
               d.Name as DegreeName, s.Semester_No
        FROM ClassSchedule cs
        JOIN Course c ON c.Course_ID = cs.Course_ID
        JOIN Classroom r ON r.Room_ID = cs.Room_ID
        JOIN TimeSlot ts ON ts.TimeSlot_ID = cs.TimeSlot_ID
        JOIN Semester s ON s.Semester_ID = cs.Semester_ID
        JOIN Degree d ON d.Degree_ID = c.Degree_ID
        WHERE cs.Instructor_ID = %s
        ORDER BY ts.Day, ts.Slot_No
    """, (instructor_id,))
    schedule_items = cur.fetchall()
    
    cur.close(); conn.close()
    
    return render_template('instructor/schedules.html',
                          instructor_name=session['name'],
                          department=dept_info,
                          degrees=degrees,
                          schedule_items=schedule_items)

@instructor_bp.route('/appointments/respond', methods=['POST'])
@instructor_required
def respond_to_appointment():
    instructor_id = session['user_id']
    appointment_id = request.form.get('appointment_id', type=int)
    response = request.form.get('response', '')
    
    if not appointment_id or not response:
        flash('Invalid request', 'error')
        return redirect(url_for('instructor.home'))
    
    conn = get_connection(); cur = conn.cursor()
    
    # Verify this appointment belongs to this instructor
    cur.execute("""
        SELECT 1 FROM Appointment 
        WHERE Appointment_ID = %s AND Instructor_ID = %s
    """, (appointment_id, instructor_id))
    
    if not cur.fetchone():
        flash('Appointment not found or does not belong to you', 'error')
        cur.close(); conn.close()
        return redirect(url_for('instructor.home'))
    
    # Update appointment status
    if response == 'accept':
        cur.execute("""
            UPDATE Appointment SET Status = 'CONFIRMED'
            WHERE Appointment_ID = %s
        """, (appointment_id,))
        flash('Appointment confirmed', 'success')
    elif response == 'reject':
        cur.execute("""
            UPDATE Appointment SET Status = 'REJECTED'
            WHERE Appointment_ID = %s
        """, (appointment_id,))
        flash('Appointment rejected', 'success')
    elif response == 'counter':
        new_date = request.form.get('new_date', '')
        new_start = request.form.get('new_start', '')
        new_end = request.form.get('new_end', '')
        
        if new_date and new_start and new_end:
            cur.execute("""
                UPDATE Appointment 
                SET Status = 'COUNTER_PROPOSED', ApptDate = %s, StartTime = %s, EndTime = %s
                WHERE Appointment_ID = %s
            """, (new_date, new_start, new_end, appointment_id))
            flash('Counter proposal sent', 'success')
        else:
            flash('Missing date or time for counter proposal', 'error')
    
    conn.commit()
    cur.close(); conn.close()
    
    return redirect(url_for('instructor.home')) 