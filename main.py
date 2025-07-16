# /cab_booking_assistant/main.py

import requests
import vertexai
from vertexai.preview.generative_models import GenerativeModel, Part, Content, Candidate

# --- Import configurations from other files ---
from bot_prompt import base_prompt, current_user
from function_declarations import booking_tools

# --- Project Configuration ---
PROJECT_ID = "cabswale-test"
LOCATION = "us-central1"
# MODIFIED: Corrected the model name to a valid, specific version.
MODEL_NAME = "gemini-2.5-flash"

# --- Global cache for driver data ---
session_drivers: list = []

# --- Tool Implementations ---

def getDriversNearMe(pickup_location: str, dropoff_location: str) -> dict:
    """
    Fetches the list of drivers from the endpoint for a specific route.
    """
    global session_drivers
    
    api_url = "https://getdriverdatatest-7cijur72sa-uc.a.run.app"
    print(f"\n[System] Fetching drivers for route: {pickup_location} to {dropoff_location}...")
    
    # Using .capitalize() as this was the last working fix for your API's case-sensitivity.
    payload = {
        "from": pickup_location.lower(),
        "to": dropoff_location.lower()
    }
    
    try:
        print(f"[Debug] Sending Payload: {payload}")
        response = requests.post(api_url, json=payload, headers={"Content-Type": "application/json"})
        response.raise_for_status()
        
        print(f"[Debug] Received Raw Response: {response.text}")
        response_data = response.json()
        
        # MODIFIED: Restored the correct logic to handle the dictionary of drivers response.
        drivers_list = []
        if isinstance(response_data, dict):
            # Loop through the dictionary's items (driver_id, driver_data)
            for driver_id, driver_info in response_data.items():
                driver_info['id'] = driver_id  # Add the driver's ID into its own object
                drivers_list.append(driver_info)
            session_drivers = drivers_list
            print(f"[System] Successfully extracted and cached {len(session_drivers)} drivers.")
        else:
            print(f"[System] API Error: Received an unexpected data format (not a dictionary).")
            session_drivers = []

    except requests.exceptions.RequestException as e:
        print(f"[System] API Error fetching driver data: {e}")
        session_drivers = []
    
    return {"drivers": session_drivers}

def _age_matches(driver_age: int | None, age_filter: str) -> bool:
    """Helper function to check if a driver's age matches the filter criteria."""
    if driver_age is None:
        return False
    if age_filter == "young" and driver_age <= 30:
        return True
    if age_filter == "old" and driver_age > 30:
        return True
    if age_filter.isdigit() and driver_age == int(age_filter):
        return True
    return False

def filterDrivers(**filters: dict) -> dict:
    """Filters the currently cached list of drivers based on the provided criteria."""
    global session_drivers
    print(f"\n[System] Filtering drivers with criteria: {filters}")

    if not session_drivers:
        print("[System] No drivers in session to filter. Please find drivers for a route first.")
        return {"drivers": []}

    filtered_results = session_drivers
    
    if "language" in filters:
        lang_filter = filters["language"].lower()
        filtered_results = [
            d for d in filtered_results if lang_filter in [lang.lower() for lang in d.get("languageSelected", [])]
        ]

    if "experience" in filters:
        exp_filter = filters["experience"]
        filtered_results = [
            d for d in filtered_results if d.get("experience", 0) >= exp_filter
        ]
    
    if "age" in filters:
        age_filter = str(filters["age"]).lower()
        filtered_results = [d for d in filtered_results if _age_matches(d.get("age"), age_filter)]

    print(f"[System] Found {len(filtered_results)} drivers matching criteria.")
    return {"drivers": filtered_results}

# --- Main Conversation Loop ---

def run_conversation() -> None:
    """Initializes and runs the main interactive conversation loop."""
    
    vertexai.init(project=PROJECT_ID, location=LOCATION)
    model = GenerativeModel(MODEL_NAME)
    
    history = [
        Content.from_dict({"role": "user", "parts": [{"text": base_prompt}]}),
        Content.from_dict({"role": "model", "parts": [{"text": f"Hello {current_user['name']}! Where would you like to book a cab from and to today?"}]})
    ]
    
    chat = model.start_chat(history=history)

    print(f"--- Starting Conversation with {current_user['name']} ---")
    print(f"Bot: Hello {current_user['name']}! Where would you like to book a cab from and to today? (Type 'exit' to end)")

    while True:
        user_input = input("You: ")
        if user_input.lower() == 'exit':
            print("Bot: Goodbye!")
            break

        try:
            response = chat.send_message(user_input, tools=[booking_tools])
            candidate = response.candidates[0]
            part = candidate.content.parts[0]
            final_response = ""

            if part.function_call:
                function_call = part.function_call
                print(f"[System] Model wants to call function: {function_call.name}")
                
                api_response = None
                
                if function_call.name == "getDriversNearMe":
                    args = {key: val for key, val in function_call.args.items()}
                    api_response = getDriversNearMe(**args)
                elif function_call.name == "filterDrivers":
                    args = {key: val for key, val in function_call.args.items()}
                    api_response = filterDrivers(**args)
                
                if api_response is not None:
                    response = chat.send_message(
                        Part.from_function_response(
                            name=function_call.name,
                            response=api_response,
                        ),
                    )
                    final_response = response.candidates[0].content.parts[0].text
                else:
                    final_response = "Sorry, I couldn't get a response from that tool."

            elif part.text:
                final_response = part.text
            else:
                final_response = "Sorry, I received an unexpected response. Please try again."

            print(f"Bot: {final_response}")

        except Exception as e:
            print(f"An error occurred: {e}")

if __name__ == "__main__":
    run_conversation()