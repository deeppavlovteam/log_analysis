from django.db import models

# Create your models here.

from django.db import models


class File(models.Model):
    name = models.TextField(unique=True)
    md5 = models.BooleanField()


class ConfigName(models.Model):
    name = models.TextField(unique=True)
    def __str__(self):
        return self.name


class Config(models.Model):
    type = models.TextField()
    name = models.ForeignKey(ConfigName, on_delete=models.CASCADE)
    dp_version = models.TextField()
    files = models.TextField()


class Record(models.Model):
    ip = models.CharField(max_length=20)
    time = models.DateTimeField('request time')
    file = models.ForeignKey(File, on_delete=models.CASCADE)
    config = models.ForeignKey(ConfigName, on_delete=models.CASCADE)
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
