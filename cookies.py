from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
import pickle
import time

# Path to save cookies
COOKIES_PATH = "/home/ec2-user/music_bot/cookies.txt"

# Configure Chrome options
chrome_options = Options()
chrome_options.add_argument("--headless")  # Run Chrome in headless mode
chrome_options.add_argument("--disable-gpu")
chrome_options.add_argument("--no-sandbox")
chrome_options.add_argument("--disable-dev-shm-usage")

# Initialize WebDriver
driver = webdriver.Chrome(service=Service("/usr/bin/chromedriver"), options=chrome_options)

def login_to_youtube(email, password):
    try:
        # Open YouTube login page
        driver.get("https://accounts.google.com/signin/v2/identifier?service=youtube")

        # Enter email
        email_field = driver.find_element(By.ID, "identifierId")
        email_field.send_keys(email)
        email_field.send_keys(Keys.RETURN)
        time.sleep(3)

        # Enter password
        password_field = driver.find_element(By.NAME, "password")
        password_field.send_keys(password)
        password_field.send_keys(Keys.RETURN)
        time.sleep(5)

        # Wait for login to complete and redirect
        time.sleep(10)

        # Export cookies
        cookies = driver.get_cookies()
        with open(COOKIES_PATH, "w") as f:
            f.write("# Netscape HTTP Cookie File\n")
            for cookie in cookies:
                # Format cookies for Netscape
                f.write(f"{cookie['domain']}\t{'TRUE' if cookie['domain'].startswith('.') else 'FALSE'}\t")
                f.write(f"{cookie['path']}\t{'TRUE' if cookie.get('secure', False) else 'FALSE'}\t")
                f.write(f"{cookie['expiry'] if 'expiry' in cookie else '0'}\t{cookie['name']}\t{cookie['value']}\n")

        print(f"Cookies saved to {COOKIES_PATH}")

    except Exception as e:
        print(f"Error during login: {e}")
    finally:
        driver.quit()

# Replace with your YouTube login credentials
YOUTUBE_EMAIL = "your-email@example.com"
YOUTUBE_PASSWORD = "your-password"

login_to_youtube(YOUTUBE_EMAIL, YOUTUBE_PASSWORD)
