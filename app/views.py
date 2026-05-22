from django.shortcuts import render, redirect
from django.http import HttpResponse
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from .models import LoteDeCafe
from django.db.models import Sum
from django.db.models import Count
from django.db.models import Sum, Count
from .models import Propriedade, Lavoura, LoteDeCafe

from .models import (
    Propriedade,
    Lavoura,
    LoteDeCafe
)

from .forms import (
    LavouraForm,
    PropriedadeForm,
    LoteForm
)


# =========================================================
# LOGIN
# =========================================================

def login_view(request):

    if request.user.is_authenticated:

        if request.user.tipo == 'admin':
            return redirect('admin_dashboard')

        elif request.user.tipo == 'produtor':
            return redirect('produtor_dashboard')

        elif request.user.tipo == 'funcionario':
            return redirect('funcionario_dashboard')

    if request.method == 'POST':

        username = request.POST.get('username')
        password = request.POST.get('password')

        user = authenticate(
            request,
            username=username,
            password=password
        )

        if user is not None:

            login(request, user)

            if user.tipo == 'admin':
                return redirect('admin_dashboard')

            elif user.tipo == 'produtor':
                return redirect('produtor_dashboard')

            elif user.tipo == 'funcionario':
                return redirect('funcionario_dashboard')

        else:

            return render(
                request,
                'login.html',
                {
                    'erro': 'Credenciais inválidas'
                }
            )

    return render(request, 'login.html')


# =========================================================
# LOGOUT
# =========================================================

def logout_view(request):

    logout(request)

    return redirect('login')


# =========================================================
# DASHBOARDS
# =========================================================

@login_required
def admin_dashboard(request):

    if request.user.tipo != 'admin':
        return HttpResponse("Acesso negado")

    return render(
        request,
        'admin_dashboard.html'
    )


@login_required
def funcionario_dashboard(request):

    if request.user.tipo != 'funcionario':
        return HttpResponse("Acesso negado")

    return render(
        request,
        'funcionario_dashboard.html'
    )


@login_required
def produtor_dashboard(request):

    propriedades = Propriedade.objects.filter(
        produtor=request.user
    )

    lavouras = Lavoura.objects.filter(
        propriedade__produtor=request.user
    )

    lotes = LoteDeCafe.objects.filter(
        lavoura__propriedade__produtor=request.user
    )

    total_sacas = lotes.aggregate(
        total=Sum('quantidade_sacas')
    )['total'] or 0

    valor_total = 0

    for lote in lotes:

        valor_total += (
            lote.quantidade_sacas *
            lote.preco_saca
        )

    etapas = lotes.values(
        'etapa'
    ).annotate(
        total=Count('id')
    )

    ultimos_lotes = lotes.order_by('-criado_em')[:5]


    producao_mensal = (
    lotes
    .annotate(mes=TruncMonth('criado_em'))
    .values('mes')
    .annotate(total=Sum('quantidade_sacas'))
    .order_by('mes')
    )

    context = {

        'propriedades': propriedades,
        'lavouras': lavouras,
        'lotes': lotes,
        'total_sacas': total_sacas,
        'valor_total': valor_total,
        'etapas': etapas,
        'ultimos_lotes': ultimos_lotes,
        'etapas': etapas,
        'producao_mensal': producao_mensal,

    }

    return render(
        request,
        'produtor_dashboard.html',
        context
    )

    etapas = lotes.values('etapa').annotate(
    total=Count('id')
    )

from django.db.models import Sum    
from django.db.models.functions import TruncMonth


@login_required
def editar_lavoura(request, id):

    lavoura = Lavoura.objects.get(id=id)

    if lavoura.propriedade.produtor != request.user:
        return HttpResponse("Acesso negado")

    if request.method == 'POST':

        form = LavouraForm(
            request.POST,
            instance=lavoura
        )

        if form.is_valid():

            form.save()

            return redirect('lavouras')

    else:

        form = LavouraForm(instance=lavoura)

        form.fields['propriedade'].queryset = Propriedade.objects.filter(
            produtor=request.user
        )

    return render(
        request,
        'editar_lavoura.html',
        {
            'form': form,
            'lavoura': lavoura
        }
    )


@login_required
def excluir_lavoura(request, id):

    lavoura = Lavoura.objects.get(id=id)

    if lavoura.propriedade.produtor != request.user:
        return HttpResponse("Acesso negado")

    lavoura.delete()

    return redirect('lavouras')


@login_required
def visualizar_lavoura(request, id):

    lavoura = Lavoura.objects.get(id=id)

    if lavoura.propriedade.produtor != request.user:
        return HttpResponse("Acesso negado")

    return render(
        request,
        'visualizar_lavoura.html',
        {
            'lavoura': lavoura
        }
    )


# =========================================================
# CADASTRAR PROPRIEDADE
# =========================================================

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

            return redirect('propriedades')

    return redirect('propriedades')

@login_required
def editar_propriedade(request, id):

    propriedade = Propriedade.objects.get(id=id)

    if propriedade.produtor != request.user:
        return HttpResponse("Acesso negado")

    if request.method == 'POST':

        form = PropriedadeForm(
            request.POST,
            instance=propriedade
        )

        if form.is_valid():

            form.save()

            return redirect('propriedades')

    else:

        form = PropriedadeForm(
            instance=propriedade
        )

    return render(
        request,
        'editar_propriedade.html',
        {
            'form': form,
            'propriedade': propriedade
        }
    )


@login_required
def excluir_propriedade(request, id):

    propriedade = Propriedade.objects.get(id=id)

    if propriedade.produtor != request.user:
        return HttpResponse("Acesso negado")

    propriedade.delete()

    return redirect('propriedades')


@login_required
def visualizar_propriedade(request, id):

    propriedade = Propriedade.objects.get(id=id)

    if propriedade.produtor != request.user:
        return HttpResponse("Acesso negado")

    lavouras = Lavoura.objects.filter(
        propriedade=propriedade
    )

    return render(
        request,
        'visualizar_propriedade.html',
        {
            'propriedade': propriedade,
            'lavouras': lavouras
        }
    )


# =========================================================
# CADASTRAR LAVOURA
# =========================================================

@login_required
def cadastrar_lavoura(request):

    if request.user.tipo != 'produtor':
        return HttpResponse("Acesso negado")

    if request.method == 'POST':

        form = LavouraForm(request.POST)

        if form.is_valid():

            lavoura = form.save(commit=False)

            if lavoura.propriedade.produtor != request.user:
                return HttpResponse("Acesso negado")

            lavoura.save()

            return redirect('lavouras')

    else:

        form = LavouraForm()

        form.fields['propriedade'].queryset = Propriedade.objects.filter(
            produtor=request.user
        )

    return render(
        request,
        'cadastrar_lavoura.html',
        {
            'form': form
        }
    )

@login_required
def editar_lavoura(request, id):

    lavoura = Lavoura.objects.get(id=id)

    if lavoura.propriedade.produtor != request.user:
        return HttpResponse("Acesso negado")

    if request.method == 'POST':

        form = LavouraForm(
            request.POST,
            instance=lavoura
        )

        if form.is_valid():

            form.save()

            return redirect('lavouras')

    else:

        form = LavouraForm(instance=lavoura)

        form.fields['propriedade'].queryset = Propriedade.objects.filter(
            produtor=request.user
        )

    return render(
        request,
        'editar_lavoura.html',
        {
            'form': form,
            'lavoura': lavoura
        }
    )


@login_required
def excluir_lavoura(request, id):

    lavoura = Lavoura.objects.get(id=id)

    if lavoura.propriedade.produtor != request.user:
        return HttpResponse("Acesso negado")

    lavoura.delete()

    return redirect('lavouras')


# =========================================================
# PÁGINA PROPRIEDADES
# =========================================================

@login_required
def propriedades_view(request):

    propriedades = Propriedade.objects.filter(
        produtor=request.user
    )

    total_hectares = sum(
        propriedade.hectares for propriedade in propriedades
    )

    cidades_count = propriedades.values(
        'cidade'
    ).distinct().count()

    form = PropriedadeForm()

    return render(
        request,
        'propriedades.html',
        {
            'propriedades': propriedades,
            'total_hectares': total_hectares,
            'cidades_count': cidades_count,
            'form': form
        }
    )


# =========================================================
# PÁGINA LAVOURAS
# =========================================================

@login_required
def lavouras_view(request):

    lavouras = Lavoura.objects.filter(
        propriedade__produtor=request.user
    )

    total_area = sum(
        lavoura.area for lavoura in lavouras
    )

    form = LavouraForm()

    form.fields['propriedade'].queryset = Propriedade.objects.filter(
        produtor=request.user
    )

    return render(
        request,
        'lavouras.html',
        {
            'lavouras': lavouras,
            'total_area': total_area,
            'form': form
        }
    )


# =========================================================
# PÁGINA LOTES
# =========================================================

@login_required
def lotes_view(request):

    lotes = LoteDeCafe.objects.filter(
        lavoura__propriedade__produtor=request.user
    )

    total_sacas = sum(
        lote.quantidade_sacas for lote in lotes
    )

    if request.method == 'POST':

        form = LoteForm(request.POST)

        form.fields['lavoura'].queryset = Lavoura.objects.filter(
            propriedade__produtor=request.user
        )

        if form.is_valid():

            lote = form.save(commit=False)

            lote.save()

            return redirect('lotes')

        else:

            print(form.errors)

    else:

        form = LoteForm()

        form.fields['lavoura'].queryset = Lavoura.objects.filter(
            propriedade__produtor=request.user
        )

    return render(
        request,
        'lotes.html',
        {
            'lotes': lotes,
            'form': form,
            'total_sacas': total_sacas,
        }
    )
@login_required
def editar_lote(request, id):

    lote = LoteDeCafe.objects.get(id=id)

    if lote.lavoura.propriedade.produtor != request.user:
        return HttpResponse("Acesso negado")

    if request.method == 'POST':

        form = LoteForm(
            request.POST,
            instance=lote
        )

        form.fields['lavoura'].queryset = Lavoura.objects.filter(
            propriedade__produtor=request.user
        )

        if form.is_valid():

            form.save()

            return redirect('lotes')

    else:

        form = LoteForm(
            instance=lote
        )

        form.fields['lavoura'].queryset = Lavoura.objects.filter(
            propriedade__produtor=request.user
        )

    return render(
        request,
        'editar_lote.html',
        {
            'form': form,
            'lote': lote
        }
    )


@login_required
def excluir_lote(request, id):

    lote = LoteDeCafe.objects.get(id=id)

    if lote.lavoura.propriedade.produtor != request.user:
        return HttpResponse("Acesso negado")

    lote.delete()

    return redirect('lotes')


@login_required
def visualizar_lote(request, id):

    lote = LoteDeCafe.objects.get(id=id)

    if lote.lavoura.propriedade.produtor != request.user:
        return HttpResponse("Acesso negado")

    return render(
        request,
        'visualizar_lote.html',
        {
            'lote': lote
        }
    )


@login_required
def excluir_lote(request, id):

    lote = LoteDeCafe.objects.get(id=id)

    if lote.lavoura.propriedade.produtor != request.user:
        return HttpResponse("Acesso negado")

    lote.delete()

    return redirect('lotes')


@login_required
def visualizar_lote(request, id):

    lote = LoteDeCafe.objects.get(id=id)

    if lote.lavoura.propriedade.produtor != request.user:
        return HttpResponse("Acesso negado")

    return render(
        request,
        'visualizar_lote.html',
        {
            'lote': lote
        }
    )


# =========================================================
# RASTREABILIDADE
# =========================================================

@login_required
def rastreabilidade_view(request):

    return render(
        request,
        'rastreabilidade.html'
    )


# =========================================================
# FINANCEIRO
# =========================================================

@login_required
def financeiro_view(request):

    return render(
        request,
        'financeiro.html'
    )


# =========================================================
# RELATÓRIOS
# =========================================================

@login_required
def relatorios_view(request):

    return render(
        request,
        'relatorios.html'
    )


# =========================================================
# PERFIL
# =========================================================

@login_required
def perfil_view(request):

    propriedades = Propriedade.objects.filter(
        produtor=request.user
    )

    lavouras = Lavoura.objects.filter(
        propriedade__produtor=request.user
    )

    lotes = LoteDeCafe.objects.filter(
        lavoura__propriedade__produtor=request.user
    )

    return render(
        request,
        'perfil.html',
        {
            'propriedades': propriedades,
            'lavouras': lavouras,
            'lotes': lotes,
        }
    )


# =========================================================
# FUNCIONÁRIO
# =========================================================

@login_required
def tarefas_view(request):

    return render(
        request,
        'tarefas.html'
    )


@login_required
def registros_view(request):

    return render(
        request,
        'registros.html'
    )


# =========================================================
# ADMIN
# =========================================================

@login_required
def usuarios_view(request):

    return render(
        request,
        'usuarios.html'
    )


@login_required
def estatisticas_view(request):

    return render(
        request,
        'estatisticas.html'
    )


@login_required
def auditoria_view(request):

    return render(
        request,
        'auditoria.html'
    )
