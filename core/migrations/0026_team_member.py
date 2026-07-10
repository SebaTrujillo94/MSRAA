from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0025_monitor_models'),
    ]

    operations = [
        migrations.CreateModel(
            name='TeamMember',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=200, verbose_name='Nombre')),
                ('role', models.CharField(blank=True, max_length=200, verbose_name='Cargo')),
                ('role_en', models.CharField(blank=True, max_length=200, verbose_name='Cargo (EN)')),
                ('bio', models.TextField(blank=True, verbose_name='Descripción breve')),
                ('bio_en', models.TextField(blank=True, verbose_name='Descripción breve (EN)')),
                ('image_url', models.URLField(blank=True, max_length=500, verbose_name='Foto (URL Cloudinary)')),
                ('img_gravity', models.CharField(blank=True, choices=[('auto', 'Automático (IA)'), ('face', 'Cara'), ('faces', 'Caras múltiples'), ('center', 'Centro'), ('north', 'Arriba'), ('south', 'Abajo'), ('east', 'Derecha'), ('west', 'Izquierda'), ('northeast', 'Arriba-Derecha'), ('northwest', 'Arriba-Izquierda'), ('southeast', 'Abajo-Derecha'), ('southwest', 'Abajo-Izquierda')], default='face', max_length=20, verbose_name='Punto de enfoque')),
                ('img_ratio', models.CharField(blank=True, choices=[('', 'Original'), ('16:9', '16:9 — Panorámico'), ('4:3', '4:3 — Clásico'), ('3:2', '3:2 — Foto'), ('1:1', '1:1 — Cuadrado'), ('2:3', '2:3 — Retrato')], default='1:1', max_length=10, verbose_name='Proporción')),
                ('img_x', models.IntegerField(blank=True, default=0, verbose_name='Ajuste X')),
                ('img_y', models.IntegerField(blank=True, default=0, verbose_name='Ajuste Y')),
                ('img_crop_w', models.PositiveIntegerField(blank=True, default=0, verbose_name='Recorte ancho px')),
                ('img_crop_h', models.PositiveIntegerField(blank=True, default=0, verbose_name='Recorte alto px')),
                ('img_crop', models.CharField(blank=True, choices=[('fill', 'Rellenar (c_fill) — recorta para llenar'), ('fit', 'Ajustar (c_fit) — escala sin recortar'), ('pad', 'Añadir fondo (c_pad) — letterbox/pillarbox'), ('scale', 'Estirar (c_scale) — deforma proporciones')], default='fill', max_length=10, verbose_name='Modo de recorte')),
                ('img_bg', models.CharField(blank=True, default='', max_length=30, verbose_name='Color de fondo')),
                ('order', models.PositiveIntegerField(default=0, verbose_name='Orden')),
                ('is_active', models.BooleanField(default=True, verbose_name='Activo')),
            ],
            options={
                'verbose_name': 'Colaborador',
                'verbose_name_plural': 'Colaboradores',
                'ordering': ['order', 'name'],
            },
        ),
    ]
