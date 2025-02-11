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
    61: { 'id':'pool_status', 't':REGISTER_TYPE_DIGITAL },
    83: { 'id':'reset_alarms', 't':REGISTER_TYPE_DIGITAL },
    105: { 'id':'heating_status', 't':REGISTER_TYPE_DIGITAL },
    107: { 'id':'cooling_status', 't':REGISTER_TYPE_DIGITAL },
    190: { 'id':'dhw_recirculation_enabled', 't':REGISTER_TYPE_DIGITAL },
    206: { 'id':'direct_heating', 't':REGISTER_TYPE_DIGITAL },
    207: { 'id':'direct_cooling', 't':REGISTER_TYPE_DIGITAL },
    208: { 'id':'dhw_demand', 't':REGISTER_TYPE_DIGITAL },
    209: { 'id':'pool_demand', 't':REGISTER_TYPE_DIGITAL },
    210: { 'id':'htr_status', 't':REGISTER_TYPE_DIGITAL },
    211: { 'id':'dhw_recirculation_status', 't':REGISTER_TYPE_DIGITAL },
    249: { 'id':'buffer_heating', 't':REGISTER_TYPE_DIGITAL },
    250: { 'id':'buffer_cooling', 't':REGISTER_TYPE_DIGITAL },
}

heat_pump_registers_2002 = {
    1: { 'id':'brine_outlet_temperature', 't':REGISTER_TYPE_ANALOG },
    2: { 'id':'brine_inlet_temperature', 't':REGISTER_TYPE_ANALOG },
    3: { 'id':'heating_real_temperature_1', 't':REGISTER_TYPE_ANALOG },
    4: { 'id':'production_inlet_temperature', 't':REGISTER_TYPE_ANALOG },
    8: { 'id':'dhw_temperature', 't':REGISTER_TYPE_ANALOG },
    13: { 'id':'brine_circuit_pressure', 't':REGISTER_TYPE_ANALOG },
    14: { 'id':'production_circuit_pressure', 't':REGISTER_TYPE_ANALOG },
    15: { 'id':'dhw_offset_temperature', 't':REGISTER_TYPE_ANALOG },
    17: { 'id':'dhw_set_temperature', 't':REGISTER_TYPE_ANALOG },
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
    5033: { 'id':'production_pump_adjustment', 't':REGISTER_TYPE_ANALOG },
    5034: { 'id':'brine_pump_adjustment', 't':REGISTER_TYPE_ANALOG },
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
    5274: { 'id':'zone_4_active_demand', 't':REGISTER_TYPE_INTEGER }, # 0=none, 1=heating, 2=refrigerate
    5290: { 'id':'status', 't':REGISTER_TYPE_INTEGER }, # 0:off, 1:on, 2:alarm
}

heat_pump_alarms = {
    1: {"text": "Fallo en reloj interno"},
    2: {"text": "Fallo en memoria extendida"},
    3: {"text": "Fuentes no disponibles"},
    7: {"text": "Fallo sonda presión descarga compresor"},
    8: {"text": "Fallo sonda temperatura impulsión captación"},
    9: {"text": "Fallo sonda temperatura retorno captación"},
    10: {"text": "Fallo sonda presión captación"},
    11: {"text": "Fallo sonda temperatura impulsión producción"},
    12: {"text": "Fallo sonda temperatura retorno producción"},
    13: {"text": "Fallo sonda presión producción"},
    14: {"text": "Fallo sonda temperatura"},
    15: {"ref": 14},
    16: {"ref": 14},
    214: {"ref": 14},
    215: {"ref": 14},
    217: {"ref": 14},
    17: {"text": "Temperatura captación baja"},
    21: {"ref": 17},
    18: {"text": "Presión descarga compresor alta"},
    19: {"text": "Temperatura descarga compresor alta"},
    20: {"text": "Temperatura inverter alta"},
    25: {"text": "Presión captación baja"},
    26: {"text": "Presión producción baja"},
    34: {"text": "Presión aspiración compresor baja"},
    39: {"ref": 34},
    36: {"text": "Fallo sonda presión aspiración compresor"},
    37: {"text": "Fallo sonda temperatura aspiración compresor"},
    38: {"text": "Recalentamiento aspiración bajo (lowSH)"},
    40: {"text": "Temperatura evaporación alta (MOP)"},
    41: {"text": "Temperatura aspiración compresor baja"},
    212: {"text": "Fallo comunicación inverter"},
    213: {"text": "Temperatura captación alta"},
    218: {"text": "Fallo comunicación pCOe"},
    219: {"text": "Fallo Terminal SG1"},
    220: {"text": "Fallo comunicación Terminal SG1"},
    221: {"text": "Fallo Terminal SG2"},
    222: {"text": "Fallo comunicación Terminal SG2"},
    223: {"text": "Fallo Terminal SG3"},
    224: {"text": "Fallo comunicación Terminal SG3"},
    225: {"text": "Fallo Terminal SG4"},
    226: {"text": "Fallo comunicación Terminal SG4"},
    33: {"text": "Caudal evaporador bajo"}
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
            self.wfile.flush()
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

    def get_alarm_text(self,index):
        reg = heat_pump_alarms[index]
        if 'ref' in reg:
            ref = reg['ref']
            return self.get_alarm_text(ref)
        else:
            return reg['text']

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
        # digital: 0-42, 83, 105, 107, 190, 206, 208, 210, 211, 249, 250
        # numbers: 5033, 5034, 5082, 5083, 5290, 97, 1, 2, 3, 4, 8, 11, 13, 14, 97, 200, 201

        EcoforestServer.current_hp_data['alarms'] = ""

        self.ecoforest_query_registers(2001, 1, 107)
        self.ecoforest_query_registers(2001, 190, 37)
        self.ecoforest_query_registers(2001, 249, 2)
        self.ecoforest_query_registers(2002, 5033, 2)
        self.ecoforest_query_registers(2002, 5082, 10)
        self.ecoforest_query_registers(2002, 5271, 20)
        self.ecoforest_query_registers(2002, 1, 17)
        self.ecoforest_query_registers(2002, 97, 1)
        self.ecoforest_query_registers(2002, 200, 2)

        return EcoforestServer.current_hp_data

    def ecoforest_query_registers(self,oper,ini,num):
        dict = EcoforestServer.current_hp_data
        stats = self.ecoforest_call('idOperacion=' + str(oper) + '&dir=' + str(ini) + '&num=' + str(num))
        lines = stats.text.split('\n')
        data = lines[1].split('&')
        heat_pump_registers = heat_pump_registers_2001 if oper == 2001 else heat_pump_registers_2002
        for i in range(2,len(data)):
            regid = ini + i - 2
            if regid in heat_pump_alarms and oper == 2001 and data[i]=='1':
                self.store_alarm(regid,data[i])
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

    def store_alarm(self,regid,value):
        dict = EcoforestServer.current_hp_data
        alarm = self.get_alarm_text(regid)
        dict['alarms'] += alarm + "\n"

    def convert_to_register_value(self,value,rtype):
        if rtype == REGISTER_TYPE_DIGITAL:
            return str(value)
        elif rtype == REGISTER_TYPE_INTEGER:
            return hex(value if value >=0 else value + 65536)
        elif rtype == REGISTER_TYPE_ANALOG:
            return format(int(value*10) if value >=0 else int(value * 10) + 65536, '04X')

    def get_status_value(self,attribute,fetch=True):
        if fetch:
            oper,regid,rtype = self.get_attribute_data(attribute)
            self.ecoforest_query_registers(oper, regid, 1)
        if attribute in EcoforestServer.current_hp_data:
            return EcoforestServer.current_hp_data[attribute]
        else:
            return None

    def set_status_value(self,attribute,value):
        oper,regid,rtype = self.get_attribute_data(attribute)
        sval = self.convert_to_register_value(value,rtype)
        result = self.ecoforest_call('idOperacion=' + str(oper + 10) + '&dir=' + str(regid) + '&num=1&' + sval)
        lines = result.text.split('\n')
        if int(lines[1]) >= 0:
            EcoforestServer.current_hp_data[attribute] = value

    def get_attribute_data(self,attribute):
        for regid in heat_pump_registers_2001:
            if heat_pump_registers_2001[regid]['id'] == attribute:
                return 2001, regid, heat_pump_registers_2001[regid]['t']
        for regid in heat_pump_registers_2002:
            if heat_pump_registers_2002[regid]['id'] == attribute:
                return 2002, regid, heat_pump_registers_2002[regid]['t']
        return None,None

    def heating_status(self, post_body=None):
        self.handle_switch('heating_status', post_body)

    def cooling_status(self, post_body=None):
        self.handle_switch('cooling_status', post_body)

    def dhw_recirculation_enabled(self, post_body=None):
        self.handle_switch('dhw_recirculation_enabled', post_body)

    def reset_alarms(self, post_body=None):
        self.handle_switch('reset_alarms', post_body)

    def dhw_set_temperature(self, post_body=None):
        self.handle_sensor('dhw_set_temperature', post_body)

    def dhw_offset_temperature(self, post_body=None):
        self.handle_sensor('dhw_offset_temperature', post_body)

    def handle_switch(self, register, post_body):
        current_status = 'on' if self.get_status_value(register) == 1 else 'off'
        if post_body:
            data = json.loads(post_body.decode('utf-8'))
            status = data['status']
            if status == "on" and current_status == 'off':
                logging.info(register + ' enabled')
                self.set_status_value(register, 1)
            elif status == "off" and current_status == 'on':
                logging.info(register + ' disabled')
                self.set_status_value(register, 0)
            current_status = status
        self.send({'status':current_status})

    def handle_sensor(self, register, post_body):
        current_status = self.get_status_value(register)
        if post_body:
            data = json.loads(post_body.decode('utf-8'))
            status = float(data['status'])
            if status != float(current_status):
                logging.info('set ' + register + ' to ' + str(status))
                self.set_status_value(register, status)
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
            request = requests.post(ECOFOREST_URL, data=body, headers=headers, auth=HTTPBasicAuth(username, passwd), timeout=10)
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

        if DEBUG: logging.debug('POST: TARGET URL: %s, %s' % (parsed_path.path, parsed_path.query))
        content_len = int(self.headers.get('content-length', 0))
        post_body = self.rfile.read(content_len)

        dispatch = {
            '/ecoforest/status': self.set_status,
            '/ecoforest/heating_status': self.heating_status,
            '/ecoforest/cooling_status': self.cooling_status,
            '/ecoforest/dhw_recirculation_enabled': self.dhw_recirculation_enabled,
            '/ecoforest/dhw_set_temperature': self.dhw_set_temperature,
            '/ecoforest/dhw_offset_temperature': self.dhw_offset_temperature,
            '/ecoforest/reset_alarms': self.reset_alarms
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
            '/ecoforest/set_temp': self.set_temp,
            '/ecoforest/set_power': self.set_power,
            '/ecoforest/heating_status': self.heating_status,
            '/ecoforest/cooling_status': self.cooling_status,
            '/ecoforest/dhw_recirculation_enabled': self.dhw_recirculation_enabled,
            '/ecoforest/dhw_set_temperature': self.dhw_set_temperature,
            '/ecoforest/dhw_offset_temperature': self.dhw_offset_temperature,
            '/ecoforest/reset_alarms': self.reset_alarms
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
