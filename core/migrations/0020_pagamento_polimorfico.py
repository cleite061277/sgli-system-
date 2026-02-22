# Auto-gerado por script de padronização
# Data: 2026-02-16 17:09:08

from django.db import migrations, models
import django.db.models.deletion


def migrar_pagamentos(apps, schema_editor):
    """Migra pagamentos existentes para sistema polimórfico"""
    Pagamento = apps.get_model('core', 'Pagamento')
    ContentType = apps.get_model('contenttypes', 'ContentType')
    
    try:
        comanda_ct = ContentType.objects.get(app_label='core', model='comanda')
    except ContentType.DoesNotExist:
        comanda_ct = ContentType.objects.create(app_label='core', model='comanda')
    
    count = 0
    for pag in Pagamento.objects.all():
        if pag.comanda_id:
            pag.content_type = comanda_ct
            pag.object_id = pag.comanda_id
            pag.save(update_fields=['content_type', 'object_id'])
            count += 1
    
    print(f"✅ {count} pagamentos migrados")


class Migration(migrations.Migration):
    dependencies = [
        ('core', '0019_alter_contratodownloadtoken_options_and_more'),
        ('contenttypes', '0002_remove_content_type_name'),
    ]
    
    operations = [
        migrations.AddField(
            model_name='pagamento',
            name='content_type',
            field=models.ForeignKey(
                blank=True, null=True,
                on_delete=django.db.models.deletion.CASCADE,
                to='contenttypes.contenttype',
                help_text='Tipo de comanda'
            ),
        ),
        migrations.AddField(
            model_name='pagamento',
            name='object_id',
            field=models.UUIDField(blank=True, null=True, help_text='ID genérico'),
        ),
        migrations.RunPython(migrar_pagamentos, migrations.RunPython.noop),
        migrations.AddIndex(
            model_name='pagamento',
            index=models.Index(fields=['content_type', 'object_id'], name='pag_poly_idx'),
        ),
    ]
