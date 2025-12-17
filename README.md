# Lazy Quiz v3.0 - Bot Otomatis Kuis Moodle (Playwright Version)

## Pendahuluan

**Lazy Quiz** adalah skrip Python cerdas yang dirancang untuk mengotomatiskan pengerjaan kuis di platform e-learning Moodle.

🚀 **Pembaruan Versi 2.0:**
Proyek ini telah mengalami **refactoring total**. Versi lama menggunakan Selenium, versi ini beralih ke **Playwright** - library browser automation modern yang lebih cepat, stabil, dan powerful.

**Apa bedanya dengan versi lama?**

- **Lebih Modern & Stabil:** Playwright lebih ringan dari Selenium, dengan API yang lebih baik dan error handling yang superior.
- **Headless Ready:** Bisa berjalan di mode headless untuk server/VPS atau dengan browser visible untuk debugging.
- **Anti-Detection:** Dilengkapi dengan teknik anti-bot detection (menghapus webdriver flags, mocking navigator properties).
- **Multi-Browser Support:** Mendukung Chromium, Firefox, dan WebKit (meskipun default menggunakan Chromium).

Proyek ini tetap terintegrasi dengan **Google Gemini AI** untuk menganalisis dan menjawab pertanyaan secara otomatis.

---

## 🚨 **Penting: Penafian (Disclaimer)**

**PROYEK INI DIBUAT HANYA UNTUK TUJUAN PENDIDIKAN DAN EKSPERIMENTAL.**

- **Jangan Pernah** menggunakan skrip ini untuk mengerjakan ujian, kuis, atau tugas akademik yang sesungguhnya. Melakukan hal tersebut adalah bentuk kecurangan dan pelanggaran serius terhadap **integritas akademik**.
- Konsekuensi dari kecurangan akademik bisa sangat berat, termasuk kegagalan mata kuliah, skorsing, atau bahkan dikeluarkan dari institusi pendidikan Anda.
- **Pengguna bertanggung jawab penuh** atas segala tindakan yang dilakukan menggunakan kode ini. Pengembang tidak bertanggung jawab atas penyalahgunaan apa pun.

---

## ✨ Fitur Baru (v3.0)

- **Playwright Browser Automation:** Login dan navigasi halaman dilakukan menggunakan Playwright dengan anti-detection features.
- **Auto-Fill & Save (Safe Mode):**
  - Bot akan **mengisi dan menyimpan** jawaban ke server Moodle secara otomatis.
  - **Human-in-the-loop:** Secara default, bot **TIDAK** akan melakukan _Final Submit_. Bot akan berhenti dan meminta konfirmasi Anda, memberi Anda kesempatan untuk memeriksa jawaban di browser sebelum disubmit.
- **Auto-Submit:** Opsi argumen `--auto-submit` untuk Anda yang ingin bot langsung melakukan _Submit all and finish_ tanpa konfirmasi.
- **Smart Scraping:** Mendeteksi navigasi halaman (pagination) dan melewati soal bergambar secara otomatis.
- **Integrasi AI:** Menggunakan Google Gemini untuk menjawab soal pilihan ganda berbasis teks.
- **Cache System:** Menyimpan soal yang sudah diambil agar tidak perlu _request_ ulang jika terjadi gangguan koneksi.

---

## 🌐 Platform Compatibility

This tool works with multiple learning management systems:

- **Moodle LMS**: Any Moodle-based platform (detects automatically from URL)
- **ASP.NET Exam Platforms**: Web Forms-based quiz systems (detects `.aspx` in URL)
- **Auto-Detection**: Scraper type is selected automatically based on your quiz URL

---

## ⚙️ Kebutuhan Sistem

- **Python 3.8** atau yang lebih baru.
- **uv** - Package manager modern untuk Python (lebih cepat dari pip).
- Koneksi Internet.
- Akun Google Gemini API (Gratis).
- **Playwright** akan menginstal browser Chromium secara otomatis saat setup.

---

## 🚀 Cara Penggunaan

1.  **Clone Repositori**

    ```bash
    git clone https://github.com/jtnqr/lazy-quiz.git
    cd lazy-quiz
    ```

2.  **Instal Dependensi & Sync Project**

    Proyek ini menggunakan **uv** untuk manajemen dependency yang lebih cepat:

    ```bash
    # Instal uv jika belum ada (opsional, hanya jika belum terinstal)
    pip install uv

    # Sync dependencies dari pyproject.toml
    uv sync
    ```

3.  **Instal Browser Playwright**

    Setelah menginstal dependencies, Playwright perlu mengunduh browser Chromium:

    ```bash
    # Gunakan uv run untuk menjalankan command di environment virtual
    uv run playwright install chromium
    ```

4.  **Siapkan File Konfigurasi (`.env`)**
    Salin file `.env.example` menjadi `.env` dan isi dengan kredensial Anda.

    ```bash
    # Ganti kredensial berikut dengan akun Moodle/V-Class Anda
    MOODLE_USERNAME="USERNAME_ANDA"
    MOODLE_PASSWORD="PASSWORD_ANDA"

    # API Key Google Gemini (Wajib untuk fitur AI)
    GEMINI_API_KEY="AIzaSy....."
    GEMINI_MODEL="gemini-pro"
    ```

5.  **Jalankan Skrip**

    - **Mode Interaktif (Rekomendasi):**
      Jalankan tanpa argumen. Skrip akan meminta URL kuis, mengisi jawaban, lalu meminta konfirmasi sebelum submit.

      ```bash
      uv run python main.py
      ```

    - **Mode Non-Interaktif (Langsung URL):**

      ```bash
      uv run python main.py --url "https://your-moodle-site.edu/mod/quiz/attempt.php?attempt=xxxxx"
      ```

    - **Mode Auto-Submit (Langsung Kumpul):**
      Gunakan flag ini jika Anda ingin bot langsung melakukan _Submit all and finish_ tanpa konfirmasi.

      ```bash
      uv run python main.py --url "..." --auto-submit
      ```

    - **Opsi Tambahan:**
      - `--scrape-only`: Hanya mengambil soal dan simpan ke JSON (tidak menjawab/mengisi ke Moodle).
      - `--answer-file "file.json"`: Mengisi kuis menggunakan jawaban dari file JSON lokal (tanpa AI).
      - `--no-cache`: Paksa ambil ulang soal dari server.
      - `--dry-run`: Tes login dan koneksi API tanpa mengakses kuis.

---

## 📁 Struktur Proyek

```
lazy-quiz/
├── .env                     # Konfigurasi kredensial
├── main.py                  # Entry point (CLI & Logic Controller)
├── pyproject.toml           # Daftar dependencies (playwright, google-generativeai, python-dotenv)
├── utils/
│   ├── scraper_base.py      # Base class untuk semua scrapers (Abstract)
│   ├── scraper_moodle.py    # Moodle LMS scraper implementation
│   ├── scraper_exam.py      # ASP.NET Web Forms exam scraper
│   └── ai_utils.py          # Integrasi Gemini API
├── cache/                   # Penyimpanan sementara soal (JSON)
└── output/                  # Hasil jawaban (Shareable JSON)
```

## 📜 Lisensi

Proyek ini dilindungi dan didistribusikan di bawah Lisensi **GNU General Public License v3.0 (GPLv3)**.

Lihat file `LICENSE` untuk informasi lebih lanjut.
