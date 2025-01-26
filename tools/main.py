from selenium_profiles.webdriver import Chrome
from selenium_profiles.profiles import profiles
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
from selenium import webdriver
from quart import Quart, request, jsonify
import asyncio
from queue import Queue, Empty
import traceback
from quart_cors import cors
import time
import base64
import json
import os

app = Quart(__name__)

cors(app, allow_origin="*")
# Global variables for Selenium setup
MAX_BROWSERS = 3  # Maximum number of browser windows
browser_pool = Queue(maxsize=MAX_BROWSERS)
RESPONSE_TIMEOUT = 10  # Timeout for waiting for the chatgpt's response
BROWSER_POOL_TIMEOUT = 60  # Timeout for waiting for an available browser
CONFIG_FILE = "config.json"


def load_or_create_config():
    # Check if the config file exists
    if os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, "r") as file:
            try:
                config = json.load(file)
                # Ensure required keys exist
                if "username" in config and "password" in config:
                    return config["username"], base64.b64decode(
                        config["password"]
                    ).decode("utf-8")
                else:
                    print("Config file is missing required fields.")
            except json.JSONDecodeError:
                print("Error decoding JSON. Creating a new config.")
            except (base64.binascii.Error, UnicodeDecodeError) as e:
                # Print any errors that occur during decoding
                print("Error decoding password. Creating a new config.")
    # If file doesn't exist or is invalid, create a new one
    username = input("Enter your username: ")
    password = input("Enter your password: ")
    config = {
        "username": username,
        "password": base64.b64encode(password.encode("utf-8")).decode("utf-8"),
    }

    # Save to file
    with open(CONFIG_FILE, "w") as file:
        json.dump(config, file, indent=4)
    print("Config saved successfully.")
    return username, password


# Load or create the config
STORED_EMAIL_ID, STORED_EMAIL_PASS = load_or_create_config()


def initialize_browser():
    """Initialize a new Selenium browser instance."""
    profile = profiles.Windows()
    options = webdriver.ChromeOptions()
    options.add_argument("--headless")
    browser = Chrome(profile, options=options, uc_driver=True)
    browser.get("https://chatgpt.com")
    return browser


def get_traceback(error):
    etype = type(error)
    trace = error.__traceback__
    lines = traceback.format_exception(etype, error, trace)
    traceback_text = "".join(lines)
    return traceback_text


def get_new_browser():
    browser = initialize_browser()
    browser.current_n = 3
    try:
        WebDriverWait(browser, 5).until(EC.url_contains("https://auth.openai.com"))
    except TimeoutException:
        return browser

    try:
        # Click on "Continue with Google"
        google_button = WebDriverWait(browser, 10).until(
            EC.element_to_be_clickable(
                (By.XPATH, "//button[.//span[text()='Continue with Google']]")
            )
        )
        google_button.click()

        # Switch to Google login page
        # Wait for the email input field and fill it
        email_input = WebDriverWait(browser, 10).until(
            EC.presence_of_element_located((By.ID, "identifierId"))
        )
        WebDriverWait(browser, 10).until(
            EC.element_to_be_clickable((By.ID, "identifierId"))
        )
        email_input.send_keys(STORED_EMAIL_ID)

        # Click "Next" after entering email
        next_button = WebDriverWait(browser, 10).until(
            EC.element_to_be_clickable(
                (By.XPATH, "//span[text()='Next']/ancestor::button")
            )
        )
        next_button.click()

        # Wait for the password input field and fill it
        password_input = WebDriverWait(browser, 10).until(
            EC.presence_of_element_located((By.NAME, "Passwd"))
        )
        WebDriverWait(browser, 10).until(
            EC.element_to_be_clickable((By.NAME, "Passwd"))
        )
        password_input.send_keys(STORED_EMAIL_PASS)

        # Click "Next" after entering the password
        next_button = WebDriverWait(browser, 10).until(
            EC.element_to_be_clickable(
                (By.XPATH, "//span[text()='Next']/ancestor::button")
            )
        )
        next_button.click()

        # Wait for the page to redirect back to ChatGPT
        WebDriverWait(browser, 10).until(EC.url_contains("https://chatgpt.com"))
    except TimeoutException:
        browser.quit()
        return None
    return browser


for _ in range(MAX_BROWSERS):
    browser = get_new_browser()
    if browser:
        browser_pool.put(browser)


async def get_prompt_response(browser, prompt):
    """Send the prompt to the browser and fetch the response."""
    global RESPONSE_TIMEOUT
    try:
        textarea = WebDriverWait(browser, RESPONSE_TIMEOUT).until(
            EC.presence_of_element_located((By.ID, "prompt-textarea"))
        )
        textarea.clear()
        textarea.send_keys(prompt)

        button = WebDriverWait(browser, 15).until(
            EC.presence_of_element_located(
                (By.CSS_SELECTOR, "button[data-testid='send-button']")
            )
        )
        button.click()

        response = WebDriverWait(browser, RESPONSE_TIMEOUT).until(
            EC.presence_of_element_located(
                (
                    By.CSS_SELECTOR,
                    f"article[data-testid='conversation-turn-{browser.current_n}']",
                )
            )
        )
        browser.current_n += 2
        while len(response.text.split("\n")) <= 1:
            await asyncio.sleep(1)
        while browser.find_elements(By.CSS_SELECTOR, "div.result-streaming"):
            await asyncio.sleep(0.25)

        response_text = response.text
        if "You’re giving feedback on a new version of chatgpt." in response_text:
            response_text = response_text.replace(
                "You’re giving feedback on a new version of chatgpt.", ""
            )
            response_text = response_text.replace(
                "Which response do you prefer? Responses may take a moment to load.", ""
            )
            response_text = response_text.replace("Response 1", "")
            response_text = response_text.replace("Response 2", "")
            response_text = response_text.replace("Response 3", "")
            response_text = response_text.replace("I prefer this response", "")
        response_text = response_text.split("\n")
        del response_text[0]
        response_text = "{0}".format(".".join(response_text))
        # log the response and the prompt
        with open("log.txt", "a", encoding="utf-8") as f:
            f.write(f"Prompt: {prompt}\n")
            f.write(f"Response: {response_text}\n\n")
        return response_text
    except TimeoutException:
        return None


@app.route("/get-answer", methods=["POST"])
async def get_answer():
    """Handle the 'get-answer' request by assigning a browser from the pool."""
    data = await request.json
    if not data or "question" not in data:
        return jsonify({"error": 'Invalid request, "question" is required'}), 400

    question = data["question"]
    print(f"Received question: {question}")
    # Attempt to get a browser from the pool with a timeout
    try:
        browser = browser_pool.get(
            timeout=BROWSER_POOL_TIMEOUT
        )  # Wait for up to BROWSER_POOL_TIMEOUT seconds
    except Empty:
        return (
            jsonify({"error": "No available browsers, try again later"}),
            503,
        )  # Service unavailable if no browser is available

    try:
        # Get the response using Selenium
        response = await get_prompt_response(browser, question)
        if response:
            browser_pool.put(browser)
        else:
            browser = get_new_browser()
            response = await get_prompt_response(browser, question)
            if response:
                browser_pool.put(browser)
            else:
                raise TimeoutException("Response not found")

        return jsonify({"answer": response})

    except Exception as e:
        with open(f"error_{int(time.time())}.txt", "w", encoding="utf-8") as f:
            f.write(get_traceback(e))
            f.write("\n\n")
            f.write(browser.page_source)

        browser.quit()
        return jsonify({"error": str(e)}), 500


def run_server():
    """Run the Quart server."""
    app.run(host="0.0.0.0", port=5000, debug=True)


if __name__ == "__main__":
    run_server()
