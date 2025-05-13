# core/report_generator.py
import os
import time
import shutil 
from jinja2 import Environment, FileSystemLoader, select_autoescape, exceptions as JinjaExceptions

# Impor konfigurasi dan logger
import sys
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(current_dir)
if project_root not in sys.path:
    sys.path.insert(0, project_root)

import config
from utils.logger_config import setup_logger

# Setup logger untuk modul ini
logger = setup_logger(__name__, config.LOG_LEVEL, config.LOG_FILE)

class HTMLReportGenerator:
    def __init__(self, template_dir="templates"):
        """
        Inisialisasi generator laporan.
        :param template_dir: Direktori tempat template HTML disimpan.
        """
        self.template_dir = os.path.join(project_root, template_dir)
        self.env = Environment(
            loader=FileSystemLoader(self.template_dir),
            autoescape=select_autoescape(['html', 'xml'])
        )
        self.env.filters['unixtimestampformat'] = self.unixtimestampformat
        logger.debug(f"Jinja2 Environment initialized with template directory: {self.template_dir}")

    def unixtimestampformat(self, value, format="%Y-%m-%d %H:%M:%S"):
        """Filter Jinja2 untuk memformat timestamp Unix."""
        if value is None or isinstance(value, (str)) or value == -1: 
            return "Sesi" if value == -1 else "Tidak Ditentukan"
        try:
            return time.strftime(format, time.localtime(value))
        except (TypeError, ValueError):
            return value 

    def generate_report(self, analysis_data):
        """
        Menghasilkan laporan HTML dari data analisis DINAMIS yang diterima.
        :param analysis_data: Dictionary yang berisi data untuk laporan.
        :return: Path ke file laporan HTML yang dihasilkan, atau None jika gagal.
        """
        try:
            template_name = "report_template.html" 
            template = self.env.get_template(template_name)
            logger.debug(f"Mencoba memuat template: {template_name}")
            
            target_url = analysis_data.get('target_url', 'N/A') 
            
            url_slug = target_url.split('//')[-1].split('/')[0].replace('.', '_').replace(':', '_')
            timestamp_str = time.strftime("%Y%m%d-%H%M%S")
            report_filename = f"{url_slug}_{timestamp_str}_{config.DEFAULT_HTML_REPORT_FILENAME}"
            report_filepath = os.path.join(project_root, config.HTML_REPORT_DIR, report_filename)

            if not os.path.exists(os.path.dirname(report_filepath)):
                os.makedirs(os.path.dirname(report_filepath))
                logger.info(f"Direktori laporan HTML dibuat: {os.path.dirname(report_filepath)}")

            original_screenshot_path = analysis_data.get('screenshot_path') 
            screenshot_filename_for_report = None
            if original_screenshot_path and os.path.exists(original_screenshot_path):
                try:
                    base_screenshot_name = os.path.basename(original_screenshot_path)
                    report_specific_screenshot_name = f"{url_slug}_{timestamp_str}_{base_screenshot_name}"
                    destination_screenshot_path = os.path.join(os.path.dirname(report_filepath), report_specific_screenshot_name)
                    shutil.copy2(original_screenshot_path, destination_screenshot_path)
                    screenshot_filename_for_report = report_specific_screenshot_name
                    logger.info(f"Screenshot disalin ke: {destination_screenshot_path}")
                except Exception as e:
                    logger.error(f"Gagal menyalin screenshot {original_screenshot_path} ke direktori laporan: {e}", exc_info=True)
                    screenshot_filename_for_report = None
            else:
                logger.warning(f"File screenshot asli tidak ditemukan di: {original_screenshot_path} atau path tidak valid.")

            # --- PENAMBAHAN DEBUG LOG DI SINI ---
            dynamic_js_calls_received = analysis_data.get('dynamic_js_calls', [])
            logger.debug(f"Data 'dynamic_js_calls' yang diterima oleh report_generator: {dynamic_js_calls_received}")
            # --- AKHIR PENAMBAHAN DEBUG LOG ---

            template_data = {
                'target_url': target_url,
                'analysis_timestamp': analysis_data.get('analysis_timestamp', time.strftime("%Y-%m-%d %H:%M:%S")),
                'screenshot_path': original_screenshot_path, 
                'screenshot_filename': screenshot_filename_for_report, 
                'network_events': analysis_data.get('network_events', []),
                'local_storage': analysis_data.get('local_storage', {}),     
                'session_storage': analysis_data.get('session_storage', {}),
                'extracted_iocs': analysis_data.get('extracted_iocs', {}),
                'cookies': analysis_data.get('cookies', []),
                'dynamic_js_calls': dynamic_js_calls_received # Menggunakan variabel yang sudah di-debug
            }

            rendered_html = template.render(template_data)

            with open(report_filepath, 'w', encoding='utf-8') as f:
                f.write(rendered_html)
            
            logger.info(f"Laporan HTML berhasil dibuat: {report_filepath}")
            return report_filepath

        except JinjaExceptions.TemplateNotFound as e: 
            logger.error(f"Template file tidak ditemukan: {e}. Pastikan file '{template_name}' ada di direktori '{self.template_dir}'.", exc_info=True)
            return None
        except Exception as e:
            logger.error(f"Gagal menghasilkan laporan HTML: {e}", exc_info=True)
            return None

# Bagian ini HANYA untuk pengujian modul report_generator.py secara terpisah.
if __name__ == '__main__':
    logger.info("Menjalankan report_generator.py secara langsung untuk pengujian DUMMY.")
    
    dummy_target_url = "https://example-dummy-dynamicjs.com"
    dummy_timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
    
    dummy_screenshot_dir = os.path.join(project_root, config.SCREENSHOT_DIR)
    if not os.path.exists(dummy_screenshot_dir):
        os.makedirs(dummy_screenshot_dir)
    
    dummy_screenshot_filename = f"example_dummy_dynamicjs_com_{time.strftime('%Y%m%d-%H%M%S')}_capture.png"
    dummy_screenshot_path = os.path.join(dummy_screenshot_dir, dummy_screenshot_filename)
    try:
        with open(dummy_screenshot_path, 'wb') as f: 
            f.write(b"dummy screenshot content") 
        logger.info(f"File screenshot dummy dibuat di: {dummy_screenshot_path}")
    except Exception as e:
        logger.error(f"Tidak dapat membuat file screenshot dummy: {e}")
        dummy_screenshot_path = None

    dummy_network_events = [] 
    dummy_local_storage = {}
    dummy_session_storage = {}
    dummy_extracted_iocs = {}
    dummy_cookies = []

    dummy_dynamic_js_calls = [
        {"timestamp": time.time(), "function_name": "eval", "arguments": "alert('eval test 1');", "source_url": dummy_target_url},
        {"timestamp": time.time(), "function_name": "setTimeout", "arguments": "console.log('timeout test')", "source_url": dummy_target_url},
        {"timestamp": time.time(), "function_name": "Function", "arguments": "param1, param2, return param1 + param2;", "source_url": dummy_target_url},
        {"timestamp": time.time(), "function_name": "eval", "arguments": "var x = 10; var y = 20; console.log(x+y);", "source_url": "http://some-other-script.js"},
    ]

    dummy_analysis_data = {
        'target_url': dummy_target_url,
        'analysis_timestamp': dummy_timestamp,
        'screenshot_path': dummy_screenshot_path,
        'network_events': dummy_network_events,
        'local_storage': dummy_local_storage,        
        'session_storage': dummy_session_storage,
        'extracted_iocs': dummy_extracted_iocs,
        'cookies': dummy_cookies,
        'dynamic_js_calls': dummy_dynamic_js_calls 
    }

    generator = HTMLReportGenerator()
    report_file = generator.generate_report(dummy_analysis_data) 

    if report_file:
        logger.info(f"Pengujian selesai. Laporan dummy dibuat di: {report_file}")
    else:
        logger.error("Pengujian gagal menghasilkan laporan dummy.")

    if dummy_screenshot_path and os.path.exists(dummy_screenshot_path):
        try:
            os.remove(dummy_screenshot_path)
            logger.info(f"File screenshot dummy dihapus: {dummy_screenshot_path}")
        except Exception as e:
            logger.warning(f"Gagal menghapus file screenshot dummy: {e}")
