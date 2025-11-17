// ============================================================
// HABITAT PRO - DASHBOARD PREMIUM ANIMATIONS
// ============================================================

document.addEventListener('DOMContentLoaded', function() {
    
    // === NÚMEROS ANIMADOS ===
    function animateNumbers() {
        const numbers = document.querySelectorAll('.stat-value');
        
        numbers.forEach(number => {
            const target = parseInt(number.textContent.replace(/[^0-9]/g, '')) || 0;
            const duration = 1500;
            const start = 0;
            const increment = target / (duration / 16);
            let current = start;
            
            const timer = setInterval(() => {
                current += increment;
                if (current >= target) {
                    current = target;
                    clearInterval(timer);
                }
                
                // Manter prefixo/sufixo (R$, %, etc)
                const originalText = number.textContent;
                const prefix = originalText.match(/^[^\d]*/)[0];
                const suffix = originalText.match(/[^\d]*$/)[0];
                
                number.textContent = prefix + Math.floor(current) + suffix;
            }, 16);
        });
    }
    
    // === INTERSECTION OBSERVER (Animar ao aparecer) ===
    const observerOptions = {
        threshold: 0.1,
        rootMargin: '0px 0px -50px 0px'
    };
    
    const observer = new IntersectionObserver((entries) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                entry.target.style.opacity = '1';
                entry.target.style.transform = 'translateY(0)';
            }
        });
    }, observerOptions);
    
    // Observar elementos
    document.querySelectorAll('.stat-card, .action-card, .module').forEach(el => {
        el.style.opacity = '0';
        el.style.transform = 'translateY(30px)';
        el.style.transition = 'opacity 0.6s ease, transform 0.6s ease';
        observer.observe(el);
    });
    
    // === PARALLAX NO HEADER ===
    window.addEventListener('scroll', () => {
        const header = document.querySelector('.dashboard-header');
        if (header) {
            const scrolled = window.pageYOffset;
            header.style.transform = `translateY(${scrolled * 0.3}px)`;
        }
    });
    
    // === RIPPLE EFFECT NOS CARDS ===
    document.querySelectorAll('.stat-card, .action-card').forEach(card => {
        card.addEventListener('click', function(e) {
            const ripple = document.createElement('span');
            const rect = this.getBoundingClientRect();
            const size = Math.max(rect.width, rect.height);
            const x = e.clientX - rect.left - size / 2;
            const y = e.clientY - rect.top - size / 2;
            
            ripple.style.width = ripple.style.height = size + 'px';
            ripple.style.left = x + 'px';
            ripple.style.top = y + 'px';
            ripple.classList.add('ripple');
            
            this.appendChild(ripple);
            
            setTimeout(() => ripple.remove(), 600);
        });
    });
    
    // CSS para ripple
    const style = document.createElement('style');
    style.textContent = `
        .ripple {
            position: absolute;
            border-radius: 50%;
            background: rgba(255, 255, 255, 0.5);
            transform: scale(0);
            animation: ripple-animation 0.6s ease-out;
            pointer-events: none;
        }
        
        @keyframes ripple-animation {
            to {
                transform: scale(4);
                opacity: 0;
            }
        }
    `;
    document.head.appendChild(style);
    
    // === INICIAR ANIMAÇÕES ===
    setTimeout(animateNumbers, 300);
    
    // === TOOLTIP NOS CARDS ===
    document.querySelectorAll('.stat-card').forEach(card => {
        card.setAttribute('data-aos', 'fade-up');
    });
    
    console.log('🚀 Dashboard Premium carregado com sucesso!');
});
