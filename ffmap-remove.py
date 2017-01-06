#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Lösche einen Knoten manuell aus dem Backend:
- JSON
  - NodeDB
  - NodeList
  - Graph
- RRD-Dateien
- Bilder vom Webserver

Änderungsprotokoll
==================

Version  Datum       Änderung(en)                                           von 
-------- ----------- ------------------------------------------------------ ----
1.0      2017-01-06  Programm in das ffmap-backend Projekt integriert       tho

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
    'nodedb': '/var/lib/fmap/nodedb',
    'imgpath': '/var/www/meshviewer/stats/img'
}

def main(cfg):

    # Pfade zu den beteiligten Dateien
    nodes_fn = os.path.join(cfg['dest_dir'], 'nodes.json')
    graph_fn = os.path.join(cfg['dest_dir'], 'graph.json')
    nodelist_fn = os.path.join(cfg['dest_dir'], 'nodelist.json')

    # 1. Knotendaten (NodeDB) bereinigen
    # 1.1 Daten laden
    try:
        with open(nodes_fn, 'r') as nodedb_handle:
            nodedb = json.load(nodedb_handle)
    except IOError:
        print("Error reading nodedb file %s" % nodes_fn)
        nodedb = {'nodes': dict()}
    # 1.2 Knoten entfernen
    changed = False
    for n in cfg['nodeid']:
        if n in nodedb['nodes']:
            print("Remove %s from nodedb" % n)
            del nodedb['nodes'][n]
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

    # 2. Knotenliste (NodeList) bereinigen
    try:
        with open(nodelist_fn, 'r') as nodelist_handle:
            nodelist = json.load(nodelist_handle)
    except IOError:
        print("Error reading nodelist file %s" % nodelist_fn)
        nodelist = {'nodelist': dict()}
    # 2.1 Knoten entfernen
    changed = False
    ixlist = []
    for nodeid in cfg['nodeid']:
        found = False
        for ix, node in enumerate(nodelist['nodes']):
            if node['id'] == nodeid:
                found = True
                break
        if found:
            print("Remove %s from nodelist" % nodeid)
            del nodelist['nodes'][ix]
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

    # 3. Graph (NodeGraph) bereinigen
    # 3.1 Graph laden
    try:
        with open(graph_fn, 'r') as graph_handle:
            graph = json.load(graph_handle)
    except IOError:
        print("Error reading graph file %s" % graph_fn)
        graph = {'graph': dict()}
    # 3.2 Finde Knoten und Links
    # Nodes und Links gehören zusammen   
    changed = False
    for nodeid in cfg['nodeid']:
        found = False
        for ixn, node in enumerate(graph["batadv"]["nodes"]):
            # Es kann nodes ohne "node_id" geben
            try:
                if node["node_id"] == nodeid:
                    found = True
                    break
            except KeyError:
                pass
        if found:
            print("Found %s in graph nodes at index %d" % (nodeid, ixn))
            del graph["batadv"]["nodes"][ixn]
            # Suche Link source oder target dem gefundenen Index entsprechen
            ixlist = []
            for ixg, link in enumerate(graph["batadv"]["links"]):
                if link["source"] == ixn:
                    print("Found source link at index %d" % ixg)
                    print("  -> %s" % graph["batadv"]["nodes"][link["target"]])
                    ixlist.append(ixg)
                if link["target"] == ixn:
                    print("Found target link at index %d" % ixg)
                    print("  -> %s" % graph["batadv"]["nodes"][link["source"]])
                    ixlist.append(ixg)
            for ix in ixlist:
                del graph["batadv"]["nodes"][ix]
            changed = True
        else:
            print("Node %s not found in graph nodes" % nodeid)
    # 3.3 Zurückschreiben der geänderten Daten
    if changed:
        try:
            with open(graph_fn, 'w') as graph_handle:
                json.dump(graph, graph_handle)
        except IOError:
            print("Error writing graph file %s" % graph_fn)

    # 4. Entferne RRD-Dateien
    for nodeid in cfg['nodeid']:
        rrdfile = os.path.join(cfg['nodedb'], nodeid+'.rrd')
        if os.path.isfile(rrdfile):
            print("Removing RRD database file %s" % os.path.basename(rrdfile))
        else:
            print("RRD database file %s not found" % os.path.basename(rrdfile))
        try:
            os.remove(rrdfile)
        except OSError:
            pass

    # 5. Entferne Bilder vom Webserver
    count_deleted = 0
    for nodeid in cfg['nodeid']:
        for imagefile in glob.glob(os.path.join(cfg['imgpath'], nodeid+'_*.png')):
            print("Removing stats image %s" % os.path.basename(imagefile))
            try:
                os.remove(imagefile)
                count_deleted += 1
            except OSError:
                pass
    if count_deleted == 0:
        print("No stats images found in %s" % cfg['imgpath'])

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
                        help='Node id  to remove')

    parser.add_argument('-n', '--nodedb', metavar='RRD_DIR', action='store',
                        help='Directory for node RRD data files')

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
        if 'rrd' in config:
            cfg['nodedb'] = config['rrd']['nodedb']
    else:
        print('Config file %s not parsed' % cfg['cfgfile'])

    # Optionen von der Kommandozeile haben höchste Priorität
    cfg['nodeid'] = options['nodeid']
    if options['dest_dir']:
        cfg['dest_dir'] = options['dest_dir']
    if options['nodedb']:
        cfg['nodedb'] = options['nodedb']

    # Alles initialisiert, auf geht's
    main(cfg)
