from flask import Blueprint, render_template, redirect, url_for, flash, Response, request
from utils.auth import admin_required
from db_config import get_connection
from utils.helpers import get_degrees_with_semesters
import csv
import io

schedule_bp = Blueprint('schedule', __name__, url_prefix='/schedule')

@schedule_bp.route('/')
def degrees_for_schedule():
    degree_semesters = get_degrees_with_semesters()
    return render_template('schedule/select_degree.html', degree_semesters=degree_semesters)

@schedule_bp.route('/view/<int:degree_id>/<int:semester_no>')
def view_schedule(degree_id, semester_no):
    # Get degree name first
    conn = get_connection(); cur = conn.cursor()
    cur.execute("""
        SELECT d.Name, dp.Prefix
        FROM Degree d
        JOIN Department dp ON dp.Department_ID = d.Department_ID
        WHERE d.Degree_ID = %s
    """, (degree_id,))
    degree_info = cur.fetchone()
    
    if not degree_info:
        flash('Degree not found', 'error')
        return redirect(url_for('schedule.degrees_for_schedule'))
    
    degree_name = degree_info[0]
    dept_prefix = degree_info[1]
    
    # Get semester ID
    cur.execute("""
        SELECT Semester_ID
        FROM Semester
        WHERE Degree_ID = %s AND Semester_No = %s
    """, (degree_id, semester_no))
    semester_row = cur.fetchone()
    
    if not semester_row:
        flash('Semester not found', 'error')
        return redirect(url_for('schedule.degrees_for_schedule'))
    
    semester_id = semester_row[0]
    
    # Get all time slots
    cur.execute("""
        SELECT TimeSlot_ID, Day, Slot_No, StartTime, EndTime
        FROM TimeSlot
        ORDER BY Day, Slot_No
    """)
    all_slots = cur.fetchall()
    
    # Create a dictionary to organize slots by day
    days = ['MON', 'TUE', 'WED', 'THU', 'FRI']
    time_slots = {day: [] for day in days}
    
    for slot_id, day, slot_no, start_time, end_time in all_slots:
        time_slots[day].append({
            'id': slot_id,
            'no': slot_no,
            'start': start_time,
            'end': end_time
        })
    
    # Get schedule for this semester
    cur.execute("""
        SELECT cs.Schedule_ID, c.Name, c.IsLab, u.Name as InstructorName,
               r.RoomNumber, ts.Day, ts.Slot_No, ts.StartTime, ts.EndTime
        FROM ClassSchedule cs
        JOIN Course c ON c.Course_ID = cs.Course_ID
        JOIN Instructor i ON i.Instructor_ID = cs.Instructor_ID
        JOIN UserAccount u ON u.User_ID = i.User_ID
        JOIN Classroom r ON r.Room_ID = cs.Room_ID
        JOIN TimeSlot ts ON ts.TimeSlot_ID = cs.TimeSlot_ID
        WHERE cs.Semester_ID = %s
        ORDER BY ts.Day, ts.Slot_No
    """, (semester_id,))
    schedule_items = cur.fetchall()
    
    # Create a 2D dictionary for the schedule grid
    schedule_grid = {day: {} for day in days}
    
    for item in schedule_items:
        day = item[5]  # ts.Day
        slot_no = item[6]  # ts.Slot_No
        schedule_grid[day][slot_no] = {
            'id': item[0],
            'course': item[1],
            'is_lab': item[2],
            'instructor': item[3],
            'room': item[4],
            'start': item[7],
            'end': item[8]
        }
    
    cur.close(); conn.close()
    
    return render_template('schedule/view_schedule.html',
                          degree_id=degree_id,
                          semester_no=semester_no,
                          degree_name=degree_name,
                          dept_prefix=dept_prefix,
                          days=days,
                          time_slots=time_slots,
                          schedule_grid=schedule_grid)

@schedule_bp.route('/generate', methods=['GET', 'POST'])
@admin_required
def generate_schedule():
    """Generate timetable for all courses"""
    if request.method == 'POST':
        from schedule.schedule_generator import generate_schedule as run_schedule_generator
        
        # Run the schedule generator
        try:
            result_summary = run_schedule_generator()
            flash(result_summary, 'success')
            return redirect(url_for('schedule.degrees_for_schedule'))
        except Exception as e:
            flash(f'Error generating schedule: {str(e)}', 'error')
            return redirect(url_for('schedule.generate_schedule'))
    
    conn = get_connection(); cur = conn.cursor()
    
    # Get all courses that need scheduling
    cur.execute("""
        SELECT c.Course_ID, c.Name, c.IsLab, c.CreditHours, 
               s.Semester_ID, s.Semester_No, d.Degree_ID, d.Name as DegreeName
        FROM Course c
        JOIN Semester s ON s.Semester_ID = c.Semester_ID
        JOIN Degree d ON d.Degree_ID = c.Degree_ID
        LEFT JOIN ClassSchedule cs ON cs.Course_ID = c.Course_ID
        WHERE cs.Schedule_ID IS NULL
        ORDER BY d.Name, s.Semester_No, c.Name
    """)
    unscheduled_courses = cur.fetchall()
    
    # Get summary of existing schedule
    cur.execute("""
        SELECT COUNT(DISTINCT cs.Course_ID) as ScheduledCourses,
               COUNT(DISTINCT cs.Semester_ID) as ScheduledSemesters
        FROM ClassSchedule cs
    """)
    schedule_summary = cur.fetchone()
    
    # Get degrees with schedules
    cur.execute("""
        SELECT DISTINCT d.Degree_ID, d.Name, s.Semester_No
        FROM ClassSchedule cs
        JOIN Semester s ON s.Semester_ID = cs.Semester_ID
        JOIN Degree d ON d.Degree_ID = s.Degree_ID
        ORDER BY d.Name, s.Semester_No
    """)
    scheduled_degrees = cur.fetchall()
    
    cur.close(); conn.close()
    
    return render_template('admin/generate_schedule.html',
                          unscheduled_courses=unscheduled_courses,
                          schedule_summary=schedule_summary,
                          scheduled_degrees=scheduled_degrees)

@schedule_bp.route('/generate/options', methods=['POST'])
@admin_required
def generate_options():
    """Save schedule generation options"""
    algorithm = request.form.get('algorithm', 'genetic')
    constraints = request.form.getlist('constraints[]')
    
    # In a real application, you would save these options to a database or config file
    # For now, just show a success message
    flash(f'Schedule generation options saved: {algorithm} algorithm with {len(constraints)} constraints', 'success')
    return redirect(url_for('schedule.generate_schedule'))

@schedule_bp.route('/export/<int:degree_id>/<int:semester_no>')
def export_csv(degree_id, semester_no):
    """Export schedule as CSV"""
    conn = get_connection(); cur = conn.cursor()
    
    # Get degree name
    cur.execute("""
        SELECT d.Name, dp.Prefix
        FROM Degree d
        JOIN Department dp ON dp.Department_ID = d.Department_ID
        WHERE d.Degree_ID = %s
    """, (degree_id,))
    degree_info = cur.fetchone()
    
    if not degree_info:
        flash('Degree not found', 'error')
        return redirect(url_for('schedule.degrees_for_schedule'))
    
    degree_name = degree_info[0]
    dept_prefix = degree_info[1]
    
    # Get semester ID
    cur.execute("""
        SELECT Semester_ID
        FROM Semester
        WHERE Degree_ID = %s AND Semester_No = %s
    """, (degree_id, semester_no))
    semester_row = cur.fetchone()
    
    if not semester_row:
        flash('Semester not found', 'error')
        return redirect(url_for('schedule.degrees_for_schedule'))
    
    semester_id = semester_row[0]
    
    # Get schedule for this semester
    cur.execute("""
        SELECT c.Name, c.IsLab, u.Name as InstructorName,
               r.RoomNumber, ts.Day, ts.Slot_No, ts.StartTime, ts.EndTime
        FROM ClassSchedule cs
        JOIN Course c ON c.Course_ID = cs.Course_ID
        JOIN Instructor i ON i.Instructor_ID = cs.Instructor_ID
        JOIN UserAccount u ON u.User_ID = i.User_ID
        JOIN Classroom r ON r.Room_ID = cs.Room_ID
        JOIN TimeSlot ts ON ts.TimeSlot_ID = cs.TimeSlot_ID
        WHERE cs.Semester_ID = %s
        ORDER BY ts.Day, ts.Slot_No
    """, (semester_id,))
    schedule_items = cur.fetchall()
    
    cur.close(); conn.close()
    
    # Create CSV in memory
    output = io.StringIO()
    writer = csv.writer(output)
    
    # Write header
    writer.writerow(['Course', 'Type', 'Instructor', 'Room', 'Day', 'Slot', 'Start Time', 'End Time'])
    
    # Write data
    for item in schedule_items:
        course_name = item[0]
        course_type = 'Lab' if item[1] else 'Lecture'
        instructor = item[2]
        room = item[3]
        day = item[4]
        slot = item[5]
        start_time = item[6]
        end_time = item[7]
        
        writer.writerow([course_name, course_type, instructor, room, day, slot, start_time, end_time])
    
    # Prepare response
    output.seek(0)
    filename = f"{dept_prefix}_{degree_name}_Semester{semester_no}_Schedule.csv"
    filename = filename.replace(' ', '_')
    
    return Response(
        output.getvalue(),
        mimetype="text/csv",
        headers={"Content-disposition": f"attachment; filename={filename}"}
    ) 