# main.py
import os
import json
import time
import argparse 
import sys # Untuk sys.exit

# Impor modul-modul yang sudah kita buat
import config
from utils.logger_config import setup_logger
from core.browser_operations import BrowserAutomation
from core.report_generator import HTMLReportGenerator
from core.ioc_extractor import IOCExtractor 

# Setup logger utama untuk aplikasi
logger = setup_logger('websandbox_main', config.LOG_LEVEL, config.LOG_FILE)

def save_network_log(network_data, target_url, project_root_path):
    if not network_data:
        logger.info("Tidak ada data jaringan untuk disimpan.")
        return None

    log_dir_path = os.path.join(project_root_path, config.NETWORK_LOG_DIR)
    if not os.path.exists(log_dir_path):
        try:
            os.makedirs(log_dir_path)
            logger.info(f"Direktori {log_dir_path} berhasil dibuat.")
        except OSError as e:
            logger.error(f"Gagal membuat direktori {log_dir_path}: {e}", exc_info=True)
            return None

    try:
        url_slug = target_url.split('//')[-1].split('/')[0].replace('.', '_').replace(':', '_')
    except Exception:
        url_slug = "invalid_url"
        
    timestamp_str = time.strftime("%Y%m%d-%H%M%S")
    filename = f"{url_slug}_{timestamp_str}_{config.DEFAULT_NETWORK_LOG_FILENAME}"
    filepath = os.path.join(log_dir_path, filename)

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

def get_user_input(prompt_message, default_value=None, type_converter=str, validator=None, allowed_values=None):
    """Fungsi helper untuk mendapatkan input pengguna dengan validasi."""
    while True:
        user_input_str = input(f"{prompt_message} (default: {default_value}): ").strip()
        if not user_input_str and default_value is not None:
            return default_value
        try:
            converted_value = type_converter(user_input_str)
            if validator and not validator(converted_value):
                logger.warning("Input tidak valid. Silakan coba lagi.")
                if allowed_values:
                    logger.info(f"Pilihan yang diizinkan: {', '.join(allowed_values)}")
                continue
            if allowed_values and converted_value not in allowed_values:
                logger.warning(f"Input tidak ada dalam pilihan yang diizinkan. Pilihan: {', '.join(allowed_values)}")
                continue
            return converted_value
        except ValueError:
            logger.warning("Format input tidak valid. Silakan coba lagi.")

def main():
    logger.info("="*50)
    logger.info("Memulai Web Sandbox Analyzer")
    logger.info("="*50)

    project_root_path = os.path.dirname(os.path.abspath(__file__)) 

    parser = argparse.ArgumentParser(description="Analisis perilaku halaman web di sandbox.")
    parser.add_argument("url", nargs='?', default=None,
                        help="URL yang akan dianalisis.")
    parser.add_argument("-i", "--interactive", action="store_true",
                        help="Jalankan dalam mode interaktif untuk memasukkan parameter.")
    parser.add_argument("-b", "--browser", choices=['chromium', 'firefox', 'webkit'], default=None,
                        help=f"Tipe browser yang digunakan (default dari config: {config.BROWSER_TYPE}).")
    parser.add_argument("--headless", choices=['true', 'false'], default=None,
                        help=f"Jalankan browser dalam mode headless (default dari config: {'true' if config.HEADLESS_MODE else 'false'}).")
    
    args = parser.parse_args()

    target_url_to_analyze = args.url
    browser_type_to_use = args.browser
    headless_mode_input = args.headless
    
    run_interactively = args.interactive

    if not target_url_to_analyze and not args.interactive:
        logger.info("Tidak ada URL yang diberikan dan mode interaktif tidak dipilih.")
        parser.print_help()
        logger.info("Menjalankan mode interaktif secara default...")
        run_interactively = True

    if run_interactively:
        logger.info("--- Mode Interaktif ---")
        if not target_url_to_analyze: 
            target_url_to_analyze = get_user_input("Masukkan URL Target", default_value="https://example.com")
            if not target_url_to_analyze or not target_url_to_analyze.startswith(('http://', 'https://')):
                logger.error("URL tidak valid atau kosong. Keluar.")
                sys.exit(1)
        
        if browser_type_to_use is None: 
            browser_type_to_use = get_user_input(
                "Pilih tipe browser [chromium, firefox, webkit]",
                default_value=config.BROWSER_TYPE,
                allowed_values=['chromium', 'firefox', 'webkit']
            ).lower()

        if headless_mode_input is None: 
            headless_choice = get_user_input(
                "Jalankan dalam mode headless? [y/n]",
                default_value='y' if config.HEADLESS_MODE else 'n',
                allowed_values=['y', 'n', 'yes', 'no']
            ).lower()
            headless_mode_to_use = headless_choice in ['y', 'yes']
        else: 
            headless_mode_to_use = headless_mode_input == 'true'
        logger.info("----------------------")
    else: 
        if not target_url_to_analyze:
            logger.error("URL target harus disediakan jika tidak dalam mode interaktif. Gunakan -i untuk mode interaktif.")
            parser.print_help()
            sys.exit(1)
        
        if browser_type_to_use is None:
            browser_type_to_use = config.BROWSER_TYPE
        if headless_mode_input is None:
            headless_mode_to_use = config.HEADLESS_MODE
        else:
            headless_mode_to_use = headless_mode_input == 'true'

    logger.info(f"URL target untuk analisis: {target_url_to_analyze}")
    logger.info(f"Tipe browser yang akan digunakan: {browser_type_to_use}")
    logger.info(f"Mode headless: {headless_mode_to_use}")

    automation = BrowserAutomation(
        target_url=target_url_to_analyze,
        browser_type=browser_type_to_use,
        headless_mode=headless_mode_to_use
    )

    analysis_timestamp_start = time.strftime("%Y-%m-%d %H:%M:%S")
    # --- PERUBAHAN DI SINI: Menerima 6 nilai ---
    screenshot_path, network_events, local_storage, session_storage, cookies, dynamic_js_calls = automation.analyze_page()
    
    extracted_iocs = {} 
    if network_events:
        logger.info("Memulai ekstraksi IOC dari data jaringan...")
        ioc_extractor = IOCExtractor(network_events)
        extracted_iocs = ioc_extractor.extract()
        logger.info(f"Ekstraksi IOC selesai. {len(extracted_iocs.get('unique_domains', []))} domain unik ditemukan.")
    else:
        logger.info("Tidak ada event jaringan, ekstraksi IOC dilewati.")

    report_generator = HTMLReportGenerator() 
    
    # --- PERUBAHAN DI SINI: Menambahkan data dynamic_js_calls ke laporan ---
    analysis_data_for_report = {
        'target_url': target_url_to_analyze,
        'analysis_timestamp': analysis_timestamp_start,
        'screenshot_path': screenshot_path,
        'network_events': network_events,
        'local_storage': local_storage,        
        'session_storage': session_storage,
        'extracted_iocs': extracted_iocs,
        'cookies': cookies,
        'dynamic_js_calls': dynamic_js_calls # BARU
    }
    html_report_path = report_generator.generate_report(analysis_data_for_report)

    if screenshot_path:
        logger.info(f"Analisis selesai. Screenshot disimpan di: {screenshot_path}")
    else:
        logger.warning("Analisis mungkin gagal atau tidak menghasilkan screenshot.")

    if network_events:
        logger.info(f"Total {len(network_events)} event jaringan terdeteksi.")
        saved_log_path = save_network_log(network_events, target_url_to_analyze, project_root_path)
        if saved_log_path:
            logger.info(f"Detail event jaringan telah disimpan.")
        else:
            logger.warning("Gagal menyimpan detail event jaringan.")
    else:
        logger.info("Tidak ada event jaringan yang terdeteksi atau analisis gagal.")
    
    if local_storage:
        logger.info(f"Data localStorage terdeteksi: {len(local_storage)} item.")
    if session_storage:
        logger.info(f"Data sessionStorage terdeteksi: {len(session_storage)} item.")
    if cookies and not (len(cookies) == 1 and 'error' in cookies[0]):
        logger.info(f"Data cookies terdeteksi: {len(cookies)} cookie.")
    elif cookies and 'error' in cookies[0]: # Handle case where cookies might be an error list
        logger.warning(f"Gagal mengambil cookies: {cookies[0]['error']}")
    
    # BARU: Logging untuk eksekusi JS dinamis
    if dynamic_js_calls: # Check if the list is not None and not empty
        logger.info(f"Eksekusi JS Dinamis terdeteksi: {len(dynamic_js_calls)} panggilan.")
    else: 
        logger.info("Tidak ada eksekusi JS dinamis yang terdeteksi.")


    if html_report_path:
        logger.info(f"Laporan HTML disimpan di: {html_report_path}")
    else:
        logger.warning("Gagal membuat laporan HTML.")

    logger.info("="*50)
    logger.info("Analisis Web Sandbox Selesai")
    logger.info("="*50)

if __name__ == "__main__":
    output_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "output")
    if not os.path.exists(output_dir):
        try:
            os.makedirs(output_dir)
        except OSError as e:
            print(f"KRITIS: Tidak dapat membuat direktori output utama 'output': {e}", file=sys.stderr)
            
    main()
