# test_login.py - Playwright version
# Simple script to test login functionality

import os
import time

from dotenv import load_dotenv
from playwright.sync_api import sync_playwright

# Load environment variables
load_dotenv()

MOODLE_USERNAME = os.environ.get("MOODLE_USERNAME")
MOODLE_PASSWORD = os.environ.get("MOODLE_PASSWORD")
LOGIN_URL = "https://your-moodle-site.edu/login/index.php"  # Generic URL


def test_login():
    """
    Test login functionality using Playwright.
    Updates the script to use Playwright instead of Selenium.
    """
    if not all([MOODLE_USERNAME, MOODLE_PASSWORD]):
        print("Error: MOODLE_USERNAME and MOODLE_PASSWORD must be set in .env")
        return

    print("Starting Playwright browser for login test...")

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)  # Set to True for headless
        context = browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        )
        page = context.new_page()

        try:
            print(f"Opening login page: {LOGIN_URL}")
            page.goto(LOGIN_URL)

            print("Filling in login credentials...")
            page.fill('input[name="username"]', MOODLE_USERNAME)
            page.fill('input[name="password"]', MOODLE_PASSWORD)

            print("Clicking login button...")
            page.click("button#loginbtn")

            # Wait for navigation
            page.wait_for_load_state("domcontentloaded")

            # Check if login was successful
            if "Dashboard" in page.title() or "My courses" in page.title():
                print("\n" + "=" * 40)
                print("  LOGIN SUCCESSFUL!")
                print("=" * 40)
                print(f"Current URL: {page.url}")
                print(f"Page title: {page.title()}")
            else:
                print("\n" + "=" * 40)
                print("  LOGIN FAILED")
                print("=" * 40)
                print(f"Current URL: {page.url}")
                print(
                    "Check your credentials or update LOGIN_URL for your Moodle instance."
                )

                # Take screenshot for debugging
                page.screenshot(path="login_failure.png")
                print("Screenshot saved as 'login_failure.png'")

            print("\nBrowser will close in 3 seconds...")
            time.sleep(3)

        except Exception as e:
            print(f"\nError during login test: {e}")
            page.screenshot(path="login_error.png")
            print("Screenshot saved as 'login_error.png'")

        finally:
            browser.close()
            print("Browser closed.")


if __name__ == "__main__":
    test_login()
