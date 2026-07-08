from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0021_img_crop_bg_fields'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='portfolioprojectimage',
            name='size',
        ),
        migrations.AddField(
            model_name='portfolioprojectimage',
            name='img_gravity',
            field=models.CharField(blank=True, default='auto', max_length=20, verbose_name='Punto de enfoque'),
        ),
        migrations.AddField(
            model_name='portfolioprojectimage',
            name='img_ratio',
            field=models.CharField(blank=True, default='', max_length=10, verbose_name='Proporción'),
        ),
        migrations.AddField(
            model_name='portfolioprojectimage',
            name='img_zoom',
            field=models.DecimalField(decimal_places=2, default=1.0, max_digits=4, verbose_name='Zoom'),
        ),
        migrations.AddField(
            model_name='portfolioprojectimage',
            name='img_x',
            field=models.IntegerField(default=0, verbose_name='Ajuste X'),
        ),
        migrations.AddField(
            model_name='portfolioprojectimage',
            name='img_y',
            field=models.IntegerField(default=0, verbose_name='Ajuste Y'),
        ),
        migrations.AddField(
            model_name='portfolioprojectimage',
            name='img_crop',
            field=models.CharField(
                blank=True, default='fill', max_length=10,
                choices=[
                    ('fill', 'Rellenar (c_fill) — recorta para llenar'),
                    ('fit', 'Ajustar (c_fit) — escala sin recortar'),
                    ('pad', 'Añadir fondo (c_pad) — letterbox/pillarbox'),
                    ('scale', 'Estirar (c_scale) — deforma proporciones'),
                ],
                verbose_name='Modo de recorte',
            ),
        ),
        migrations.AddField(
            model_name='portfolioprojectimage',
            name='img_bg',
            field=models.CharField(blank=True, default='', max_length=30, verbose_name='Color de fondo'),
        ),
    ]
