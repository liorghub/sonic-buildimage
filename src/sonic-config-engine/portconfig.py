#!/usr/bin/env python

try:
    import os
    import sys
    import ast
    import json
    from swsssdk import ConfigDBConnector
except ImportError as e:
    raise ImportError("%s - required module not found" % str(e))


def get_port_config_file_name(hwsku=None, platform=None, asic=None):
    port_config_candidates = []
    port_config_candidates.append('/usr/share/sonic/hwsku/port_config.ini')
    if hwsku:
        if platform:
            if asic:
                port_config_candidates.append(os.path.join('/usr/share/sonic/device', platform, hwsku, asic,'port_config.ini'))
            port_config_candidates.append(os.path.join('/usr/share/sonic/device', platform, hwsku, 'port_config.ini'))
        port_config_candidates.append(os.path.join('/usr/share/sonic/platform', hwsku, 'port_config.ini'))
        port_config_candidates.append(os.path.join('/usr/share/sonic', hwsku, 'port_config.ini'))
    for candidate in port_config_candidates:
        if os.path.isfile(candidate):
            return candidate
    return None


def get_ports_config_db():
    config_db = ConfigDBConnector()
    try:
        config_db.connect()
        ports_table = config_db.get_table("PORT")
        ports = ast.literal_eval(json.dumps(ports_table))
    except Exception as e:
        ports = None
    return ports


def get_port_config(hwsku=None, platform=None, port_config_file=None, asic=None, get_ports_from_db=False):
    if get_ports_from_db:
        ports = get_ports_config_db()
        return (ports, {}, {})

    if not port_config_file:
        port_config_file = get_port_config_file_name(hwsku, platform, asic)
        if not port_config_file:
            return ({}, {}, {})
    return parse_port_config_file(port_config_file)


def parse_port_config_file(port_config_file):
    ports = {}
    port_alias_map = {}
    port_alias_asic_map = {}
    # Default column definition
    titles = ['name', 'lanes', 'alias', 'index']
    with open(port_config_file) as data:
        for line in data:
            if line.startswith('#'):
                if "name" in line:
                    titles = line.strip('#').split()
                continue;
            tokens = line.split()
            if len(tokens) < 2:
                continue
            name_index = titles.index('name')
            name = tokens[name_index]
            data = {}
            for i, item in enumerate(tokens):
                if i == name_index:
                    continue
                data[titles[i]] = item
            data.setdefault('alias', name)
            ports[name] = data
            port_alias_map[data['alias']] = name
            # asic_port_name to sonic_name mapping also included in
            # port_alias_map
            if (('asic_port_name' in data) and
                (data['asic_port_name'] != name)):
                port_alias_map[data['asic_port_name']] = name
            # alias to asic_port_name mapping
            if 'asic_port_name' in data:
                port_alias_asic_map[data['alias']] = data['asic_port_name'].strip()
    return (ports, port_alias_map, port_alias_asic_map)


