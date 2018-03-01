#!/usr/bin/env python
import redis
import ConfigParser
import socket
import json
import requests as req
from time import sleep
BUFSIZE = 4096


def adsb_poll(url, qfilter, r_client):
    print 'starting polling data ...'
    while True:
        try:
            resp = req.get('{}{}'.format(url, qfilter), timeout=60)
        except (req.exceptions.ConnectionError,
                req.exceptions.ReadTimeout, req.exceptions.Timeout):
            return True, '\nadsb server connection fail: \n{}\n'.format(resp)
        if resp.status_code != 200:
            return True, '\nadsb server returned bad code: \n{}\n'.format(resp)
        else:
            ac_list = resp.text
        icao_list = gen_icao_list(ac_list)
        rds_write_res, rds_write_err = wr_icao_redis(icao_list, r_client, 600)
        if rds_write_err:
            return True, rds_write_err
        sleep(300)


def adsb_stream(server, port, r_client):
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        s.connect((server, port))
        s.settimeout(60)
    except (socket.gaierror, socket.timeout) as e:
        return True, '\nadsb server connection fail: \n{}\n'.format(e.strerror)

    last_read = ''
    last_repeated_len = 0
    len_saved = 0
    print 'starting receiving data ...'
    while True:
        chunks = []
        bytes_recd = 0
        while bytes_recd < BUFSIZE:
            try:
                chunk = s.recv(min(BUFSIZE - bytes_recd, 2048))
            except socket.timeout as e:
                return None, '\nadsb connection fail: \n{}\n'.format(e.message)
            if chunk == b'':
                return True, "adsb server socket connection broken"
            chunks.append(chunk)
            bytes_recd = bytes_recd + len(chunk)
#           print 'received {} bytes of data ...'.format(bytes_recd)
        last_read = last_read + b''.join(chunks)
#       print 'current buffer size is {} ...'.format(len(last_read))
        if last_read.count('acList') >= 2:
            last_ac_list, remainder = get_one_aclist(last_read)
            last_read = remainder
            icao_list = gen_icao_list(last_ac_list)
            rds_write_res, rds_write_err = wr_icao_redis(icao_list,
                                                         r_client, 60)
            if rds_write_err:
                return True, rds_write_err
        len_last_read = len(last_read)
        if len_last_read > 10000000:
            return True, "Buffer runs to big"
        elif len_last_read == len_saved:
            if last_repeated_len >= 10:
                return True, "adsb server socket connection broken"
        len_saved = len_last_read


def get_one_aclist(in_string):
    first_pos = in_string.find('acList') - 2
    second_pos = in_string.find('acList', first_pos + 8) - 2
    print ' received a new acft list ...'
    return in_string[first_pos:second_pos], in_string[second_pos:]


def gen_icao_list(acft_json):
    acftdict = json.loads(acft_json)
    acft_list = acftdict.get('acList', None)
    icao_list = [acft.get('Icao', None) for acft in acft_list]
    return icao_list


def wr_icao_redis(icao_list, r_client, data_lifetime):
    pipe = r_client.pipeline()
    for icao in icao_list:
        pipe.hset(icao, "airborne", "true")
        pipe.expire(icao, data_lifetime)
    try:
        pipe.execute()
    except (redis.exceptions.ConnectionError,
            redis.exceptions.TimeoutError) as e:
        return None, '\nredis connection fail: \n{}\n'.format(e.message)
    print "wrote {} records into redis".format(len(icao_list))
    return True, None


def main():
    config = ConfigParser.ConfigParser()
    assert config.read('config/config.ini'), 'could not read config file'

    redis_server = config.get('main', 'redis_server')
    try:
        redis_port = int(config.get('main', 'redis_port'))
    except ConfigParser.NoOptionError:
        redis_port = 6379

    r_client = redis.StrictRedis(host=redis_server, port=redis_port,
                                 socket_timeout=10)

    if config.get('main', 'adsb_type') == 'stream':
        adsb_server_stream = config.get('main', 'adsb_server_stream')
        unrecoverable_error = False
        try:
            adsb_port = int(config.get('main', 'adsb_port'))
        except ConfigParser.NoOptionError:
            adsb_port = 32030
        while not unrecoverable_error:
            error, error_details = adsb_stream(adsb_server_stream, adsb_port,
                                               r_client)
            if error:
                print 'Error in data ret/wr loop:{}'.format(error_details)
            print 'Trying to start data retrieval loop again in 30 seconds\n'
            sleep(30)

    if config.get('main', 'adsb_type') == 'poll':

        unrecoverable_error = False
        adsb_server_url = config.get('main', 'adsb_server_poll_url')
        try:
            adsb_qfilter = config.get('main', 'adsb_poll_filter')
        except ConfigParser.NoOptionError:
            adsb_qfilter = '?fRegS=N'
        while not unrecoverable_error:
            error, error_details = adsb_poll(adsb_server_url, adsb_qfilter,
                                             r_client)
            if error:
                print 'Error in data poll loop:{}'.format(error_details)
            print 'Trying to start data poll loop again in 30 seconds\n'
            sleep(30)


if __name__ == '__main__':
    main()
