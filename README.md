Location creation  

**Description :**

This enhanced version of the Warehouse AI Assistant automatically generates location IDs based on zone and aisle information provided by users.

This eliminates the need for manual location ID entry and reduces errors.


**Key Features**

1. Auto-Generated Fields:
 
   LOCATION_ID: Automatically generated based on Zone + Aisle + Sequential Number
- 
   SITE_CODE: Automatically generated based on Zone mapping

2. User-Provided Fields

- LOCATION_NAME: Name of the storage location
- ZONE: Warehouse zone (A, B, C, etc.)
- AISLE: Aisle number (01, 02, etc.)
- LOCATION_TYPE: Type of location (Warehouse, Storage, Shelf, etc.)

3.Location ID Generation Logic

**Setup instruction**

1.Install Python

2. Install Required Python Packages
   
3. This project requires the cx_Oracle package to connect to Oracle databases.
pip install cx_Oracle

3.Oracle Database Access

Ensure you have access to an Oracle database and the credentials (username, password, DSN/connection string).

**Usage**

 **User Experience**
 
- Simplified Input: Users only need to provide zone and aisle
- 
- Reduced Errors: No manual location ID entry
- 
- Consistent Format: All location IDs follow the same pattern
- 
- Automatic Sequencing: No need to track next available numbers

**System Benefits**

- Data Integrity: Ensures unique location IDs
- 
- Scalability: Supports unlimited locations per zone/aisle
- 
- Maintainability: Easy to understand and modify
- 
- Audit Trail: Clear tracking of auto-generated vs. user-provided data
