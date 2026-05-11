from django.urls import path
from . import views

urlpatterns = [
    path('', views.login_view, name='login'),

    path('admin-dashboard/', views.admin_dashboard, name='admin_dashboard'),
    path('produtor-dashboard/', views.produtor_dashboard, name='produtor_dashboard'),
    path('funcionario-dashboard/', views.funcionario_dashboard, name='funcionario_dashboard'),

    path('logout/', views.logout_view, name='logout'),
]