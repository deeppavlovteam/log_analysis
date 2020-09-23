from django.db import models

# Create your models here.

from django.db import models


class Record(models.Model):
    ip = models.CharField(max_length=20)
    time = models.DateTimeField('request time')
    file = models.TextField()
    md5 = models.BooleanField()
    config = models.TextField(null=True)
    response_code = models.PositiveIntegerField()
    bytes = models.BigIntegerField()
    ref = models.TextField()
    app = models.TextField()
    forwarded_for = models.TextField()
    outer_request = models.BooleanField()
    country = models.TextField(null=True)
    city = models.TextField(null=True)
    company = models.TextField(null=True)

    gz_hash = models.TextField()

    def __str__(self):
        return f'{self.ip} {self.time} {self.file}'


class Hash(models.Model):
    filename = models.TextField()
    hash = models.TextField()


class File(models.Model):
    name = models.TextField()
    downloads_number = models.BigIntegerField()
