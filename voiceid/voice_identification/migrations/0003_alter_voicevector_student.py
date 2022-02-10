# Generated by Django 3.2.11 on 2022-02-07 02:28

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('voice_identification', '0002_voicevector'),
    ]

    operations = [
        migrations.AlterField(
            model_name='voicevector',
            name='student',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, primary_key=True, serialize=False, to='voice_identification.student', unique=True),
        ),
    ]
