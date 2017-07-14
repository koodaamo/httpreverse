import json
from collections import ChainMap
from xml.etree import ElementTree

from .client import AsyncioAPIClient
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



import aiohttp
import async_timeout
from aiohttp import ClientOSError


async def get(session, url, params=None):
   with async_timeout.timeout(10):
      async with session.get(url) as response:
         if response.status == 200:
            return await response.text()
         else:
            raise Exception("Response status: %i" response.status)

async def post(session, url, data=None):
   with async_timeout.timeout(10):
      async with session.post(url, data=data) as response:
         if response.status == 200:
            return await response.text()
         else:
            raise Exception("Response status: %i" response.status)

"""
def do_request(opspec):
   "return method, url and params/data"

   method = globals().get(opspec["method"].lower())
   url = opspec["url"]
   params_or_data =
   http, url, args = extract_request(opspec)
   await http(url, args)

   return (method, url, params_or_data)
"""

async def run_operations(opname, api, context, hostinfo, authinfo=None, auther=None):

   COMPOSITE = REPEAT = False

   # accept either an operation or composite
   if opname in api["operations"]:
      opspec = api["operations"][opname]
   elif opname in api.get("composites", ""):
      opspec = api["composites"][opname]
      COMPOSITE = True
   else:
      raise Exception("no such operation '%s' found in the api" % opname)

   if "repeat" in opspec:
      REPEAT = True

   operations = opspec["operations"] if COMPOSITE else [opspec]

   async with aiohttp.ClientSession(loop=loop) as session:

      if REPEAT:
         for ctx in context:
            for opspec in operations:
               ctx = {"previous": do_request(opspec, ctx)}
      else:
         for opspec in ops:
            do_request(opspec, contextprovider)


"""
def get_operation_task(opname, api, contextprovider, hostinfo, authinfo=None, auther=None):
   "given a prepared spec, return an asyncio task that performs the operation"

   COMPOSITE = REPEAT = False

   # accept either an operation or composite
   if opname in api["operations"]:
      opspec = api["operations"][opname]
   elif opname in api.get("composites", ""):
      opspec = api["composites"][opname]
      COMPOSITE = True
   else:
      raise Exception("no such operation '%s' found in the api" % opname)

   if "repeat" in opspec:
      REPEAT = True

   operations = opspec["operations"] if COMPOSITE else [opspec]


   client = AsyncioAPIClient(hostinfo, authinfo, loglevel=ll, auther=auther)

   if repeat:
      for context in contextprovider:
         result = client.call(opspec, params=)

   else:
      result = client.call(opspec, params=)



   #-----



   hostinfo = (host, port)
   authinfo = (user, password)
   ll = getattr(logging, loglevel.upper())

   client = APIClient(hostinfo, authinfo, loglevel=ll)
   apiname, opname = op.split('/')
   api = apis[apiname]
   params = parse_named_cli_params(parameters)
   result = client.call(opname, api, params=params)
"""
