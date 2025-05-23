import mysql.connector
import os
import sys

def execute_sql_file(file_path, conn=None, close_conn=True):
    """Execute SQL statements from a file"""
    print(f"Executing SQL file: {file_path}")
    
    try:
        # Create connection if not provided
        if conn is None:
            conn = mysql.connector.connect(
                host='localhost',
                user='root',
                password='Ali.ak711'
            )
        
        cursor = conn.cursor()
        
        # Read the SQL file
        with open(file_path, 'r') as file:
            sql_script = file.read()
        
        # Split the script at the semicolons and execute each statement
        statements = sql_script.split(';')
        for statement in statements:
            if statement.strip():  # Skip empty statements
                cursor.execute(statement)
        
        conn.commit()
        
        if close_conn:
            cursor.close()
            conn.close()
            
        print(f"✅ SQL file executed successfully: {file_path}")
        return True, conn if not close_conn else None
        
    except mysql.connector.Error as e:
        print(f"❌ Error executing SQL file: {str(e)}")
        return False, None
    except Exception as e:
        print(f"❌ Error reading or processing SQL file: {str(e)}")
        return False, None

def reset_database():
    """Reset and recreate the entire database"""
    try:
        # Try to connect directly to MySQL server
        conn = mysql.connector.connect(
            host='localhost',
            user='root',
            password='Ali.ak711'
        )
        
        cursor = conn.cursor()
        
        print("Checking if edutime_final database exists...")
        
        # Check if database exists
        cursor.execute("SHOW DATABASES")
        databases = [db[0] for db in cursor.fetchall()]
        
        # Drop the database if it exists
        if 'edutime_final' in databases:
            print("Dropping existing edutime_final database...")
            cursor.execute("DROP DATABASE edutime_final")
            print("✅ Database dropped successfully")
            
        # Create the database
        print("Creating edutime_final database...")
        cursor.execute("CREATE DATABASE edutime_final")
        print("✅ Database created successfully")
        
        cursor.close()
        conn.close()
        
        # Execute the DDL script
        ddl_path = os.path.join(os.path.dirname(__file__), 'EduTime_DDL_final.sql')
        success, _ = execute_sql_file(ddl_path)
        
        if success:
            print("\n✅ Database reset and recreated successfully!")
            return True
        else:
            print("\n❌ Failed to reset and recreate the database.")
            return False
        
    except mysql.connector.Error as e:
        print(f"Error connecting to MySQL: {str(e)}")
        print("\nPossible issues:")
        print("  1. MySQL server is not running")
        print("  2. Username or password in the script is incorrect")
        print("  3. MySQL server is not accepting connections from localhost")
        return False

def create_admin_user():
    """Create a default admin user"""
    import hashlib
    
    try:
        # Connect to edutime_final database
        conn = mysql.connector.connect(
            host='localhost',
            user='root',
            password='Ali.ak711',
            database='edutime_final'
        )
        
        cursor = conn.cursor()
        
        # Default admin credentials
        name = "Administrator"
        email = "admin@edutime.com"
        password = "admin123"
        hashed_password = hashlib.sha256(password.encode()).hexdigest()
        
        print(f"\nCreating default admin user:")
        print(f"  Name: {name}")
        print(f"  Email: {email}")
        print(f"  Password: {password}")
        
        # Insert the admin user
        cursor.execute("""
            INSERT INTO UserAccount (Name, Email, Role, PasswordHash)
            VALUES (%s, %s, 'ADMIN', %s)
        """, (name, email, hashed_password))
        
        admin_id = cursor.lastrowid
        
        # Create administrator record
        cursor.execute("INSERT INTO Administrator (Admin_ID, User_ID) VALUES (%s, %s)", 
                     (admin_id, admin_id))
        
        conn.commit()
        cursor.close()
        conn.close()
        
        print(f"✅ Admin user created successfully!")
        return True
        
    except mysql.connector.Error as e:
        print(f"❌ Error creating admin user: {str(e)}")
        return False

if __name__ == "__main__":
    print("EduTime Database Reset Tool")
    print("--------------------------")
    
    if len(sys.argv) > 1 and sys.argv[1] == "--confirm":
        print("WARNING: This will delete and recreate the edutime_final database!")
        print("All existing data will be lost!")
        
        reset_success = reset_database()
        
        if reset_success:
            admin_success = create_admin_user()
            
            if admin_success:
                print("\n✅ Database reset and admin user created successfully!")
                print("\nYou can now login with:")
                print("  Email: admin@edutime.com")
                print("  Password: admin123")
            else:
                print("\n⚠️ Database reset successfully but failed to create admin user.")
                print("Try running create_admin.py separately.")
        
    else:
        print("⚠️ This script will DELETE ALL DATA in the edutime_final database!")
        print("To proceed, run the script with the --confirm flag:")
        print("  python EduTime/reset_database.py --confirm") 