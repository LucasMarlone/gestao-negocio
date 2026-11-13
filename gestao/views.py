
    filtros = request.GET.copy()
    filtros.pop("page", None)

    return render(
        request,
        "gestao/historico_estoque.html",
        {
            "movimentos": pagina,
            "pagina": pagina,
            "total_movimentos": paginador.count,
            "busca": busca,
            "tipo": tipo,
            "origem": origem,
            "inicio": inicio,
            "fim": fim,
            "erro": erro,
            "tipos": MovimentoEstoque.TIPOS,
            "origens": MovimentoEstoque.ORIGENS,
            "filtros_url": filtros.urlencode(),
        },
    )


@staff_member_required
def ajuste_estoque(request):
    if request.method == "POST":
        form = AjusteEstoqueForm(request.POST)
        chave_operacao = request.POST.get(
            "chave_operacao",
            "",
        )

        if form.is_valid():
            dados = {
                "produto_id": form.cleaned_data["produto"].pk,
                "tipo": form.cleaned_data["tipo"],
                "quantidade": form.cleaned_data["quantidade"],
                "motivo": form.cleaned_data["motivo"],
            }

            def executar():
                ajustar_estoque(
                    produto_id=dados["produto_id"],
                    tipo=dados["tipo"],
                    quantidade=dados["quantidade"],
                    motivo=dados["motivo"],
                    usuario=request.user,
                )

                return reverse("lista_produtos")

            try:
                destino, criada = executar_operacao_unica(
                    chave=chave_operacao,
                    usuario=request.user,
                    acao="ajuste_estoque",
                    dados=dados,
                    executar=executar,
                )
            except ValueError as erro:
                form.add_error(
                    None,
                    str(erro),
                )
            except ValidationError as erro:
                form.add_error(
                    None,
                    " ".join(erro.messages),
                )
            else:
                if criada:
                    messages.success(
                        request,
                        "Ajuste registrado com sucesso.",
                    )
                else:
                    messages.info(
                        request,
                        "Este ajuste já foi processado. "
                        "Nenhuma alteração foi repetida.",
                    )

                return redirect(destino)

        try:
            chave_operacao = str(
                uuid.UUID(chave_operacao)
            )
        except (ValueError, TypeError, AttributeError):
            chave_operacao = str(uuid.uuid4())
    else:
        form = AjusteEstoqueForm()
        chave_operacao = str(uuid.uuid4())

    return render(
        request,
        "gestao/ajuste_estoque.html",
        {
            "form": form,
            "chave_operacao": chave_operacao,
        },
    )
