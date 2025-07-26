import cx_Oracle
import getpass
from datetime import datetime

# 1. Establish connection to the Oracle database for the specified site.
def get_db_connection():
    # Prompt user for Oracle DB credentials and connection string
    username = input("Enter Oracle username: ")
    password = getpass.getpass("Enter Oracle password: ")
    dsn = input("Enter Oracle DSN (e.g., host:port/service): ")
    # Establish and return the database connection
    return cx_Oracle.connect(username, password, dsn)

def get_location_input():
    # Collect all required fields from the user
    location = {}
    location['LOCATION_ID'] = input("Enter LOCATION_ID: ").strip()
    location['LOCATION_NAME'] = input("Enter LOCATION_NAME: ").strip()
    location['SITE_CODE'] = input("Enter SITE_CODE: ").strip()
    location['LOCATION_TYPE'] = input("Enter LOCATION_TYPE: ").strip()
    location['CREATED_BY'] = input("Enter your username (CREATED_BY): ").strip()
    location['CREATED_DATE'] = datetime.now()
    return location

def validate_fields(location):
    # --- Field Validation ---
    # Check that all mandatory fields are provided
    missing = [field for field in ['LOCATION_ID', 'LOCATION_NAME', 'SITE_CODE', 'LOCATION_TYPE'] if not location[field]]
    if missing:
        # If any mandatory field is missing, print which ones
        print(f"Mandatory fields are required: {', '.join(missing)}")
        return False
    return True

def check_duplicate(conn, location_id):
    # --- Duplicate Check ---
    # Query the LOC table to see if the LOCATION_ID already exists
    cursor = conn.cursor()
    cursor.execute("SELECT 1 FROM LOC WHERE LOCATION_ID = :id", id=location_id)
    exists = cursor.fetchone() is not None
    cursor.close()
    if exists:
        # If LOCATION_ID exists, inform the user
        print("Location ID already available")
    return exists

def show_test_result(location):
    # --- User Approval (Simulated Test Result) ---
    # Display the location details for user confirmation before insertion
    print("\nSimulated Test Result:")
    for k, v in location.items():
        print(f"{k}: {v}")
    while True:
        # Prompt user for approval
        approval = input("\nDo you approve to create this location in the database? (yes/no): ").strip().lower()
        if approval in ['yes', 'no']:
            return approval == 'yes'
        print("Please enter 'yes' or 'no'.")

def insert_location(conn, location):
    # --- Insert into LOC Table ---
    # Insert the new location data into the LOC table with metadata
    cursor = conn.cursor()
    sql = """
        INSERT INTO LOC (LOCATION_ID, LOCATION_NAME, SITE_CODE, LOCATION_TYPE, CREATED_BY, CREATED_DATE)
        VALUES (:LOCATION_ID, :LOCATION_NAME, :SITE_CODE, :LOCATION_TYPE, :CREATED_BY, :CREATED_DATE)
    """
    cursor.execute(sql, location)
    conn.commit()
    cursor.close()

def fetch_inserted_record(conn, location_id):
    # Fetch the inserted record details for confirmation
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM LOC WHERE LOCATION_ID = :id", id=location_id)
    row = cursor.fetchone()
    columns = [col[0] for col in cursor.description]
    cursor.close()
    return dict(zip(columns, row)) if row else None

def main():
    try:
        # Step 1: Connect to the Oracle database
        conn = get_db_connection()
        # Step 2: Collect location data from user
        location = get_location_input()
        # Step 3: Validate mandatory fields
        if not validate_fields(location):
            return
        # Step 4: Check for duplicate LOCATION_ID
        if check_duplicate(conn, location['LOCATION_ID']):
            return
        # Step 5: Show test result and ask for user approval
        if not show_test_result(location):
            print("Location creation aborted by user")
            return
        # Step 6: Insert the new location into the LOC table
        insert_location(conn, location)
        print("\nLocation successfully created.")
        # Step 7: Fetch and display the inserted record details
        record = fetch_inserted_record(conn, location['LOCATION_ID'])
        print("Inserted Record Details:")
        for k, v in record.items():
            print(f"{k}: {v}")
    except Exception as e:
        # Handle any errors that occur during the process
        print("Error:", e)
    finally:
        try:
            conn.close()
        except:
            pass

if __name__ == "__main__":
    main() 