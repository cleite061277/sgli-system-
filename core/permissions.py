class PagamentoPermission(BasePermission):
    """
    Granular permissions for payment operations.
    """
    
    def has_permission(self, request, view):
        """Check general permission for payment operations."""
        if not request.user or not request.user.is_authenticated:
            return False
        
        # Superuser has all permissions
        if request.user.is_superuser:
            return True
        
        user_type = getattr(request.user, 'tipo_usuario', None)
        action = view.action
        
        # Define permission matrix
        permission_matrix = {
            'list': [Usuario.TipoUsuario.ADMINISTRADOR, Usuario.TipoUsuario.OPERACIONAL, Usuario.TipoUsuario.FINANCEIRO],
            'retrieve': [Usuario.TipoUsuario.ADMINISTRADOR, Usuario.TipoUsuario.OPERACIONAL, Usuario.TipoUsuario.FINANCEIRO],
            'create': [Usuario.TipoUsuario.ADMINISTRADOR, Usuario.TipoUsuario.OPERACIONAL, Usuario.TipoUsuario.FINANCEIRO],
            'update': [Usuario.TipoUsuario.ADMINISTRADOR, Usuario.TipoUsuario.FINANCEIRO],
            'partial_update': [Usuario.TipoUsuario.ADMINISTRADOR, Usuario.TipoUsuario.FINANCEIRO],
            'destroy': [Usuario.TipoUsuario.ADMINISTRADOR],
            'confirmar': [Usuario.TipoUsuario.ADMINISTRADOR, Usuario.TipoUsuario.FINANCEIRO],
            'cancelar': [Usuario.TipoUsuario.ADMINISTRADOR, Usuario.TipoUsuario.FINANCEIRO],
            'relatorio_financeiro': [Usuario.TipoUsuario.ADMINISTRADOR, Usuario.TipoUsuario.OPERACIONAL, Usuario.TipoUsuario.FINANCEIRO],
        }
        
        allowed_types = permission_matrix.get(action, [])
        return user_type in allowed_types
    
    def has_object_permission(self, request, view, obj):
        """Check object-level permissions."""
        if not request.user or not request.user.is_authenticated:
            return False
        
        # Superuser has all permissions
        if request.user.is_superuser:
            return True
        
        user_type = getattr(request.user, 'tipo_usuario', None)
        
        # Administrador e Financeiro têm acesso total
        if user_type in [Usuario.TipoUsuario.ADMINISTRADOR, Usuario.TipoUsuario.FINANCEIRO]:
            return True
        
        # Operacional pode ver apenas pagamentos que criou
        if user_type == Usuario.TipoUsuario.OPERACIONAL:
            return obj.usuario_responsavel == request.user
        
        return False

