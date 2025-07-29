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
        self.required_fields = ['LOCATION_NAME', 'ZONE', 'AISLE', 'LOCATION_TYPE']
        self.auto_generated_fields = ['LOCATION_ID', 'SITE_CODE']
        self.validation_errors = []
        
    def connect_database(self):
        """Establish connection to Oracle database"""
        try:
            print("🤖 AI Assistant: Hello! I'm your Warehouse Location Management Assistant.")
            print("I can automatically generate location IDs based on zone and aisle information.")
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
    
    def validate_zone(self, zone):
        """Validate zone format and range"""
        if not zone:
            return False, "Zone is required"
        
        if not re.match(r'^[A-Z]$', zone):
            return False, "Zone must be a single letter (A-Z)"
        
        # Check if zone is within valid range (A-Z)
        if not ('A' <= zone <= 'Z'):
            return False, "Zone must be between A and Z"
        
        return True, "Zone is valid"
    
    def validate_aisle(self, aisle):
        """Validate aisle format and range"""
        if not aisle:
            return False, "Aisle is required"
        
        if not re.match(r'^\d{1,2}$', aisle):
            return False, "Aisle must be 1-2 digits (01-99)"
        
        aisle_num = int(aisle)
        if aisle_num < 1 or aisle_num > 99:
            return False, "Aisle number must be between 01 and 99"
        
        return True, "Aisle is valid"
    
    def validate_location_name(self, name):
        """Validate location name"""
        if not name:
            return False, "Location name is required"
        
        if len(name.strip()) < 3:
            return False, "Location name must be at least 3 characters long"
        
        if len(name.strip()) > 100:
            return False, "Location name must be less than 100 characters"
        
        # Check for special characters that might cause issues
        if re.search(r'[<>"\']', name):
            return False, "Location name contains invalid characters"
        
        return True, "Location name is valid"
    
    def validate_location_type(self, location_type):
        """Validate location type"""
        if not location_type:
            return False, "Location type is required"
        
        valid_types = [
            'Warehouse', 'Storage', 'Shelf', 'Rack', 'Zone', 
            'Area', 'Section', 'Room', 'Floor', 'Bay', 'Slot'
        ]
        
        if location_type not in valid_types:
            return False, f"Location type must be one of: {', '.join(valid_types)}"
        
        return True, "Location type is valid"
    
    def comprehensive_validation(self):
        """Perform comprehensive validation of all fields"""
        self.validation_errors = []
        is_valid = True
        
        # Validate each required field
        for field in self.required_fields:
            value = self.current_location.get(field, '').strip()
            
            if field == 'LOCATION_NAME':
                field_valid, message = self.validate_location_name(value)
            elif field == 'ZONE':
                field_valid, message = self.validate_zone(value)
            elif field == 'AISLE':
                field_valid, message = self.validate_aisle(value)
            elif field == 'LOCATION_TYPE':
                field_valid, message = self.validate_location_type(value)
            else:
                field_valid, message = (bool(value), f"{field} is required")
            
            if not field_valid:
                self.validation_errors.append(f"• {field}: {message}")
                is_valid = False
        
        # Additional business logic validations
        if is_valid:
            # Check for duplicate location names in the same zone/aisle
            duplicate_check = self.check_duplicate_location_name()
            if duplicate_check:
                self.validation_errors.append(f"• Duplicate: {duplicate_check}")
                is_valid = False
        
        return is_valid, self.validation_errors
    
    def check_duplicate_location_name(self):
        """Check if location name already exists in the same zone/aisle"""
        try:
            cursor = self.conn.cursor()
            cursor.execute("""
                SELECT LOCATION_NAME 
                FROM LOC 
                WHERE LOCATION_NAME = :name 
                AND LOCATION_ID LIKE :pattern
            """, {
                'name': self.current_location['LOCATION_NAME'],
                'pattern': f"{self.current_location['ZONE']}{self.current_location['AISLE']}%"
            })
            
            existing = cursor.fetchone()
            cursor.close()
            
            if existing:
                return f"Location name '{self.current_location['LOCATION_NAME']}' already exists in Zone {self.current_location['ZONE']}, Aisle {self.current_location['AISLE']}"
            
            return None
            
        except Exception as e:
            print(f"❌ Error checking duplicate location name: {e}")
            return None
    
    def get_next_location_id(self, zone, aisle):
        """Generate the next available location ID based on zone and aisle"""
        try:
            cursor = self.conn.cursor()
            
            # Search for existing locations with the same zone and aisle pattern
            pattern = f"{zone}{aisle}%"
            cursor.execute("""
                SELECT LOCATION_ID 
                FROM LOC 
                WHERE LOCATION_ID LIKE :pattern 
                ORDER BY LOCATION_ID DESC
            """, pattern=pattern)
            
            existing_ids = cursor.fetchall()
            cursor.close()
            
            if existing_ids:
                # Get the highest existing ID and increment
                last_id = existing_ids[0][0]
                # Extract the numeric part and increment
                numeric_part = int(last_id[len(zone) + len(aisle):])
                next_number = numeric_part + 1
            else:
                # No existing locations for this zone/aisle, start with 001
                next_number = 1
            
            # Format: ZONE + AISLE + 3-digit number (e.g., A01A001, B02B001)
            location_id = f"{zone}{aisle}{next_number:03d}"
            return location_id
            
        except Exception as e:
            print(f"❌ Error generating location ID: {e}")
            return None
    
    def generate_site_code(self, zone):
        """Generate site code based on zone"""
        # Simple mapping: Zone A = WH1, Zone B = WH2, etc.
        zone_mapping = {
            'A': 'WH1', 'B': 'WH2', 'C': 'WH3', 'D': 'WH4', 'E': 'WH5',
            'F': 'WH6', 'G': 'WH7', 'H': 'WH8', 'I': 'WH9', 'J': 'WH10'
        }
        return zone_mapping.get(zone.upper(), 'WH0')
    
    def extract_location_info(self, user_input):
        """Extract location information from natural language input"""
        user_input = user_input.lower()
        
        # Extract LOCATION_NAME (quoted text or after "name")
        name_match = re.search(r'name\s*[:\-]?\s*["\']([^"\']+)["\']', user_input)
        if not name_match:
            name_match = re.search(r'name\s*[:\-]?\s*(\w+(?:\s+\w+)*)', user_input)
        if name_match:
            self.current_location['LOCATION_NAME'] = name_match.group(1).title()
        
        # Extract ZONE (single letter, usually A-Z)
        zone_match = re.search(r'zone\s*[:\-]?\s*([a-zA-Z])', user_input)
        if zone_match:
            self.current_location['ZONE'] = zone_match.group(1).upper()
        
        # Extract AISLE (numbers, usually 01-99)
        aisle_match = re.search(r'aisle\s*[:\-]?\s*(\d{1,2})', user_input)
        if aisle_match:
            self.current_location['AISLE'] = aisle_match.group(1).zfill(2)  # Pad with leading zero
        
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
            'floor': 'Floor',
            'bay': 'Bay',
            'slot': 'Slot'
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
    
    def generate_auto_fields(self):
        """Generate automatic fields based on user input"""
        try:
            zone = self.current_location.get('ZONE')
            aisle = self.current_location.get('AISLE')
            
            if zone and aisle:
                # Generate location ID
                location_id = self.get_next_location_id(zone, aisle)
                if location_id:
                    self.current_location['LOCATION_ID'] = location_id
                
                # Generate site code
                site_code = self.generate_site_code(zone)
                self.current_location['SITE_CODE'] = site_code
                
                return True, "Auto-generated fields created successfully"
            else:
                return False, "Cannot generate auto fields without zone and aisle"
                
        except Exception as e:
            return False, f"Error generating auto fields: {e}"
    
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
        """Insert new location into database with final validation"""
        try:
            # Final validation before insertion
            is_valid, errors = self.comprehensive_validation()
            if not is_valid:
                return False, f"Validation failed:\n" + "\n".join(errors)
            
            # Check for duplicate location ID
            if self.check_duplicate(self.current_location['LOCATION_ID']):
                return False, "Generated location ID already exists. Please try a different zone or aisle combination."
            
            # Add metadata
            self.current_location['CREATED_BY'] = 'AI_Assistant'
            self.current_location['CREATED_DATE'] = datetime.now()
            
            # Insert into database
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
        
        # Show user-provided fields
        for field in self.required_fields:
            if field in self.current_location:
                summary += f"   • {field}: {self.current_location[field]}\n"
        
        # Show auto-generated fields
        summary += "\n🔄 Auto-Generated Fields:\n"
        for field in self.auto_generated_fields:
            if field in self.current_location:
                summary += f"   • {field}: {self.current_location[field]}\n"
        
        return summary
    
    def get_validation_summary(self):
        """Generate validation summary"""
        if not self.validation_errors:
            return "✅ All validations passed successfully!"
        
        summary = "❌ Validation Errors Found:\n"
        for error in self.validation_errors:
            summary += f"   {error}\n"
        return summary
    
    def process_user_input(self, user_input):
        """Process user input and provide appropriate response"""
        user_input = user_input.strip()
        
        # Handle conversation flow
        if self.conversation_state == "greeting":
            if any(word in user_input.lower() for word in ['create', 'add', 'new', 'location']):
                self.conversation_state = "collecting_info"
                return "🤖 AI Assistant: Great! I'll help you create a new storage location. I'll automatically generate the location ID and site code based on your zone and aisle information.\n\nPlease provide:\n• Location name (3-100 characters)\n• Zone (A-Z)\n• Aisle number (01-99)\n• Location type (Warehouse, Storage, Shelf, Rack, Zone, Area, Section, Room, Floor, Bay, Slot)\n\nYou can say something like:\n'Create location name \"Main Storage Area\", zone A, aisle 01, type warehouse'"
            else:
                return "🤖 AI Assistant: I can help you create new storage locations in the warehouse. I'll automatically generate location IDs for you! Say 'create location' or 'add new location' to get started!"
        
        elif self.conversation_state == "collecting_info":
            # Extract information from user input
            self.extract_location_info(user_input)
            
            # Perform comprehensive validation
            is_valid, validation_errors = self.comprehensive_validation()
            
            if is_valid:
                # Generate automatic fields
                auto_success, auto_message = self.generate_auto_fields()
                
                if auto_success:
                    # Show summary and ask for approval
                    self.conversation_state = "approval"
                    summary = self.get_location_summary()
                    validation_summary = self.get_validation_summary()
                    return f"{summary}\n{validation_summary}\n🤖 AI Assistant: Does this look correct? Type 'yes' to create the location or 'no' to start over."
                else:
                    return f"🤖 AI Assistant: {auto_message}\nPlease provide valid zone and aisle information."
            else:
                # Show validation errors and ask for correction
                validation_summary = self.get_validation_summary()
                return f"🤖 AI Assistant: {validation_summary}\nPlease correct the errors and provide the missing information."
        
        elif self.conversation_state == "approval":
            if user_input.lower() in ['yes', 'y', 'confirm', 'create']:
                # Insert location with final validation
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
        print("I'll automatically generate location IDs based on zone and aisle information.")
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
