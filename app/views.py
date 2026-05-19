from django.shortcuts import render, redirect
from django.http import HttpResponse
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from .models import (Propriedade,Lavoura,LoteDeCafe)
from .forms import LavouraForm
from .forms import PropriedadeForm


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

    propriedades = Propriedade.objects.filter(
        produtor=request.user
    )

    lavouras = Lavoura.objects.filter(
        propriedade__produtor=request.user
    )

    lotes = LoteDeCafe.objects.filter(
        lavoura__propriedade__produtor=request.user
    )

    total_sacas = sum(
        lote.quantidade_sacas for lote in lotes
    )

    context = {
        'propriedades': propriedades,
        'lavouras': lavouras,
        'lotes': lotes,
        'total_sacas': total_sacas,
    }

    return render(
        request,
        'produtor_dashboard.html',
        context
    )

@login_required
def funcionario_dashboard(request):
    if request.user.tipo != 'funcionario':
        return HttpResponse("Acesso negado")
    return render(request, 'funcionario_dashboard.html')


def logout_view(request):
    logout(request)
    return redirect('login')

@login_required
def dashboard(request):

    return render(
        request,
        'dashboard.html'
    )

@login_required
def cadastrar_lavoura(request):

    if request.user.tipo != 'produtor':
        return HttpResponse("Acesso negado")

    if request.method == 'POST':

        form = LavouraForm(request.POST)

        if form.is_valid():

            lavoura = form.save(commit=False)

            propriedade = lavoura.propriedade

            if propriedade.produtor != request.user:
                return HttpResponse("Acesso negado")

            lavoura.save()

            return redirect('produtor_dashboard')

    else:

        form = LavouraForm()

        form.fields['propriedade'].queryset = Propriedade.objects.filter(
            produtor=request.user
        )

    return render(
        request,
        'cadastrar_lavoura.html',
        {'form': form}
    )
@login_required
def cadastrar_propriedade(request):

    if request.user.tipo != 'produtor':
        return HttpResponse("Acesso negado")

    if request.method == 'POST':

        form = PropriedadeForm(request.POST)

        if form.is_valid():

            propriedade = form.save(commit=False)

            propriedade.produtor = request.user

            propriedade.save()

            return redirect('produtor_dashboard')

    return redirect('produtor_dashboard')
# =========================
# PÁGINAS PRODUTOR
# =========================

@login_required
def propriedades_view(request):
    return render(request, 'propriedades.html')


@login_required
def lavouras_view(request):
    return render(request, 'lavouras.html')


@login_required
def lotes_view(request):
    return render(request, 'lotes.html')


@login_required
def financeiro_view(request):
    return render(request, 'financeiro.html')


@login_required
def relatorios_view(request):
    return render(request, 'relatorios.html')


@login_required
def perfil_view(request):
    return render(request, 'perfil.html')


# =========================
# FUNCIONÁRIO
# =========================

@login_required
def tarefas_view(request):
    return render(request, 'tarefas.html')


@login_required
def registros_view(request):
    return render(request, 'registros.html')


# =========================
# ADMIN
# =========================

@login_required
def usuarios_view(request):
    return render(request, 'usuarios.html')


@login_required
def estatisticas_view(request):
    return render(request, 'estatisticas.html')


@login_required
def auditoria_view(request):
    return render(request, 'auditoria.html')

@login_required
def rastreabilidade_view(request):

    return render(
        request,
        'rastreabilidade.html'
    )


@login_required
def propriedades_view(request):

    propriedades = Propriedade.objects.filter(
        produtor=request.user
    )

    return render(
        request,
        'propriedades.html',
        {
            'propriedades': propriedades
        }
    )


@login_required
def lavouras_view(request):

    lavouras = Lavoura.objects.filter(
        propriedade__produtor=request.user
    )

    return render(
        request,
        'lavouras.html',
        {
            'lavouras': lavouras
        }
    )


@login_required
def lotes_view(request):

    lotes = LoteDeCafe.objects.filter(
        lavoura__propriedade__produtor=request.user
    )

    return render(
        request,
        'lotes.html',
        {
            'lotes': lotes
        }
    )


@login_required
def financeiro_view(request):

    return render(
        request,
        'financeiro.html'
    )


@login_required
def relatorios_view(request):

    return render(
        request,
        'relatorios.html'
    )


@login_required
def perfil_view(request):

    return render(
        request,
        'perfil.html'
    )

@login_required
def propriedades_view(request):

    propriedades = Propriedade.objects.filter(
        produtor=request.user
    )

    return render(
        request,
        'propriedades.html',
        {'propriedades': propriedades}
    )


@login_required
def lavouras_view(request):

    lavouras = Lavoura.objects.filter(
        propriedade__produtor=request.user
    )

    return render(
        request,
        'lavouras.html',
        {'lavouras': lavouras}
    )


@login_required
def lotes_view(request):

    lotes = LoteDeCafe.objects.filter(
        lavoura__propriedade__produtor=request.user
    )

    total_sacas = sum(
        lote.quantidade_sacas for lote in lotes
    )

    return render(
        request,
        'lotes.html',
        {
            'lotes': lotes,
            'total_sacas': total_sacas
        }
    )


@login_required
def rastreabilidade_view(request):

    return render(
        request,
        'rastreabilidade.html'
    )


@login_required
def financeiro_view(request):

    return render(
        request,
        'financeiro.html'
    )


@login_required
def relatorios_view(request):

    return render(
        request,
        'relatorios.html'
    )


@login_required
def perfil_view(request):

    return render(
        request,
        'perfil.html'
    )