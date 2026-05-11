from django.contrib.auth.models import AbstractUser
from django.db import models

class Usuario(AbstractUser):
    TIPO_CHOICES = (
        ('admin', 'Administrador'),
        ('produtor', 'Produtor'),
        ('funcionario', 'Funcionário'),
    )
    tipo = models.CharField(max_length=20, choices=TIPO_CHOICES)