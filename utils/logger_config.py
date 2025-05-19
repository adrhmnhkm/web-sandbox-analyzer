# utils/logger_config.py
import logging
import sys
import os
# Impor konfigurasi dari file config.py di root project
try:
    import config
except ModuleNotFoundError:
    current_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(current_dir) 
    if project_root not in sys.path:
        sys.path.insert(0, project_root)
    import config

# --- BARU: Definisi Kode Warna ANSI ---
class ANSIColors:
    RESET = "\033[0m"
    BOLD = "\033[1m"
    UNDERLINE = "\033[4m"

    BLACK = "\033[30m"
    RED = "\033[31m"
    GREEN = "\033[32m"
    YELLOW = "\033[33m"
    BLUE = "\033[34m"
    MAGENTA = "\033[35m"
    CYAN = "\033[36m"
    WHITE = "\033[37m"

    BRIGHT_BLACK = "\033[90m" # Grey
    BRIGHT_RED = "\033[91m"
    BRIGHT_GREEN = "\033[92m"
    BRIGHT_YELLOW = "\033[93m"
    BRIGHT_BLUE = "\033[94m"
    BRIGHT_MAGENTA = "\033[95m"
    BRIGHT_CYAN = "\033[96m"
    BRIGHT_WHITE = "\033[97m"

    BACKGROUND_BLACK = "\033[40m"
    BACKGROUND_RED = "\033[41m"
    BACKGROUND_GREEN = "\033[42m"
    BACKGROUND_YELLOW = "\033[43m"
    BACKGROUND_BLUE = "\033[44m"
    BACKGROUND_MAGENTA = "\033[45m"
    BACKGROUND_CYAN = "\033[46m"
    BACKGROUND_WHITE = "\033[47m"
# --- AKHIR BAGIAN BARU ---

# --- BARU: Custom Formatter untuk Warna ---
class ColoredFormatter(logging.Formatter):
    """
    Formatter kustom untuk menambahkan warna ke output log berdasarkan level.
    """
    LOG_LEVEL_COLORS = {
        logging.DEBUG: ANSIColors.BRIGHT_BLUE,
        logging.INFO: ANSIColors.BRIGHT_GREEN,
        logging.WARNING: ANSIColors.BRIGHT_YELLOW,
        logging.ERROR: ANSIColors.BRIGHT_RED,
        logging.CRITICAL: ANSIColors.BOLD + ANSIColors.BRIGHT_RED + ANSIColors.BACKGROUND_WHITE,
    }

    def format(self, record):
        # Dapatkan warna berdasarkan level log
        log_color = self.LOG_LEVEL_COLORS.get(record.levelno, ANSIColors.RESET)
        
        # Format pesan log asli
        # Kita bisa mewarnai seluruh baris atau hanya bagian tertentu (misalnya, levelname)
        # Untuk contoh ini, kita warnai levelname dan pesan
        
        # Simpan format asli
        original_fmt = self._style._fmt
        
        # Warnai levelname
        record.levelname = f"{log_color}{record.levelname}{ANSIColors.RESET}"
        
        # Kita bisa juga mewarnai pesan jika mau, tapi hati-hati jika pesan mengandung format lain
        # record.msg = f"{log_color}{record.msg}{ANSIColors.RESET}" # Contoh mewarnai pesan

        # Format pesan dengan levelname yang sudah berwarna
        formatted_message = super().format(record)
        
        # Kembalikan format asli untuk penggunaan selanjutnya (penting jika formatter digunakan oleh handler lain)
        self._style._fmt = original_fmt
        
        # Tambahkan warna pada seluruh pesan jika diinginkan, atau hanya pada bagian tertentu
        # Untuk output yang lebih elegan, kita bisa mewarnai timestamp, nama logger, dll. secara berbeda
        # Contoh sederhana: mewarnai seluruh baris berdasarkan level
        # return f"{log_color}{formatted_message}{ANSIColors.RESET}"
        
        # Untuk saat ini, kita hanya mewarnai levelname seperti di atas.
        # Jika ingin mewarnai lebih banyak, kita perlu memodifikasi format string atau
        # mem-parse dan mewarnai setiap bagian secara terpisah.

        # Untuk membuat lebih elegan, mari kita format ulang dengan warna pada bagian-bagian tertentu.
        log_fmt_parts = {
            'asctime': f"{ANSIColors.BRIGHT_BLACK}{record.asctime}{ANSIColors.RESET}",
            'name': f"{ANSIColors.CYAN}{record.name}{ANSIColors.RESET}",
            'levelname_colored': record.levelname, # Sudah diwarnai di atas
            'message': f"{log_color if record.levelno >= logging.WARNING else ANSIColors.RESET}{record.getMessage()}{ANSIColors.RESET}",
        }
        
        # Format string yang lebih elegan
        # Anda bisa menyesuaikan ini sesuai selera
        # Contoh: "2023-10-27 10:00:00,123 - my_logger - INFO - Ini pesan info"
        # Kita akan gunakan format default dari config, tapi dengan bagian yang diwarnai
        
        # Menggunakan format string yang mirip dengan config.LOG_FORMAT
        # tapi dengan placeholder yang sudah diwarnai
        # Ini agak rumit jika formatnya sangat dinamis.
        # Cara yang lebih mudah adalah dengan memodifikasi record sebelum diformat oleh super().format(record)
        
        # Kita akan tetap pada pendekatan mewarnai levelname dan pesan utama untuk kesederhanaan implementasi awal
        # dan mengembalikan formatted_message yang sudah dimodifikasi oleh super().format(record)
        # dengan record.levelname yang sudah berwarna.

        # Jika ingin mewarnai seluruh baris:
        # return f"{log_color}{super().format(record)}{ANSIColors.RESET}"
        
        # Untuk mewarnai bagian tertentu, kita perlu memodifikasi record sebelum super().format
        # atau membuat string format secara manual.

        # Mari kita coba pendekatan yang lebih terkontrol untuk format output:
        # Format dasar: '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        
        # Dapatkan pesan asli tanpa warna tambahan dari record.getMessage()
        message_original = record.getMessage()
        
        # Tentukan warna pesan utama berdasarkan level
        message_color = log_color if record.levelno >= logging.WARNING else "" # Hanya warnai pesan untuk WARNING ke atas
        
        # Buat output yang diformat
        # Ini adalah contoh, Anda bisa menyesuaikan format dan warna sesuai keinginan
        output = (
            f"{ANSIColors.BRIGHT_BLACK}{self.formatTime(record, self.datefmt)}{ANSIColors.RESET} - "
            f"{ANSIColors.CYAN}{record.name}{ANSIColors.RESET} - "
            f"{log_color}{record.levelname:<8}{ANSIColors.RESET} - " # <8 untuk padding
            f"{message_color}{message_original}{ANSIColors.RESET}"
        )
        return output

# --- AKHIR BAGIAN BARU ---


def setup_logger(logger_name='web_sandbox', level=config.LOG_LEVEL, log_file=config.LOG_FILE):
    """
    Menyiapkan dan mengkonfigurasi logger.
    """
    logger = logging.getLogger(logger_name)
    
    # Hindari duplikasi handler jika logger sudah diinisialisasi sebelumnya
    if logger.hasHandlers():
        logger.handlers.clear()
        
    logger.setLevel(getattr(logging, level.upper(), logging.INFO)) 

    # --- PERUBAHAN: Gunakan ColoredFormatter untuk console_handler ---
    # Formatter untuk konsol (berwarna)
    console_formatter = ColoredFormatter(config.LOG_FORMAT) # config.LOG_FORMAT mungkin tidak sepenuhnya digunakan jika kita override format di ColoredFormatter
    
    # Formatter untuk file (teks biasa, tanpa warna)
    file_formatter = logging.Formatter(config.LOG_FORMAT)
    # --- AKHIR PERUBAHAN ---

    # Handler untuk output ke konsol
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(console_formatter) # Menggunakan formatter berwarna
    logger.addHandler(console_handler)

    log_dir = os.path.dirname(log_file)
    if log_dir and not os.path.exists(log_dir):
        try:
            os.makedirs(log_dir)
        except OSError as e:
            print(f"Error creating log directory {log_dir}: {e}", file=sys.stderr)
    
    if log_file and (not log_dir or os.path.exists(log_dir)):
        try:
            file_handler = logging.FileHandler(log_file, mode='a') 
            file_handler.setFormatter(file_formatter) # Menggunakan formatter teks biasa
            logger.addHandler(file_handler)
        except Exception as e:
            print(f"Error creating file handler for {log_file}: {e}", file=sys.stderr)

    logger.propagate = False
    return logger

# Contoh penggunaan logger (bisa dihapus atau dikomentari nanti)
if __name__ == '__main__':
    # Atur LOG_LEVEL ke DEBUG untuk melihat semua level saat pengujian
    # Anda bisa mengubah ini di config.py atau secara langsung di sini untuk tes
    # config.LOG_LEVEL = "DEBUG" 
    
    test_logger = setup_logger('test_colored_logger', level="DEBUG", log_file="test_app_activity.log") # Tes dengan file log berbeda
    test_logger.debug(f"Ini adalah pesan {ANSIColors.BOLD}debug{ANSIColors.RESET} dengan sedikit {ANSIColors.UNDERLINE}gaya{ANSIColors.RESET}.")
    test_logger.info("Ini adalah pesan info standar.")
    test_logger.info(f"Anda juga bisa menyisipkan {ANSIColors.MAGENTA}warna{ANSIColors.RESET} di dalam pesan info jika perlu.")
    test_logger.warning("Peringatan! Ada sesuatu yang perlu diperhatikan.")
    test_logger.error("Terjadi kesalahan dalam operasi X.")
    test_logger.critical("Kesalahan Kritis! Sistem mungkin tidak stabil.")

    # Contoh untuk melihat bagaimana logger lain (misalnya dari library) akan tampil
    # logging.getLogger("another_library").warning("Pesan dari library lain.")
