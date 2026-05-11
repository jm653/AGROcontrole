from django.shortcuts import render, redirect
from django.http import HttpResponse
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required


def login_view(request):
    # 🔒 Se já estiver logado, manda pro dashboard correto
    if request.user.is_authenticated:
        user = request.user

        if user.tipo == 'admin':
            return redirect('admin_dashboard')
        elif user.tipo == 'produtor':
            return redirect('produtor_dashboard')
        elif user.tipo == 'funcionario':
            return redirect('funcionario_dashboard')

    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')

        user = authenticate(request, username=username, password=password)

        if user is not None:
            if not user.tipo:
                return render(request, 'login.html', {'erro': 'Usuário sem tipo definido'})

            login(request, user)

            # 🎯 Redirecionamento correto por tipo
            if user.tipo == 'admin':
                return redirect('admin_dashboard')
            elif user.tipo == 'produtor':
                return redirect('produtor_dashboard')
            elif user.tipo == 'funcionario':
                return redirect('funcionario_dashboard')

        else:
            return render(request, 'login.html', {'erro': 'Credenciais inválidas'})

    return render(request, 'login.html')


@login_required
def admin_dashboard(request):
    if request.user.tipo != 'admin':
        return HttpResponse("Acesso negado")
    return render(request, 'admin_dashboard.html')


@login_required
def produtor_dashboard(request):
    if request.user.tipo != 'produtor':
        return HttpResponse("Acesso negado")
    return render(request, 'produtor_dashboard.html')


@login_required
def funcionario_dashboard(request):
    if request.user.tipo != 'funcionario':
        return HttpResponse("Acesso negado")
    return render(request, 'funcionario_dashboard.html')


def logout_view(request):
    logout(request)
    return redirect('login')