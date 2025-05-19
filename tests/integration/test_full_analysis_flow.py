# tests/integration/test_full_analysis_flow.py
import os
import sys
import pytest
import json
import time
import shutil # Untuk membersihkan direktori output jika perlu

# Tambahkan path root proyek ke sys.path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
sys.path.insert(0, project_root)

# Impor fungsi inti dari main.py dan konfigurasi
from main import run_analysis_pipeline, ensure_url_scheme # Pastikan ini bisa diimpor
import config

# Path ke halaman HTML uji lokal kita
TEST_PAGE_FILENAME = "test_page_for_integration.html"
TEST_PAGE_DIR = os.path.join(project_root, "tests", "integration")
TEST_PAGE_PATH = os.path.join(TEST_PAGE_DIR, TEST_PAGE_FILENAME)

@pytest.fixture(scope="module", autouse=True)
def create_test_html_page():
    """
    Fixture untuk memastikan file HTML uji ada sebelum tes dijalankan.
    scope="module" berarti hanya dijalankan sekali per modul tes.
    autouse=True berarti akan otomatis digunakan tanpa perlu dipanggil di tes.
    """
    if not os.path.exists(TEST_PAGE_DIR):
        os.makedirs(TEST_PAGE_DIR)
    
    html_content = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>Integration Test Page</title>
    <script>
        function setupTestData() {
            localStorage.setItem('integration_test_local_key', 'local_value_123');
            localStorage.setItem('another_local', 'some data');
            sessionStorage.setItem('integration_test_session_key', 'session_value_456');
            try {
                eval("var integration_eval_var = 'eval_executed_successfully'; console.log('Integration test eval: ' + integration_eval_var);");
            } catch (e) { console.error('Error during eval in test page:', e); }
            console.log("Test page setup complete.");
        }
    </script>
</head>
<body onload="setupTestData()">
    <h1>Integration Test Page</h1>
    <p>This page is used for integration testing of the Web Sandbox Analyzer.</p>
</body>
</html>
    """
    with open(TEST_PAGE_PATH, "w") as f:
        f.write(html_content)
    yield # Tes berjalan di sini
    # Cleanup setelah semua tes di modul selesai (opsional, bisa juga dibiarkan)
    # if os.path.exists(TEST_PAGE_PATH):
    #     os.remove(TEST_PAGE_PATH)

@pytest.fixture
def default_analysis_params():
    """Menyediakan parameter analisis default untuk tes integrasi."""
    # Pastikan URL file lokal diformat dengan benar
    file_url = f"file://{os.path.abspath(TEST_PAGE_PATH)}"
    return {
        "target_url": file_url,
        "browser_type": config.BROWSER_TYPE, # Gunakan dari config
        "headless_mode": True, # Jalankan headless agar tidak mengganggu
        "threat_intel_enabled": False, # Nonaktifkan VT untuk tes integrasi cepat
        "project_root_path": project_root
    }

def clear_output_directory(output_subdir):
    """Membersihkan subdirektori output tertentu sebelum tes."""
    dir_to_clear = os.path.join(project_root, "output", output_subdir)
    if os.path.exists(dir_to_clear):
        for filename in os.listdir(dir_to_clear):
            file_path = os.path.join(dir_to_clear, filename)
            try:
                if os.path.isfile(file_path) or os.path.islink(file_path):
                    os.unlink(file_path)
                elif os.path.isdir(file_path):
                    shutil.rmtree(file_path)
            except Exception as e:
                print(f"Gagal menghapus {file_path}. Penyebab: {e}")

@pytest.fixture(autouse=True)
def cleanup_output_dirs_before_each_test():
    """Fixture untuk membersihkan direktori output sebelum setiap tes."""
    clear_output_directory(os.path.basename(config.HTML_REPORT_DIR))
    clear_output_directory(os.path.basename(config.SCREENSHOT_DIR))
    clear_output_directory(os.path.basename(config.NETWORK_LOG_DIR))
    yield # Tes berjalan di sini

def test_full_analysis_pipeline_generates_outputs(default_analysis_params):
    """
    Tes integrasi untuk memastikan alur analisis utama menghasilkan file output.
    """
    results = run_analysis_pipeline(**default_analysis_params)

    assert results is not None, "Hasil analisis tidak boleh None"
    
    # 1. Cek apakah file laporan HTML dibuat
    html_report_path = results.get("html_report_path")
    assert html_report_path is not None, "Path laporan HTML tidak boleh None"
    assert os.path.exists(html_report_path), f"File laporan HTML tidak ditemukan di: {html_report_path}"
    assert os.path.basename(html_report_path).endswith(config.DEFAULT_HTML_REPORT_FILENAME)

    # 2. Cek apakah file screenshot dibuat (jika screenshot_path tidak None)
    screenshot_path = results.get("screenshot_path")
    if screenshot_path: # Screenshot mungkin None jika ada error awal
        assert os.path.exists(screenshot_path), f"File screenshot tidak ditemukan di: {screenshot_path}"
        assert os.path.basename(screenshot_path).endswith(config.DEFAULT_SCREENSHOT_FILENAME)
    else:
        # Jika kita mengharapkan screenshot selalu ada untuk tes ini, ini bisa jadi assert False
        print("Peringatan Tes: Screenshot path adalah None.")


    # 3. Cek apakah file log jaringan dibuat (jika ada network_events)
    # Halaman uji kita tidak melakukan banyak permintaan jaringan, jadi network_log_path mungkin None
    network_log_path = results.get("network_log_path")
    analysis_data = results.get("analysis_data", {})
    network_events = analysis_data.get("network_events", [])
    
    if network_events: # Hanya cek jika ada network events
        assert network_log_path is not None, "Path log jaringan tidak boleh None jika ada network events"
        assert os.path.exists(network_log_path), f"File log jaringan tidak ditemukan di: {network_log_path}"
        assert os.path.basename(network_log_path).endswith(config.DEFAULT_NETWORK_LOG_FILENAME)
    else:
        assert network_log_path is None, "Path log jaringan seharusnya None jika tidak ada network events"


def test_full_analysis_pipeline_captures_data(default_analysis_params):
    """
    Tes integrasi untuk memeriksa apakah data yang diharapkan dari halaman uji lokal
    tercatat dengan benar dalam hasil analisis.
    """
    results = run_analysis_pipeline(**default_analysis_params)
    assert results is not None
    analysis_data = results.get("analysis_data", {})
    assert analysis_data is not None

    # 1. Cek localStorage
    local_storage = analysis_data.get("local_storage", {})
    assert "integration_test_local_key" in local_storage, "Kunci localStorage tidak ditemukan"
    assert local_storage["integration_test_local_key"] == "local_value_123", "Nilai localStorage tidak sesuai"
    assert local_storage.get("another_local") == "some data"

    # 2. Cek sessionStorage
    session_storage = analysis_data.get("session_storage", {})
    assert "integration_test_session_key" in session_storage, "Kunci sessionStorage tidak ditemukan"
    assert session_storage["integration_test_session_key"] == "session_value_456", "Nilai sessionStorage tidak sesuai"

    # 3. Cek deteksi eval
    dynamic_js_calls = analysis_data.get("dynamic_js_calls", [])
    assert len(dynamic_js_calls) > 0, "Tidak ada panggilan JS dinamis yang terdeteksi"
    
    eval_call_found = False
    for call in dynamic_js_calls:
        if call.get("function_name") == "eval":
            assert "integration_eval_var" in call.get("arguments", ""), "Argumen eval tidak sesuai"
            eval_call_found = True
            break
    assert eval_call_found, "Panggilan eval tidak ditemukan dalam log JS dinamis"
    
    # 4. Cek IOC (domain dari URL file lokal mungkin tidak relevan atau None)
    # Kita bisa fokus pada apakah IOC extractor dipanggil jika ada network events.
    # Halaman uji kita saat ini tidak membuat banyak network events yang menghasilkan IOC menarik.
    # Tes ini bisa diperluas jika halaman uji dimodifikasi untuk membuat permintaan jaringan.
    extracted_iocs = analysis_data.get("extracted_iocs", {})
    assert "unique_domains" in extracted_iocs # Pastikan key ada

    # 5. Cek Cookies (halaman uji kita tidak mengatur cookie via JS secara default)
    cookies = analysis_data.get("cookies", [])
    # Untuk file:/// URL, biasanya tidak ada cookies yang relevan dari browser itu sendiri
    assert isinstance(cookies, list), "Cookies seharusnya berupa list"
    # Jika Anda mengharapkan cookie tertentu, tambahkan asersi di sini.

    # 6. Cek Laporan VirusTotal (dinonaktifkan di default_analysis_params, jadi harus kosong)
    vt_reports = analysis_data.get("virustotal_reports", [])
    assert len(vt_reports) == 0, "Laporan VirusTotal seharusnya kosong karena dinonaktifkan untuk tes ini"

