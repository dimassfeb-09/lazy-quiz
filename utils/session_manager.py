# utils/session_manager.py
"""
Session manager for Playwright browser contexts.
Saves and loads browser sessions to skip login on subsequent runs.
"""

import json
from pathlib import Path
from typing import Optional

from .logger import logger


class SessionManager:
    """Manages browser session persistence."""

    def __init__(self, session_dir: str = "cache"):
        self.session_dir = Path(session_dir)
        self.session_dir.mkdir(exist_ok=True)
        self.session_file = self.session_dir / "browser_session.json"
        self.state_file = self.session_dir / "browser_state"

    def save_session(self, context, username: str):
        """
        Save browser context state and username.

        Args:
            context: Playwright browser context
            username: Current username for validation
        """
        try:
            # Save browser state (cookies, localStorage, etc.)
            context.storage_state(path=str(self.state_file))

            # Save metadata (username for validation)
            metadata = {
                "username": username,
            }
            with open(self.session_file, "w") as f:
                json.dump(metadata, f)

            logger.info("✓ Session saved successfully")
        except Exception as e:
            logger.warning(f"Failed to save session: {e}")

    def load_session(self, current_username: str) -> Optional[str]:
        """
        Load browser session if valid for current username.

        Args:
            current_username: Username from .env to validate against

        Returns:
            Path to state file if valid, None otherwise
        """
        if not self.session_file.exists() or not self.state_file.exists():
            logger.debug("No saved session found")
            return None

        try:
            # Check if username matches
            with open(self.session_file, "r") as f:
                metadata = json.load(f)

            saved_username = metadata.get("username")

            if saved_username != current_username:
                logger.info(
                    f"Username changed ({saved_username} → {current_username}), skipping saved session"
                )
                return None

            logger.info("✓ Found valid session, loading...")
            return str(self.state_file)

        except Exception as e:
            logger.warning(f"Failed to load session: {e}")
            return None

    def clear_session(self):
        """Clear saved session."""
        try:
            if self.session_file.exists():
                self.session_file.unlink()
            if self.state_file.exists():
                self.state_file.unlink()
            logger.info("✓ Session cleared")
        except Exception as e:
            logger.warning(f"Failed to clear session: {e}")
