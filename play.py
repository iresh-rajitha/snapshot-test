import json
from seleniumwire import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
import time

# Load recorded events
with open("recorded_events.json", "r") as f:
    recorded_events = json.load(f)

# Set up WebDriver
chrome_options = Options()
chrome_options.add_argument("--incognito")

driver_path = "/usr/bin/chromedriver"
service = Service(driver_path)
driver = webdriver.Chrome(service=service, options=chrome_options)

# Open website
driver.get('https://www.google.com')

time.sleep(2)  # Let the page load

# Replay recorded events
for event in recorded_events:
    try:
        if event["type"] == "click":
            element = driver.find_element(By.TAG_NAME, event["target"])
            element.click()
        # elif event["type"] == "keydown":
        #     element = driver.find_element(By.TAG_NAME, event["target"])
        #     element.send_keys(event["key"])
        elif event["type"] == "input":
            element = driver.find_element(By.TAG_NAME, event["target"])
            element.clear()
            element.send_keys(event["value"])
        time.sleep(0.5)  # Simulate human-like delay
    except Exception as e:
        print(f"Error replaying event {event}: {e}")

print("Playback completed!")

# Close the browser
driver.quit()
