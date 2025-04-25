import pymysql

# Database connection parameters
db_params = {
    'host': 'localhost',
    'port': 3307,
    'user': 'root',
    'password': 'yash#oo7',
    'database': 'farmconnect'
}

try:
    # Connect to the database
    connection = pymysql.connect(**db_params)
    cursor = connection.cursor()
    
    # Execute the ALTER TABLE command
    sql = "ALTER TABLE farmer_profile ADD COLUMN upi_qr_code VARCHAR(255);"
    cursor.execute(sql)
    
    # Commit the changes
    connection.commit()
    print("Successfully added upi_qr_code column to farmer_profile table")
    
except pymysql.Error as e:
    print(f"Error: {e}")
    
finally:
    if 'connection' in locals():
        cursor.close()
        connection.close()
        print("Database connection closed")
