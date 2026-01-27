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