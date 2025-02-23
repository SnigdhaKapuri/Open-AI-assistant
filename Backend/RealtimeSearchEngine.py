from googlesearch import search
from groq import Groq
from json import load, dump
import datetime
from dotenv import dotenv_values
import sys
import os

# Load environment variables
env_vars = dotenv_values(".env")

Username = env_vars.get("Username", "User")
Assistantname = env_vars.get("Assistantname", "Assistant")
GroqAPIKey = env_vars.get("GroqAPIKey")

# Initialize Groq client
client = Groq(api_key=GroqAPIKey)

# System message
System = f"""Hello, I am {Username}. You are an advanced AI chatbot named {Assistantname} with real-time access to information.
*** Provide answers professionally, ensuring proper grammar, punctuation, and clarity. ***
*** Just answer the question accurately and concisely. ***"""

# Load chat logs
chat_log_path = os.path.join("Data", "ChatLog.json")
if not os.path.exists("Data"):
    os.makedirs("Data")

try:
    with open(chat_log_path, "r") as f:
        messages = load(f)
except (FileNotFoundError, ValueError):
    messages = []

# Google Search Function
def GoogleSearch(query):
    try:
        results = list(search(query, advanced=True, num_results=5))
        answer = f"Search results for '{query}':\n[start]\n"

        for i in results:
            answer += f"Title: {i.title}\nDescription: {i.description}\n\n"

        answer += "[end]"
        print(answer)  # Debugging output
        return answer
    except Exception as e:
        return f"Error fetching search results: {str(e)}"

# Answer formatting function
def AnswerModifier(answer):
    return "\n".join(line.strip() for line in answer.split("\n") if line.strip())

# Function to get real-time information
def Information():
    now = datetime.datetime.now()
    return (
        f"Use This Real-time Information if needed:\n"
        f"Day: {now.strftime('%A')}\n"
        f"Date: {now.strftime('%d')}\n"
        f"Month: {now.strftime('%B')}\n"
        f"Year: {now.strftime('%Y')}\n"
        f"Time: {now.strftime('%H')} hours, {now.strftime('%M')} minutes, {now.strftime('%S')} seconds.\n"
    )

# Function to perform real-time search and return AI-generated response
def RealtimeSearchEngine(prompt):
    global messages

    # Load previous chat history
    try:
        with open(chat_log_path, "r") as f:
            messages = load(f)
    except (FileNotFoundError, ValueError):
        messages = []

    messages.append({"role": "user", "content": prompt})

    # Get search results and real-time info
    search_results = GoogleSearch(prompt)
    real_time_info = Information()

    system_chatbot = [
        {"role": "system", "content": System},
        {"role": "system", "content": search_results},
        {"role": "system", "content": real_time_info},
    ]

    # API call
    completion = client.chat.completions.create(
        model="llama3-70b-8192",
        messages=system_chatbot + messages,
        max_tokens=1024,
        temperature=0.7,
        top_p=1,
        stream=True,
    )

    # Process response
    answer = ""
    for chunk in completion:
        if hasattr(chunk.choices[0], "delta") and chunk.choices[0].delta.content:
            answer += chunk.choices[0].delta.content

    answer = answer.strip().replace("</s>", "")
    messages.append({"role": "assistant", "content": answer})

    # Save updated chat history
    with open(chat_log_path, "w") as f:
        dump(messages, f, indent=4)

    return AnswerModifier(answer)

# Main chatbot interaction loop
if __name__ == "__main__":
    try:
        while True:
            prompt = input("Enter your query: ")
            print(RealtimeSearchEngine(prompt))
    except KeyboardInterrupt:
        print("\nChatbot exited.")
        sys.exit(0)
