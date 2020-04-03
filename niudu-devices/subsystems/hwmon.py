from PySide2.QtWidgets import QTreeWidgetItem

from util import get_file_contents


def update_dict(device_path, device_dict):
    device_dict['chip_name'] = get_file_contents(device_path, 'name')
    device_dict['name'] = 'Hardware monitoring node ' + device_path.split('/')[-1][len('hwmon'):] + ': "' + device_dict['chip_name'] + '"'

sensors_titles_dict = {
    'in': 'voltage',
    'pwm': 'PWM',
    'temp': 'temperature',
    'curr': 'current',
    'freq': 'frequency'
}

sensors_params_dict = {
    'in': {
        'min': 'min value',
        'lcrit': 'critical min value',
        'max': 'max value',
        'crit': 'critical max value',
        'input': 'input (read) value',
        'average': 'average',
        'lowest': 'historical minimum',
        'highest': 'historical maximum',
        #'reset_history':
        'label': 'suggested channel label',
        'enable': 'sensor enabled',
    },
    'fan': {
        'min': 'minimum value',
        'max': 'maximum value',
        'input': 'input (read) value',
        'div': 'divisor',
        'pulses': 'tachometer pulses per revolution',
        'target': 'desired speed',
        'label': 'suggested channel label',
        'enable': 'sensor enabled'
    },
    'pwm': {},
    'temp': {},
    'curr': {},
    'power': {
        'average': 'average use',
        'average_interval': 'use averaging interval',
        'average_interval_max': 'maximum use averaging interval',
        'average_interval_min': 'minimum use averaging interval',
        'average_highest': 'historical average maximum use',
        'average_lowest': 'historical average minimum use',
        #'average_max': '',
        #'average_min': '',
        'input': 'instantenous use',
        'input_highest': 'historical maximum use',
        'input_lowest': 'historical minimum use',
        #'reset_history'
        'accuracy': 'accuracy of the meter',
        'cap': 'cap',
        'cap_hyst': 'margin of hysteresis built around capping and notification',
        'cap_max': 'maximum cap that can be set',
        'cap_min': 'minimum cap that can be set',
        'max': 'maximum',
        'crit': 'critical maximum',
        'enable': 'sensor enabled'
    },
    'energy': {},
    'humidity': {},
    'freq': {
        'label': 'suggested channel label',
        'enable': 'sensor enabled'
    }
}

sensors_units_dict = {
    'in': {
        'min': 'mV',
        'lcrit': 'mV',
        'max': 'mV',
        'crit': 'mV',
        'input': 'mV',
        'average': 'mV',
        'lowest': 'mV',
        'highest': 'mV',
    },
    'fan': {
        'min': 'RPM',
        'max': 'RPM',
        'input': 'RPM',
        'target': 'RPM',
    },
    'pwm': {},
    'temp': {
        'crit': '°C',
        'crit_hyst': '°C',
        'input': '°C'
    },
    'curr': {
        'input': 'mA'
    },
    'power': {
        'cap': 'W',
        'cap_min': 'W',
        'cap_max': 'W',
        'input': 'W'
    },
    'energy': {
        'input': 'mcJ'
    },
    'humidity': {},
    'freq': {
        'input': 'Hz',
    }
}

sensors_multipliers_dict = {
    'in': {
        'min': 0.001,
        'lcrit': 0.001,
        'max': 0.001,
        'crit': 0.001,
        'input': 0.001,
        'average': 0.001,
        'lowest': 0.001,
        'highest': 0.001,
    },
    'pwm': {},
    'temp': {
        'input': 0.001
    },
    'curr': {
        'input': 0.001
    },
    'power': {
        'input': 0.000001
    },
    'energy': {
        'input': 0.000001
    },
    'humidity': {},
}

def add_sensor(item, sensors_dict, device_dict, device_path, subsystem_item):
    name, param = (item.split('_', 1)+[''])[:2]
    for k in sensors_params_dict:
        if name.startswith(k):
            sensor = k
            sensor_params_dict = sensors_params_dict[k]
            sensor_units_dict = sensors_units_dict[k]
            break
    if name not in sensors_dict:
        if name+'_label' in device_dict['listdir']:
            label = get_file_contents(device_path, name+'_label')
        else:
            label = None
        sensors_dict[name] = QTreeWidgetItem(subsystem_item, [sensors_titles_dict.get(sensor, sensor)+' '+name[len(sensor):]+(': "'+label+'"' if label is not None else '')])
    if item == name+'_label':
        return
    QTreeWidgetItem(sensors_dict[name], [sensor_params_dict.get(param, param)+': '+get_file_contents(device_path, item)+(' '+sensor_units_dict[param] if param in sensor_units_dict else '')])    
    

def iter_props_tree_items(device_path, device_dict):
    parent_item = None

    subsystem_item = QTreeWidgetItem(parent_item, ['Subsystem: Hardware monitoring'])

    QTreeWidgetItem(subsystem_item, ['Chip name: '+device_dict['chip_name']])

    sensors_dict = {}
    for item in device_dict['listdir']:
        if any(item.startswith(k) and len(item)>len(k) and item[len(k)].isdigit() for k in sensors_params_dict):
            add_sensor(item, sensors_dict, device_dict, device_path, subsystem_item)
        elif item.startswith('fan'):
            name, param = item.split('_')
            if name not in sensors_dict:
                if name+'_label' in device_dict['listdir']:
                    label = get_file_contents(device_path, name+'_label')
                sensors_dict[name] = QTreeWidgetItem(subsystem_item, ['Fan '+name[len('fan'):]])
            if item == name+'_label':
                continue
            QTreeWidgetItem(sensors_dict[name], [fan_params_dict.get(param, param)+': '+get_file_contents(device_path, item)])
        elif item.startswith('freq'):
            add_sensor(item)
        elif item.startswith('power'):
            pass
        elif item.startswith('pwm'):
            pass
        elif item.startswith('temp'):
            pass

    yield subsystem_item
