# Web Sandbox Analyzer 🛡️🔍

**Analisis Perilaku Halaman Web Mencurigakan di Lingkungan Terisolasi (Client-Side Sandbox)**

[![Lisensi MIT](https://img.shields.io/badge/License-MIT-blue.svg)](https://opensource.org/licenses/MIT)
[![Python Versi](https://img.shields.io/badge/python-3.9%2B-blue.svg)](https://www.python.org/downloads/)
[![Docker Support](https://img.shields.io/badge/docker-%230db7ed.svg?style=for-the-badge&logo=docker&logoColor=white)](https://www.docker.com/)
[![Kontribusi Diterima](https://img.shields.io/badge/Contributions-welcome-brightgreen.svg?style=flat)](CONTRIBUTING.md)
[![Open Source Love](https://badges.frapsoft.com/os/v1/open-source.svg?v=103)](https://opensource.org/)
---

Web Sandbox Analyzer adalah sebuah alat yang dirancang untuk membantu analis keamanan (*blue teams*), peneliti, dan pengembang web dalam menganalisis perilaku halaman web atau skrip JavaScript yang mencurigakan di sisi klien. Alat ini menjalankan halaman web dalam *headless browser* di lingkungan Docker yang terisolasi, memantau berbagai aktivitas seperti permintaan jaringan, dan menghasilkan laporan untuk analisis lebih lanjut.

## ✨ Fitur Utama

* **Analisis Dinamis Sisi Klien:** Merender halaman web secara penuh, termasuk eksekusi JavaScript.
* **Pemantauan Aktivitas Jaringan:** Mencatat semua permintaan HTTP/HTTPS (termasuk XHR/Fetch), metode, *headers*, dan status respons.
* **Pengambilan Screenshot:** Mengambil gambar visual dari halaman yang dianalisis.
* **Isolasi dengan Docker:** Menjalankan analisis dalam *container* Docker yang aman dan terisolasi untuk mencegah dampak pada sistem *host*.
* **Output Terstruktur:** Menghasilkan log aktivitas jaringan dalam format JSON untuk kemudahan analisis.
* **Konfigurasi Mudah:** Pengaturan dapat disesuaikan melalui file `config.py`.
* **Operasi CLI:** Mudah dijalankan melalui antarmuka baris perintah.

## 🛠️ Teknologi yang Digunakan

* [Python](https://www.python.org/)
* [Playwright](https://playwright.dev/) untuk automasi browser
* [Docker](https://www.docker.com/) untuk kontainerisasi dan isolasi

## 🚀 Memulai

Berikut adalah cara untuk menyiapkan dan menjalankan Web Sandbox Analyzer.

### Prasyarat

* Python 3.9 atau lebih tinggi
* Pip (Python package installer)
* Git
* Docker (jika ingin menjalankan dalam mode terisolasi)

### Instalasi Lokal

1.  **Clone repositori:**
    ```bash
    git clone [https://github.com/adrhmnhkm/web-sandbox-analyzer.git](https://github.com/adrhmnhkm/web-sandbox-analyzer.git)
    cd NAMA_REPOSITORI_ANDA
    ```
2.  **Buat dan aktifkan virtual environment (disarankan):**
    ```bash
    python -m venv venv
    # Untuk Windows
    # .\venv\Scripts\activate
    # Untuk macOS/Linux
    source venv/bin/activate
    ```
3.  **Instal dependensi Python:**
    ```bash
    pip install -r requirements.txt
    ```
4.  **Instal browser Playwright (jika belum ada):**
    ```bash
    playwright install # Atau playwright install chromium
    ```

### Instalasi dengan Docker (Cara yang Direkomendasikan untuk Analisis Aman)

1.  **Clone repositori (jika belum):**
    ```bash
    git clone [https://github.com/NAMA_PENGGUNA_ANDA/NAMA_REPOSITORI_ANDA.git](https://github.com/NAMA_PENGGUNA_ANDA/NAMA_REPOSITORI_ANDA.git)
    cd NAMA_REPOSITORI_ANDA
    ```
2.  **Bangun Docker image:**
    ```bash
    docker build -t web-sandbox-analyzer .
    ```

## 📖 Penggunaan

### Menjalankan Secara Lokal

Dari direktori root proyek (pastikan virtual environment aktif):

* **Menganalisis URL default (dari `config.py`):**
    ```bash
    python main.py
    ```
* **Menganalisis URL spesifik:**
    ```bash
    python main.py [https://contoh-situs-mencurigakan.com](https://contoh-situs-mencurigakan.com)
    ```

### Menjalankan dengan Docker

* **Menganalisis URL spesifik:**
    ```bash
    docker run --rm -v "$(pwd)/output":/app/output web-sandbox-analyzer [https://contoh-situs-mencurigakan.com](https://contoh-situs-mencurigakan.com)
    ```
    *(Ganti `$(pwd)` dengan `%cd%` untuk Command Prompt Windows atau `${PWD}` untuk PowerShell Windows jika perlu)*

    Hasil analisis (screenshot dan log jaringan JSON) akan disimpan di direktori `output/` di sistem *host* Anda.

## 📊 Contoh Output

Setelah analisis selesai, Anda akan mendapatkan:

* **Screenshot Halaman:** File gambar (PNG) dari tampilan halaman web yang disimpan di `output/screenshots/`.
* **Log Aktivitas Jaringan:** File JSON yang berisi detail semua permintaan dan respons jaringan, disimpan di `output/network_logs/`.
* **Log Aplikasi:** Output log dari proses analisis akan ditampilkan di konsol dan disimpan di `app_activity.log`.

## 🗺️ Roadmap

Berikut adalah beberapa rencana pengembangan di masa depan:

* [ ] Implementasi Laporan HTML Interaktif untuk hasil analisis.
* [ ] Pemantauan `localStorage` dan `sessionStorage`.
* [ ] Deteksi penggunaan `eval()` dan eksekusi skrip dinamis.
* [ ] Ekstraksi otomatis Indikator Kompromi (IOC).
* [ ] Penambahan unit tests dan integration tests.
* [ ] Integrasi CI/CD dengan GitHub Actions.

Lihat [open issues](https://github.com/NAMA_PENGGUNA_ANDA/NAMA_REPOSITORI_ANDA/issues) untuk daftar lengkap fitur yang diusulkan (dan bug yang diketahui).

## 🤝 Berkontribusi

Kontribusi sangat kami hargai! Jika Anda ingin berkontribusi pada proyek ini, silakan lihat panduan di `CONTRIBUTING.md` (Anda perlu membuat file ini).

Beberapa cara Anda bisa berkontribusi:
* Melaporkan bug.
* Mengusulkan fitur baru.
* Menulis atau memperbaiki dokumentasi.
* Mengirimkan *pull request* dengan perbaikan atau fitur baru.

## 📜 Lisensi

Proyek ini dilisensikan di bawah Lisensi MIT. Lihat file `LICENSE` untuk detail lebih lanjut.
(Pastikan Anda memiliki file `LICENSE` di repositori Anda. Jika Anda memilih MIT, teksnya bisa didapatkan dari [sini](https://opensource.org/licenses/MIT)).

---

*Dibuat dengan ❤️ untuk komunitas keamanan siber.*
