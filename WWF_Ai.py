from groq import Groq
import time
import sys

# --- Configuration ---
# NOTE: Set your Groq API key as an environment variable: GROQ_API_KEY
# Or replace "YOUR_GROQ_API_KEY_HERE" with your actual API key.
client = Groq()

MODEL_NAME = "openai/gpt-oss-20b"

# --- Farm Knowledge Base and Persona (System Instruction) ---
# This instruction defines the agent's persona, its rules,
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
    -   When asked about general bird characteristics, care, or non-farm-specific facts (like general meat weights), you MUST ONLY provide basic, high-level information. Detailed, in-depth knowledge on bird care and characteristics is reserved for the premium members of the website.
"""

def ask_wwf_ai(user_query, max_retries=5):
    """
    Sends a customer query to the Groq API and handles the response.

    Args:
        user_query (str): The question from the customer.
        max_retries (int): Maximum number of retries for API call failure.

    Returns:
        str: The generated response text from the AI.
    """
    
    # 1. Construct the messages for the API
    messages = [
        {"role": "system", "content": WWF_SYSTEM_INSTRUCTION},
        {"role": "user", "content": user_query}
    ]

    # 2. Implement Exponential Backoff
    for attempt in range(max_retries):
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
            
            # Extract the response text
            generated_text = completion.choices[0].message.content
            return generated_text

        except Exception as e:
            if attempt < max_retries - 1:
                # Handle rate limiting or temporary errors with exponential backoff
                sleep_time = 2 ** attempt
                print(f"Error occurred: {e}. Retrying in {sleep_time} seconds...")
                time.sleep(sleep_time)
            else:
                # Handle final failure
                return f"API Error: {e}"
    
    return "API request failed after multiple retries."


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
            response_text = ask_wwf_ai(user_input)
            
            print("\nWWF AI Response:", response_text)
            print("="*50 + "\n")

        except KeyboardInterrupt:
            print("\n\nThank you for chatting with WWF AI. Goodbye!")
            sys.exit(0)
        except EOFError:
            print("\n\nThank you for chatting with WWF AI. Goodbye!")
            sys.exit(0)