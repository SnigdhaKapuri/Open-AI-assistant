from groq import Groq
from json import load, dump, JSONDecodeError
import datetime
from dotenv import dotenv_values
import os

# Load environment variables
env_vars = dotenv_values(".env")

# Retrieve required environment variables
Username = env_vars.get("Username", "User")
Assistantname = env_vars.get("Assistantname", "Assistant")
GroqAPIKey = env_vars.get("GroqAPIKey")

# Ensure the API key is available
if not GroqAPIKey:
    raise ValueError("❌ ERROR: Groq API Key is missing. Check your .env file.")

# Initialize Groq client
client = Groq(api_key=GroqAPIKey)

# Set up chatbot system message
System = f"""Hello, I am {Username}. You are an accurate and advanced AI chatbot named {Assistantname} 
with real-time up-to-date information from the internet.

*** Do not tell time until I ask, do not talk too much, just answer the question.***
*** Reply in only English, even if the question is in Hindi.***
*** Do not provide notes in the output, just answer the question and never mention your training data. ***
"""

SystemChatBot = [{"role": "system", "content": System}]

# Ensure the data folder exists
if not os.path.exists("Data"):
    os.makedirs("Data")

# Load chat history from file
chatlog_path = r"Data\ChatLog.json"

def load_chat_history():
    try:
        with open(chatlog_path, "r", encoding="utf-8") as f:
            return load(f)
    except (FileNotFoundError, JSONDecodeError):
        return []

def save_chat_history(messages):
    with open(chatlog_path, "w", encoding="utf-8") as f:
        dump(messages, f, indent=4)

messages = load_chat_history()

# Function to get real-time date and time
def RealtimeInformation():
    now = datetime.datetime.now()
    return f"""Please use this real-time information if needed:
Day: {now.strftime("%A")}
Date: {now.strftime("%d")} {now.strftime("%B")} {now.strftime("%Y")}
Time: {now.strftime("%H")} hours : {now.strftime("%M")} minutes : {now.strftime("%S")} seconds.
"""

# Function to clean and format chatbot responses
def AnswerModifier(answer):
    return "\n".join([line for line in answer.split("\n") if line.strip()])

# Main chatbot function
def ChatBot(Query):
    """Processes the user's query and returns the chatbot's response."""
    global messages  # Ensure messages are updated globally

    try:
        # Add user input to the chat history
        messages.append({"role": "user", "content": Query})

        # Get AI response
        response = client.chat.completions.create(
            model="llama3-70b-8192",
            messages=SystemChatBot + [{"role": "system", "content": RealtimeInformation()}] + messages,
            max_tokens=1024,
            temperature=0.7,
            top_p=1,
            stream=False  # Stream handling improved
        )

        # Extract AI response
        Answer = response.choices[0].message.content if response.choices else "Sorry, I couldn't generate a response."

        # Clean up the response
        Answer = Answer.replace("</s>", "")
        messages.append({"role": "assistant", "content": Answer})

        # Save chat history
        save_chat_history(messages)

        return AnswerModifier(Answer)

    except Exception as e:
        print(f"⚠️ Error: {e}")
        return "An error occurred while processing your request. Please try again."

# Interactive chat loop
if __name__ == "__main__":
    while True:
        user_input = input("\n👤 You: ")
        if user_input.lower() in ["exit", "quit", "bye"]:
            print("👋 Goodbye!")
            break
        print(f"\n🤖 {Assistantname}: {ChatBot(user_input)}")
