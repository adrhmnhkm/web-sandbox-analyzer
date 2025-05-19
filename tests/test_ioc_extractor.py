# tests/test_ioc_extractor.py
import os
import sys
import pytest

# Tambahkan path root proyek ke sys.path agar bisa mengimpor modul dari core
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.insert(0, project_root)

# Impor kelas yang akan diuji
from core.ioc_extractor import IOCExtractor, POTENTIALLY_HARMFUL_EXTENSIONS

# --- Tes untuk metode helper di IOCExtractor ---

# Buat instance IOCExtractor untuk mengakses metode helper
dummy_extractor = IOCExtractor(network_events=None)

# Tes untuk _get_domain_from_url
@pytest.mark.parametrize("url_input, expected_domain", [
    ("http://example.com/path", "example.com"),
    ("https://www.sub.example.co.uk/page.html?query=1", "www.sub.example.co.uk"),
    ("ftp://files.example.org:21/files", "files.example.org"),
    ("http://192.168.1.1/admin", "192.168.1.1"),
    ("http://localhost:8000", "localhost"),
    ("http://[::1]/ipv6", "::1"), # PERUBAHAN: Ekspektasi diubah dari "[::1]" menjadi "::1"
    ("example.com/no-scheme", None), 
    ("justadomain.com", None),       
    ("", None), 
    (None, None), 
    ("htp://malformed.url", "malformed.url") 
])
def test_get_domain_from_url(url_input, expected_domain):
    """Tes ekstraksi domain dari berbagai format URL."""
    assert dummy_extractor._get_domain_from_url(url_input) == expected_domain

# Tes untuk _check_harmful_extension
@pytest.mark.parametrize("url_input, expected_result, expected_ext", [
    ("http://example.com/file.exe", True, ".exe"),
    ("http://example.com/document.docm", True, ".docm"),
    ("http://example.com/archive.zip", True, ".zip"),
    ("http://example.com/image.png", False, None),
    ("http://example.com/script.js", False, None), 
    ("http://example.com/path/to/file.EXE", True, ".exe"), 
    ("http://example.com/no_extension", False, None),
    ("http://example.com/evil.JsOn.Zip", True, ".zip"), 
    ("http://example.com/file.with.dots.exe", True, ".exe"),
    ("http://example.com/file%20with%20spaces.bat", True, ".bat"), 
    ("", False, None),
    (None, False, None)
])
def test_check_harmful_extension(url_input, expected_result, expected_ext):
    is_harmful, ext = dummy_extractor._check_harmful_extension(url_input)
    assert is_harmful == expected_result
    assert ext == expected_ext

# Tes untuk _is_ip_address
@pytest.mark.parametrize("input_str, expected_result", [
    ("192.168.1.1", True),
    ("10.0.0.255", True),
    ("0.0.0.0", True),
    ("255.255.255.255", True),
    ("1.2.3.4.5", False), 
    ("256.1.1.1", False), 
    ("192.168.1", False), 
    ("example.com", False),
    ("localhost", False),
    ("123.45.67.a", False), 
    ("", False),
    (None, False),
    ("::1", False), 
    ("[::1]", False) 
])
def test_is_ip_address(input_str, expected_result):
    assert dummy_extractor._is_ip_address(input_str) == expected_result

# --- Tes untuk metode extract() ---
def test_extract_no_events():
    """Tes extract() dengan network_events kosong."""
    extractor = IOCExtractor(network_events=[])
    iocs = extractor.extract()
    assert iocs["unique_domains"] == [] 
    assert iocs["potentially_harmful_urls"] == []
    assert iocs["post_requests"] == []
    assert iocs["direct_ip_requests"] == []

def test_extract_with_sample_events():
    """Tes extract() dengan beberapa event jaringan sampel."""
    sample_events = [
        {"timestamp": 123, "type": "request", "method": "GET", "url": "http://example.com/index.html"},
        {"timestamp": 124, "type": "request", "method": "GET", "url": "http://ads.example.com/ad.js"},
        {"timestamp": 125, "type": "request", "method": "GET", "url": "http://malware-site.net/payload.exe"},
        {"timestamp": 126, "type": "request", "method": "POST", "url": "http://example.com/api/data", "post_data": {"key": "value"}},
        {"timestamp": 127, "type": "request", "method": "GET", "url": "http://123.45.67.89/beacon.php"},
        {"timestamp": 128, "type": "request", "method": "GET", "url": "http://example.com/another.html"}, 
        {"timestamp": 129, "type": "response", "url": "http://example.com/index.html", "status": 200}, 
        {"timestamp": 130, "type": "request", "method": "GET", "url": "http://[::1]/ipv6_resource"}, 
    ]
    extractor = IOCExtractor(network_events=sample_events)
    iocs = extractor.extract()

    # PERUBAHAN: Ekspektasi untuk IPv6 diubah menjadi "::1" (tanpa kurung siku)
    assert iocs["unique_domains"] == sorted(["123.45.67.89", "::1", "ads.example.com", "example.com", "malware-site.net"])
    
    assert len(iocs["potentially_harmful_urls"]) == 1
    assert iocs["potentially_harmful_urls"][0]["url"] == "http://malware-site.net/payload.exe"
    assert iocs["potentially_harmful_urls"][0]["extension"] == ".exe"

    assert len(iocs["post_requests"]) == 1
    assert iocs["post_requests"][0]["url"] == "http://example.com/api/data"
    assert iocs["post_requests"][0]["post_data_summary"] == "Available"

    assert len(iocs["direct_ip_requests"]) == 1
    assert iocs["direct_ip_requests"][0]["url"] == "http://123.45.67.89/beacon.php"
