from django.db import models

class Contact(models.Model):
    email = models.EmailField(null=False, default="scit.uinsuka@gmail.com")
    website = models.CharField(max_length=255, blank=True, null=True, verbose_name="Domain website")
    github = models.CharField(max_length=255, blank=True, null=True, verbose_name="Username github")
    instagram = models.CharField(max_length=255, blank=True, null=True, verbose_name="Username instagram")
    linkedin = models.CharField(max_length=255, blank=True, null=True, verbose_name="Profil linkedin")
    whatsapp = models.CharField(max_length=50, blank=True, null=True, verbose_name="Contact admin scit")
    is_active = models.BooleanField(default=False, verbose_name="Aktifkan untuk menampilkanya saat get *[0]")

    def __str__(self):
        return f"Contact is_active = {self.is_active}"

class Terms(models.Model):
    title = models.CharField(max_length=255, verbose_name="Title")
    content = models.TextField(verbose_name="Content")
    is_active = models.BooleanField(default=False, verbose_name="Aktifkan untuk menampilkanya saat get *[0]")
    updated_at = models.DateTimeField(auto_now=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.title} is_active = {self.is_active}"
    
class FirmwareUpdate(models.Model):
    version = models.CharField(max_length=50, unique=True, help_text="Contoh: v1.0.1")
    file = models.FileField(upload_to='firmware_updates/')
    description = models.TextField(blank=True)
    is_active = models.BooleanField(default=True, help_text="Hanya firmware aktif yang akan di-download device")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"Firmware {self.version}"