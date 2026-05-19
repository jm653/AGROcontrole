from django.urls import path
from . import views

urlpatterns = [

    # LOGIN
    path('', views.login_view, name='login'),

    # DASHBOARDS
    path(
        'admin-dashboard/',
        views.admin_dashboard,
        name='admin_dashboard'
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

    # NOVA DASHBOARD MODERNA
    path(
        'dashboard/',
        views.dashboard,
        name='dashboard'
    ),

    # LOGOUT
    path(
        'logout/',
        views.logout_view,
        name='logout'
    ),

    path(
    'cadastrar-lavoura/',
    views.cadastrar_lavoura,
    name='cadastrar_lavoura'
),
path(
    'cadastrar-propriedade/',
    views.cadastrar_propriedade,
    name='cadastrar_propriedade'
),

]