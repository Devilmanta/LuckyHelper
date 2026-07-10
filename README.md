# LuckyHelper — Futures Trading Journal

> Bir futures trader'ın işlemlerini takip etmesine yarayan, dark-theme, offline çalışan masaüstü uygulaması.

---

## Özellikler

| Modül | Açıklama |
|---|---|
| 📅 **Takvim** | Aylık takvim görünümü, günlük PnL, trade ekleme/düzenleme |
| 📊 **İstatistikler** | Winrate, ortalama R/R, equity eğrisi, detaylı metrikler |
| ⚡ **Risk Hesaplayıcı** | Bakiye × risk % × kaldıraç ile pozisyon boyutu hesabı |
| ⚖️ **Ortalama Maliyet** | DCA hesaplayıcı |
| 🏆 **Winrate Hesaplayıcı** | Manuel senaryo hesaplayıcı |
| ⚙️ **Ayarlar** | Bakiye, risk %, takvim, istatistik ve risk tercihlerini ayarla |

---

## Kurulum (Hazır EXE — Önerilen)

1. `dist/LuckyHelper/` klasörünü istediğiniz yere kopyalayın
2. `LuckyHelper.exe` dosyasını çalıştırın
3. İlk açılışta **Ayarlar → Hesap** bölümünden başlangıç bakiyenizi girin

> **Veri konumu:** `%APPDATA%\LuckyHelper\`  
> Trade verileriniz ve screenshot'larınız buraya kaydedilir. EXE'yi taşısanız bile verileriniz kaybolmaz.

---

## Geliştirici Kurulumu

### Gereksinimler
- Python 3.11+
- Windows 10/11 (64-bit)

### Adımlar

```bash
# Bağımlılıkları kur
pip install -r requirements.txt

# Uygulamayı başlat
python main.py
```

### Build (EXE Oluştur)

```bash
# Tek komutla build et
build.bat
```

Çıktı: `dist/LuckyHelper/LuckyHelper.exe`

---

## Proje Yapısı

```
LuckyHelper/
├── main.py                  # Giriş noktası
├── build.bat                # Build script
├── LuckyHelper.spec         # PyInstaller konfigürasyonu
├── requirements.txt
├── assets/
│   ├── icon.ico             # Uygulama ikonu
│   └── icon.png
├── database/
│   └── db_manager.py        # SQLite CRUD + ayarlar
└── ui/
    ├── main_window.py       # Ana pencere + sayfa yönetimi
    ├── sidebar.py           # Sol navigasyon paneli
    ├── styles.py            # QSS dark theme
    ├── calendar_view.py     # Takvim sayfası
    ├── trade_dialog.py      # Trade ekleme/düzenleme dialog
    ├── statistics_view.py   # İstatistik sayfası
    ├── risk_calculator.py   # Risk hesaplayıcı
    ├── avg_cost_calculator.py
    ├── winrate_calculator.py
    └── settings_view.py     # Ayarlar paneli
```

---

## Veri Güvenliği

- Tüm veriler **yerel SQLite** veritabanında saklanır (`%APPDATA%\LuckyHelper\luckyhelper.db`)
- İnternet bağlantısı **gerekmez** — tamamen offline çalışır
- Yedek almak için sadece `%APPDATA%\LuckyHelper\` klasörünü kopyalayın

---
<img width="1424" height="891" alt="image" src="https://github.com/user-attachments/assets/9d62a556-a292-4c95-a378-b70616d9cd24" />
<img width="1430" height="925" alt="image" src="https://github.com/user-attachments/assets/71f11620-478d-46b1-ac3d-4404bf6e2a01" />
<img width="1413" height="672" alt="image" src="https://github.com/user-attachments/assets/a9bb27f6-7f9b-4f94-a26b-42d7fa435554" />
<img width="1408" height="652" alt="image" src="https://github.com/user-attachments/assets/8fa44776-549d-4d3b-9fab-7c3f7b6b881d" />
<img width="1403" height="927" alt="image" src="https://github.com/user-attachments/assets/14180881-68db-4d61-8e09-c0f7f2a12dcd" />

## Lisans

MIT © LuckyHelper
