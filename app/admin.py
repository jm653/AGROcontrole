from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from .models import (
    Usuario,
    Propriedade,
    Lavoura,
    LoteDeCafe,
    RegistroOperacional,
    MovimentacaoFinanceira,
    FuncionarioPropriedade,
    Notificacao,
    Relatorio,
    Equipamento,
    Fornecedor
)


# ==========================
# USUÁRIOS
# ==========================

@admin.register(Usuario)
class CustomUserAdmin(UserAdmin):

    fieldsets = UserAdmin.fieldsets + (
        (
            'Tipo de Usuário',
            {
                'fields': ('tipo',)
            }
        ),
    )

    add_fieldsets = UserAdmin.add_fieldsets + (
        (
            'Tipo de Usuário',
            {
                'fields': ('tipo',)
            }
        ),
    )

    list_display = (
        'username',
        'email',
        'tipo',
        'is_active'
    )

    list_filter = (
        'tipo',
        'is_active'
    )


# ==========================
# NOTIFICAÇÕES
# ==========================

@admin.register(Notificacao)
class NotificacaoAdmin(admin.ModelAdmin):

    list_display = (
        'titulo',
        'usuario',
        'lida',
        'criada_em'
    )

    list_filter = (
        'lida',
        'criada_em'
    )

    search_fields = (
        'titulo',
        'mensagem',
        'usuario__username'
    )

    ordering = (
        '-criada_em',
    )

    date_hierarchy = 'criada_em'

    exclude = (
        'lida',
    )


# ==========================
# PROPRIEDADES
# ==========================

@admin.register(Propriedade)
class PropriedadeAdmin(admin.ModelAdmin):

    list_display = (
        'nome',
        'produtor',
        'cidade',
        'hectares'
    )

    search_fields = (
        'nome',
        'cidade'
    )


# ==========================
# LAVOURAS
# ==========================

@admin.register(Lavoura)
class LavouraAdmin(admin.ModelAdmin):

    list_display = (
        'nome',
        'propriedade',
        'variedade',
        'area'
    )

    search_fields = (
        'nome',
        'variedade'
    )


# ==========================
# LOTES
# ==========================

@admin.register(LoteDeCafe)
class LoteDeCafeAdmin(admin.ModelAdmin):

    list_display = (
        'codigo',
        'lavoura',
        'responsavel',
        'etapa',
        'quantidade_sacas'
    )

    list_filter = (
        'etapa',
    )

    search_fields = (
        'codigo',
    )


# ==========================
# REGISTROS OPERACIONAIS
# ==========================

@admin.register(RegistroOperacional)
class RegistroOperacionalAdmin(admin.ModelAdmin):

    list_display = (
        'funcionario',
        'etapa',
        'data'
    )

    list_filter = (
        'etapa',
    )


# ==========================
# FINANCEIRO
# ==========================

@admin.register(MovimentacaoFinanceira)
class MovimentacaoFinanceiraAdmin(admin.ModelAdmin):

    list_display = (
        'titulo',
        'produtor',
        'tipo',
        'valor',
        'criado_em'
    )

    list_filter = (
        'tipo',
        'criado_em'
    )

    search_fields = (
        'titulo',
        'descricao',
        'produtor__username'
    )

    ordering = (
        '-criado_em',
    )

    list_per_page = 20

    date_hierarchy = 'criado_em'


# ==========================
# FUNCIONÁRIO X PROPRIEDADE
# ==========================

@admin.register(FuncionarioPropriedade)
class FuncionarioPropriedadeAdmin(admin.ModelAdmin):

    list_display = (
        'funcionario',
        'propriedade',
        'criado_em'
    )


# ==========================
# RELATÓRIOS
# ==========================

@admin.register(Relatorio)
class RelatorioAdmin(admin.ModelAdmin):

    list_display = (
        '__str__',
    )


# ==========================
# EQUIPAMENTOS
# ==========================

@admin.register(Equipamento)
class EquipamentoAdmin(admin.ModelAdmin):

    list_display = (
        '__str__',
    )


# ==========================
# FORNECEDORES
# ==========================

@admin.register(Fornecedor)
class FornecedorAdmin(admin.ModelAdmin):

    list_display = (
        '__str__',
    )