from flask import Blueprint, render_template, jsonify, g, request
from utils.auth import get_current_user_from_token
from model.login_model import get_all_users
# from model.studyData_model import add_card, update_deckInfo
import requests
from dotenv import load_dotenv
import os
import json
import ast

load_dotenv()
# blueprint should have a simple import name; the URL is provided by app.register_blueprint
chatProxy_bp = Blueprint('chatProxy', __name__)
OPENWEBUI_API_URL = os.environ.get('OPENWEBUI_API_URL', 'http://ai.spencer-anderson.com/api/')
OPENWEBUI_API_KEY = os.environ.get('OPENWEBUI_API_KEY')

model = 'mistral:7b'#'gemma3n:e2b'#"dolphin-phi:latest"#'gemma3n:e2b'

systemPrompt = (
    "You are an advanced AI assistant integrated into a flashcard web application called 'BookMe'. "
    "Your task is to generate flashcards based on user-provided content. "
    "When given a text input, analyze the content and extract key concepts, definitions, and important information "
    "to create effective flashcards for study purposes. Be sure to create as many flashcards as requested, if specified."
    "Each flashcard should consist of a 'front' (question or prompt) and a 'back' (answer or explanation). "
    "Ensure that the flashcards are clear, concise, and relevant to the material provided. "
    "Format your response strictly as a single JSON object with the following structure: "
    "Produce exactly one valid JSON object describing a flashcard deck with keys: \"name\" (string), "
    "\"summary\" (string), \"flashcards\" (array of objects with \"front\" and \"back\"), and \"feedback\" (string). "
    "Feedback will be a response back to the user's stored in the JSON with key \"feedback\" (string) a brief (1-3 sentence) message. "
    "Ensure the JSON uses double quotes and is strictly valid JSON. If no flashcards can be generated, return "
    "{\"name\": \"\", \"summary\": \"\", \"flashcards\": [], \"feedback\": 'ERROR: Please try a different request'}. "
    "The user's request is: "
)

def upload_file(file_path):
    """Uploads a file to OpenWebUI and returns the response JSON."""
    import mimetypes
    url = OPENWEBUI_API_URL.rstrip('/') + "/v1/files/"
    headers = {"Authorization": f"Bearer {OPENWEBUI_API_KEY}", "Accept": "application/json"}
    filename = os.path.basename(file_path)
    mimetype = mimetypes.guess_type(filename)[0] or 'application/octet-stream'
    # Use a context manager to ensure the file handle is closed after upload
    with open(file_path, 'rb') as fh:
        files = {"file": (filename, fh, mimetype)}
        response = requests.post(url, headers=headers, files=files, timeout=120)
    # forward upstream response (may raise on non-json)
    try:
        print(response.status_code, response.text)
        return response.json()
    except Exception:
        # return a dict with status/text for debugging
        return {"status_code": response.status_code, "text": response.text}

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
    user_message = request.form.get('message')
    uploaded_file = request.files.get('file')

    # 1. Handle File Upload (If applicable)
    # OpenWebUI usually requires a 2-step process: Upload file -> Get ID -> Chat with ID.
    # For this example, we will assume we are sending text, or processing the file locally first.
    uploadId = []
    if uploaded_file:
        # Example: Read file content strictly for context (simplest approach)
        # In production, you might upload this to OpenWebUI's /v1/files endpoint first
        #file_content = uploaded_file.read().decode('utf-8', errors='ignore')
        #file_context = f"\n\nContext from uploaded file ({uploaded_file.filename}):\n{file_content[:2000]}..." # Truncate for safety
        temp_path = f"/tmp/{uploaded_file.filename}"
        uploaded_file.save(temp_path)
        upload_response = upload_file(temp_path)
        if 'id' in upload_response:
            uploadId.append(upload_response['id'])
        file_context = f"\n\n[File uploaded with ID: {upload_response.get('id', 'N/A')}]"
        uploaded_file.close()
    # 2. Prepare Payload for OpenWebUI
    # OpenWebUI is generally OpenAI compatible
    fullPrompt = systemPrompt + user_message
    
    payload = {
        'model': model,
        'messages': [{'role': 'user', 'content': fullPrompt}],
        'files': [{'type': 'file', 'id': file_id} for file_id in uploadId],
        "max_tokens": 800,
        "enable_web_search": True
    } 

    headers = {
        "Authorization": f"Bearer {OPENWEBUI_API_KEY}",
        "Content-Type": "application/json"
    }

    try:
        # 3. Send to OpenWebUI
        response = requests.post(OPENWEBUI_API_URL + 'chat/completions', json=payload, headers=headers)
        response.raise_for_status() # Raise error for bad status codes
        
        # 4. Return result to Frontend
        ai_data = response.json()
        # Extract the actual text from the OpenAI-style response
        ai_text = ai_data['choices'][0]['message']['content']
        
        #return jsonify({"status": "success", "reply": ai_text})
        jsonResp = ai_text.split('## Feedback:')[0].strip()

        # Safely extract JSON code fence if present. AI responses sometimes wrap JSON
        # in ```json ... ``` or plain ``` ... ```. Use find() to avoid ValueError.
        extracted = None
        start_tag = '```json'
        start = jsonResp.find(start_tag)
        if start != -1:
            start += len(start_tag)
            end = jsonResp.find('```', start)
            extracted = jsonResp[start:end].strip() if end != -1 else jsonResp[start:].strip()
        else:
            # Fallback: look for any triple-backtick block
            start = jsonResp.find('```')
            if start != -1:
                start += 3
                end = jsonResp.find('```', start)
                extracted = jsonResp[start:end].strip() if end != -1 else jsonResp[start:].strip()

        if extracted is None:
            # No fenced block found; use the whole pre-feedback text
            extracted = jsonResp

        # Remove any stray backticks and whitespace
        jsonResp = extracted.replace('```', '').strip()
        feedback = ai_text.split('## Feedback:')[1].strip() if '## Feedback:' in ai_text else ''

        # Validate JSON. Try a direct parse first, then a fallback extracting the
        # first {...} object if possible. If parsing succeeds return the parsed
        # JSON object; otherwise return the raw string plus a parse_error message
        # so the frontend can still show the content and let the user decide.
        parsed = None
        parse_error = None
        # 1) Try strict JSON first
        try:
            parsed = json.loads(jsonResp)
        except Exception as e_json:
            # 2) Try ast.literal_eval to handle Python-style dicts (single quotes)
            try:
                parsed_candidate = ast.literal_eval(jsonResp)
                # Normalize via json.dumps -> json.loads to ensure JSON-serializable types
                parsed = json.loads(json.dumps(parsed_candidate))
            except Exception:
                # 3) Fallback: try to extract braced substring then try a conservative single-quote->double-quote fix
                try:
                    s = jsonResp.find('{')
                    epos = jsonResp.rfind('}')
                    if s != -1 and epos != -1 and epos > s:
                        candidate = jsonResp[s:epos+1]
                        try:
                            parsed = json.loads(candidate)
                            jsonResp = candidate
                        except Exception:
                            # try replacing single quotes with double quotes (conservative)
                            candidate2 = candidate.replace("'", '"')
                            parsed = json.loads(candidate2)
                            jsonResp = candidate2
                    else:
                        # as a last resort, try replacing single quotes globally and parse
                        candidate2 = jsonResp.replace("'", '"')
                        parsed = json.loads(candidate2)
                        jsonResp = candidate2
                except Exception as e_final:
                    parse_error = str(e_json)
                    # log the failure for debugging
                    print('Failed to parse JSON from AI response (json loads & fallbacks):', e_json)
                    print('AI raw response:', ai_text)

        if parsed is not None:
            return jsonify({"status": "success", "json": parsed, "feedback": feedback})
        else:
            # Return the raw string plus parse error info (frontend can handle string or object)
            payload = {"status": "success", "json": jsonResp, "feedback": feedback}
            if parse_error:
                payload['parse_error'] = parse_error
            return jsonify(payload)
    except requests.exceptions.RequestException as e:
        print(f"API Error: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500
