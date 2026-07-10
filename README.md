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

## Lisans

MIT © LuckyHelper
