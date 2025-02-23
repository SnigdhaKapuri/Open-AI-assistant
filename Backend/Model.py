import cohere
from rich import print
from dotenv import dotenv_values

# Load environment variables
env_vars = dotenv_values(".env")
CohereAPIKey = env_vars.get("CohereAPIKey")

# Validate API Key
if not CohereAPIKey:
    print("[red]Error: Cohere API Key not found in .env file.[/red]")
    exit(1)

# Initialize Cohere client
co = cohere.Client(api_key=CohereAPIKey)

# List of recognized functions
funcs = [
    "exit", "general", "realtime", "open", "close", "play",
    "generate image", "system", "content", "google search",
    "youtube search", "reminder"
]

messages = []

# Preamble for the AI model
preamble = """
You are a very accurate Decision-Making Model, which decides what kind of query is given to you...
(Your full preamble text here)
"""

# Initial chat history
ChatHistory = [
    {"role": "User", "message": "how are you"},
    {"role": "Chatbot", "message": "general how are you"},
    {"role": "User", "message": "do you like pizza?"},
    {"role": "Chatbot", "message": "general do you like pizza?"},
    {"role": "User", "message": "open chrome and tell me about mahatma gandhi."},
    {"role": "Chatbot", "message": "open chrome, general tell me about mahatma gandhi."},
    {"role": "User", "message": "open chrome and firefox"},
    {"role": "Chatbot", "message": "open chrome, open firefox"},
    {"role": "User", "message": "what is today's date and remind me I have a dancing performance on 5th Aug 11pm"},
    {"role": "Chatbot", "message": "general what is today's date, reminder 11:00 pm 5th aug dancing performance"},
    {"role": "User", "message": "chat with me."},
    {"role": "Chatbot", "message": "general chat with me."}
]

def FirstLayerDMM(prompt: str) -> list:
    """Processes a query to classify it into predefined categories."""
    messages.append({"role": "user", "content": prompt})

    try:
        # Stream response from Cohere API
        response_text = ""
        stream = co.chat_stream(
            model='command-r-plus',
            message=prompt,
            temperature=0.7,
            chat_history=ChatHistory,
            prompt_truncation='OFF',
            connectors=[],
            preamble=preamble
        )

        for event in stream:
            if event.event_type == "text-generation":
                response_text += event.text

        # Normalize and clean the response
        response_text = response_text.replace("\n", "").split(",")
        response_text = [task.strip() for task in response_text]

        # Extract valid function-based responses
        valid_responses = [task for task in response_text if any(task.startswith(func) for func in funcs)]

        # Fallback if the response is empty or invalid
        if not valid_responses:
            return ["general " + prompt]

        return valid_responses

    except Exception as e:
        print(f"[red]Error:[/red] {e}")
        return ["general " + prompt]

if __name__ == "__main__":
    while True:
        try:
            user_input = input(">>> ").strip()
            if user_input.lower() in ["exit", "quit"]:
                print("[cyan]Goodbye![/cyan]")
                break
            print(FirstLayerDMM(user_input))
        except KeyboardInterrupt:
            print("\n[cyan]Goodbye![/cyan]")
            break
