import sys, logging, datetime, urllib.request, urllib.parse, urllib.error, urllib.request, urllib.error, urllib.parse, json, requests, urllib.parse

from os import curdir, sep
from http.server import BaseHTTPRequestHandler
from requests.auth import HTTPBasicAuth

# configuration
jdata = json.load(open('/data/options.json'))

DEBUG = bool(jdata['debug'])
DEFAULT_PORT = int(jdata['proxy_port'])

host = str(jdata['ecoforest_host'])
username = str(jdata['ecoforest_user'])
passwd = str(jdata['ecoforest_pass'])
heatertype = str(jdata['type']) if 'type' in jdata else 'stove'
stove = heatertype == 'stove'

ECOFOREST_URL = host + '/recepcion_datos_4.cgi'

REGISTER_TYPE_DIGITAL = 1
REGISTER_TYPE_INTEGER = 2
REGISTER_TYPE_ANALOG = 3

heat_pump_registers_2001 = {
    61: { 'id':'estado_piscina', 't':REGISTER_TYPE_DIGITAL },
    105: { 'id':'heating_status', 't':REGISTER_TYPE_DIGITAL },
    208: { 'id':'dhw_heating', 't':REGISTER_TYPE_DIGITAL },
    209: { 'id':'piscina', 't':REGISTER_TYPE_DIGITAL },
    206: { 'id':'calefaccion_directa', 't':REGISTER_TYPE_DIGITAL },
    249: { 'id':'calefaccion_inercia', 't':REGISTER_TYPE_DIGITAL },
    207: { 'id':'refrigeracion_directa', 't':REGISTER_TYPE_DIGITAL },
    250: { 'id':'refrigeracion_inercia', 't':REGISTER_TYPE_DIGITAL },
    210: { 'id':'htr', 't':REGISTER_TYPE_DIGITAL },
    211: { 'id':'recirc_acs', 't':REGISTER_TYPE_DIGITAL },
}

heat_pump_registers_2002 = {
    1: { 'id':'heating_outlet_temperature', 't':REGISTER_TYPE_ANALOG },
    2: { 'id':'heating_inlet_temperature', 't':REGISTER_TYPE_ANALOG },
    3: { 'id':'heating_real_temperature_1', 't':REGISTER_TYPE_ANALOG },
    4: { 'id':'outlet_heating_temperature', 't':REGISTER_TYPE_ANALOG },
    8: { 'id':'dhw_temperature', 't':REGISTER_TYPE_ANALOG },
    13: { 'id':'pcp_a', 't':REGISTER_TYPE_ANALOG },
    14: { 'id':'pcc_a', 't':REGISTER_TYPE_ANALOG },
    15: { 'id':'offset', 't':REGISTER_TYPE_ANALOG },
    19: { 'id':'imp_pool', 't':REGISTER_TYPE_ANALOG },
    11: { 'id':'outdoor_temperature', 't':REGISTER_TYPE_ANALOG },
    22: { 'id':'temp_cal', 't':REGISTER_TYPE_ANALOG },
    30: { 'id':'cop_value', 't':REGISTER_TYPE_ANALOG },
    31: { 'id':'pf_value', 't':REGISTER_TYPE_ANALOG },
    55: { 'id':'offset_inercia_cool', 't':REGISTER_TYPE_ANALOG },
    58: { 'id':'offset_inercia_heat', 't':REGISTER_TYPE_ANALOG },
    97: { 'id':'heating_set_temperature_1', 't':REGISTER_TYPE_ANALOG },
    98: { 'id':'set_th1_1', 't':REGISTER_TYPE_ANALOG },
    99: { 'id':'set_th2_1', 't':REGISTER_TYPE_ANALOG },
    125: { 'id':'temp_ref_act', 't':REGISTER_TYPE_ANALOG },
    120: { 'id':'set_th3_1', 't':REGISTER_TYPE_ANALOG },
    123: { 'id':'set_th4_1', 't':REGISTER_TYPE_ANALOG },
    126: { 'id':'temp_ref', 't':REGISTER_TYPE_ANALOG },
    176: { 'id':'c_dg1', 't':REGISTER_TYPE_ANALOG },
    177: { 'id':'c_dg2', 't':REGISTER_TYPE_ANALOG },
    178: { 'id':'c_dg3', 't':REGISTER_TYPE_ANALOG },
    179: { 'id':'c_dg4', 't':REGISTER_TYPE_ANALOG },
    186: { 'id':'d_dg1', 't':REGISTER_TYPE_ANALOG },
    187: { 'id':'d_dg2', 't':REGISTER_TYPE_ANALOG },
    188: { 'id':'d_dg3', 't':REGISTER_TYPE_ANALOG },
    189: { 'id':'d_dg4', 't':REGISTER_TYPE_ANALOG },
    190: { 'id':'h_dg1', 't':REGISTER_TYPE_ANALOG },
    191: { 'id':'h_dg2', 't':REGISTER_TYPE_ANALOG },
    192: { 'id':'h_dg3', 't':REGISTER_TYPE_ANALOG },
    193: { 'id':'h_dg4', 't':REGISTER_TYPE_ANALOG },
    194: { 'id':'heating_real_temperature_2', 't':REGISTER_TYPE_ANALOG },
    195: { 'id':'heating_real_temperature_3', 't':REGISTER_TYPE_ANALOG },
    196: { 'id':'heating_real_temperature_4', 't':REGISTER_TYPE_ANALOG },
    198: { 'id':'comp_on_t', 't':REGISTER_TYPE_ANALOG },
    200: { 'id':'temp_dep_heat', 't':REGISTER_TYPE_ANALOG },
    201: { 'id':'temp_dep_cool', 't':REGISTER_TYPE_ANALOG },
    215: { 'id':'set_inercia_heat', 't':REGISTER_TYPE_ANALOG },
    216: { 'id':'set_inercia_cool', 't':REGISTER_TYPE_ANALOG },
    214: { 'id':'consigna_acs', 't':REGISTER_TYPE_ANALOG },
    202: { 'id':'eer_value', 't':REGISTER_TYPE_ANALOG },
    5033: { 'id':'reg_bc_a', 't':REGISTER_TYPE_ANALOG },
    5034: { 'id':'reg_bp_a', 't':REGISTER_TYPE_ANALOG },
    5066: { 'id':'heating_set_temperature_2', 't':REGISTER_TYPE_ANALOG },
    5082: { 'id':'electric_energy', 't':REGISTER_TYPE_INTEGER },
    5083: { 'id':'useful_heat_power', 't':REGISTER_TYPE_INTEGER },
    5113: { 'id':'heating_set_temperature_3', 't':REGISTER_TYPE_ANALOG },
    5185: { 'id':'useful_cool_power', 't':REGISTER_TYPE_INTEGER },
    5206: { 'id':'heating_set_temperature_4', 't':REGISTER_TYPE_ANALOG },
    5210: { 'id':'heating_regulation_2', 't':REGISTER_TYPE_ANALOG },
    5209: { 'id':'heating_regulation_3', 't':REGISTER_TYPE_ANALOG },
    5211: { 'id':'heating_regulation_4', 't':REGISTER_TYPE_ANALOG },
    5271: { 'id':'zone_1_active_demand', 't':REGISTER_TYPE_INTEGER }, # 0=none, 1=heating, 2=refrigerate
    5272: { 'id':'zone_2_active_demand', 't':REGISTER_TYPE_INTEGER }, # 0=none, 1=heating, 2=refrigerate
    5273: { 'id':'zone_3_active_demand', 't':REGISTER_TYPE_INTEGER }, # 0=none, 1=heating, 2=refrigerate
    5274: { 'id':'zone_4_active_demand', 't':REGISTER_TYPE_INTEGER } # 0=none, 1=heating, 2=refrigerate
}

if DEBUG:
    FORMAT = '%(asctime)-0s %(levelname)s %(message)s [at line %(lineno)d]'
    logging.basicConfig(level=logging.DEBUG, format=FORMAT, datefmt='%Y-%m-%dT%I:%M:%S')
else:
    FORMAT = '%(asctime)-0s %(message)s'
    logging.basicConfig(level=logging.INFO, format=FORMAT, datefmt='%Y-%m-%dT%I:%M:%S')

class EcoforestServer(BaseHTTPRequestHandler):

    current_hp_data = {}

    def send(self, response):
        try:
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps(response).encode())
        except:
            self.send_error(500, 'Something went wrong here on the server side.')


    def healthcheck(self):
        self.send({'status': 'ok'})


    def stats(self):
        if DEBUG: logging.debug('GET stats')
        stats = self.ecoforest_stats()
        if stats:
            self.send(stats)
        else:
            self.send_error(500, 'Something went wrong here on the server side.')


    def set_status(self, status):
        if DEBUG: logging.debug('SET STATUS: %s' % (status))
        stats = self.ecoforest_stats()

        # only if 'estado' is off send request to turn on
        if status == "on" and stats['state'] == "off":
            data = self.ecoforest_call('idOperacion=1013&on_off=1')

        # only if 'estado' is on send request to turn off
        if status == "off" and (stats['state'] in ["on", "stand by", "starting"]):
            data = self.ecoforest_call('idOperacion=1013&on_off=0')

        self.send(self.get_status())


    def get_status(self):
        stats = self.ecoforest_stats()
        self.send(stats['state'])


    def set_temp(self, temp):
        if DEBUG: logging.debug('SET TEMP: %s' % (temp))
        if float(temp) < 12:
            temp = "12"
        if float(temp) > 40:
            temp = "30"
        # idOperacion=1019&temperatura
        data = self.ecoforest_call('idOperacion=1019&temperatura=' + temp)
        self.send(self.ecoforest_stats())


    def set_power(self, power):
        stats = self.ecoforest_call('idOperacion=1002')
        reply = dict(e.split('=') for e in stats.text.split('\n')[:-1]) # discard last line ?
        power_now = reply['consigna_potencia']
        power_now = int(power_now)
        logging.info('Power %s issued, stove power is at %s' % (power, power_now))

        if DEBUG: logging.debug('POWER: %s' % (power_now))
        if  power == "up":
            if power_now < 9:
                power_final = power_now + 1
                logging.info('Stove will change to %s' % power_final)
            else:
                if DEBUG: logging.debug('POWER at MAX: %s' % (power_now))
                power_final = power_now
                logging.info('Stove at MAX: %s' % power_final)
        if power == "down":
            if (power_now <= 9 and power_now > 1):
                power_final = power_now - 1
                logging.info('Stove will change to %s' % power_final)
            else:
                if DEBUG: logging.debug('POWER at MIN: %s' % (power_now))
                power_final = power_now
                logging.info('Stove at MIN: %s' % power_final)
        # idOperacion=1004&potencia=
        data = self.ecoforest_call('idOperacion=1004&potencia=' + str(power_final))
        print(data)
        self.send(self.ecoforest_stats())

    def ecoforest_stats(self):
        if stove:
            return self.ecoforest_stats_stove()
        else:
            return self.ecoforest_stats_heatpump()

    def ecoforest_stats_stove(self):
        stats = self.ecoforest_call('idOperacion=1002')
        reply = dict(e.split('=') for e in stats.text.split('\n')[:-1]) # discard last line ?

        states = {
            '0'  : 'off',
            '1'  : 'off',
            '2'  : 'starting', 
            '3'  : 'starting', 
            '4'  : 'starting', 
            '5'  : 'starting', 
            '6'  : 'starting', 
            '10' : 'starting', 
            '7'  : 'on', 
            '8'  : 'shutting down', 
            '-2' : 'shutting down', 
            '9'  : 'shutting down', 
            '11' : 'shutting down', 
            '-3' : 'alarm',
            '-4' : 'alarm',
            '20' : 'stand by',
        }

        state = reply['estado']
        if state in states: 
            reply['state'] = states[state]
        else:
            reply['state'] = 'unknown'
            logging.debug('reply: %s', reply)

        return reply

    def ecoforest_stats_heatpump(self):
        # Status registers:
        # digital: 105
        # numbers: 5082, 5083, 97, 3, 11, 8

        self.ecoforest_query_registers(2001, 105, 1)
        self.ecoforest_query_registers(2002, 5082, 2)
        self.ecoforest_query_registers(2002, 1, 12)
        self.ecoforest_query_registers(2002, 97, 1)
        return EcoforestServer.current_hp_data

    def ecoforest_query_registers(self,oper,ini,num):
        dict = EcoforestServer.current_hp_data
        stats = self.ecoforest_call('idOperacion=' + str(oper) + '&dir=' + str(ini) + '&num=' + str(num))
        lines = stats.text.split('\n')
        data = lines[1].split('&')
        heat_pump_registers = heat_pump_registers_2001 if oper == 2001 else heat_pump_registers_2002
        for i in range(2,len(data)):
            regid = ini + i - 2
            if regid in heat_pump_registers:
                reg = heat_pump_registers[regid]
                dict[reg['id']] = self.convert_register_value(data[i],reg['t'])

    def convert_register_value(self,value,rtype):
        if rtype == REGISTER_TYPE_DIGITAL:
            return int(value)
        elif rtype == REGISTER_TYPE_INTEGER:
            val = int(value,16)
            return val if val <= 32768 else val - 65536
        elif rtype == REGISTER_TYPE_ANALOG:
            val = int(value,16)
            return val/10 if val <= 32768 else (val - 65536) / 10
        else:
            return 0

    def get_status_value(self,attribute):
        if attribute in EcoforestServer.current_hp_data:
            return EcoforestServer.current_hp_data[attribute]
        else:
            return None

    def heating_status(self, status=None):
        self.ecoforest_query_registers(2001, 105, 1)
        current_status = 'on' if self.get_status_value('heating_status') == 1 else 'off'
        if status:
            if status == "on" and current_status == 'off':
                logging.info('Heater enabled')
                self.ecoforest_call('idOperacion=2011&dir=105&num=1&1')
            elif status == "off" and current_status == 'on':
                logging.info('Heater disabled')
                self.ecoforest_call('idOperacion=2011&dir=105&num=1&0')
            current_status = status
        self.send({'status':current_status})

    def get_heating_status(self):
        stats = self.ecoforest_stats()
        self.send(stats['state'])



    # queries the ecoforest server with the supplied contents and parses the results into JSON
    def ecoforest_call(self, body):
        if DEBUG: logging.debug('Request:\n%s' % (body))
        headers = { 'Content-Type': 'application/json' }
        try:
            request = requests.post(ECOFOREST_URL, data=body, headers=headers, auth=HTTPBasicAuth(username, passwd), timeout=2.5)
            if DEBUG: logging.debug('Request:\n%s' %(request.url))
            if DEBUG: logging.debug('Result:\n%s' %(request.text))
            return request
        except requests.Timeout:
            pass


    def do_POST(self):
        parsed_path = urllib.parse.urlparse(self.path)
        args = dict()
        if parsed_path.query:
            args = dict(qc.split("=") for qc in parsed_path.query.split("&"))

        if DEBUG: logging.debug('GET: TARGET URL: %s, %s' % (parsed_path.path, parsed_path.query))
        content_len = int(self.headers.getheader('content-length', 0))
        post_body = self.rfile.read(content_len)

        dispatch = {
            '/ecoforest/status': self.set_status,
        }

        # API calls
        if parsed_path.path in dispatch:
            try:
                dispatch[parsed_path.path](post_body, **args)
            except:
                self.send_error(500, 'Something went wrong here on the server side.')
        else:
            self.send_error(404,'File Not Found: %s' % parsed_path.path)

        return


    def do_GET(self):
        parsed_path = urllib.parse.urlparse(self.path)
        args = dict()
        if parsed_path.query:
            args = dict(qc.split("=") for qc in parsed_path.query.split("&"))
        
        dispatch = {
            '/healthcheck': self.healthcheck,
            '/ecoforest/fullstats': self.stats,
            '/ecoforest/status': self.get_status,
            '/ecoforest/set_status': self.set_status,
            '/ecoforest/heating_status': self.heating_status,
            '/ecoforest/set_temp': self.set_temp,
            '/ecoforest/set_power': self.set_power,
        }

        # API calls
        if parsed_path.path in dispatch:
            try:
                dispatch[parsed_path.path](**args)
            except:
                self.send_error(500, 'Something went wrong here on the server side.')
        else:
            self.send_error(404,'File Not Found: %s' % parsed_path.path)

        return


if __name__ == '__main__':
    try:
        from http.server import HTTPServer
        server = HTTPServer(('', DEFAULT_PORT), EcoforestServer)
        logging.info('Ecoforest proxy server has started (' + heatertype + ')')
        server.serve_forever()
    except Exception as e:
        logging.error(e)
        sys.exit(2)
