import requests
import time
import json
import sys

# --- Configuration ---
# NOTE: Replace "YOUR_API_KEY_HERE" with your actual Gemini API key.
# For security, you might want to load this from an environment variable.
API_KEY = "AIzaSyDB4wVI1WR6M4sP97rpsc78Zq4hLd1cyMc"
MODEL_NAME = "gemini-2.5-flash-preview-09-2025"
API_URL = f"https://generativelanguage.googleapis.com/v1beta/models/{MODEL_NAME}:generateContent?key={API_KEY}"

# --- Farm Knowledge Base and Persona (System Instruction) ---
# This instruction is critical. It defines the agent's persona, its rules,
# and its complete, proprietary knowledge about Willy's Wing Farm (WWF).
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
    -   The farm sells: Eggs, Meat, Live Birds, Chicks, Poultry Manure, Organic Fertiliser Bags, Feed Supply, Poultry Equipment (drinkers, feeders, brooders), Portable Structures, and Poultry Medicines.
    -   Special Services: Farm tours, Educational programs, Local delivery, Online courses, and Poultry events.

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

5.  **General Knowledge Constraint:**
    -   When asked about general bird characteristics, care, or non-farm-specific facts (like general meat weights), you MUST ONLY provide basic, high-level information. Detailed, in-depth knowledge on bird care and characteristics is reserved for the premium members of the website. Use the Google Search tool for these general facts.
"""

def ask_wwf_ai(user_query, max_retries=5):
    """
    Sends a customer query to the Gemini API and handles the response.

    Args:
        user_query (str): The question from the customer.
        max_retries (int): Maximum number of retries for API call failure.

    Returns:
        tuple: (generated_text, sources_list)
    """
    if not API_KEY or API_KEY == "YOUR_API_KEY_HERE":
        return "Error: Please set your Gemini API key in the script.", []

    # 1. Construct the API Payload
    payload = {
        "contents": [
            {"parts": [{"text": user_query}]}
        ],
        "systemInstruction": {
            "parts": [{"text": WWF_SYSTEM_INSTRUCTION}]
        },
        # 2. Enable Google Search Grounding
        "tools": [
            {"google_search": {}}
        ]
    }

    # 3. Implement Exponential Backoff
    for attempt in range(max_retries):
        try:
            response = requests.post(
                API_URL,
                headers={'Content-Type': 'application/json'},
                data=json.dumps(payload),
                timeout=30  # Set a timeout for the request
            )
            response.raise_for_status() # Raise HTTPError for bad responses (4xx or 5xx)
            result = response.json()
            
            # Successful response, proceed to parsing
            break

        except requests.exceptions.HTTPError as e:
            if response.status_code == 429 and attempt < max_retries - 1:
                # Handle 429 Too Many Requests with exponential backoff
                sleep_time = 2 ** attempt
                print(f"Rate limit hit. Retrying in {sleep_time} seconds...")
                time.sleep(sleep_time)
            else:
                # Handle other HTTP errors or final 429 failure
                return f"API HTTP Error: {e}", []
        except requests.exceptions.RequestException as e:
            # Handle network errors (e.g., DNS failure, connection reset)
            return f"Network Error: {e}", []
    else:
        return "API request failed after multiple retries due to rate limiting or timeout.", []


    # 4. Parse the Response and Extract Sources
    generated_text = "Sorry, I couldn't process that request."
    sources = []

    candidate = result.get('candidates', [{}])[0]
    
    # Extract the generated text
    if candidate.get('content') and candidate['content'].get('parts'):
        generated_text = candidate['content']['parts'][0].get('text', generated_text)

    # Extract grounding sources if they exist
    grounding_metadata = candidate.get('groundingMetadata')
    if grounding_metadata and grounding_metadata.get('groundingAttributions'):
        for attribution in grounding_metadata['groundingAttributions']:
            web_info = attribution.get('web')
            if web_info and web_info.get('uri') and web_info.get('title'):
                sources.append({
                    'uri': web_info['uri'],
                    'title': web_info['title']
                })
    
    return generated_text, sources

# --- Interactive Chat Agent Usage ---
if __name__ == "__main__":
    print("==============================================")
    print("Welcome to the Willy's Wing Farm (WWF) AI Chat")
    print("==============================================")
    print("Ask me anything about the farm, products, or policies.")
    print("Type 'exit' or 'quit' to end the session.\n")

    while True:
        try:
            user_input = input("Customer Query: ")
            
            if user_input.lower() in ['exit', 'quit']:
                print("\nThank you for chatting with WWF AI. Goodbye!")
                break
            
            if not user_input.strip():
                continue

            print("WWF AI is thinking...")
            response_text, sources = ask_wwf_ai(user_input)
            
            print("\nWWF AI Response:", response_text)

            if sources:
                print("\n--- Sources Used (For General Facts) ---")
                for i, source in enumerate(sources):
                    # Only show source title and URI if available
                    title = source.get('title', 'No Title Available')
                    uri = source.get('uri', 'No URI Available')
                    print(f"[{i+1}] {title}: {uri}")
            
            print("="*50 + "\n")

        except KeyboardInterrupt:
            print("\n\nThank you for chatting with WWF AI. Goodbye!")
            sys.exit(0)
        except EOFError:
            print("\n\nThank you for chatting with WWF AI. Goodbye!")
            sys.exit(0)