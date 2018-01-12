from flask import Flask, jsonify
import flask_sqlalchemy
import flask_restless
import pymysql
import requests
pymysql.install_as_MySQLdb()

app = Flask(__name__)
app.config.from_pyfile('config/config.cfg')
database_uri = 'mysql://{}:{}@{}/{}'.format(app.config['DATABASE_USER'],
                                            app.config['DATABASE_PWD'],
                                            app.config['DATABASE_URL'],
                                            app.config['DATABASE'])
app.config['SQLALCHEMY_DATABASE_URI'] = database_uri
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = flask_sqlalchemy.SQLAlchemy(app)


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


@app.route('/api/planedetails/<icao>')
def planedetails(icao):
    host = 'public-api.adsbexchange.com'
    path = '/VirtualRadar/AircraftList.json'
    query = '?fIcoQ={}'.format(icao)
    req = requests.get('http://{}{}{}'.format(host, path, query))

    try:
        ac_details = req.json()['acList'][0]
        return jsonify(ac_details)
    except IndexError:
        return 'aircraft not found', 404


@app.route('/api/planepicture/<icao>')
def planepicture(icao):
    host = 'www.airport-data.com'
    path = '/api/ac_thumb.json'
    query = '?m={}'.format(icao)
    req = requests.get('http://{}{}{}'.format(host, path, query))

    try:
        ac_pictures = req.json()['data'][0]
        return jsonify(ac_pictures)
    except KeyError:
        message = req.json()
        return jsonify(message), 404


manager = flask_restless.APIManager(app, flask_sqlalchemy_db=db)
manager.create_api(Planetype, methods=['GET', 'POST', 'DELETE'],
                   collection_name='planetypes')
manager.create_api(Plane, methods=['GET', 'POST', 'DELETE'],
                   collection_name='planes')

if __name__ == '__main__':
    app.run(host='0.0.0.0', debug=False, threaded=True, port=80)
