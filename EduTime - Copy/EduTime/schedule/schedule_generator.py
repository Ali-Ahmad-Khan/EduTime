import random
from db_config import get_connection
from schedule.conflict_checker import all_slots_free
from schedule.utils import fetch_all
import time

# ---------------------------------------------------------
# CONSTANTS
LECTURE_DURATION = 1        # 50-minute slot
LAB_DURATION     = 3        # 3 consecutive slots
MAX_RETRIES = 50            # Per course placement attempt

def generate_schedule():
    """
    Main entry point. Deletes old schedule then creates a new one.
    Returns a summary of the scheduling results.
    """
    start_time = time.time()
    
    print("Starting schedule generation...")
    
    # Clear existing schedule
    _clear_existing()
    
    # Generate new schedule
    result_summary = _seed()
    
    end_time = time.time()
    execution_time = end_time - start_time
    
    print(f"Schedule generation completed in {execution_time:.2f} seconds")
    
    return result_summary

def _clear_existing():
    """Clear all existing schedule entries"""
    try:
        conn = get_connection(); cur = conn.cursor()
        
        # Get count before deletion for reporting
        cur.execute("SELECT COUNT(*) FROM ClassSchedule")
        count = cur.fetchone()[0]
        
        # Delete all schedule entries
        cur.execute("DELETE FROM ClassSchedule")
        conn.commit(); cur.close(); conn.close()
        
        print(f"Cleared {count} existing schedule entries")
        return True
    except Exception as e:
        print(f"Error clearing existing schedule: {e}")
        return False

def _seed():
    """Generate schedules for all departments, degrees and semesters"""
    # Check if time slots exist
    time_slots = fetch_all("SELECT TimeSlot_ID, Day, Slot_No FROM TimeSlot ORDER BY Day, Slot_No")
    
    if not time_slots:
        return "⚠ No time slots defined in the database. Please add time slots first."
    
    # Check if departments exist
    departments = fetch_all("SELECT Department_ID, Prefix, Name FROM Department")
    if not departments:
        return "⚠ No departments defined in the database. Please add departments first."
    
    # Track statistics
    stats = {
        'departments_processed': 0,
        'degrees_processed': 0,
        'semesters_processed': 0,
        'courses_scheduled': 0,
        'courses_failed': 0,
        'errors': []
    }
    
    # Process each department
    for dept_id, prefix, dept_name in departments:
        print(f"Scheduling for department: {prefix} - {dept_name}")
        
        # Get classrooms for this department
        rooms = fetch_all("""
            SELECT Room_ID, RoomNumber, RoomType
            FROM Classroom
            WHERE Department_ID = %s
        """, (dept_id,))
        
        if not rooms:
            error_msg = f"⚠ No rooms defined for department {prefix}. Skipping."
            print(error_msg)
            stats['errors'].append(error_msg)
            continue
        
        # Get degrees for this department
        degrees = fetch_all("""
            SELECT Degree_ID, Name
            FROM Degree
            WHERE Department_ID = %s
        """, (dept_id,))
        
        if not degrees:
            error_msg = f"⚠ No degrees defined for department {prefix}. Skipping."
            print(error_msg)
            stats['errors'].append(error_msg)
            continue
        
        # Process each degree
        for degree_id, degree_name in degrees:
            print(f"  Processing degree: {degree_name}")
            
            # Get semesters for this degree
            semesters = fetch_all("""
                SELECT Semester_ID, Semester_No
                FROM Semester
                WHERE Degree_ID = %s
                ORDER BY Semester_No
            """, (degree_id,))
            
            if not semesters:
                error_msg = f"⚠ No semesters defined for degree {degree_name}. Skipping."
                print(error_msg)
                stats['errors'].append(error_msg)
                continue
            
            # Process each semester
            for semester_id, semester_no in semesters:
                print(f"    Processing semester: {semester_no}")
                
                # Get courses for this semester
                courses = fetch_all("""
                    SELECT Course_ID, Name, CreditHours, IsLab
                    FROM Course
                    WHERE Semester_ID = %s
                """, (semester_id,))
                
                if not courses:
                    error_msg = f"⚠ No courses defined for {degree_name} Semester {semester_no}. Skipping."
                    print(error_msg)
                    stats['errors'].append(error_msg)
                    continue
                
                # Process each course
                semester_success = 0
                semester_failed = 0
                
                for course_id, course_name, credits, is_lab in courses:
                    result = _schedule_course(course_id, semester_id, credits, bool(is_lab), 
                                              time_slots, rooms, course_name)
                    
                    if result:
                        semester_success += 1
                        stats['courses_scheduled'] += 1
                    else:
                        semester_failed += 1
                        stats['courses_failed'] += 1
                
                print(f"    Semester {semester_no}: {semester_success} courses scheduled, {semester_failed} failed")
                stats['semesters_processed'] += 1
            
            stats['degrees_processed'] += 1
        
        stats['departments_processed'] += 1
    
    # Return a summary of the scheduling results
    result_msg = (
        f"✅ Schedule generation completed:\n"
        f"- {stats['departments_processed']} departments processed\n"
        f"- {stats['degrees_processed']} degrees processed\n"
        f"- {stats['semesters_processed']} semesters processed\n"
        f"- {stats['courses_scheduled']} courses successfully scheduled\n"
        f"- {stats['courses_failed']} courses could not be scheduled\n"
    )
    
    if stats['errors']:
        result_msg += f"- {len(stats['errors'])} errors occurred:\n"
        for i, error in enumerate(stats['errors'][:5], 1):  # Show first 5 errors
            result_msg += f"  {i}. {error}\n"
        
        if len(stats['errors']) > 5:
            result_msg += f"  ... and {len(stats['errors']) - 5} more errors\n"
    
    print(result_msg)
    return result_msg

def _schedule_course(course_id, semester_id, credits, is_lab, time_slots, rooms, course_name=None):
    """
    Schedule a course with robust error handling.
    Returns True if scheduling succeeded, False otherwise.
    """
    try:
        blocks_needed = credits if not is_lab else 1  # labs count as one 3-slot block
        blocks_done = 0
        
        # Check if course has an assigned instructor
        instructor_rows = fetch_all("""
            SELECT t.Instructor_ID, u.Name
            FROM Teaches t
            JOIN Instructor i ON i.Instructor_ID = t.Instructor_ID
            JOIN UserAccount u ON u.User_ID = i.User_ID
            WHERE t.Course_ID = %s
            LIMIT 1
        """, (course_id,))
        
        # Skip scheduling if no instructor assigned
        if not instructor_rows:
            print(f"⚠ Course {course_id} ({course_name or 'Unknown'}) has no instructor assigned. Skipping.")
            return False
        
        instructor_id = instructor_rows[0][0]
        instructor_name = instructor_rows[0][1]
        
        # Filter appropriate rooms based on course type
        suitable_rooms = []
        for room_id, room_number, room_type in rooms:
            if is_lab and room_type == 'LAB':
                suitable_rooms.append((room_id, room_number, room_type))
            elif not is_lab and room_type == 'CLASSROOM':
                suitable_rooms.append((room_id, room_number, room_type))
        
        if not suitable_rooms:
            room_type_needed = "LAB" if is_lab else "CLASSROOM"
            print(f"⚠ No {room_type_needed} rooms available for course {course_id} ({course_name or 'Unknown'})")
            return False
        
        # Create a database connection for the scheduling operation
        conn = get_connection()
        cur = conn.cursor()
        course_scheduled = False
        
        try:
            retries = 0
            conflicts = set()  # Track conflict reasons
            
            while blocks_done < blocks_needed and retries < MAX_RETRIES:
                retries += 1
                
                # Randomly select time slot and room
                random_ts_idx = random.randint(0, len(time_slots) - 1)
                ts_id, day, slot_no = time_slots[random_ts_idx]
                
                random_room_idx = random.randint(0, len(suitable_rooms) - 1)
                room_id, room_number, room_type = suitable_rooms[random_room_idx]
                
                # Handle lab scheduling
                if is_lab:
                    # Need slot_no 1-5 only so slot_no+2 ≤ 7 (three consecutive slots)
                    if slot_no > 5:
                        continue
                    
                    # Find the next two consecutive slots with same day
                    consecutive_slots = [ts_id]
                    next_slots = []
                    
                    for ts in time_slots:
                        if ts[1] == day and ts[2] == slot_no + 1:
                            next_slots.append(ts[0])
                        elif ts[1] == day and ts[2] == slot_no + 2:
                            next_slots.append(ts[0])
                    
                    if len(next_slots) != 2:
                        # Record the conflict reason
                        conflict_reason = f"Lab needs 3 consecutive slots but found {len(next_slots)+1} on {day}"
                        conflicts.add(conflict_reason)
                        continue  # Skip if we can't find consecutive slots
                    
                    consecutive_slots.extend(next_slots)
                    
                    # Check for scheduling conflicts
                    if all_slots_free(room_id, instructor_id, semester_id, consecutive_slots):
                        # Lab spans 3 consecutive slots
                        for slot_id in consecutive_slots:
                            cur.execute("""
                              INSERT INTO ClassSchedule
                              (Course_ID, Instructor_ID, Semester_ID,
                               Room_ID, TimeSlot_ID, Duration)
                              VALUES (%s,%s,%s,%s,%s,%s)
                            """, (course_id, instructor_id, semester_id,
                                  room_id, slot_id, LAB_DURATION))
                        
                        conn.commit()
                        blocks_done += 1
                        course_scheduled = True
                        print(f"✅ Scheduled lab course {course_id} ({course_name or 'Unknown'}) in room {room_number} on {day} at slot {slot_no}")
                    else:
                        # Record the conflict reason
                        conflict_reason = f"Conflict with existing schedule (room {room_number} or instructor {instructor_name} busy on {day} slot {slot_no})"
                        conflicts.add(conflict_reason)
                # Handle lecture scheduling
                else:
                    if all_slots_free(room_id, instructor_id, semester_id, [ts_id]):
                        cur.execute("""
                          INSERT INTO ClassSchedule
                          (Course_ID, Instructor_ID, Semester_ID,
                           Room_ID, TimeSlot_ID, Duration)
                          VALUES (%s,%s,%s,%s,%s,%s)
                        """, (course_id, instructor_id, semester_id,
                              room_id, ts_id, LECTURE_DURATION))
                        
                        conn.commit()
                        blocks_done += 1
                        
                        if blocks_done >= blocks_needed:
                            course_scheduled = True
                            print(f"✅ Scheduled lecture course {course_id} ({course_name or 'Unknown'}) in room {room_number} on {day} at slot {slot_no}")
                    else:
                        # Record the conflict reason
                        conflict_reason = f"Conflict with existing schedule (room {room_number} or instructor {instructor_name} busy on {day} slot {slot_no})"
                        conflicts.add(conflict_reason)
            
            if blocks_done < blocks_needed:
                print(f"⚠ Could only place {blocks_done}/{blocks_needed} blocks for course {course_id} ({course_name or 'Unknown'})")
                if conflicts:
                    print(f"   Conflicts encountered:")
                    for i, reason in enumerate(conflicts, 1):
                        print(f"   {i}. {reason}")
            
            return course_scheduled
            
        except Exception as e:
            conn.rollback()
            print(f"❌ Error scheduling course {course_id} ({course_name or 'Unknown'}): {e}")
            return False
        finally:
            cur.close()
            conn.close()
            
    except Exception as e:
        print(f"❌ Unexpected error in course scheduling: {e}")
        return False
