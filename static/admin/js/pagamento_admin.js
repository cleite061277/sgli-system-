(function($) {
    $(document).ready(function() {
        // Quando o campo comanda mudar
        $('#id_comanda').change(function() {
            var comandaId = $(this).val();
            if (comandaId) {
                // Fazer requisição para obter dados da comanda
                $.ajax({
                    url: '/financeiro/',
                    success: function(data) {
                        // Encontrar a comanda selecionada
                        var comanda = data.comandas.find(c => c.numero === comandaId);
                        if (comanda) {
                            // Atualizar campo de informações
                            var info = '<div class="readonly">' +
                                       '<strong>Locatário:</strong> ' + comanda.locatario + '<br>' +
                                       '<strong>Valor Total:</strong> ' + comanda.valor_total + '<br>' +
                                       '<strong>Valor Pago:</strong> ' + comanda.valor_pago + '<br>' +
                                       '<strong>Saldo:</strong> ' + comanda.saldo +
                                       '</div>';
                            $('#info_contrato').html(info);
                        }
                    }
                });
            }
        });
    });
})(django.jQuery);
