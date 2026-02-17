import time
import os
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager

# ==========================================
# CONFIGURATION
# ==========================================
HRONE_URL = "https://app.hrone.cloud/login#dynamischit"
EMAIL_ID = os.environ.get("HRONE_USER")
PASSWORD = os.environ.get("HRONE_PASS")

# --- 📍 LOCATION CONFIGURATION ---
try:
    LATITUDE = float(os.environ.get("LATITUDE")) 
    LONGITUDE = float(os.environ.get("LONGITUDE"))
except (TypeError, ValueError):
    raise ValueError("Latitude/Longitude not found or invalid! Check GitHub Secrets.")

ACCURACY = 100
HEADLESS_MODE = True 

def run_attendance():
    print("Initializing Chrome...")
    chrome_options = Options()
    
    # 1. Enable Geolocation Permission by default
    prefs = {
        "profile.default_content_setting_values.geolocation": 1,
        "profile.managed_default_content_settings.geolocation": 1
    }
    chrome_options.add_experimental_option("prefs", prefs)

    if HEADLESS_MODE:
        chrome_options.add_argument("--headless")
        chrome_options.add_argument("--window-size=1920,1080")
        chrome_options.add_argument("--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/90.0.4430.212 Safari/537.36")
    else:
        chrome_options.add_argument("--start-maximized")

    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=chrome_options)
    
    # 2. OVERRIDE LOCATION (Spoofing)
    params = {
        "latitude": LATITUDE,
        "longitude": LONGITUDE,
        "accuracy": ACCURACY
    }
    # This command will now receive Numbers, not Strings
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
        time.sleep(5) 

        # Check for auto-open popup
        try:
            print("Checking if popup is already open...")
            popup_mark_btn = driver.find_element(By.XPATH, "//div[contains(@class, 'modal') or contains(@class, 'dialog') or contains(@class, 'popup')]//button[contains(., 'Mark attendance')]")
            if popup_mark_btn.is_displayed():
                print("Popup is already open! Clicking confirm directly...")
                driver.execute_script("arguments[0].click();", popup_mark_btn)
                print("Clicked Popup. Waiting for confirmation...")
                time.sleep(5)
                driver.save_screenshot("final_status.png")
                return
        except:
            print("Popup not found yet.")

        # Click Dashboard Button
        print("Locating Dashboard 'Mark attendance' button...")
        home_mark_btn = wait.until(EC.presence_of_element_located((By.XPATH, "//button[contains(., 'Mark attendance')]")))
        
        print("Force-clicking Dashboard button...")
        driver.execute_script("arguments[0].click();", home_mark_btn)

        # --- MARK ATTENDANCE (POPUP) ---
        print("Waiting for Popup...")
        time.sleep(2)
        
        popup_mark_btn = wait.until(EC.presence_of_element_located((By.XPATH, "//div[contains(@class, 'modal') or contains(@class, 'dialog') or contains(@class, 'popup')]//button[contains(., 'Mark attendance')]")))
        
        print("Force-clicking Popup 'Mark attendance'...")
        driver.execute_script("arguments[0].click();", popup_mark_btn)
        
        print("Click Action Performed.")
        
        # --- VERIFICATION ---
        time.sleep(5)
        print("Taking debugging screenshot 'final_status.png'...")
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