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
EMAIL_ID = os.environ["HRONE_USER"]
PASSWORD = os.environ["HRONE_PASS"]

# Set FALSE to see the browser (Local testing), TRUE for GitHub Actions
HEADLESS_MODE = True 

def run_attendance():
    print("Initializing Chrome...")
    chrome_options = Options()
    if HEADLESS_MODE:
        chrome_options.add_argument("--headless")
        chrome_options.add_argument("--window-size=1920,1080")
    else:
        chrome_options.add_argument("--start-maximized")

    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=chrome_options)
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
        
        # 1. Wait for the page to settle (Crucial for overlays to disappear)
        time.sleep(5) 

        # 2. Check if the "Confirm" popup is ALREADY open (e.g. auto-open)
        try:
            print("Checking if popup is already open...")
            popup_mark_btn = driver.find_element(By.XPATH, "//div[contains(@class, 'modal') or contains(@class, 'dialog') or contains(@class, 'popup')]//button[contains(., 'Mark attendance')]")
            if popup_mark_btn.is_displayed():
                print("Popup is already open! Clicking confirm directly...")
                driver.execute_script("arguments[0].click();", popup_mark_btn)
                print("SUCCESS: Attendance Marked (Popup was auto-open).")
                return # Exit function, we are done
        except:
            print("Popup not found yet. Proceeding to click Dashboard button.")

        # 3. If popup wasn't there, find the Dashboard button
        print("Locating Dashboard 'Mark attendance' button...")
        home_mark_btn = wait.until(EC.presence_of_element_located((By.XPATH, "//button[contains(., 'Mark attendance')]")))
        
        # FIX: Use JavaScript Click to bypass overlays
        print("Force-clicking Dashboard button...")
        driver.execute_script("arguments[0].click();", home_mark_btn)

        # --- MARK ATTENDANCE (POPUP) ---
        print("Waiting for Popup...")
        time.sleep(2)
        
        # Wait for the popup button
        popup_mark_btn = wait.until(EC.presence_of_element_located((By.XPATH, "//div[contains(@class, 'modal') or contains(@class, 'dialog') or contains(@class, 'popup')]//button[contains(., 'Mark attendance')]")))
        
        print("Force-clicking Popup 'Mark attendance'...")
        driver.execute_script("arguments[0].click();", popup_mark_btn)
        
        print("SUCCESS: Attendance Marked Successfully.")
        time.sleep(5)

    except Exception as e:
        print(f"ERROR: {str(e)}")
        # driver.save_screenshot("debug_error.png")
        raise e
    
    finally:
        print("Closing browser...")
        driver.quit()

if __name__ == "__main__":
    run_attendance()