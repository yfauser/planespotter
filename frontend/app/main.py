from flask import Flask, render_template, request
from flask_paginate import Pagination, get_page_args
import requests as req
import os
import json

app = Flask(__name__)
port = os.getenv('PORT', '5000')
app_server_hostname = os.getenv('PLANESPOTTER_API_ENDPOINT', 'localhost')
registry_url = 'http://{}/api/planes'.format(app_server_hostname)
planetypes_url = 'http://{}/api/planetypes'.format(app_server_hostname)
planedetails_url = 'http://{}/api/planedetails'.format(app_server_hostname)
planepicture_url = 'http://{}/api/planepicture'.format(app_server_hostname)


@app.route('/')
@app.route('/index.html')
def index():
    return render_template('index.html')


@app.route('/registry.html')
def registry():
    page, per_page, offset = get_page_args()

    req_params = {'page': page}

    search_owner = request.args.get('owner', None)
    search_reg = request.args.get('reg', None)
    search_model = request.args.get('model', None)
    search_mfr = request.args.get('mfr', None)

    req_filters = []
    if search_owner:
        search_owner = '%{}%'.format(search_owner)
        req_filters.append({"name": "name", "op": "like", "val": search_owner})
    if search_reg:
        req_filters.append({"name": "n_number", "op": "eq",
                            "val": search_reg})
    if search_model:
        search_model = '%{}%'.format(search_model)
        planedetails_model_fiter = {"name": "model", "op": "like",
                                    "val": search_model}
        req_filters.append({"name": "planedetails", "op": "has",
                            "val": planedetails_model_fiter})
    if search_mfr:
        search_mfr = '%{}%'.format(search_mfr)
        planedetails_mfr_fiter = {"name": "mfr", "op": "like",
                                  "val": search_mfr}
        req_filters.append({"name": "planedetails", "op": "has",
                            "val": planedetails_mfr_fiter})

    if search_owner or search_reg or search_model or search_mfr:
        req_params['q'] = json.dumps(dict(filters=req_filters))

    headers = {'Content-Type': 'application/json'}
    resp = req.get(registry_url, params=req_params, headers=headers).json()

    acfts_raw = resp.get('objects', None)
    acfts = [trim_dict_content(acft_raw) for acft_raw in acfts_raw]
    num_results = resp.get('num_results', 1)
    pagination = Pagination(page=page, total=num_results,
                            record_name='Aircrafts', bs_version=3)

    return render_template('registry.html', acfts=acfts, pagination=pagination)


@app.route('/details.html')
def details():
    search_icoa = request.args.get('icao', None)
    search_reg = request.args.get('reg', None)
    req_headers = {'Content-Type': 'application/json'}

    if not search_icoa or search_icoa == '':
        if search_reg and search_reg != '':
            req_filters = [{"name": "n_number", "op": "eq", "val": search_reg}]
            req_params = {}
            req_params['q'] = json.dumps(dict(filters=req_filters))
            resp = req.get(registry_url, params=req_params,
                           headers=req_headers).json()
            acfts_raw = resp.get('objects', None)
            if acfts_raw:
                acft = trim_dict_content(acfts_raw[0])
                icao = acft.get('mode_s_code_hex', None)
            else:
                return render_template('details.html', search=False)
        else:
            return render_template('details.html', search=False)
    else:
        req_filters = [{"name": "mode_s_code_hex", "op": "eq",
                        "val": search_icoa}]
        req_params = {}
        req_params['q'] = json.dumps(dict(filters=req_filters))
        resp = req.get(registry_url, params=req_params,
                       headers=req_headers).json()
        acfts_raw = resp.get('objects', None)
        if acfts_raw:
            acft = trim_dict_content(acfts_raw[0])
        else:
            acft = None
        icao = search_icoa

    resp = req.get('{}/{}'.format(planedetails_url, icao))
    if resp.status_code == 200:
        plane_details = resp.json()
    else:
        plane_details = None

    resp = req.get('{}/{}'.format(planepicture_url, icao))
    if resp.status_code == 200:
        plane_picture = resp.json()
    else:
        plane_picture = None

    return render_template('details.html', acft=acft, picture=plane_picture,
                           acft_details=plane_details, icao=icao, search=True)


@app.route('/health.html')
def health():
    return render_template('health.html')


@app.route('/contact.html')
def contact():
    return render_template('contact.html')


def trim_dict_content(dict_to_trim):
    new_dict = {}
    for key, value in dict_to_trim.iteritems():
        if isinstance(value, unicode) or isinstance(value, basestring):
            trimmed = value.strip()
            new_dict[key] = trimmed
        elif isinstance(value, dict):
            new_sub_dict = {}
            for sub_key, sub_value in value.iteritems():
                trimmed = sub_value.strip()
                new_sub_dict[sub_key] = trimmed
            new_dict[key] = new_sub_dict
    return new_dict


debugmode = os.getenv('DEBUG_MODE', False)
if __name__ == '__main__':
    app.run(host='0.0.0.0', debug=debugmode, port=int(port))
