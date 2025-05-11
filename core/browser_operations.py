
import os
import time
from playwright.sync_api import sync_playwright, Error as PlaywrightError


import sys
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(current_dir)
if project_root not in sys.path:
    sys.path.insert(0, project_root)

import config
from utils.logger_config import setup_logger

# Setup logger untuk modul ini
logger = setup_logger(__name__, config.LOG_LEVEL, config.LOG_FILE)

class BrowserAutomation:
    def __init__(self, target_url):
        """
        Inisialisasi BrowserAutomation.
        :param target_url: URL yang akan dianalisis.
        """
        self.target_url = target_url
        self.playwright_context = None
        self.browser = None
        self.context = None
        self.page = None
        self.network_data = [] # Untuk menyimpan data jaringan yang terkumpul

    def _handle_request(self, request):
        """
        Handler untuk event 'request'. Mengumpulkan detail permintaan.
        """
        timestamp = time.time()
        request_info = {
            "timestamp": timestamp,
            "type": "request",
            "url": request.url,
            "method": request.method,
            "headers": dict(request.headers),
            "resource_type": request.resource_type
        }
        if request.method.upper() == "POST":
            try:
                request_info["post_data"] = request.post_data_json if request.post_data else None
            except Exception: # Jika post_data bukan JSON valid atau error lain
                request_info["post_data"] = request.post_data_buffer.hex() if request.post_data_buffer else None
                request_info["post_data_format"] = "hex_buffer"


        self.network_data.append(request_info)
        logger.debug(f"Request: {request.method} {request.url}")

    def _handle_response(self, response):
        """
        Handler untuk event 'response'. Mengumpulkan detail respons.
        """
        timestamp = time.time()
        response_info = {
            "timestamp": timestamp,
            "type": "response",
            "url": response.url,
            "status": response.status,
            "status_text": response.status_text,
            "headers": dict(response.headers),
        }
        # Coba dapatkan body respons jika perlu (hati-hati dengan ukuran besar)
        # Untuk sekarang kita skip body agar tidak terlalu verbose dan berat
        # if "application/json" in response.headers.get("content-type", "").lower():
        #     try:
        #         response_info["body_json"] = response.json()
        #     except PlaywrightError:
        #         logger.warning(f"Could not parse JSON response from {response.url}")
        #         response_info["body_text"] = response.text()[:500] # Ambil sebagian kecil
        # else:
        #     response_info["body_text"] = response.text()[:500] # Ambil sebagian kecil

        self.network_data.append(response_info)
        logger.debug(f"Response: {response.status} {response.url}")


    def analyze_page(self):
        """
        Melakukan analisis halaman: meluncurkan browser, navigasi, dan mengumpulkan data.
        :return: Tuple (path_screenshot, data_jaringan_terkumpul) atau (None, []) jika gagal.
        """
        logger.info(f"Starting analysis for URL: {self.target_url}")
        screenshot_path = None
        collected_network_data = [] # Reset data untuk analisis baru
        self.network_data = [] # Pastikan network_data bersih setiap kali analyze_page dipanggil

        try:
            with sync_playwright() as p:
                self.playwright_context = p
                logger.info(f"Launching browser: {config.BROWSER_TYPE}, Headless: {config.HEADLESS_MODE}")
                if config.BROWSER_TYPE == "chromium":
                    self.browser = self.playwright_context.chromium.launch(headless=config.HEADLESS_MODE)
                elif config.BROWSER_TYPE == "firefox":
                    self.browser = self.playwright_context.firefox.launch(headless=config.HEADLESS_MODE)
                elif config.BROWSER_TYPE == "webkit":
                    self.browser = self.playwright_context.webkit.launch(headless=config.HEADLESS_MODE)
                else:
                    logger.error(f"Unsupported browser type: {config.BROWSER_TYPE}")
                    raise ValueError(f"Unsupported browser type: {config.BROWSER_TYPE}")

                logger.debug("Browser launched successfully.")
                self.context = self.browser.new_context(
                    user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36 Sandbox/1.0"
                )
                logger.debug("Browser context created.")
                self.page = self.context.new_page()
                logger.debug("New page created.")

                # Mendaftarkan event listeners
                self.page.on("request", self._handle_request)
                self.page.on("response", self._handle_response)
                logger.info("Network event listeners registered.")

                logger.info(f"Navigating to {self.target_url}...")
                self.page.goto(self.target_url, timeout=config.DEFAULT_TIMEOUT, wait_until="domcontentloaded")
                logger.info(f"Navigation to {self.target_url} successful (DOM content loaded).")

                wait_after_load_ms = 5000 
                logger.info(f"Waiting for {wait_after_load_ms / 1000} seconds for dynamic content to load...")
                self.page.wait_for_timeout(wait_after_load_ms)
                logger.info("Initial wait period complete.")

                if not os.path.exists(config.SCREENSHOT_DIR):
                    os.makedirs(config.SCREENSHOT_DIR)
                
                url_slug = self.target_url.split('//')[-1].split('/')[0].replace('.', '_')
                timestamp_str = time.strftime("%Y%m%d-%H%M%S")
                filename = f"{url_slug}_{timestamp_str}_{config.DEFAULT_SCREENSHOT_FILENAME}"
                screenshot_path = os.path.join(config.SCREENSHOT_DIR, filename)
                
                self.page.screenshot(path=screenshot_path, full_page=True)
                logger.info(f"Screenshot saved to: {screenshot_path}")

                collected_network_data = list(self.network_data) 
                logger.info(f"Collected {len(collected_network_data)} network events.")

        except PlaywrightError as e:
            logger.error(f"A Playwright error occurred: {e}", exc_info=True)
            screenshot_path = None 
        except ValueError as e: 
            logger.error(f"Configuration error: {e}", exc_info=True)
            screenshot_path = None
        except Exception as e:
            logger.error(f"An unexpected error occurred during browser automation: {e}", exc_info=True)
            screenshot_path = None 
        finally:
            # --- AWAL BLOK YANG DIGANTI ---
            if self.browser: # Hanya coba tutup jika browser berhasil diinisialisasi
                try:
                    logger.info("Closing browser (this should also close its contexts and pages)...")
                    self.browser.close() # Ini seharusnya juga menutup page dan context terkait.
                    logger.info("Browser closed successfully.")
                except PlaywrightError as e:
                    logger.warning(f"Error closing browser: {e}", exc_info=True)
            
            # self.playwright_context (yaitu 'p' dari with sync_playwright() as p:) 
            # dikelola oleh statement 'with' dan akan dibersihkan secara otomatis.
            logger.debug("Exiting analyze_page method.")
            # --- AKHIR BLOK YANG DIGANTI ---

        return screenshot_path, collected_network_data

# Contoh penggunaan (bisa dipindahkan ke main.py nanti)
if __name__ == '__main__':
    logger.info("Starting browser_operations.py directly for testing.")
    
    if not os.path.exists(config.SCREENSHOT_DIR):
        os.makedirs(config.SCREENSHOT_DIR)
    if not os.path.exists(config.NETWORK_LOG_DIR):
        os.makedirs(config.NETWORK_LOG_DIR)

    test_url = config.DEFAULT_TARGET_URL 

    automation = BrowserAutomation(target_url=test_url)
    screenshot, network_log = automation.analyze_page()

    if screenshot:
        logger.info(f"Analysis complete. Screenshot at: {screenshot}")
    else:
        logger.error("Analysis failed to produce a screenshot.")

    if network_log:
        logger.info(f"Total network events captured: {len(network_log)}")
    else:
        logger.info("No network events captured or analysis failed.")

    logger.info("browser_operations.py test finished.")
