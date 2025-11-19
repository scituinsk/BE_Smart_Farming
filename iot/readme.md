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

### 2. Perintah sreaming data
```markdown
STREAMING_ON 

STREAMING_OFF
```

## IoT ke server
### 1. Mengirim status keberhasilan penyalaan selenoit
```json
{
    "device":"<auth_id>",
    "schedule":"<id_schedule>", // mengembalikan id schedule yang dikirim server untuk inisiasi
    "message":"Selenoit berhasil menyala" // pesan untuk ditampilkan ke log (opsional)
}
```

### 2. Mengirimkan data setiap sensor setiap 30 menit dan wajib mengirim data ketika mendapat perintah streaming <STREAMING_ON>
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

### 3. Menjaga koneksi agar tidak timeout (60s)
```json
{
    "device":"<auth_id>"
}
```