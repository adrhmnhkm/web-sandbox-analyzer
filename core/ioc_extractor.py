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

import config 
from utils.logger_config import setup_logger

logger = setup_logger(__name__, config.LOG_LEVEL, config.LOG_FILE)

POTENTIALLY_HARMFUL_EXTENSIONS = [
    '.exe', '.dll', '.msi', '.bat', '.sh', '.jar', '.ps1', '.vbs',
    '.zip', '.rar', '.7z', '.tar', '.gz', '.iso', 
    '.docm', '.xlsm', '.pptm', '.dotm', 
    '.scr', 
]

class IOCExtractor:
    def __init__(self, network_events):
        self.network_events = network_events if network_events else []
        self.extracted_iocs = {
            "unique_domains": set(),
            "potentially_harmful_urls": [],
            "post_requests": [],
            "direct_ip_requests": [],
        }
        logger.debug("IOCExtractor diinisialisasi.")

    def _get_domain_from_url(self, url_string):
        try:
            if not url_string: # Tambahkan pengecekan untuk input None atau string kosong
                return None
            parsed_url = urlparse(url_string)
            # hostname akan mengembalikan None jika tidak ada, atau string domain/IP
            # Untuk IPv6, ia akan mengembalikan '[::1]' termasuk kurung siku
            return parsed_url.hostname 
        except Exception as e:
            logger.warning(f"Tidak dapat mem-parsing domain dari URL: {url_string} - Error: {e}")
            return None

    def _check_harmful_extension(self, url_string):
        try:
            if not url_string: return False, None # Tambah pengecekan
            decoded_url = unquote(url_string)
            path = urlparse(decoded_url).path
            _, ext = os.path.splitext(path) # Ambil ekstensi
            if ext.lower() in POTENTIALLY_HARMFUL_EXTENSIONS:
                return True, ext.lower()
        except Exception as e:
            logger.warning(f"Error saat memeriksa ekstensi berbahaya untuk URL: {url_string} - Error: {e}")
        return False, None

    def _is_ip_address(self, hostname_or_ip):
        if not hostname_or_ip:
            return False
        # Pola regex untuk IPv4 yang juga memeriksa rentang nilai (0-255)
        # Ini lebih kompleks tapi lebih akurat.
        # Oktet: (25[0-5]|2[0-4][0-9]|1[0-9]{2}|[1-9]?[0-9])
        octet_pattern = r"(25[0-5]|2[0-4][0-9]|1[0-9]{2}|[1-9]?[0-9])"
        ip_pattern = re.compile(rf"^{octet_pattern}\.{octet_pattern}\.{octet_pattern}\.{octet_pattern}$")
        
        # Untuk IPv6, validasinya jauh lebih kompleks dan biasanya menggunakan pustaka khusus.
        # Untuk saat ini, kita fokus pada IPv4. Jika hostname_or_ip adalah IPv6 valid (mis. '[::1]'),
        # regex ini tidak akan cocok, yang mana benar karena ini bukan IPv4.
        return bool(ip_pattern.match(hostname_or_ip))

    def extract(self):
        if not self.network_events:
            logger.info("Tidak ada event jaringan untuk diekstrak IOC-nya.")
            # Pastikan unique_domains selalu list
            self.extracted_iocs["unique_domains"] = []
            return self.extracted_iocs

        logger.info(f"Memulai ekstraksi IOC dari {len(self.network_events)} event jaringan...")

        for event in self.network_events:
            if event.get("type") == "request": 
                url = event.get("url")
                method = event.get("method", "").upper()

                if not url:
                    continue

                domain = self._get_domain_from_url(url)
                if domain:
                    self.extracted_iocs["unique_domains"].add(domain)
                    if self._is_ip_address(domain): # Hanya cek jika domain itu sendiri adalah IP
                        self.extracted_iocs["direct_ip_requests"].append({
                            "url": url,
                            "method": method,
                            "timestamp": event.get("timestamp")
                        })
                
                is_harmful, ext = self._check_harmful_extension(url)
                if is_harmful:
                    self.extracted_iocs["potentially_harmful_urls"].append({
                        "url": url,
                        "extension": ext,
                        "method": method,
                        "timestamp": event.get("timestamp")
                    })

                if method == "POST":
                    self.extracted_iocs["post_requests"].append({
                        "url": url,
                        "timestamp": event.get("timestamp"),
                        "post_data_summary": "Available" if event.get("post_data") or event.get("post_data_format") else "Not available"
                    })
        
        self.extracted_iocs["unique_domains"] = sorted(list(self.extracted_iocs["unique_domains"]))
        
        logger.info(f"Ekstraksi IOC selesai. Ditemukan {len(self.extracted_iocs['unique_domains'])} domain unik.")
        logger.info(f"Ditemukan {len(self.extracted_iocs['potentially_harmful_urls'])} URL berpotensi berbahaya.")
        logger.info(f"Ditemukan {len(self.extracted_iocs['post_requests'])} permintaan POST.")
        logger.info(f"Ditemukan {len(self.extracted_iocs['direct_ip_requests'])} permintaan ke IP langsung.")
        
        return self.extracted_iocs

# ... (Bagian if __name__ == '__main__': tetap sama) ...
if __name__ == '__main__':
    logger.info("Menjalankan ioc_extractor.py secara langsung untuk pengujian.")
    
    dummy_network_events_for_ioc = [
        {"timestamp": time.time(), "type": "request", "method": "GET", "url": "http://example.com/index.html", "resource_type": "document"},
        {"timestamp": time.time(), "type": "request", "method": "GET", "url": "http://example.com/script.js", "resource_type": "script"},
        {"timestamp": time.time(), "type": "request", "method": "GET", "url": "http://another-domain.com/malware.exe", "resource_type": "other"},
        {"timestamp": time.time(), "type": "request", "method": "POST", "url": "http://example.com/api/submit", "resource_type": "xhr", "post_data": {"user": "test"}},
        {"timestamp": time.time(), "type": "request", "method": "GET", "url": "https://evil-site.net/payload.zip?key=123", "resource_type": "other"},
        {"timestamp": time.time(), "type": "request", "method": "GET", "url": "http://192.168.1.100/config.php", "resource_type": "other"},
        {"timestamp": time.time(), "type": "request", "method": "GET", "url": "http://example.com/legit.pdf", "resource_type": "other"}, 
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
    
    logger.info("Menguji dengan network_events kosong:")
    empty_extractor = IOCExtractor([])
    empty_iocs = empty_extractor.extract()
    logger.info(f"Domain Unik (kosong): {empty_iocs['unique_domains']}")

    logger.info("Pengujian ioc_extractor.py selesai.")
