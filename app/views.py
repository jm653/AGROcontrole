from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpResponse
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.db.models import Sum, Count
from datetime import datetime, timedelta
import json
import openpyxl
import urllib.request as _urllib_req
import urllib.error   as _urllib_err

from .models import (
    Propriedade, Lavoura, LoteDeCafe,
    MovimentacaoFinanceira, RegistroOperacional,
    Usuario, FuncionarioPropriedade, Notificacao
)
from .forms import LavouraForm, PropriedadeForm, LoteForm, MovimentacaoFinanceiraForm

from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.units import cm
from reportlab.platypus import (
    SimpleDocTemplate, Table, TableStyle,
    Paragraph, Spacer, HRFlowable
)
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_RIGHT


# =========================================================
# LOGIN / LOGOUT
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


def logout_view(request):
    logout(request)
    return redirect('login')


@login_required
def cafe_preco_api(request):
    """Proxy para /api/cafe da Flask (cotação brasileira)."""
    from django.http import JsonResponse
    try:
        with _urllib_req.urlopen('http://127.0.0.1:5001/api/cafe', timeout=8) as resp:
            data = json.loads(resp.read().decode('utf-8'))
            return JsonResponse(data)
    except Exception as e:
        return JsonResponse({'arabica': 'Não encontrado', 'conilon': 'Não encontrado', 'erro': str(e)})


@login_required
def cafe_historico_api(request):
    """Proxy para /api/historico da Flask (histórico CSV)."""
    from django.http import JsonResponse
    try:
        with _urllib_req.urlopen('http://127.0.0.1:5001/api/historico', timeout=8) as resp:
            data = json.loads(resp.read().decode('utf-8'))
            return JsonResponse(data, safe=False)
    except Exception:
        return JsonResponse([], safe=False)


@login_required
def coffee_prices_api(request):
    """
    Busca cotações de café via Yahoo Finance (gratuito, sem chave).
    Tickers:
      KC=F  — Arábica futures (ICE, US cents/lb)
      RC=F  — Robusta futures (ICE, USD/ton)
      BRL=X — USD/BRL para conversão
    """
    from django.http import JsonResponse

    def fetch_yahoo(ticker):
        url = f'https://query1.finance.yahoo.com/v8/finance/chart/{ticker}?interval=1d&range=7d'
        req = _urllib_req.Request(url, headers={
            'User-Agent': 'Mozilla/5.0',
            'Accept': 'application/json',
        })
        with _urllib_req.urlopen(req, timeout=10) as resp:
            return json.loads(resp.read().decode('utf-8'))

    try:
        # ── Arábica (US cents/lb) ──
        kc_data      = fetch_yahoo('KC=F')
        kc_meta      = kc_data['chart']['result'][0]['meta']
        arabica      = round(float(kc_meta.get('regularMarketPrice', 0)), 2)
        arabica_prev = round(float(kc_meta.get('chartPreviousClose', arabica)), 2)
        arabica_chg  = round(arabica - arabica_prev, 2)
        arabica_pct  = round((arabica_chg / arabica_prev) * 100, 2) if arabica_prev else 0
        arabica_up   = arabica_chg >= 0

        # ── Sparkline (últimos 7 dias) ──
        closes     = kc_data['chart']['result'][0]['indicators']['quote'][0].get('close', [])
        timestamps = kc_data['chart']['result'][0].get('timestamp', [])
        import datetime as _dt
        spark_labels = []
        spark_values = []
        for i, c in enumerate(closes):
            if c is not None:
                try:
                    d = _dt.datetime.fromtimestamp(timestamps[i])
                    spark_labels.append(d.strftime('%d/%m'))
                except Exception:
                    spark_labels.append(str(i))
                spark_values.append(round(c, 2))

        # ── Robusta (USD/ton) ──
        rc_data      = fetch_yahoo('RC=F')
        rc_meta      = rc_data['chart']['result'][0]['meta']
        robusta      = round(float(rc_meta.get('regularMarketPrice', 0)), 0)
        robusta_prev = round(float(rc_meta.get('chartPreviousClose', robusta)), 0)
        robusta_chg  = robusta - robusta_prev
        robusta_pct  = round((robusta_chg / robusta_prev) * 100, 2) if robusta_prev else 0
        robusta_up   = robusta_chg >= 0

        # ── Taxa de câmbio USD/BRL ──
        brl_data = fetch_yahoo('BRL=X')
        brl_meta = brl_data['chart']['result'][0]['meta']
        usd_brl  = float(brl_meta.get('regularMarketPrice', 5.8))

        # ── Conversões ──
        # Arábica: US cents/lb → USD/lb (/100) → USD/saca (*132.277lb) → BRL (*usd_brl)
        arabica_brl_saca  = round((arabica / 100) * 132.277 * usd_brl, 2)
        especial_brl_saca = round(arabica_brl_saca * 1.30, 2)   # 30% premium
        soluvel_brl_kg    = round((arabica_brl_saca * 0.60) / 60, 2)  # 60% do arábica

        return JsonResponse({
            'arabica_usc_lb':    arabica,
            'arabica_change':    f'{arabica_pct:+.2f}%',
            'arabica_up':        arabica_up,
            'arabica_brl_saca':  arabica_brl_saca,
            'robusta_usd_ton':   int(robusta),
            'robusta_change':    f'{robusta_pct:+.2f}%',
            'robusta_up':        robusta_up,
            'brasil_brl_saca':   arabica_brl_saca,
            'brasil_change':     f'{arabica_pct:+.2f}%',
            'brasil_up':         arabica_up,
            'especial_brl_saca': especial_brl_saca,
            'especial_change':   f'{round(arabica_pct * 1.1, 2):+.2f}%',
            'especial_up':       arabica_up,
            'soluvel_brl_kg':    soluvel_brl_kg,
            'soluvel_change':    '0.00%',
            'soluvel_up':        None,
            'usd_brl':           round(usd_brl, 4),
            'sparkline_labels':  spark_labels[-7:],
            'sparkline_values':  spark_values[-7:],
        })

    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

# =========================================================
# DASHBOARDS
# =========================================================

@login_required
def admin_dashboard(request):
    if request.user.tipo != 'admin':
        return HttpResponse("Acesso negado")
    return render(request, 'admin_dashboard.html')


@login_required
def funcionario_dashboard(request):

    lotes = LoteDeCafe.objects.filter(
        responsavel=request.user
    )

    propriedades_ids = FuncionarioPropriedade.objects.filter(
        funcionario=request.user
    ).values_list(
        'propriedade_id',
        flat=True
    )

    total_sacas = sum(
        lote.quantidade_sacas
        for lote in lotes
    )

    total_lavouras = Lavoura.objects.filter(
        propriedade_id__in=propriedades_ids
    ).count()

    total_registros = RegistroOperacional.objects.filter(
        funcionario=request.user
    ).count()

    context = {
        'lotes': lotes,
        'total_lotes': lotes.count(),
        'total_sacas': total_sacas,
        'total_lavouras': total_lavouras,
        'total_registros': total_registros,
        'preco_cafe': '2.150,00'
    }

    return render(
        request,
        'funcionario_dashboard.html',
        context
    )

@login_required
def produtor_dashboard(request):
    propriedades = Propriedade.objects.filter(produtor=request.user)
    lavouras     = Lavoura.objects.filter(propriedade__produtor=request.user)
    lotes        = LoteDeCafe.objects.filter(lavoura__propriedade__produtor=request.user)

    etapas = lotes.values('etapa').annotate(total=Count('id'))
    etapas_labels  = [e['etapa'] for e in etapas]
    etapas_valores = [e['total'] for e in etapas]

    total_sacas = lotes.aggregate(total=Sum('quantidade_sacas'))['total'] or 0
    valor_total = sum(l.quantidade_sacas * l.preco_saca for l in lotes)

    return render(request, 'produtor_dashboard.html', {
        'propriedades':   propriedades,
        'lavouras':       lavouras,
        'lotes':          lotes,
        'total_sacas':    total_sacas,
        'valor_total':    valor_total,
        'etapas':         etapas,
        'ultimos_lotes':  lotes.order_by('-id')[:5],
        'etapas_labels':  json.dumps(etapas_labels),
        'etapas_valores': json.dumps(etapas_valores),
    })


# =========================================================
# FUNCIONÁRIO — avançar etapa / meus lotes / vínculos
# =========================================================

@login_required
def avancar_etapa(request, lote_id):
    lote = get_object_or_404(LoteDeCafe, id=lote_id, responsavel=request.user)
    etapas = ['plantio','colheita','secagem','armazenamento','torra','qualidade','venda']
    idx = etapas.index(lote.etapa)
    if idx < len(etapas) - 1:
        lote.etapa = etapas[idx + 1]
        lote.save()
        RegistroOperacional.objects.create(
            LoteDeCafe=lote,
            funcionario=request.user,
            descricao=f"Lote avançado para {lote.etapa}",
            etapa=lote.etapa
        )
    return redirect('meus_lotes')


@login_required
def meus_lotes(request):
    if request.user.tipo != 'funcionario':
        return HttpResponse("Acesso negado")
    lotes = LoteDeCafe.objects.filter(responsavel=request.user)
    return render(request, 'meus_lotes.html', {'lotes': lotes})


@login_required
def excluir_vinculo(request, id):
    vinculo = get_object_or_404(FuncionarioPropriedade, id=id, propriedade__produtor=request.user)
    vinculo.delete()
    return redirect('funcionarios')


@login_required
def funcionarios_view(request):
    if request.user.tipo not in ['produtor', 'admin']:
        return HttpResponse("Acesso negado")

    propriedades = Propriedade.objects.filter(produtor=request.user)
    vinculos     = FuncionarioPropriedade.objects.filter(
        propriedade__produtor=request.user
    ).select_related('funcionario', 'propriedade')
    funcionarios = Usuario.objects.filter(tipo='funcionario')

    if request.method == 'POST':
        FuncionarioPropriedade.objects.get_or_create(
            funcionario_id=request.POST.get('funcionario'),
            propriedade_id=request.POST.get('propriedade')
        )
        return redirect('funcionarios')

    return render(request, 'funcionarios.html', {
        'vinculos':     vinculos,
        'funcionarios': funcionarios,
        'propriedades': propriedades,
    })


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
            p = form.save(commit=False)
            p.produtor = request.user
            p.save()
            return redirect('propriedades')
    return redirect('propriedades')


@login_required
def propriedades_view(request):
    propriedades   = Propriedade.objects.filter(produtor=request.user)
    total_hectares = sum(p.hectares for p in propriedades)
    cidades_count  = propriedades.values('cidade').distinct().count()
    return render(request, 'propriedades.html', {
        'propriedades':   propriedades,
        'total_hectares': total_hectares,
        'cidades_count':  cidades_count,
        'form':           PropriedadeForm(),
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
    return render(request, 'visualizar_propriedade.html', {'propriedade': propriedade, 'lavouras': lavouras})


# =========================================================
# LAVOURAS
# =========================================================

@login_required
def lavouras_view(request):

    # FUNCIONÁRIO
    if request.user.tipo == 'funcionario':

        propriedades_ids = FuncionarioPropriedade.objects.filter(
            funcionario=request.user
        ).values_list(
            'propriedade_id',
            flat=True
        )

        lavouras = Lavoura.objects.filter(
            propriedade_id__in=propriedades_ids
        )

        total_area = sum(
            lavoura.area
            for lavoura in lavouras
        )

        form = LavouraForm()

        form.fields['propriedade'].queryset = Propriedade.objects.filter(
            id__in=propriedades_ids
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

    # PRODUTOR / ADMIN

    lavouras = Lavoura.objects.filter(
        propriedade__produtor=request.user
    )

    total_area = sum(
        lavoura.area
        for lavoura in lavouras
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

@login_required
def cadastrar_lavoura(request):

    if request.user.tipo == 'funcionario':

        propriedades_ids = FuncionarioPropriedade.objects.filter(
            funcionario=request.user
        ).values_list(
            'propriedade_id',
            flat=True
        )

        if request.method == 'POST':

            form = LavouraForm(request.POST)

            form.fields['propriedade'].queryset = Propriedade.objects.filter(
                id__in=propriedades_ids
            )

            if form.is_valid():

                lavoura = form.save(commit=False)

                if lavoura.propriedade.id not in propriedades_ids:
                    return HttpResponse("Acesso negado")

                lavoura.save()

                return redirect('lavouras')

        else:

            form = LavouraForm()

            form.fields['propriedade'].queryset = Propriedade.objects.filter(
                id__in=propriedades_ids
            )

        return render(
            request,
            'cadastrar_lavoura.html',
            {'form': form}
        )

    # PRODUTOR E ADMIN

    if request.method == 'POST':

        form = LavouraForm(request.POST)

        form.fields['propriedade'].queryset = Propriedade.objects.filter(
            produtor=request.user
        )

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
        {'form': form}
    )


@login_required
def etapas_view(request):

    if request.user.tipo == 'funcionario':

        lotes = LoteDeCafe.objects.filter(
            responsavel=request.user
        )

    else:

        lotes = LoteDeCafe.objects.all()

    return render(
        request,
        'etapas.html',
        {
            'lotes': lotes
        }
    )

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

    # =========================
    # FUNCIONÁRIO
    # =========================

    if request.user.tipo == 'funcionario':

        propriedades_ids = FuncionarioPropriedade.objects.filter(
            funcionario=request.user
        ).values_list(
            'propriedade_id',
            flat=True
        )

        lotes = LoteDeCafe.objects.filter(
            lavoura__propriedade_id__in=propriedades_ids
        )

        total_sacas = sum(
            lote.quantidade_sacas
            for lote in lotes
        )

        if request.method == 'POST':

            form = LoteForm(request.POST)

            form.fields['lavoura'].queryset = Lavoura.objects.filter(
                propriedade_id__in=propriedades_ids
            )

            form.fields['responsavel'].queryset = Usuario.objects.filter(
                id=request.user.id
            )

            if form.is_valid():

                lote = form.save()

                RegistroOperacional.objects.create(
                    lote_cafe=lote,
                    funcionario=request.user,
                    descricao="Lote cadastrado pelo funcionário",
                    etapa=lote.etapa
                )

                return redirect('lotes')

        else:

            form = LoteForm()

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
                'form': form,
                'total_sacas': total_sacas
            }
        )

    # =========================
    # PRODUTOR
    # =========================

    lotes = LoteDeCafe.objects.filter(
        lavoura__propriedade__produtor=request.user
    )

    total_sacas = sum(
        lote.quantidade_sacas
        for lote in lotes
    )

    if request.method == 'POST':

        form = LoteForm(request.POST)

        form.fields['lavoura'].queryset = Lavoura.objects.filter(
            propriedade__produtor=request.user
        )

        form.fields['responsavel'].queryset = Usuario.objects.filter(
            tipo='funcionario'
        )

        if form.is_valid():

            lote = form.save()

            RegistroOperacional.objects.create(
                lote_cafe=lote,
                funcionario=lote.responsavel,
                descricao="Lote cadastrado no sistema",
                etapa=lote.etapa
            )

            return redirect('lotes')

    else:

        form = LoteForm()

        form.fields['lavoura'].queryset = Lavoura.objects.filter(
            propriedade__produtor=request.user
        )

        form.fields['responsavel'].queryset = Usuario.objects.filter(
            tipo='funcionario'
        )

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
def visualizar_lote(request, id):

    lote = get_object_or_404(
        LoteDeCafe,
        id=id
    )

    return render(
        request,
        'visualizar_lote.html',
        {
            'lote': lote
        }
    )


@login_required
def editar_lote(request, id):

    lote = get_object_or_404(
        LoteDeCafe,
        id=id
    )

    if request.method == 'POST':

        form = LoteForm(
            request.POST,
            instance=lote
        )

        if form.is_valid():
            form.save()
            return redirect('lotes')

    else:

        form = LoteForm(
            instance=lote
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

    lote = get_object_or_404(
        LoteDeCafe,
        id=id
    )

    lote.delete()

    return redirect('lotes')


# =========================================================
# RASTREABILIDADE
# =========================================================

@login_required
def rastreabilidade_view(request):
    """Produtor vê todos os lotes das suas propriedades."""
    if request.user.tipo != 'produtor':
        return HttpResponse("Acesso negado")

    lotes = LoteDeCafe.objects.filter(
        lavoura__propriedade__produtor=request.user
    ).select_related('lavoura', 'lavoura__propriedade', 'responsavel').order_by('-criado_em')

    registros = RegistroOperacional.objects.filter(
        LoteDeCafe__lavoura__propriedade__produtor=request.user
    ).select_related('LoteDeCafe', 'funcionario').order_by('-data')[:20]

    return render(request, 'rastreabilidade.html', {
        'lotes':               lotes,
        'total_lotes':         lotes.count(),
        'lotes_plantio':       lotes.filter(etapa='plantio').count(),
        'lotes_colheita':      lotes.filter(etapa='colheita').count(),
        'lotes_secagem':       lotes.filter(etapa='secagem').count(),
        'lotes_armazenamento': lotes.filter(etapa='armazenamento').count(),
        'lotes_finalizados':   lotes.filter(etapa='venda').count(),
        'registros':           registros,
    })


@login_required
def rastreabilidade_funcionario_view(request):
    """Funcionário vê APENAS os lotes em que é responsável."""
    if request.user.tipo != 'funcionario':
        return HttpResponse("Acesso negado")

    lotes = LoteDeCafe.objects.filter(
        responsavel=request.user
    ).select_related('lavoura', 'lavoura__propriedade').order_by('-criado_em')

    registros = RegistroOperacional.objects.filter(
        funcionario=request.user
    ).select_related('LoteDeCafe').order_by('-data')[:20]

    return render(request, 'rastreabilidade.html', {
        'lotes':               lotes,
        'total_lotes':         lotes.count(),
        'lotes_plantio':       lotes.filter(etapa='plantio').count(),
        'lotes_colheita':      lotes.filter(etapa='colheita').count(),
        'lotes_secagem':       lotes.filter(etapa='secagem').count(),
        'lotes_armazenamento': lotes.filter(etapa='armazenamento').count(),
        'lotes_finalizados':   lotes.filter(etapa='venda').count(),
        'registros':           registros,
    })


@login_required
def detalhe_lote_view(request, lote_id):
    if request.user.tipo == 'funcionario':
        lote = get_object_or_404(LoteDeCafe, id=lote_id, responsavel=request.user)
    else:
        lote = get_object_or_404(LoteDeCafe, id=lote_id, lavoura__propriedade__produtor=request.user)

    registros = RegistroOperacional.objects.filter(
        LoteDeCafe=lote
    ).select_related('funcionario').order_by('-data')

    return render(request, 'detalhe_lote.html', {'lote': lote, 'registros': registros})


# =========================================================
# FINANCEIRO
# =========================================================

@login_required
def financeiro_view(request):
    lotes         = LoteDeCafe.objects.filter(lavoura__propriedade__produtor=request.user)
    movimentacoes = MovimentacaoFinanceira.objects.filter(produtor=request.user).order_by('-id')

    if request.method == 'POST':
        form = MovimentacaoFinanceiraForm(request.POST)
        if form.is_valid():
            m = form.save(commit=False)
            m.produtor = request.user
            m.save()
            return redirect('financeiro')
    else:
        form = MovimentacaoFinanceiraForm()

    faturamento_total = sum(l.quantidade_sacas * l.preco_saca for l in lotes)
    entradas_total    = movimentacoes.filter(tipo='LUCRO').aggregate(total=Sum('valor'))['total'] or 0
    despesas_total    = movimentacoes.filter(tipo='DESPESA').aggregate(total=Sum('valor'))['total'] or 0
    faturamento_total += entradas_total
    lucro_total        = faturamento_total - despesas_total

    return render(request, 'financeiro.html', {
        'faturamento_total': faturamento_total,
        'lucro_total':       lucro_total,
        'despesas_total':    despesas_total,
        'lotes_valiosos':    lotes.order_by('-preco_saca')[:3],
        'movimentacoes':     movimentacoes,
        'form':              form,
    })


@login_required
def editar_movimentacao(request, id):
    mov = get_object_or_404(MovimentacaoFinanceira, id=id, produtor=request.user)
    if request.method == 'POST':
        form = MovimentacaoFinanceiraForm(request.POST, instance=mov)
        if form.is_valid():
            form.save()
            return redirect('financeiro')
    else:
        form = MovimentacaoFinanceiraForm(instance=mov)
    return render(request, 'editar_movimentacao.html', {'form': form, 'movimentacao': mov})


@login_required
def excluir_movimentacao(request, id):
    get_object_or_404(MovimentacaoFinanceira, id=id, produtor=request.user).delete()
    return redirect('financeiro')


# =========================================================
# RELATÓRIOS
# =========================================================

@login_required
def relatorios_view(request):
    lavouras = Lavoura.objects.filter(propriedade__produtor=request.user)
    lotes    = LoteDeCafe.objects.filter(lavoura__propriedade__produtor=request.user)

    periodo       = request.GET.get('periodo', '')
    movimentacoes = MovimentacaoFinanceira.objects.filter(produtor=request.user)

    if periodo == '7dias':
        movimentacoes = movimentacoes.filter(criado_em__date__gte=datetime.now().date() - timedelta(days=7))
    elif periodo == '30dias':
        movimentacoes = movimentacoes.filter(criado_em__date__gte=datetime.now().date() - timedelta(days=30))
    elif periodo == '365dias':
        movimentacoes = movimentacoes.filter(criado_em__date__gte=datetime.now().date() - timedelta(days=365))

    producao_total    = sum(l.quantidade_sacas for l in lotes)
    faturamento_total = sum(l.quantidade_sacas * l.preco_saca for l in lotes)
    despesas_total    = movimentacoes.filter(tipo='DESPESA').aggregate(total=Sum('valor'))['total'] or 0
    entradas_total    = movimentacoes.filter(tipo='LUCRO').aggregate(total=Sum('valor'))['total'] or 0
    faturamento_total += entradas_total
    lucro_total        = faturamento_total - despesas_total
    eficiencia         = round((lucro_total / faturamento_total) * 100, 1) if faturamento_total > 0 else 0

    relatorio_lavouras = []
    for lavoura in lavouras:
        ll  = LoteDeCafe.objects.filter(lavoura=lavoura)
        fat = sum(l.quantidade_sacas * l.preco_saca for l in ll)
        relatorio_lavouras.append({
            'nome': lavoura.nome,
            'sacas': sum(l.quantidade_sacas for l in ll),
            'faturamento': fat,
            'lotes': ll.count(),
        })

    desempenho_filtro      = request.GET.get('desempenho', '')
    relatorio_lavouras_fil = relatorio_lavouras
    if desempenho_filtro == 'excelente':
        relatorio_lavouras_fil = [i for i in relatorio_lavouras if i['faturamento'] > 1000000]
    elif desempenho_filtro == 'bom':
        relatorio_lavouras_fil = [i for i in relatorio_lavouras if 300000 < i['faturamento'] <= 1000000]
    elif desempenho_filtro == 'medio':
        relatorio_lavouras_fil = [i for i in relatorio_lavouras if i['faturamento'] <= 300000]

    return render(request, 'relatorios.html', {
        'producao_total':           producao_total,
        'faturamento_total':        faturamento_total,
        'lucro_total':              lucro_total,
        'despesas_total':           despesas_total,
        'total_lotes':              lotes.count(),
        'eficiencia':               eficiencia,
        'relatorio_lavouras':       relatorio_lavouras_fil,
        'relatorio_lavouras_todos': relatorio_lavouras,
        'desempenho_filtro':        desempenho_filtro,
        'periodo':                  periodo,
    })


# =========================================================
# EXPORTAR EXCEL / PDF
# =========================================================

@login_required
def exportar_excel(request):
    movimentacoes = MovimentacaoFinanceira.objects.filter(produtor=request.user)
    wb    = openpyxl.Workbook()
    sheet = wb.active
    sheet.title = 'Relatório Financeiro'
    sheet['A1'], sheet['B1'], sheet['C1'], sheet['D1'] = 'Título', 'Tipo', 'Valor', 'Data'
    for i, mov in enumerate(movimentacoes, 2):
        sheet[f'A{i}'] = mov.titulo
        sheet[f'B{i}'] = mov.tipo
        sheet[f'C{i}'] = float(mov.valor)
        sheet[f'D{i}'] = mov.criado_em.strftime('%d/%m/%Y')
    resp = HttpResponse(content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
    resp['Content-Disposition'] = 'attachment; filename=relatorio.xlsx'
    wb.save(resp)
    return resp


@login_required
def exportar_pdf(request):
    movimentacoes = MovimentacaoFinanceira.objects.filter(produtor=request.user).order_by('-criado_em')
    lotes         = LoteDeCafe.objects.filter(lavoura__propriedade__produtor=request.user)

    faturamento_total = sum(l.quantidade_sacas * l.preco_saca for l in lotes)
    total_lucros      = movimentacoes.filter(tipo='LUCRO').aggregate(total=Sum('valor'))['total'] or 0
    total_despesas    = movimentacoes.filter(tipo='DESPESA').aggregate(total=Sum('valor'))['total'] or 0
    lucro_total       = faturamento_total + total_lucros - total_despesas
    producao_total    = sum(l.quantidade_sacas for l in lotes)

    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = 'attachment; filename=relatorio_agrocontrole.pdf'

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

    doc   = SimpleDocTemplate(response, pagesize=A4, rightMargin=2*cm, leftMargin=2*cm, topMargin=2*cm, bottomMargin=2*cm)
    col_w = A4[0] - 4*cm
    styles = getSampleStyleSheet()

    def s(name, **kw):
        return ParagraphStyle(name, parent=styles['Normal'], **kw)

    ST = {
        'header_title': s('ht', fontSize=22, textColor=WHITE,    fontName='Helvetica-Bold', leading=28),
        'header_sub':   s('hs', fontSize=9,  textColor=colors.HexColor('#d7ccc8'), fontName='Helvetica', leading=13),
        'header_date':  s('hd', fontSize=8,  textColor=colors.HexColor('#a1887f'), fontName='Helvetica', alignment=TA_RIGHT),
        'section':      s('sc', fontSize=11, textColor=ESPRESSO, fontName='Helvetica-Bold', spaceBefore=18, spaceAfter=6),
        'label':        s('lb', fontSize=7.5,textColor=MUTED,    fontName='Helvetica', leading=11),
        'value':        s('vl', fontSize=18, textColor=ESPRESSO, fontName='Helvetica-Bold', leading=22),
        'value_green':  s('vg', fontSize=18, textColor=SUCCESS,  fontName='Helvetica-Bold', leading=22),
        'value_red':    s('vr', fontSize=18, textColor=DANGER,   fontName='Helvetica-Bold', leading=22),
        'footer':       s('ft', fontSize=7.5,textColor=MUTED,    fontName='Helvetica', alignment=TA_CENTER),
    }

    now_str  = datetime.now().strftime('%d/%m/%Y às %H:%M')
    user_str = request.user.get_full_name() or request.user.username
    story    = []

    ht = Table([[
        [Paragraph('AgroControle', ST['header_title']), Spacer(1,4),
         Paragraph('Relatório Financeiro de Produção', ST['header_sub'])],
        [Paragraph(f'Gerado em {now_str}', ST['header_date']), Spacer(1,4),
         Paragraph(f'Produtor: {user_str}', ST['header_date'])],
    ]], colWidths=[col_w*0.6, col_w*0.4])
    ht.setStyle(TableStyle([
        ('BACKGROUND',(0,0),(-1,-1),ESPRESSO),('TOPPADDING',(0,0),(-1,-1),20),
        ('BOTTOMPADDING',(0,0),(-1,-1),20),('LEFTPADDING',(0,0),(0,-1),20),
        ('RIGHTPADDING',(-1,0),(-1,-1),20),('VALIGN',(0,0),(-1,-1),'MIDDLE'),
        ('ALIGN',(1,0),(1,-1),'RIGHT'),
    ]))
    story += [ht, Spacer(1,20)]

    ef = round((lucro_total/faturamento_total*100),1) if faturamento_total > 0 else 0

    def kpi_cell(lbl, val, style='value'):
        return [Paragraph(lbl.upper(), ST['label']), Spacer(1,4), Paragraph(str(val), ST[style])]

    kt = Table([[
        kpi_cell('Produção Total',   f'{producao_total} sacas'),
        kpi_cell('Faturamento Bruto',f'R$ {faturamento_total:,.2f}'),
        kpi_cell('Lucro Final',      f'R$ {lucro_total:,.2f}', 'value_green' if lucro_total >= 0 else 'value_red'),
        kpi_cell('Eficiência',       f'{ef}%'),
    ]], colWidths=[col_w/4]*4, rowHeights=[70])
    kt.setStyle(TableStyle([
        ('BACKGROUND',(0,0),(0,-1),IVORY),('BACKGROUND',(1,0),(1,-1),IVORY),
        ('BACKGROUND',(2,0),(2,-1),IVORY),('BACKGROUND',(3,0),(3,-1),IVORY),
        ('BOX',(0,0),(0,-1),0.5,LIGHT_LINE),('BOX',(1,0),(1,-1),0.5,LIGHT_LINE),
        ('BOX',(2,0),(2,-1),0.5,LIGHT_LINE),('BOX',(3,0),(3,-1),0.5,LIGHT_LINE),
        ('TOPPADDING',(0,0),(-1,-1),14),('BOTTOMPADDING',(0,0),(-1,-1),14),
        ('LEFTPADDING',(0,0),(-1,-1),14),('RIGHTPADDING',(0,0),(-1,-1),14),
        ('VALIGN',(0,0),(-1,-1),'TOP'),
        ('LINEABOVE',(0,0),(0,-1),3,CARAMEL),('LINEABOVE',(1,0),(1,-1),3,CARAMEL),
        ('LINEABOVE',(2,0),(2,-1),3,SUCCESS),('LINEABOVE',(3,0),(3,-1),3,INFO),
    ]))
    story += [kt, Spacer(1,22)]

    story += [Paragraph('Movimentações Financeiras', ST['section']),
              HRFlowable(width=col_w, thickness=1, color=LIGHT_LINE, spaceAfter=8)]

    rows = [['Título','Tipo','Valor (R$)','Data']]
    for mov in movimentacoes:
        sinal = '+' if mov.tipo == 'LUCRO' else '-'
        rows.append([mov.titulo, 'Lucro' if mov.tipo=='LUCRO' else 'Despesa',
                     f'{sinal} R$ {mov.valor:,.2f}', mov.criado_em.strftime('%d/%m/%Y')])
    if len(rows) == 1:
        rows.append(['Nenhuma movimentação encontrada.','','',''])

    mt = Table(rows, colWidths=[col_w*0.42,col_w*0.16,col_w*0.22,col_w*0.20], repeatRows=1)
    ms = [
        ('BACKGROUND',(0,0),(-1,0),ESPRESSO),('TEXTCOLOR',(0,0),(-1,0),WHITE),
        ('FONTNAME',(0,0),(-1,0),'Helvetica-Bold'),('FONTSIZE',(0,0),(-1,0),8),
        ('TOPPADDING',(0,0),(-1,0),9),('BOTTOMPADDING',(0,0),(-1,0),9),
        ('LEFTPADDING',(0,0),(-1,0),10),
        ('FONTNAME',(0,1),(-1,-1),'Helvetica'),('FONTSIZE',(0,1),(-1,-1),8.5),
        ('TEXTCOLOR',(0,1),(-1,-1),COFFEE),('TOPPADDING',(0,1),(-1,-1),8),
        ('BOTTOMPADDING',(0,1),(-1,-1),8),('LEFTPADDING',(0,1),(-1,-1),10),
        ('ROWBACKGROUNDS',(0,1),(-1,-1),[WHITE,IVORY]),
        ('LINEBELOW',(0,0),(-1,-1),0.4,LIGHT_LINE),
        ('BOX',(0,0),(-1,-1),0.5,LIGHT_LINE),
        ('VALIGN',(0,0),(-1,-1),'MIDDLE'),
    ]
    for i, row in enumerate(rows[1:], 1):
        if len(row) > 1:
            if row[1] == 'Lucro':
                ms += [('TEXTCOLOR',(2,i),(2,i),SUCCESS),('FONTNAME',(2,i),(2,i),'Helvetica-Bold')]
            elif row[1] == 'Despesa':
                ms += [('TEXTCOLOR',(2,i),(2,i),DANGER),('FONTNAME',(2,i),(2,i),'Helvetica-Bold')]
    mt.setStyle(TableStyle(ms))
    story += [mt, Spacer(1,22)]

    story += [
        HRFlowable(width=col_w, thickness=0.5, color=LIGHT_LINE, spaceBefore=10, spaceAfter=8),
        Paragraph(f'AgroControle — Relatório gerado em {now_str} · Documento confidencial', ST['footer'])
    ]
    doc.build(story)
    return response


# =========================================================
# NOTIFICAÇÕES
# =========================================================

@login_required
def notificacoes(request):
    notifs = Notificacao.objects.filter(usuario=request.user).order_by('-criada_em')
    return render(request, 'notificacoes.html', {'notificacoes': notifs})


@login_required
def marcar_notificacao_lida(request, id):
    n = get_object_or_404(Notificacao, id=id, usuario=request.user)
    n.lida = True
    n.save()
    return redirect('notificacoes')


# =========================================================
# PERFIL
# =========================================================

@login_required
@login_required
def perfil_view(request):
    if request.user.tipo == 'produtor':
        propriedades = Propriedade.objects.filter(produtor=request.user)
        lavouras     = Lavoura.objects.filter(propriedade__produtor=request.user)
        lotes        = LoteDeCafe.objects.filter(lavoura__propriedade__produtor=request.user)
        return render(request, 'perfil.html', {
            'propriedades': propriedades,
            'lavouras':     lavouras,
            'lotes':        lotes,
        })
    elif request.user.tipo == 'funcionario':
        lotes             = LoteDeCafe.objects.filter(responsavel=request.user)
        registros_count   = RegistroOperacional.objects.filter(funcionario=request.user).count()
        lotes_finalizados = lotes.filter(etapa='venda').count()
        return render(request, 'perfil.html', {
            'lotes':             lotes,
            'registros_count':   registros_count,
            'lotes_finalizados': lotes_finalizados,
        })
    return render(request, 'perfil.html', {})   
# =========================================================
# STAFF
# =========================================================

@login_required
def tarefas_view(request):
    return render(request, 'tarefas.html')

@login_required
def registros_view(request):
    if request.user.tipo == 'funcionario':
        registros = RegistroOperacional.objects.filter(
            funcionario=request.user
        ).select_related('lote_cafe', 'funcionario').order_by('-data')
    else:
        registros = RegistroOperacional.objects.filter(
            lote_cafe__lavoura__propriedade__produtor=request.user
        ).select_related('lote_cafe', 'funcionario').order_by('-data')

    return render(request, 'registros.html', {'registros': registros})


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