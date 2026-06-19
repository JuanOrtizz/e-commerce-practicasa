import os
from django.contrib.auth import get_user_model
from django.db.utils import OperationalError

try:
    # get_user_model() es vital acá, porque trae tu modelo 'Usuarios' automáticamente
    User = get_user_model()

    # Traemos las variables de entorno nuevas
    email = os.getenv("DJANGO_SUPERUSER_EMAIL")
    password = os.getenv("DJANGO_SUPERUSER_PASSWORD")
    # Le ponemos un valor por defecto ("Admin") por si te olvidas de poner la variable
    nombre = os.getenv("DJANGO_SUPERUSER_NOMBRE", "Admin")

    # Verificamos que al menos el email y el password existan en el .env
    if not email or not password:
        print("Error: Faltan las variables DJANGO_SUPERUSER_EMAIL o DJANGO_SUPERUSER_PASSWORD en el entorno.")

    # Filtramos por email, no por username
    if not User.objects.filter(email=email).exists():
        # Llamamos al create_superuser de UsuarioManager
        User.objects.create_superuser(
            email=email,
            nombre_completo=nombre,
            password=password,
        )
        print(f"Superusuario creado exitosamente con el email: {email}")
    else:
        print(f"El superusuario con email {email} ya existe. Omitiendo creación.")

except OperationalError:
    print("La base de datos aún no está lista o faltan correr las migraciones. Intenta de nuevo más tarde.")
except Exception as e:
    # Atrapamos cualquier otro error (ej: si el modelo no tiene el campo nombre_completo)
    print(f"Ocurrió un error inesperado al crear el superusuario: {e}")