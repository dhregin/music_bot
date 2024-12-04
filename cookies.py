import os
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from dotenv import load_dotenv

def login_youtube():
    # Load environment variables
    load_dotenv(dotenv_path="/home/ec2-user/music_bot/.env")
    youtube_email = os.getenv("youtube_email")
    youtube_password = os.getenv("youtube_password")

    if not youtube_email or not youtube_password:
        print("YouTube email or password not found in .env file.")
        return

    # Setup WebDriver
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    service = Service('/usr/bin/chromedriver')  # Update with your ChromeDriver path
    driver = webdriver.Chrome(service=service, options=chrome_options)

    try:
        # Navigate to YouTube login
        driver.get("https://accounts.google.com/signin/v2/identifier")

        # Enter email
        email_input = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.NAME, "identifier"))
        )
        email_input.send_keys(youtube_email + Keys.RETURN)

        # Enter password
        password_input = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.NAME, "password"))
        )
        password_input.send_keys(youtube_password + Keys.RETURN)

        # Wait for the login process to complete
        WebDriverWait(driver, 15).until(
            EC.presence_of_element_located((By.XPATH, "//ytd-topbar-logo-renderer"))
        )

        # Export cookies
        cookies = driver.get_cookies()
        netscape_cookies = []
        for cookie in cookies:
            netscape_cookies.append(
                f"{cookie['domain']}\tTRUE\t{cookie['path']}\t{cookie['secure']}\t{cookie['expiry']}\t{cookie['name']}\t{cookie['value']}"
            )

        with open("/home/ec2-user/music_bot/cookies.txt", "w") as f:
            f.write("\n".join(netscape_cookies))

        print("Cookies saved successfully!")

    except Exception as e:
        print(f"Error during YouTube login: {e}")
    finally:
        driver.quit()

# Run the login function
login_youtube()
