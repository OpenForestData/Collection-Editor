# Generated by Django 2.2.13 on 2020-07-30 09:55

from django.conf import settings
import django.contrib.postgres.fields
import django.contrib.postgres.fields.jsonb
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='Datatable',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('title', models.CharField(max_length=255)),
                ('collection_name', models.CharField(max_length=255, unique=True)),
                ('columns', django.contrib.postgres.fields.ArrayField(base_field=models.TextField(blank=True), blank=True, null=True, size=None)),
            ],
        ),
        migrations.CreateModel(
            name='DatatableAction',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('action', models.CharField(choices=[('CREATE', 'CREATE'), ('UPDATE', 'UPDATE'), ('DELETE', 'DELETE')], max_length=10)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('old_row', django.contrib.postgres.fields.jsonb.JSONField(null=True)),
                ('new_row', django.contrib.postgres.fields.jsonb.JSONField(null=True)),
                ('reverted', models.BooleanField(default=False)),
                ('datatable', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='core.Datatable')),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.DO_NOTHING, to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'ordering': ['-created_at'],
            },
        ),
    ]
