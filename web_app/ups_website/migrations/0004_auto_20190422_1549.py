# Generated by Django 2.2 on 2019-04-22 15:49

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('ups_website', '0003_auto_20190422_0118'),
    ]

    operations = [
        migrations.AlterField(
            model_name='package_info',
            name='package_status',
            field=models.CharField(choices=[('a', 'waiting for package'), ('b', 'out for delivery'), ('c', 'delivered')], default='a', max_length=30),
        ),
        migrations.AlterField(
            model_name='package_info',
            name='truck_id',
            field=models.IntegerField(),
        ),
        migrations.AlterField(
            model_name='truck_info',
            name='truck_status',
            field=models.CharField(choices=[('a', 'idle'), ('b', 'travelling'), ('c', 'arrive warehouse'), ('d', 'loading'), ('e', 'delivering')], default='a', max_length=30),
        ),
    ]
