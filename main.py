# main.py
import os
import json
import time
import argparse # Untuk menangani argumen baris perintah

# Impor modul-modul yang sudah kita buat
import config
from utils.logger_config import setup_logger
from core.browser_operations import BrowserAutomation

# Setup logger utama untuk aplikasi
logger = setup_logger('websandbox_main', config.LOG_LEVEL, config.LOG_FILE)

def save_network_log(network_data, target_url):
    """
    Menyimpan data log jaringan ke file JSON.
    Nama file akan didasarkan pada URL target dan timestamp.
    """
    if not network_data:
        logger.info("Tidak ada data jaringan untuk disimpan.")
        return None

    # Pastikan direktori network_logs ada
    if not os.path.exists(config.NETWORK_LOG_DIR):
        try:
            os.makedirs(config.NETWORK_LOG_DIR)
            logger.info(f"Direktori {config.NETWORK_LOG_DIR} berhasil dibuat.")
        except OSError as e:
            logger.error(f"Gagal membuat direktori {config.NETWORK_LOG_DIR}: {e}", exc_info=True)
            return None

    # Buat nama file yang unik dan deskriptif
    try:
        url_slug = target_url.split('//')[-1].split('/')[0].replace('.', '_').replace(':', '_')
    except Exception:
        url_slug = "invalid_url" # Fallback jika URL tidak standar
        
    timestamp_str = time.strftime("%Y%m%d-%H%M%S")
    filename = f"{url_slug}_{timestamp_str}_{config.DEFAULT_NETWORK_LOG_FILENAME}"
    filepath = os.path.join(config.NETWORK_LOG_DIR, filename)

    try:
        with open(filepath, 'w') as f:
            json.dump(network_data, f, indent=4)
        logger.info(f"Log jaringan berhasil disimpan ke: {filepath}")
        return filepath
    except IOError as e:
        logger.error(f"Gagal menyimpan log jaringan ke {filepath}: {e}", exc_info=True)
        return None
    except Exception as e:
        logger.error(f"Terjadi error tak terduga saat menyimpan log jaringan: {e}", exc_info=True)
        return None

def main():
    """
    Fungsi utama untuk menjalankan aplikasi sandbox.
    """
    logger.info("="*50)
    logger.info("Memulai Web Sandbox Analyzer")
    logger.info("="*50)

    # Setup parser argumen baris perintah
    parser = argparse.ArgumentParser(description="Analisis perilaku halaman web di sandbox.")
    parser.add_argument("url", nargs='?', default=config.DEFAULT_TARGET_URL,
                        help=f"URL yang akan dianalisis. Default: {config.DEFAULT_TARGET_URL}")
    
    args = parser.parse_args()
    target_url_to_analyze = args.url

    logger.info(f"URL target untuk analisis: {target_url_to_analyze}")

    # Buat instance BrowserAutomation
    automation = BrowserAutomation(target_url=target_url_to_analyze)

    # Lakukan analisis
    screenshot_path, network_events = automation.analyze_page()

    # Proses hasil
    if screenshot_path:
        logger.info(f"Analisis selesai. Screenshot disimpan di: {screenshot_path}")
    else:
        logger.warning("Analisis mungkin gagal atau tidak menghasilkan screenshot.")

    if network_events:
        logger.info(f"Total {len(network_events)} event jaringan terdeteksi.")
        saved_log_path = save_network_log(network_events, target_url_to_analyze)
        if saved_log_path:
            logger.info(f"Detail event jaringan telah disimpan.")
        else:
            logger.warning("Gagal menyimpan detail event jaringan.")
    else:
        logger.info("Tidak ada event jaringan yang terdeteksi atau analisis gagal.")

    logger.info("="*50)
    logger.info("Analisis Web Sandbox Selesai")
    logger.info("="*50)

if __name__ == "__main__":
    # Pastikan direktori output utama ada sebelum memulai
    # Meskipun sub-direktori akan dibuat oleh fungsi masing-masing,
    # memiliki direktori 'output' utama bisa berguna.
    if not os.path.exists("output"):
        try:
            os.makedirs("output")
        except OSError as e:
            # Jika tidak bisa membuat direktori output utama, log sebagai error kritis
            # karena ini akan mempengaruhi penyimpanan semua artefak.
            # Menggunakan print karena logger mungkin belum sepenuhnya siap atau bergantung pada path ini.
            print(f"CRITICAL: Tidak dapat membuat direktori output utama 'output': {e}", file=sys.stderr)
            # Anda bisa memilih untuk keluar dari aplikasi di sini jika direktori output krusial.
            # sys.exit(1) 
            
    main()
