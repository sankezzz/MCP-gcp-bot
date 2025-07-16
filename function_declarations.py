# /cab_booking_assistant/function_declarations.py

from vertexai.preview.generative_models import FunctionDeclaration, Tool

# --- Function Declaration for getDriversNearMe ---
# RE-INTRODUCED: This function now finds drivers for a specific route.
get_drivers_near_me_func = FunctionDeclaration(
    name="getDriversNearMe",
    description="Gets a list of available cab drivers for a specific route.",
    parameters={
        "type": "object",
        "properties": {
            "pickup_location": {
                "type": "string",
                "description": "The user's starting location or city, e.g., 'Delhi'.",
            },
            "dropoff_location": {
                "type": "string",
                "description": "The user's destination location or city, e.g., 'Lucknow'.",
            },
        },
        "required": ["pickup_location", "dropoff_location"],
    },
)

# --- Function Declaration for filterDrivers ---
# This remains the same.
filter_drivers_func = FunctionDeclaration(
    name="filterDrivers",
    description="Filters the current list of drivers based on user-specified criteria like language, age, etc.",
    parameters={
        "type": "object",
        "properties": {
            "language": {
                "type": "string",
                "description": "The language the user wants the driver to speak, e.g., 'punjabi', 'hindi'.",
            },
            "experience": {
                "type": "number",
                "description": "The minimum years of experience the user prefers for the driver.",
            },
            "age": {
                "type": "string",
                "description": "A specific age or type, e.g., '25', 'young', 'old'.",
            },
        },
    },
)

# --- Tool object containing all function declarations ---
# UPDATED: Both functions are now included.
booking_tools = Tool(
    function_declarations=[
        get_drivers_near_me_func,
        filter_drivers_func,
    ],
)