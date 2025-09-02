from seleniumwire import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
import json
import time
import os
from dotenv import load_dotenv

# Set up Chrome options
chrome_options = Options()
chrome_options.add_argument("--incognito")
chrome_options.add_argument("--start-maximized")

# Set the path to your WebDriver executable
driver_path = "/usr/bin/chromedriver"

# Initialize the WebDriver
service = Service(driver_path)
driver = webdriver.Chrome(service=service, options=chrome_options)
try:
    driver.maximize_window()
except Exception:
    pass

# Load env and resolve start URL
load_dotenv()
start_url = os.getenv('START_URL', 'https://www-test.pageroonline.com/einvoice/start')

# Open the target website
driver.get(start_url)

# Inject JavaScript to capture user events
script = """
// Idempotent recorder injection
(function(){
  if (window.__recorderInstalled) {
    return;
  }
  window.__recorderInstalled = true;
  window.recordedEvents = window.recordedEvents || [];
  window.__enterCounter = window.__enterCounter || 0;

  function recordEvent(event) {
      try {
        var target = event.target || {};
        var isEnter = (event && (event.key === 'Enter' || event.which === 13 || event.keyCode === 13));
        var recordedEvent = {
            type: event.type,
            target: (target.tagName || '').toLowerCase() || null,
            id: target.id || null,
            class: target.className || null,
            fieldType: target.type || null,
            name: target.name || null,
            value: (target.value !== undefined ? target.value : null),
            timestamp: Date.now(),
            key: (event.key !== undefined ? event.key : (isEnter ? 'Enter' : null)),
            x: (event.clientX !== undefined ? event.clientX : null),
            y: (event.clientY !== undefined ? event.clientY : null)
        };
        if (recordedEvent.type === 'keydown' && (recordedEvent.key === 'Enter' || event.which === 13 || event.keyCode === 13)) {
          window.__enterCounter = (window.__enterCounter || 0) + 1;
        }
        window.recordedEvents.push(recordedEvent);
        // Emit a synthetic 'enter' action for robustness
        if (recordedEvent.type === 'keydown' && isEnter) {
          window.recordedEvents.push({
            type: 'enter',
            target: recordedEvent.target,
            id: recordedEvent.id,
            class: recordedEvent.class,
            fieldType: recordedEvent.fieldType,
            name: recordedEvent.name,
            timestamp: Date.now()
          });
        }
      } catch (e) {
        // swallow
      }
  }

  // Capture common events
  document.addEventListener('click', recordEvent, true);
  document.addEventListener('keydown', recordEvent, true);
  document.addEventListener('keypress', recordEvent, true);
  document.addEventListener('keyup', recordEvent, true);
  document.addEventListener('change', recordEvent, true);
  document.addEventListener('input', recordEvent, true);
  document.addEventListener('submit', function(e){ try { recordEvent(e); } catch(e2){} }, true);
  window.addEventListener('beforeunload', function(e){ try { recordEvent({ type: 'beforeunload', target: document.body }); } catch(e2){} });

  console.log('Event recording started (idempotent install)');
})();
"""

driver.execute_script(script)

# Poll and keep the latest snapshot of events until the window is closed by the user
events_all = []  # Accumulates across navigations/refreshes
last_len = 0     # Tracks count for the current page lifecycle
last_url = None
try:
    print("Recording... Interact with the page. Close the browser window when done.")
    while True:
        time.sleep(0.2)
        # Detect URL change/refresh and persist immediately
        try:
            current_url = driver.current_url
        except Exception:
            current_url = None
        if last_url is None:
            last_url = current_url
        elif current_url is not None and current_url != last_url:
            # URL changed: persist accumulated events and reset page-local counter
            try:
                with open("recorded_events.json", "w") as f:
                    json.dump(events_all, f, indent=4)
                print(f"Persisted {len(events_all)} events on URL change: {last_url} -> {current_url}")
            except Exception:
                pass
            last_url = current_url
            last_len = 0
            # Re-inject recorder after navigation
            try:
                driver.execute_script(script)
            except Exception:
                pass

        # Try to get the latest events snapshot and enter counter
        result = driver.execute_script("return { events: (window.recordedEvents||[]), enterCounter: (window.__enterCounter||0) };")
        events = result.get('events', []) if isinstance(result, dict) else []
        enter_counter = result.get('enterCounter', 0) if isinstance(result, dict) else 0
        # If the page reloaded, the in-page buffer resets; detect shrink and reset
        if isinstance(events, list) and len(events) < last_len:
            last_len = 0
            # Likely a refresh; re-inject the recorder to ensure listeners reattach
            try:
                driver.execute_script(script)
            except Exception:
                pass
        # Stream any new events to the console in real-time
        if isinstance(events, list) and len(events) > last_len:
            new_events = events[last_len:]
            for ev in new_events:
                try:
                    print(f"EVENT {json.dumps(ev, ensure_ascii=False)}")
                except Exception:
                    print("EVENT <unserializable>")
            # Add to cumulative buffer and advance page-local counter
            events_all.extend(new_events)
            last_len = len(events)

        # Persist to disk continuously to avoid loss on refresh/crash
        try:
            with open("recorded_events.json", "w") as f:
                json.dump(events_all, f, indent=4)
        except Exception:
            pass
        # Additionally, if all windows are gone, we'll break on the next call/exception
        if len(driver.window_handles) == 0:
            break
except Exception:
    # Likely the window was closed; proceed to save whatever we have
    pass
finally:
    # Save events to a file
    try:
        with open("recorded_events.json", "w") as f:
            json.dump(events_all, f, indent=4)
        print(f"Recorded events saved to recorded_events.json ({len(events_all)} total)")
    finally:
        # Close the browser if still open
        try:
            driver.quit()
        except Exception:
            pass
