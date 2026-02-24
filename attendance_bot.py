import time
import os
import sys
from dotenv import load_dotenv # Import dotenv
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager

# 1. Load Environment Variables (from .env file if present)
load_dotenv()

# ==========================================
# CONFIGURATION
# ==========================================
HRONE_URL = "https://app.hrone.cloud/login#dynamischit"
EMAIL_ID = os.getenv("HRONE_USER")
PASSWORD = os.getenv("HRONE_PASS")

# Configuration for Headless Mode
# On GitHub Actions, usually we want this True. Locally, False to see what happens.
is_headless = os.getenv("HEADLESS_MODE", "True").lower() == "true"

# --- 📍 LOCATION CONFIGURATION ---
try:
    lat_str = os.getenv("LATITUDE")
    long_str = os.getenv("LONGITUDE")
    
    if not lat_str or not long_str:
        raise ValueError("Latitude/Longitude not found in .env or Secrets")
        
    LATITUDE = float(lat_str)
    LONGITUDE = float(long_str)
except ValueError as e:
    print(f"Configuration Error: {e}")
    sys.exit(1)

ACCURACY = 100

def run_attendance():
    print(f"Initializing Chrome (Headless: {is_headless})...")
    chrome_options = Options()
    
    # Enable Geolocation Permission
    prefs = {
        "profile.default_content_setting_values.geolocation": 1, 
        "profile.managed_default_content_settings.geolocation": 1
    }
    chrome_options.add_experimental_option("prefs", prefs)

    if is_headless:
        chrome_options.add_argument("--headless=new") # Updated headless flag
        chrome_options.add_argument("--no-sandbox") 
        chrome_options.add_argument("--disable-dev-shm-usage") 
        chrome_options.add_argument("--window-size=1920,1080")
        chrome_options.add_argument("--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
    else:
        chrome_options.add_argument("--start-maximized")

    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=chrome_options)
    
    # 2. OVERRIDE LOCATION (Spoofing)
    params = {
        "latitude": LATITUDE,
        "longitude": LONGITUDE,
        "accuracy": ACCURACY
    }
    driver.execute_cdp_cmd("Emulation.setGeolocationOverride", params)
    print(f"Location spoofed to: {LATITUDE}, {LONGITUDE}")

    wait = WebDriverWait(driver, 25)

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

        # --- HANDLING THE DASHBOARD ---
        time.sleep(8) # Generous wait for page load and location fetch

        # Case A: Check if Popup is ALREADY open
        try:
            print("Checking if popup is already open...")
            # We use a very short wait here just to check
            popup_btn = driver.find_element(By.XPATH, "//div[contains(@class, 'modal') or contains(@class, 'dialog') or contains(@class, 'popup')]//button[contains(., 'Mark attendance')]")
            if popup_btn.is_displayed():
                print("Popup is auto-open. Clicking...")
                driver.execute_script("arguments[0].click();", popup_btn)
                print("Clicked auto-open popup.")
                time.sleep(5)
                return
        except:
            print("Popup not auto-open.")

        # Case B: Click Dashboard Button
        print("Locating Dashboard 'Mark attendance' button...")
        home_mark_btn = wait.until(EC.presence_of_element_located((By.XPATH, "//button[contains(., 'Mark attendance')]")))
        
        print("Force-clicking Dashboard button...")
        driver.execute_script("arguments[0].click();", home_mark_btn)

        # --- MARK ATTENDANCE (POPUP) ---
        print("Waiting for Popup to appear...")
        time.sleep(2)
        
        popup_mark_btn = wait.until(EC.presence_of_element_located((By.XPATH, "//div[contains(@class, 'modal') or contains(@class, 'dialog') or contains(@class, 'popup')]//button[contains(., 'Mark attendance')]")))
        
        print("Force-clicking Popup 'Mark attendance'...")
        driver.execute_script("arguments[0].click();", popup_mark_btn)
        
        print("SUCCESS: Click Action Performed.")
        
        # --- VERIFICATION ---
        time.sleep(5)
        # Only save screenshot if running in headless or if you want logs
        if is_headless:
            print("Taking screenshot 'final_status.png'...")
            driver.save_screenshot("final_status.png")

    except Exception as e:
        print(f"ERROR: {str(e)}")
        driver.save_screenshot("error_debug.png")
        raise e
    
    finally:
        print("Closing browser...")
        driver.quit()

if __name__ == "__main__":
    run_attendance()
