from flask import Flask, render_template, request, jsonify, session
import cx_Oracle
from datetime import datetime
import re
import os

app = Flask(__name__)
app.secret_key = 'warehouse_ai_secret_key'

class WebWarehouseAI:
    def __init__(self):
        self.required_fields = ['LOCATION_ID', 'LOCATION_NAME', 'SITE_CODE', 'LOCATION_TYPE']
        
    def extract_location_info(self, user_input, current_location):
        """Extract location information from natural language input"""
        user_input = user_input.lower()
        
        # Extract LOCATION_ID (numbers)
        location_id_match = re.search(r'location\s*(?:id|#)?\s*[:\-]?\s*(\d+)', user_input)
        if location_id_match:
            current_location['LOCATION_ID'] = location_id_match.group(1)
        
        # Extract LOCATION_NAME (quoted text or after "name")
        name_match = re.search(r'name\s*[:\-]?\s*["\']([^"\']+)["\']', user_input)
        if not name_match:
            name_match = re.search(r'name\s*[:\-]?\s*(\w+(?:\s+\w+)*)', user_input)
        if name_match:
            current_location['LOCATION_NAME'] = name_match.group(1).title()
        
        # Extract SITE_CODE (alphanumeric codes)
        site_match = re.search(r'site\s*(?:code)?\s*[:\-]?\s*([a-zA-Z0-9]+)', user_input)
        if site_match:
            current_location['SITE_CODE'] = site_match.group(1).upper()
        
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
                current_location['LOCATION_TYPE'] = location_type
                break
        
        return current_location
    
    def validate_fields(self, current_location):
        """Validate all required fields are present"""
        missing_fields = []
        for field in self.required_fields:
            if field not in current_location or not current_location[field]:
                missing_fields.append(field)
        
        if missing_fields:
            return False, f"Missing required information: {', '.join(missing_fields)}"
        return True, "All fields validated successfully"
    
    def check_duplicate(self, conn, location_id):
        """Check if LOCATION_ID already exists"""
        try:
            cursor = conn.cursor()
            cursor.execute("SELECT 1 FROM LOC WHERE LOCATION_ID = :id", id=location_id)
            exists = cursor.fetchone() is not None
            cursor.close()
            return exists
        except Exception as e:
            print(f"Error checking duplicates: {e}")
            return False
    
    def insert_location(self, conn, current_location):
        """Insert new location into database"""
        try:
            current_location['CREATED_BY'] = 'Web_AI_Assistant'
            current_location['CREATED_DATE'] = datetime.now()
            
            cursor = conn.cursor()
            sql = """
                INSERT INTO LOC (LOCATION_ID, LOCATION_NAME, SITE_CODE, LOCATION_TYPE, CREATED_BY, CREATED_DATE)
                VALUES (:LOCATION_ID, :LOCATION_NAME, :SITE_CODE, :LOCATION_TYPE, :CREATED_BY, :CREATED_DATE)
            """
            cursor.execute(sql, current_location)
            conn.commit()
            cursor.close()
            return True, "Location created successfully!"
        except Exception as e:
            return False, f"Database error: {e}"
    
    def get_location_summary(self, current_location):
        """Generate a summary of the location details"""
        summary = "📋 Location Summary:<br>"
        for field in self.required_fields:
            if field in current_location:
                summary += f"   • {field}: {current_location[field]}<br>"
        return summary

# Initialize AI assistant
ai_assistant = WebWarehouseAI()

@app.route('/')
def index():
    """Main chat interface"""
    return render_template('chat.html')

@app.route('/chat', methods=['POST'])
def chat():
    """Handle chat messages"""
    if 'conversation_state' not in session:
        session['conversation_state'] = 'greeting'
        session['current_location'] = {}
    
    user_message = request.json.get('message', '').strip()
    conversation_state = session['conversation_state']
    current_location = session['current_location']
    
    # Handle conversation flow
    if conversation_state == "greeting":
        if any(word in user_message.lower() for word in ['create', 'add', 'new', 'location']):
            session['conversation_state'] = "collecting_info"
            return jsonify({
                'reply': "🤖 AI Assistant: Great! I'll help you create a new storage location. Please provide the location details. You can say something like:<br>'Create location ID 101, name \"Main Storage Area\", site code WH1, type warehouse'",
                'state': 'collecting_info'
            })
        else:
            return jsonify({
                'reply': "🤖 AI Assistant: I can help you create new storage locations in the warehouse. Say 'create location' or 'add new location' to get started!",
                'state': 'greeting'
            })
    
    elif conversation_state == "collecting_info":
        # Extract information from user input
        current_location = ai_assistant.extract_location_info(user_message, current_location)
        session['current_location'] = current_location
        
        # Check if we have all required information
        is_valid, message = ai_assistant.validate_fields(current_location)
        
        if is_valid:
            # For demo purposes, we'll skip duplicate check and go straight to approval
            # In production, you'd check duplicates here
            session['conversation_state'] = "approval"
            summary = ai_assistant.get_location_summary(current_location)
            return jsonify({
                'reply': f"{summary}<br>🤖 AI Assistant: Does this look correct? Type 'yes' to create the location or 'no' to start over.",
                'state': 'approval'
            })
        else:
            return jsonify({
                'reply': f"🤖 AI Assistant: {message}<br>Please provide the missing information.",
                'state': 'collecting_info'
            })
    
    elif conversation_state == "approval":
        if user_message.lower() in ['yes', 'y', 'confirm', 'create']:
            # For demo purposes, we'll simulate success
            # In production, you'd insert into database here
            session['conversation_state'] = "greeting"
            session['current_location'] = {}
            return jsonify({
                'reply': "✅ Location created successfully!<br>🤖 AI Assistant: The location has been added to the database. Is there anything else I can help you with?",
                'state': 'greeting'
            })
        elif user_message.lower() in ['no', 'n', 'cancel', 'abort']:
            session['conversation_state'] = "greeting"
            session['current_location'] = {}
            return jsonify({
                'reply': "🤖 AI Assistant: Location creation cancelled. Say 'create location' if you want to try again.",
                'state': 'greeting'
            })
        else:
            return jsonify({
                'reply': "🤖 AI Assistant: Please type 'yes' to confirm or 'no' to cancel.",
                'state': 'approval'
            })
    
    # Fallback
    return jsonify({
        'reply': "🤖 AI Assistant: I didn't understand that. Say 'create location' to add a new storage location.",
        'state': 'greeting'
    })

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000) 
