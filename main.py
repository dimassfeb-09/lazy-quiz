# main.py (Support Continuous Loop / Multi-Block Exam)
# Copyright (C) 2025 Julius W. (@jtnqr)

import json
import os
import time

import typer
from dotenv import load_dotenv

import utils.ai_utils as ai
from utils.scraper_exam import ExamScraper
from utils.scraper_moodle import MoodleScraper

CACHE_DIR = "cache"


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
        print(f"Menginisialisasi Driver: {ScraperClass.__name__}")
        qz = ScraperClass(url, username, password)

        part_counter = 1  # Untuk penamaan file cache per bagian (Bagian 1, 2, dst)

        # --- LOOP UTAMA (CONTINUOUS) ---
        while True:
            if hasattr(qz, "get_current_block"):
                real_part = qz.get_current_block()
                if real_part > 0:
                    part_counter = real_part
                    print(
                        f"[Info] Terdeteksi halaman Website berada di BAGIAN {part_counter}"
                    )
            print(f"\n>>> MEMULAI PROSES: BAGIAN / PUTARAN KE-{part_counter} <<<")

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
                print(f"Cache Soal ditemukan! Memuat dari '{cache_file}'...")
                with open(cache_file, "r") as f:
                    qz_quizzes = json.load(f)
                qz.set_quiz_data(qz_quizzes)
            else:
                # Scraping via Playwright
                # Jika ini loop kedua (Bagian 2), fetch_all_quizzes akan ambil soal baru
                qz_quizzes = qz.fetch_all_quizzes()

                # --- CHECKPOINT KELUAR LOOP ---
                if not qz_quizzes:
                    print("\n[INFO] Tidak ditemukan soal lagi pada halaman ini.")
                    print(
                        "Kemungkinan seluruh ujian telah selesai atau berada di halaman Summary."
                    )
                    break  # KELUAR DARI LOOP WHILE

                os.makedirs(CACHE_DIR, exist_ok=True)
                with open(cache_file, "w") as f:
                    json.dump(qz_quizzes, f, indent=2)

            # --- FASE 2: LOAD JAWABAN (AI) ---
            if args.scrape_only:
                print("Mode --scrape-only aktif. Berhenti di sini.")
                break

            questions_for_ai = {
                int(k): {"question_text": v["question_text"], "answers": v["answers"]}
                for k, v in qz_quizzes.items()
                if not v.get("has_image")
            }

            answers_from_ai = {}
            # Cek Cache Jawaban
            if os.path.exists(answer_cache_file) and not args.no_cache:
                print(f"Cache Jawaban ditemukan! Memuat dari '{answer_cache_file}'...")
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
                print("\n" + "=" * 40)
                print(f"MENGISI BAGIAN {part_counter}...")
                print("=" * 40)

                filled_ids = qz.save_answers(answers_to_fill)

                # Statistik
                total_soal = len(qz_quizzes)
                total_terisi = len(filled_ids)
                total_gagal = total_soal - total_terisi
                print(f"Statistik: {total_terisi}/{total_soal} Terisi.")

                # Logic Konfirmasi
                do_submit = False
                if args.auto_submit:
                    do_submit = True
                else:
                    is_safe = total_gagal == 0
                    if is_safe:
                        prompt = f"Semua soal Bagian {part_counter} terisi. Lanjut Submit & Next Bagian? (y/n): "
                    else:
                        print(
                            f"⚠️ Peringatan: Ada {total_gagal} soal kosong di Bagian {part_counter}!"
                        )
                        prompt = "Paksa Submit & Lanjut? (ketik 'force' / 'n'): "

                    choice = input(prompt).strip().lower()
                    if (is_safe and choice in ["y", "yes"]) or choice == "force":
                        do_submit = True
                    else:
                        print(
                            "User membatalkan submit. Bot berhenti (Session Browser tetap terbuka sebentar)."
                        )
                        break  # Stop loop

                if do_submit:
                    print(f"\n[Action] Submit Bagian {part_counter}...")
                    qz.submit_final()

                    # Beri waktu napas untuk loading halaman baru
                    print("Menunggu loading halaman Bagian selanjutnya...")
                    time.sleep(5)

                    # Increment counter untuk loop berikutnya
                    part_counter += 1
            else:
                print("Tidak ada jawaban untuk diisi.")
                break

        print("\n=== SEMUA PROSES SELESAI ===")

    except Exception as e:
        print(f"\n--- TERJADI ERROR ---: {e}")
        import traceback

        traceback.print_exc()
    finally:
        if qz:
            qz.close()


def main(
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
    Lazy Quiz - Automated quiz solver for Moodle and ASP.NET platforms.

    Uses Playwright browser automation and Google Gemini AI to automatically
    answer quiz questions. For educational and research purposes only.
    """
    load_dotenv()
    moodle_username = os.environ.get("MOODLE_USERNAME")
    moodle_password = os.environ.get("MOODLE_PASSWORD")
    gemini_api_key = os.environ.get("GEMINI_API_KEY")
    gemini_model = os.environ.get("GEMINI_MODEL", "gemini-flash-latest")

    # Create args object for compatibility with run_quiz_process
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
        raw_url = typer.prompt("Masukkan URL Kuis")
        if raw_url:
            run_quiz_process(
                raw_url.strip(),
                args,
                moodle_username,
                moodle_password,
                gemini_api_key,
                gemini_model,
            )


if __name__ == "__main__":
    typer.run(main)
