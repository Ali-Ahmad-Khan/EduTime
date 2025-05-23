# EduTime Database Troubleshooting Guide

## Common Database Issues

If you're experiencing issues with the EduTime database, follow these troubleshooting steps.

### 1. Database Connection Failures

**Symptoms:**
- "Connection refused" errors
- Python scripts hanging without error messages
- MySQL Workbench cannot connect
- Queries taking too long to execute

**Solutions:**

#### Check MySQL Service Status
```bash
# Windows (run in Command Prompt as Administrator)
net start mysql

# Linux
sudo systemctl status mysql
```

#### Restart MySQL Service
```bash
# Windows (run in Command Prompt as Administrator)
net stop mysql
net start mysql

# Linux
sudo systemctl restart mysql
```

### 2. Lock/Deadlock Issues

**Symptoms:**
- Queries hang indefinitely
- DELETE or UPDATE queries never complete
- Error about "deadlock" or "lock wait timeout"

**Solutions:**

#### Check for Locks in MySQL
```sql
-- Run in MySQL Workbench or console
SHOW PROCESSLIST;
SHOW OPEN TABLES WHERE In_use > 0;
```

#### Kill Hanging Processes
```sql
-- Replace XX with process ID from SHOW PROCESSLIST
KILL XX;
```

### 3. Database Schema Problems

**Symptoms:**
- "Table doesn't exist" errors
- "Unknown column" errors
- Constraint violations

**Solutions:**

#### Reset the Database
1. Run the reset script:
   ```bash
   python EduTime/reset_database.py --confirm
   ```

2. Initialize with sample data:
   ```bash
   python EduTime/initialize_database.py --confirm
   ```

### 4. Database Name Mismatch

**Symptoms:**
- Application looking for a different database name than what exists
- "Unknown database" errors

**Solution:**

Check `db_config.py` to ensure the database name matches your actual database:

```python
# The database configuration should match your MySQL setup
import mysql.connector

def get_connection():
    return mysql.connector.connect(
        host='localhost',
        user='root',
        password='your_password_here',
        database='edutime_final'
    )
```

### 5. Account Issues

**Symptoms:**
- "Access denied" when logging in
- Admin account not working

**Solution:**

Run the admin creation script to ensure an admin account exists:
```bash
python EduTime/create_admin.py
```

This will create (or confirm the existence of) an admin account with:
- Email: admin@edutime.com
- Password: admin123

### 6. Connection Timeouts

**Symptoms:**
- Database operations hang without completing
- Queries take excessively long to execute

**Solutions:**

#### Increase MySQL Timeout Settings
Edit your MySQL configuration file (my.ini or my.cnf):

```ini
[mysqld]
wait_timeout = 600
interactive_timeout = 600
```

#### Check Database and Table Sizes
Large tables may need optimization:

```sql
-- Show database sizes
SELECT table_schema, ROUND(SUM(data_length + index_length) / 1024 / 1024, 2) 'Size (MB)'
FROM information_schema.tables
GROUP BY table_schema;

-- Show table sizes in edutime_final
SELECT table_name, ROUND((data_length + index_length) / 1024 / 1024, 2) 'Size (MB)'
FROM information_schema.tables
WHERE table_schema = 'edutime_final'
ORDER BY (data_length + index_length) DESC;
```

### 7. SQL Syntax or Query Issues

**Symptoms:**
- Syntax errors in SQL queries
- Queries taking unusually long to execute

**Solutions:**

#### Check SQL Syntax
Verify your query using a tool like MySQL Workbench before running it in your application.

#### Add Indexes for Performance
```sql
-- Example: Add index to email field for faster lookups
ALTER TABLE UserAccount ADD INDEX idx_email (Email);
```

## Contact Support

If you continue to experience issues after trying these solutions, please contact technical support with the following information:
- Exact error messages
- Steps to reproduce the issue
- MySQL version
- Python version (if applicable)
- Operating system details 