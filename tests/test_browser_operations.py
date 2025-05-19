# tests/test_browser_operations.py
import os
import sys
import time
import pytest
from unittest import mock

# Tambahkan path root proyek ke sys.path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.insert(0, project_root)

# Impor kelas yang akan diuji dan konfigurasi
from core.browser_operations import BrowserAutomation, PlaywrightError
import config

# --- Tes untuk BrowserAutomation ---

@pytest.fixture
def default_config_values():
    """Mengembalikan nilai default dari config untuk perbandingan."""
    return {
        "browser_type": config.BROWSER_TYPE,
        "headless_mode": False, # Konsisten dengan log yang menunjukkan headless=False saat tes
        "default_timeout": config.DEFAULT_TIMEOUT,
    }

@pytest.fixture
def mock_playwright_page():
    """Fixture untuk mock objek page Playwright dan metode-metodenya."""
    page_mock = mock.MagicMock(name="page_mock_fixture")
    page_mock.url = "http://mockedurl.com/currentpage"
    page_mock.is_closed.return_value = False
    
    page_mock.goto = mock.MagicMock(return_value=None, name="page_goto_mock")
    page_mock.evaluate = mock.MagicMock(return_value={}, name="page_evaluate_mock")
    page_mock.screenshot = mock.MagicMock(return_value=None, name="page_screenshot_mock")
    page_mock.wait_for_timeout = mock.MagicMock(return_value=None, name="page_wait_for_timeout_mock")
    page_mock.add_init_script = mock.MagicMock(return_value=None, name="page_add_init_script_mock")
    page_mock.expose_function = mock.MagicMock(return_value=None, name="page_expose_function_mock")
    page_mock.on = mock.MagicMock(return_value=None, name="page_on_mock")
    page_mock.close = mock.MagicMock(return_value=None, name="page_close_mock")
    return page_mock

@pytest.fixture
def mock_playwright_context(mock_playwright_page):
    """Fixture untuk mock objek context Playwright."""
    context_mock = mock.MagicMock(name="context_mock_fixture")
    context_mock.new_page.return_value = mock_playwright_page
    context_mock.cookies.return_value = [] 
    context_mock.close = mock.MagicMock(return_value=None, name="context_close_mock")
    return context_mock

@pytest.fixture
def mock_playwright_browser(mock_playwright_context):
    """Fixture untuk mock objek browser Playwright."""
    browser_mock = mock.MagicMock(name="browser_mock_fixture")
    browser_mock.new_context.return_value = mock_playwright_context
    browser_mock.close = mock.MagicMock(return_value=None, name="browser_close_mock")
    return browser_mock

@pytest.fixture
def patched_playwright_manager_setup(mocker, mock_playwright_browser):
    """
    Fixture yang mem-patch sync_playwright dan mengembalikan playwright_manager_mock.
    Ini akan digunakan oleh fixture browser_automation_instance.
    """
    playwright_manager_mock = mock.MagicMock(name="playwright_manager_patched_in_setup")
    
    playwright_manager_mock.chromium = mock.MagicMock(name="chromium_manager_in_setup")
    playwright_manager_mock.firefox = mock.MagicMock(name="firefox_manager_in_setup")
    playwright_manager_mock.webkit = mock.MagicMock(name="webkit_manager_in_setup")

    playwright_manager_mock.chromium.launch = mock.MagicMock(return_value=mock_playwright_browser, name="chromium_launch_in_setup")
    playwright_manager_mock.firefox.launch = mock.MagicMock(return_value=mock_playwright_browser, name="firefox_launch_in_setup")
    playwright_manager_mock.webkit.launch = mock.MagicMock(return_value=mock_playwright_browser, name="webkit_launch_in_setup")
    playwright_manager_mock.stop = mock.MagicMock(name="playwright_manager_stop_in_setup")

    # Patch sync_playwright di modul browser_operations
    mock_sync_playwright_constructor = mocker.patch('core.browser_operations.sync_playwright')
    mock_sync_playwright_constructor.return_value.start.return_value = playwright_manager_mock
    
    return playwright_manager_mock


@pytest.fixture
def bai(default_config_values, patched_playwright_manager_setup): # Menggunakan patched_playwright_manager_setup
    """Fixture untuk membuat instance BrowserAutomation yang sudah menggunakan Playwright yang di-mock."""
    instance = BrowserAutomation(
        target_url="http://testurl.com", 
        browser_type=default_config_values["browser_type"], 
        headless_mode=default_config_values["headless_mode"]
    )
    # Simpan referensi ke manager mock yang digunakan agar bisa diakses di tes
    instance._test_playwright_manager = patched_playwright_manager_setup
    return instance


# --- Tes Inisialisasi ---
def test_browser_automation_initialization_defaults(default_config_values):
    target_url = "http://example.com"
    with mock.patch.object(config, 'HEADLESS_MODE', default_config_values['headless_mode']): 
        automation = BrowserAutomation(target_url=target_url)
        assert automation.target_url == target_url
        assert automation.browser_type == default_config_values["browser_type"]
        assert automation.headless_mode == default_config_values["headless_mode"] 
        assert automation.network_data == []
        assert automation.local_storage_data == {}

def test_browser_automation_initialization_custom_params():
    target_url = "http://custom.com"
    browser_type = "firefox"
    headless_mode = True 
    automation = BrowserAutomation(target_url=target_url, browser_type=browser_type, headless_mode=headless_mode)
    assert automation.target_url == target_url
    assert automation.browser_type == browser_type
    assert automation.headless_mode == headless_mode

# --- Tes Metode Analyze Page ---
def test_analyze_page_calls_playwright_launch_and_goto(
    bai, mock_playwright_browser, mock_playwright_page, default_config_values
): # mocker dan patched_playwright_manager tidak perlu di sini lagi
    """Tes apakah analyze_page memanggil launch browser dan page.goto."""
    target_url = "http://testurl.com" 
    bai.target_url = target_url 
    
    # Dapatkan manager mock dari instance bai
    pm_mock = bai._test_playwright_manager 
    
    bai.analyze_page()

    expected_headless_mode = bai.headless_mode 
    if bai.browser_type == "chromium":
        pm_mock.chromium.launch.assert_called_once_with(headless=expected_headless_mode)
    elif bai.browser_type == "firefox":
        pm_mock.firefox.launch.assert_called_once_with(headless=expected_headless_mode)
    elif bai.browser_type == "webkit":
        pm_mock.webkit.launch.assert_called_once_with(headless=expected_headless_mode)

    # Setelah analyze_page, bai.page seharusnya adalah mock_playwright_page
    assert bai.page is mock_playwright_page 
    bai.page.goto.assert_called_once_with(
        target_url, 
        timeout=default_config_values["default_timeout"], 
        wait_until="load" 
    )
    
    # bai.browser_instance seharusnya adalah mock_playwright_browser
    assert bai.browser_instance is mock_playwright_browser 
    bai.browser_instance.close.assert_called_once()
    pm_mock.stop.assert_called_once()


def test_analyze_page_calls_helper_methods(bai): # mocker dan patched_playwright_manager tidak perlu
    """Tes apakah analyze_page memanggil _get_storage_data dan _get_cookies_data."""
    # Instance bai sudah menggunakan Playwright yang di-mock
    with mock.patch.object(bai, '_get_storage_data', return_value=({}, {})) as mock_get_storage, \
         mock.patch.object(bai, '_get_cookies_data', return_value=[]) as mock_get_cookies:
        
        bai.analyze_page()
        
        mock_get_storage.assert_called_once()
        mock_get_cookies.assert_called_once()

def test_analyze_page_adds_init_script_and_exposes_function(bai, mock_playwright_page): # mocker dan patched_playwright_manager tidak perlu
    """Tes apakah add_init_script dan expose_function dipanggil."""
    bai.analyze_page()
    
    assert bai.page is mock_playwright_page 
    bai.page.add_init_script.assert_called_once()
    bai.page.expose_function.assert_called_once_with(
        "logPythonDynamicJSCall", 
        bai._log_dynamic_js_call
    )

def test_analyze_page_registers_network_event_handlers(bai, mock_playwright_page): # mocker dan patched_playwright_manager tidak perlu
    """Tes apakah event handler jaringan (request, response) didaftarkan."""
    bai.analyze_page()
    
    assert bai.page is mock_playwright_page 
    calls = bai.page.on.call_args_list
    assert mock.call("request", bai._handle_request) in calls
    assert mock.call("response", bai._handle_response) in calls


def test_log_dynamic_js_call(bai, mock_playwright_page): 
    """Tes apakah _log_dynamic_js_call menambahkan entri ke dynamic_js_executions."""
    bai.page = mock_playwright_page 
    
    func_name = "eval"
    args_str = "alert('test');"
    bai._log_dynamic_js_call(func_name, args_str)
    
    assert len(bai.dynamic_js_executions) == 1
    log_entry = bai.dynamic_js_executions[0]
    assert log_entry["function_name"] == func_name
    assert log_entry["arguments"] == args_str
    assert log_entry["source_url"] == mock_playwright_page.url

@mock.patch.object(config, 'DEFAULT_TIMEOUT', 1000) 
def test_analyze_page_handles_goto_timeout(bai, mock_playwright_browser, mock_playwright_page): # mocker dan patched_playwright_manager tidak perlu
    """Tes penanganan error timeout saat page.goto."""
    # Dapatkan manager mock dari instance bai
    pm_mock = bai._test_playwright_manager
    
    # Atur mock_playwright_page (yang akan menjadi bai.page) untuk melempar error
    # Kita perlu memastikan bahwa bai.page akan menjadi mock_playwright_page ini.
    # Fixture bai sudah diatur agar menggunakan mock_playwright_browser yang mengembalikan mock_playwright_page.
    mock_playwright_page.goto.side_effect = PlaywrightError("Navigasi timeout!")

    screenshot_path, network, local_s, session_s, cookies, js_calls = bai.analyze_page()

    assert screenshot_path is None 
    
    assert bai.browser_instance is mock_playwright_browser 
    if bai.browser_instance:
         bai.browser_instance.close.assert_called_once()
    pm_mock.stop.assert_called_once()
