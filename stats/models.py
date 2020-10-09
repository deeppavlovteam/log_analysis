from django.db import models
from django.db.models.functions import Concat


class ConfigName(models.Model):
    name = models.TextField(unique=True)
    def __str__(self):
        return self.name


class File(models.Model):
    name = models.TextField(unique=True)
    md5 = models.BooleanField()
    def configs(self):
        return ', '.join(self.config_set.annotate(config_ver=Concat('name__name', models.Value(' ('), 'dp_version', models.Value(')'), output_field=models.CharField())).values_list('config_ver', flat=True))
    def __str__(self):
        return self.name


class Config(models.Model):
    type = models.TextField()
    name = models.ForeignKey(ConfigName, on_delete=models.CASCADE)
    dp_version = models.TextField()
    files = models.ManyToManyField(File)
    def files_display(self):
        return ', '.join([f.name for f in self.files.all()])

class Record(models.Model):
    ip = models.CharField(max_length=20)
    time = models.DateTimeField('request time')
    file = models.ForeignKey(File, on_delete=models.CASCADE)
    config = models.ForeignKey(ConfigName, on_delete=models.CASCADE, null=True, blank=True)
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
