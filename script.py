import requests
from openai import OpenAI
import datetime
import time
from dotenv import load_dotenv, find_dotenv

# Load environment variables
load_dotenv(find_dotenv())

# Initialize the OpenAI client
client = OpenAI()

print("OpenAI client initialized.")


# Define the custom functions
def get_opening_hours():
    try:
        print("Fetching opening hours...")
        response = requests.get("http://localhost:8000/opening-hours")
        if response.status_code == 200:
            return response.json()  # Assuming the API returns JSON data
        else:
            return "Error: Unable to fetch opening hours."
    except requests.exceptions.RequestException as e:
        return f"Request failed: {e}"


def how_late():
    print("Getting current time...")
    return datetime.datetime.now().strftime("%H:%M:%S")  # Current time in HH:MM:SS


# Create the file for the assistant
file = client.files.create(file=open("knowledge.txt", "rb"), purpose="assistants")
print("File created for assistant.")

assistant = client.beta.assistants.create(
    name="Summariser",
    description="You are great at assisting customers of a bank.",
    model="gpt-4-turbo-preview",
    tools=[
        {"type": "code_interpreter"},
        {"type": "retrieval"},
        {
            "type": "function",
            "function": {
                "name": "get_opening_hours",
                "description": "Get the opening hours of the bank",
                "parameters": {"type": "object", "properties": {}, "required": []},
            },
        },
        {
            "type": "function",
            "function": {
                "name": "how_late",
                "description": "Get the current time",
                "parameters": {"type": "object", "properties": {}, "required": []},
            },
        },
    ],
    file_ids=[file.id],
)
print("Assistant created.")

thread = client.beta.threads.create()
print(f"New thread created: {thread.id}")

message = client.beta.threads.messages.create(
    thread_id=thread.id, role="user", content="Wie spät ist es?"
)
print(f"Message sent: {message.content}")

run = client.beta.threads.runs.create(
    thread_id=thread.id,
    assistant_id=assistant.id,
    instructions="Please address the user as Jane Doe. The user has a premium account.",
)
print(f"New run created: {run.id}")

while True:
    time.sleep(2)
    run = client.beta.threads.runs.retrieve(thread_id=thread.id, run_id=run.id)
    print(f"Checking run status: {run.status}")

    if run.status == "completed":
        print("Run completed successfully.")
        break
    elif run.status == "requires_action":
        print("Run requires action. Processing...")
        for tool_call in run.required_action.submit_tool_outputs.tool_calls:
            tool_call_id = tool_call.id
            function_name = tool_call.function.name
            print(f"Executing function: {function_name}")

            if function_name == "get_opening_hours":
                output = get_opening_hours()
            elif function_name == "how_late":
                output = how_late()
            else:
                output = "Function not recognized"
                print("Error: Function not recognized.")

            client.beta.threads.runs.submit_tool_outputs(
                thread_id=thread.id,
                run_id=run.id,
                tool_outputs=[
                    {"tool_call_id": tool_call_id, "output": output},
                ],
            )
            print(f"Output submitted for {function_name}: {output}")
    elif run.status == "failed":
        print("Run failed.")
        break
