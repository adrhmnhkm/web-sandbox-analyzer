# utils/logger_config.py
import logging
import sys
import os
# Impor konfigurasi dari file config.py di root project
# Untuk melakukannya, kita perlu menambahkan root project ke sys.path jika belum ada
# Ini adalah cara umum untuk menangani impor dari direktori yang berbeda dalam struktur proyek
try:
    import config
except ModuleNotFoundError:
    # Jika config.py tidak ditemukan, coba tambahkan direktori parent (root proyek) ke sys.path
    # Ini mengasumsikan logger_config.py ada di dalam direktori 'utils'
    # dan 'config.py' ada di root direktori proyek.
    current_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(current_dir) # Ini adalah direktori 'web_sandbox'
    if project_root not in sys.path:
        sys.path.insert(0, project_root)
    import config


def setup_logger(logger_name='web_sandbox', level=config.LOG_LEVEL, log_file=config.LOG_FILE):
    """
    Menyiapkan dan mengkonfigurasi logger.
    """
    logger = logging.getLogger(logger_name)
    logger.setLevel(getattr(logging, level.upper(), logging.INFO)) # Default ke INFO jika level tidak valid

    # Buat formatter
    formatter = logging.Formatter(config.LOG_FORMAT)

    # Handler untuk output ke konsol
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    # Handler untuk output ke file
    # Pastikan direktori log ada
    log_dir = os.path.dirname(log_file)
    if log_dir and not os.path.exists(log_dir):
        try:
            os.makedirs(log_dir)
        except OSError as e:
            # Jika ada masalah saat membuat direktori (misalnya, isu permission)
            # kita bisa log error ini ke konsol dan lanjut tanpa file logging
            # atau menghentikan aplikasi, tergantung kebutuhan.
            # Untuk sekarang, kita cetak error dan lanjut.
            print(f"Error creating log directory {log_dir}: {e}", file=sys.stderr)
            # Atau, bisa raise error jika file log sangat krusial:
            # raise OSError(f"Could not create log directory {log_dir}") from e
    
    # Hanya tambahkan file handler jika log_file diset dan direktori berhasil dibuat atau sudah ada
    if log_file and (not log_dir or os.path.exists(log_dir)):
        try:
            file_handler = logging.FileHandler(log_file, mode='a') # mode 'a' untuk append
            file_handler.setFormatter(formatter)
            logger.addHandler(file_handler)
        except Exception as e:
            # Jika ada masalah saat membuat file handler (misalnya, isu permission file)
            print(f"Error creating file handler for {log_file}: {e}", file=sys.stderr)


    # Hindari duplikasi log jika logger sudah memiliki handler (misalnya saat di-reload)
    logger.propagate = False

    return logger

# Contoh penggunaan logger (bisa dihapus atau dikomentari nanti)
# if __name__ == '__main__':
#     logger = setup_logger()
#     logger.debug("Ini adalah pesan debug.")
#     logger.info("Ini adalah pesan info.")
#     logger.warning("Ini adalah pesan peringatan.")
#     logger.error("Ini adalah pesan error.")
#     logger.critical("Ini adalah pesan critical.")
