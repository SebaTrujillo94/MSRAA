from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0019_mediaitem_portfolio_img_crop_fields'),
    ]

    operations = [
        migrations.AddField(
            model_name='mediaitem',
            name='img_zoom',
            field=models.DecimalField(blank=True, decimal_places=2, default=1.0, help_text='1.0 = normal · 0.5 = más contexto · 2.0 = acercar', max_digits=4, verbose_name='Zoom'),
        ),
        migrations.AddField(
            model_name='mediaitem',
            name='img_x',
            field=models.IntegerField(blank=True, default=0, help_text='+ = derecha, − = izquierda (desde punto de enfoque)', verbose_name='Offset X (px)'),
        ),
        migrations.AddField(
            model_name='mediaitem',
            name='img_y',
            field=models.IntegerField(blank=True, default=0, help_text='+ = abajo, − = arriba (desde punto de enfoque)', verbose_name='Offset Y (px)'),
        ),
        migrations.AddField(
            model_name='portfolioproject',
            name='img_zoom',
            field=models.DecimalField(blank=True, decimal_places=2, default=1.0, help_text='1.0 = normal · 0.5 = más contexto · 2.0 = acercar', max_digits=4, verbose_name='Zoom'),
        ),
        migrations.AddField(
            model_name='portfolioproject',
            name='img_x',
            field=models.IntegerField(blank=True, default=0, help_text='+ = derecha, − = izquierda (desde punto de enfoque)', verbose_name='Offset X (px)'),
        ),
        migrations.AddField(
            model_name='portfolioproject',
            name='img_y',
            field=models.IntegerField(blank=True, default=0, help_text='+ = abajo, − = arriba (desde punto de enfoque)', verbose_name='Offset Y (px)'),
        ),
        migrations.AlterModelOptions(
            name='mediaitem',
            options={
                'ordering': ['-year', 'order'],
                'permissions': [('edit_media_crop', 'Puede usar el editor de medios')],
                'verbose_name': 'Ítem de Medios',
                'verbose_name_plural': 'Ítems de Medios',
            },
        ),
        migrations.AlterModelOptions(
            name='portfolioproject',
            options={
                'ordering': ['order'],
                'permissions': [('edit_media_crop', 'Puede usar el editor de medios')],
                'verbose_name': 'Proyecto de Portafolio',
                'verbose_name_plural': 'Proyectos de Portafolio',
            },
        ),
    ]
