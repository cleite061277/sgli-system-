(function($) {
    $(document).ready(function() {
        var comandaSelect = $('#id_comanda');
        var infoBox = $('#comanda-info-box');
        
        if (comandaSelect.length) {
            // Função para carregar informações da comanda
            function loadComandaInfo(comandaId) {
                if (!comandaId) {
                    infoBox.hide();
                    return;
                }
                
                // Buscar informações via API
                $.ajax({
                    url: '/admin/core/comanda/' + comandaId + '/change/',
                    type: 'GET',
                    success: function(response) {
                        // Extrair informações da página
                        var parser = new DOMParser();
                        var doc = parser.parseFromString(response, 'text/html');
                        
                        // Tentar pegar informações dos campos readonly
                        infoBox.show();
                    },
                    error: function() {
                        infoBox.hide();
                    }
                });
            }
            
            // Listener para mudança de seleção
            comandaSelect.on('change', function() {
                loadComandaInfo($(this).val());
            });
            
            // Carregar info se já houver valor selecionado
            if (comandaSelect.val()) {
                loadComandaInfo(comandaSelect.val());
            }
        }
    });
})(django.jQuery);
