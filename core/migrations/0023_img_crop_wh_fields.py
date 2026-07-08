from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0022_portfolioprojectimage_crop_fields'),
    ]

    operations = [
        migrations.AddField(
            model_name='mediaitem',
            name='img_crop_w',
            field=models.PositiveIntegerField(default=0, verbose_name='Ancho recorte (px)'),
        ),
        migrations.AddField(
            model_name='mediaitem',
            name='img_crop_h',
            field=models.PositiveIntegerField(default=0, verbose_name='Alto recorte (px)'),
        ),
        migrations.AddField(
            model_name='portfolioproject',
            name='img_crop_w',
            field=models.PositiveIntegerField(default=0, verbose_name='Ancho recorte (px)'),
        ),
        migrations.AddField(
            model_name='portfolioproject',
            name='img_crop_h',
            field=models.PositiveIntegerField(default=0, verbose_name='Alto recorte (px)'),
        ),
        migrations.AddField(
            model_name='portfolioprojectimage',
            name='img_crop_w',
            field=models.PositiveIntegerField(default=0, verbose_name='Ancho recorte (px)'),
        ),
        migrations.AddField(
            model_name='portfolioprojectimage',
            name='img_crop_h',
            field=models.PositiveIntegerField(default=0, verbose_name='Alto recorte (px)'),
        ),
    ]
