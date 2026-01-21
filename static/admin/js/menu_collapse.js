/**
 * HABITAT PRO - Menu Collapse
 * Mantém funcionalidade << >> do Django
 * Compatível com Django 4.x e 5.x
 */

(function() {
    'use strict';
    
    // Aguardar DOM carregar
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', initMenuCollapse);
    } else {
        initMenuCollapse();
    }
    
    function initMenuCollapse() {
        console.log('🏠 HABITAT PRO - Menu Collapse inicializado');
        
        // Django já tem o botão de toggle nativo
        // Vamos apenas adicionar classes extras para nosso CSS
        
        const sidebar = document.querySelector('#nav-sidebar');
        const mainContent = document.querySelector('.main');
        const toggleButton = document.querySelector('#nav-sidebar-toggle');
        
        if (!sidebar || !mainContent) {
            console.warn('Sidebar ou main content não encontrado');
            return;
        }
        
        // Adicionar atributos data-emoji aos headers (para modo colapsado)
        const cadastrosHeader = document.querySelector('.model-imovel');
        const contratosHeader = document.querySelector('.model-locacao');
        const vistoriasHeader = document.querySelector('.model-inspection');
        const financeiroHeader = document.querySelector('.model-pagamento');
        const sistemaHeader = document.querySelector('.model-usuario');
        
        if (cadastrosHeader) cadastrosHeader.setAttribute('data-emoji', '📋');
        if (contratosHeader) contratosHeader.setAttribute('data-emoji', '📄');
        if (vistoriasHeader) vistoriasHeader.setAttribute('data-emoji', '🏠');
        if (financeiroHeader) financeiroHeader.setAttribute('data-emoji', '💰');
        if (sistemaHeader) sistemaHeader.setAttribute('data-emoji', '⚙️');
        
        // Observer para detectar quando Django colapsa/expande
        const observer = new MutationObserver(function(mutations) {
            mutations.forEach(function(mutation) {
                if (mutation.attributeName === 'class') {
                    const isCollapsed = mainContent.classList.contains('shifted');
                    
                    if (isCollapsed) {
                        console.log('📕 Menu colapsado');
                        // Adicionar classe para CSS customizado
                        sidebar.classList.add('habitat-collapsed');
                    } else {
                        console.log('📖 Menu expandido');
                        sidebar.classList.remove('habitat-collapsed');
                    }
                }
            });
        });
        
        // Observar mudanças de classe no main content
        observer.observe(mainContent, {
            attributes: true,
            attributeFilter: ['class']
        });
        
        // Verificar estado inicial
        if (mainContent.classList.contains('shifted')) {
            sidebar.classList.add('habitat-collapsed');
        }
        
        console.log('✅ Menu Collapse configurado');
    }
})();
