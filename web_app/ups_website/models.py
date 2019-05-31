from django.db import models
from django.utils.timezone import now
from model_utils import Choices
# from django.contrib.postgres.fields import ArrayField
# Create your models here.
class account_info(models.Model):
    username = models.CharField(max_length = 50)
    email = models.CharField(max_length = 50)
    password = models.CharField(max_length = 50)


class truck_info(models.Model):
	truck_id = models.IntegerField(primary_key = True)
	STATUS = Choices(('a', 'idle'), ('b', 'travelling'), ('c', 'arrive warehouse'), ('d', 'loading'), ('e', 'delivering'))
	truck_status = models.CharField(max_length=30, choices = STATUS, default = STATUS.a)
	pos_x = models.FloatField()
	pos_y = models.FloatField()

class package_info(models.Model):
	package_id = models.IntegerField(primary_key = True)
	username = models.CharField(max_length = 50)
	dest_x = models.FloatField()
	dest_y = models.FloatField()
	STATUS = Choices(('a', 'in warehouse'), ('b', 'out for delivery'), ('c', 'delivered'))
	package_status = models.CharField(max_length=30, choices = STATUS, default = STATUS.a)
	truck_id = models.IntegerField()


class time(models.Model):
	package_id = models.IntegerField()
	time1 = models.DateTimeField(default=now, editable=False)
	time2 = models.DateTimeField(default=now, editable=False)
	time3 = models.DateTimeField(default=now, editable=False)



