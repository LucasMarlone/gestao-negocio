import uuid
from datetime import date
from decimal import Decimal

from django.contrib import messages
from django.contrib.admin.views.decorators import staff_member_required
from django.core.exceptions import ValidationError
from django.core.paginator import Paginator
from django.db import transaction
from django.db.models import F, Q
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils import timezone
from django.views.decorators.http import require_POST
from .forms import (
    AjusteEstoqueForm,
    CancelamentoVendaForm,
    ClienteForm,
    EntradaEstoqueForm,
    ItemVendaFormSet,
    MovimentoCaixaForm,
    ProdutoEdicaoForm,
    ProdutoForm,
    RecebimentoVendaForm,
    ReembolsoVendaForm,
    VendaForm,
)
from .models import (
    Cliente,
    EntradaEstoque,
    ItemVenda,
    MovimentoCaixa,
    MovimentoEstoque,
    Produto,
    Venda,
)
from .operacoes import executar_operacao_unica
from .services import (
    ajustar_estoque,
    cancelar_venda_com_estoque,
    confirmar_venda_com_estoque,
    registrar_recebimento_venda,
    registrar_reembolso_venda,
)


# Número padrão de registros exibidos em cada página das listagens.
ITENS_POR_PAGINA = 10


def _paginar(request, queryset, por_pagina=ITENS_POR_PAGINA):
    """Retorna uma página válida sem quebrar quando o número é inválido."""
    paginator = Paginator(queryset, por_pagina)
    return paginator.get_page(request.GET.get("page"))


def _ler_periodo(request):
    """Lê os filtros de data usados nas listagens de vendas e caixa."""
    inicio = request.GET.get("inicio", "").strip()
    fim = request.GET.get("fim", "").strip()
    data_inicio = None
    data_fim = None
    erro = ""

    try:
        if inicio:
            data_inicio = date.fromisoformat(inicio)
        if fim:
            data_fim = date.fromisoformat(fim)
    except ValueError:
        erro = "Informe datas válidas para o período."

    if not erro and data_inicio and data_fim and data_inicio > data_fim:
        erro = "A data inicial não pode ser posterior à data final."

    return inicio, fim, data_inicio, data_fim, erro


@staff_member_required
def dashboard(request):
    inicio = request.GET.get("inicio", "").strip()
    fim = request.GET.get("fim", "").strip()

    data_inicio = None
    data_fim = None
    erro = ""

    try:
        if inicio:
            data_inicio = date.fromisoformat(inicio)

        if fim:
            data_fim = date.fromisoformat(fim)
    except ValueError:
        erro = "Informe datas válidas para o período."
