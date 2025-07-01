from seleniumwire import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
import json

# Set up Chrome options
chrome_binary_path = "/usr/bin/chromium-browser"
chrome_options = Options()
chrome_options.binary_location = chrome_binary_path
chrome_options.add_argument("--incognito")

# Set the path to your WebDriver executable
driver_path = "/usr/bin/chromedriver"

# Initialize the WebDriver
service = Service(driver_path)
driver = webdriver.Chrome(service=service, options=chrome_options)

# Open the target website
driver.get('https://www.google.com')

# Inject JavaScript to capture user events
script = """
window.recordedEvents = [];

function recordEvent(event) {
    let recordedEvent = {
        type: event.type,
        target: event.target.tagName.toLowerCase(),
        id: event.target.id || null,
        class: event.target.className || null,
        value: event.target.value || null,
        timestamp: Date.now(),
        key: event.key || null,
        x: event.clientX || null,
        y: event.clientY || null
    };
    console.log(recordedEvent);
    window.recordedEvents.push(recordedEvent);
}

// Capture common events
document.addEventListener('click', recordEvent);
document.addEventListener('keydown', recordEvent);
document.addEventListener('input', recordEvent);

console.log("Event recording started...");
"""

driver.execute_script(script)

input("Press Enter to stop recording and save events...")

# Retrieve recorded events
events = driver.execute_script("return window.recordedEvents;")

# Save events to a file
with open("recorded_events.json", "w") as f:
    json.dump(events, f, indent=4)

print("Recorded events saved to recorded_events.json")

# Close the browser
driver.quit()
