from flask import Flask, request, jsonify, render_template
from flask_cors import CORS
from groq import Groq
import os
from dotenv import load_dotenv  # <--- Add this import

# --- Configuration ---
load_dotenv()
app = Flask(__name__)
CORS(app)  # Enable CORS for all routes

# --- New Route to serve the HTML ---
@app.route('/')
def home():
    """Serves the index.html file from the templates folder."""
    return render_template(
        'index.html',
        supabase_url=os.getenv('SUPABASE_URL', ''),
        supabase_anon_key=os.getenv('SUPABASE_ANON_KEY', '')
    )

# Initialize Groq client lazily so a missing/invalid API key doesn't crash
# the whole serverless function on import (which would 500 every route,
# not just /api/chat).
GROQ_API_KEY = os.getenv('GROQ_API_KEY')
client = None
client_init_error = None

if GROQ_API_KEY:
    try:
        client = Groq(api_key=GROQ_API_KEY)
    except Exception as e:
        client_init_error = str(e)
else:
    client_init_error = "GROQ_API_KEY environment variable is not set"

MODEL_NAME = "openai/gpt-oss-20b"

# --- Farm Knowledge Base and Persona (System Instruction) ---
WWF_SYSTEM_INSTRUCTION = """
You are the WWF AI, a friendly, accurate, and knowledgeable customer service agent for Willy's Wing Farm.
Your primary goal is to answer customer queries concisely and professionally, using the following farm-specific facts.

--- WILLY'S WING FARM KNOWLEDGE BASE ---
1.  **Contact & Logistics:**
    -   Address: Makhonge, Tongaren Constituency, Bungoma County.
    -   Email: willyswingfarm@gmail.com
    -   Phone: +254706809000.
    -   Hours of Operation: Monday to Saturday, 8:00 AM to 4:00 PM (for pickups).
    -   Sourcing: All birds are raised using **Organic Feed** methods.
    -   For up-to-date news and community: Direct clients to the WhatsApp group link: https://chat.whatsapp.com/KUDjHkQxhkvIkbwFOzKZZp?mode=hqrc

2.  **Products & Services:**
    -   The farm's primary product is 1-month-old chicks (Kienyeji, Layers, Broilers - subject to availability set by admin).
    -   The farm also sells: Eggs, Meat, Live Birds, Poultry Manure, Organic Fertiliser Bags, Feed Supply, Poultry Equipment (drinkers, feeders, brooders), Portable Structures, and Poultry Medicines.
    -   Special Services: Farm tours, Educational programs, Local delivery, Online courses, and Poultry events.
    -   Pricing for chicks is set dynamically by the admin - tell customers to check the website's poultry listing for current chick prices or ask the admin directly.

3.  **Pricing (Eggs):**
    -   Chicken Eggs: KES 180 per dozen.
    -   Duck Eggs: KES 600 per dozen.
    -   Guinea Fowl Eggs: KES 1,200 per dozen.
    -   Turkey Eggs: KES 2,400 per dozen.
    -   Goose Eggs: KES 200 per piece.

4.  **Policies:**
    -   **Pick-up:** Available at the farm Mon-Sat, 8:00 AM to 4:00 PM.
    -   **Delivery:** Available; transportation charges apply depending on the location.
    -   **Cracked Egg Discount:** A 50% discount is offered for every egg cracked during transportation.
    -   **Payment:** For payment, once your order is confirmed by our team, you will be instructed to send payment via M-Pesa to 0706809000 (Willy's Wing Farm). Do not send payment before receiving confirmation.

5.  **General Knowledge Constraint:**
    -   When asked about general bird characteristics, care, or non-farm-specific facts (like general meat weights), you MUST ONLY provide basic, high-level information. Detailed, in-depth knowledge on bird care and characteristics is reserved for the premium members of the website.
"""


@app.route('/api/chat', methods=['POST'])
def chat():
    """
    API endpoint to handle chat messages from the frontend.
    Expects JSON: {"message": "user's question"}
    Returns JSON: {"response": "AI's answer"}
    """
    if client is None:
        # This is almost always the real cause of a 500 here: the
        # GROQ_API_KEY env var isn't set (or is invalid) on the deployment.
        return jsonify({
            "error": f"Groq client not initialized: {client_init_error}. "
                      f"Check that GROQ_API_KEY is set in your Vercel project's "
                      f"Environment Variables (Settings > Environment Variables), "
                      f"then redeploy."
        }), 500

    try:
        data = request.get_json()

        if not data or 'message' not in data:
            return jsonify({"error": "Missing 'message' field in request"}), 400

        user_message = data['message'].strip()

        if not user_message:
            return jsonify({"error": "Message cannot be empty"}), 400

        # Construct messages for the API
        messages = [
            {"role": "system", "content": WWF_SYSTEM_INSTRUCTION},
            {"role": "user", "content": user_message}
        ]

        # Call Groq API. Some installed versions of the groq SDK don't
        # support reasoning_effort yet, so retry without it if that's
        # what's failing — this keeps the endpoint working either way.
        try:
            completion = client.chat.completions.create(
                model=MODEL_NAME,
                messages=messages,
                temperature=1,
                max_completion_tokens=8192,
                top_p=1,
                reasoning_effort="medium",
                stream=False,
                stop=None
            )
        except TypeError:
            completion = client.chat.completions.create(
                model=MODEL_NAME,
                messages=messages,
                temperature=1,
                max_completion_tokens=8192,
                top_p=1,
                stream=False,
                stop=None
            )

        # Extract the response
        ai_response = completion.choices[0].message.content

        return jsonify({"response": ai_response}), 200

    except Exception as e:
        # Print full traceback to Vercel function logs for debugging,
        # while still returning a readable error to the frontend.
        import traceback
        traceback.print_exc()
        return jsonify({"error": f"Server error: {str(e)}"}), 500


@app.route('/api/health', methods=['GET'])
def health_check():
    """Simple health check endpoint."""
    return jsonify({
        "status": "healthy",
        "service": "WWF AI API",
        "groq_client_ready": client is not None,
        "groq_client_error": client_init_error
    }), 200


if __name__ == '__main__':
    print("=" * 50)
    print("WWF AI Backend Server")
    print("=" * 50)
    print("Starting server on http://localhost:5000")
    print("API Endpoint: POST http://localhost:5000/api/chat")
    print("Health Check: GET http://localhost:5000/api/health")
    print("=" * 50)
    
    # Run the Flask app
    app.run(host='0.0.0.0', port=5000, debug=True)