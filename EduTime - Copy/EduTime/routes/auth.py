from flask import Blueprint, render_template, request, redirect, url_for, session, flash
from db_config import get_connection
from utils.auth import hash_password
from utils.email import send_welcome_email

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    # If user is already logged in, redirect to dashboard
    if 'user_id' in session and session.get('role'):
        return redirect(url_for('dashboard'))
        
    if request.method == 'POST':
        email = request.form.get('email', '')
        password = request.form.get('password', '')
        
        if not email or not password:
            flash('Email and password are required', 'error')
            return render_template('auth/login.html')
        
        hashed_password = hash_password(password)
        
        try:
            conn = get_connection(); cur = conn.cursor()
            cur.execute("SELECT User_ID, Name, Role FROM UserAccount WHERE Email = %s AND PasswordHash = %s", 
                     (email, hashed_password))
            user = cur.fetchone()
            cur.close(); conn.close()
            
            if user:
                # Store user info in session
                session['user_id'] = user[0]
                session['name'] = user[1]
                session['role'] = user[2]
                
                flash(f'Welcome back, {user[1]}!', 'success')
                return redirect(url_for('dashboard'))
            else:
                flash('Invalid email or password', 'error')
        except Exception as e:
            flash(f'An error occurred: {str(e)}', 'error')
    
    return render_template('auth/login.html')

@auth_bp.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        name = request.form['name']
        email = request.form['email']
        password = hash_password(request.form['password'])
        role = request.form['role']
        
        # Prevent admin signup through the form
        if role == 'ADMIN':
            flash('Admin accounts cannot be created through this form.', 'error')
            return redirect(url_for('auth.signup'))
        
        conn = get_connection(); cur = conn.cursor()
        
        # Handle different user roles
        if role == 'INSTRUCTOR':
            # For instructors, check if they've been pre-registered by admin
            # Check if this email exists in the pre-registered instructors
            cur.execute("""
                SELECT ua.User_ID, i.Department_ID 
                FROM UserAccount ua
                JOIN Instructor i ON i.User_ID = ua.User_ID
                WHERE ua.Email = %s AND ua.Role = 'INSTRUCTOR'
            """, (email,))
            
            instructor_row = cur.fetchone()
            if not instructor_row:
                flash('This email is not registered as an instructor. Please contact the administrator.', 'error')
                cur.close(); conn.close()
                return redirect(url_for('auth.signup'))
            
            # Use the department ID from the pre-registered record
            user_id = instructor_row[0]
            dept_id = instructor_row[1]
            
            # Update the existing instructor record with the password
            cur.execute("""
                UPDATE UserAccount 
                SET Name = %s, PasswordHash = %s
                WHERE User_ID = %s
            """, (name, password, user_id))
            
            conn.commit()
            cur.close(); conn.close()
            
            # Send welcome email
            send_welcome_email(email, 'INSTRUCTOR')
            
            flash('Instructor account setup completed! You can now log in.', 'success')
            return redirect(url_for('auth.login'))
        
        elif role == 'STUDENT':
            # Check if email already exists
            cur.execute("SELECT 1 FROM UserAccount WHERE Email = %s", (email,))
            if cur.fetchone():
                flash('Email already registered', 'error')
                cur.close(); conn.close()
                return redirect(url_for('auth.signup'))
                
            # Get department ID and CMS ID
            dept_id = request.form.get('department_id', type=int)
            cms_id = request.form.get('cms_id', '')
            
            if not dept_id:
                flash('Please select a department', 'error')
                cur.close(); conn.close()
                return redirect(url_for('auth.signup'))
                
            if not cms_id:
                flash('CMS ID is required for student registration', 'error')
                cur.close(); conn.close()
                return redirect(url_for('auth.signup'))
            
            # Create student account directly
            cur.execute("""
                INSERT INTO UserAccount (Name, Email, Role, PasswordHash)
                VALUES (%s, %s, %s, %s)
            """, (name, email, role, password))
            user_id = cur.lastrowid
            
            # Create student record with CMS ID
            cur.execute("""
                INSERT INTO Student (Student_ID, User_ID, CMS_ID, Department_ID)
                VALUES (%s, %s, %s, %s)
            """, (user_id, user_id, cms_id, dept_id))
            
            conn.commit()
            cur.close(); conn.close()
            
            # Send welcome email
            send_welcome_email(email, 'STUDENT')
            
            flash('Student account created successfully! You can now log in.', 'success')
            return redirect(url_for('auth.login'))
    
    # Get departments for student/instructor signup
    conn = get_connection(); cur = conn.cursor()
    cur.execute("SELECT Department_ID, Name, Prefix FROM Department")
    departments = cur.fetchall()
    cur.close(); conn.close()
    
    return render_template('auth/signup.html', departments=departments)

@auth_bp.route('/logout')
def logout():
    # Mark the session as non-permanent to help with removal
    session.permanent = False
    # Get the user name before clearing for a personalized message
    username = session.get('name', 'User')
    # Clear all session data
    session.clear()
    
    response = redirect(url_for('auth.login'))
    # Set an expired session cookie to force browsers to remove it
    response.set_cookie('session', '', expires=0)
    
    flash(f'You have been logged out, {username}', 'info')
    return response 