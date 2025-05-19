# tests/test_report_generator.py
import os
import sys
import time
import pytest
from unittest import mock
from jinja2 import exceptions as JinjaExceptions # Impor yang benar untuk JinjaExceptions

# Tambahkan path root proyek ke sys.path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.insert(0, project_root)

# Impor kelas yang akan diuji dan konfigurasi
from core.report_generator import HTMLReportGenerator
import config

# --- Tes untuk HTMLReportGenerator ---

@pytest.fixture
def report_generator_instance():
    """Fixture untuk membuat instance HTMLReportGenerator."""
    template_dir_path = os.path.join(project_root, "templates")
    if not os.path.exists(template_dir_path):
        os.makedirs(template_dir_path)
    dummy_template_path = os.path.join(template_dir_path, "report_template.html")
    if not os.path.exists(dummy_template_path):
        with open(dummy_template_path, "w") as f:
            # Konten minimal yang cukup untuk tidak error saat render dummy
            # dan mencakup beberapa variabel yang mungkin diakses
            f.write("<html><body><h1>{{ target_url }}</h1>"
                    "{% if network_events %}Network Events: {{ network_events | length }}{% endif %}"
                    "{% if local_storage %}LocalStorage: {{ local_storage | length }}{% endif %}"
                    "{% if session_storage %}SessionStorage: {{ session_storage | length }}{% endif %}"
                    "{% if cookies %}Cookies: {{ cookies | length }}{% endif %}"
                    "{% if dynamic_js_calls %}JS Calls: {{ dynamic_js_calls | length }}{% endif %}"
                    "{% if extracted_iocs %}IOCs: {{ extracted_iocs.unique_domains | length }}{% endif %}"
                    "{% if virustotal_reports %}VT Reports: {{ virustotal_reports | length }}{% endif %}"
                    "</body></html>")
    return HTMLReportGenerator(template_dir="templates")

@pytest.fixture
def dummy_screenshot_file_path():
    """Fixture untuk membuat dan membersihkan file screenshot dummy."""
    path = os.path.join(project_root, "output", "screenshots", "dummy_screenshot_for_test.png")
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "wb") as f: 
        f.write(b"dummy_image_content")
    yield path 
    if os.path.exists(path): 
        os.remove(path)


@pytest.fixture
def dummy_analysis_data(dummy_screenshot_file_path): 
    """Fixture untuk menyediakan data analisis dummy."""
    current_time = time.time()
    return {
        'target_url': "http://test-example.com",
        'analysis_timestamp': time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(current_time)),
        'screenshot_path': dummy_screenshot_file_path, 
        'network_events': [{"type": "request", "url": "http://test-example.com/resource"}],
        'local_storage': {"key1": "value1"},
        'session_storage': {"skey1": "svalue1"},
        'extracted_iocs': {"unique_domains": ["test-example.com", "ads.test.com"]},
        'cookies': [{"name": "c1", "value": "v1", "domain": "test-example.com", "expires": current_time + 3600, "httpOnly": False, "secure": False, "sameSite": "Lax"}],
        'dynamic_js_calls': [{"function_name": "eval", "arguments": "alert(1)", "timestamp": current_time, "source_url": "http://test-example.com"}],
        'virustotal_reports': [{"domain": "ads.test.com", "malicious": 1, "link_to_report": "http://vt.com/ads"}]
    }

# Tes untuk filter unixtimestampformat
@pytest.mark.parametrize("timestamp_input, expected_output", [
    (None, "Tidak Ditentukan"),
    (-1, "Sesi"),
    ("-1", "Sesi"), 
    (0, "Tidak Ditentukan"),
    ("0", "Tidak Ditentukan"), 
    (1678886400, "2023-03-15 20:20:00"), 
    ("1678886400.0", "2023-03-15 20:20:00"), 
    ("invalid_timestamp", "invalid_timestamp") # String invalid akan dikembalikan apa adanya
])
def test_unixtimestampformat_filter(report_generator_instance, timestamp_input, expected_output):
    """Tes filter Jinja2 unixtimestampformat."""
    # Mock time.localtime hanya untuk timestamp angka yang valid agar output konsisten
    if (isinstance(timestamp_input, (int, float)) and timestamp_input not in [-1, 0]) or \
       (isinstance(timestamp_input, str) and timestamp_input.replace('.', '', 1).isdigit() and timestamp_input not in ["-1", "0"]):
        
        # Kasus spesifik untuk 1678886400 agar cocok dengan ekspektasi "2023-03-15 20:20:00"
        if str(float(timestamp_input) if isinstance(timestamp_input, str) and timestamp_input.replace('.', '', 1).isdigit() else timestamp_input) == "1678886400.0":
             with mock.patch('time.localtime', return_value=time.struct_time((2023, 3, 15, 20, 20, 0, 2, 74, 0))): # Rabu, DST tidak aktif
                 assert report_generator_instance.unixtimestampformat(timestamp_input) == expected_output
        else:
            # Untuk timestamp lain yang valid, kita hanya cek apakah ia mengembalikan string (karena output pasti bisa bervariasi)
            assert isinstance(report_generator_instance.unixtimestampformat(timestamp_input), str)
    else:
        assert report_generator_instance.unixtimestampformat(timestamp_input) == expected_output


@mock.patch('core.report_generator.os.makedirs')
@mock.patch('core.report_generator.os.path.exists')
@mock.patch('core.report_generator.shutil.copy2')
@mock.patch('builtins.open', new_callable=mock.mock_open) 
def test_generate_report_success(mock_open_file, mock_shutil_copy, mock_os_path_exists, mock_os_makedirs,
                                 report_generator_instance, dummy_analysis_data, dummy_screenshot_file_path):
    """Tes generate_report untuk kasus sukses."""
    
    def os_path_exists_side_effect(path_to_check):
        # Path absolut ke direktori laporan yang diharapkan
        expected_report_dir_abs = os.path.join(project_root, config.HTML_REPORT_DIR)
        if path_to_check == dummy_screenshot_file_path: # Path screenshot asli
            return True 
        if path_to_check == expected_report_dir_abs:
            return False # Direktori laporan belum ada, akan memicu makedirs
        return True # Default untuk path lain (misalnya, direktori template sudah ada)
    mock_os_path_exists.side_effect = os_path_exists_side_effect
    
    report_path = report_generator_instance.generate_report(dummy_analysis_data)

    assert report_path is not None
    assert config.HTML_REPORT_DIR in report_path
    assert ".html" in report_path
    
    expected_report_dir_abs = os.path.join(project_root, config.HTML_REPORT_DIR)
    mock_os_makedirs.assert_called_with(expected_report_dir_abs) 
    
    mock_shutil_copy.assert_called_once() 
    
    # Cek apakah file HTML ditulis dengan path yang benar
    # Panggilan terakhir ke open harusnya untuk menulis file laporan
    assert mock_open_file.call_args_list[-1] == mock.call(report_path, 'w', encoding='utf-8')
    mock_open_file().write.assert_called()


@mock.patch('core.report_generator.os.makedirs')
@mock.patch('core.report_generator.os.path.exists', return_value=False) # Screenshot tidak ditemukan
@mock.patch('core.report_generator.shutil.copy2')
@mock.patch('builtins.open', new_callable=mock.mock_open)
def test_generate_report_no_screenshot_file(mock_open_file, mock_shutil_copy, mock_os_path_exists_false, mock_os_makedirs,
                                          report_generator_instance, dummy_analysis_data):
    """Tes generate_report ketika file screenshot asli tidak ditemukan."""
    dummy_analysis_data_no_ss = dummy_analysis_data.copy()
    dummy_analysis_data_no_ss['screenshot_path'] = "/non/existent/screenshot.png" 
    
    report_path = report_generator_instance.generate_report(dummy_analysis_data_no_ss)

    assert report_path is not None
    mock_shutil_copy.assert_not_called() 
    
    # Cek apakah panggilan untuk menulis file laporan ada
    found_write_call_to_report = False
    # report_path akan memiliki timestamp, jadi kita tidak bisa membandingkan string penuh secara langsung
    # Kita cek apakah ada panggilan 'open' dalam mode 'w' yang path-nya ada di config.HTML_REPORT_DIR
    for call_obj in mock_open_file.call_args_list:
        args, kwargs = call_obj
        if len(args) >= 2 and args[1] == 'w' and config.HTML_REPORT_DIR in args[0] and args[0].endswith(config.DEFAULT_HTML_REPORT_FILENAME):
            found_write_call_to_report = True
            break
    assert found_write_call_to_report, "Expected 'open' to be called in write mode for the HTML report file."


def test_generate_report_template_not_found(report_generator_instance, dummy_analysis_data):
    """Tes generate_report ketika file template HTML tidak ditemukan."""
    with mock.patch.object(report_generator_instance.env, 'get_template', side_effect=JinjaExceptions.TemplateNotFound("non_existent_template.html")):
        report_path = report_generator_instance.generate_report(dummy_analysis_data)
        assert report_path is None
