from flask import Flask, render_template, redirect, url_for, session, flash
from routes.auth import auth_bp
from routes.admin import admin_bp
from routes.instructor import instructor_bp
from routes.student import student_bp
from routes.schedule import schedule_bp
from utils.auth import login_required
from datetime import datetime

app = Flask(__name__)
app.secret_key = 'edutime_secret_key_for_sessions'  # Use a static key instead of random
# Set session cookie to expire when browser closes (no permanent cookies)
app.config['SESSION_PERMANENT'] = False
# Set additional cookie security
app.config['SESSION_COOKIE_SECURE'] = False  # Set to True in production with HTTPS
app.config['SESSION_COOKIE_HTTPONLY'] = True
app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'

# Register blueprints
app.register_blueprint(auth_bp)
app.register_blueprint(admin_bp)
app.register_blueprint(instructor_bp)
app.register_blueprint(student_bp)
app.register_blueprint(schedule_bp)

# Context processor to provide current datetime to all templates
@app.context_processor
def inject_now():
    return {'now': datetime.now()}

# Root route
@app.route('/')
def home():
    if 'user_id' in session:
        return redirect(url_for('dashboard'))
    return redirect(url_for('auth.login'))

# Dashboard route - redirects to appropriate role-based dashboard
@app.route('/dashboard')
@login_required
def dashboard():
    """Dashboard route - redirects to appropriate role-based dashboard"""
    role = session.get('role')
    
    if role == 'ADMIN':
        return redirect(url_for('admin.home'))
    elif role == 'INSTRUCTOR':
        return redirect(url_for('instructor.home'))
    elif role == 'STUDENT':
        return redirect(url_for('student.home'))
    else:
        # Fallback in case of unexpected role
        session.clear()  # Clear invalid session
        flash('Invalid user role. Please log in again.', 'error')
        
        return redirect(url_for('auth.login'))

if __name__ == '__main__':
    app.run(debug=True) 