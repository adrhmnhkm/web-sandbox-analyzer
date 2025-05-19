# tests/test_threat_intelligence.py
import os
import sys
import pytest
from unittest import mock # Pustaka standar untuk mocking

# Tambahkan path root proyek ke sys.path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.insert(0, project_root)

# Impor kelas yang akan diuji dan konfigurasi
from core.threat_intelligence import VirusTotalAnalyzer, VIRUSTOTAL_API_URL_DOMAIN_REPORT
import config # Untuk mengakses config.VIRUSTOTAL_API_KEY saat inisialisasi

# --- Tes untuk VirusTotalAnalyzer ---

# Contoh respons sukses dari VirusTotal API (domain bersih)
MOCK_VT_SUCCESS_CLEAN = {
    "data": {
        "attributes": {
            "last_analysis_stats": {
                "harmless": 65,
                "malicious": 0,
                "suspicious": 0,
                "undetected": 5,
                "timeout": 0
            },
            "total_votes": {"harmless": 10, "malicious": 0},
            "last_analysis_date": 1678886400, # Contoh timestamp Unix
            "reputation": 0
        }
    }
}

# Contoh respons sukses dari VirusTotal API (domain berbahaya)
MOCK_VT_SUCCESS_MALICIOUS = {
    "data": {
        "attributes": {
            "last_analysis_stats": {
                "harmless": 2,
                "malicious": 55,
                "suspicious": 3,
                "undetected": 10,
                "timeout": 0
            },
            "total_votes": {"harmless": 1, "malicious": 25},
            "last_analysis_date": 1678880000,
            "reputation": -30
        }
    }
}

# Contoh respons error dari VirusTotal API (misalnya, Not Found atau API Key Invalid)
class MockResponse:
    def __init__(self, json_data, status_code):
        self.json_data = json_data
        self.status_code = status_code

    def json(self):
        return self.json_data

    def raise_for_status(self):
        if self.status_code >= 400:
            # Import HTTPError di sini untuk menghindari circular import jika requests di-mock secara global
            from requests.exceptions import HTTPError 
            http_error_msg = f"{self.status_code} Client Error"
            raise HTTPError(http_error_msg, response=self)


@pytest.fixture
def vt_analyzer_with_key():
    """Fixture untuk membuat instance VirusTotalAnalyzer dengan API key dummy."""
    # Simpan API key asli jika ada, lalu set dummy key untuk tes
    original_api_key = config.VIRUSTOTAL_API_KEY
    config.VIRUSTOTAL_API_KEY = "dummy_vt_api_key_for_testing"
    analyzer = VirusTotalAnalyzer()
    yield analyzer
    # Kembalikan API key asli setelah tes selesai
    config.VIRUSTOTAL_API_KEY = original_api_key

@pytest.fixture
def vt_analyzer_no_key():
    """Fixture untuk membuat instance VirusTotalAnalyzer tanpa API key."""
    original_api_key = config.VIRUSTOTAL_API_KEY
    config.VIRUSTOTAL_API_KEY = "" # Set API key kosong
    analyzer = VirusTotalAnalyzer()
    yield analyzer
    config.VIRUSTOTAL_API_KEY = original_api_key


def test_get_domain_report_no_api_key(vt_analyzer_no_key):
    """Tes get_domain_report ketika API key tidak dikonfigurasi."""
    report = vt_analyzer_no_key.get_domain_report("example.com")
    assert report is None

@mock.patch('core.threat_intelligence.requests.get') # Mock object requests.get di dalam modul threat_intelligence
def test_get_domain_report_success_clean_domain(mock_requests_get, vt_analyzer_with_key):
    """Tes get_domain_report untuk domain bersih."""
    mock_requests_get.return_value = MockResponse(MOCK_VT_SUCCESS_CLEAN, 200)
    
    domain = "cleandomain.com"
    report = vt_analyzer_with_key.get_domain_report(domain)

    assert report is not None
    assert report["domain"] == domain
    assert report["malicious"] == 0
    assert report["suspicious"] == 0
    assert report["harmless"] == 65
    assert report["link_to_report"] == f"https://www.virustotal.com/gui/domain/{domain}/detection"
    mock_requests_get.assert_called_once_with(
        f"{VIRUSTOTAL_API_URL_DOMAIN_REPORT}{domain}",
        headers={"x-apikey": "dummy_vt_api_key_for_testing", "accept": "application/json"}
    )

@mock.patch('core.threat_intelligence.requests.get')
def test_get_domain_report_success_malicious_domain(mock_requests_get, vt_analyzer_with_key):
    """Tes get_domain_report untuk domain berbahaya."""
    mock_requests_get.return_value = MockResponse(MOCK_VT_SUCCESS_MALICIOUS, 200)
    
    domain = "maliciousdomain.com"
    report = vt_analyzer_with_key.get_domain_report(domain)

    assert report is not None
    assert report["domain"] == domain
    assert report["malicious"] == 55
    assert report["suspicious"] == 3
    assert report["reputation"] == -30
    mock_requests_get.assert_called_once_with(
        f"{VIRUSTOTAL_API_URL_DOMAIN_REPORT}{domain}",
        headers={"x-apikey": "dummy_vt_api_key_for_testing", "accept": "application/json"}
    )

@mock.patch('core.threat_intelligence.requests.get')
def test_get_domain_report_api_error_401(mock_requests_get, vt_analyzer_with_key):
    """Tes get_domain_report ketika API mengembalikan error 401 (Unauthorized)."""
    mock_requests_get.return_value = MockResponse({"error": {"code": "AuthenticationRequiredError", "message": "API key invalid"}}, 401)
    
    domain = "anydomain.com"
    report = vt_analyzer_with_key.get_domain_report(domain)

    assert report is not None
    assert report["domain"] == domain
    assert report["error"] == "HTTP Error: 401"
    assert "API key invalid" in report["message"] # Pesan error bisa bervariasi

@mock.patch('core.threat_intelligence.requests.get')
def test_get_domain_report_api_error_429(mock_requests_get, vt_analyzer_with_key):
    """Tes get_domain_report ketika API mengembalikan error 429 (Too Many Requests)."""
    mock_requests_get.return_value = MockResponse({"error": {"code": "QuotaExceededError", "message": "Quota exceeded"}}, 429)
    
    domain = "anydomain.com"
    report = vt_analyzer_with_key.get_domain_report(domain)

    assert report is not None
    assert report["domain"] == domain
    assert report["error"] == "HTTP Error: 429"
    assert "Quota exceeded" in report["message"]

@mock.patch('core.threat_intelligence.requests.get')
def test_get_domain_report_connection_error(mock_requests_get, vt_analyzer_with_key):
    """Tes get_domain_report ketika terjadi error koneksi."""
    # Import RequestException di sini untuk digunakan oleh side_effect
    from requests.exceptions import RequestException
    mock_requests_get.side_effect = RequestException("Koneksi gagal")
    
    domain = "anydomain.com"
    report = vt_analyzer_with_key.get_domain_report(domain)

    assert report is not None
    assert report["domain"] == domain
    assert report["error"] == "Connection Error"
    assert "Koneksi gagal" in report["message"]

@mock.patch('core.threat_intelligence.requests.get')
def test_get_domain_report_unexpected_json_structure(mock_requests_get, vt_analyzer_with_key):
    """Tes get_domain_report jika struktur JSON respons tidak seperti yang diharapkan."""
    mock_requests_get.return_value = MockResponse({"unexpected_key": "unexpected_value"}, 200)
    
    domain = "anydomain.com"
    report = vt_analyzer_with_key.get_domain_report(domain)

    assert report is not None
    assert report["domain"] == domain
    # Karena struktur tidak sesuai, beberapa field mungkin default ke 0 atau None
    assert report["malicious"] == 0 
    assert report["total_engines"] == 0 # Karena last_analysis_stats akan kosong
    # Anda bisa menambahkan assert lain untuk memeriksa bagaimana error parsing ditangani
    # atau apakah ia mengembalikan error spesifik jika parsing gagal total.
    # Saat ini, ia akan mencoba mengambil field dan default ke 0/None jika tidak ada.
