from flask import Blueprint, render_template, jsonify, g, request
from utils.auth import get_current_user_from_token
from model.login_model import get_all_users
# from model.studyData_model import add_card, update_deckInfo
from dotenv import load_dotenv
import os
import json
import ast
from google import genai
from google.genai import types

load_dotenv()
# blueprint should have a simple import name; the URL is provided by app.register_blueprint
chatProxy_bp = Blueprint('chatProxy', __name__)

GEMINI_API_KEY = os.environ.get('GEMINI_API_KEY')
MODEL_NAME = "gemini-2.5-flash"

# Initialize the Gemini client (lazy-load if key is missing)
client = None
if GEMINI_API_KEY:
    try:
        client = genai.Client(api_key=GEMINI_API_KEY)
    except ValueError as e:
        print(f"Warning: Could not initialize Gemini client: {e}")
else:
    print("Warning: GEMINI_API_KEY not set. AI chat features will not work.")

systemPrompt = (
    "You are an advanced AI assistant integrated into a flashcard web application called 'BookMe'. "
    "Your task is to generate flashcards based on user-provided content. "
    "When given a text input, analyze the content and extract key concepts, definitions, and important information "
    "to create effective flashcards for study purposes. Be sure to create as many flashcards as requested, if specified. "
    "Each flashcard should consist of a 'front' (question or prompt) and a 'back' (answer or explanation). "
    "Ensure that the flashcards are clear, concise, and relevant to the material provided. "
    "Format your response strictly as a single JSON object with the following structure: "
    "Produce exactly one valid JSON object describing a flashcard deck with keys: \"name\" (string), "
    "\"summary\" (string), \"flashcards\" (array of objects with \"front\" and \"back\"), and \"feedback\" (string). "
    "Feedback will be a response back to the user's stored in the JSON with key \"feedback\" (string) a brief (1-3 sentence) message. "
    "Ensure the JSON uses double quotes and is strictly valid JSON. If no flashcards can be generated, return "
    "{\"name\": \"\", \"summary\": \"\", \"flashcards\": [], \"feedback\": \"ERROR: Please try a different request\"}. "
    "The user's request is: "
)

def upload_file_to_gemini(file_path):
    """Uploads a file to Gemini and returns the file object."""
    if not client:
        print("Error: Gemini client not initialized. GEMINI_API_KEY may be missing.")
        return None
    try:
        file = client.files.upload(path=file_path)
        print(f"Uploaded file: {file.name}")
        return file
    except Exception as e:
        print(f"File upload error: {e}")
        return None

@chatProxy_bp.before_request
def require_auth():
    """Set g.current_user or redirect to login."""
    user = get_current_user_from_token()
    # If helper returns a redirect response, just return it
    from flask import redirect
    if not isinstance(user, str):
        return user
    g.current_user = user

@chatProxy_bp.route('/', methods=['POST'], endpoint='chatProxy')
def chat_proxy():
    if not client:
        return jsonify({"error": "AI service not available. GEMINI_API_KEY is not configured."}), 503
    
    user_message = request.form.get('message')
    uploaded_file = request.files.get('file')

    # 1. Handle File Upload (If applicable)
    uploaded_gemini_file = None
    if uploaded_file:
        # Save temporarily and upload to Gemini
        temp_path = f"/tmp/{uploaded_file.filename}"
        uploaded_file.save(temp_path)
        uploaded_gemini_file = upload_file_to_gemini(temp_path)
        uploaded_file.close()
        # Clean up temp file
        try:
            os.remove(temp_path)
        except Exception:
            pass
    
    # 2. Prepare content for Gemini
    fullPrompt = systemPrompt + user_message
    
    # Build the content list for Gemini
    content_parts = [fullPrompt]
    if uploaded_gemini_file:
        content_parts.append(uploaded_gemini_file)

    try:
        # 3. Call Gemini API
        response = client.models.generate_content(
            model=MODEL_NAME,
            contents=content_parts,
            config=types.GenerateContentConfig(
                temperature=0.7,
                max_output_tokens=8192,  # Increased to allow longer responses (Gemini 2.0 supports up to 8192)
            )
        )
        
        # 4. Extract response text
        ai_text = str(response.text).strip()
        
        # 5. Clean and parse JSON response
        jsonResp = ai_text
        
        # Extract JSON from code fence if present (```json ... ``` or ``` ... ```)
        if '```' in jsonResp:
            if '```json' in jsonResp:
                start = jsonResp.find('```json') + 7
                end = jsonResp.find('```', start)
                if end != -1:
                    jsonResp = jsonResp[start:end].strip()
                else:
                    # No closing fence, take everything after opening
                    jsonResp = jsonResp[start:].strip()
            else:
                start = jsonResp.find('```') + 3
                end = jsonResp.find('```', start)
                if end != -1:
                    jsonResp = jsonResp[start:end].strip()
                else:
                    jsonResp = jsonResp[start:].strip()
        
        # Find first { and last } to extract JSON object
        first_brace = jsonResp.find('{')
        last_brace = jsonResp.rfind('}')
        
        if first_brace != -1 and last_brace != -1 and last_brace > first_brace:
            jsonResp = jsonResp[first_brace:last_brace + 1]
        
        # Parse JSON with multiple fallback strategies including truncation handling
        parsed = None
        parse_error = None
        import re
        
        try:
            # 1) Direct JSON parse
            parsed = json.loads(jsonResp)
        except json.JSONDecodeError as e:
            print(f'Initial JSON parse failed: {e}')
            print(f'Attempting to repair truncated JSON...')
            
            # 2) Aggressively repair truncated JSON
            try:
                cleaned = jsonResp
                
                # Strategy: Find last complete flashcard object and truncate there
                # Look for the last occurrence of "},\n" or "}," which indicates a complete flashcard
                last_complete = max(
                    cleaned.rfind('},\n'),
                    cleaned.rfind('},'),
                    cleaned.rfind('}\n')
                )
                
                if last_complete != -1:
                    # Truncate to after the last complete flashcard
                    cleaned = cleaned[:last_complete + 1]
                    
                    # Ensure we're inside the flashcards array - remove any incomplete entry
                    # Close the flashcards array
                    cleaned += '\n  ]'
                    
                    # Add feedback field and close main object
                    cleaned += ',\n  "feedback": "Response was truncated. Some flashcards may be missing."\n}'
                    
                    print(f'Repaired JSON (last 200 chars): ...{cleaned[-200:]}')
                    
                    # Try to parse the repaired JSON
                    parsed = json.loads(cleaned)
                    print(f'Successfully repaired truncated JSON! Recovered {len(parsed.get("flashcards", []))} flashcards.')
                    
            except json.JSONDecodeError as e2:
                print(f'First repair attempt failed: {e2}')
                # 3) More aggressive: remove trailing commas and try again
                try:
                    cleaned = jsonResp
                    
                    # Find last valid closing brace for an object in the flashcards array
                    last_brace = cleaned.rfind('}')
                    if last_brace != -1:
                        # Take everything up to and including that brace
                        cleaned = cleaned[:last_brace + 1]
                        
                        # Check if we need to close the array
                        if '"flashcards"' in cleaned and cleaned.count('[') > cleaned.count(']'):
                            cleaned += '\n  ]'
                        
                        # Check if we need to close the main object
                        if cleaned.count('{') > cleaned.count('}'):
                            cleaned += ',\n  "feedback": "Response truncated"\n}'
                        
                        # Clean up trailing commas
                        cleaned = re.sub(r',(\s*[}\]])', r'\1', cleaned)
                        
                        parsed = json.loads(cleaned)
                        print(f'Second repair succeeded! Recovered {len(parsed.get("flashcards", []))} flashcards.')
                        
                except json.JSONDecodeError as e3:
                    print(f'Second repair attempt failed: {e3}')
                    # 4) Last resort: try ast.literal_eval
                    try:
                        parsed_candidate = ast.literal_eval(jsonResp)
                        parsed = json.loads(json.dumps(parsed_candidate))
                    except Exception as e4:
                        parse_error = f"JSON parse error: {str(e)}"
                        print(f'All repair attempts failed.')
                        print(f'AI raw response (last 500 chars): ...{ai_text[-500:]}')
                        print(f'Extracted JSON (last 500 chars): ...{jsonResp[-500:]}')
        
        # Extract feedback from parsed JSON if present
        feedback = ''
        if parsed and isinstance(parsed, dict):
            feedback = parsed.pop('feedback', '')  # Remove feedback from JSON, use separately
        
        if parsed is not None:
            return jsonify({
                "status": "success", 
                "json": parsed, 
                "feedback": feedback
            })
        else:
            # Return error with raw response for debugging
            return jsonify({
                "status": "error",
                "message": parse_error or "Failed to parse AI response",
                "raw_response": ai_text[:500]  # First 500 chars for debugging
            }), 500
    except Exception as e:
        print(f"Gemini API Error: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500
