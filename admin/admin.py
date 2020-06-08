from flask import Flask, render_template, request, url_for
from sqlalchemy import text, create_engine

app = Flask(__name__)

engine = create_engine(f'postgresql://nginx:nginx@192.168.10.78/nginx_logs')


def get_table():
    with engine.connect() as connection:
        res = connection.execute(text('select config.name, (select count(*) from record where record.file=any(config.files) and record.outer_request is True) as TOT,'
                                      ' cardinality(config.files) from config'))
        res = [{'name': name, 'popularity': round(cnt/ln,1)} for name, cnt, ln in res]
    return sorted(res, key=lambda x: x['popularity'], reverse=True)


def get_countries(name):
    with engine.connect() as connection:
        res = connection.execute(text(f"select country, count(*) from record where file=any(select unnest(files) from config where name='{name}') and outer_request is true group by country;"))
        res = [{'country': cnt, 'reqs': reqs} for cnt, reqs in res]
        total = sum([x['reqs'] for x in res])
        [x.update({'%': round(x['reqs']*100/total, 2)}) for x in res]
    return sorted(res, key=lambda x: x['reqs'], reverse=True)


@app.route("/", methods=['POST', 'GET'])
def table():
    if request.method == 'GET':
        dict_table = get_table()
        return render_template('table.html', dict_table=dict_table)


@app.route('/<name>')
def stat(name):
    return render_template('country.html', dict_table=get_countries(str(name)))

if __name__ == '__main__':
    app.run(debug=True)