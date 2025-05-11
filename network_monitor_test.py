from playwright.sync_api import sync_playwright, Error

def handle_request(request):
    """
    Fungsi ini akan dipanggil setiap kali ada permintaan jaringan baru.
    Kita akan mencetak URL dan metode permintaan tersebut.
    """
    print(f">> Request: {request.method} {request.url}")
    # Anda bisa menambahkan lebih banyak detail di sini, misalnya:
    # print(f"   Headers: {request.headers}")
    # if request.method == "POST":
    #     print(f"   Post Data: {request.post_data}")
    # Penting: Jangan memodifikasi request di sini kecuali Anda tahu apa yang Anda lakukan,
    # karena bisa mengganggu pemuatan halaman. Untuk saat ini, kita hanya mencatat.

def handle_response(response):
    """
    Fungsi ini akan dipanggil setiap kali ada respons jaringan.
    """
    print(f"<< Response: {response.status} {response.url}")
    # Anda bisa menambahkan lebih banyak detail di sini, misalnya:
    # print(f"   Headers: {response.headers}")
    # try:
    #     if "application/json" in response.headers.get("content-type", "").lower():
    #         print(f"   JSON Response Body: {response.json()}")
    #     else:
    #         # Hati-hati dengan response body yang besar, bisa memenuhi log.
    #         # Pertimbangkan untuk hanya mengambil beberapa byte pertama atau tidak mencetaknya.
    #         # print(f"   Response Body (text): {response.text()[:200]}...") # Ambil 200 karakter pertama
    #         pass
    # except Error as e:
    #     print(f"   Error reading response body: {e}")


def run(playwright):
    # Pilih browser yang ingin digunakan: chromium, firefox, atau webkit
    # headless=False akan menampilkan GUI browser, berguna untuk debugging awal.
    # Setelah yakin, ganti kembali ke headless=True.
    browser = playwright.chromium.launch(headless=True)

    # Buat konteks browser baru
    context = browser.new_context()

    # Buat halaman baru di dalam konteks
    page = context.new_page()

    # Mendaftarkan event listener untuk permintaan jaringan
    # 'request' akan dipicu untuk setiap permintaan yang dibuat oleh halaman
    page.on("request", handle_request)

    # Mendaftarkan event listener untuk respons jaringan
    # 'response' akan dipicu untuk setiap respons yang diterima
    page.on("response", handle_response)

    # Buka URL - ganti dengan URL yang ingin Anda uji
    # Halaman yang melakukan banyak request XHR/Fetch akan lebih menarik untuk diuji.
    # Misalnya, coba buka situs berita atau media sosial.
    target_url = "https://jsonplaceholder.typicode.com/todos/1" # Contoh URL yang melakukan Fetch request
    print(f"Navigating to {target_url}...")
    try:
        page.goto(target_url, timeout=60000) # Timeout 60 detik
        print("Navigation successful.")

        # Beri sedikit waktu agar semua request yang mungkin tertunda bisa selesai
        # (Ini hanya untuk demonstrasi, cara yang lebih baik mungkin diperlukan untuk kasus nyata)
        page.wait_for_timeout(5000) # Tunggu 5 detik

        # Ambil screenshot (opsional, tapi bisa berguna)
        screenshot_path = "network_activity_screenshot.png"
        page.screenshot(path=screenshot_path)
        print(f"Screenshot saved to {screenshot_path}")

    except Error as e: # Menggunakan Playwright's Error class
        print(f"An error occurred during navigation or processing: {e}")
    except Exception as e:
        print(f"A general error occurred: {e}")
    finally:
        # Tutup browser
        browser.close()
        print("Browser closed.")

with sync_playwright() as playwright:
    run(playwright)
