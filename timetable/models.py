import datetime

from django.db import models

# Create your models here.
class Schedule(models.Model):
    team_name = models.CharField(max_length=200)
    start_time = models.DateTimeField('시작')
    end_time = models.DateTimeField('끝')

    def __str__(self):
        return self.team_name

    def valid_schedule(self):
        return self.start_time < self.end_time

    def is_in_limit(self):
        return self.end_time <= self.start_time + datetime.timedelta(hours=2)

    def is_collision(self):
        for time in Schedule.objects.all():
            if not (self.end_time <= time.start_time or self.start_time >= time.end_time):
                return False
        return True

class Stack(models.Model):
    name = models.CharField(max_length=100)
    value = models.IntegerField(default=0)

    def __str__(self):
        return self.name

    def is_valid(self):
        return self.value>=0

    def is_full(self):
        return self.value>2
