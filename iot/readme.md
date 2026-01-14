# Format pesan antara IoT dan Server

## Server ke IoT
### 1. Menyalakan Selenoit 1 selama 30 detik dan menonaktifkan selenoit 2 dan 3 (dihitung berdasarkan sequential)

```markdown
check=0
relay=1,2,3 (gpio mana) 
time=6 (detik) 
schedule=<id_schedule>
sequential=2 (pin/sequential)

Mendapatkan data dari sensor
check=1
```

### 2. Perintah untuk meminta data sensor
```markdown
GET_SENSOR
```

## IoT ke server
### 1. Mengirim Log Device ke server (perintah-feedback)
```json
{
    "device":"<auth_id>",
    "device_logs":{
        "type": "value", // untuk menentukan logo di frontend (default = modul)
        "name": "value", // untuk menentukan judul di frontend (diisi otomatis)
        "data": {
            // isi dengan format json
            "message": "Modul IoT Kembali On"
        }
    }
}
```

### 2. Mengirim Perubahan Pin Via Log Device ke server (schedule)
```json
{
    "device":"<auth_id>",
    "device_logs":{
        "id":<log_id>, // Log id Wajib
        "data": {
            "pins": [
                {"pin": 6, "start": "10:00", "end": "10:10"},
                {"pin": 7, "start": "10:00", "end": "10:10"},
                {"pin": 8, "start": "10:10", "end": "10:20"}
            ]
        }
    }
}
```

### 3. Mengirimkan data setiap sensor setiap 30 menit dan wajib mengirim data ketika mendapat perintah streaming <STREAMING_ON>
```json
{
    "device":"<auth_id>", // didapat dari variable yang ditanam di modul iot
    "temperature_data":[
        {"name": "value", "data":45}
        {"name": "value", "data":45}
        {"name": "value", "data":45}
    ], // dalam celcius
    "humidity_data":[
        {"name": "value", "data":45}
    ], // persentase
    "battery_data":[
        {"name": "value", "data":45}
    ], // presentase
    "water_level_data": [
        {"name": "value", "data":45}
    ] //presentase
    // tambah sesuai keperluan
}
```

### 4. Menjaga koneksi agar tidak timeout (60s)
```json
{
    "device":"<auth_id>"
}
```