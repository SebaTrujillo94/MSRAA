from django.db import migrations, models
import django.core.validators


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0026_team_member'),
    ]

    operations = [
        migrations.AddField(
            model_name='siteconfiguration',
            name='color_text',
            field=models.CharField(
                default='#f0ede8',
                help_text='Color del texto en tema oscuro (CSS --white). Ej: #f0ede8 (crema), #ffffff (blanco puro)',
                max_length=20,
                verbose_name='Color de texto principal',
            ),
        ),
        migrations.AlterField(
            model_name='siteconfiguration',
            name='font_family',
            field=models.CharField(
                default='Calibri, sans-serif',
                help_text="Ej: 'Calibri, sans-serif' o 'Georgia, serif' o 'Helvetica Neue, Helvetica, sans-serif'",
                max_length=200,
                verbose_name='Familia tipográfica',
            ),
        ),
        migrations.AlterField(
            model_name='siteconfiguration',
            name='font_size_base',
            field=models.PositiveIntegerField(
                default=16,
                help_text='Tamaño base de fuente en px (12–24). Los visitantes pueden sobrescribirlo en el panel de Apariencia.',
                validators=[
                    django.core.validators.MinValueValidator(12),
                    django.core.validators.MaxValueValidator(24),
                ],
                verbose_name='Tamaño de fuente base (px)',
            ),
        ),
    ]
