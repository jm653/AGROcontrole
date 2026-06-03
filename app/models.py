from django.db import models
from django.contrib.auth.models import AbstractUser


class Usuario(AbstractUser):

    TIPOS = (
        ('admin', 'Administrador'),
        ('produtor', 'Produtor'),
        ('funcionario', 'Funcionário'),
    )

    tipo = models.CharField(
        max_length=20,
        choices=TIPOS
    )

    @property
    def is_admin(self):
        return self.tipo == 'admin'

    @property
    def is_produtor(self):
        return self.tipo == 'produtor'

    @property
    def is_funcionario(self):
        return self.tipo == 'funcionario'

    def __str__(self):
        return self.username


class Propriedade(models.Model):

    produtor = models.ForeignKey(
        Usuario,
        on_delete=models.CASCADE,
        limit_choices_to={'tipo': 'produtor'}
    )

    nome = models.CharField(max_length=100)

    cidade = models.CharField(max_length=100)

    hectares = models.DecimalField(
        max_digits=10,
        decimal_places=2
    )

    def __str__(self):
        return self.nome


class Lavoura(models.Model):

    propriedade = models.ForeignKey(
        Propriedade,
        on_delete=models.CASCADE
    )

    nome = models.CharField(max_length=100)

    variedade = models.CharField(max_length=100)

    area = models.DecimalField(
        max_digits=10,
        decimal_places=2
    )

    data_plantio = models.DateField()

    def __str__(self):
        return self.nome


class LoteDeCafe(models.Model):

    ETAPAS = (
        ('plantio', 'Plantio'),
        ('colheita', 'Colheita'),
        ('secagem', 'Secagem'),
        ('armazenamento', 'Armazenamento'),
        ('torra', 'Torra'),
        ('qualidade', 'Qualidade'),
        ('venda', 'Venda'),
    )

    lavoura = models.ForeignKey(
        Lavoura,
        on_delete=models.CASCADE
    )

    responsavel = models.ForeignKey(
        Usuario,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='lotes_responsaveis',
        limit_choices_to={'tipo': 'funcionario'}
    )

    codigo = models.CharField(
        max_length=50,
        unique=True
    )

    quantidade_sacas = models.IntegerField()

    qualidade = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=0
    )

    preco_saca = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0
    )

    etapa = models.CharField(
        max_length=30,
        choices=ETAPAS,
        default='plantio'
    )

    observacoes = models.TextField(
        blank=True,
        null=True
    )

    criado_em = models.DateTimeField(
        auto_now_add=True
    )

    data_atualizacao = models.DateTimeField(
        auto_now=True
    )

    def valor_total(self):
        return self.quantidade_sacas * self.preco_saca

    def __str__(self):
        return self.codigo


class RegistroOperacional(models.Model):

    LoteDeCafe = models.ForeignKey(
        LoteDeCafe,
        on_delete=models.CASCADE
    )

    funcionario = models.ForeignKey(
        Usuario,
        on_delete=models.CASCADE,
        limit_choices_to={'tipo': 'funcionario'}
    )

    descricao = models.TextField()

    data = models.DateTimeField(
        auto_now_add=True
    )

    etapa = models.CharField(
    max_length=30
)

    local = models.CharField(
        max_length=100,
        blank=True,
        null=True
    )

    def __str__(self):
        return f"{self.funcionario.username} - {self.data}"
    

class MovimentacaoFinanceira(models.Model):

    TIPOS = (
        ('LUCRO', 'Lucro'),

        ('DESPESA', 'Despesa'),
    )

    produtor = models.ForeignKey(
        Usuario,
        on_delete=models.CASCADE
    )

    titulo = models.CharField(
        max_length=200
    )

    valor = models.DecimalField(
        max_digits=10,
        decimal_places=2
    )

    tipo = models.CharField(
        max_length=20,
        choices=TIPOS
    )

    descricao = models.TextField(
        blank=True,
        null=True
    )

    criado_em = models.DateTimeField(
        auto_now_add=True
    )

    def __str__(self):

        return self.titulo
    
class FuncionarioPropriedade(models.Model):

    funcionario = models.ForeignKey(
        Usuario,
        on_delete=models.CASCADE,
        limit_choices_to={'tipo': 'funcionario'}
    )

    propriedade = models.ForeignKey(
        Propriedade,
        on_delete=models.CASCADE
    )

    criado_em = models.DateTimeField(
        auto_now_add=True
    )

    class Meta:
        unique_together = ('funcionario', 'propriedade')

    def __str__(self):
        return f"{self.funcionario.username} - {self.propriedade.nome}"
    
class Notificacao(models.Model):

    usuario = models.ForeignKey(
        Usuario,
        on_delete=models.CASCADE
    )

    titulo = models.CharField(
        max_length=200
    )

    mensagem = models.TextField()

    lida = models.BooleanField(
        default=False
    )

    criada_em = models.DateTimeField(
        auto_now_add=True
    )

    def __str__(self):
        return self.titulo
    
    
class Relatorio(models.Model):

    nome = models.CharField(max_length=100)

    descricao = models.TextField()

    criado_em = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.nome
    
class Equipamento(models.Model):

    nome = models.CharField(max_length=100)

    status = models.CharField(max_length=50)

    def __str__(self):
        return self.nome
    
class Fornecedor(models.Model):

    nome = models.CharField(max_length=100)

    telefone = models.CharField(max_length=20)

    def __str__(self):
        return self.nome