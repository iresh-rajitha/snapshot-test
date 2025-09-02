import json
from seleniumwire import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time
import os
from dotenv import load_dotenv

# Load recorded events if available
try:
    with open("recorded_events.json", "r") as f:
        recorded_events = json.load(f)
except FileNotFoundError:
    recorded_events = []

# Set up WebDriver
chrome_options = Options()
chrome_options.add_argument("--incognito")
chrome_options.add_argument("--start-maximized")

driver_path = "/usr/bin/chromedriver"
service = Service(driver_path)
driver = webdriver.Chrome(service=service, options=chrome_options)
try:
    driver.maximize_window()
except Exception:
    pass

# Load .env and resolve start URL (align with recorder)
load_dotenv()
start_url = os.getenv('START_URL', 'https://www-test.pageroonline.com/einvoice/start')
driver.get(start_url)

wait = WebDriverWait(driver, 10)

time.sleep(2)  # Let the page load

# Helper to find best element target

def find_target(event):
    # Prefer id
    if event.get("id"):
        try:
            return driver.find_element(By.ID, event["id"])
        except Exception:
            pass
    # Then class name (first class token)
    if event.get("class"):
        class_tokens = str(event["class"]).split()
        for token in class_tokens:
            try:
                return driver.find_element(By.CLASS_NAME, token)
            except Exception:
                continue
    # Then by name if available
    if event.get("name"):
        try:
            return driver.find_element(By.NAME, event["name"])
        except Exception:
            pass
    # Fallback to tag name
    if event.get("target"):
        try:
            candidates = driver.find_elements(By.TAG_NAME, event["target"])
            # If fieldType is provided, narrow down
            field_type = event.get("fieldType")
            if field_type and candidates:
                for el in candidates:
                    try:
                        if (el.get_attribute("type") or "").lower() == field_type.lower():
                            return el
                    except Exception:
                        continue
            return candidates[0] if candidates else None
        except Exception:
            pass
    return None

# Replay recorded events (if any)
if recorded_events:
    for event in recorded_events:
        try:
            # Wait for page to be interactive
            try:
                wait.until(lambda d: d.execute_script('return document.readyState') == 'complete')
            except Exception:
                pass

            element = find_target(event)
            if element is None:
                raise Exception("Target element not found for event")

            if event["type"] == "click":
                element.click()
            elif event["type"] == "input":
                element.clear()
                value = event.get("value") or ""
                element.send_keys(value)
            elif event["type"] == "keydown" and event.get("key"):
                key = event["key"]
                # Skip modifier-only keys like Shift
                if key in ["Shift", "ShiftLeft", "ShiftRight"]:
                    continue
                # Normalize Enter/Return
                if key.lower() in ["enter", "return"]:
                    from selenium.webdriver.common.keys import Keys
                    element.send_keys(Keys.ENTER)
                else:
                    element.send_keys(key)
            elif event["type"] == "enter":
                from selenium.webdriver.common.keys import Keys
                element.send_keys(Keys.ENTER)
            time.sleep(0.3)
        except Exception as e:
            print(f"Error replaying event {event}: {e}")
else:
    print("No recorded events. Loaded page and will close.")

print("Playback completed!")

# Close the browser
driver.quit()
