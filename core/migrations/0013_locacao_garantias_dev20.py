# Generated migration for DEV_20 - Garantias de Contrato
# Migration: 0013_locacao_garantias_dev20.py

from django.db import migrations, models
import django.core.validators
from decimal import Decimal
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0012_rename_valor_aluguel_to_historico'),
    ]

    operations = [
        migrations.AddField(
            model_name='locacao',
            name='tipo_garantia',
            field=models.CharField(
                choices=[('fiador', 'Fiador'), ('caucao', 'Caução'), ('seguro', 'Seguro Garantia'), ('nenhuma', 'Sem Garantia')],
                default='nenhuma',
                help_text='Tipo de garantia exigida para este contrato',
                max_length=20,
                verbose_name='Tipo de Garantia'
            ),
        ),
        migrations.AddField(
            model_name='locacao',
            name='fiador_garantia',
            field=models.ForeignKey(
                blank=True,
                help_text='Fiador responsável pela garantia deste contrato',
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name='locacoes_garantidas',
                to='core.fiador',
                verbose_name='Fiador (Garantia)'
            ),
        ),
        migrations.AddField(
            model_name='locacao',
            name='caucao_quantidade_meses',
            field=models.IntegerField(
                blank=True,
                help_text='Quantidade de aluguéis como caução (1-12)',
                null=True,
                validators=[
                    django.core.validators.MinValueValidator(1),
                    django.core.validators.MaxValueValidator(12)
                ],
                verbose_name='Caução (Quantidade de Meses)'
            ),
        ),
        migrations.AddField(
            model_name='locacao',
            name='caucao_valor_total',
            field=models.DecimalField(
                blank=True,
                decimal_places=2,
                help_text='Valor total da caução (calculado automaticamente)',
                max_digits=10,
                null=True,
                validators=[django.core.validators.MinValueValidator(Decimal('0.01'))],
                verbose_name='Caução (Valor Total)'
            ),
        ),
        migrations.AddField(
            model_name='locacao',
            name='seguro_apolice',
            field=models.CharField(
                blank=True,
                help_text='Número da apólice do seguro garantia (máx. 100 caracteres)',
                max_length=100,
                verbose_name='Seguro Garantia (Nº Apólice)'
            ),
        ),
        migrations.AddField(
            model_name='locacao',
            name='seguro_seguradora',
            field=models.CharField(
                blank=True,
                help_text='Nome da seguradora',
                max_length=200,
                verbose_name='Seguro Garantia (Seguradora)'
            ),
        ),
    ]
