# core/report_generator.py
import os
import time
import shutil # Untuk menyalin file screenshot
from jinja2 import Environment, FileSystemLoader, select_autoescape

# Impor konfigurasi dan logger
# Kita asumsikan file ini ada di core/, config.py di root, dan logger_config.py di utils/
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
        logger.debug(f"Jinja2 Environment initialized with template directory: {self.template_dir}")

    def generate_report(self, analysis_data):
        """
        Menghasilkan laporan HTML dari data analisis.
        :param analysis_data: Dictionary yang berisi data untuk laporan, termasuk:
                              'target_url', 'analysis_timestamp', 'screenshot_path',
                              'network_events'.
        :return: Path ke file laporan HTML yang dihasilkan, atau None jika gagal.
        """
        try:
            # --- PERUBAHAN DI SINI ---
            # Langsung gunakan nama file template yang telah kita sepakati
            template_name = "report_template.html" 
            template = self.env.get_template(template_name)
            logger.debug(f"Mencoba memuat template: {template_name}")
            # --- AKHIR PERUBAHAN ---
            
            target_url = analysis_data.get('target_url', 'N/A')
            
            # Persiapkan nama file dan path untuk laporan HTML
            url_slug = target_url.split('//')[-1].split('/')[0].replace('.', '_').replace(':', '_')
            timestamp_str = time.strftime("%Y%m%d-%H%M%S")
            report_filename = f"{url_slug}_{timestamp_str}_{config.DEFAULT_HTML_REPORT_FILENAME}"
            report_filepath = os.path.join(project_root, config.HTML_REPORT_DIR, report_filename)

            # Pastikan direktori laporan HTML ada
            if not os.path.exists(os.path.dirname(report_filepath)):
                os.makedirs(os.path.dirname(report_filepath))
                logger.info(f"Direktori laporan HTML dibuat: {os.path.dirname(report_filepath)}")

            # Tangani screenshot: salin ke direktori laporan dan buat path relatif
            original_screenshot_path = analysis_data.get('screenshot_path')
            screenshot_filename_for_report = None
            if original_screenshot_path and os.path.exists(original_screenshot_path):
                try:
                    # Ambil hanya nama file dari screenshot_path
                    base_screenshot_name = os.path.basename(original_screenshot_path)
                    # Buat nama file screenshot yang unik untuk laporan ini agar tidak bentrok jika ada banyak laporan
                    report_specific_screenshot_name = f"{url_slug}_{timestamp_str}_{base_screenshot_name}"
                    
                    destination_screenshot_path = os.path.join(os.path.dirname(report_filepath), report_specific_screenshot_name)
                    shutil.copy2(original_screenshot_path, destination_screenshot_path)
                    screenshot_filename_for_report = report_specific_screenshot_name # Path relatif untuk tag <img>
                    logger.info(f"Screenshot disalin ke: {destination_screenshot_path}")
                except Exception as e:
                    logger.error(f"Gagal menyalin screenshot {original_screenshot_path} ke direktori laporan: {e}", exc_info=True)
                    # Jika gagal menyalin, screenshot tidak akan ditampilkan di laporan
                    screenshot_filename_for_report = None # Set ke None agar template tahu
            else:
                logger.warning(f"File screenshot asli tidak ditemukan di: {original_screenshot_path} atau path tidak valid.")


            # Data yang akan diteruskan ke template
            template_data = {
                'target_url': target_url,
                'analysis_timestamp': analysis_data.get('analysis_timestamp', time.strftime("%Y-%m-%d %H:%M:%S")),
                'screenshot_path': original_screenshot_path, # Path asli untuk informasi
                'screenshot_filename': screenshot_filename_for_report, # Nama file untuk tag <img>
                'network_events': analysis_data.get('network_events', [])
            }

            rendered_html = template.render(template_data)

            with open(report_filepath, 'w', encoding='utf-8') as f:
                f.write(rendered_html)
            
            logger.info(f"Laporan HTML berhasil dibuat: {report_filepath}")
            return report_filepath

        except jinja2.exceptions.TemplateNotFound as e: # Menangkap error spesifik
            logger.error(f"Template file tidak ditemukan: {e}. Pastikan file '{template_name}' ada di direktori '{self.template_dir}'.", exc_info=True)
            return None
        except Exception as e:
            logger.error(f"Gagal menghasilkan laporan HTML: {e}", exc_info=True)
            return None

# Contoh penggunaan (bisa dipindahkan ke main.py nanti)
if __name__ == '__main__':
    logger.info("Menjalankan report_generator.py secara langsung untuk pengujian.")
    
    # Buat data analisis dummy
    dummy_target_url = "https://kompas.com"
    dummy_timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
    
    # Buat file screenshot dummy untuk pengujian
    dummy_screenshot_dir = os.path.join(project_root, config.SCREENSHOT_DIR)
    if not os.path.exists(dummy_screenshot_dir):
        os.makedirs(dummy_screenshot_dir)
    
    dummy_screenshot_filename = f"example_com_{time.strftime('%Y%m%d-%H%M%S')}_capture.png"
    dummy_screenshot_path = os.path.join(dummy_screenshot_dir, dummy_screenshot_filename)
    try:
        # Buat file gambar kosong sebagai placeholder
        with open(dummy_screenshot_path, 'wb') as f: # 'wb' untuk file biner, meskipun hanya placeholder
            f.write(b"dummy screenshot content") # Konten placeholder byte
        logger.info(f"File screenshot dummy dibuat di: {dummy_screenshot_path}")
    except Exception as e:
        logger.error(f"Tidak dapat membuat file screenshot dummy: {e}")
        dummy_screenshot_path = None


    dummy_network_events = [
        {"timestamp": time.time(), "type": "request", "method": "GET", "url": "https://example.com/", "resource_type": "document", "headers": {}},
        {"timestamp": time.time(), "type": "response", "url": "https://example.com/", "status": 200, "status_text": "OK", "headers": {}},
        {"timestamp": time.time(), "type": "request", "method": "GET", "url": "https://example.com/style.css", "resource_type": "stylesheet", "headers": {}},
        {"timestamp": time.time(), "type": "response", "url": "https://example.com/style.css", "status": 200, "status_text": "OK", "headers": {}},
        {"timestamp": time.time(), "type": "request", "method": "POST", "url": "https://example.com/api/data", "resource_type": "xhr", "headers": {}, "post_data": {"key": "value"}},
        {"timestamp": time.time(), "type": "response", "url": "https://example.com/api/data", "status": 201, "status_text": "Created", "headers": {}},
    ]

    dummy_analysis_data = {
        'target_url': dummy_target_url,
        'analysis_timestamp': dummy_timestamp,
        'screenshot_path': dummy_screenshot_path,
        'network_events': dummy_network_events
    }

    generator = HTMLReportGenerator()
    report_file = generator.generate_report(dummy_analysis_data)

    if report_file:
        logger.info(f"Pengujian selesai. Laporan dummy dibuat di: {report_file}")
        # Coba buka laporan di browser jika memungkinkan (tergantung OS dan konfigurasi)
        # import webbrowser
        # webbrowser.open(f"file://{os.path.abspath(report_file)}")
    else:
        logger.error("Pengujian gagal menghasilkan laporan dummy.")

    # Bersihkan file screenshot dummy jika ada
    if dummy_screenshot_path and os.path.exists(dummy_screenshot_path):
        try:
            os.remove(dummy_screenshot_path)
            logger.info(f"File screenshot dummy dihapus: {dummy_screenshot_path}")
        except Exception as e:
            logger.warning(f"Gagal menghapus file screenshot dummy: {e}")
