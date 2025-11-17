def save_formset(self, request, form, formset, change):
    """
    Preenche usuario_registro automaticamente ao salvar pagamentos via inline.
    Garante que qualquer instância que tenha o atributo `usuario_registro`
    e esteja sem valor receba request.user antes do save().
    """
    instances = formset.save(commit=False)
    for instance in instances:
        # Se o objeto tem o atributo usuario_registro e ele está vazio, preenche
        if hasattr(instance, "usuario_registro") and not getattr(instance, "usuario_registro"):
            # request.user no Admin é o usuário autenticado
            instance.usuario_registro = request.user
        # salva a instância (poderá lançar validações do modelo se houver)
        instance.save()
    # salvar relacionamentos many-to-many
    formset.save_m2m()