# main.py
import os
import json
import time
import argparse 
import sys 
from urllib.parse import urlparse

# Impor modul-modul yang sudah kita buat
import config
from utils.logger_config import setup_logger, ANSIColors
from core.browser_operations import BrowserAutomation
from core.report_generator import HTMLReportGenerator
from core.ioc_extractor import IOCExtractor 
from core.threat_intelligence import VirusTotalAnalyzer

# Setup logger utama untuk aplikasi
# Kita akan memindahkan inisialisasi logger utama ke dalam fungsi yang dipanggil
# agar tidak otomatis berjalan saat modul diimpor oleh skrip tes.
# logger = setup_logger('websandbox_main', config.LOG_LEVEL, config.LOG_FILE) # Dipindahkan

def get_main_logger():
    """Fungsi untuk mendapatkan instance logger utama."""
    return setup_logger('websandbox_main', config.LOG_LEVEL, config.LOG_FILE)

def save_network_log(network_data, target_url, project_root_path):
    logger = get_main_logger() # Gunakan logger
    if not network_data:
        logger.info("Tidak ada data jaringan untuk disimpan.")
        return None
    # ... (sisa kode save_network_log tetap sama) ...
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


def ensure_url_scheme(url_string):
    logger = get_main_logger() # Gunakan logger
    if not url_string:
        return None
    # ... (sisa kode ensure_url_scheme tetap sama) ...
    parsed_url = urlparse(url_string)
    if not parsed_url.scheme: 
        if os.path.exists(url_string) or url_string.startswith('/') or (len(url_string) > 1 and url_string[1] == ':'):
             logger.info(f"URL '{url_string}' terdeteksi sebagai path file lokal, menambahkan 'file:///'.")
             if len(url_string) > 1 and url_string[1] == ':':
                 return f"file:///{url_string.replace(os.sep, '/')}"
             return f"file://{os.path.abspath(url_string)}"
        logger.info(f"URL '{url_string}' tidak memiliki skema, menambahkan 'https://' secara default.")
        return f"https://{url_string}"
    elif parsed_url.scheme not in ['http', 'https', 'file']:
        logger.warning(f"URL '{url_string}' memiliki skema tidak didukung ('{parsed_url.scheme}'). Mencoba dengan 'https://'.")
        path_part = url_string.split('://', 1)[-1]
        return f"https://{path_part}"
    return url_string

def get_user_input(prompt_message, default_value=None, type_converter=str, validator=None, allowed_values=None):
    # ... (kode fungsi ini tetap sama, pastikan menggunakan print untuk interaksi langsung) ...
    colored_prompt = f"{ANSIColors.BRIGHT_CYAN}{prompt_message}{ANSIColors.RESET}"
    default_display = f"{ANSIColors.BRIGHT_YELLOW}(default: {default_value}){ANSIColors.RESET}" if default_value is not None else ""
    
    while True:
        try:
            user_input_str = input(f"{colored_prompt} {default_display}: ").strip()
            
            final_value_to_process = None
            if not user_input_str and default_value is not None:
                final_value_to_process = str(default_value)
            else:
                final_value_to_process = user_input_str

            if prompt_message.lower().startswith("masukkan url target"):
                processed_url = ensure_url_scheme(final_value_to_process)
                if not processed_url:
                    if not user_input_str and default_value is not None:
                        print(f"{ANSIColors.BRIGHT_RED}URL tidak boleh kosong. Silakan masukkan URL.{ANSIColors.RESET}")
                        continue
                    elif not user_input_str:
                         print(f"{ANSIColors.BRIGHT_RED}URL tidak boleh kosong. Silakan masukkan URL.{ANSIColors.RESET}")
                         continue
                    print(f"{ANSIColors.BRIGHT_RED}Gagal memproses URL. Silakan coba lagi.{ANSIColors.RESET}")
                    continue
                final_value_to_process = processed_url
            
            converted_value = type_converter(final_value_to_process)
            
            if validator and not validator(converted_value):
                print(f"{ANSIColors.BRIGHT_RED}Input tidak valid. Silakan coba lagi.{ANSIColors.RESET}")
                if allowed_values:
                    print(f"{ANSIColors.YELLOW}Pilihan yang diizinkan: {', '.join(allowed_values)}{ANSIColors.RESET}")
                continue
            if allowed_values and converted_value not in allowed_values:
                print(f"{ANSIColors.BRIGHT_RED}Input tidak ada dalam pilihan yang diizinkan. Pilihan: {', '.join(allowed_values)}{ANSIColors.RESET}")
                continue
            return converted_value
        except ValueError:
            print(f"{ANSIColors.BRIGHT_RED}Format input tidak valid. Silakan coba lagi.{ANSIColors.RESET}")
        except KeyboardInterrupt: 
            print(f"\n{ANSIColors.BRIGHT_YELLOW}Input dibatalkan oleh pengguna. Keluar...{ANSIColors.RESET}")
            sys.exit(0)
        except Exception as e:
            print(f"{ANSIColors.BRIGHT_RED}Terjadi error tak terduga saat input: {e}{ANSIColors.RESET}")
            sys.exit(1)

def print_banner():
    # ... (kode fungsi ini tetap sama) ...
    banner = fr"""
{ANSIColors.BRIGHT_GREEN}

  (`\ .-') /`   ('-. .-. .-')    .-')     ('-.         .-') _  _ .-') _ .-. .-')              ) (`-.      
   `.( OO ),' _(  OO)\  ( OO )  ( OO ).  ( OO ).-.    ( OO ) )( (  OO) )\  ( OO )              ( OO ).    
,--./  .--.  (,------.;-----.\ (_)---\_) / . --. /,--./ ,--,'  \     .'_ ;-----.\  .-'),-----.(_/.  \_)-. 
|      |  |   |  .---'| .-.  | /    _ |  | \-.  \ |   \ |  |\  ,`'--..._)| .-.  | ( OO'  .-.  '\  `.'  /  
|  |   |  |,  |  |    | '-' /_)\  :` `..-'-'  |  ||    \|  | ) |  |  \  '| '-' /_)/   |  | |  | \     /\  
|  |.'.|  |_)(|  '--. | .-. `.  '..`''.)\| |_.'  ||  .     |/  |  |   ' || .-. `. \_) |  |\|  |  \   \ |  
|         |   |  .--' | |  \  |.-._)   \ |  .-.  ||  |\    |   |  |   / :| |  \  |  \ |  | |  | .'    \_) 
|   ,'.   |   |  `---.| '--'  /\       / |  | |  ||  | \   |   |  '--'  /| '--'  /   `'  '-'  '/  .'.  \  
'--'   '--'   `------'`------'  `-----'  `--' `--'`--'  `--'   `-------' `------'      `-----''--'   '--' 
 
{ANSIColors.BRIGHT_CYAN}                        Client-Side Web Behavior Sandbox{ANSIColors.RESET}
{ANSIColors.BRIGHT_YELLOW}===================================================================================={ANSIColors.RESET}
"""
    print(banner)

# --- BARU: Fungsi Inti Analisis ---
def run_analysis_pipeline(target_url, browser_type, headless_mode, threat_intel_enabled, project_root_path):
    """
    Menjalankan alur kerja analisis inti.
    Mengembalikan dictionary berisi path ke file output dan data analisis.
    """
    logger = get_main_logger() # Pastikan logger diinisialisasi di sini
    logger.info(f"Memulai pipeline analisis untuk: {target_url}")
    logger.info(f"Browser: {browser_type}, Headless: {headless_mode}, Threat Intel: {threat_intel_enabled}")

    automation = BrowserAutomation(
        target_url=target_url,
        browser_type=browser_type,
        headless_mode=headless_mode
    )

    analysis_timestamp_start = time.strftime("%Y-%m-%d %H:%M:%S")
    screenshot_path, network_events, local_storage, session_storage, cookies, dynamic_js_calls = automation.analyze_page()
    
    extracted_iocs = {} 
    if network_events:
        logger.info("Memulai ekstraksi IOC dari data jaringan...")
        ioc_extractor = IOCExtractor(network_events)
        extracted_iocs = ioc_extractor.extract()
        logger.info(f"Ekstraksi IOC selesai. {len(extracted_iocs.get('unique_domains', []))} domain unik ditemukan.")
    else:
        logger.info("Tidak ada event jaringan, ekstraksi IOC dilewati.")

    virustotal_reports = []
    if threat_intel_enabled and config.VIRUSTOTAL_API_KEY and extracted_iocs.get("unique_domains"):
        logger.info("Memulai pemeriksaan reputasi domain dengan VirusTotal...")
        vt_analyzer = VirusTotalAnalyzer()
        unique_domains_to_check = extracted_iocs.get("unique_domains", [])
        for i, domain in enumerate(unique_domains_to_check):
            report = vt_analyzer.get_domain_report(domain)
            if report:
                virustotal_reports.append(report)
            if i < len(unique_domains_to_check) - 1: 
                logger.info(f"Menunggu {config.VIRUSTOTAL_REQUEST_DELAY} detik sebelum permintaan VirusTotal berikutnya...")
                time.sleep(config.VIRUSTOTAL_REQUEST_DELAY)
        logger.info(f"Pemeriksaan VirusTotal selesai. {len(virustotal_reports)} laporan diterima.")
    elif not config.VIRUSTOTAL_API_KEY and threat_intel_enabled:
        logger.warning("Pemeriksaan Threat Intelligence diaktifkan tetapi VIRUSTOTAL_API_KEY tidak diatur di config.py.")
    else:
        logger.info("Pemeriksaan Threat Intelligence (VirusTotal) dinonaktifkan atau tidak ada domain untuk diperiksa.")
    
    report_generator = HTMLReportGenerator() 
    analysis_data_for_report = {
        'target_url': target_url,
        'analysis_timestamp': analysis_timestamp_start,
        'screenshot_path': screenshot_path,
        'network_events': network_events,
        'local_storage': local_storage,        
        'session_storage': session_storage,
        'extracted_iocs': extracted_iocs,
        'cookies': cookies,
        'dynamic_js_calls': dynamic_js_calls,
        'virustotal_reports': virustotal_reports 
    }
    html_report_path = report_generator.generate_report(analysis_data_for_report)

    network_log_path = None
    if network_events:
        network_log_path = save_network_log(network_events, target_url, project_root_path)

    # Logging hasil (bisa dipindahkan ke luar jika fungsi ini hanya mengembalikan data)
    if screenshot_path: logger.info(f"Screenshot disimpan di: {screenshot_path}")
    else: logger.warning("Analisis mungkin gagal atau tidak menghasilkan screenshot.")
    if network_log_path: logger.info(f"Detail event jaringan telah disimpan di: {network_log_path}")
    if local_storage and 'error' not in local_storage: logger.info(f"Data localStorage terdeteksi: {len(local_storage)} item.")
    if session_storage and 'error' not in session_storage: logger.info(f"Data sessionStorage terdeteksi: {len(session_storage)} item.")
    if cookies and not (len(cookies) == 1 and 'error' in cookies[0]): logger.info(f"Data cookies terdeteksi: {len(cookies)} cookie.")
    if dynamic_js_calls: logger.info(f"Eksekusi JS Dinamis terdeteksi: {len(dynamic_js_calls)} panggilan.")
    if html_report_path: logger.info(f"Laporan HTML disimpan di: {html_report_path}")
    else: logger.warning("Gagal membuat laporan HTML.")

    return {
        "html_report_path": html_report_path,
        "screenshot_path": screenshot_path,
        "network_log_path": network_log_path,
        "analysis_data": analysis_data_for_report # Mengembalikan semua data untuk verifikasi tes
    }
# --- AKHIR FUNGSI BARU ---

def main():
    logger = get_main_logger() # Inisialisasi logger utama di sini
    if sys.stdout.isatty(): 
        print_banner()
    else: 
        logger.info("="*60)
        logger.info("               Web Sandbox Analyzer - Mode Non-Interaktif")
        logger.info("="*60)

    project_root_path = os.path.dirname(os.path.abspath(__file__)) 

    parser = argparse.ArgumentParser(description="Analisis perilaku halaman web di sandbox.")
    parser.add_argument("url", nargs='?', default=None, help="URL yang akan dianalisis.")
    parser.add_argument("-i", "--interactive", action="store_true", help="Jalankan dalam mode interaktif untuk memasukkan parameter.")
    parser.add_argument("-b", "--browser", choices=['chromium', 'firefox', 'webkit'], default=None, help=f"Tipe browser yang digunakan (default dari config: {config.BROWSER_TYPE}).")
    parser.add_argument("--headless", choices=['true', 'false'], default=None, help=f"Jalankan browser dalam mode headless (default dari config: {'true' if config.HEADLESS_MODE else 'false'}).")
    parser.add_argument("--no-threat-intel", action="store_false", dest="threat_intel", default=config.THREAT_INTEL_ENABLED, help="Nonaktifkan pemeriksaan threat intelligence (VirusTotal).")

    args = parser.parse_args()

    target_url_to_analyze = args.url
    browser_type_to_use = args.browser
    headless_mode_input = args.headless
    threat_intel_enabled_arg = args.threat_intel
    
    run_interactively = args.interactive

    if target_url_to_analyze: 
        processed_url_from_arg = ensure_url_scheme(target_url_to_analyze)
        if not processed_url_from_arg:
            logger.error(f"URL yang diberikan dari argumen CLI ('{target_url_to_analyze}') tidak valid. Keluar.")
            sys.exit(1)
        target_url_to_analyze = processed_url_from_arg

    if not target_url_to_analyze and not args.interactive:
        if sys.stdout.isatty(): 
            print(f"{ANSIColors.YELLOW}Tidak ada URL yang diberikan dan mode interaktif tidak dipilih.{ANSIColors.RESET}")
            parser.print_help()
            print(f"{ANSIColors.BRIGHT_GREEN}Menjalankan mode interaktif secara default...{ANSIColors.RESET}\n")
        else:
            logger.info("Tidak ada URL yang diberikan dan mode interaktif tidak dipilih. Menjalankan mode interaktif secara default...")
        run_interactively = True

    if run_interactively:
        if sys.stdout.isatty():
            print(f"{ANSIColors.BOLD}{ANSIColors.BRIGHT_MAGENTA}--- Mode Interaktif Konfigurasi Analisis ---{ANSIColors.RESET}")
        else:
            logger.info("--- Mode Interaktif Konfigurasi Analisis ---")

        if not target_url_to_analyze: 
            target_url_to_analyze = get_user_input("Masukkan URL Target", default_value=config.DEFAULT_TARGET_URL)
            if not target_url_to_analyze: 
                print(f"{ANSIColors.BRIGHT_RED}URL tidak valid atau kosong setelah input interaktif. Keluar.{ANSIColors.RESET}")
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
        
        if threat_intel_enabled_arg is config.THREAT_INTEL_ENABLED: 
            threat_intel_choice = get_user_input(
                "Aktifkan pemeriksaan Threat Intelligence (VirusTotal)? [y/n]",
                default_value='y' if config.THREAT_INTEL_ENABLED else 'n',
                allowed_values=['y', 'n', 'yes', 'no']
            ).lower()
            threat_intel_enabled_final = threat_intel_choice in ['y', 'yes']
        else:
            threat_intel_enabled_final = threat_intel_enabled_arg
        
        if sys.stdout.isatty():
            print(f"{ANSIColors.BOLD}{ANSIColors.BRIGHT_MAGENTA}-------------------------------------------{ANSIColors.RESET}\n")
        else:
            logger.info("-------------------------------------------")
    else: 
        if not target_url_to_analyze: 
            logger.error("URL target harus disediakan. Gunakan -i untuk mode interaktif atau berikan URL sebagai argumen.")
            parser.print_help()
            sys.exit(1)
        if browser_type_to_use is None: browser_type_to_use = config.BROWSER_TYPE
        if headless_mode_input is None: headless_mode_to_use = config.HEADLESS_MODE
        else: headless_mode_to_use = headless_mode_input == 'true'
        threat_intel_enabled_final = threat_intel_enabled_arg
    
    # --- PERUBAHAN: Memanggil fungsi pipeline analisis ---
    analysis_results = run_analysis_pipeline(
        target_url=target_url_to_analyze,
        browser_type=browser_type_to_use,
        headless_mode=headless_mode_to_use,
        threat_intel_enabled=threat_intel_enabled_final,
        project_root_path=project_root_path
    )
    # --- AKHIR PERUBAHAN ---

    logger.info("="*50)
    logger.info("Analisis Web Sandbox Selesai (dari main.py)") # Diubah sedikit untuk membedakan
    logger.info("="*50)


if __name__ == "__main__":
    output_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "output")
    if not os.path.exists(output_dir):
        try:
            os.makedirs(output_dir)
        except OSError as e:
            # Menggunakan get_main_logger() di sini bisa jadi masalah jika setup_logger belum dipanggil
            # Jadi, kita gunakan print untuk error kritis ini.
            print(f"KRITIS: Tidak dapat membuat direktori output utama 'output': {e}", file=sys.stderr)
            
    main()
