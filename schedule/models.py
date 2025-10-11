from django.db import models
from django.contrib.auth.models import User
from iot.models import Modul

class Alarm(models.Model):
    """
    Mewakili satu entitas alaram yang diatur oleh pengguna.
    """
    # Relasi ke modul yang memiliki alaram ini
    modul = models.ForeignKey(Modul, on_delete=models.CASCADE, related_name='alarms', help_text="Modul pemilik alaram")

    # Informasi dasar alaram
    label = models.CharField(max_length=100, blank=True, help_text="Label atau nama untuk alaram")
    time = models.TimeField(help_text="Waktu alaram akan berbunyi (HH:MM:SS)")
    is_active = models.BooleanField(default=True, help_text="Status alaram aktif atau tidak")
    celery_task_id = models.CharField(max_length=255, blank=True, null=True, editable=False, help_text="ID dari tugas Celery yang dijadwalkan di background")

    # Opsi pengulangan
    repeat_monday = models.BooleanField(default=False)
    repeat_tuesday = models.BooleanField(default=False)
    repeat_wednesday = models.BooleanField(default=False)
    repeat_thursday = models.BooleanField(default=False)
    repeat_friday = models.BooleanField(default=False)
    repeat_saturday = models.BooleanField(default=False)
    repeat_sunday = models.BooleanField(default=False)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['time']
        verbose_name = "Alaram"
        verbose_name_plural = "Daftar Alaram"

    def __str__(self):
        return f"{self.label or 'Alaram'} - {self.time.strftime('%H:%M')} ({self.modul.serial_id})"

    @property
    def is_repeating(self):
        """Properti untuk mengecek apakah alaram ini memiliki jadwal pengulangan."""
        return any([
            self.repeat_monday, self.repeat_tuesday, self.repeat_wednesday,
            self.repeat_thursday, self.repeat_friday, self.repeat_saturday,
            self.repeat_sunday
        ])