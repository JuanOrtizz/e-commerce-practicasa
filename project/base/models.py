from django.db import models

# Create your models here.
class ConsultaModel(models.Model):
    class Estados(models.TextChoices):
        PENDIENTE = 'pendiente', 'Pendiente'
        RESUELTA = 'resuelta', 'Resuelta'

    nombre = models.CharField(max_length=100)
    email = models.EmailField()
    telefono = models.CharField(max_length=20)
    mensaje = models.TextField()
    fecha_y_hora = models.DateTimeField(auto_now_add=True, db_index=True)
    estado = models.CharField(max_length=20, choices=Estados.choices, default=Estados.PENDIENTE)

    def __str__(self):
        return self.nombre

    class Meta:
        db_table = 'consultas'
        ordering = ['-fecha_y_hora']
        verbose_name = 'Consulta'
        verbose_name_plural = 'Consultas'
