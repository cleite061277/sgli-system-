from django.db import migrations, models

class Migration(migrations.Migration):
    dependencies = [
        ('core', '0001_initial'),  # Ajustar para última migration
    ]

    operations = [
        migrations.AlterField(
            model_name='pagamento',
            name='usuario_registro',
            field=models.ForeignKey(
                null=True,
                blank=True,
                on_delete=models.SET_NULL,
                to='core.usuario',
                verbose_name='Usuário que registrou'
            ),
        ),
    ]
