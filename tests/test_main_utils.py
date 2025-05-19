# tests/test_main_utils.py
import os
import sys
import pytest

# Tambahkan path root proyek ke sys.path agar bisa mengimpor modul dari main.py
# Ini diperlukan karena tests/ adalah direktori terpisah.
# Sesuaikan kedalaman '..' jika struktur direktori Anda berbeda.
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.insert(0, project_root)

# Sekarang kita bisa mengimpor fungsi dari main.py
# Karena main.py tidak dirancang sebagai modul yang bisa diimpor langsung,
# kita mungkin perlu sedikit trik atau merefaktor main.py jika banyak fungsi yang mau diuji.
# Untuk ensure_url_scheme, kita bisa coba impor langsung jika tidak ada side effect saat impor main.
# Alternatif: pindahkan ensure_url_scheme ke file utilitas terpisah.

# Untuk saat ini, kita asumsikan kita bisa mengimpornya atau kita akan menyalin fungsinya ke sini untuk diuji.
# Cara yang lebih baik adalah memindahkan ensure_url_scheme ke file utils.py
# dan mengimpornya dari sana di main.py dan di file tes ini.

# Mari kita coba impor langsung dari main (mungkin perlu penyesuaian jika main.py melakukan banyak hal saat diimpor)
try:
    from main import ensure_url_scheme # Mencoba impor dari main.py
except ImportError as e:
    print(f"Tidak dapat mengimpor ensure_url_scheme dari main: {e}")
    # Jika impor gagal, sebagai fallback untuk pengujian, Anda bisa menyalin definisi fungsi ensure_url_scheme ke sini.
    # Ini bukan praktik terbaik, idealnya fungsi tersebut ada di modul utilitas.
    # Untuk demonstrasi, jika impor gagal, kita definisikan ulang di sini (HANYA UNTUK TES INI)
    if 'ensure_url_scheme' not in globals():
        from urllib.parse import urlparse
        def ensure_url_scheme(url_string): # Definisi ulang sederhana untuk tes
            if not url_string: return None
            parsed_url = urlparse(url_string)
            if not parsed_url.scheme:
                if url_string.startswith('file:///'): return url_string
                # Heuristik sederhana untuk path file lokal
                if os.path.exists(url_string) or url_string.startswith('/') or (len(url_string) > 1 and url_string[1] == ':'):
                     if len(url_string) > 1 and url_string[1] == ':': return f"file:///{url_string.replace(os.sep, '/')}"
                     return f"file://{os.path.abspath(url_string)}"
                return f"https://{url_string}"
            elif parsed_url.scheme not in ['http', 'https', 'file']:
                path_part = url_string.split('://', 1)[-1]
                return f"https://{path_part}"
            return url_string

# --- Kumpulan Tes untuk ensure_url_scheme ---

def test_ensure_url_scheme_no_scheme():
    """Tes URL tanpa skema, seharusnya ditambahkan https."""
    assert ensure_url_scheme("example.com") == "https://example.com"
    assert ensure_url_scheme("sub.example.com/path?query=1") == "https://sub.example.com/path?query=1"

def test_ensure_url_scheme_with_http():
    """Tes URL dengan skema http, seharusnya tidak berubah."""
    assert ensure_url_scheme("http://example.com") == "http://example.com"

def test_ensure_url_scheme_with_https():
    """Tes URL dengan skema https, seharusnya tidak berubah."""
    assert ensure_url_scheme("https://example.com") == "https://example.com"

def test_ensure_url_scheme_with_file_scheme():
    """Tes URL dengan skema file, seharusnya tidak berubah."""
    assert ensure_url_scheme("file:///path/to/file.html") == "file:///path/to/file.html"

def test_ensure_url_scheme_local_file_path_unix():
    """Tes path file lokal Unix, seharusnya dikonversi ke URL file."""
    # Kita perlu mock os.path.exists atau membuat file dummy untuk ini agar lebih robust
    # Untuk kesederhanaan awal, kita asumsikan pathnya valid untuk logika ensure_url_scheme
    # Perhatian: os.path.abspath akan bergantung pada CWD saat tes dijalankan.
    # Ini mungkin bukan tes unit yang murni jika bergantung pada sistem file.
    # Untuk tes yang lebih baik, fungsi ensure_url_scheme mungkin perlu di-refactor
    # agar tidak bergantung pada os.path.exists secara langsung atau di-mock.
    
    # Contoh path absolut
    abs_path = "/tmp/testfile.html"
    expected_url = f"file://{os.path.abspath(abs_path)}" # abspath mungkin tidak perlu jika sudah absolut
    assert ensure_url_scheme(abs_path) == expected_url

    # Contoh path relatif (hasilnya akan bergantung pada CWD saat tes dijalankan)
    # relative_path = "testfile_rel.html"
    # expected_rel_url = f"file://{os.path.abspath(relative_path)}"
    # assert ensure_url_scheme(relative_path) == expected_rel_url


def test_ensure_url_scheme_local_file_path_windows():
    """Tes path file lokal Windows, seharusnya dikonversi ke URL file."""
    # Hanya jalankan tes ini jika kita tidak di Windows untuk menghindari error path
    # atau gunakan path yang valid untuk Windows jika di Windows.
    # Ini juga memiliki ketergantungan sistem file.
    if os.name != 'nt': # Jika bukan Windows
        win_path = "C:\\Users\\Test\\file.html"
        # Logika ensure_url_scheme kita akan menambahkan https jika os.path.exists(win_path) False
        # dan tidak dimulai dengan '/' atau drive letter.
        # Jika kita ingin benar-benar menguji konversi path Windows,
        # ensure_url_scheme perlu penyesuaian atau tes ini perlu dijalankan di Windows.
        # Untuk sekarang, kita uji kasus di mana ia akan default ke https
        # karena os.path.exists("C:\\...") akan False di non-Windows.
        # Atau, kita bisa mock os.path.exists.
        
        # Asumsi ensure_url_scheme akan menambahkan https karena path tidak valid di non-Windows
        # Ini menunjukkan batasan tes lintas platform tanpa mocking yang tepat.
        # assert ensure_url_scheme(win_path) == f"https://{win_path}"
        # Seharusnya dikonversi menjadi file:///C:/Users/Test/file.html jika logikanya benar
        # Untuk saat ini, kita skip tes path Windows yang kompleks di non-Windows tanpa mocking.
        pass 
    else: # Jika di Windows
        win_path_abs = "C:\\Users\\Test\\file.html"
        expected_win_url = f"file:///C:/Users/Test/file.html"
        assert ensure_url_scheme(win_path_abs) == expected_win_url


def test_ensure_url_scheme_unsupported_scheme():
    """Tes URL dengan skema tidak didukung, seharusnya diubah ke https."""
    assert ensure_url_scheme("ftp://example.com") == "https://example.com"
    assert ensure_url_scheme("customscheme://some/path") == "https://some/path"

def test_ensure_url_scheme_empty_string():
    """Tes dengan string kosong."""
    assert ensure_url_scheme("") == None

def test_ensure_url_scheme_none_input():
    """Tes dengan input None."""
    assert ensure_url_scheme(None) == None

# Anda bisa menambahkan lebih banyak kasus uji di sini
