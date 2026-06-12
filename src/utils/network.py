import os
import xml.etree.ElementTree as ET


def sumo_tool(name):
    exe = name + (".exe" if os.name == "nt" else "")
    sumo_home = os.environ.get("SUMO_HOME")
    if sumo_home:
        candidate = os.path.join(sumo_home, "bin", exe)
        if os.path.exists(candidate):
            return candidate
    return exe


def parse_tl_junction_ids(net_xml_path):
    root = ET.parse(net_xml_path).getroot()
    return [tl.get("id") for tl in root.findall("tlLogic") if tl.get("id")]


def parse_junction_positions(net_xml_path):
    root = ET.parse(net_xml_path).getroot()
    positions = {}
    for junc in root.iter("junction"):
        jid = junc.get("id")
        if jid and not jid.startswith(":"):
            try:
                positions[jid] = (float(junc.get("x", 0)), float(junc.get("y", 0)))
            except (TypeError, ValueError):
                pass
    return positions


def parse_edge_geometries(net_xml_path):
    root = ET.parse(net_xml_path).getroot()
    edges = {}
    for edge in root.iter("edge"):
        eid = edge.get("id")
        if eid and not eid.startswith(":"):
            edges[eid] = (edge.get("from"), edge.get("to"))
    return edges
