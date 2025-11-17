════════════════════════════════════════════════════════════
  BACKUP DO HABITAT PRO - ANTES DA DASHBOARD MODERNA
════════════════════════════════════════════════════════════

📦 CONTEÚDO DESTE BACKUP:

  • database_backup.json      - Dados completos do banco
  • css_backup/                - Arquivos CSS originais
  • templates_backup/          - Templates (se existiam)
  • urls_backup.py             - URLs principais
  • core_urls_backup.py        - URLs do core
  • views*.py                  - Views customizadas
  • admin*.py                  - Admin customizado
  • RESTAURAR.sh               - Script de restauração

════════════════════════════════════════════════════════════

🔄 COMO RESTAURAR:

  Opção 1 - Script automático:
    ./RESTAURAR.sh

  Opção 2 - Manual:
    1. Copiar arquivos de volta
    2. Coletar estáticos: python manage.py collectstatic
    3. Reiniciar servidor

════════════════════════════════════════════════════════════

⚠️ IMPORTANTE:

  • Guarde este backup em local seguro
  • Não delete até confirmar que a nova dashboard está OK
  • Em caso de dúvida, use o script RESTAURAR.sh

════════════════════════════════════════════════════════════
