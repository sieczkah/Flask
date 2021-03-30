from flask import Flask
from flask import flash, render_template, redirect, request, url_for
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime, timezone, timedelta
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
        if exists:  # checking existance in database
            flash('The city has already been added to the list!')

        elif city and exists is None:
            if check_response(city) == 200:  # checking response from the server
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
    url = f"{API_URL}?q={city}&APPID={API_KEY}"
    return requests.get(url).status_code


def get_localtime(_timezone):
    """From passed timezone returning local time in the town"""
    tz = timezone(timedelta(seconds=_timezone))
    time = datetime.now(tz)
    return time.strftime('%b %d %H:%M')


def get_daytime(_timezone, sunrise, sunset):
    """Returning time of the day in city"""
    tz = timezone(timedelta(seconds=_timezone))
    time = datetime.now(tz)
    sun_rise = datetime.fromtimestamp(sunrise, tz)
    sun_set = datetime.fromtimestamp(sunset, tz)
    # hour gap is an hour after sunrise and hour before sunset
    hour_gap = timedelta(hours=1)
    if (sun_set - hour_gap < time < sun_set + hour_gap or
            sun_rise - hour_gap < time < sun_rise + hour_gap):
        return 'evening-morning'
    elif sun_rise < time < sun_set:
        return 'day'
    else:
        return 'night'


def get_weather(_id, city, units='metric'):
    """With City, database ID and API key returns weather dictionary"""
    params = {'q': city, 'appid': API_KEY, 'units': units}
    req = requests.get(API_URL, params=params)
    if req.ok:
        data_json = req.json()
        weather = {'id': _id,
                   'city': f'{city}',
                   'state': data_json["weather"][0]["description"],
                   'temp': round(data_json["main"]["temp"]),
                   'daytime': get_daytime(
                       data_json["timezone"],
                       data_json['sys']['sunrise'],
                       data_json['sys']['sunset']
                   ),
                   'localtime': get_localtime(data_json["timezone"])
                   }
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
