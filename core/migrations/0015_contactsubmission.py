from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0014_curriculumitem_subtitle_en_curriculumitem_title_en_and_more'),
    ]

    operations = [
        migrations.CreateModel(
            name='ContactSubmission',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=200, verbose_name='Nombre')),
                ('phone', models.CharField(blank=True, max_length=50, verbose_name='Teléfono')),
                ('email', models.EmailField(max_length=254, verbose_name='Correo')),
                ('project_type', models.CharField(blank=True, max_length=200, verbose_name='Tipo de proyecto')),
                ('message', models.TextField(verbose_name='Mensaje')),
                ('created_at', models.DateTimeField(auto_now_add=True, verbose_name='Fecha de envío')),
                ('is_read', models.BooleanField(default=False, verbose_name='Leído')),
            ],
            options={
                'verbose_name': 'Consulta de Contacto',
                'verbose_name_plural': 'Consultas de Contacto',
                'ordering': ['-created_at'],
            },
        ),
    ]
