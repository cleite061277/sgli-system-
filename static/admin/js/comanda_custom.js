/*
 * Comanda Admin - Scripts Customizados
 * HABITAT PRO - Sistema de Gestão de Imóveis
 */

(function($) {
    'use strict';
    
    $(document).ready(function() {
        console.log('✅ Comanda Admin carregado');
        
        // Destacar comandas vencidas
        $('.field-is_vencida').each(function() {
            if ($(this).find('img[alt="True"]').length > 0) {
                $(this).closest('tr').addClass('comanda-vencida');
            }
        });
        
        // Adicionar tooltips nos valores
        $('.field-valor_total').attr('title', 'Valor total com multa e juros aplicados');
        
        console.log('✅ Customizações da Comanda aplicadas');
    });
    
})(django.jQuery);
