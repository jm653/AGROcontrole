from django.urls import path
from . import views

urlpatterns = [

    # =========================
    # LOGIN
    # =========================

    path(
        '',
        views.login_view,
        name='login'
    ),

    path(
        'logout/',
        views.logout_view,
        name='logout'
    ),

    # =========================
    # DASHBOARDS
    # =========================

    path(
        'admin-dashboard/',
        views.admin_dashboard,
        name='admin_dashboard'
    ),

    path(
    'rastreabilidade/',
    views.rastreabilidade_view,
    name='rastreabilidade'
),

    path(
        'produtor-dashboard/',
        views.produtor_dashboard,
        name='produtor_dashboard'
    ),

    path(
        'funcionario-dashboard/',
        views.funcionario_dashboard,
        name='funcionario_dashboard'
    ),

    # =========================
    # PRODUTOR
    # =========================

    path(
        'propriedades/',
        views.propriedades_view,
        name='propriedades'
    ),

    path(
        'lavouras/',
        views.lavouras_view,
        name='lavouras'
    ),
    path(
    'editar-lavoura/<int:id>/',
    views.editar_lavoura,
    name='editar_lavoura'
    ),

    path(
    'excluir-lavoura/<int:id>/',
    views.excluir_lavoura,
    name='excluir_lavoura'
    ),

    path(
    'visualizar-lavoura/<int:id>/',
    views.visualizar_lavoura,
    name='visualizar_lavoura'
    ),

    path(
        'lotes/',
        views.lotes_view,
        name='lotes'
    ),

    path(
        'rastreabilidade/',
        views.rastreabilidade_view,
        name='rastreabilidade'
    ),

    path(
        'financeiro/',
        views.financeiro_view,
        name='financeiro'
    ),

    path(
        'relatorios/',
        views.relatorios_view,
        name='relatorios'
    ),

    path(
    'exportar-pdf/',
    views.exportar_pdf,
    name='exportar_pdf'
    ),

    path(
    'rastreabilidade/lote/<int:lote_id>/',
    views.detalhe_lote_view,
    name='detalhe_lote'
    ),

    path(
        'perfil/',
        views.perfil_view,
        name='perfil'
    ),

    path(
    'editar-movimentacao/<int:id>/',
    views.editar_movimentacao,
    name='editar_movimentacao'
    ),
    path(
    'excluir-movimentacao/<int:id>/',
    views.excluir_movimentacao,
    name='excluir_movimentacao'
    ),

    # =========================
    # FUNCIONÁRIO
    # =========================

    path(
        'tarefas/',
        views.tarefas_view,
        name='tarefas'
    ),

    path(
        'registros/',
        views.registros_view,
        name='registros'
    ),

    # =========================
    # ADMIN
    # =========================

    path(
        'usuarios/',
        views.usuarios_view,
        name='usuarios'
    ),

    path(
        'estatisticas/',
        views.estatisticas_view,
        name='estatisticas'
    ),

    path(
        'auditoria/',
        views.auditoria_view,
        name='auditoria'
    ),

    # =========================
    # CADASTROS
    # =========================

    path(
        'cadastrar-lavoura/',
        views.cadastrar_lavoura,
        name='cadastrar_lavoura'
    ),
    path(
    'editar-lavoura/<int:id>/',
    views.editar_lavoura,
    name='editar_lavoura'
    ),

    path(
    'excluir-lavoura/<int:id>/',
    views.excluir_lavoura,
    name='excluir_lavoura'
    ),

        

    path(
        'cadastrar-propriedade/',
        views.cadastrar_propriedade,
        name='cadastrar_propriedade'
    ),

    path(
    'editar-propriedade/<int:id>/',
    views.editar_propriedade,
    name='editar_propriedade'
    ),

    path(
    'excluir-propriedade/<int:id>/',
    views.excluir_propriedade,
    name='excluir_propriedade'
    ),

    path(
    'visualizar-propriedade/<int:id>/',
    views.visualizar_propriedade,
    name='visualizar_propriedade'
    ),

    # PROPRIEDADES

path(
    'editar-propriedade/<int:id>/',
    views.editar_propriedade,
    name='editar_propriedade'
),

path(
    'excluir-propriedade/<int:id>/',
    views.excluir_propriedade,
    name='excluir_propriedade'
),

path(
    'visualizar-propriedade/<int:id>/',
    views.visualizar_propriedade,
    name='visualizar_propriedade'
),

path(
    'editar-lote/<int:id>/',
    views.editar_lote,
    name='editar_lote'
),

path(
    'excluir-lote/<int:id>/',
    views.excluir_lote,
    name='excluir_lote'
),

path(
    'visualizar-lote/<int:id>/',
    views.visualizar_lote,
    name='visualizar_lote'
),


]
    


#mandar criar uma vuzualizacao completa no propriedaades depois