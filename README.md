# Lazy Quiz v3.1 - Bot Otomatis Kuis (Playwright + Gemini AI)

## Pendahuluan

**Lazy Quiz** adalah skrip Python cerdas yang dirancang untuk mengotomatiskan pengerjaan kuis di platform e-learning menggunakan browser automation dan AI.

🚀 **Fitur Versi 3.1:**

- **Playwright Browser Automation** - Modern, cepat, dan stabil
- **Integrasi Gemini AI** - Mendukung soal teks DAN gambar
- **Auto Captcha Solving** - Gemini Vision memecahkan captcha otomatis
- **Session Persistence** - Skip login di run berikutnya
- **Smart Rate Limiting** - Penggunaan API yang efisien

---

## 🚨 **Penting: Penafian (Disclaimer)**

**PROYEK INI DIBUAT HANYA UNTUK TUJUAN PENDIDIKAN DAN EKSPERIMENTAL.**

- **Jangan Pernah** menggunakan skrip ini untuk mengerjakan ujian atau kuis yang sesungguhnya. Ini adalah kecurangan akademik.
- Pengguna **bertanggung jawab penuh** atas segala tindakan menggunakan kode ini.
- Pengembang tidak bertanggung jawab atas penyalahgunaan apa pun.

---

## ✨ Fitur

### Fitur Utama

- **Multi-Platform:** Moodle LMS dan platform ujian ASP.NET
- **AI-Powered:** Google Gemini untuk soal berbasis teks
- **Soal Bergambar:** Gemini Vision menganalisis screenshot soal bergambar
- **Anti-Detection:** Menghapus flag webdriver, mocking navigator properties
- **Sistem Cache:** Menyimpan soal secara lokal agar tidak perlu fetch ulang

### Baru di v3.1

- **Session Persistence:** Menyimpan cookies/state browser setelah login, skip login berikutnya
- **Auto Captcha Solving:** Gemini Vision membaca dan memecahkan captcha (platform ujian)
- **Smart Rate Limiting:** Hanya delay saat mendekati limit API, exponential backoff pada 429
- **Flag `--no-session`:** Paksa login baru saat diperlukan
- **Pemilihan Model Interaktif:** Pilih model Gemini jika belum dikonfigurasi

### Safe Mode (Default)

- Bot mengisi jawaban tapi **TIDAK auto-submit**
- Meminta konfirmasi sebelum submit akhir
- Gunakan `--auto-submit` untuk bypass konfirmasi

---

## 🌐 Kompatibilitas Platform

| Platform     | Deteksi            | Login              | Soal Gambar      |
| ------------ | ------------------ | ------------------ | ---------------- |
| Moodle LMS   | Otomatis (default) | Auto + Session     | ✅ Gemini Vision |
| ASP.NET Exam | `.aspx` di URL     | Auto Captcha Solve | ✅ Gemini Vision |

---

## ⚙️ Kebutuhan Sistem

- **Python 3.8+**
- **uv** - Package manager modern untuk Python
- Koneksi internet
- Google Gemini API Key (Gratis!)
- Playwright (auto-install Chromium)

---

## 🚀 Cara Penggunaan

### 1. Clone & Install

```bash
git clone https://github.com/jtnqr/lazy-quiz.git
cd lazy-quiz

# Install dependencies
pip install uv
uv sync

# Install browser
uv run playwright install chromium
```

### 2. Konfigurasi `.env`

```bash
# Salin example dan edit
cp .env.example .env
```

```ini
# Kredensial
MOODLE_USERNAME=username_anda
MOODLE_PASSWORD=password_anda

# URL Platform (opsional - untuk kemudahan)
MOODLE_URL=https://moodle-anda.edu
EXAM_URL=https://exam-anda.edu

# Gemini AI
GEMINI_API_KEY=AIzaSy.....
GEMINI_MODEL=gemini-flash-latest
```

### 3. Jalankan

```bash
# Mode interaktif (rekomendasi)
uv run python main.py

# Dengan URL
uv run python main.py run --url "https://moodle.edu/mod/quiz/attempt.php?..."

# Auto-submit (tanpa konfirmasi)
uv run python main.py run --url "..." --auto-submit
```

---

## 📋 Perintah CLI

| Perintah                  | Deskripsi                                    |
| ------------------------- | -------------------------------------------- |
| `run`                     | Otomasi kuis utama (default)                 |
| `test-login`              | Tes kredensial login                         |
| `test-login --no-session` | Paksa login baru (abaikan session tersimpan) |
| `check-models`            | Lihat daftar model Gemini yang tersedia      |

### Opsi Run

| Flag                 | Deskripsi                        |
| -------------------- | -------------------------------- |
| `--url TEXT`         | URL kuis yang akan diproses      |
| `--auto-submit`      | Submit tanpa konfirmasi          |
| `--scrape-only`      | Hanya ambil soal, tidak menjawab |
| `--no-cache`         | Paksa ambil ulang soal           |
| `--dry-run`          | Tes koneksi saja                 |
| `--answer-file FILE` | Muat jawaban dari file JSON      |

---

## 📁 Struktur Proyek

```
lazy-quiz/
├── main.py                  # Entry point CLI (Typer)
├── pyproject.toml           # Dependencies
├── .env                     # Kredensial (gitignored)
├── utils/
│   ├── scraper_base.py      # Base class scraper
│   ├── scraper_moodle.py    # Implementasi Moodle
│   ├── scraper_exam.py      # Implementasi ASP.NET exam
│   ├── ai_utils.py          # Gemini AI + Vision + Rate Limiter
│   ├── session_manager.py   # Session persistence browser
│   └── logger.py            # Logging terpusat
├── scripts/
│   ├── test_login.py        # Utilitas tes login
│   └── check_models.py      # Cek model Gemini
└── cache/                   # Cache soal (gitignored)
```

---

## 🔧 Cara Kerja

```
1. Muat session tersimpan (jika ada)
2. Login (otomatis atau manual)
   - Moodle: Auto-fill kredensial
   - Exam: Auto-solve captcha dengan Gemini Vision
3. Scrape soal-soal
   - Soal teks → batch ke Gemini
   - Soal gambar → screenshot → Gemini Vision
4. Isi jawaban di browser
5. Tunggu konfirmasi (atau auto-submit)
6. Simpan session untuk run berikutnya
```

---

## 📜 Lisensi

Proyek ini dilisensikan di bawah **GNU General Public License v3.0 (GPLv3)**.

Lihat file [LICENSE](LICENSE) untuk detail lebih lanjut.
