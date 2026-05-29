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

# =========================================================
# SUBSTITUA a função exportar_pdf no seu views.py por esta
# =========================================================
# Dependência: pip install reportlab
# (provavelmente já está instalado pois você já usa canvas)
# =========================================================

from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.units import cm
from reportlab.platypus import (
    SimpleDocTemplate, Table, TableStyle,
    Paragraph, Spacer, HRFlowable
)
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
from reportlab.platypus import KeepTogether
from datetime import datetime

@login_required
def exportar_pdf(request):

    # ── dados ──────────────────────────────────────────
    movimentacoes = MovimentacaoFinanceira.objects.filter(
        produtor=request.user
    ).order_by('-data')

    lotes = LoteDeCafe.objects.filter(
        lavoura__propriedade__produtor=request.user
    )

    faturamento_total = sum(
        l.quantidade_sacas * l.preco_saca for l in lotes
    )
    total_lucros = movimentacoes.filter(tipo='LUCRO').aggregate(
        total=Sum('valor'))['total'] or 0
    total_despesas = movimentacoes.filter(tipo='DESPESA').aggregate(
        total=Sum('valor'))['total'] or 0
    lucro_total = faturamento_total + total_lucros - total_despesas
    producao_total = sum(l.quantidade_sacas for l in lotes)

    # ── response ───────────────────────────────────────
    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = 'attachment; filename=relatorio_agrocontrole.pdf'

    # ── cores ──────────────────────────────────────────
    ESPRESSO  = colors.HexColor('#1c0a03')
    COFFEE    = colors.HexColor('#4E342E')
    CARAMEL   = colors.HexColor('#c8813a')
    CREAM     = colors.HexColor('#F5F5DC')
    IVORY     = colors.HexColor('#fdfaf4')
    SUCCESS   = colors.HexColor('#2d7a4f')
    DANGER    = colors.HexColor('#b83232')
    MUTED     = colors.HexColor('#9a8878')
    WHITE     = colors.white
    LIGHT_LINE= colors.HexColor('#ede5d8')

    # ── doc ────────────────────────────────────────────
    doc = SimpleDocTemplate(
        response,
        pagesize=A4,
        rightMargin=2*cm, leftMargin=2*cm,
        topMargin=2*cm,   bottomMargin=2*cm,
    )

    W, H = A4
    col_w = W - 4*cm   # usable width

    # ── estilos ────────────────────────────────────────
    styles = getSampleStyleSheet()

    def s(name, **kw):
        base = styles['Normal']
        return ParagraphStyle(name, parent=base, **kw)

    ST = {
        'header_title': s('ht',
            fontSize=22, textColor=WHITE,
            fontName='Helvetica-Bold', leading=28),
        'header_sub': s('hs',
            fontSize=9, textColor=colors.HexColor('#d7ccc8'),
            fontName='Helvetica', leading=13),
        'header_date': s('hd',
            fontSize=8, textColor=colors.HexColor('#a1887f'),
            fontName='Helvetica', alignment=TA_RIGHT),
        'section': s('sec',
            fontSize=11, textColor=ESPRESSO,
            fontName='Helvetica-Bold', spaceBefore=18, spaceAfter=6),
        'label': s('lbl',
            fontSize=7.5, textColor=MUTED,
            fontName='Helvetica', leading=11),
        'value': s('val',
            fontSize=18, textColor=ESPRESSO,
            fontName='Helvetica-Bold', leading=22),
        'value_green': s('vg',
            fontSize=18, textColor=SUCCESS,
            fontName='Helvetica-Bold', leading=22),
        'value_red': s('vr',
            fontSize=18, textColor=DANGER,
            fontName='Helvetica-Bold', leading=22),
        'normal': s('nm',
            fontSize=9, textColor=COFFEE,
            fontName='Helvetica', leading=13),
        'footer': s('ft',
            fontSize=7.5, textColor=MUTED,
            fontName='Helvetica', alignment=TA_CENTER),
    }

    story = []

    # ══════════════════════════════════════════════════
    # HEADER BLOCK (tabela com fundo escuro)
    # ══════════════════════════════════════════════════
    now_str = datetime.now().strftime('%d/%m/%Y às %H:%M')
    user_str = request.user.get_full_name() or request.user.username

    header_left = [
        Paragraph('☕ AgroControle', ST['header_title']),
        Spacer(1, 4),
        Paragraph('Relatório Financeiro de Produção', ST['header_sub']),
    ]
    header_right = [
        Paragraph(f'Gerado em {now_str}', ST['header_date']),
        Spacer(1, 4),
        Paragraph(f'Produtor: {user_str}', ST['header_date']),
    ]

    header_table = Table(
        [[header_left, header_right]],
        colWidths=[col_w * 0.6, col_w * 0.4]
    )
    header_table.setStyle(TableStyle([
        ('BACKGROUND',   (0,0), (-1,-1), ESPRESSO),
        ('ROUNDEDCORNERS', [10]),
        ('TOPPADDING',   (0,0), (-1,-1), 20),
        ('BOTTOMPADDING',(0,0), (-1,-1), 20),
        ('LEFTPADDING',  (0,0), (0,-1),  20),
        ('RIGHTPADDING', (-1,0),(-1,-1), 20),
        ('VALIGN',       (0,0), (-1,-1), 'MIDDLE'),
        ('ALIGN',        (1,0), (1,-1),  'RIGHT'),
    ]))
    story.append(header_table)
    story.append(Spacer(1, 20))

    # ══════════════════════════════════════════════════
    # KPI CARDS (4 colunas)
    # ══════════════════════════════════════════════════
    def kpi_cell(label, value, value_style='value'):
        return [
            Paragraph(label.upper(), ST['label']),
            Spacer(1, 4),
            Paragraph(str(value), ST[value_style]),
        ]

    eficiencia_val = round((lucro_total / faturamento_total * 100), 1) if faturamento_total > 0 else 0

    kpi_data = [[
        kpi_cell('Produção Total', f'{producao_total} sacas'),
        kpi_cell('Faturamento Bruto', f'R$ {faturamento_total:,.2f}'),
        kpi_cell('Lucro Final', f'R$ {lucro_total:,.2f}',
                 'value_green' if lucro_total >= 0 else 'value_red'),
        kpi_cell('Eficiência', f'{eficiencia_val}%'),
    ]]

    kpi_table = Table(kpi_data, colWidths=[col_w/4]*4, rowHeights=[70])
    kpi_table.setStyle(TableStyle([
        ('BACKGROUND',   (0,0), (0,-1), IVORY),
        ('BACKGROUND',   (1,0), (1,-1), IVORY),
        ('BACKGROUND',   (2,0), (2,-1), IVORY),
        ('BACKGROUND',   (3,0), (3,-1), IVORY),
        ('BOX',          (0,0), (0,-1), 0.5, LIGHT_LINE),
        ('BOX',          (1,0), (1,-1), 0.5, LIGHT_LINE),
        ('BOX',          (2,0), (2,-1), 0.5, LIGHT_LINE),
        ('BOX',          (3,0), (3,-1), 0.5, LIGHT_LINE),
        ('TOPPADDING',   (0,0), (-1,-1), 14),
        ('BOTTOMPADDING',(0,0), (-1,-1), 14),
        ('LEFTPADDING',  (0,0), (-1,-1), 14),
        ('RIGHTPADDING', (0,0), (-1,-1), 14),
        ('VALIGN',       (0,0), (-1,-1), 'TOP'),
        ('LINEABOVE',    (0,0), (0,-1), 3, CARAMEL),
        ('LINEABOVE',    (1,0), (1,-1), 3, CARAMEL),
        ('LINEABOVE',    (2,0), (2,-1), 3, SUCCESS),
        ('LINEABOVE',    (3,0), (3,-1), 3, colors.HexColor('#1a5fa0')),
    ]))
    story.append(kpi_table)
    story.append(Spacer(1, 22))

    # ══════════════════════════════════════════════════
    # MOVIMENTAÇÕES FINANCEIRAS
    # ══════════════════════════════════════════════════
    story.append(Paragraph('Movimentações Financeiras', ST['section']))
    story.append(HRFlowable(width=col_w, thickness=1, color=LIGHT_LINE, spaceAfter=8))

    mov_header = ['Descrição', 'Tipo', 'Valor (R$)', 'Data']
    mov_rows = [mov_header]

    for mov in movimentacoes:
        tipo_label = 'Lucro' if mov.tipo == 'LUCRO' else 'Despesa'
        sinal = '+' if mov.tipo == 'LUCRO' else '-'
        mov_rows.append([
            mov.descricao,
            tipo_label,
            f'{sinal} R$ {mov.valor:,.2f}',
            str(mov.data.strftime('%d/%m/%Y') if hasattr(mov.data, 'strftime') else mov.data),
        ])

    if len(mov_rows) == 1:
        mov_rows.append(['Nenhuma movimentação encontrada.', '', '', ''])

    col_widths = [col_w*0.42, col_w*0.16, col_w*0.22, col_w*0.20]
    mov_table = Table(mov_rows, colWidths=col_widths, repeatRows=1)

    mov_style = [
        # header
        ('BACKGROUND',   (0,0), (-1,0),  ESPRESSO),
        ('TEXTCOLOR',    (0,0), (-1,0),  WHITE),
        ('FONTNAME',     (0,0), (-1,0),  'Helvetica-Bold'),
        ('FONTSIZE',     (0,0), (-1,0),  8),
        ('TOPPADDING',   (0,0), (-1,0),  9),
        ('BOTTOMPADDING',(0,0), (-1,0),  9),
        ('LEFTPADDING',  (0,0), (-1,0),  10),
        # rows
        ('FONTNAME',     (0,1), (-1,-1), 'Helvetica'),
        ('FONTSIZE',     (0,1), (-1,-1), 8.5),
        ('TEXTCOLOR',    (0,1), (-1,-1), COFFEE),
        ('TOPPADDING',   (0,1), (-1,-1), 8),
        ('BOTTOMPADDING',(0,1), (-1,-1), 8),
        ('LEFTPADDING',  (0,1), (-1,-1), 10),
        ('ROWBACKGROUNDS',(0,1),(-1,-1), [WHITE, IVORY]),
        ('LINEBELOW',    (0,0), (-1,-1), 0.4, LIGHT_LINE),
        ('BOX',          (0,0), (-1,-1), 0.5, LIGHT_LINE),
        ('VALIGN',       (0,0), (-1,-1), 'MIDDLE'),
    ]

    # colorir coluna valor por tipo
    for i, row in enumerate(mov_rows[1:], 1):
        if len(row) > 1:
            if row[1] == 'Lucro':
                mov_style.append(('TEXTCOLOR', (2,i), (2,i), SUCCESS))
                mov_style.append(('FONTNAME',  (2,i), (2,i), 'Helvetica-Bold'))
            elif row[1] == 'Despesa':
                mov_style.append(('TEXTCOLOR', (2,i), (2,i), DANGER))
                mov_style.append(('FONTNAME',  (2,i), (2,i), 'Helvetica-Bold'))

    mov_table.setStyle(TableStyle(mov_style))
    story.append(mov_table)
    story.append(Spacer(1, 22))

    # ══════════════════════════════════════════════════
    # FOOTER
    # ══════════════════════════════════════════════════
    story.append(HRFlowable(width=col_w, thickness=0.5, color=LIGHT_LINE, spaceBefore=10, spaceAfter=8))
    story.append(Paragraph(
        f'AgroControle — Relatório gerado em {now_str} · Documento confidencial',
        ST['footer']
    ))

    # ── build ──────────────────────────────────────────
    doc.build(story)
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
