import time
import os
import sys
from dotenv import load_dotenv
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
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

    wait = WebDriverWait(driver, 30) 

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
        driver.save_screenshot("01_after_login.png")

        # Check for auto-open popup
        try:
            print("Checking for auto-open popup...")
            popup_btn = driver.find_element(By.XPATH, "//div[contains(@class, 'modal') or contains(@class, 'dialog') or contains(@class, 'popup')]//button[contains(., 'Mark attendance')]")
            if popup_btn.is_displayed():
                print("Popup found immediately!")
                time.sleep(2) # Wait for animation
                driver.execute_script("arguments[0].click();", popup_btn)
                print("Clicked auto-open popup.")
                time.sleep(5)
                driver.save_screenshot("final_success.png")
                return
        except:
            print("Popup not auto-open.")

        # Click Dashboard Button
        print("Locating Dashboard 'Mark attendance' button...")
        home_mark_btn = wait.until(EC.element_to_be_clickable((By.XPATH, "//button[contains(., 'Mark attendance')]")))
        
        print("Clicking Dashboard button...")
        driver.execute_script("arguments[0].click();", home_mark_btn)

        # --- MARK ATTENDANCE (POPUP) ---
        print("Waiting for Popup to appear...")
        # Wait specifically for the popup to be VISIBLE
        popup_element = wait.until(EC.visibility_of_element_located((By.XPATH, "//div[contains(@class, 'modal') or contains(@class, 'dialog') or contains(@class, 'popup')]//button[contains(., 'Mark attendance')]")))
        
        print("Popup visible. Pausing for animation...")
        time.sleep(3)
        driver.save_screenshot("02_before_popup_click.png")

        print("Clicking Popup 'Mark attendance'...")
        driver.execute_script("arguments[0].click();", popup_element)
        driver.save_screenshot("03_immediately_after_click.png")

        print("`SUCCESS`: Click Action Performed.")

        # --- VERIFICATION SCREENSHOT ---
        time.sleep(1) # Wait for Toast message/Success notification
        print("Taking verification screenshot...")
        driver.save_screenshot("final_result.png")

    except Exception as e:
        print(f"ERROR: {str(e)}")
        driver.save_screenshot("error_debug.png")
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