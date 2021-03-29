from flask import Flask
from flask import flash, render_template, redirect, request, url_for
from flask_sqlalchemy import SQLAlchemy
import requests
import sys

SECRET_KEY = 'secret'
API_URL = 'http://api.openweathermap.org/data/2.5/weather'
with open('private.txt', 'r') as f1:
    API_KEY = f1.read()

app = Flask(__name__)

app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///weather.db'
db = SQLAlchemy(app)
app.config['SECRET_KEY'] = SECRET_KEY


class Cities(db.Model):
    """Data model for cities"""
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(20), unique=True, nullable=False)

    def __repr__(self):
        return f'{self.id} {self.name.upper()}'


@app.route('/')
def index():
    cities = Cities.query.all()
    weather_list = [get_weather(city.id, city.name) for city in cities]
    return render_template('index.html', weather_list=weather_list)


@app.route('/add', methods=['POST', 'GET'])
def add_city():
    if request.method == 'POST':
        city = request.form["city_name"]
        exists = Cities.query.filter_by(name=city).first()
        if exists:
            flash('The city has already been added to the list!')

        elif city and exists is None:
            if check_response(city) == 200:
                db.session.add(Cities(name=city))
                db.session.commit()
            else:
                flash("The city doesn't exist!")
        return redirect(url_for('index'))
    else:
        return redirect(url_for('index'))


@app.route('/delete/<city_id>', methods=['GET', 'POST'])
def delete(city_id):
    city = Cities.query.filter_by(id=city_id).first()
    db.session.delete(city)
    db.session.commit()
    return redirect('/')


def check_response(city):
    url = f"{API_URL}q={city}&APPID={API_KEY}"
    return requests.get(url).status_code


def get_weather(id, city, units='metric'):
    url = f"{API_URL}q={city}&APPID={API_KEY}&units={units}"
    req = requests.get(url)
    if req.ok:
        data = req.json()
        weather = {'id': id, 'city': f'{city}', 'state': data["weather"][0]["description"],
                   'temp': round(data["main"]["temp"])}
        return weather
    else:
        return False


if __name__ == '__main__':
    db.create_all()
    if len(sys.argv) > 1:
        arg_host, arg_port = sys.argv[1].split(':')
        app.run(host=arg_host, port=arg_port)
    else:
        app.run(debug=True)
