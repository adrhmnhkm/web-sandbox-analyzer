# core/ioc_extractor.py
import os
import re
import time
from urllib.parse import urlparse, unquote

# Impor konfigurasi dan logger
import sys
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(current_dir)
if project_root not in sys.path:
    sys.path.insert(0, project_root)

import config # Meskipun tidak digunakan langsung di sini, mungkin berguna untuk konfigurasi IOC di masa depan
from utils.logger_config import setup_logger

logger = setup_logger(__name__, config.LOG_LEVEL, config.LOG_FILE)

# Daftar ekstensi file yang berpotensi berbahaya atau menarik untuk diinvestigasi
POTENTIALLY_HARMFUL_EXTENSIONS = [
    '.exe', '.dll', '.msi', '.bat', '.sh', '.jar', '.ps1', '.vbs',  # Eksekusi
    '.zip', '.rar', '.7z', '.tar', '.gz', '.iso', # Arsip
    '.docm', '.xlsm', '.pptm', '.dotm', # Dokumen Office dengan makro
    '.scr', # Screensaver, sering disalahgunakan
    # '.js', # Bisa ditambahkan, tapi mungkin terlalu banyak noise jika tidak difilter berdasarkan domain
    # '.pdf', # PDF juga bisa membawa exploit, tapi perlu analisis lebih dalam
]

class IOCExtractor:
    def __init__(self, network_events):
        """
        Inisialisasi IOCExtractor.
        :param network_events: List dari dictionary event jaringan.
        """
        self.network_events = network_events if network_events else []
        self.extracted_iocs = {
            "unique_domains": set(),
            "potentially_harmful_urls": [],
            "post_requests": [],
            "direct_ip_requests": [],
            # "contacted_ips": set(), # Untuk masa depan jika ada resolusi DNS
        }
        logger.debug("IOCExtractor diinisialisasi.")

    def _get_domain_from_url(self, url_string):
        """Helper untuk mendapatkan domain dari URL."""
        try:
            parsed_url = urlparse(url_string)
            return parsed_url.hostname
        except Exception as e:
            logger.warning(f"Tidak dapat mem-parsing domain dari URL: {url_string} - Error: {e}")
            return None

    def _check_harmful_extension(self, url_string):
        """Helper untuk memeriksa ekstensi file berbahaya."""
        try:
            # Dekode URL untuk menangani karakter yang di-encode seperti %20
            decoded_url = unquote(url_string)
            path = urlparse(decoded_url).path
            filename, ext = os.path.splitext(path)
            if ext.lower() in POTENTIALLY_HARMFUL_EXTENSIONS:
                return True, ext.lower()
        except Exception as e:
            logger.warning(f"Error saat memeriksa ekstensi berbahaya untuk URL: {url_string} - Error: {e}")
        return False, None

    def _is_ip_address(self, hostname_or_ip):
        """Helper untuk memeriksa apakah string adalah alamat IP v4."""
        if not hostname_or_ip:
            return False
        # Pola regex sederhana untuk IPv4. Untuk IPv6 atau validasi lebih ketat, pustaka khusus mungkin diperlukan.
        ip_pattern = re.compile(r"^(?:[0-9]{1,3}\.){3}[0-9]{1,3}$")
        return bool(ip_pattern.match(hostname_or_ip))

    def extract(self):
        """
        Mengekstrak IOC dari network_events.
        :return: Dictionary yang berisi IOC yang diekstrak.
        """
        if not self.network_events:
            logger.info("Tidak ada event jaringan untuk diekstrak IOC-nya.")
            return self.extracted_iocs

        logger.info(f"Memulai ekstraksi IOC dari {len(self.network_events)} event jaringan...")

        for event in self.network_events:
            if event.get("type") == "request": # Kita fokus pada request untuk IOC
                url = event.get("url")
                method = event.get("method", "").upper()

                if not url:
                    continue

                # 1. Ekstrak Domain Unik
                domain = self._get_domain_from_url(url)
                if domain:
                    self.extracted_iocs["unique_domains"].add(domain)

                    # 4. Cek Permintaan ke Alamat IP Langsung
                    if self._is_ip_address(domain):
                        self.extracted_iocs["direct_ip_requests"].append({
                            "url": url,
                            "method": method,
                            "timestamp": event.get("timestamp")
                        })
                
                # 2. Cek URL dengan Ekstensi Berbahaya
                is_harmful, ext = self._check_harmful_extension(url)
                if is_harmful:
                    self.extracted_iocs["potentially_harmful_urls"].append({
                        "url": url,
                        "extension": ext,
                        "method": method,
                        "timestamp": event.get("timestamp")
                    })

                # 3. Catat Permintaan POST
                if method == "POST":
                    self.extracted_iocs["post_requests"].append({
                        "url": url,
                        "timestamp": event.get("timestamp"),
                        "post_data_summary": "Available" if event.get("post_data") or event.get("post_data_format") else "Not available"
                        # Di masa depan, kita bisa tambahkan ringkasan atau hash dari post_data
                    })
        
        # Konversi set ke list untuk konsistensi output (misalnya, untuk JSON serialization)
        self.extracted_iocs["unique_domains"] = sorted(list(self.extracted_iocs["unique_domains"]))
        
        logger.info(f"Ekstraksi IOC selesai. Ditemukan {len(self.extracted_iocs['unique_domains'])} domain unik.")
        logger.info(f"Ditemukan {len(self.extracted_iocs['potentially_harmful_urls'])} URL berpotensi berbahaya.")
        logger.info(f"Ditemukan {len(self.extracted_iocs['post_requests'])} permintaan POST.")
        logger.info(f"Ditemukan {len(self.extracted_iocs['direct_ip_requests'])} permintaan ke IP langsung.")
        
        return self.extracted_iocs

# Contoh penggunaan (hanya untuk pengujian modul ini secara terpisah)
if __name__ == '__main__':
    logger.info("Menjalankan ioc_extractor.py secara langsung untuk pengujian.")
    
    dummy_network_events_for_ioc = [
        {"timestamp": time.time(), "type": "request", "method": "GET", "url": "http://example.com/index.html", "resource_type": "document"},
        {"timestamp": time.time(), "type": "request", "method": "GET", "url": "http://example.com/script.js", "resource_type": "script"},
        {"timestamp": time.time(), "type": "request", "method": "GET", "url": "http://another-domain.com/malware.exe", "resource_type": "other"},
        {"timestamp": time.time(), "type": "request", "method": "POST", "url": "http://example.com/api/submit", "resource_type": "xhr", "post_data": {"user": "test"}},
        {"timestamp": time.time(), "type": "request", "method": "GET", "url": "https://evil-site.net/payload.zip?key=123", "resource_type": "other"},
        {"timestamp": time.time(), "type": "request", "method": "GET", "url": "http://192.168.1.100/config.php", "resource_type": "other"},
        {"timestamp": time.time(), "type": "request", "method": "GET", "url": "http://example.com/legit.pdf", "resource_type": "other"}, # Tidak masuk harmful default
        {"timestamp": time.time(), "type": "request", "method": "GET", "url": "http://example.com/data.docm", "resource_type": "other"},
        {"timestamp": time.time(), "type": "request", "method": "GET", "url": "http://example.com/path with spaces/file.dll", "resource_type": "other"},
    ]

    extractor = IOCExtractor(dummy_network_events_for_ioc)
    iocs = extractor.extract()

    logger.info("\n--- Hasil Ekstraksi IOC (Dummy) ---")
    logger.info(f"Domain Unik: {iocs['unique_domains']}")
    logger.info(f"URL Berpotensi Berbahaya: {iocs['potentially_harmful_urls']}")
    logger.info(f"Permintaan POST: {iocs['post_requests']}")
    logger.info(f"Permintaan ke IP Langsung: {iocs['direct_ip_requests']}")
    logger.info("-----------------------------------\n")
    
    # Tes dengan network_events kosong
    logger.info("Menguji dengan network_events kosong:")
    empty_extractor = IOCExtractor([])
    empty_iocs = empty_extractor.extract()
    logger.info(f"Domain Unik (kosong): {empty_iocs['unique_domains']}")

    logger.info("Pengujian ioc_extractor.py selesai.")
