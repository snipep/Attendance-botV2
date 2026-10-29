import time
import os
import re
import sys
from datetime import datetime
from zoneinfo import ZoneInfo
from dotenv import load_dotenv
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
from webdriver_manager.chrome import ChromeDriverManager

load_dotenv()

# ==========================================
# CONFIGURATION
# ==========================================
HRONE_URL = "https://app.hrone.cloud/login#dynamischit"
EMAIL_ID = os.getenv("HRONE_USER")
PASSWORD = os.getenv("HRONE_PASS")

is_headless = os.getenv("HEADLESS_MODE", "True").lower() == "true"
# --- 📍 LOCATION CONFIGURATION ---
try:
    LATITUDE = float(os.getenv("LATITUDE")) 
    LONGITUDE = float(os.getenv("LONGITUDE"))
except (TypeError, ValueError):
    print("Error: Latitude/Longitude missing.")
    sys.exit(1)

ACCURACY = 100
TIMEZONE_ID = os.getenv("TIMEZONE_ID", "Asia/Kolkata")

POPUP_BTN_XPATH = "//div[contains(@class, 'modal') or contains(@class, 'dialog') or contains(@class, 'popup')]//button[contains(., 'Mark attendance')]"
# Dashboard widget shows e.g. "Last punch : 10:01 PM | 27-10-2026"
LAST_PUNCH_RE = re.compile(r"Last punch\s*:\s*(\d{1,2}:\d{2}\s*[AP]M)\s*\|\s*(\d{2}-\d{2}-\d{4})", re.I)
PUNCH_MAX_AGE_SECONDS = 5 * 60

def dismiss_tour(driver):
    # HROne's navigation redesign (Oct 2026) shows a "Start tour / Skip tour" dialog over the dashboard
    for btn in driver.find_elements(By.XPATH, "//button[normalize-space(.)='Skip tour']"):
        if btn.is_displayed():
            driver.execute_script("arguments[0].click();", btn)
            print("Dismissed 'Skip tour' dialog.")
            time.sleep(2)
            return

def read_last_punch(driver):
    match = LAST_PUNCH_RE.search(driver.find_element(By.TAG_NAME, "body").text)
    if not match:
        return None
    punch_time = datetime.strptime(f"{match.group(1)} {match.group(2)}", "%I:%M %p %d-%m-%Y")
    return punch_time.replace(tzinfo=ZoneInfo(TIMEZONE_ID))

def is_fresh_punch(punch, punch_before):
    if punch is None or punch == punch_before:
        return False
    age = abs((datetime.now(ZoneInfo(TIMEZONE_ID)) - punch).total_seconds())
    return age <= PUNCH_MAX_AGE_SECONDS

def wait_for_new_punch(driver, punch_before, timeout=30):
    def fresh_punch(d):
        punch = read_last_punch(d)
        return punch if is_fresh_punch(punch, punch_before) else False
    try:
        return WebDriverWait(driver, timeout).until(fresh_punch)
    except TimeoutException:
        return None

def run_attendance():
    print(f"Initializing Chrome (Headless: {is_headless})...")
    chrome_options = Options()
    
    # --- 1. GEO PERMISSIONS ---
    prefs = {
        "profile.default_content_setting_values.geolocation": 1, 
        "profile.managed_default_content_settings.geolocation": 1
    }
    chrome_options.add_experimental_option("prefs", prefs)

    # --- 2. LINUX SERVER OPTIMIZATIONS ---
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--window-size=1920,1080")
    
    # --- 3. ANTI-DETECTION (IMPORTANT) ---
    # Makes HROne think this is a real Windows PC, not a Linux Server
    chrome_options.add_argument("--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36")
    chrome_options.add_argument("--disable-blink-features=AutomationControlled")

    if is_headless:
        chrome_options.add_argument("--headless=new")

    # --- DIAGNOSTICS: capture browser console/network errors ---
    chrome_options.set_capability("goog:loggingPrefs", {"browser": "ALL", "performance": "ALL"})

    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=chrome_options)
    
    # --- 4. LOCATION SPOOFING ---
    params = {
        "latitude": LATITUDE,
        "longitude": LONGITUDE,
        "accuracy": ACCURACY
    }
    driver.execute_cdp_cmd("Emulation.setGeolocationOverride", params)
    print(f"Location spoofed to: {LATITUDE}, {LONGITUDE}")

    # --- 5. TIMEZONE SPOOFING (must match the spoofed location) ---
    driver.execute_cdp_cmd("Emulation.setTimezoneOverride", {"timezoneId": TIMEZONE_ID})
    print(f"Timezone spoofed to: {TIMEZONE_ID}")

    wait = WebDriverWait(driver, 45)

    try:
        print(f"Navigating to {HRONE_URL}...")
        driver.get(HRONE_URL)
        
        # --- LOGIN FLOW ---
        try:
            WebDriverWait(driver, 5).until(
                EC.presence_of_element_located((By.XPATH, "//button[contains(., 'Mark attendance')]"))
            )
            print("Already logged in.")
        except:
            print("Login required...")
            
            # Email
            email_input = wait.until(EC.element_to_be_clickable((By.XPATH, "//input[@type='text' or @type='email']")))
            email_input.clear()
            email_input.send_keys(EMAIL_ID)
            
            # Next
            wait.until(EC.element_to_be_clickable((By.XPATH, "//button[contains(translate(., 'NEXT', 'next'), 'next')]"))).click()
            
            # Password
            password_input = wait.until(EC.element_to_be_clickable((By.XPATH, "//input[@type='password']")))
            password_input.clear()
            password_input.send_keys(PASSWORD)
            time.sleep(1)
            password_input.send_keys(Keys.RETURN)
            
            print("Credentials submitted. Waiting for dashboard...")

        # --- DASHBOARD & POPUP HANDLING ---
        time.sleep(10)
        dismiss_tour(driver)

        punch_before = read_last_punch(driver)
        print(f"Last punch before: {punch_before}")

        # Check for auto-open popup
        auto_popup = [b for b in driver.find_elements(By.XPATH, POPUP_BTN_XPATH) if b.is_displayed()]
        if auto_popup:
            print("Popup found immediately!")
            time.sleep(2) # Wait for animation
            driver.execute_script("arguments[0].click();", auto_popup[0])
            print("Clicked auto-open popup.")
        else:
            print("Popup not auto-open.")

            # Click Dashboard Button
            print("Locating Dashboard 'Mark attendance' button...")
            try:
                home_mark_btn = wait.until(EC.element_to_be_clickable((By.XPATH, "//button[contains(., 'Mark attendance')]")))
            except TimeoutException:
                print("Button not found in time. Refreshing page and retrying...")
                driver.refresh()
                time.sleep(10)
                dismiss_tour(driver)
                home_mark_btn = wait.until(EC.element_to_be_clickable((By.XPATH, "//button[contains(., 'Mark attendance')]")))

            print("Clicking Dashboard button...")
            driver.execute_script("arguments[0].click();", home_mark_btn)

            # --- MARK ATTENDANCE (POPUP) ---
            # Older HROne UI opened a confirmation popup; the current one punches straight from the dashboard card
            try:
                popup_element = WebDriverWait(driver, 10).until(EC.visibility_of_element_located((By.XPATH, POPUP_BTN_XPATH)))
                print("Confirmation popup visible. Pausing for animation...")
                time.sleep(3)
                print("Clicking Popup 'Mark attendance'...")
                driver.execute_script("arguments[0].click();", popup_element)
            except TimeoutException:
                print("No confirmation popup (dashboard punches directly).")

        # --- VERIFY PUNCH ---
        print("Verifying 'Last punch' updated...")
        punch_after = wait_for_new_punch(driver, punch_before)
        if punch_after is None:
            print("'Last punch' not updated yet. Refreshing page and re-checking...")
            driver.refresh()
            time.sleep(10)
            punch_after = wait_for_new_punch(driver, punch_before)
        if punch_after is None:
            raise RuntimeError(f"Attendance not confirmed: 'Last punch' is {read_last_punch(driver)}, expected a punch within the last {PUNCH_MAX_AGE_SECONDS // 60} minutes")

        print(f"`SUCCESS`: Attendance marked. Last punch: {punch_after}")

    except Exception as e:
        print(f"ERROR: {str(e)}")
        try:
            screenshot_path = f"error_{time.strftime('%Y%m%d_%H%M%S')}.png"
            driver.save_screenshot(screenshot_path)
            print(f"Saved error screenshot to {screenshot_path}")
        except Exception as ss_err:
            print(f"Could not save error screenshot: {ss_err}")
        raise e

    finally:
        try:
            print("--- Browser console log ---")
            for entry in driver.get_log("browser"):
                print(entry)
        except Exception as log_err:
            print(f"Could not fetch browser console log: {log_err}")

        print("Closing browser...")
        driver.quit()

if __name__ == "__main__":
    run_attendance()