import json
from collections import ChainMap
from xml.etree import ElementTree

from .httpreverse import apply_template, parametrize, marshal


def parse_json(response):
   return json.loads(response)

def parse_xml(response):
   return ElementTree.fromstring(response)

def prepare_opspec(opspec, api, params=None):
   "process an individual operation spec"

   # apply operation template
   if "template" in opspec:
      opspec = apply_template(opspec, api.get("templates", {}))

   # parametrize request
   context = api.get("contexts", {})
   if params:
      context.update(params)
   parametrize(opspec, context=context)

   # marshal parameters and body
   marshal(opspec, api.get("defaults", {}))

   return opspec
