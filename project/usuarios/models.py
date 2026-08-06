from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.db import models

class UsuarioManager(BaseUserManager):
    def get_by_natural_key(self, email):
        return self.get(**{self.model.USERNAME_FIELD: email.strip().lower()})

    def create_user(self, email, nombre_completo, password=None, **extra_fields):
        if not email:
            raise ValueError("El email es obligatorio")
        email = self.normalize_email(email)
        user = self.model(email=email, nombre_completo=nombre_completo, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, nombre_completo, password=None, **extra_fields):
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        extra_fields.setdefault("tipo", UsuarioModel.Tipos.SUPERUSER)
        return self.create_user(email, nombre_completo, password, **extra_fields)


class UsuarioModel(AbstractBaseUser, PermissionsMixin):
    class Tipos(models.TextChoices):
        SUPERUSER = "superuser", "Superuser"
        ADMINISTRADOR_TIENDA = "administrador_tienda", "Administrador Tienda"
        CLIENTE = "cliente", "Cliente"

    email = models.EmailField(unique=True, db_index=True)
    nombre_completo = models.CharField(max_length=150)
    tipo = models.CharField(max_length=20, choices=Tipos.choices, default=Tipos.CLIENTE)
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    date_joined = models.DateTimeField(auto_now_add=True)

    objects = UsuarioManager()

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ["nombre_completo"]

    class Meta:
        db_table = "usuarios"
        verbose_name = 'Usuario'
        verbose_name_plural = 'Usuarios'

    def save(self, *args, **kwargs):
        self.email = self.email.lower()
        super().save(*args, **kwargs)

    def __str__(self):
        return self.email