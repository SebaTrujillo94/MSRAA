from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0020_media_editor_fields'),
    ]

    operations = [
        migrations.AddField(
            model_name='mediaitem',
            name='img_crop',
            field=models.CharField(
                blank=True, default='fill', max_length=10,
                choices=[
                    ('fill',  'Rellenar (c_fill) — recorta para llenar'),
                    ('fit',   'Ajustar (c_fit) — escala sin recortar'),
                    ('pad',   'Añadir fondo (c_pad) — letterbox/pillarbox'),
                    ('scale', 'Estirar (c_scale) — deforma proporciones'),
                ],
                verbose_name='Modo de recorte',
            ),
        ),
        migrations.AddField(
            model_name='mediaitem',
            name='img_bg',
            field=models.CharField(
                blank=True, default='', max_length=30,
                verbose_name='Color de fondo',
            ),
        ),
        migrations.AddField(
            model_name='portfolioproject',
            name='img_crop',
            field=models.CharField(
                blank=True, default='fill', max_length=10,
                choices=[
                    ('fill',  'Rellenar (c_fill) — recorta para llenar'),
                    ('fit',   'Ajustar (c_fit) — escala sin recortar'),
                    ('pad',   'Añadir fondo (c_pad) — letterbox/pillarbox'),
                    ('scale', 'Estirar (c_scale) — deforma proporciones'),
                ],
                verbose_name='Modo de recorte',
            ),
        ),
        migrations.AddField(
            model_name='portfolioproject',
            name='img_bg',
            field=models.CharField(
                blank=True, default='', max_length=30,
                verbose_name='Color de fondo',
            ),
        ),
    ]
