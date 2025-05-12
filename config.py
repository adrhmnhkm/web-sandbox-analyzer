# config.py

# Pengaturan Browser
HEADLESS_MODE = True  # True untuk berjalan tanpa GUI, False untuk menampilkan browser (berguna saat debugging)
BROWSER_TYPE = "chromium"  # Pilihan: "chromium", "firefox", "webkit"
DEFAULT_TIMEOUT = 60000  # Timeout dalam milidetik (misalnya, untuk navigasi halaman)

# Pengaturan Output
SCREENSHOT_DIR = "output/screenshots"
NETWORK_LOG_DIR = "output/network_logs"
HTML_REPORT_DIR = "output/html_reports" # BARIS BARU

DEFAULT_SCREENSHOT_FILENAME = "capture.png"
DEFAULT_NETWORK_LOG_FILENAME = "network_activity.json"
DEFAULT_HTML_REPORT_FILENAME = "analysis_report.html" # BARIS BARU


# Pengaturan Logging
LOG_LEVEL = "INFO"  # Pilihan: "DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"
LOG_FILE = "app_activity.log" # File log utama aplikasi
LOG_FORMAT = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'

# Target URL default untuk analisis (bisa di-override dari argumen CLI nantinya)
DEFAULT_TARGET_URL = "https://jsonplaceholder.typicode.com/todos/1"
