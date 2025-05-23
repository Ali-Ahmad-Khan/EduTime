from flask import render_template
from db_config import get_connection

def get_degrees_with_semesters():
    """Get all degrees with their semesters that have courses"""
    conn = get_connection(); cur = conn.cursor()
    
    # Get all degrees with their department names
    cur.execute("""
        SELECT d.Degree_ID, d.Name, dp.Prefix 
        FROM Degree d
        JOIN Department dp ON dp.Department_ID = d.Department_ID
        ORDER BY dp.Prefix, d.Name
    """)
    degrees = cur.fetchall()
    
    # For each degree, get a list of semesters that have courses
    degree_semesters = {}
    for deg_id, deg_name, prefix in degrees:
        cur.execute("""
            SELECT DISTINCT s.Semester_No
            FROM Semester s
            JOIN Course c ON c.Semester_ID = s.Semester_ID
            WHERE s.Degree_ID = %s
            ORDER BY s.Semester_No
        """, (deg_id,))
        semesters = [row[0] for row in cur.fetchall()]
        if semesters:  # Only include degrees that have semesters with courses
            degree_semesters[deg_id] = {
                'name': f"{prefix} - {deg_name}",
                'semesters': semesters
            }
    
    cur.close(); conn.close()
    return degree_semesters

def render_selection_page(template_name, **kwargs):
    """Helper function to render selection pages with common data"""
    conn = get_connection(); cur = conn.cursor()
    
    # Get departments
    cur.execute("SELECT Department_ID, Name, Prefix FROM Department")
    departments = cur.fetchall()
    
    # Get degrees
    cur.execute("""
        SELECT d.Degree_ID, d.Name, dp.Prefix, d.Department_ID
        FROM Degree d
        JOIN Department dp ON dp.Department_ID = d.Department_ID
        ORDER BY dp.Prefix, d.Name
    """)
    degrees = cur.fetchall()
    
    # We don't need to pre-load semesters here, they'll be loaded via AJAX
    # when a degree is selected
    
    cur.close(); conn.close()
    
    # Add common data to kwargs
    kwargs.update({
        'departments': departments,
        'degrees': degrees
    })
    
    return render_template(template_name, **kwargs) 