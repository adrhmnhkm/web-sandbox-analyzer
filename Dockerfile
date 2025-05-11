# Dockerfile

# 1. Gunakan image dasar Python yang resmi.
# Pilih versi Python yang sesuai dengan yang Anda gunakan untuk pengembangan (misalnya, 3.9, 3.10, 3.11).
# Versi slim lebih kecil ukurannya.
FROM python:3.10-slim

# 2. Set direktori kerja di dalam container
WORKDIR /app

# 3. Salin file requirements.txt terlebih dahulu untuk caching layer Docker
# Ini akan mempercepat build jika requirements tidak berubah.
COPY requirements.txt .

# 4. Instal dependensi Playwright dan browser yang dibutuhkan
#    Kita perlu menginstal beberapa dependensi sistem untuk Playwright/browser sebelum menginstal dari pip.
#    Daftar dependensi ini bisa bervariasi tergantung browser yang digunakan (chromium, firefox, webkit).
#    Perintah `playwright install-deps` akan membantu menginstal dependensi sistem.
#    Kemudian instal pustaka Python dari requirements.txt.
RUN apt-get update && apt-get install -y --no-install-recommends \
    # Dependensi umum yang mungkin dibutuhkan oleh Playwright dan browser headless
    # Ini adalah daftar yang cukup komprehensif untuk Chromium di Debian/Ubuntu.
    # Jika Anda hanya menargetkan satu browser, Anda mungkin bisa memangkasnya.
    libnss3 libnspr4 libdbus-1-3 libatk1.0-0 libatk-bridge2.0-0 \
    libcups2 libdrm2 libexpat1 libgbm1 libasound2 libxkbcommon0 \
    libx11-6 libx11-xcb1 libxcb1 libxcomposite1 libxcursor1 libxdamage1 \
    libxext6 libxfixes3 libxi6 libxrandr2 libxrender1 libxtst6 \
    # Font dependencies (penting agar teks render dengan benar)
    fonts-liberation \
    # Lainnya
    wget \
    xdg-utils \
    && rm -rf /var/lib/apt/lists/*

# Instal dependensi Python
RUN pip install --no-cache-dir -r requirements.txt

# Instal browser binaries yang dibutuhkan oleh Playwright
# Anda bisa memilih untuk menginstal semua atau hanya browser tertentu (misalnya, 'chromium')
# Menginstal semua akan membuat image lebih besar. Untuk sandbox, mungkin lebih baik spesifik.
# Kita akan menggunakan BROWSER_TYPE dari config.py jika memungkinkan,
# tapi untuk Dockerfile, kita hardcode dulu atau instal semua.
# Untuk contoh ini, kita instal Chromium saja untuk menjaga ukuran image.
# Jika Anda ingin semua: RUN playwright install --with-deps
# Jika hanya chromium:
RUN playwright install chromium --with-deps
# Jika Anda ingin menginstal browser berdasarkan config.py, itu akan lebih kompleks
# karena Dockerfile biasanya tidak membaca file Python saat build.
# Alternatifnya adalah menginstal semua browser di image dasar.

# 5. Salin sisa kode aplikasi ke dalam direktori kerja di container
COPY . .

# 6. Buat direktori output di dalam container (opsional, karena kita akan mount volume)
#    Namun, baik untuk mendefinisikannya agar aplikasi tidak error jika volume tidak di-mount.
RUN mkdir -p /app/output/screenshots && mkdir -p /app/output/network_logs

# 7. Tentukan perintah default yang akan dijalankan saat container dimulai.
#    Kita akan menjalankan main.py.
#    `python -u` digunakan untuk unbuffered output, yang baik untuk logging Docker.
ENTRYPOINT ["python", "-u", "main.py"]

# Default command (bisa di-override saat docker run)
# Misalnya, jika Anda ingin selalu menjalankan dengan URL default dari config.py
# CMD []
# Atau jika Anda ingin pengguna selalu menyediakan URL:
# (ENTRYPOINT sudah cukup untuk ini, pengguna akan menambahkan URL setelah nama image saat `docker run`)
