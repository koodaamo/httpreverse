import json
from xml.etree import ElementTree


def parse_json(response):
   return json.loads(response)

def parse_xml(response):
   return ElementTree.fromstring(response)
