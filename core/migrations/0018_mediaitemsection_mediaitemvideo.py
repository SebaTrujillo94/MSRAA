from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0017_hero_slide_duration'),
    ]

    operations = [
        migrations.CreateModel(
            name='MediaItemSection',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('title', models.CharField(blank=True, max_length=200, verbose_name='Título de sección')),
                ('body', models.TextField(blank=True, verbose_name='Contenido')),
                ('order', models.PositiveIntegerField(default=0)),
                ('media_item', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='sections', to='core.mediaitem')),
            ],
            options={
                'verbose_name': 'Sección adicional',
                'verbose_name_plural': 'Secciones adicionales',
                'ordering': ['order'],
            },
        ),
        migrations.CreateModel(
            name='MediaItemVideo',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('video_url', models.URLField(max_length=500, verbose_name='URL de video', help_text='YouTube, Vimeo, Dropbox (.mp4 con ?raw=1), etc.')),
                ('caption', models.CharField(blank=True, max_length=200, verbose_name='Pie de video')),
                ('order', models.PositiveIntegerField(default=0)),
                ('media_item', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='videos', to='core.mediaitem')),
            ],
            options={
                'verbose_name': 'Video',
                'verbose_name_plural': 'Videos',
                'ordering': ['order'],
            },
        ),
    ]
