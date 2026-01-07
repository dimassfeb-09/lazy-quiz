#  Lazy Quiz - Moodle Quiz Bot
#  Copyright (C) 2025 Julius W. (@jtnqr)
#
#  This program is free software: you can redistribute it and/or modify
#  it under the terms of the GNU General Public License as published by
#  the Free Software Foundation, either version 3 of the License, or
#  (at your option) any later version.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#  along with this program.  If not, see <https://www.gnu.org/licenses/>.

import json
import re
import time
from typing import Dict

import google.generativeai as genai
from google.api_core import exceptions

from utils.logger import logger


def _format_batch_prompt(quizzes: dict) -> str:
    prompt = (
        "Anda adalah seorang ahli yang sangat akurat dalam menjawab kuis pilihan ganda. "
        "Di bawah ini ada beberapa pertanyaan. Analisis setiap pertanyaan dan pilihan jawabannya, "
        "lalu kembalikan satu objek JSON yang valid.\n\n"
        'Struktur JSON harus berupa: { "nomor_soal": "teks_jawaban_lengkap" }.\n'
        'Contoh: { "1": "b. Pilihan Jawaban Benar", "2": "c. Pilihan Lainnya" }.\n'
        "Pastikan teks jawaban yang Anda kembalikan sama persis dengan salah satu pilihan yang diberikan.\n\n"
        "Berikut adalah pertanyaannya:\n"
        "-------------------------------------\n"
    )
    for number, data in quizzes.items():
        prompt += f"\nSoal Nomor: {number}\n"
        prompt += f"Pertanyaan: {data['question_text']}\n"
        prompt += "Pilihan:\n"
        for opt in data["answers"]:
            prompt += f"- {opt}\n"
        prompt += "-------------------------------------\n"
    prompt += "\nHarap kembalikan hanya objek JSON sebagai respons Anda."
    return prompt


def get_gemini_answers(quizzes: dict, api_key: str, model_name: str) -> Dict[str, str]:
    genai.configure(api_key=api_key)
    try:
        model = genai.GenerativeModel(model_name)
    except exceptions.NotFound:
        logger.info(f"Gemini API Error: Model '{model_name}' tidak ditemukan.")
        return {}

    logger.info("--- Menghubungi Gemini API untuk semua jawaban (Mode Batch) ---")
    batch_prompt = _format_batch_prompt(quizzes)

    try:
        logger.info(f"Mengirim {len(quizzes)} pertanyaan teks dalam satu permintaan...")
        response = model.generate_content(batch_prompt)

        json_text = re.search(r"```json\s*([\s\S]+?)\s*```", response.text)
        cleaned_text = json_text.group(1) if json_text else response.text

        answers_from_ai = json.loads(cleaned_text)
        logger.info("Berhasil menerima dan mem-parsing semua jawaban dari Gemini.")
        return answers_from_ai
    except (json.JSONDecodeError, Exception) as e:
        logger.info(f"  > Terjadi error saat memproses respons dari AI: {e}")
        return {}


def get_gemini_answer_for_image(
    question_number: str,
    question_text: str,
    answers: list,
    image_data: bytes,
    api_key: str,
    model_name: str,
) -> str:
    """
    Get answer for an image-based question using Gemini Vision.

    Args:
        question_number: Question number for logging
        question_text: Any text associated with the question
        answers: List of answer options
        image_data: Screenshot of question as bytes (PNG)
        api_key: Gemini API key
        model_name: Gemini model name

    Returns:
        The selected answer text, or empty string if failed
    """
    import io

    import PIL.Image

    genai.configure(api_key=api_key)

    try:
        model = genai.GenerativeModel(model_name)
    except exceptions.NotFound:
        logger.error(f"Gemini API Error: Model '{model_name}' not found")
        return ""

    # Convert bytes to PIL Image
    image = PIL.Image.open(io.BytesIO(image_data))

    # Build prompt
    prompt = (
        "You are an expert at answering multiple choice questions. "
        "Look at this image carefully - it shows a question and/or answer options. "
        "The answer options may be shown as text OR as images in the screenshot. "
        "Identify the correct answer and return ONLY the letter/label of the correct option (e.g., 'a' or 'b' or 'c'). "
        "If you can see the full answer text, include it after the letter.\n\n"
    )

    if question_text and question_text.strip():
        prompt += f"Question context (if readable): {question_text}\n\n"

    if answers:
        prompt += "Known options (may or may not match image):\n"
        for opt in answers:
            prompt += f"- {opt}\n"

    prompt += "\nRespond with the correct answer option (letter + text if visible)."

    try:
        logger.info(f"  > [Image Q{question_number}] Sending to Gemini Vision...")
        response = model.generate_content([prompt, image])

        # Rate limiting: 15 RPM = 4 seconds between requests
        time.sleep(4)

        answer = response.text.strip()

        # Try to match with actual options
        for opt in answers:
            if answer.lower() in opt.lower() or opt.lower() in answer.lower():
                logger.info(f"  > [Image Q{question_number}] Answer: {opt[:50]}...")
                return opt

        # If no match, return the raw response (might still work)
        logger.info(f"  > [Image Q{question_number}] Raw answer: {answer[:50]}...")
        return answer

    except Exception as e:
        logger.error(f"  > [Image Q{question_number}] Gemini Vision error: {e}")
        return ""


def test_gemini_api(api_key: str, model_name: str) -> bool:
    logger.info("\n--- Testing Gemini API Connection ---")
    try:
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel(model_name)
        response = model.generate_content(
            "This is a test. Respond with the single word: OK"
        )
        if "OK" in response.text:
            logger.info("Gemini API Check: SUCCESS")
            return True
        else:
            logger.info("Gemini API Check: WARNING - Respons tidak terduga")
            return True
    except exceptions.PermissionDenied:
        logger.error("Gemini API Check: FAILED - API Key tidak valid")
        return False
    except exceptions.NotFound:
        logger.error(f"Gemini API Check: FAILED - Model '{model_name}' tidak ditemukan")
        return False
    except Exception as e:
        logger.error(f"Gemini API Check: FAILED - Error: {e}")
        return False
