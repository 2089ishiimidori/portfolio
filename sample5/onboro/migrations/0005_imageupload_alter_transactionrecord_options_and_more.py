# Generated by Django 5.1.5 on 2025-01-31 16:26

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('onboro', '0004_transactionrecord'),
    ]

    operations = [
        migrations.CreateModel(
            name='ImageUpload',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('image', models.ImageField(upload_to='images/')),
                ('description', models.CharField(blank=True, max_length=255)),
            ],
        ),
        migrations.AlterModelOptions(
            name='transactionrecord',
            options={'verbose_name': '取引記録', 'verbose_name_plural': '取引記録'},
        ),
        migrations.AddField(
            model_name='book',
            name='image',
            field=models.ImageField(default='default_image_path.jpg', upload_to='images/', verbose_name='画像'),
        ),
        migrations.AddField(
            model_name='user',
            name='books',
            field=models.ManyToManyField(through='onboro.TransactionRecord', to='onboro.book'),
        ),
    ]
