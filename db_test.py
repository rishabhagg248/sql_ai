# test_db_fixed.py
import mysql.connector

connection = None  # Initialize the variable
try:
    connection = mysql.connector.connect(
        host='localhost',
        database='atliq_tshirts',
        user='root',
        password=''  # Empty password
    )
    
    if connection.is_connected():
        cursor = connection.cursor()
        cursor.execute("SELECT COUNT(*) FROM t_shirts;")
        result = cursor.fetchone()
        print(f"Database connected successfully! T-shirts count: {result[0]}")
        cursor.close()
        
except mysql.connector.Error as e:
    print(f"Error connecting to MySQL: {e}")
    
finally:
    if connection and connection.is_connected():
        connection.close()