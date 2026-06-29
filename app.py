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
    return render_template('index.html')

# Initialize Groq client
# Make sure to set your GROQ_API_KEY environment variable
client = Groq()

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
        
        # Call Groq API
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
        
        # Extract the response
        ai_response = completion.choices[0].message.content
        
        return jsonify({"response": ai_response}), 200
        
    except Exception as e:
        return jsonify({"error": f"Server error: {str(e)}"}), 500


@app.route('/api/health', methods=['GET'])
def health_check():
    """Simple health check endpoint."""
    return jsonify({"status": "healthy", "service": "WWF AI API"}), 200


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