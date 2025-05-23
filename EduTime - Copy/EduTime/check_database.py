import mysql.connector

def check_database():
    """Check if the database and required tables exist"""
    try:
        # Try to connect directly to MySQL server
        conn = mysql.connector.connect(
            host='localhost',
            user='root',
            password='Ali.ak711'
        )
        
        cursor = conn.cursor()
        
        # Check if database exists
        cursor.execute("SHOW DATABASES")
        databases = [db[0] for db in cursor.fetchall()]
        
        print("Available databases:")
        for db in databases:
            print(f"  - {db}")
        
        # Check if edutime_final database exists
        if 'edutime_final' in databases:
            print("\n✅ edutime_final database found!")
            
            # Connect to edutime_final database
            cursor.execute("USE edutime_final")
            
            # List tables
            cursor.execute("SHOW TABLES")
            tables = [table[0] for table in cursor.fetchall()]
            
            print("\nTables in edutime_final database:")
            if tables:
                for table in tables:
                    # Count rows
                    cursor.execute(f"SELECT COUNT(*) FROM {table}")
                    count = cursor.fetchone()[0]
                    print(f"  - {table} ({count} rows)")
            else:
                print("  No tables found. Database might be empty.")
                
            # Check specific tables needed for our app
            required_tables = ['UserAccount', 'Administrator', 'Instructor', 'Student', 
                              'Department', 'Degree', 'Semester', 'Course', 
                              'Classroom', 'TimeSlot', 'ClassSchedule', 'Appointment']
            
            missing_tables = [table for table in required_tables if table.lower() not in [t.lower() for t in tables]]
            
            if missing_tables:
                print("\n❌ Missing required tables:")
                for table in missing_tables:
                    print(f"  - {table}")
                print("\nYou need to run the DDL script to create these tables.")
                print("Try: mysql -u root -p edutime_final < EduTime/EduTime_DDL_final.sql")
            else:
                print("\n✅ All required tables are present!")
            
        else:
            print("\n❌ edutime_final database NOT found!")
            print("You need to create the database and tables.")
            print("Try: mysql -u root -p < EduTime/EduTime_DDL_final.sql")
        
        cursor.close()
        conn.close()
        
    except mysql.connector.Error as e:
        print(f"Error connecting to MySQL: {str(e)}")
        print("\nPossible issues:")
        print("  1. MySQL server is not running")
        print("  2. Username or password in the script is incorrect")
        print("  3. MySQL server is not accepting connections from localhost")

if __name__ == "__main__":
    print("EduTime Database Checker")
    print("-----------------------")
    check_database() 