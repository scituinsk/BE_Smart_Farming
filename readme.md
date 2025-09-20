# Smart Farming SCIT
Ini merupakan project backend dari smart farming SCIT yang dikembangkan oleh [`arbath@teknohole.com`](mailto:arbath@teknohole.com)

## Dokumentasi API
Silahkan lihat di [Postman](https://www.postman.com/teknohole/workspace/smart-farming-scit)

## Peran Komunikasi

Setiap bagian memiliki peran yang spesifik:

1.  **Perangkat IoT (ESP32 / Simulator Postman)**: Ini adalah **"Agen di Lapangan"**. Tugasnya adalah mengumpulkan data (sensor) atau melakukan aksi (menyalakan lampu/relay).

2.  **Broker MQTT (Mosquitto)**: Ini adalah **"Sistem Kurir" atau "Kantor Pos"** super efisien. Semua pesan dari dan untuk agen lapangan harus melewati kantor pos ini. Ia tidak peduli isi pesannya, hanya memastikan pesan sampai ke alamat (topic) yang benar.

3.  **Backend Django**: Inilah **"Pusat Komando"**
    * **Subscriber MQTT ([`mqtt_subscribe.py`](/smartfarming/management\commands\mqtt_subscribe.py))**: Bertugas sebagai **"Operator Radio Penerima"**. Ia terus-menerus mendengarkan semua laporan yang masuk dari agen lapangan melalui sistem kurir (MQTT).
    * **Django Channels ([Consumer](/iot/consumers.py) & [WebSocket](/smartfarming/asgi.py))**: Bertugas sebagai **"Operator Ruang Kontrol"**. Ia berkomunikasi langsung dengan Kamu (Manajer) melalui layar monitor canggih (WebSocket di browser).

4.  **Frontend (Browser / Postman WebSocket)**: Ini adalah Kamu, **"Manajer"**, yang duduk di ruang kontrol. Kamu bisa melihat semua data yang masuk dan memberikan perintah.

5.  **Redis**: Ini adalah **"Papan Pengumuman Internal"** di dalam Pusat Komando. Ini memungkinkan Operator Radio (Subscriber MQTT) yang berada di satu ruangan untuk dengan cepat memberikan informasi kepada Operator Ruang Kontrol (Channels) yang berada di ruangan lain tanpa harus bertemu langsung.

---
## Alur Komunikasi

Komunikasi terjadi dalam dua alur utama yang berjalan secara bersamaan.

### Alur 1: Mengontrol Perangkat (Perintah dari Manajer ke Agen)

Ini adalah alur "dari atas ke bawah".

1.  **Manajer (Frontend)**: Kamu menekan tombol "ON" di browser. Perintah ini dikirim melalui koneksi **WebSocket**.
2.  **Operator Ruang Kontrol (Channels Consumer)**: Menerima perintah `{"command": "ON"}` dari WebSocket.
3.  **Pusat Komando (Fungsi Django)**: Operator Ruang Kontrol memanggil fungsi internal untuk mengirim perintah keluar.
4.  **Sistem Kurir (MQTT)**: Perintah tersebut di-**publish** ke alamat spesifik, misalnya `devices/postman/control`.
5.  **Agen di Lapangan (ESP32)**: Perangkat yang sudah berlangganan (`subscribe`) alamat tersebut akan langsung menerima perintah dan menyalakan LED.

**Singkatnya: Browser → WebSocket → Django → MQTT → ESP32**

---
### Alur 2: Memonitor Data (Laporan dari Agen ke Manajer)

Ini adalah alur "dari bawah ke atas".

1.  **Agen di Lapangan (ESP32)**: Sensor membaca data temperatur. Perangkat membuat laporan dalam format JSON, misalnya `{"temperature": 29.5}`.
2.  **Sistem Kurir (MQTT)**: Laporan tersebut di-**publish** ke alamat laporan, misalnya `devices/postman/data`.
3.  **Operator Radio (Subscriber MQTT)**: Operator yang selalu mendengarkan alamat tersebut menerima laporan dari MQTT.
4.  **Papan Pengumuman Internal (Redis)**: Operator Radio tidak langsung berteriak ke Operator Ruang Kontrol. Ia menempelkan laporan tersebut di papan pengumuman Redis untuk grup [`device_postman`](/smartfarming/management\commands\mqtt_subscribe.py#L42).
5.  **Operator Ruang Kontrol (Channels Consumer)**: Karena ia memantau papan pengumuman untuk grup itu, ia langsung melihat laporan baru dan mengambilnya.
6.  **Manajer (Frontend)**: Operator Ruang Kontrol menampilkan data laporan tersebut di layar monitor Kamu (mengirimnya melalui **WebSocket** ke browser), dan Kamu melihat temperatur berubah secara real-time.

**Singkatnya: ESP32 → MQTT → Django Subscriber → Redis → Django Channels → WebSocket → Browser**