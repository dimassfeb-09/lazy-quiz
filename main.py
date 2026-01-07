# main.py (Support Continuous Loop / Multi-Block Exam)
# Copyright (C) 2025 Julius W. (@jtnqr)

import json
import os
import time

import typer
from dotenv import load_dotenv

import utils.ai_utils as ai
from utils.logger import logger
from utils.scraper_exam import ExamScraper
from utils.scraper_moodle import MoodleScraper

# Create Typer app
app = typer.Typer(
    help="Lazy Quiz - Automated quiz solver for Moodle and ASP.NET platforms"
)

CACHE_DIR = "cache"


def get_available_models(api_key: str) -> list:
    """Get list of available Gemini models that support text generation."""
    try:
        import google.generativeai as genai

        genai.configure(api_key=api_key)

        models = []
        for model in genai.list_models():
            if "generateContent" in model.supported_generation_methods:
                models.append(model.name)
        return models
    except Exception as e:
        logger.error(f"Failed to fetch models: {e}")
        return []


def prompt_model_selection(api_key: str) -> str:
    """Prompt user to select a Gemini model if not configured."""
    logger.info("GEMINI_MODEL not configured in .env")
    logger.info("Fetching available models...")

    models = get_available_models(api_key)

    if not models:
        logger.warning("No models found, using default: gemini-flash-latest")
        return "gemini-flash-latest"

    logger.info("\nAvailable Gemini models:")
    for i, model in enumerate(models, 1):
        logger.info(f"  {i}. {model}")

    # Prompt for selection
    while True:
        choice = typer.prompt("\nSelect model number (or press Enter for default)")

        if choice == "":
            default = "gemini-flash-latest"
            logger.info(f"Using default: {default}")
            return default

        try:
            idx = int(choice) - 1
            if 0 <= idx < len(models):
                selected = models[idx]
                logger.info(f"Selected: {selected}")
                return selected
            else:
                logger.warning(f"Invalid choice. Enter 1-{len(models)}")
        except ValueError:
            logger.warning("Invalid input. Enter a number or press Enter")


def get_scraper_class(url: str):
    """Detect scraper type based on platform indicators in URL"""
    # Check for ASP.NET indicators (.aspx extension, common ASP.NET patterns)
    if ".aspx" in url.lower():
        return ExamScraper
    # Default to Moodle (most common LMS)
    else:
        return MoodleScraper


def run_quiz_process(url, args, username, password, gemini_api_key, gemini_model):
    qz = None
    try:
        # 1. Start Browser (Hanya sekali di awal)
        ScraperClass = get_scraper_class(url)
        logger.info(f"Initializing scraper: {ScraperClass.__name__}")
        qz = ScraperClass(url, username, password)

        part_counter = 1  # Untuk penamaan file cache per bagian (Bagian 1, 2, dst)

        # --- LOOP UTAMA (CONTINUOUS) ---
        while True:
            if hasattr(qz, "get_current_block"):
                real_part = qz.get_current_block()
                if real_part > 0:
                    part_counter = real_part
                    logger.info(f"Detected current section: Part {part_counter}")
            logger.info(f"\n>>> STARTING PROCESS: PART {part_counter} <<<")

            # Reset memori scraper agar bersih untuk bagian baru
            qz.reset_quiz_data()

            # Ambil Info Kuis
            qz_title = qz.get_sanitized_title()
            quiz_id = qz.quiz_id

            # Setup Cache Filenames (Pembeda per part)
            # Contoh: Quiz_ID_Part1_questions.json
            file_suffix = f"_Part{part_counter}"
            cache_file = os.path.join(
                CACHE_DIR, f"{qz_title}_{quiz_id}{file_suffix}_questions.json"
            )
            answer_cache_file = os.path.join(
                CACHE_DIR, f"{qz_title}_{quiz_id}{file_suffix}_answers.json"
            )

            answers_to_fill = {}
            qz_quizzes = {}

            # --- FASE 1: SCRAPING SOAL ---
            # Cek apakah ada cache lokal untuk PART ini
            if os.path.exists(cache_file) and not args.no_cache:
                logger.info(f"Questions cache found! Loading from '{cache_file}'...")
                with open(cache_file, "r") as f:
                    qz_quizzes = json.load(f)
                qz.set_quiz_data(qz_quizzes)
            else:
                # Scraping via Playwright
                # Jika ini loop kedua (Bagian 2), fetch_all_quizzes akan ambil soal baru
                qz_quizzes = qz.fetch_all_quizzes()

                # --- CHECKPOINT KELUAR LOOP ---
                if not qz_quizzes:
                    logger.info("\nNo more questions found on this page.")
                    logger.info("Likely all sections complete or on summary page.")
                    break  # KELUAR DARI LOOP WHILE

                os.makedirs(CACHE_DIR, exist_ok=True)
                with open(cache_file, "w") as f:
                    json.dump(qz_quizzes, f, indent=2)

            # --- FASE 2: LOAD JAWABAN (AI) ---
            if args.scrape_only:
                logger.info("--scrape-only mode active. Stopping here.")
                break

            questions_for_ai = {
                int(k): {"question_text": v["question_text"], "answers": v["answers"]}
                for k, v in qz_quizzes.items()
                if not v.get("has_image")
            }

            answers_from_ai = {}
            # Cek Cache Jawaban
            if os.path.exists(answer_cache_file) and not args.no_cache:
                logger.info(
                    f"Answers cache found! Loading from '{answer_cache_file}'..."
                )
                with open(answer_cache_file, "r") as f:
                    answers_from_ai = json.load(f)
            # Tanya AI
            elif gemini_api_key and questions_for_ai:
                answers_from_ai = ai.get_gemini_answers(
                    questions_for_ai, gemini_api_key, gemini_model
                )
                if answers_from_ai:
                    with open(answer_cache_file, "w") as f:
                        json.dump(answers_from_ai, f, indent=2)

            # Gabungkan jawaban
            answers_to_fill = answers_from_ai

            # --- FASE 3: PENGISIAN & SUBMIT ---
            if answers_to_fill:
                logger.info("\n" + "=" * 40)
                logger.info(f"FILLING SECTION {part_counter}...")
                logger.info("=" * 40)

                filled_ids = qz.save_answers(answers_to_fill)

                # Statistik
                total_soal = len(qz_quizzes)
                total_terisi = len(filled_ids)
                total_gagal = total_soal - total_terisi
                logger.info(f"Statistics: {total_terisi}/{total_soal} Filled.")

                # Logic Konfirmasi
                do_submit = False
                if args.auto_submit:
                    do_submit = True
                else:
                    is_safe = total_gagal == 0
                    if is_safe:
                        prompt = f"Semua soal Bagian {part_counter} terisi. Lanjut Submit & Next Bagian? (y/n): "
                    else:
                        logger.warning(
                            f"⚠️  Warning: {total_gagal} questions empty in Part {part_counter}!"
                        )
                        prompt = "Paksa Submit & Lanjut? (ketik 'force' / 'n'): "

                    choice = input(prompt).strip().lower()
                    if (is_safe and choice in ["y", "yes"]) or choice == "force":
                        do_submit = True
                    else:
                        logger.info(
                            "User membatalkan submit. Bot berhenti (Session Browser tetap terbuka sebentar)."
                        )
                        break  # Stop loop

                if do_submit:
                    logger.info(f"\n[Action] Submitting Part {part_counter}...")
                    qz.submit_final()

                    # Beri waktu napas untuk loading halaman baru
                    logger.info("Waiting for next section to load...")
                    time.sleep(5)

                    # Increment counter untuk loop berikutnya
                    part_counter += 1
            else:
                logger.warning("No answers to fill.")
                break

        logger.info("\n=== ALL PROCESSES COMPLETE ===")

    except Exception as e:
        logger.error(f"\n--- ERROR OCCURRED ---: {e}")
        import traceback

        traceback.print_exc()
    finally:
        if qz:
            qz.close()


@app.command("run")
def run_command(
    url: str = typer.Option(None, "--url", help="Quiz URL to process"),
    scrape_only: bool = typer.Option(
        False, "--scrape-only", help="Only scrape questions, don't answer"
    ),
    no_cache: bool = typer.Option(False, "--no-cache", help="Ignore cached questions"),
    auto_submit: bool = typer.Option(
        False, "--auto-submit", help="Auto submit without confirmation"
    ),
    dry_run: bool = typer.Option(False, "--dry-run", help="Test connection only"),
    answer_file: str = typer.Option(
        None, "--answer-file", help="Use answers from JSON file"
    ),
):
    """
    Run the quiz automation (default command).

    Automatically solves quiz questions using Playwright and Gemini AI.
    """
    load_dotenv()
    moodle_username = os.environ.get("MOODLE_USERNAME")
    moodle_password = os.environ.get("MOODLE_PASSWORD")
    gemini_api_key = os.environ.get("GEMINI_API_KEY")
    gemini_model = os.environ.get("GEMINI_MODEL", "").strip()

    # If model not configured, prompt for selection
    if not gemini_model and gemini_api_key:
        gemini_model = prompt_model_selection(gemini_api_key)
    elif not gemini_model:
        # No API key, use default
        gemini_model = "gemini-flash-latest"
        logger.warning(f"Using default model: {gemini_model}")

    # Create args object for compatibility
    class Args:
        pass

    args = Args()
    args.scrape_only = scrape_only
    args.no_cache = no_cache
    args.auto_submit = auto_submit
    args.dry_run = dry_run
    args.answer_file = answer_file

    if url:
        run_quiz_process(
            url,
            args,
            moodle_username,
            moodle_password,
            gemini_api_key,
            gemini_model,
        )
    else:
        # Interactive mode
        raw_url = typer.prompt("Enter Quiz URL")
        if raw_url:
            run_quiz_process(
                raw_url.strip(),
                args,
                moodle_username,
                moodle_password,
                gemini_api_key,
                gemini_model,
            )


@app.command()
def test_login(
    url: str = typer.Option(None, "--url", help="Moodle/platform URL"),
    no_session: bool = typer.Option(
        False, "--no-session", help="Skip saved session, force fresh login"
    ),
):
    """Test Moodle/platform login credentials (opens browser)."""
    # Import and call the test_login script
    import sys

    sys.path.insert(0, "scripts")
    from test_login import test_login as run_test_login

    run_test_login(url, no_session=no_session)


@app.command()
def check_models():
    """Check available Gemini AI models for your API key."""
    # Import and run the check_models script
    import sys

    sys.path.insert(0, "scripts")


if __name__ == "__main__":
    # Make 'run' default if no command specified
    import sys

    if len(sys.argv) == 1 or (
        len(sys.argv) > 1
        and not sys.argv[1].startswith("-")
        and sys.argv[1] not in ["run", "test-login", "check-models"]
    ):
        sys.argv.insert(1, "run")

    app()
