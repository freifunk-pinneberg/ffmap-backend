#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Knotendaten manuell ändern
Das ist z.B. für ausgeschaltete Knoten interessant, die nur 
temporär nicht zur Verfügung stehen. Die können ausgeblendet
werden.
Das ist besser als löschen, weil so die Statistik nicht
verschwindet

Änderungsprotokoll
==================

Version  Datum       Änderung(en)                                           von 
-------- ----------- ------------------------------------------------------ ----
1.0      2017-08-03  Programm in das ffmap-backend Projekt integriert       tho

"""

import argparse
import configparser
import json
import os
import sys
import glob

# Einstellungen werden in folgender Reihenfolge verarbeitet
# später gesetzte Werte überschreiben frühere
#  1. im Programm hart codiert
#  2. aus der zentralen Konfigurationsdatei gelesen  
#  3. als Kommandozeilenoptionen angegeben
cfg = {
    'cfgfile': '/etc/ffmap/ffmap.cfg',
    'logfile': '/var/log/ffmap.log',
    'loglevel': 2,
    'dest_dir': '/var/lib/ffmap/mapdata',
    'nodedb': '/var/lib/ffmap/nodedb',
    'imgpath': '/var/www/meshviewer/stats/img'
}

roles_defined = ('node', 'temp', 'mobile', 'offloader', 'service', 'test', 'gate', 'plan', 'hidden')

def main(cfg):

    # Pfade zu den beteiligten Dateien
    nodes_fn = os.path.join(cfg['dest_dir'], 'nodes.json')
    nodelist_fn = os.path.join(cfg['dest_dir'], 'nodelist.json')

    # 1. Knotendaten (NodeDB)
    # 1.1 Daten laden
    try:
        with open(nodes_fn, 'r') as nodedb_handle:
            nodedb = json.load(nodedb_handle)
    except IOError:
        print("Error reading nodedb file %s" % nodes_fn)
        nodedb = {'nodes': dict()}
    # 1.2 Knoten bearbeiten
    changed = False
    for n in cfg['nodeid']:
        if n in nodedb['nodes']:
            print("Modify %s in nodedb" % n)
            if 'role' in cfg and cfg['role'] in roles_defined:
                try:
                    oldrole = nodedb['nodes'][n]['nodeinfo']['system']['role']
                except KeyError:
                    oldrole = '<unset>'
                print("  - change role from '%s' to '%s'" % (oldrole, cfg['role']))
                nodedb['nodes'][n]['nodeinfo']['system']['role'] = cfg['role']
                changed = True
            if 'location' in cfg:
                print("  - remove location")
                # del nodedb['nodes'][n]['nodeinfo']['location']
                changed = True
        else:
            print("Node %s not found in nodedb" % n)        
    # 1.3 Geänderte Daten zurückschreiben
    if changed:
        try:
            with open(nodes_fn, 'w') as nodedb_handle:
                json.dump(nodedb, nodedb_handle)
        except IOError:
            print("Error writing nodedb file %s" % nodes_fn)

    # 2. Knotenliste (NodeList)
    try:
        with open(nodelist_fn, 'r') as nodelist_handle:
            nodelist = json.load(nodelist_handle)
    except IOError:
        print("Error reading nodelist file %s" % nodelist_fn)
        nodelist = {'nodelist': dict()}
    # 2.1 Knoten bearbeiten
    changed = False
    ixlist = []
    for nodeid in cfg['nodeid']:
        found = False
        for ix, node in enumerate(nodelist['nodes']):
            if node['id'] == nodeid:
                found = True
                break
        if found:
            print("Modify %s in nodelist" % nodeid)
            if 'role' in cfg and cfg['role'] in roles_defined:
                try:
                    oldrole = nodelist['nodes'][ix]['role']
                except KeyError:
                    oldrole = '<unset>'
                print("  - change role from '%s' to '%s'" % (oldrole, cfg['role']))
                nodelist['nodes'][ix]['role'] = cfg['role']
            if 'location' in cfg:
                print("  - remove location")
                try:
                    #del nodelist['nodes'][ix]['position']
                    pass
                except KeyError:
                    pass
                changed = True
        else:
            print ("Node %s not found in nodelist" % nodeid)
    # 2.3 Geänderte Daten zurückschreiben
    if changed:
        try:
            with open(nodelist_fn, 'w') as nodelist_handle:
                json.dump(nodelist, nodelist_handle)
        except IOError:
            print("Error writing nodelist file %s" % nodelist_fn)

if __name__ == "__main__":

    # Optionen von der Kommandozeile lesen
    parser = argparse.ArgumentParser()

    parser.add_argument('-c', '--config', action='store',
                        help='Configuration file')

    parser.add_argument('-d', '--dest-dir', action='store',
                        help='Directory with JSON data files',
                        required=False)

    parser.add_argument('-i', '--nodeid', metavar='ID', action='store',
                        nargs='+', required=True,
                        help='Node id to modify')

    parser.add_argument('-l', '--location', action='store_true',
                        help='Clear location information (hides node)',
                        required=False)

    parser.add_argument('-r', '--role', action='store',
                        help='Set new role',
                        required=False)

    # TODO
    # Optionen was genau gemacht werden soll
    # -p Position entfernen, Knoten wird nicht mehr angezeigt
    # -r <rolle> Rolle einstellen

    options = vars(parser.parse_args())


    # Konfigurationsdatei einlesen
    if options['config']:
        cfg['cfgfile'] = options['config']
    config = configparser.ConfigParser(cfg)
    # config.read liefert eine Liste der geparsten Dateien
    # zurück. Wenn sie leer ist, war z.B. die Datei nicht
    # vorhanden
    if config.read(cfg['cfgfile']):
        if 'global' in config:
            cfg['logfile'] = config['global']['logfile']
            cfg['loglevel'] = config['global']['loglevel']
            cfg['dest_dir'] = config['global']['dest_dir']
    else:
        print('Config file %s not parsed' % cfg['cfgfile'])

    # Optionen von der Kommandozeile haben höchste Priorität
    cfg['nodeid'] = options['nodeid']
    if options['dest_dir']:
        cfg['dest_dir'] = options['dest_dir']
    if options['location']:
        cfg['location'] = True
    if options['role']:
        cfg['role'] = options['role']

    # Alles initialisiert, auf geht's
    main(cfg)
