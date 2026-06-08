from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpResponse
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.db.models import Sum, Count
from datetime import datetime, timedelta
import json
import openpyxl

from .models import Propriedade, Lavoura, LoteDeCafe, MovimentacaoFinanceira, RegistroOperacional,Usuario,FuncionarioPropriedade,Notificacao
from .forms import LavouraForm, PropriedadeForm, LoteForm, MovimentacaoFinanceiraForm
from .models import FuncionarioPropriedade
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.units import cm
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, HRFlowable
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_RIGHT
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
        user = authenticate(request, username=username, password=password)

        if user is not None:
            login(request, user)
            if user.tipo == 'admin':
                return redirect('admin_dashboard')
            elif user.tipo == 'produtor':
                return redirect('produtor_dashboard')
            elif user.tipo == 'funcionario':
                return redirect('funcionario_dashboard')
        else:
            return render(request, 'login.html', {'erro': 'Credenciais inválidas'})

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
    return render(request, 'admin_dashboard.html')


from .models import FuncionarioPropriedade

@login_required
def funcionario_dashboard(request):

    lotes = LoteDeCafe.objects.filter(
        responsavel=request.user
    )

    context = {
        'lotes': lotes,
        'total_lotes': lotes.count()
    }

    return render(
        request,
        'funcionario_dashboard.html',
        context
    )

@login_required
def avancar_etapa(request, lote_id):

    lote = get_object_or_404(
        LoteDeCafe,
        id=lote_id,
        responsavel=request.user
    )

    etapas = [
        'plantio',
        'colheita',
        'secagem',
        'armazenamento',
        'torra',
        'qualidade',
        'venda'
    ]

    indice = etapas.index(lote.etapa)

    if indice < len(etapas) - 1:

        lote.etapa = etapas[indice + 1]
        lote.save()

        RegistroOperacional.objects.create(
            lote_cafe=lote,
            funcionario=request.user,
            descricao=f"Lote avançado para {lote.etapa}",
            etapa=lote.etapa
        )

    return redirect('meus_lotes')

@login_required
def excluir_vinculo(request, id):

    vinculo = get_object_or_404(
        FuncionarioPropriedade,
        id=id,
        propriedade__produtor=request.user
    )

    vinculo.delete()

    return redirect('funcionarios')


@login_required
def meus_lotes(request):

    if request.user.tipo != 'funcionario':
        return HttpResponse("Acesso negado")

    lotes = LoteDeCafe.objects.filter(
        responsavel=request.user
    )

    return render(
        request,
        'meus_lotes.html',
        {
            'lotes': lotes
        }
    )

@login_required
def funcionarios_view(request):

    if request.user.tipo not in ['produtor', 'admin']:  
        return HttpResponse("Acesso negado")

    propriedades = Propriedade.objects.filter(
        produtor=request.user
    )

    vinculos = FuncionarioPropriedade.objects.filter(
        propriedade__produtor=request.user
    ).select_related(
        'funcionario',
        'propriedade'
    )

    funcionarios = Usuario.objects.filter(
        tipo='funcionario'
    )

    if request.method == 'POST':

        funcionario_id = request.POST.get('funcionario')
        propriedade_id = request.POST.get('propriedade')

        FuncionarioPropriedade.objects.get_or_create(
            funcionario_id=funcionario_id,
            propriedade_id=propriedade_id
        )

        return redirect('funcionarios')

    return render(
        request,
        'funcionarios.html',
        {
            'vinculos': vinculos,
            'funcionarios': funcionarios,
            'propriedades': propriedades
        }
    )


@login_required
def produtor_dashboard(request):

    propriedades = Propriedade.objects.filter(produtor=request.user)
    lavouras = Lavoura.objects.filter(propriedade__produtor=request.user)
    lotes = LoteDeCafe.objects.filter(lavoura__propriedade__produtor=request.user)

    # ETAPAS DOS LOTES
    etapas = lotes.values('etapa').annotate(total=Count('id'))

    etapas_labels = []
    etapas_valores = []
    for etapa in etapas:
        etapas_labels.append(etapa['etapa'])
        etapas_valores.append(etapa['total'])

    # TOTAL DE SACAS
    total_sacas = lotes.aggregate(total=Sum('quantidade_sacas'))['total'] or 0

    # VALOR TOTAL
    valor_total = sum(lote.quantidade_sacas * lote.preco_saca for lote in lotes)

    context = {
        'propriedades': propriedades,
        'lavouras': lavouras,
        'lotes': lotes,
        'total_sacas': total_sacas,
        'valor_total': valor_total,
        'etapas': etapas,
        'ultimos_lotes': lotes.order_by('-id')[:5],
        'etapas_labels': json.dumps(etapas_labels),
        'etapas_valores': json.dumps(etapas_valores),
    }

    return render(request, 'produtor_dashboard.html', context)

@login_required
def marcar_notificacao_lida(request, id):

    notificacao = get_object_or_404(
        Notificacao,
        id=id,
        usuario=request.user
    )

    notificacao.lida = True
    notificacao.save()

    return redirect('notificacoes')

@login_required
def marcar_notificacao_lida(request, id):

    notificacao = get_object_or_404(
        Notificacao,
        id=id,
        usuario=request.user
    )

    notificacao.lida = True
    notificacao.save()

    return redirect('notificacoes')


# =========================================================
# PROPRIEDADES
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
def propriedades_view(request):
    propriedades = Propriedade.objects.filter(produtor=request.user)
    total_hectares = sum(p.hectares for p in propriedades)
    cidades_count = propriedades.values('cidade').distinct().count()
    form = PropriedadeForm()
    return render(request, 'propriedades.html', {
        'propriedades': propriedades,
        'total_hectares': total_hectares,
        'cidades_count': cidades_count,
        'form': form,
    })


@login_required
def editar_propriedade(request, id):
    propriedade = Propriedade.objects.get(id=id)
    if propriedade.produtor != request.user:
        return HttpResponse("Acesso negado")
    if request.method == 'POST':
        form = PropriedadeForm(request.POST, instance=propriedade)
        if form.is_valid():
            form.save()
            return redirect('propriedades')
    else:
        form = PropriedadeForm(instance=propriedade)
    return render(request, 'editar_propriedade.html', {'form': form, 'propriedade': propriedade})

@login_required
def notificacoes(request):

    notificacoes = Notificacao.objects.filter(
        usuario=request.user
    ).order_by('-criada_em')

    return render(
        request,
        'notificacoes.html',
        {
            'notificacoes': notificacoes
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
    lavouras = Lavoura.objects.filter(propriedade=propriedade)
    return render(request, 'visualizar_propriedade.html', {
        'propriedade': propriedade,
        'lavouras': lavouras,
    })


# =========================================================
# LAVOURAS
# =========================================================

@login_required
def lavouras_view(request):
    lavouras = Lavoura.objects.filter(propriedade__produtor=request.user)
    total_area = sum(l.area for l in lavouras)
    form = LavouraForm()
    form.fields['propriedade'].queryset = Propriedade.objects.filter(produtor=request.user)
    return render(request, 'lavouras.html', {
        'lavouras': lavouras,
        'total_area': total_area,
        'form': form,
    })


@login_required
def cadastrar_lavoura(request):
    if request.user.tipo not in ['produtor', 'admin']:
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
        form.fields['propriedade'].queryset = Propriedade.objects.filter(produtor=request.user)
    return render(request, 'cadastrar_lavoura.html', {'form': form})


@login_required
def editar_lavoura(request, id):
    lavoura = Lavoura.objects.get(id=id)
    if lavoura.propriedade.produtor != request.user:
        return HttpResponse("Acesso negado")
    if request.method == 'POST':
        form = LavouraForm(request.POST, instance=lavoura)
        if form.is_valid():
            form.save()
            return redirect('lavouras')
    else:
        form = LavouraForm(instance=lavoura)
        form.fields['propriedade'].queryset = Propriedade.objects.filter(produtor=request.user)
    return render(request, 'editar_lavoura.html', {'form': form, 'lavoura': lavoura})


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
    return render(request, 'visualizar_lavoura.html', {'lavoura': lavoura})


# =========================================================
# LOTES
# =========================================================

@login_required
def lotes_view(request):

    # FUNCIONÁRIO
    if request.user.tipo == 'funcionario':

        lotes = LoteDeCafe.objects.filter(
        responsavel=request.user
    )

    total_sacas = sum(
        lote.quantidade_sacas
        for lote in lotes
    )

    form = LoteForm()

    propriedades_ids = FuncionarioPropriedade.objects.filter(
        funcionario=request.user
    ).values_list(
        'propriedade_id',
        flat=True
    )

    form.fields['lavoura'].queryset = Lavoura.objects.filter(
        propriedade_id__in=propriedades_ids
    )

    form.fields['responsavel'].queryset = Usuario.objects.filter(
        id=request.user.id
    )

    return render(
        request,
        'lotes.html',
        {
            'lotes': lotes,
            'total_sacas': total_sacas,
            'form': form
        }
    )

    # PRODUTOR / ADMIN

    lotes = LoteDeCafe.objects.filter(
        lavoura__propriedade__produtor=request.user
    )

    total_sacas = sum(
        lote.quantidade_sacas
        for lote in lotes
    )

    funcionarios_ids = FuncionarioPropriedade.objects.filter(
        propriedade__produtor=request.user
    ).values_list(
        'funcionario_id',
        flat=True
    )

    if request.method == 'POST':

        form = LoteForm(request.POST)

        form.fields['lavoura'].queryset = Lavoura.objects.filter(
            propriedade__produtor=request.user
        )

        form.fields['responsavel'].queryset = Usuario.objects.filter(
            id__in=funcionarios_ids
        )

        if form.is_valid():

            lote = form.save()

            if lote.responsavel:

                RegistroOperacional.objects.create(
                    lote_cafe=lote,
                    funcionario=lote.responsavel,
                    descricao="Lote cadastrado no sistema",
                    etapa=lote.etapa
                )

            return redirect('lotes')

        print(form.errors)

    else:

        form = LoteForm()

        form.fields['lavoura'].queryset = Lavoura.objects.filter(
            propriedade__produtor=request.user
        )

        form.fields['responsavel'].queryset = Usuario.objects.filter(
            id__in=funcionarios_ids
        )

        print(form)

    return render(
        request,
        'lotes.html',
        {
            'lotes': lotes,
            'form': form,
            'total_sacas': total_sacas
        }
    )



@login_required
def editar_lote(request, id):

    lote = LoteDeCafe.objects.get(id=id)

    if request.user.tipo == 'funcionario':

        if lote.responsavel != request.user:
            return HttpResponse("Acesso negado")

    else:

        if lote.lavoura.propriedade.produtor != request.user:
            return HttpResponse("Acesso negado")

    if request.method == 'POST':

        form = LoteForm(
            request.POST,
            instance=lote
        )

        if request.user.tipo != 'funcionario':

            form.fields['lavoura'].queryset = Lavoura.objects.filter(
                propriedade__produtor=request.user
            )

        if form.is_valid():

            form.save()

            return redirect('lotes')

    else:

        form = LoteForm(instance=lote)

        if request.user.tipo != 'funcionario':

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

    if request.user.tipo == 'funcionario':

        if lote.responsavel != request.user:
            return HttpResponse("Acesso negado")

    else:

        if lote.lavoura.propriedade.produtor != request.user:
            return HttpResponse("Acesso negado")

    lote.delete()

    return redirect('lotes')


@login_required
def visualizar_lote(request, id):

    lote = LoteDeCafe.objects.get(id=id)

    if request.user.tipo == 'funcionario':

        if lote.responsavel != request.user:
            return HttpResponse("Acesso negado")

    else:

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

    lotes = LoteDeCafe.objects.filter(
    lavoura__propriedade__produtor=request.user
    ).select_related(
        'lavoura',
        'lavoura__propriedade',
        'responsavel'
    ).order_by('-criado_em')

    registros = RegistroOperacional.objects.filter(
        LoteDeCafe__lavoura__propriedade__produtor=request.user
    ).select_related(
        'LoteDeCafe',
        'funcionario'
    ).order_by('-data')[:4]

    total_lotes = lotes.count()

    lotes_plantio = lotes.filter(
        etapa='plantio'
    ).count()

    lotes_colheita = lotes.filter(
        etapa='colheita'
    ).count()

    lotes_secagem = lotes.filter(
        etapa='secagem'
    ).count()

    lotes_armazenamento = lotes.filter(
        etapa='armazenamento'
    ).count()

    lotes_finalizados = lotes.filter(
        etapa='venda'
    ).count()


    for lote in lotes:
        print(
            lote.codigo,
            lote.responsavel
    )

    context = {

        'lotes': lotes,

        'total_lotes': total_lotes,

        'lotes_plantio': lotes_plantio,

        'lotes_colheita': lotes_colheita,

        'lotes_secagem': lotes_secagem,

        'lotes_armazenamento': lotes_armazenamento,

        'lotes_finalizados': lotes_finalizados,

        'registros': registros,

        

    }

    return render(
        request,
        'rastreabilidade.html',
        context
    )


# =========================================================
# detalhe
# =========================================================
@login_required
def detalhe_lote_view(request, lote_id):

    lote = LoteDeCafe.objects.get(
        id=lote_id,
        lavoura__propriedade__produtor=request.user
    )

    registros = RegistroOperacional.objects.filter(
        LoteDeCafe=lote
    ).select_related(
        'funcionario'
    ).order_by('-data')

    context = {

        'lote': lote,

        'registros': registros,

    }

    return render(
        request,
        'detalhe_lote.html',
        context
    )

# =========================================================
# FINANCEIRO
# =========================================================

@login_required
def financeiro_view(request):
    lotes = LoteDeCafe.objects.filter(lavoura__propriedade__produtor=request.user)
    movimentacoes = MovimentacaoFinanceira.objects.filter(produtor=request.user).order_by('-id')

    if request.method == 'POST':
        form = MovimentacaoFinanceiraForm(request.POST)
        if form.is_valid():
            movimentacao = form.save(commit=False)
            movimentacao.produtor = request.user
            movimentacao.save()
            return redirect('financeiro')
    else:
        form = MovimentacaoFinanceiraForm()

    faturamento_total = sum(l.quantidade_sacas * l.preco_saca for l in lotes)
    entradas_total = movimentacoes.filter(tipo='LUCRO').aggregate(total=Sum('valor'))['total'] or 0
    despesas_total = movimentacoes.filter(tipo='DESPESA').aggregate(total=Sum('valor'))['total'] or 0
    faturamento_total += entradas_total
    lucro_total = faturamento_total - despesas_total
    lotes_valiosos = lotes.order_by('-preco_saca')[:3]

    context = {
        'faturamento_total': faturamento_total,
        'lucro_total': lucro_total,
        'despesas_total': despesas_total,
        'lotes_valiosos': lotes_valiosos,
        'movimentacoes': movimentacoes,
        'form': form,
    }
    return render(request, 'financeiro.html', context)


@login_required
def editar_movimentacao(request, id):
    movimentacao = get_object_or_404(MovimentacaoFinanceira, id=id, produtor=request.user)
    if request.method == 'POST':
        form = MovimentacaoFinanceiraForm(request.POST, instance=movimentacao)
        if form.is_valid():
            form.save()
            return redirect('financeiro')
    else:
        form = MovimentacaoFinanceiraForm(instance=movimentacao)
    return render(request, 'editar_movimentacao.html', {'form': form, 'movimentacao': movimentacao})


@login_required
def excluir_movimentacao(request, id):
    movimentacao = get_object_or_404(MovimentacaoFinanceira, id=id, produtor=request.user)
    movimentacao.delete()
    return redirect('financeiro')


# =========================================================
# RELATÓRIOS
# =========================================================

@login_required
def relatorios_view(request):

    lavouras = Lavoura.objects.filter(propriedade__produtor=request.user)
    lotes = LoteDeCafe.objects.filter(lavoura__propriedade__produtor=request.user)

    # FILTRO DE PERÍODO
    # CAMPO CORRETO: criado_em (MovimentacaoFinanceira não tem campo 'data')
    periodo = request.GET.get('periodo', '')
    movimentacoes = MovimentacaoFinanceira.objects.filter(produtor=request.user)

    if periodo == '7dias':
        movimentacoes = movimentacoes.filter(
            criado_em__date__gte=datetime.now().date() - timedelta(days=7)
        )
    elif periodo == '30dias':
        movimentacoes = movimentacoes.filter(
            criado_em__date__gte=datetime.now().date() - timedelta(days=30)
        )
    elif periodo == '365dias':
        movimentacoes = movimentacoes.filter(
            criado_em__date__gte=datetime.now().date() - timedelta(days=365)
        )

    # PRODUÇÃO E FATURAMENTO
    producao_total = 0
    faturamento_total = 0
    for lote in lotes:
        producao_total += lote.quantidade_sacas
        faturamento_total += lote.quantidade_sacas * lote.preco_saca

    despesas_total = movimentacoes.filter(tipo='DESPESA').aggregate(total=Sum('valor'))['total'] or 0
    entradas_total = movimentacoes.filter(tipo='LUCRO').aggregate(total=Sum('valor'))['total'] or 0
    faturamento_total += entradas_total
    lucro_total = faturamento_total - despesas_total
    total_lotes = lotes.count()

    eficiencia = round((lucro_total / faturamento_total) * 100, 1) if faturamento_total > 0 else 0

    # RELATÓRIO POR LAVOURA
    relatorio_lavouras = []
    for lavoura in lavouras:
        lotes_lavoura = LoteDeCafe.objects.filter(lavoura=lavoura)
        total_sacas = sum(l.quantidade_sacas for l in lotes_lavoura)
        faturamento_lavoura = sum(l.quantidade_sacas * l.preco_saca for l in lotes_lavoura)
        relatorio_lavouras.append({
            'nome': lavoura.nome,
            'sacas': total_sacas,
            'faturamento': faturamento_lavoura,
            'lotes': lotes_lavoura.count(),
        })

    # FILTRO DE DESEMPENHO
    desempenho_filtro = request.GET.get('desempenho', '')
    relatorio_lavouras_filtrado = relatorio_lavouras

    if desempenho_filtro == 'excelente':
        relatorio_lavouras_filtrado = [i for i in relatorio_lavouras if i['faturamento'] > 1000000]
    elif desempenho_filtro == 'bom':
        relatorio_lavouras_filtrado = [i for i in relatorio_lavouras if 300000 < i['faturamento'] <= 1000000]
    elif desempenho_filtro == 'medio':
        relatorio_lavouras_filtrado = [i for i in relatorio_lavouras if i['faturamento'] <= 300000]

    context = {
        'producao_total': producao_total,
        'faturamento_total': faturamento_total,
        'lucro_total': lucro_total,
        'despesas_total': despesas_total,
        'total_lotes': total_lotes,
        'eficiencia': eficiencia,
        'relatorio_lavouras': relatorio_lavouras_filtrado,
        'relatorio_lavouras_todos': relatorio_lavouras,  # usado no ranking (sem filtro)
        'desempenho_filtro': desempenho_filtro,
        'periodo': periodo,
    }
    return render(request, 'relatorios.html', context)


# =========================================================
# EXPORTAR EXCEL
# =========================================================

@login_required
def exportar_excel(request):
    movimentacoes = MovimentacaoFinanceira.objects.filter(produtor=request.user)
    workbook = openpyxl.Workbook()
    sheet = workbook.active
    sheet.title = 'Relatório Financeiro'
    sheet['A1'] = 'Título'
    sheet['B1'] = 'Tipo'
    sheet['C1'] = 'Valor'
    sheet['D1'] = 'Data'
    linha = 2
    for mov in movimentacoes:
        sheet[f'A{linha}'] = mov.titulo
        sheet[f'B{linha}'] = mov.tipo
        sheet[f'C{linha}'] = float(mov.valor)
        sheet[f'D{linha}'] = str(mov.criado_em.strftime('%d/%m/%Y'))
        linha += 1
    response = HttpResponse(
        content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    )
    response['Content-Disposition'] = 'attachment; filename=relatorio.xlsx'
    workbook.save(response)
    return response


# =========================================================
# EXPORTAR PDF
# =========================================================

@login_required
def exportar_pdf(request):

    movimentacoes = MovimentacaoFinanceira.objects.filter(
        produtor=request.user
    ).order_by('-criado_em')   # CORRIGIDO: criado_em em vez de data

    lotes = LoteDeCafe.objects.filter(
        lavoura__propriedade__produtor=request.user
    )

    faturamento_total = sum(l.quantidade_sacas * l.preco_saca for l in lotes)
    total_lucros   = movimentacoes.filter(tipo='LUCRO').aggregate(total=Sum('valor'))['total'] or 0
    total_despesas = movimentacoes.filter(tipo='DESPESA').aggregate(total=Sum('valor'))['total'] or 0
    lucro_total    = faturamento_total + total_lucros - total_despesas
    producao_total = sum(l.quantidade_sacas for l in lotes)

    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = 'attachment; filename=relatorio_agrocontrole.pdf'

    # CORES
    ESPRESSO   = colors.HexColor('#1c0a03')
    COFFEE     = colors.HexColor('#4E342E')
    CARAMEL    = colors.HexColor('#c8813a')
    IVORY      = colors.HexColor('#fdfaf4')
    SUCCESS    = colors.HexColor('#2d7a4f')
    DANGER     = colors.HexColor('#b83232')
    MUTED      = colors.HexColor('#9a8878')
    WHITE      = colors.white
    LIGHT_LINE = colors.HexColor('#ede5d8')
    INFO       = colors.HexColor('#1a5fa0')

    doc = SimpleDocTemplate(
        response, pagesize=A4,
        rightMargin=2*cm, leftMargin=2*cm,
        topMargin=2*cm, bottomMargin=2*cm,
    )
    W, H = A4
    col_w = W - 4*cm

    styles = getSampleStyleSheet()

    def s(name, **kw):
        return ParagraphStyle(name, parent=styles['Normal'], **kw)

    ST = {
        'header_title': s('ht', fontSize=22, textColor=WHITE,      fontName='Helvetica-Bold', leading=28),
        'header_sub':   s('hs', fontSize=9,  textColor=colors.HexColor('#d7ccc8'), fontName='Helvetica', leading=13),
        'header_date':  s('hd', fontSize=8,  textColor=colors.HexColor('#a1887f'), fontName='Helvetica', alignment=TA_RIGHT),
        'section':      s('sc', fontSize=11, textColor=ESPRESSO,    fontName='Helvetica-Bold', spaceBefore=18, spaceAfter=6),
        'label':        s('lb', fontSize=7.5,textColor=MUTED,       fontName='Helvetica', leading=11),
        'value':        s('vl', fontSize=18, textColor=ESPRESSO,    fontName='Helvetica-Bold', leading=22),
        'value_green':  s('vg', fontSize=18, textColor=SUCCESS,     fontName='Helvetica-Bold', leading=22),
        'value_red':    s('vr', fontSize=18, textColor=DANGER,      fontName='Helvetica-Bold', leading=22),
        'footer':       s('ft', fontSize=7.5,textColor=MUTED,       fontName='Helvetica', alignment=TA_CENTER),
    }

    story = []
    now_str  = datetime.now().strftime('%d/%m/%Y às %H:%M')
    user_str = request.user.get_full_name() or request.user.username

    # ── HEADER ──
    header_table = Table(
        [[
            [Paragraph('AgroControle', ST['header_title']),
             Spacer(1,4),
             Paragraph('Relatório Financeiro de Produção', ST['header_sub'])],
            [Paragraph(f'Gerado em {now_str}', ST['header_date']),
             Spacer(1,4),
             Paragraph(f'Produtor: {user_str}', ST['header_date'])],
        ]],
        colWidths=[col_w*0.6, col_w*0.4]
    )
    header_table.setStyle(TableStyle([
        ('BACKGROUND',    (0,0),(-1,-1), ESPRESSO),
        ('TOPPADDING',    (0,0),(-1,-1), 20),
        ('BOTTOMPADDING', (0,0),(-1,-1), 20),
        ('LEFTPADDING',   (0,0),(0,-1),  20),
        ('RIGHTPADDING',  (-1,0),(-1,-1),20),
        ('VALIGN',        (0,0),(-1,-1), 'MIDDLE'),
        ('ALIGN',         (1,0),(1,-1),  'RIGHT'),
    ]))
    story.append(header_table)
    story.append(Spacer(1, 20))

    # ── KPI CARDS ──
    eficiencia_val = round((lucro_total / faturamento_total * 100), 1) if faturamento_total > 0 else 0

    def kpi_cell(label, value, style='value'):
        return [Paragraph(label.upper(), ST['label']), Spacer(1,4), Paragraph(str(value), ST[style])]

    kpi_table = Table([[
        kpi_cell('Produção Total',   f'{producao_total} sacas'),
        kpi_cell('Faturamento Bruto',f'R$ {faturamento_total:,.2f}'),
        kpi_cell('Lucro Final',      f'R$ {lucro_total:,.2f}', 'value_green' if lucro_total >= 0 else 'value_red'),
        kpi_cell('Eficiência',       f'{eficiencia_val}%'),
    ]], colWidths=[col_w/4]*4, rowHeights=[70])

    kpi_table.setStyle(TableStyle([
        ('BACKGROUND',    (0,0),(0,-1), IVORY),
        ('BACKGROUND',    (1,0),(1,-1), IVORY),
        ('BACKGROUND',    (2,0),(2,-1), IVORY),
        ('BACKGROUND',    (3,0),(3,-1), IVORY),
        ('BOX',           (0,0),(0,-1), 0.5, LIGHT_LINE),
        ('BOX',           (1,0),(1,-1), 0.5, LIGHT_LINE),
        ('BOX',           (2,0),(2,-1), 0.5, LIGHT_LINE),
        ('BOX',           (3,0),(3,-1), 0.5, LIGHT_LINE),
        ('TOPPADDING',    (0,0),(-1,-1),14),
        ('BOTTOMPADDING', (0,0),(-1,-1),14),
        ('LEFTPADDING',   (0,0),(-1,-1),14),
        ('RIGHTPADDING',  (0,0),(-1,-1),14),
        ('VALIGN',        (0,0),(-1,-1),'TOP'),
        ('LINEABOVE',     (0,0),(0,-1), 3, CARAMEL),
        ('LINEABOVE',     (1,0),(1,-1), 3, CARAMEL),
        ('LINEABOVE',     (2,0),(2,-1), 3, SUCCESS),
        ('LINEABOVE',     (3,0),(3,-1), 3, INFO),
    ]))
    story.append(kpi_table)
    story.append(Spacer(1, 22))

    # ── MOVIMENTAÇÕES ──
    story.append(Paragraph('Movimentações Financeiras', ST['section']))
    story.append(HRFlowable(width=col_w, thickness=1, color=LIGHT_LINE, spaceAfter=8))

    # CORRIGIDO: usa 'titulo' e 'criado_em' (campos reais do model)
    mov_rows = [['Título', 'Tipo', 'Valor (R$)', 'Data']]
    for mov in movimentacoes:
        tipo_label = 'Lucro' if mov.tipo == 'LUCRO' else 'Despesa'
        sinal      = '+' if mov.tipo == 'LUCRO' else '-'
        mov_rows.append([
            mov.titulo,
            tipo_label,
            f'{sinal} R$ {mov.valor:,.2f}',
            mov.criado_em.strftime('%d/%m/%Y'),
        ])

    if len(mov_rows) == 1:
        mov_rows.append(['Nenhuma movimentação encontrada.', '', '', ''])

    mov_table = Table(
        mov_rows,
        colWidths=[col_w*0.42, col_w*0.16, col_w*0.22, col_w*0.20],
        repeatRows=1
    )
    mov_style = [
        ('BACKGROUND',    (0,0),(-1,0),  ESPRESSO),
        ('TEXTCOLOR',     (0,0),(-1,0),  WHITE),
        ('FONTNAME',      (0,0),(-1,0),  'Helvetica-Bold'),
        ('FONTSIZE',      (0,0),(-1,0),  8),
        ('TOPPADDING',    (0,0),(-1,0),  9),
        ('BOTTOMPADDING', (0,0),(-1,0),  9),
        ('LEFTPADDING',   (0,0),(-1,0),  10),
        ('FONTNAME',      (0,1),(-1,-1), 'Helvetica'),
        ('FONTSIZE',      (0,1),(-1,-1), 8.5),
        ('TEXTCOLOR',     (0,1),(-1,-1), COFFEE),
        ('TOPPADDING',    (0,1),(-1,-1), 8),
        ('BOTTOMPADDING', (0,1),(-1,-1), 8),
        ('LEFTPADDING',   (0,1),(-1,-1), 10),
        ('ROWBACKGROUNDS',(0,1),(-1,-1), [WHITE, IVORY]),
        ('LINEBELOW',     (0,0),(-1,-1), 0.4, LIGHT_LINE),
        ('BOX',           (0,0),(-1,-1), 0.5, LIGHT_LINE),
        ('VALIGN',        (0,0),(-1,-1), 'MIDDLE'),
    ]
    for i, row in enumerate(mov_rows[1:], 1):
        if len(row) > 1:
            if row[1] == 'Lucro':
                mov_style += [('TEXTCOLOR',(2,i),(2,i),SUCCESS), ('FONTNAME',(2,i),(2,i),'Helvetica-Bold')]
            elif row[1] == 'Despesa':
                mov_style += [('TEXTCOLOR',(2,i),(2,i),DANGER),  ('FONTNAME',(2,i),(2,i),'Helvetica-Bold')]

    mov_table.setStyle(TableStyle(mov_style))
    story.append(mov_table)
    story.append(Spacer(1, 22))

    # ── FOOTER ──
    story.append(HRFlowable(width=col_w, thickness=0.5, color=LIGHT_LINE, spaceBefore=10, spaceAfter=8))
    story.append(Paragraph(
        f'AgroControle — Relatório gerado em {now_str} · Documento confidencial',
        ST['footer']
    ))

    doc.build(story)
    return response


# =========================================================
# API DE PREÇOS DO CAFÉ — proxy seguro para a Anthropic
# =========================================================

import urllib.request
import urllib.error

@login_required
def coffee_prices_api(request):
    from django.http import JsonResponse
    from django.conf import settings

    prompt = "\n".join([
        "You are a financial data assistant. Return ONLY a raw JSON object, no markdown, no explanation, no backticks.",
        "Provide realistic approximate current market reference prices for coffee as of today.",
        "JSON structure (use realistic values based on your latest knowledge):",
        "{",
        '  "arabica_usc_lb": 185.40,',
        '  "arabica_change": "+1.2%",',
        '  "arabica_up": true,',
        '  "robusta_usd_ton": 2340,',
        '  "robusta_change": "-0.4%",',
        '  "robusta_up": false,',
        '  "brasil_brl_saca": 1320,',
        '  "brasil_change": "+0.8%",',
        '  "brasil_up": true,',
        '  "especial_brl_saca": 2100,',
        '  "especial_change": "+2.1%",',
        '  "especial_up": true,',
        '  "soluvel_brl_kg": 38,',
        '  "soluvel_change": "0.0%",',
        '  "soluvel_up": null,',
        '  "sparkline_labels": ["Seg","Ter","Qua","Qui","Sex","Sab","Dom"],',
        '  "sparkline_values": [180, 182, 181, 185, 183, 186, 185]',
        "}"
    ])

    payload = json.dumps({
        "model": "claude-sonnet-4-20250514",
        "max_tokens": 500,
        "messages": [{"role": "user", "content": prompt}]
    }).encode('utf-8')

    req = urllib.request.Request(
        "https://api.anthropic.com/v1/messages",
        data=payload,
        headers={
            "Content-Type": "application/json",
            "x-api-key": settings.ANTHROPIC_API_KEY,
            "anthropic-version": "2023-06-01",
        },
        method="POST"
    )

    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            body = json.loads(resp.read().decode('utf-8'))
            raw = "".join(
                item.get("text", "")
                for item in body.get("content", [])
            )
            raw = raw.replace("```json", "").replace("```", "").strip()
            prices = json.loads(raw)
            return JsonResponse(prices)

    except urllib.error.HTTPError as e:
        return JsonResponse({"error": f"API error {e.code}"}, status=502)
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)
# =========================================================
# PERFIL
# =========================================================

@login_required
def perfil_view(request):
    propriedades = Propriedade.objects.filter(produtor=request.user)
    lavouras = Lavoura.objects.filter(propriedade__produtor=request.user)
    lotes = LoteDeCafe.objects.filter(lavoura__propriedade__produtor=request.user)
    return render(request, 'perfil.html', {
        'propriedades': propriedades,
        'lavouras': lavouras,
        'lotes': lotes,
    })


# =========================================================
# FUNCIONÁRIO
# =========================================================

@login_required
def tarefas_view(request):
    return render(request, 'tarefas.html')


@login_required
def registros_view(request):

    if request.user.tipo == 'funcionario':

        registros = RegistroOperacional.objects.filter(
            funcionario=request.user
        )

    else:

        registros = RegistroOperacional.objects.filter(
            lote_cafe__lavoura__propriedade__produtor=request.user
        )

    return render(
        request,
        'registros.html',
        {
            'registros': registros
        }
    )


# =========================================================
# ADMIN
# =========================================================

@login_required
def usuarios_view(request):
    return render(request, 'usuarios.html')


@login_required
def estatisticas_view(request):
    return render(request, 'estatisticas.html')


@login_required
def auditoria_view(request):
    return render(request, 'auditoria.html')

