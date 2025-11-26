# Cole/mescle este método dentro de ComandaAdmin (substitua qualquer implementação errada)
class ComandaAdmin(admin.ModelAdmin):
    # ... seus atributos existentes ...

    def has_add_permission(self, request):
        # Permite criação no Admin para superusers e para quem tem permissão.
        return super().has_add_permission(request)

    def has_delete_permission(self, request, obj=None):
        # Mantenha o comportamento desejado — por padrão delega ao permission system
        return super().has_delete_permission(request, obj)