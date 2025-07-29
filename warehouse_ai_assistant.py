import cx_Oracle
import getpass
from datetime import datetime
import re
import json

class WarehouseAIAssistant:
    def __init__(self):
        self.conn = None
        self.current_location = {}
        self.conversation_state = "greeting"
        self.required_fields = ['LOCATION_ID', 'LOCATION_NAME', 'SITE_CODE', 'LOCATION_TYPE']
        
    def connect_database(self):
        """Establish connection to Oracle database"""
        try:
            print("🤖 AI Assistant: Hello! I'm your Warehouse Location Management Assistant.")
            print("Let me connect to the database first...")
            
            username = input("Enter Oracle username: ")
            password = getpass.getpass("Enter Oracle password: ")
            dsn = input("Enter Oracle DSN (e.g., host:port/service): ")
            
            self.conn = cx_Oracle.connect(username, password, dsn)
            print("✅ Database connected successfully!")
            return True
        except Exception as e:
            print(f"❌ Database connection failed: {e}")
            return False
    
    def extract_location_info(self, user_input):
        """Extract location information from natural language input"""
        user_input = user_input.lower()
        
        # Extract LOCATION_ID (numbers)
        location_id_match = re.search(r'location\s*(?:id|#)?\s*[:\-]?\s*(\d+)', user_input)
        if location_id_match:
            self.current_location['LOCATION_ID'] = location_id_match.group(1)
        
        # Extract LOCATION_NAME (quoted text or after "name")
        name_match = re.search(r'name\s*[:\-]?\s*["\']([^"\']+)["\']', user_input)
        if not name_match:
            name_match = re.search(r'name\s*[:\-]?\s*(\w+(?:\s+\w+)*)', user_input)
        if name_match:
            self.current_location['LOCATION_NAME'] = name_match.group(1).title()
        
        # Extract SITE_CODE (alphanumeric codes)
        site_match = re.search(r'site\s*(?:code)?\s*[:\-]?\s*([a-zA-Z0-9]+)', user_input)
        if site_match:
            self.current_location['SITE_CODE'] = site_match.group(1).upper()
        
        # Extract LOCATION_TYPE
        type_keywords = {
            'warehouse': 'Warehouse',
            'storage': 'Storage',
            'shelf': 'Shelf',
            'rack': 'Rack',
            'zone': 'Zone',
            'area': 'Area',
            'section': 'Section',
            'room': 'Room',
            'floor': 'Floor'
        }
        
        for keyword, location_type in type_keywords.items():
            if keyword in user_input:
                self.current_location['LOCATION_TYPE'] = location_type
                break
    
    def validate_fields(self):
        """Validate all required fields are present"""
        missing_fields = []
        for field in self.required_fields:
            if field not in self.current_location or not self.current_location[field]:
                missing_fields.append(field)
        
        if missing_fields:
            return False, f"Missing required information: {', '.join(missing_fields)}"
        return True, "All fields validated successfully"
    
    def check_duplicate(self, location_id):
        """Check if LOCATION_ID already exists"""
        try:
            cursor = self.conn.cursor()
            cursor.execute("SELECT 1 FROM LOC WHERE LOCATION_ID = :id", id=location_id)
            exists = cursor.fetchone() is not None
            cursor.close()
            return exists
        except Exception as e:
            print(f"❌ Error checking duplicates: {e}")
            return False
    
    def insert_location(self):
        """Insert new location into database"""
        try:
            self.current_location['CREATED_BY'] = 'AI_Assistant'
            self.current_location['CREATED_DATE'] = datetime.now()
            
            cursor = self.conn.cursor()
            sql = """
                INSERT INTO LOC (LOCATION_ID, LOCATION_NAME, SITE_CODE, LOCATION_TYPE, CREATED_BY, CREATED_DATE)
                VALUES (:LOCATION_ID, :LOCATION_NAME, :SITE_CODE, :LOCATION_TYPE, :CREATED_BY, :CREATED_DATE)
            """
            cursor.execute(sql, self.current_location)
            self.conn.commit()
            cursor.close()
            return True, "Location created successfully!"
        except Exception as e:
            return False, f"Database error: {e}"
    
    def get_location_summary(self):
        """Generate a summary of the location details"""
        summary = "📋 Location Summary:\n"
        for field in self.required_fields:
            if field in self.current_location:
                summary += f"   • {field}: {self.current_location[field]}\n"
        return summary
    
    def process_user_input(self, user_input):
        """Process user input and provide appropriate response"""
        user_input = user_input.strip()
        
        # Handle conversation flow
        if self.conversation_state == "greeting":
            if any(word in user_input.lower() for word in ['create', 'add', 'new', 'location']):
                self.conversation_state = "collecting_info"
                return "🤖 AI Assistant: Great! I'll help you create a new storage location. Please provide the location details. You can say something like:\n'Create location ID 101, name \"Main Storage Area\", site code WH1, type warehouse'"
            else:
                return "🤖 AI Assistant: I can help you create new storage locations in the warehouse. Say 'create location' or 'add new location' to get started!"
        
        elif self.conversation_state == "collecting_info":
            # Extract information from user input
            self.extract_location_info(user_input)
            
            # Check if we have all required information
            is_valid, message = self.validate_fields()
            
            if is_valid:
                # Check for duplicates
                if self.check_duplicate(self.current_location['LOCATION_ID']):
                    self.conversation_state = "greeting"
                    self.current_location = {}
                    return "❌ Location ID already exists. Please use a different ID."
                
                # Show summary and ask for approval
                self.conversation_state = "approval"
                summary = self.get_location_summary()
                return f"{summary}\n🤖 AI Assistant: Does this look correct? Type 'yes' to create the location or 'no' to start over."
            else:
                return f"🤖 AI Assistant: {message}\nPlease provide the missing information."
        
        elif self.conversation_state == "approval":
            if user_input.lower() in ['yes', 'y', 'confirm', 'create']:
                # Insert location
                success, message = self.insert_location()
                if success:
                    self.conversation_state = "greeting"
                    self.current_location = {}
                    return f"✅ {message}\n🤖 AI Assistant: The location has been added to the database. Is there anything else I can help you with?"
                else:
                    self.conversation_state = "greeting"
                    self.current_location = {}
                    return f"❌ {message}\n🤖 AI Assistant: Let's try again. Say 'create location' to start over."
            elif user_input.lower() in ['no', 'n', 'cancel', 'abort']:
                self.conversation_state = "greeting"
                self.current_location = {}
                return "🤖 AI Assistant: Location creation cancelled. Say 'create location' if you want to try again."
            else:
                return "🤖 AI Assistant: Please type 'yes' to confirm or 'no' to cancel."
        
        # Fallback
        return "🤖 AI Assistant: I didn't understand that. Say 'create location' to add a new storage location."
    
    def run(self):
        """Main conversation loop"""
        if not self.connect_database():
            return
        
        print("\n🤖 AI Assistant: I'm ready to help you manage warehouse locations!")
        print("Type 'quit' to exit the assistant.\n")
        
        while True:
            try:
                user_input = input("👤 You: ")
                
                if user_input.lower() in ['quit', 'exit', 'bye']:
                    print("🤖 AI Assistant: Goodbye! Have a great day!")
                    break
                
                response = self.process_user_input(user_input)
                print(response + "\n")
                
            except KeyboardInterrupt:
                print("\n🤖 AI Assistant: Goodbye! Have a great day!")
                break
            except Exception as e:
                print(f"❌ Error: {e}")
        
        if self.conn:
            self.conn.close()

def main():
    """Main function to start the AI assistant"""
    assistant = WarehouseAIAssistant()
    assistant.run()

if __name__ == "__main__":
    main() 
