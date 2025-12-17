import os

import google.generativeai as genai
from dotenv import load_dotenv

from utils.logger import logger

# Load environment variables from .env file
load_dotenv()

# Get your API key from the environment
API_KEY = os.environ.get("GEMINI_API_KEY")

if not API_KEY:
    logger.error("Error: GEMINI_API_KEY not found in .env file.")
else:
    try:
        genai.configure(api_key=API_KEY)

        logger.info("--- Finding Available Gemini Models ---")
        logger.info(
            "The following models support the 'generateContent' method and should work with your script:"
        )

        found_model = False
        for model in genai.list_models():
            # The script uses the 'generateContent' method, so we check for that support.
            if "generateContent" in model.supported_generation_methods:
                logger.info(f"  - {model.name}")
                found_model = True

        if not found_model:
            logger.info("\nCould not find any models that support 'generateContent'.")
            logger.info("This is unusual. Consider the following:")
            logger.info("1. Your API key may have restrictions.")
            logger.info("2. You might be in a region with limited model access.")
            logger.info(
                "3. Try generating a new API key in a new project in Google AI Studio."
            )

    except Exception as e:
        logger.error(f"\nAn error occurred while trying to connect to the API: {e}")
        logger.error(
            "Please check that your GEMINI_API_KEY in the .env file is correct and has no extra characters."
        )
