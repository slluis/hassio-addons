import sys, logging, datetime, urllib.request, urllib.parse, urllib.error, urllib.request, urllib.error, urllib.parse, json, requests, urllib.parse
import urllib3
import signal
import threading
import os

from os import curdir, sep
from http.server import BaseHTTPRequestHandler
from requests.auth import HTTPBasicAuth

# Disable SSL warnings for unverified HTTPS requests
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# configuration - try local data.json first, then fall back to Home Assistant addon options
def load_configuration():
    """Load configuration from either local data.json or Home Assistant addon options.json"""
    local_config_path = 'data.json'
    addon_config_path = '/data/options.json'
    
    if os.path.exists(local_config_path):
        config_path = local_config_path
        print(f'Loading configuration from local file: {config_path}')
    elif os.path.exists(addon_config_path):
        config_path = addon_config_path
        print(f'Loading configuration from Home Assistant addon: {config_path}')
    else:
        # Fall back to local file even if it doesn't exist for better error messages
        config_path = local_config_path
        print(f'Warning: Neither {local_config_path} nor {addon_config_path} found, attempting {local_config_path}')
    
    try:
        with open(config_path, 'r') as config_file:
            config_data = json.load(config_file)
            print(f'Successfully loaded configuration from {config_path}')
            return config_data
    except FileNotFoundError:
        print(f'Error: Configuration file {config_path} not found')
        raise
    except json.JSONDecodeError as e:
        print(f'Error: Invalid JSON in configuration file {config_path}: {e}')
        raise
    except Exception as e:
        print(f'Error: Failed to load configuration from {config_path}: {e}')
        raise

jdata = load_configuration()

DEBUG = bool(jdata['debug'])
DEFAULT_PORT = int(jdata['proxy_port'])

host = str(jdata['ecoforest_host'])
username = str(jdata['ecoforest_user'])
passwd = str(jdata['ecoforest_pass'])
heatertype = str(jdata['type']) if 'type' in jdata else 'heatpump'
stove = heatertype == 'stove'

ECOFOREST_URL = 'https://' + username + ':' + passwd + '@' + host + ':8000/recepcion_datos_4.cgi'

REGISTER_TYPE_DIGITAL = 1
REGISTER_TYPE_INTEGER = 2
REGISTER_TYPE_ANALOG = 3

heat_pump_registers_2001 = {
    61: { 'id':'pool_status', 't':REGISTER_TYPE_DIGITAL },
    83: { 'id':'reset_alarms', 't':REGISTER_TYPE_DIGITAL },
    1552: { 'id':'heating_status', 't':REGISTER_TYPE_DIGITAL },
    1568: { 'id':'cooling_status', 't':REGISTER_TYPE_DIGITAL },
    1535: { 'id':'dhw_recirculation_status', 't':REGISTER_TYPE_DIGITAL },
    206: { 'id':'direct_heating', 't':REGISTER_TYPE_DIGITAL },
    207: { 'id':'direct_cooling', 't':REGISTER_TYPE_DIGITAL },
    208: { 'id':'dhw_demand', 't':REGISTER_TYPE_DIGITAL },
    209: { 'id':'pool_demand', 't':REGISTER_TYPE_DIGITAL },
    210: { 'id':'htr_status', 't':REGISTER_TYPE_DIGITAL },
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
        """
        Get comprehensive heat pump statistics by combining data from multiple operations
        """
        if DEBUG: logging.debug('Getting comprehensive heat pump stats')
        
        # Initialize the data dictionary with alarms
        EcoforestServer.current_hp_data = {'alarms': ""}
        
        try:
            # Get energy reference data first (operation 2113)
            energy_ref_data = self.get_page_data_cooling()
            if energy_ref_data:
                EcoforestServer.current_hp_data.update(energy_ref_data)

            heating_data = self.get_page_data_heating()
            if heating_data:
                EcoforestServer.current_hp_data.update(heating_data)

            # Get basic system data
            basic_data = self.get_page_data_basic()
            if basic_data:
                EcoforestServer.current_hp_data.update(basic_data)
            
            # Get energy and demand data
            energy_data = self.get_page_data_energy()
            if energy_data:
                EcoforestServer.current_hp_data.update(energy_data)
            
            # Get zone data
            zone_data = self.get_page_data_zones()
            if zone_data:
                EcoforestServer.current_hp_data.update(zone_data)
            
            # Get detailed zone and DHW data
            detailed_data = self.get_page_data_detailed_zones()
            if detailed_data:
                EcoforestServer.current_hp_data.update(detailed_data)
            
            # Get system configuration data
            config_data = self.get_page_data_system_config()
            if config_data:
                EcoforestServer.current_hp_data.update(config_data)
                
        except Exception as e:
            if DEBUG:
                logging.debug(f'Error getting additional heat pump data: {e}')
        
        return EcoforestServer.current_hp_data

    def get_page_data_basic(self):
        """Get basic system data - equivalent to JavaScript actualizarpagina function (operation 2148)"""
        field_definitions = [
            # Basic values
            (0, 'lg', 'integer'),
        ]
        
        # Add common field groups
        field_definitions.extend(self.BASIC_DATETIME_FIELDS)
        field_definitions.extend(self.BASIC_ICON_STATUS_FIELDS)
        
        # Add specific fields for this operation
        field_definitions.extend([
            # Pressure values (divided by 10)
            (18, 'production_circuit_pressure', 'temperature'), # pcc
            (20, 'brine_circuit_pressure', 'temperature'), # pcp
            
            # Temperature values (divided by 10)
            (19, 'production_inlet_temperature', 'temperature'), # trc
            (21, 'outdoor_temperature', 'temperature'),
            (22, 'production_outlet_temperature', 'temperature'), # tic
            (23, 'brine_outlet_temperature', 'temperature'), # tip
            (24, 'brine_inlet_temperature', 'temperature'), # trp
            
            # Mode and status flags
            (25, 'dpfm', 'integer'),
            (26, 'hpfm', 'integer'),
            (27, 'cpfm', 'integer'),
            (28, 'epmrp', 'integer'),
            (29, 'ppfmode', 'integer'),
            (32, 'haf', 'integer'),
            (33, 'caf', 'integer'),
            (34, 'htpfm', 'integer'),
            (35, 'ea3', 'integer'),
        ])
        
        return self.get_data_page(2148, field_definitions)

    def get_page_data_energy(self):
        """Get energy and demand data - equivalent to JavaScript actualizarpagina1 function (operation 2149)"""
        field_definitions = [
            # Power unit and energy values
            (0, 'power_unit', 'temperature'),
            (1, 'useful_heat_power', 'integer'),
            (2, 'useful_cool_power', 'integer'),
            (3, 'electric_energy', 'integer'),
            (30, 'electric_cool_internal', 'integer'),
            (31, 'electric_cool_op', 'integer'),
            
            # Demand status flags
            (4, 'buffer_cooling', 'integer'), # active_cool_buffer_demand
            (5, 'antifreeze_buffer_demand', 'integer'),
            (6, 'dhw_demand', 'integer'),
            (7, 'buffer_heating', 'integer'), # heating_buffer_demand
            (8, 'legionella_demand', 'integer'),
            (9, 'passive_cool_buffer_demand', 'integer'),
            (10, 'pool_demand', 'integer'),
            
            # Additional status flags
            (17, 'cascade_max_power', 'integer'),
            (18, 'cascade_internal_pump', 'integer'),
            (34, 'htr_status', 'integer'), # dhw_htr_active
            (35, 'pool_htr_demand', 'integer'),
        ]
        
        # Add zone demand fields using helper method
        field_definitions.extend(self.create_zone_fields(11, 5, '_active_demand', 'integer'))
        # This creates: zone_1_active_demand, zone_2_active_demand, ..., zone_5_active_demand
        
        return self.get_data_page(2149, field_definitions)

    def get_page_data_zones(self):
        """Get zone temperatures and control data - equivalent to JavaScript actualizarpagina2 function (operation 2150)"""
        field_definitions = [
            # Temperature values (all divided by 10)
            (1, 'heating_inlet_temperature', 'temperature'),
            (2, 'heating_regulation_temp', 'temperature'),
            (4, 'cooling_inlet_temperature', 'temperature'),
            (5, 'cooling_regulation_temp', 'temperature'),
            (6, 'heating_reference_temp', 'temperature'),
            (7, 'cooling_reference_active_temp', 'temperature'),
            (8, 'cooling_reference_passive_temp', 'temperature'),
            
            # Control status and set points
            (24, 'surplus_control_status', 'integer'),
            (25, 'power_balance', 'temperature'),
            (26, 'surplus_control_setpoint', 'temperature'),
            (27, 'consumption_limit_status', 'integer'),
            (28, 'consumption_limit_setpoint', 'temperature'),
        ]
        
        # Add zone fields using helper methods
        zone_set_mapping = {9: 'zone_1_set_temp', 10: 'zone_2_set_temp', 11: 'zone_3_set_temp',
                           12: 'zone_4_set_temp', 13: 'zone_5_set_temp'}
        zone_real_mapping = {14: 'heating_real_temperature_1', 15: 'heating_real_temperature_2', 16: 'heating_real_temperature_3',
                            17: 'heating_real_temperature_4', 18: 'heating_real_temperature_5'}
        zone_regulation_mapping = {19: 'zone_1_regulation', 20: 'zone_2_regulation', 21: 'zone_3_regulation',
                                  22: 'zone_4_regulation', 23: 'zone_5_regulation'}
        
        field_definitions.extend(self._create_field_range(zone_set_mapping, 'temperature'))
        field_definitions.extend(self._create_field_range(zone_real_mapping, 'temperature'))
        field_definitions.extend(self._create_field_range(zone_regulation_mapping, 'temperature'))
        
        return self.get_data_page(2150, field_definitions)

    def get_page_data_detailed_zones(self):
        """Get detailed zone information and DHW data - equivalent to JavaScript actualizarpagina3 function (operation 2151)"""
        field_definitions = [
            # Heating set temperatures for zones
            (0, 'heating_set_temperature_1', 'temperature'),
            (1, 'heating_set_temperature_2', 'temperature'),
            (2, 'heating_set_temperature_3', 'temperature'),
            (3, 'heating_set_temperature_4', 'temperature'),
            (4, 'heating_set_temperature_5', 'temperature'),
            
            # Zone inlet temperatures
            (5, 'zone_1_inlet_temp', 'temperature'),
            (6, 'zone_2_inlet_temp', 'temperature'),
            (7, 'zone_3_inlet_temp', 'temperature'),
            (8, 'zone_4_inlet_temp', 'temperature'),
            (9, 'zone_5_inlet_temp', 'temperature'),
            
            # Zone regulation values
            (10, 'zone_1_regulation_val', 'temperature'),
            (11, 'zone_2_regulation_val', 'temperature'),
            (12, 'zone_3_regulation_val', 'temperature'),
            (13, 'zone_4_regulation_val', 'temperature'),
            (14, 'zone_5_regulation_val', 'temperature'),
            
            # Cooling set temperatures for zones
            (15, 'cooling_zone_1_set_temp', 'temperature'),
            (16, 'cooling_zone_2_set_temp', 'temperature'),
            (17, 'cooling_zone_3_set_temp', 'temperature'),
            (18, 'cooling_zone_4_set_temp', 'temperature'),
            (19, 'cooling_zone_5_set_temp', 'temperature'),
            
            # Inertia and buffer temperatures
            (20, 'temp_dep_heat', 'temperature'), # inertia_inlet_temp
            (21, 'heating_buffer_set_temp', 'temperature'),
            (22, 'heating_offset_inertia', 'temperature'),
            (23, 'cooling_inertia_temp', 'temperature'),
            (24, 'cooling_buffer_set_temp', 'temperature'),
            (25, 'cooling_offset_inertia', 'temperature'),
            
            # DHW related temperatures and settings
            (26, 'dhw_setpoint_manual', 'temperature'),
            (27, 'dhw_offset', 'temperature'),
            (28, 'dhw_temperature', 'temperature'),
            (29, 'dhw_recirculation_status', 'integer'),
            (30, 'dhw_recirculation_setpoint', 'temperature'),
            (31, 'dhw_recirculation_temp', 'temperature'),
            (32, 'dhw_recirculation_offset', 'temperature'),
            (33, 'pool_setpoint', 'temperature'),
        ]
        
        return self.get_data_page(2151, field_definitions)

    def get_page_data_system_config(self):
        """Get system configuration and ODU data - equivalent to JavaScript actualizarpagina4 function (operation 2152)"""
        field_definitions = [
            # Pool temperatures
            (0, 'pool_inlet_temp', 'temperature'),
            (1, 'pool_accumulator_temp', 'temperature'),
            (2, 'pool_offset', 'temperature'),
            
            # Feature information flags
            (15, 'heating_groups_feature_info', 'integer'),
            (16, 'dhw_groups_feature_info', 'integer'),
            (17, 'pool_groups_feature_info', 'integer'),
            (18, 'cooling_groups_feature_info', 'integer'),
            (19, 'heating_terminals_feature_info', 'integer'),
            (20, 'heating_circuits_feature_info', 'integer'),
            (21, 'cooling_circuits_feature_info', 'integer'),
            (24, 'dhw_circulation_feature_info', 'integer'),
            (25, 'pool_circuit_feature', 'integer'),
            (26, 'energy_feature_info', 'integer'),
            (27, 'heat_pump_registers_buffer', 'integer'),
            
            # Auxiliary status
            (28, 'aux_alarm_temp', 'integer'),
        ]
        
        # Add ODU status and enable fields using helper methods
        field_definitions.extend(self._create_sequential_fields(3, 6, 'odu_', 'integer'))  # odu_1_status to odu_6_status
        field_definitions.extend([(i + 9, f'odu_{i+1}_enabled', 'integer') for i in range(6)])  # odu_1_enabled to odu_6_enabled
        field_definitions.extend(self._create_sequential_fields(29, 5, 'aux_', 'integer'))  # aux_1_status to aux_5_status
        
        return self.get_data_page(2152, field_definitions)

    def get_page_data_cooling(self):
        """Get energy reference data - equivalent to JavaScript actualizarpagina function (operation 2113)"""
        field_definitions = [
            # Based on the JavaScript code: eru = a[15].replace("ERU=", "")
            # The eru value is extracted from index 15 and ERU= prefix is removed
            (15, 'cooling_status', 'key_value_integer'),  # Energy reference value (ERU) with prefix removal
        ]
        
        return self.get_data_page(2113, field_definitions)

    def get_page_data_heating(self):
        """Get heating data - equivalent to JavaScript actualizarpagina function (operation 2113)"""
        field_definitions = [
            (12, 'heating_status', 'key_value_integer'),  # Energy reference value (ERU) with prefix removal
        ]
        
        return self.get_data_page(2108, field_definitions)

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

    def get_status_value(self,attribute):
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
        self.handle_switch('dhw_recirculation_status', post_body)

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
                logging.debug(register + ' enabled')
                self.set_status_value(register, 1)
            elif status == "off" and current_status == 'on':
                logging.debug(register + ' disabled')
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
        if DEBUG: logging.debug('Body:\n%s' % (body))
        headers = { 'Content-Type': 'application/json' }
        try:
            if DEBUG: logging.debug('Request:\n%s' %(ECOFOREST_URL))
            # Disable SSL verification for self-signed certificates
            request = requests.post(ECOFOREST_URL, data=body, headers=headers, auth=HTTPBasicAuth(username, passwd), timeout=10, verify=False)
            if DEBUG: logging.debug('Result:\n%s' %(request.text))
            return request
        except requests.exceptions.SSLError as e:
            if DEBUG: logging.debug(f'SSL Error: {e}')
            return None
        except requests.exceptions.ConnectionError as e:
            if DEBUG: logging.debug(f'Connection Error: {e}')
            return None
        except requests.exceptions.Timeout as e:
            if DEBUG: logging.debug(f'Timeout Error: {e}')
            return None
        except requests.exceptions.RequestException as e:
            if DEBUG: logging.debug(f'Request Error: {e}')
            return None

    def _parse_hex_integer(self, hex_str):
        """Parse a hex string to signed 16-bit integer"""
        val = int(hex_str, 16)
        return val if val <= 32768 else val - 65536

    def _parse_hex_temperature(self, hex_str):
        """Parse a hex string to temperature value (divided by 10)"""
        return self._parse_hex_integer(hex_str) / 10

    def _format_time_component(self, value):
        """Format time component with leading zero if needed"""
        return f"0{value}" if value < 10 else str(value)

    def _parse_data_field(self, data, index, field_type='integer'):
        """Parse a data field at given index with specified type"""
        if field_type == 'integer':
            return self._parse_hex_integer(data[index])
        elif field_type == 'temperature':
            return self._parse_hex_temperature(data[index])
        elif field_type == 'time':
            val = int(data[index], 16)
            return self._format_time_component(val)
        elif field_type == 'key_value_integer':
            # Handle key=value format - extract integer value after "="
            value = data[index]
            if '=' in value:
                return int(value.split('=')[1])
            return int(value)
        else:
            return int(data[index], 16)

    def eliminar_errores(self, data_lines):
        """Remove lines containing 'error' from the data, equivalent to JavaScript eliminarErrores function"""
        cleaned_data = []
        for line in data_lines[:-1]:  # Exclude last line initially
            if 'error' not in line:
                cleaned_data.append(line)
        # Add the last line (status indicator)
        cleaned_data.append(data_lines[-1])
        return cleaned_data

    def get_data_page(self, operation_id, field_definitions):
        """
        Generic method to query ecoforest operations and parse data based on field definitions
        
        Args:
            operation_id (int): The operation ID to query (e.g., 2113, 2148, 2149, 2150, 2151, 2152)
            field_definitions (list): List of tuples (index, field_name, field_type)
                where field_type can be 'integer', 'temperature', 'time', 'key_value_integer', or 'raw'
        
        Returns:
            dict: Parsed data with field names as keys, or None if operation failed
        """
        if DEBUG: 
            logging.debug(f'get_data_page called with operation_id={operation_id}')
        
        response = self.ecoforest_call(f'idOperacion={operation_id}')
        
        if not response:
            return None
            
        lines = response.text.split('\n')
        cleaned_data = self.eliminar_errores(lines)
        
        # Check if operation was successful (last element should be 0)
        if int(cleaned_data[-1]) != 0:
            if DEBUG:
                logging.debug(f'get_data_page operation {operation_id} failed')
            return None
        
        try:
            result = {}
            
            # Parse fields based on definitions
            for index, field_name, field_type in field_definitions:
                if index < len(cleaned_data):
                    result[field_name] = self._parse_data_field(cleaned_data, index, field_type)
                else:
                    if DEBUG:
                        logging.debug(f'Index {index} out of range for field {field_name}')
            
            # Parse grouped fields (for dictionaries of related fields)
            for definition in field_definitions:
                if isinstance(definition, dict) and 'fields' in definition:
                    for index, field_name in definition['fields'].items():
                        if index < len(cleaned_data):
                            result[field_name] = self._parse_data_field(cleaned_data, index, definition.get('type', 'integer'))
            
            if DEBUG:
                logging.debug(f'get_data_page {operation_id} parsed data: {result}')
                
            return result
            
        except (ValueError, IndexError) as e:
            if DEBUG:
                logging.debug(f'Error parsing get_data_page {operation_id} data: {e}')
            return None

    # Field definition constants for better reusability
    BASIC_DATETIME_FIELDS = [
        (1, 'year', 'time'),
        (2, 'month', 'time'), 
        (3, 'day', 'time'),
        (4, 'hour', 'time'),
        (5, 'minute', 'time'),
    ]
    
    BASIC_ICON_STATUS_FIELDS = [
        (6, 'ico1', 'integer'),
        (7, 'ic2', 'integer'),
        (8, 'ic3', 'integer'),
        (9, 'ic4', 'integer'),
        (10, 'ta', 'integer'),
        (11, 'fe', 'integer'),
        (12, 'fet', 'integer'),
        (13, 'fehn', 'integer'),
        (14, 'fsoe', 'integer'),
        (15, 'fcc', 'integer'),
    ]
    
    def create_zone_fields(self, start_index, count, field_suffix='', field_type='integer'):
        """
        Create zone field definitions for common zone patterns
        
        Args:
            start_index (int): Starting index for zone fields
            count (int): Number of zones (usually 5)
            field_suffix (str): Suffix for field names (e.g., '_set_temp', '_real_temp', '_regulation')
            field_type (str): Field type ('integer', 'temperature', etc.)
        
        Returns:
            list: List of zone field definitions
        """
        return [(start_index + i, f'zone_{i+1}{field_suffix}', field_type) for i in range(count)]

    def _create_sequential_fields(self, start_index, count, field_prefix, field_type='integer'):
        """
        Helper method to create sequential field definitions
        
        Args:
            start_index (int): Starting index for the fields
            count (int): Number of sequential fields to create
            field_prefix (str): Prefix for field names (e.g., 'zone_', 'odu_')
            field_type (str): Type of field ('integer', 'temperature', 'time', 'raw')
        
        Returns:
            list: List of field definition tuples
        """
        return [(start_index + i, f"{field_prefix}{i+1}", field_type) for i in range(count)]
    
    def _create_field_range(self, field_mapping, field_type='integer'):
        """
        Helper method to create field definitions from a dictionary mapping
        
        Args:
            field_mapping (dict): Dictionary mapping index to field name
            field_type (str): Type of field ('integer', 'temperature', 'time', 'raw')
        
        Returns:
            list: List of field definition tuples
        """
        return [(index, field_name, field_type) for index, field_name in field_mapping.items()]

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
           # try:
                dispatch[parsed_path.path](post_body, **args)
           # except:
          #      self.send_error(500, 'Something went wrong here on the server side.')
        else:
            self.send_error(404,'File Not Found: %s' % parsed_path.path)
        return

if __name__ == '__main__':
    # Global server variable for signal handler
    server = None
    
    def signal_handler(sig, frame):
        """Handle shutdown signals gracefully"""
        signal_name = 'SIGINT' if sig == signal.SIGINT else 'SIGTERM'
        logging.info(f'Received {signal_name} signal. Shutting down server...')
        if server:
            # Stop the server in a separate thread to avoid blocking
            shutdown_thread = threading.Thread(target=server.shutdown)
            shutdown_thread.start()
            shutdown_thread.join(timeout=5)  # Wait max 5 seconds
            server.server_close()
        logging.info('Server stopped.')
        sys.exit(0)
    
    try:
        from http.server import HTTPServer
        server = HTTPServer(('', DEFAULT_PORT), EcoforestServer)
        
        # Register signal handlers for graceful shutdown
        signal.signal(signal.SIGINT, signal_handler)   # Ctrl+C
        signal.signal(signal.SIGTERM, signal_handler)  # Termination signal
        
        logging.info('Ecoforest proxy server has started (' + heatertype + ')')
        logging.info(f'Server listening on port {DEFAULT_PORT}')
        logging.info('Press Ctrl+C to stop the server')
        
        try:
            server.serve_forever()
        except KeyboardInterrupt:
            logging.info('Keyboard interrupt received. Shutting down...')
            raise
            
    except KeyboardInterrupt:
        logging.info('Server interrupted by user')
    except Exception as e:
        logging.error(f'Server error: {e}')
        sys.exit(2)
    finally:
        if server:
            try:
                server.shutdown()
                server.server_close()
                logging.info('Server cleanup completed')
            except:
                pass  # Ignore cleanup errors
        sys.exit(0)
