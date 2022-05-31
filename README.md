# TODO
- return upd_database to geo wrapper
- add colab region distinction

### Create db

```commandline
python manage.py createsuperuser
python manage.py runserver
python manage.py makemigrations stats
python manage.py migrate
```

### Create/update deeppavlov configs structure

```commandline
python manage.py shell -c 'from poller import upd_deeppavlov; upd_deeppavlov()'
```

### Update data

```commandline
python manage.py shell -c 'from poller import boo; boo()'
```

### Start server
```commandline
python manage.py runserver 0.0.0.0:7050
```


updating example:
select * from stats_config, stats_configname where stats_config.name_id = stats_configname.id and name in ('kbqa_cq', 'kbqa_cq_bert_ranker', 'kbqa_cq_mt_bert', 'kbqa_cq_online', 'kbqa_cq_online_mt_bert', 'kbqa_cq_rus', 'kbqa_cq_sep', 'kbqa_mt_bert_train');
update stats_config set category = 'KBQA' from stats_configname where stats_config.name_id = stats_configname.id and name in ('kbqa_cq', 'kbqa_cq_bert_ranker', 'kbqa_cq_mt_bert', 'kbqa_cq_online', 'kbqa_cq_online_mt_bert', 'kbqa_cq_rus', 'kbqa_cq_sep', 'kbqa_mt_bert_train');

cd log_stuff/data/nginx/
scp ignatov@share.ipavlov.mipt.ru:/var/log/nginx/* ./
