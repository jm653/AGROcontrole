from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpResponse
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from .models import LoteDeCafe
from django.db.models import Sum
from django.db.models import Count
from django.db.models import Sum, Count
from .models import Propriedade, Lavoura, LoteDeCafe,MovimentacaoFinanceira
from django.db.models import Sum
from django.http import HttpResponse
from datetime import datetime
import openpyxl
from datetime import timedelta
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.units import cm
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, HRFlowable
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_RIGHT

import json

from .forms import (
    LoteForm,
    MovimentacaoFinanceiraForm
)

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

    # ETAPAS DOS LOTES

    etapas = lotes.values(
        'etapa'
    ).annotate(
        total=Count('id')
    )

    etapas_labels = []
    etapas_valores = []

    for etapa in etapas:

        etapas_labels.append(
            etapa['etapa']
        )

        etapas_valores.append(
            etapa['total']
        )

    # TOTAL DE SACAS

    total_sacas = lotes.aggregate(
        total=Sum('quantidade_sacas')
    )['total'] or 0

    # VALOR TOTAL

    valor_total = 0

    for lote in lotes:

        valor_total += (
            lote.quantidade_sacas *
            lote.preco_saca
        )

    # CONTEXT

    context = {

        'propriedades': propriedades,

        'lavouras': lavouras,

        'lotes': lotes,

        'total_sacas': total_sacas,

        'valor_total': valor_total,

        # ETAPAS

        'etapas': etapas,

        # ÚLTIMOS LOTES

        'ultimos_lotes': lotes.order_by('-id')[:5],

        # GRÁFICO

        'etapas_labels': etapas_labels,

        'etapas_valores': etapas_valores,

        # ANTES (no final do produtor_dashboard):
        'etapas_labels': etapas_labels,
        'etapas_valores': etapas_valores,

        # DEPOIS:
        'etapas_labels': json.dumps(etapas_labels),
        'etapas_valores': json.dumps(etapas_valores),
    }

    return render(
        request,
        'produtor_dashboard.html',
        context
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

    lotes = LoteDeCafe.objects.filter(
        lavoura__propriedade__produtor=request.user
    )

    movimentacoes = MovimentacaoFinanceira.objects.filter(
        produtor=request.user
    ).order_by('-id')

    # FORM

    if request.method == 'POST':

        form = MovimentacaoFinanceiraForm(
            request.POST
        )

        if form.is_valid():

            movimentacao = form.save(
                commit=False
            )

            movimentacao.produtor = request.user

            movimentacao.save()

            return redirect('financeiro')

    else:

        form = MovimentacaoFinanceiraForm()

    # FATURAMENTO DOS LOTES

    faturamento_total = 0

    for lote in lotes:

        faturamento_total += (
            lote.quantidade_sacas *
            lote.preco_saca
        )

    # ENTRADAS (LUCROS)

    entradas_total = movimentacoes.filter(
        tipo='LUCRO'
    ).aggregate(
        total=Sum('valor')
    )['total'] or 0

    # DESPESAS

    despesas_total = movimentacoes.filter(
        tipo='DESPESA'
    ).aggregate(
        total=Sum('valor')
    )['total'] or 0

    # FATURAMENTO BRUTO REAL

    faturamento_total += entradas_total

    # LUCRO FINAL

    lucro_total = (
        faturamento_total -
        despesas_total
    )

    # LOTES MAIS VALIOSOS

    lotes_valiosos = lotes.order_by(
        '-preco_saca'
    )[:3]

    context = {

        'faturamento_total': faturamento_total,

        'lucro_total': lucro_total,

        'despesas_total': despesas_total,

        'saldo_final': lucro_total,

        'lotes_valiosos': lotes_valiosos,

        'movimentacoes': movimentacoes,

        'form': form,

    }

    return render(
        request,
        'financeiro.html',
        context
    )

@login_required
def editar_movimentacao(request, id):

    movimentacao = get_object_or_404(
        MovimentacaoFinanceira,
        id=id,
        produtor=request.user
    )

    if request.method == 'POST':

        form = MovimentacaoFinanceiraForm(
            request.POST,
            instance=movimentacao
        )

        if form.is_valid():

            form.save()

            return redirect('financeiro')

    else:

        form = MovimentacaoFinanceiraForm(
            instance=movimentacao
        )

    return render(
        request,
        'editar_movimentacao.html',
        {
            'form': form,
            'movimentacao': movimentacao
        }
    )


@login_required
def excluir_movimentacao(request, id):

    movimentacao = get_object_or_404(
        MovimentacaoFinanceira,
        id=id,
        produtor=request.user
    )

    movimentacao.delete()

    return redirect('financeiro')

@login_required
def excluir_movimentacao(request, id):

    movimentacao = get_object_or_404(
        MovimentacaoFinanceira,
        id=id,
        produtor=request.user
    )

    movimentacao.delete()

    return redirect('financeiro')

# =========================================================
# RELATÓRIOS
# =========================================================

@login_required
def relatorios_view(request):

    # LAVOURAS

    lavouras = Lavoura.objects.filter(
        propriedade__produtor=request.user
    )

    # LOTES

    lotes = LoteDeCafe.objects.filter(
        lavoura__propriedade__produtor=request.user
    )

    # MOVIMENTAÇÕES

    # FILTRO DE PERÍODO

    periodo = request.GET.get('periodo')

    movimentacoes = MovimentacaoFinanceira.objects.filter(
        produtor=request.user
    )


    if periodo == '7dias':
        movimentacoes = movimentacoes.filter(
            data__gte=datetime.now().date() - timedelta(days=7)
        )

    elif periodo == '30dias':

        movimentacoes = movimentacoes.filter(
            data__gte=datetime.now().date() - timedelta(days=30)
        )

    elif periodo == '365dias':

        movimentacoes = movimentacoes.filter(
            data__gte=datetime.now().date() - timedelta(days=365)
        )

    # PRODUÇÃO TOTAL

    producao_total = 0

    faturamento_total = 0

    for lote in lotes:

        producao_total += lote.quantidade_sacas

        faturamento_total += (
            lote.quantidade_sacas *
            lote.preco_saca
        )

    # DESPESAS

    despesas_total = movimentacoes.filter(
        tipo='DESPESA'
    ).aggregate(
        total=Sum('valor')
    )['total'] or 0

    # ENTRADAS / LUCROS

    entradas_total = movimentacoes.filter(
        tipo='LUCRO'
    ).aggregate(
        total=Sum('valor')
    )['total'] or 0

    # FATURAMENTO BRUTO REAL

    faturamento_total += entradas_total

    # LUCRO FINAL

    lucro_total = (
        faturamento_total -
        despesas_total
    )

    # TOTAL DE LOTES

    total_lotes = lotes.count()

    # EFICIÊNCIA

    if faturamento_total > 0:

        eficiencia = round(
            (lucro_total / faturamento_total) * 100,
            1
        )

    else:

        eficiencia = 0

    # RELATÓRIO POR LAVOURA

    relatorio_lavouras = []

    for lavoura in lavouras:

        lotes_lavoura = LoteDeCafe.objects.filter(
            lavoura=lavoura
        )

        total_sacas = 0

        faturamento_lavoura = 0

        for lote in lotes_lavoura:

            total_sacas += lote.quantidade_sacas

            faturamento_lavoura += (
                lote.quantidade_sacas *
                lote.preco_saca
            )

        quantidade_lotes = lotes_lavoura.count()

        relatorio_lavouras.append({

            'nome': lavoura.nome,

            'sacas': total_sacas,

            'faturamento': faturamento_lavoura,

            'lotes': quantidade_lotes,

        })

    # CONTEXT

    context = {

        'producao_total': producao_total,

        'faturamento_total': faturamento_total,

        'lucro_total': lucro_total,

        'despesas_total': despesas_total,

        'total_lotes': total_lotes,

        'eficiencia': eficiencia,

        'relatorio_lavouras': relatorio_lavouras,

    }

    return render(
        request,
        'relatorios.html',
        context
    )


# =========================================================
#EXPORTAR EXEL 
# =========================================================

@login_required
def exportar_excel(request):

    movimentacoes = MovimentacaoFinanceira.objects.filter(
        produtor=request.user
    )

    workbook = openpyxl.Workbook()

    sheet = workbook.active

    sheet.title = 'Relatório Financeiro'

    # CABEÇALHOS

    sheet['A1'] = 'Descrição'
    sheet['B1'] = 'Tipo'
    sheet['C1'] = 'Valor'
    sheet['D1'] = 'Data'

    linha = 2

    for mov in movimentacoes:

        sheet[f'A{linha}'] = mov.descricao
        sheet[f'B{linha}'] = mov.tipo
        sheet[f'C{linha}'] = float(mov.valor)
        sheet[f'D{linha}'] = str(mov.data)

        linha += 1

    response = HttpResponse(
        content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    )

    response[
        'Content-Disposition'
    ] = 'attachment; filename=relatorio.xlsx'

    workbook.save(response)

    return response


# =========================================================
#PDF
# =========================================================

@login_required
def exportar_pdf(request):

    movimentacoes = MovimentacaoFinanceira.objects.filter(
        produtor=request.user
    )

    response = HttpResponse(
        content_type='application/pdf'
    )

    response[
        'Content-Disposition'
    ] = 'attachment; filename=relatorio.pdf'

    pdf = canvas.Canvas(response)

    pdf.setFont("Helvetica-Bold", 16)

    pdf.drawString(
        200,
        800,
        "Relatório Financeiro"
    )

    y = 750

    pdf.setFont("Helvetica", 12)

    for mov in movimentacoes:

        texto = (
            f'{mov.descricao} | '
            f'{mov.tipo} | '
            f'R$ {mov.valor}'
        )

        pdf.drawString(
            50,
            y,
            texto
        )

        y -= 25

    pdf.save()

    return response

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
