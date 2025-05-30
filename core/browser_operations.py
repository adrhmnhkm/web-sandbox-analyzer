# core/browser_operations.py
import os
import time
import json 
from playwright.sync_api import sync_playwright, Error as PlaywrightError

# Impor konfigurasi dan logger
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
    def __init__(self, target_url, browser_type=None, headless_mode=None):
        self.target_url = target_url
        self.browser_type = browser_type if browser_type is not None else config.BROWSER_TYPE
        self.headless_mode = headless_mode if headless_mode is not None else config.HEADLESS_MODE
        
        self.playwright_context_manager = None
        self.browser_instance = None 
        self.context = None
        self.page = None
        self.network_data = []
        self.local_storage_data = {} 
        self.session_storage_data = {}
        self.cookies_data = []
        self.dynamic_js_executions = [] 

        logger.info(f"BrowserAutomation diinisialisasi untuk URL: {self.target_url}")
        logger.info(f"Menggunakan tipe browser: {self.browser_type}, Mode headless: {self.headless_mode}")

    def _handle_request(self, request):
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
            except Exception: 
                request_info["post_data"] = request.post_data_buffer.hex() if request.post_data_buffer else None
                request_info["post_data_format"] = "hex_buffer"
        self.network_data.append(request_info)
        logger.debug(f"Request: {request.method} {request.url}")


    def _handle_response(self, response):
        timestamp = time.time()
        response_info = {
            "timestamp": timestamp,
            "type": "response",
            "url": response.url,
            "status": response.status,
            "status_text": response.status_text,
            "headers": dict(response.headers),
        }
        self.network_data.append(response_info)
        logger.debug(f"Response: {response.status} {response.url}")

    def _get_storage_data(self):
        if not self.page:
            logger.warning("Halaman tidak tersedia untuk mengambil data storage.")
            return {}, {}
        try:
            logger.info("Mengambil data localStorage...")
            local_storage_items = self.page.evaluate("""() => {
                const items = {};
                for (let i = 0; i < localStorage.length; i++) {
                    const key = localStorage.key(i);
                    items[key] = localStorage.getItem(key);
                }
                return items;
            }""")
            self.local_storage_data = local_storage_items if local_storage_items else {}
            logger.info(f"Data localStorage diambil: {len(self.local_storage_data)} item.")
            logger.debug(f"Isi localStorage: {self.local_storage_data}")
        except Exception as e:
            logger.error(f"Gagal mengambil data localStorage: {e}", exc_info=True)
            self.local_storage_data = {"error": str(e)}
        try:
            logger.info("Mengambil data sessionStorage...")
            session_storage_items = self.page.evaluate("""() => {
                const items = {};
                for (let i = 0; i < sessionStorage.length; i++) {
                    const key = sessionStorage.key(i);
                    items[key] = sessionStorage.getItem(key);
                }
                return items;
            }""")
            self.session_storage_data = session_storage_items if session_storage_items else {}
            logger.info(f"Data sessionStorage diambil: {len(self.session_storage_data)} item.")
            logger.debug(f"Isi sessionStorage: {self.session_storage_data}")
        except Exception as e:
            logger.error(f"Gagal mengambil data sessionStorage: {e}", exc_info=True)
            self.session_storage_data = {"error": str(e)}
        return self.local_storage_data, self.session_storage_data

    def _get_cookies_data(self):
        if not self.context:
            logger.warning("Konteks browser tidak tersedia untuk mengambil cookies.")
            return []
        try:
            logger.info("Mengambil data cookies...")
            all_cookies = self.context.cookies() 
            self.cookies_data = all_cookies if all_cookies else []
            logger.info(f"Data cookies diambil: {len(self.cookies_data)} cookie.")
            logger.debug(f"Isi cookies: {self.cookies_data}")
        except Exception as e:
            logger.error(f"Gagal mengambil data cookies: {e}", exc_info=True)
            self.cookies_data = [{"error": str(e)}] 
        return self.cookies_data

    def _log_dynamic_js_call(self, function_name, args_string):
        """Mencatat pemanggilan fungsi JS dinamis."""
        timestamp = time.time()
        log_entry = {
            "timestamp": timestamp,
            "function_name": function_name,
            "arguments": args_string, 
            "source_url": self.page.url if self.page else "N/A" 
        }
        self.dynamic_js_executions.append(log_entry)
        logger.info(f"Eksekusi JS Dinamis Terdeteksi: {function_name} dengan argumen (awal): {args_string[:100]}{'...' if len(args_string)>100 else ''}")

    def analyze_page(self):
        logger.info(f"Memulai analisis untuk URL: {self.target_url}")
        screenshot_path = None
        collected_network_data = []
        self.network_data = [] 
        self.local_storage_data = {}
        self.session_storage_data = {}
        self.cookies_data = []
        self.dynamic_js_executions = [] 

        try:
            self.playwright_context_manager = sync_playwright().start()
            
            logger.info(f"Meluncurkan browser: {self.browser_type}, Headless: {self.headless_mode}")
            
            active_browser = None
            if self.browser_type == "chromium":
                active_browser = self.playwright_context_manager.chromium.launch(headless=self.headless_mode)
            elif self.browser_type == "firefox":
                active_browser = self.playwright_context_manager.firefox.launch(headless=self.headless_mode)
            elif self.browser_type == "webkit":
                active_browser = self.playwright_context_manager.webkit.launch(headless=self.headless_mode)
            else:
                logger.error(f"Tipe browser tidak didukung: {self.browser_type}")
                raise ValueError(f"Tipe browser tidak didukung: {self.browser_type}")
            self.browser_instance = active_browser

            logger.debug("Browser berhasil diluncurkan.")
            self.context = self.browser_instance.new_context(
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36 Sandbox/1.0"
            )
            logger.debug("Konteks browser dibuat.")
            self.page = self.context.new_page()
            logger.debug("Halaman baru dibuat.")

            self.page.expose_function("logPythonDynamicJSCall", self._log_dynamic_js_call)

            # --- PERUBAHAN DI SINI: Memperluas skrip inisialisasi ---
            init_script_dynamic_detection = """
                (() => {
                    // Helper untuk mengirim log ke Python
                    const sendLog = (funcName, argsArray) => {
                        try {
                            // Mengubah semua argumen menjadi string untuk logging sederhana
                            // Untuk setTimeout/setInterval, kita hanya tertarik jika argumen pertama adalah string (kode)
                            let loggableArgs = "";
                            if (funcName === 'setTimeout' || funcName === 'setInterval') {
                                if (typeof argsArray[0] === 'string') {
                                    loggableArgs = argsArray[0]; // Hanya log kode string
                                } else {
                                    return; // Jangan log jika bukan string kode
                                }
                            } else {
                                // Untuk eval dan Function, argumen biasanya adalah kode
                                loggableArgs = Array.from(argsArray).map(arg => String(arg)).join(', ');
                            }
                             window.logPythonDynamicJSCall(funcName, loggableArgs);
                        } catch (e) {
                            // Jika terjadi error saat logging, jangan sampai merusak halaman
                            console.warn('Error logging dynamic JS call:', e);
                        }
                    };

                    // Override eval
                    const originalEval = window.eval;
                    window.eval = function(...args) {
                        sendLog('eval', args);
                        return originalEval.apply(this, args);
                    };

                    // Override Function constructor
                    const originalFunction = window.Function;
                    window.Function = function(...args) {
                        sendLog('Function', args);
                        // Membuat instance Function baru menggunakan originalFunction
                        // 'new originalFunction(...args)' atau 'originalFunction.apply(this, args)'
                        // atau 'new (Function.prototype.bind.apply(originalFunction, [null, ...args]))'
                        // Cara paling aman untuk memanggil konstruktor asli adalah:
                        if (this instanceof window.Function && !this.prototype) { // Dipanggil sebagai konstruktor: new Function(...)
                             return new originalFunction(...args);
                        } else { // Dipanggil sebagai fungsi: Function(...)
                             return originalFunction(...args);
                        }
                    };
                    // Pastikan prototype tetap sama untuk instanceof checks
                    window.Function.prototype = originalFunction.prototype;


                    // Override setTimeout
                    const originalSetTimeout = window.setTimeout;
                    window.setTimeout = function(...args) {
                        if (typeof args[0] === 'string') {
                            sendLog('setTimeout', args);
                        }
                        return originalSetTimeout.apply(this, args);
                    };

                    // Override setInterval
                    const originalSetInterval = window.setInterval;
                    window.setInterval = function(...args) {
                        if (typeof args[0] === 'string') {
                            sendLog('setInterval', args);
                        }
                        return originalSetInterval.apply(this, args);
                    };
                    
                    console.log('Dynamic JS detection overrides installed.');
                })();
            """
            self.page.add_init_script(init_script_dynamic_detection)
            logger.info("Skrip inisialisasi untuk deteksi JS dinamis (eval, Function, setTimeout, setInterval) ditambahkan.")
            # --- AKHIR PERUBAHAN ---

            self.page.on("request", self._handle_request)
            self.page.on("response", self._handle_response)
            logger.info("Event listener jaringan didaftarkan.")

            logger.info(f"Menavigasi ke {self.target_url}...")
            self.page.goto(self.target_url, timeout=config.DEFAULT_TIMEOUT, wait_until="load")
            logger.info(f"Navigasi ke {self.target_url} berhasil (event 'load' terpicu).")

            self._get_storage_data() 
            self._get_cookies_data() 

            wait_after_load_ms = 3000 
            logger.info(f"Menunggu tambahan {wait_after_load_ms / 1000} detik untuk aktivitas pasca-pemuatan...")
            self.page.wait_for_timeout(wait_after_load_ms)
            logger.info("Periode tunggu tambahan selesai.")

            screenshot_dir_path = os.path.join(project_root, config.SCREENSHOT_DIR)
            if not os.path.exists(screenshot_dir_path):
                os.makedirs(screenshot_dir_path)
            
            url_slug = self.target_url.split('//')[-1].split('/')[0].replace('.', '_').replace(':', '_')
            timestamp_str = time.strftime("%Y%m%d-%H%M%S")
            filename = f"{url_slug}_{timestamp_str}_{config.DEFAULT_SCREENSHOT_FILENAME}"
            screenshot_path = os.path.join(screenshot_dir_path, filename)
            
            self.page.screenshot(path=screenshot_path, full_page=True)
            logger.info(f"Screenshot disimpan ke: {screenshot_path}")

            collected_network_data = list(self.network_data) 
            logger.info(f"Mengumpulkan {len(collected_network_data)} event jaringan.")
            logger.info(f"Terdeteksi {len(self.dynamic_js_executions)} pemanggilan fungsi JS dinamis.")

        except PlaywrightError as e:
            logger.error(f"Terjadi error Playwright: {e}", exc_info=True)
            screenshot_path = None 
        except ValueError as e: 
            logger.error(f"Error konfigurasi: {e}", exc_info=True)
            screenshot_path = None
        except Exception as e:
            logger.error(f"Terjadi error tak terduga saat automasi browser: {e}", exc_info=True)
            screenshot_path = None 
        finally:
            if self.page:
                try:
                    logger.debug("Menutup halaman...")
                    self.page.close()
                    logger.debug("Halaman berhasil ditutup.")
                except PlaywrightError as e:
                    logger.warning(f"Error saat menutup halaman: {e}", exc_info=True)
                except Exception as e: 
                    logger.warning(f"Error umum saat menutup halaman: {e}", exc_info=True)
            
            if self.context:
                try:
                    logger.debug("Menutup konteks browser...")
                    self.context.close() 
                    logger.debug("Konteks browser berhasil ditutup.")
                except PlaywrightError as e:
                    logger.warning(f"Error saat menutup konteks browser: {e}", exc_info=True)
                except Exception as e:
                    logger.warning(f"Error umum saat menutup konteks browser: {e}", exc_info=True)

            if self.browser_instance: 
                try:
                    logger.info("Menutup browser...")
                    self.browser_instance.close() 
                    logger.info("Browser berhasil ditutup.")
                except PlaywrightError as e:
                    logger.warning(f"Error saat menutup browser: {e}", exc_info=True)
                except Exception as e:
                    logger.warning(f"Error umum saat menutup browser: {e}", exc_info=True)
            
            if self.playwright_context_manager:
                try:
                    logger.debug("Menghentikan Playwright context manager...")
                    self.playwright_context_manager.stop()
                    logger.debug("Playwright context manager berhasil dihentikan.")
                except Exception as e:
                    logger.warning(f"Error saat menghentikan Playwright context manager: {e}", exc_info=True)
            logger.debug("Keluar dari method analyze_page.")

        return screenshot_path, collected_network_data, self.local_storage_data, self.session_storage_data, self.cookies_data, self.dynamic_js_executions
