# test_login.py - Playwright version
# Simple script to test login functionality

import os
import time

from dotenv import load_dotenv
from playwright.sync_api import sync_playwright

from utils.logger import logger
from utils.session_manager import SessionManager

# Load environment variables
load_dotenv()

MOODLE_USERNAME = os.environ.get("MOODLE_USERNAME")
MOODLE_PASSWORD = os.environ.get("MOODLE_PASSWORD")


def test_login(url=None, no_session=False):
    """
    Test login functionality using Playwright.

    Args:
        url: Login URL (optional, will prompt if not provided)
        no_session: If True, skip saved session and force fresh login
    """
    if not all([MOODLE_USERNAME, MOODLE_PASSWORD]):
        logger.error("Error: MOODLE_USERNAME and MOODLE_PASSWORD must be set in .env")
        return

    if not url:
        # Try to get base URL from .env first
        base_url = os.environ.get("MOODLE_URL", "").strip()

        if base_url:
            # Append /login to base URL
            url = base_url.rstrip("/") + "/login"
            logger.info(f"Using MOODLE_URL from .env: {url}")
        else:
            # Prompt user for URL
            url = input("Enter login URL: ").strip()
            if not url:
                url = "https://your-moodle-site.edu/login/index.php"
                logger.info(f"Using default URL: {url}")

    logger.info("Starting Playwright browser for login test...")

    # Initialize session manager
    session_manager = SessionManager()

    # Load session only if not skipped
    if no_session:
        logger.info("Skipping saved session (--no-session flag)")
        storage_state = None
    else:
        storage_state = session_manager.load_session(MOODLE_USERNAME)

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)  # Set to True for headless

        # Load saved session if available
        if storage_state:
            context = browser.new_context(
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
                storage_state=storage_state,
            )
        else:
            context = browser.new_context(
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
            )
        page = context.new_page()

        try:
            # If we have a session, just verify it works
            if storage_state:
                logger.info("Testing saved session...")
                # Go directly to dashboard to check if session is valid
                base_url = url.replace("/login", "")
                page.goto(base_url + "/my/")
                page.wait_for_load_state("domcontentloaded")

                if "Dashboard" in page.title() or "My courses" in page.title():
                    logger.info("=" * 30)
                    logger.info("  SESSION STILL VALID!")
                    logger.info("=" * 30)
                    logger.info(f"Current URL: {page.url}")
                    logger.info(f"Page title: {page.title()}")
                    logger.info("\\nBrowser will close in 3 seconds...")
                    time.sleep(3)
                    return  # Session works, no need to login
                else:
                    logger.info("Session expired, performing fresh login...")
                    session_manager.clear_session()

            # Normal login flow
            logger.info(f"Opening login page: {url}")
            page.goto(url)

            logger.info("Filling in login credentials...")
            page.fill('input[name="username"]', MOODLE_USERNAME)
            page.fill('input[name="password"]', MOODLE_PASSWORD)

            logger.info("Clicking login button...")
            page.click("button#loginbtn")

            # Wait for navigation
            page.wait_for_load_state("domcontentloaded")

            # Check if login was successful
            if "Dashboard" in page.title() or "My courses" in page.title():
                logger.info("=" * 21)
                logger.info("  LOGIN SUCCESSFUL!")
                logger.info("=" * 21)
                logger.info(f"Current URL: {page.url}")
                logger.info(f"Page title: {page.title()}")

                # Save session for future use
                session_manager = SessionManager()
                session_manager.save_session(context, MOODLE_USERNAME)
            else:
                logger.info("=" * 20)
                logger.info("  LOGIN FAILED")
                logger.info("=" * 20)
                logger.info(f"Current URL: {page.url}")
                logger.info(
                    "Check your credentials or update LOGIN_URL for your Moodle instance."
                )

                # Take screenshot for debugging
                page.screenshot(path="login_failure.png")
                logger.info("Screenshot saved as 'login_failure.png'")

            logger.info("\nBrowser will close in 3 seconds...")
            time.sleep(3)

        except Exception as e:
            logger.error(f"\nError during login test: {e}")
            page.screenshot(path="login_error.png")
            logger.info("Screenshot saved as 'login_error.png'")

        finally:
            browser.close()
            logger.info("Browser closed.")


if __name__ == "__main__":
    test_login()
