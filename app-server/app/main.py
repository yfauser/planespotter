from flask import Flask, jsonify
import flask_sqlalchemy
import flask_restless
import pymysql
import requests
import socket
import redis
pymysql.install_as_MySQLdb()

app = Flask(__name__)
app.config.from_pyfile('config/config.cfg')

database_uri = 'mysql://{}:{}@{}/{}'.format(app.config['DATABASE_USER'],
                                            app.config['DATABASE_PWD'],
                                            app.config['DATABASE_URL'],
                                            app.config['DATABASE'])
redis_server = app.config['REDIS_HOST']
redis_port = app.config['REDIS_PORT']
listen_port = int(app.config['LISTEN_PORT'])
app.config['SQLALCHEMY_DATABASE_URI'] = database_uri
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SQLALCHEMY_POOL_TIMEOUT'] = 2
db = flask_sqlalchemy.SQLAlchemy(app)

adsb_server = {'host': 'public-api.adsbexchange.com',
               'path': '/VirtualRadar/AircraftList.json',
               'query': '?fIcoQ='}
airport_data_server = {'host': 'www.airport-data.com',
                       'path': '/api/ac_thumb.json', 'query': '?m='}

r_client = redis.StrictRedis(host=redis_server, port=redis_port,
                             socket_timeout=3)


class Planetype(db.Model):
    __tablename__ = 'ACFTREF'
    code = db.Column('CODE', db.String(255), unique=True, primary_key=True)
    mfr = db.Column('MFR', db.String(255))
    model = db.Column('MODEL', db.String(255))
    tp_acft = db.Column('TYPE-ACFT', db.String(255))
    tp_eng = db.Column('TYPE-ENG', db.String(255))
    ac_cat = db.Column('AC-CAT', db.String(255))
    build_cert_ind = db.Column('BUILD-CERT-IND', db.String(255))
    no_eng = db.Column('NO-ENG', db.String(255))
    no_setas = db.Column('NO-SEATS', db.String(255))
    ac_weight = db.Column('AC-WEIGHT', db.String(255))
    speed = db.Column('SPEED', db.String(255))


class Plane(db.Model):
    __tablename__ = 'MASTER'
    n_number = db.Column('N-NUMBER', db.String(255), unique=True,
                         primary_key=True)
    serial_number = db.Column('SERIAL_NUMBER', db.String(255))
    mfr_mdl_code = db.Column('MFR_MDL_CODE', db.String(255),
                             db.ForeignKey('ACFTREF.CODE'))
    planedetails = db.relationship('Planetype')
    eng_mfr_mdl = db.Column('ENG_MFR_MDL', db.String(255))
    year_mfr = db.Column('YEAR_MFR', db.String(255))
    type_registrant = db.Column('TYPE_REGISTRANT', db.String(255))
    name = db.Column('NAME', db.String(255))
    street = db.Column('STREET', db.String(255))
    street2 = db.Column('STREET2', db.String(255))
    city = db.Column('CITY', db.String(255))
    state = db.Column('STATE', db.String(255))
    zip_code = db.Column('ZIP_CODE', db.String(255))
    county = db.Column('COUNTY', db.String(255))
    country = db.Column('COUNTRY', db.String(255))
    last_action_date = db.Column('LAST_ACTION_DATE', db.String(255))
    cert_issue_date = db.Column('CERT_ISSUE_DATE', db.String(255))
    certification = db.Column('CERTIFICATION', db.String(255))
    tp_aircraft = db.Column('TYPE_AIRCRAFT', db.String(255))
    tp_engine = db.Column('TYPE_ENGINE', db.String(255))
    status_code = db.Column('STATUS_CODE', db.String(255))
    mode_s_code = db.Column('MODE_S_CODE', db.String(255))
    fract_owner = db.Column('FRACT_OWNER', db.String(255))
    air_worth_date = db.Column('AIR_WORTH_DATE', db.String(255))
    other_names_1 = db.Column('OTHER_NAMES(1)', db.String(255))
    other_names_2 = db.Column('OTHER_NAMES(2)', db.String(255))
    other_names_3 = db.Column('OTHER_NAMES(3)', db.String(255))
    other_names_4 = db.Column('OTHER_NAMES(4)', db.String(255))
    other_names_5 = db.Column('OTHER_NAMES(5)', db.String(255))
    expiration_date = db.Column('EXPIRATION_DATE', db.String(255))
    unique_id = db.Column('UNIQUE_ID', db.String(255))
    kit_mfr = db.Column('KIT_MFR', db.String(255))
    kit_model = db.Column('KIT_MODEL', db.String(255))
    mode_s_code_hex = db.Column('MODE_S_CODE_HEX', db.String(255))

    def airborne(self):
        icao_stripped = self.mode_s_code_hex.strip()
        return get_redis_key(icao_stripped)


@app.route('/api/planedetails/<icao>')
def planedetails(icao):
    if not check_tcp_socket(adsb_server['host'], 80):
        return 'Connection to ADSB Exchange Server broken', 500

    req = requests.get('https://{}{}{}{}'.format(adsb_server['host'],
                                                 adsb_server['path'],
                                                 adsb_server['query'], icao))
    try:
        ac_details = req.json()['acList'][0]
        return jsonify(ac_details)
    except IndexError:
        return 'aircraft not found', 404


@app.route('/api/planepicture/<icao>')
def planepicture(icao):
    if not check_tcp_socket(airport_data_server['host'], 80):
        return 'Connection to Airport Data Server broken', 500

    req = requests.get('http://{}{}{}{}'.format(airport_data_server['host'],
                                                airport_data_server['path'],
                                                airport_data_server['query'],
                                                icao))
    try:
        ac_pictures = req.json()['data'][0]
        return jsonify(ac_pictures)
    except KeyError:
        message = req.json()
        return jsonify(message), 404


@app.route('/api/healthcheck')
def healthcheck():
    db_state = check_tcp_socket(app.config['DATABASE_URL'], 3306)
    position_data_state = check_tcp_socket(adsb_server['host'], 80)
    picture_data_state = check_tcp_socket(airport_data_server['host'], 80)
    redis_server = check_tcp_socket(app.config['REDIS_HOST'],
                                    int(app.config['REDIS_PORT']))

    return jsonify({'database_connection': db_state,
                    'position_data': position_data_state,
                    'picture_data': picture_data_state,
                    'redis_server': redis_server})


def check_tcp_socket(host, port, s_timeout=2):
    try:
        tcp_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        tcp_socket.settimeout(s_timeout)
        tcp_socket.connect((host, port))
        tcp_socket.close()
        return True
    except (socket.timeout, socket.error):
        return False


def check_db_connectivity(**kw):
    if not check_tcp_socket(app.config['DATABASE_URL'], 3306):
        raise flask_restless.ProcessingException(
            description='Database Connectivity Error', code=500)


def get_redis_key(icao):
    if not check_tcp_socket(app.config['REDIS_HOST'],
                            int(app.config['REDIS_PORT']), s_timeout=0.5):
        return False
    airborne_state = r_client.hget(icao, "airborne")
    if not airborne_state:
        return False
    else:
        return True


manager = flask_restless.APIManager(app, flask_sqlalchemy_db=db)
manager.create_api(Planetype, methods=['GET', 'POST', 'DELETE'],
                   collection_name='planetypes',
                   preprocessors={'GET_SINGLE': [check_db_connectivity],
                                  'GET_MANY': [check_db_connectivity],
                                  'DELETE': [check_db_connectivity]})
manager.create_api(Plane, methods=['GET', 'POST', 'DELETE'],
                   collection_name='planes',
                   preprocessors={'GET_SINGLE': [check_db_connectivity],
                                  'GET_MANY': [check_db_connectivity],
                                  'DELETE': [check_db_connectivity]},
                   include_methods=['airborne'])

if __name__ == '__main__':
    app.run(host='0.0.0.0', debug=False, threaded=True, port=listen_port)
