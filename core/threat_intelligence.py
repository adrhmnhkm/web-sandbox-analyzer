# core/threat_intelligence.py
import requests
import time
import os
import json # Untuk json.JSONDecodeError jika diperlukan

# Impor konfigurasi dan logger
import sys
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(current_dir)
if project_root not in sys.path:
    sys.path.insert(0, project_root)

import config
from utils.logger_config import setup_logger

logger = setup_logger(__name__, config.LOG_LEVEL, config.LOG_FILE)

VIRUSTOTAL_API_URL_DOMAIN_REPORT = "https://www.virustotal.com/api/v3/domains/"

class VirusTotalAnalyzer:
    def __init__(self, api_key=None):
        """
        Inisialisasi VirusTotalAnalyzer.
        :param api_key: API Key VirusTotal. Jika None, akan diambil dari config.py.
        """
        self.api_key = api_key if api_key else config.VIRUSTOTAL_API_KEY
        if not self.api_key:
            logger.warning("API Key VirusTotal tidak dikonfigurasi. Fitur Threat Intelligence tidak akan aktif.")
        self.headers = {
            "x-apikey": self.api_key,
            "accept": "application/json"
        }

    def get_domain_report(self, domain):
        """
        Mengambil laporan domain dari VirusTotal.
        :param domain: Domain yang akan diperiksa.
        :return: Dictionary berisi ringkasan laporan, atau None jika gagal atau API key tidak ada.
        """
        if not self.api_key:
            logger.debug(f"Pemeriksaan VirusTotal untuk domain '{domain}' dilewati karena API key tidak ada.")
            return None

        url = f"{VIRUSTOTAL_API_URL_DOMAIN_REPORT}{domain}"
        logger.info(f"Meminta laporan VirusTotal untuk domain: {domain}")
        
        try:
            response = requests.get(url, headers=self.headers)
            response.raise_for_status()  # Akan melempar HTTPError jika status code 4XX/5XX

            data = response.json()
            attributes = data.get("data", {}).get("attributes", {})
            
            last_analysis_stats = attributes.get("last_analysis_stats", {})
            total_votes = attributes.get("total_votes", {})
            
            report_summary = {
                "domain": domain,
                "malicious": last_analysis_stats.get("malicious", 0),
                "suspicious": last_analysis_stats.get("suspicious", 0),
                "harmless": last_analysis_stats.get("harmless", 0),
                "undetected": last_analysis_stats.get("undetected", 0),
                "total_engines": sum(last_analysis_stats.values()), # Pastikan semua nilai adalah angka
                "total_votes_harmless": total_votes.get("harmless", 0),
                "total_votes_malicious": total_votes.get("malicious", 0),
                "last_analysis_date": attributes.get("last_analysis_date"), 
                "reputation": attributes.get("reputation"),
                "link_to_report": f"https://www.virustotal.com/gui/domain/{domain}/detection"
            }
            logger.info(f"Laporan VirusTotal untuk '{domain}': Malicious={report_summary['malicious']}, Suspicious={report_summary['suspicious']}")
            return report_summary

        except requests.exceptions.HTTPError as http_err:
            # --- PERUBAHAN DI SINI: Mencoba mengambil pesan error dari JSON respons ---
            error_message = str(http_err) # Default message
            status_code = http_err.response.status_code if http_err.response is not None else "N/A"
            
            try:
                if http_err.response is not None:
                    error_json = http_err.response.json()
                    if isinstance(error_json, dict) and "error" in error_json:
                        if isinstance(error_json["error"], dict) and "message" in error_json["error"]:
                            error_message = error_json["error"]["message"]
                        elif isinstance(error_json["error"], str): 
                            error_message = error_json["error"]
            except json.JSONDecodeError: # Respons bukan JSON valid
                logger.warning(f"Respons error dari VirusTotal untuk '{domain}' bukan JSON valid.")
            except Exception as e_parse: # Error lain saat parsing
                logger.warning(f"Error saat parsing JSON respons error dari VirusTotal untuk '{domain}': {e_parse}")
            # --- AKHIR PERUBAHAN ---

            if status_code == 401: 
                logger.error(f"Error 401: API Key VirusTotal tidak valid atau tidak memiliki izin. Pesan: {error_message}")
            elif status_code == 429: 
                logger.warning(f"Error 429: Batas permintaan API VirusTotal terlampaui untuk domain '{domain}'. Pesan: {error_message}")
            else:
                logger.error(f"HTTP error saat meminta laporan VirusTotal untuk '{domain}': {http_err} - Status: {status_code}, Pesan: {error_message}")
            
            return {"domain": domain, "error": f"HTTP Error: {status_code}", "message": error_message}
        
        except requests.exceptions.RequestException as req_err:
            logger.error(f"Error koneksi saat meminta laporan VirusTotal untuk '{domain}': {req_err}")
            return {"domain": domain, "error": "Connection Error", "message": str(req_err)}
        except Exception as e:
            logger.error(f"Error tak terduga saat memproses laporan VirusTotal untuk '{domain}': {e}", exc_info=True)
            return {"domain": domain, "error": "Processing Error", "message": str(e)}

# ... (Bagian if __name__ == '__main__': tetap sama) ...
if __name__ == '__main__':
    logger.info("Menjalankan threat_intelligence.py secara langsung untuk pengujian.")
    
    if not config.VIRUSTOTAL_API_KEY:
        logger.warning("VIRUSTOTAL_API_KEY tidak diatur di config.py. Pengujian akan dilewati.")
    else:
        vt_analyzer = VirusTotalAnalyzer()
        
        test_domains = ["google.com", "thisdomainprobablydoesnotexist12345.com", "kompas.com"] 
        
        for domain_to_test in test_domains:
            report = vt_analyzer.get_domain_report(domain_to_test)
            if report:
                logger.info(f"Hasil untuk {domain_to_test}: {report}")
            else:
                logger.info(f"Tidak ada laporan untuk {domain_to_test} (mungkin karena API key tidak ada).")
            
            if domain_to_test != test_domains[-1]: 
                logger.info(f"Menunggu {config.VIRUSTOTAL_REQUEST_DELAY} detik sebelum permintaan berikutnya...")
                time.sleep(config.VIRUSTOTAL_REQUEST_DELAY)
                
    logger.info("Pengujian threat_intelligence.py selesai.")
