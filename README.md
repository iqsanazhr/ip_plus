<p align="center">
  <img src="assets/logo.svg" alt="ip+ Logo" width="128" height="128" />
</p>

<h1 align="center">ip+</h1>

<p align="center">
  <b>Native 60fps iPhone Mirroring &amp; Control Platform for Windows 11 (iOS 27 Exclusive)</b>
</p>

<p align="center">
  <a href="https://python.org"><img src="https://img.shields.io/badge/Python-3.12-3776AB?style=for-the-badge&logo=python&logoColor=white" alt="Python Version" /></a>
  <a href="https://microsoft.com"><img src="https://img.shields.io/badge/Windows-10%20%2F%2011%20(64--bit)-0078D4?style=for-the-badge&logo=windows&logoColor=white" alt="Windows 11" /></a>
  <a href="https://developer.apple.com"><img src="https://img.shields.io/badge/Stream-60fps%20H.265%20(HEVC)-00F5D4?style=for-the-badge" alt="Video Stream" /></a>
  <a href="https://developer.microsoft.com/en-us/microsoft-edge/webview2/"><img src="https://img.shields.io/badge/Engine-Microsoft_WebView2-0078D4?style=for-the-badge&logo=microsoftedge&logoColor=white" alt="Frontend Engine" /></a>
  <a href="https://apple.com"><img src="https://img.shields.io/badge/iOS-27%20Only-10B981?style=for-the-badge&logo=apple&logoColor=white" alt="iOS Support" /></a>
  <a href="LICENSE"><img src="https://img.shields.io/badge/License-GPL--3.0-green?style=for-the-badge" alt="License" /></a>
</p>

<p align="center">
  Platform desktop native Windows modern berkinerja tinggi untuk <i>screen mirroring</i> dan kontrol penuh perangkat Apple iPhone melalui koneksi kabel USB berkecepatan tinggi tanpa kompresi atau latensi jaringan Wi-Fi.
</p>

---

Didesain dengan standar kriya tinggi (*high craft & design engineering*), sistem ini menghadirkan pengalaman visual sasis fisik **Apple Space Black Titanium**, kelengkungan kontinu **Apple $G^2$ Squircle**, pulau kamera **Dynamic Island** responsif berbasis rasio matematis, arsitektur *Single-Flight Gate* 60 FPS tanpa lag, serta peluncur native tanpa konsol CMD (**`ip+.exe`**) layaknya aplikasi desktop profesional komersial.

---

## <img src="assets/icons/layers.svg" width="22" height="22" align="center" /> Arsitektur Aplikasi & Infrastruktur

Sistem **ip+** dibangun dengan arsitektur hibrida decoupled yang memisahkan lapisan rendering antarmuka pengguna, jembatan window management Windows OS, dan komunikasi protokol USB perangkat keras Apple.

```mermaid
graph TB
    subgraph "Frontend Layer (Chromium WebView2)"
        A["Edge WebView2 Runtime"]
        B["Hardware Canvas (Retina Crisp 60fps)"]
        C["WebCodecs VideoDecoder (H.265 / HEVC)"]
        D["Dynamic Island & Fluid UI Controller"]
    end

    subgraph "Native Windows Subsystem (Python 3.12 / WinForms)"
        E["Native Winexe Launcher (ip+.exe)"]
        F["pywebview GUI Host (WindowApi)"]
        G["Win32 DWM & SetWindowRgn Engine"]
        H["Single-Flight Gate IPC Dispatcher"]
        I["Win32 Job Object Process Guard"]
    end

    subgraph "Hardware & Device Services"
        J["Local TCP Streaming Socket (127.0.0.1)"]
        K["pymobiledevice3 CoreDevice Bridge"]
        L["WinRT Bluetooth AudioPlaybackConnection"]
        M["Windows Media OCR Extractor"]
    end

    subgraph "Apple Physical Hardware"
        N["Physical iPhone (iOS 27 Only)"]
        O["Lightning / USB-C High-Speed Link"]
    end

    E --> F
    F --> A
    A --> B
    C --> B
    D --> B
    F --> G
    F --> H
    H --> A
    F --> I
    J --> C
    K --> J
    K --> N
    O --> K
    L --> N
    M --> A
```

### <img src="assets/icons/cpu.svg" width="18" height="18" align="center" /> Pola Arsitektur Utama
- **Zero-Copy WebCodecs H.265 Pipeline**: Paket NAL unit H.265 dialirkan langsung melalui socket loopback TCP berlatensi rendah ke WebCodecs `VideoDecoder` perangkat keras tanpa konversi bitmap perantara.
- **Win32 SetWindowRgn DWM Squircle Clipping**: Jendela aplikasi dipotong pada level kernel grafis Windows menggunakan kurva $G^2$ Squircle ($58\text{px}$ pada Portrait, $48\text{px}$ pada Landscape), memberikan $100\%$ transparansi sudut sempurna dan *click-through* alami di luar bodi iPhone.
- **Single-Flight Gate 60 FPS Resize**: Menggunakan mekanisme penguncian *Promise-based in-flight* pada antrean IPC pywebview sehingga perbesaran dan pengecilan jendela merespons koordinat mouse secara instan tanpa lag backlog atau *thread explosion*.
- **Zero-Console Winexe Subsystem**: Menggunakan wrapper binary C# yang dikompilasi dengan `/target:winexe` dan memanggil `pythonw.exe` (`IMAGE_SUBSYSTEM_WINDOWS_GUI`) secara *hidden*, mengeliminasi jendela hitam konsol CMD secara total.
- **Win32 Job Object Lifecycle**: Menjaga semua proses anak (audio worker, server, socket) di dalam kernel Windows Job Object dengan bendera `JOB_OBJECT_LIMIT_KILL_ON_JOB_CLOSE`, menjamin nol proses tertinggal (*zero zombie processes*) saat jendela ditutup.

---

## <img src="assets/icons/workflow.svg" width="22" height="22" align="center" /> Alur Kerja Streaming & Kontrol Input (Flow Pipeline)

Diagram berikut menjelaskan siklus tertutup (*closed-loop lifecycle*) dari penerimaan video layar hingga injeksi sentuhan kapasitif mouse:

```mermaid
sequenceDiagram
    participant P as Physical iPhone
    participant U as USB CoreDevice / RemoteXPC
    participant S as Local Streaming Server
    participant W as WebView2 (Canvas & WebCodecs)
    participant K as Win32 DWM & Input Engine
    participant C as PC User (Mouse / Keyboard)

    Note over P,U: Koneksi USB Aktif
    P->>U: Raw H.265 NAL Stream (60fps)
    U->>S: TCP Loopback Socket (No-Delay)
    S->>W: VideoDecoder Decode Chunk
    W->>W: Render Frame to Canvas (Retina Crisp)
    
    C->>W: Mouse Move / Click / Trackpad Scroll
    W->>K: Koordinat Sentuh Terkalibrasi (1:1 Aspect)
    K->>U: USB HID Capacitive Touch Injection
    U->>P: iOS SpringBoard Touch Execution
    
    Note over C,K: Shortcut Alt+B / Alt+C / Alt+D
    C->>K: Alt+B (Grab Link) / Alt+C (Smart OCR)
    K->>W: Ekstraksi Teks / Link Instagram
    W->>C: Simpan ke Windows Win32 Clipboard
```

---

## <img src="assets/icons/zap.svg" width="22" height="22" align="center" /> Fitur Unggulan

### 1. <img src="assets/icons/smartphone.svg" width="18" height="18" align="center" /> Bodi Fisik Real iPhone & Dynamic Island Responsif
- **Apple CAD Titanium Space Black Chassis**: Bodi ponsel berketebalan presisi $12\text{px}$ Space Black Titanium dengan lengkungan baku Apple $G^2$ Squircle ($58\text{px}$ Portrait, $48\text{px}$ Landscape).
- **Proportional Dynamic Island Scaling**: Pulau notch kamera TrueDepth FaceID dan sensor depan secara dinamis membesar dan mengecil mengikuti skala jendela menggunakan perhitungan matematis `vw` dan `vh` terisolasi, lengkap dengan animasi ekspansi hover mulus (durasi $\le 200\text{ms}$).
- **Anti-Gepeng Strict Aspect Ratio Locking**: Rasio aspek terkunci mutlak pada rasio native iPhone ($1179 / 2556 \approx 0.4612$) dengan kompensasi bezel fisik $24\text{px}$, menjamin proporsi layar tidak pernah melar atau penyek saat ditarik.
- **Center Screen Precision**: Jendela utama dan jendela pengaturan secara otomatis terbuka tepat di titik tengah (*center screen*) monitor kerja aktif Anda.

### 2. <img src="assets/icons/zap.svg" width="18" height="18" align="center" /> Zero-Copy 60fps H.265 (HEVC) Streaming + Smart Motion PLI
- Streaming video langsung dari chip enkoder hardware iPhone ke GPU Windows melalui Edge WebView2 WebCodecs dengan latensi mendekati nol.
- Dilengkapi **Smart Motion PLI Keyframe Booster** ($180\text{ms}$ pasca-swipe) yang menjaga ketajaman teks dan gambar selama transisi animasi atau navigasi folder cepat.

### 3. <img src="assets/icons/terminal.svg" width="18" height="18" align="center" /> Zero-Console Native Desktop Launcher (`ip+.exe`)
- Dijalankan langsung melalui file biner `ip+.exe` yang menargetkan subsistem Windows GUI.
- Tidak ada jendela hitam Command Prompt (`cmd.exe`) atau konsol Python yang berkedip di layar, memberikan estetika aplikasi komersial berkelas.

### 4. <img src="assets/icons/rotate.svg" width="18" height="18" align="center" /> 37-Scenario Smart Auto-Rotate (`Alt+H`)
- Mendeteksi orientasi layar secara otomatis: langsung berputar ke **270° Widescreen Landscape** (dengan pemetaan sentuh terbalik 1:1) saat membuka game atau video layar penuh.
- Tetap stabil pada mode **0° Portrait** saat berada di iOS Home Screen, folder aplikasi, WhatsApp, TikTok, atau Instagram.

### 5. <img src="assets/icons/link.svg" width="18" height="18" align="center" /> 1-Click Social Link Grabber (`Alt+B`) & Multi-Paragraph OCR (`Alt+C`)
- **1-Click Grab Link (`Alt+B`)**: Menyalin tautan postingan, Reels, atau Threads langsung dari layar iPhone ke Clipboard Windows hanya dalam $\approx 1.3$ detik tanpa perlu membuka menu bagikan.
- **Multi-Paragraph Smart OCR (`Alt+C`)**: Mengekstrak teks dari gambar, percakapan WhatsApp, atau catatan Apple Notes dengan mempertahankan susunan paragraf asli menggunakan Windows Media OCR.

### 6. <img src="assets/icons/mouse.svg" width="18" height="18" align="center" /> Kontrol Kapasitif USB HID 1:1 & Trackpad Dua Jari
- Kontrol sentuh mulus dengan dukungan klik, tahan, seret (*drag*), geser (*swipe*), dan scrolling halus dua jari pada trackpad laptop.
- Meneruskan shortcut pengetikan native iOS (`Ctrl+A`, `Ctrl+C`, `Ctrl+V`, `Ctrl+X`, `Ctrl+Z`).

### 7. <img src="assets/icons/moon.svg" width="18" height="18" align="center" /> Physical OLED Stealth Dim 0% (`Alt+D`) & Remote PIN Unlock (`Alt+U`)
- Menurunkan kecerahan layar iPhone fisik menjadi $0\%$ (gelap total di meja) untuk menjaga privasi dan menjaga suhu baterai tetap dingin selama *mirroring*.
- Membangunkan layar dan memasukkan kode PIN secara otomatis via USB HID dengan shortcut `Alt+U`.

### 8. <img src="assets/icons/settings.svg" width="18" height="18" align="center" /> Jendela Pengaturan Modern (macOS Style)
- Jendela pengaturan mandiri (*standalone window*) terpisah bergaya macOS Ventura/Sonoma dengan tab navigasi bersih, pencarian shortcut instan, dan konfigurasi performa.

---

## <img src="assets/icons/code.svg" width="22" height="22" align="center" /> Tech Stack & Ketergantungan

| Layer | Teknologi & Komponen | Deskripsi & Peran |
| :--- | :--- | :--- |
| **Desktop Launcher** | C# 5.0 / .NET Framework 4.0 (`/target:winexe`) | Biner native `ip+.exe` tanpa konsol CMD |
| **GUI Framework** | Python 3.12, `pywebview` 5.x, WinForms | Jembatan windowing frameless berakselerasi hardware |
| **Window Compositor** | Windows DWM (`dwmapi.dll`, `user32.dll`, `gdi32.dll`) | Transparansi per-pixel, DWM acrylic & squircle region |
| **Frontend Web** | HTML5, Vanilla JavaScript (ES2022), CSS3 Modern | Antarmuka bodi iPhone, Dynamic Island, dan settings |
| **Rendering Engine** | Microsoft Edge WebView2 (Chromium Blink) | Rendering hardware canvas 60 FPS |
| **Video Decoding** | WebCodecs API (`VideoDecoder` H.265 / HEVC) | Dekoder video akselerasi GPU perangkat keras |
| **USB Communication** | `pymobiledevice3` (CoreDevice, RemoteXPC) | Protokol penghubung USB data iPhone |
| **Audio Routing** | WinRT `AudioPlaybackConnection` (A2DP Bluetooth Sink) | Penerima audio nirkabel berlatensi rendah ke speaker PC |
| **OCR Engine** | Windows Media OCR (`Windows.Media.Ocr`) | Pemindai teks multi-bahasa dari canvas video |

---

## <img src="assets/icons/git-fork.svg" width="22" height="22" align="center" /> Garis Keturunan & Atribusi Open-Source (Open-Source Lineage & Credits)

Proyek **ip+** merupakan hasil pengembangan, pembaruan, dan refaktorisasi terbuka yang berdiri di atas fondasi karya luar biasa komunitas open-source:

- **Pembuat Awal & Arsitek Proyek Fondasi**:
  - **Kelvin Daniyar** ([@kelvindaniyar](https://github.com/kelvindaniyar)) — Pencipta dan pengembang awal **iPhone Link v2.0** yang merancang mesin streaming 60fps H.265, Smart Motion PLI, Smart Auto-Rotate 37 skenario, dan integrasi shortcut iOS.
  - **teyboxv1** ([teyboxv1/pane-iphone-mirror-windows](https://github.com/teyboxv1/pane-iphone-mirror-windows)) — Pencetus proyek sumber terbuka asli *Pane iPhone Mirror for Windows*.
  - **Doron Zavelevsky** ([pymobiledevice3](https://github.com/doronz88/pymobiledevice3)) — Arsitek pustaka protokol Apple CoreDevice dan RemoteXPC via USB.

- **Pengembang & Penyempurna `ip+`**:
  - **Iqsan Azhar** ([@iqsanazhr](https://github.com/iqsanazhr)) — Melakukan refaktorisasi total arsitektur bodi fisik:
    - Merancang sasis fisik $12\text{px}$ Space Black Titanium dengan kelengkungan kontinu Apple $G^2$ Squircle ($58\text{px}$ Portrait, $48\text{px}$ Landscape).
    - Membangun pulau kamera **Dynamic Island** responsif berbasis *fluid scaling* (`vw` & `vh`) dengan rasio proporsional 1:1.
    - Mengimplementasikan arsitektur *Single-Flight Gate* 60 FPS untuk eliminasi lag pada *window resizing*.
    - Menghadirkan peluncur native tanpa jendela konsol CMD (**`ip+.exe`**).
    - Menyempurnakan sistem penempatan jendela *center screen* untuk jendela utama dan jendela pengaturan.
    - Menjamin penguncian rasio aspek fisik anti-gepeng dengan kompensasi bezel $24\text{px}$.

---

## <img src="assets/icons/keyboard.svg" width="22" height="22" align="center" /> Referensi Shortcut Keyboard

| Shortcut | Aksi | Deskripsi |
| :---: | :--- | :--- |
| **`Alt + B`** | **<img src="assets/icons/link.svg" width="16" height="16" align="center" /> 1-Click Grab Link** | Mengekstrak URL Instagram (Feeds/Reels) atau Threads langsung ke Clipboard PC dalam $\approx 1.3\text{ detik}$. |
| **`Alt + C`** | **<img src="assets/icons/file-text.svg" width="16" height="16" align="center" /> Smart OCR Copy Text** | Menjalankan Windows Media OCR pada layar iPhone dan menyalin teks multi-paragraf ke Clipboard PC. |
| **`Alt + V`** | **<img src="assets/icons/clipboard.svg" width="16" height="16" align="center" /> Paste PC Text to iPhone** | Mengetikkan/menginjeksikan teks dari Clipboard Windows langsung ke kolom input iOS yang aktif. |
| **`Alt + H`** | **<img src="assets/icons/rotate.svg" width="16" height="16" align="center" /> Toggle Landscape (270°)** | Beralih antara mode Portrait vertikal ($0^\circ$) dan Landscape gaming horizontal ($270^\circ$). |
| **`Alt + D`** | **<img src="assets/icons/moon.svg" width="16" height="16" align="center" /> Toggle USB Stealth Dim** | Mematikan layar fisik iPhone ke $0\%$ (gelap di meja) atau mengembalikan kecerahan normal $\approx 25\%$. |
| **`Alt + U`** | **<img src="assets/icons/unlock.svg" width="16" height="16" align="center" /> Remote Wake & Unlock** | Membangunkan iPhone, melewati layar Face ID, dan menginput PIN keamanan via USB HID. |
| **`Alt + L`** | **<img src="assets/icons/lock.svg" width="16" height="16" align="center" /> Lock iPhone Screen** | Mengunci layar iPhone dan memasukkannya ke mode standby dengan aman. |
| **`Alt + S`** / **`Ctrl + ,`** | **<img src="assets/icons/settings.svg" width="16" height="16" align="center" /> Buka Pengaturan (Settings)** | Membuka jendela pengaturan modern ip+ bergaya macOS di tengah layar. |
| **`Ctrl + K`** | **<img src="assets/icons/keyboard.svg" width="16" height="16" align="center" /> Toggle Virtual Keyboard** | Menampilkan atau menyembunyikan keyboard virtual iOS pada layar ponsel. |
| **`Ctrl + A / C / V / X / Z`** | **<img src="assets/icons/code.svg" width="16" height="16" align="center" /> Native iOS Editing** | Mengirimkan perintah edit native iOS (`Cmd+A`, `Cmd+C`, `Cmd+V`, `Cmd+X`, `Cmd+Z`). |
| **`Ctrl + Scroll`** / **`Ctrl + +/-`** | **<img src="assets/icons/search.svg" width="16" height="16" align="center" /> Zoom & Skala Jendela** | Memperbesar atau memperkecil ukuran jendela dengan rasio aspek $1:1$ terkunci. |

---

## <img src="assets/icons/rocket.svg" width="22" height="22" align="center" /> Panduan Memulai Cepat (Quick Start)

### <img src="assets/icons/check.svg" width="18" height="18" align="center" /> Kebutuhan Sistem
1. **Sistem Operasi**: Windows 10 atau Windows 11 (64-bit).
2. **Perangkat**: Apple iPhone yang menjalankan **iOS 27 saja** (eksklusif iOS 27, terverifikasi penuh pada iOS 27.0.1). Versi iOS selain 27 tidak didukung.
3. **Kabel Koneksi**: Kabel data USB-to-Lightning atau USB-C ke PC.
4. **Driver**: Apple Mobile Device Support / iTunes (atau terpasang otomatis via Windows Update).

### <img src="assets/icons/play.svg" width="18" height="18" align="center" /> Cara Menjalankan
1. Hubungkan iPhone ke PC menggunakan kabel data USB dan pilih **"Percayai Komputer Ini"** (*Trust This Computer*) pada layar iPhone Anda.
2. Jalankan aplikasi melalui salah satu cara berikut:
   - **Klik Ganda `ip+.exe`** di folder aplikasi (atau icon **`ip+`** di Desktop Anda).
   - Aplikasi akan langsung melayang di tengah layar Anda tanpa jendela konsol hitam CMD.

---

## <img src="assets/icons/shield.svg" width="22" height="22" align="center" /> Lisensi

Proyek ini didistribusikan di bawah lisensi **GNU General Public License v3.0 (GPL-3.0)** sesuai dengan silsilah dan lisensi komponen dasar open-source yang digunakan. Silakan lihat berkas [LICENSE](LICENSE) untuk ketentuan hukum selengkapnya.

---

<p align="center">
  <b>ip+</b> &bull; Crafted with precision by <b>Iqsan Azhar</b> &bull; Built on the open-source shoulders of <b>Kelvin Daniyar</b> &amp; <b>teyboxv1</b>
</p>
