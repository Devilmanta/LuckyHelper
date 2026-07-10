@echo off
chcp 65001 > nul
echo.
echo  ============================================================
echo    LuckyHelper - Build Script
echo    Futures Trading Journal v1.0.0
echo  ============================================================
echo.

:: ── Check Python ─────────────────────────────────────────────────────────────
python --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Python bulunamadi. Lutfen Python 3.11+ yukleyin.
    pause
    exit /b 1
)

:: ── Install / upgrade deps ────────────────────────────────────────────────────
echo [1/4] Bagimliliklar yukleniyor...
pip install pyinstaller>=6.0.0 PyQt6>=6.7.0 pillow -q
if errorlevel 1 (
    echo [ERROR] pip install basarisiz.
    pause
    exit /b 1
)
echo       Tamam.
echo.

:: ── Generate icon ─────────────────────────────────────────────────────────────
echo [2/4] Ikon olusturuluyor...
python generate_icon.py
if errorlevel 1 (
    echo [WARN] Ikon olusturulamadi, devam ediliyor...
)
echo.

:: ── Clean old build ───────────────────────────────────────────────────────────
echo [3/4] Eski build temizleniyor...
if exist "dist\LuckyHelper" rmdir /s /q "dist\LuckyHelper"
if exist "build\LuckyHelper" rmdir /s /q "build\LuckyHelper"
echo       Tamam.
echo.

:: ── Build ─────────────────────────────────────────────────────────────────────
echo [4/4] PyInstaller ile derleniyor (bu 2-3 dakika surebilir)...
echo.
python -m PyInstaller LuckyHelper.spec --noconfirm
if errorlevel 1 (
    echo.
    echo [ERROR] Build basarisiz! Yukaridaki hata mesajini inceleyin.
    pause
    exit /b 1
)

echo.
echo  ============================================================
echo    BUILD BASARILI!
echo    Cikti klasoru: dist\LuckyHelper\
echo    Calistirmak icin: dist\LuckyHelper\LuckyHelper.exe
echo  ============================================================
echo.
echo  NOT: Veri dosyalari (trades, ayarlar) sunrada saklanir:
echo       %%APPDATA%%\LuckyHelper\
echo.
pause
