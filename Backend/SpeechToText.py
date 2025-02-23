from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
from dotenv import dotenv_values
import os
import time
import mtranslate as mt

# Load environment variables
env_vars = dotenv_values(".env")
InputLanguage = env_vars.get("InputLanguage", "en")  # Default to English if not set

# HTML Code for Speech Recognition
HtmlCode = f'''<!DOCTYPE html>
<html lang="en">
<head>
    <title>Speech Recognition</title>
</head>
<body>
    <button id="start" onclick="startRecognition()">Start Recognition</button>
    <button id="end" onclick="stopRecognition()">Stop Recognition</button>
    <p id="output"></p>
    <script>
        const output = document.getElementById('output');
        let recognition;

        function startRecognition() {{
            recognition = new (window.SpeechRecognition || window.webkitSpeechRecognition)();
            recognition.lang = "{InputLanguage}";
            recognition.continuous = true;

            recognition.onresult = function(event) {{
                const transcript = event.results[event.results.length - 1][0].transcript;
                output.textContent += transcript;
            }};

            recognition.onend = function() {{
                recognition.start();
            }};
            recognition.start();
        }}

        function stopRecognition() {{
            if (recognition) {{
                recognition.stop();
                output.innerHTML = "";
            }}
        }}
    </script>
</body>
</html>'''

# Save the HTML file
data_dir = os.path.join(os.getcwd(), "Data")
os.makedirs(data_dir, exist_ok=True)
html_file_path = os.path.join(data_dir, "Voice.html")

with open(html_file_path, "w", encoding="utf-8") as f:
    f.write(HtmlCode)

# Get file path for ChromeDriver
file_url = f"file:///{html_file_path}"

# Configure ChromeDriver options
chrome_options = Options()
chrome_options.add_argument("--headless=new")  # Run in headless mode
chrome_options.add_argument("--use-fake-ui-for-media-stream")
chrome_options.add_argument("--use-fake-device-for-media-stream")
chrome_options.add_argument("--disable-gpu")
chrome_options.add_argument("--no-sandbox")
chrome_options.add_argument("--disable-dev-shm-usage")
chrome_options.add_argument("--log-level=3")  # Suppress logs

# Initialize ChromeDriver
service = Service(ChromeDriverManager().install())

# Function to modify queries for better responses
def QueryModifier(Query):
    query = Query.strip().lower()
    query_words = query.split()
    question_words = ["how", "what", "who", "where", "when", "why", "which", "whose", "whom", "what's", "where's", "how's"]

    if any(word in query_words for word in question_words):
        query = query.rstrip(".!?") + "?"
    else:
        query = query.rstrip(".!?") + "."

    return query.capitalize()

# Function to translate speech to English if needed
def UniversalTranslator(Text):
    return mt.translate(Text, "en", "auto").capitalize()

# Function to perform speech recognition using Selenium
def SpeechRecognition():
    driver = None
    try:
        driver = webdriver.Chrome(service=service, options=chrome_options)
        driver.get(file_url)

        driver.find_element(By.ID, "start").click()
        time.sleep(2)  # Allow speech recognition to start

        while True:
            try:
                text_element = driver.find_element(By.ID, "output")
                recognized_text = text_element.text.strip()

                if recognized_text:
                    driver.find_element(By.ID, "end").click()
                    driver.quit()  # Close the browser

                    if InputLanguage.lower().startswith("en"):
                        return QueryModifier(recognized_text)
                    else:
                        return QueryModifier(UniversalTranslator(recognized_text))

            except Exception:
                pass  # Continue checking output text

    except Exception as e:
        print(f"Error: {e}")

    finally:
        if driver:
            driver.quit()  # Ensure ChromeDriver is closed

# Run the speech recognition in a loop
if __name__ == "__main__":
    while True:
        text_output = SpeechRecognition()
        print(text_output)
