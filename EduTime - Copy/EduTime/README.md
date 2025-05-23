# EduTime - Educational Timetable Management System

EduTime is a comprehensive web application for managing educational timetables, courses, instructors, and student schedules.

## Project Structure

The application follows a modular structure for better organization and maintainability:

```
EduTime/
├── app.py              # Main application entry point
├── db_config.py        # Database configuration
├── logic/              # Business logic modules
│   ├── classroom_logic.py
│   ├── course_logic.py
│   ├── degree_logic.py
│   ├── department_logic.py
│   └── instructor_logic.py
├── routes/             # Route handlers
│   ├── __init__.py
│   ├── admin.py        # Admin dashboard and management routes
│   ├── auth.py         # Authentication routes (login, signup)
│   ├── instructor.py   # Instructor-specific routes
│   ├── schedule.py     # Schedule viewing and generation routes
│   └── student.py      # Student-specific routes
├── static/             # Static assets
│   ├── css/
│   │   └── style.css   # Main stylesheet
│   ├── js/             # JavaScript files
│   └── images/         # Image assets
├── templates/          # HTML templates
│   ├── admin/          # Admin templates
│   ├── auth/           # Authentication templates
│   ├── instructor/     # Instructor templates
│   ├── schedule/       # Schedule templates
│   ├── student/        # Student templates
│   └── base.html       # Base template with common layout
├── utils/              # Utility functions
│   ├── __init__.py
│   ├── auth.py         # Authentication helpers
│   ├── email.py        # Email functionality
│   └── helpers.py      # General helper functions
└── triggers.sql        # SQL triggers for database operations
```

## Features

- **User Authentication**: Login, signup, and email verification
- **Role-Based Access Control**: Different interfaces for admins, instructors, and students
- **Department Management**: Create and manage academic departments
- **Degree Management**: Set up degree programs with semesters
- **Course Management**: Add courses to degrees and semesters
- **Instructor Management**: Add instructors and assign courses
- **Venue Management**: Manage classrooms and labs
- **Schedule Generation**: Generate and view timetables
- **Appointment System**: Request and manage appointments between students and instructors

## User Roles

1. **Administrator**:
   - Manage departments, degrees, courses, instructors, and venues
   - Generate schedules
   - Set up initial data

2. **Instructor**:
   - View assigned courses
   - Manage schedule
   - Respond to appointment requests

3. **Student**:
   - View schedules
   - Request appointments with instructors

## Technical Implementation

- **Backend**: Flask (Python)
- **Database**: MySQL
- **Authentication**: Session-based with password hashing
- **Email Verification**: Token-based verification system
- **UI**: Custom CSS with responsive design

## Database Optimization

- SQL triggers for automated operations
- Cascade constraints for data integrity
- Optimized queries for performance

## Getting Started

1. Ensure you have Python 3.6+ and MySQL installed
2. Install requirements: `pip install -r requirements.txt`
3. Set up the database using the SQL scripts
4. Run the application: `python app.py`
5. Access the application at http://localhost:5000

## Future Enhancements

- Automated schedule generation algorithm
- Mobile application
- Integration with learning management systems
- Calendar export functionality
- Notification system

## Installation

1. **Clone the repository**:
   ```
   git clone https://github.com/yourusername/edutime.git
   cd edutime
   ```

2. **Set up a virtual environment**:
   ```
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**:
   ```
   pip install -r requirements.txt
   ```

4. **Configure database**:
   - Edit `db_config.py` with your MySQL credentials
   - Run the database setup script:
     ```
     python EduTime/reset_database.py --confirm
     ```

5. **Run the application**:
   ```
   python EduTime/app.py
   ```

## Quick Start

1. **Login as Admin**: 
   - Email: admin@edutime.com
   - Password: admin123

2. **Initialize Sample Data**:
   - Click "Initialize with Sample Data" on the admin dashboard
   - This will set up a sample department, degree, courses and instructors

3. **Generate a Schedule**:
   - Go to Schedule > Generate Schedule
   - View the generated timetables under Schedule > View Timetables

## Database Troubleshooting

### Connection Issues

**Symptoms:**
- "Connection refused" errors
- Python scripts hanging without error messages
- MySQL Workbench cannot connect
- Queries taking too long to execute

**Solutions:**

1. **Check MySQL Service Status**
```bash
# Windows (run in Command Prompt as Administrator)
net start mysql

# Linux
sudo systemctl status mysql
```

2. **Restart MySQL Service**
```bash
# Windows (run in Command Prompt as Administrator)
net stop mysql
net start mysql

# Linux
sudo systemctl restart mysql
```

### Lock/Deadlock Issues

**Symptoms:**
- Queries hang indefinitely
- DELETE or UPDATE queries never complete
- Multiple edits requested at once fail

**Solutions:**

1. **Clear locks**
```sql
-- Show all current locks
SHOW PROCESSLIST;

-- Kill a specific process (replace XXX with process ID)
KILL XXX;
```

2. **Reset the database**
```bash
python EduTime/reset_database.py --confirm
```

## License

MIT License

## Contributors

- Your Name
- Other Contributors 