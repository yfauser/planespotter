#!/usr/bin/env python
import redis
import ConfigParser
import socket
import json
BUFSIZE = 4096


def adsb_stream(server, port):
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.connect((server, port))

    last_read = ''
    print 'starting receiving data ... \n\n'
    while True:
        chunks = []
        bytes_recd = 0
        while bytes_recd < BUFSIZE:
            chunk = s.recv(min(BUFSIZE - bytes_recd, 2048))
            if chunk == b'':
                raise RuntimeError("socket connection broken")
            chunks.append(chunk)
            bytes_recd = bytes_recd + len(chunk)
#           print 'received {} bytes of data ...'.format(bytes_recd)
        last_read = last_read + b''.join(chunks)
        print 'current buffer size is {} ...'.format(len(last_read))
        if last_read.count('acList') >= 2:
            last_ac_list, remainder = get_one_aclist(last_read)
            icao_list = gen_icao_list(last_ac_list)
            print '\n\n{}'.format(icao_list)
            last_read = remainder
        if len(last_read) > 10000000:
            raise RuntimeError("Buffer runs to big")


def get_one_aclist(in_string):
    first_pos = in_string.find('acList') - 2
    second_pos = in_string.find('acList', first_pos + 8) - 2
    print ' \nreceived a new acft list ...\n'
    return in_string[first_pos:second_pos], in_string[second_pos:]


def gen_icao_list(acft_json):
    acftdict = json.loads(acft_json)
    acft_list = acftdict.get('acList', None)
    icao_list = [acft.get('Icao', None) for acft in acft_list]
    return icao_list


def main():
    config = ConfigParser.ConfigParser()
    assert config.read('config/config.ini'), 'could not read config file'

    REDIS_SERVER = config.get('main', 'redis_server')
    try:
        REDIS_PORT = int(config.get('main', 'redis_port'))
    except ConfigParser.NoOptionError:
        REDIS_PORT = 6379

    ADSB_SERVER = config.get('main', 'adsb_server')
    try:
        ADSB_PORT = int(config.get('main', 'adsb_port'))
    except ConfigParser.NoOptionError:
        ADSB_PORT = 32030

    adsb_stream(ADSB_SERVER, ADSB_PORT)

    #CLIENT = redis.StrictRedis(host=REDIS_SERVER, port=REDIS_PORT)

    #print dir(CLIENT)

    #CLIENT.hset("A0001", "airborne", "true")
    #CLIENT.expire("A0001", 30)


if __name__ == '__main__':
    main()
