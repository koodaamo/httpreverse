# -*- coding: utf-8 -*-

import re
import json
from importlib import import_module
from collections import ChainMap, Mapping, MutableSequence
import yaml
import jinja2
import xmltodict

# parameter (name) extraction regexps
prm_xpr = re.compile('(\$)[\w_]+') # used to get all parameters
single_xpr = re.compile(" *\$[\w_]+ *$") # used to check if value is single parameter


def expand_jinja(apispecstr, context):
   "process any Jinja templating found in the API spec"

   return jinja2.Template(apispecstr).render(context)


def apply_template(opspec, templates):
   "apply the request/response template"

   try:
      template = templates[opspec["template"]]
   except:
      raise Exception("not using a template or given template not found!")

   # workarounds for when one dict shadows another's subelements in ChainMap
   # todo: review the ChainMap-based implementation, possibly replace with a custom one

   templated = ChainMap({}, opspec, template)

   if "request" in opspec and "request" in template:
      templated["request"] = ChainMap(opspec["request"], template["request"])
      if "params" in opspec["request"] and "params" in template["request"]:
         params = ChainMap(opspec["request"]["params"], template["request"]["params"])
         templated["request"]["params"] = params
   if "response" in opspec and "response" in template:
      templated["response"] = ChainMap(opspec["response"], template["response"])

   opspec["request"] = templated["request"]
   opspec["response"] = templated["response"]

   return templated


def _substitute(data, context):
   "traverse the data structure and do parameter substitution"

   if isinstance(data, Mapping):
      iterable = data.items()
   elif isinstance(data, MutableSequence):
      iterable = enumerate(data)
   elif isinstance(data, str):
      # single replacable parameter name in string
      if re.match(single_xpr, data):
         return context[data.strip().lstrip('$')]
      # multiple parameter names in string
      else:
         return re.sub(prm_xpr, lambda m: context[m.group()[1:]], data)
   else:
      return data

   for k, v in iterable:
      # try to substitute any string parts starting with marker
      if type(v) == str:
         # if the value is a single replacable, replace from context directly
         if re.match(single_xpr, v):
            data[k] = context[v.strip().lstrip('$')]
         # if there are multiple replacables, they must be strings so do re.sub
         else:
            data[k] = re.sub(prm_xpr, lambda m: context[m.group()[1:]], v)
      # or traverse deeper when needed, using recursion
      elif isinstance(data, Mapping) or isinstance(data, MutableSequence):
         _substitute(v, context) # RECURSE
      else:
         pass
   return data


def istypedvalue(v):
   if isinstance(v, Mapping) and "type" in v and "value" in v and len(v) == 2:
      return True
   else:
      return False


def ismarshallable(v):
   return True if isinstance(v, (Mapping, MutableSequence, tuple)) else False


def marshal_typed_value(value, default):
   "given a plain data structure or typed one, marshal it"

   if istypedvalue(value):
      marshal_to = value["type"]
      marshallable = value["value"]
   elif default:
      marshal_to = default
      marshallable = value
   else:
      raise Exception("marshaling requires default or explicit value for type")

   if "json" in marshal_to:
      marshalled = json.dumps(marshallable)
   elif "xml" in marshal_to:
      marshalled = xmltodict.unparse(marshallable)
   else:
      raise Exception("can only marshal to JSON or XML, not '%s'" % marshal_to)
   return {"value": marshalled, "type": marshal_to}


def marshal_request_params(opspec, defaults):
   "convert structural parameters to the specified type"

   default = defaults.get("structured_param_type", "")
   request = opspec["request"]
   params = opspec["request"]["params"]

   for paramname, param in params.items():
      if isinstance(param, (Mapping, MutableSequence)):
         marshalled = marshal_typed_value(param, default)
         request["params"][paramname] = marshalled["value"]

   return request["params"]


def marshal_request_body(opspec, defaults):
   "convert body to the specified type"

   default = defaults.get("structured_body_type", "")
   request = opspec["request"]
   body = request.get("body", "")

   if isinstance(body, (Mapping, MutableSequence)):
      marshalled = marshal_typed_value(body, default)
      request["body"] = marshalled

   return request["body"]


def marshal(opspec, defaults):
   marshal_request_params(opspec, defaults)
   if ismarshallable(opspec["request"].get("body")):
      marshal_request_body(opspec, defaults)


def _parametrize_request_params(request, context):
   if "params" in request:
      request["params"] = _substitute(request["params"], context)
   return request


def _parametrize_request_body(request, context):
   if "body" in request:
      request["body"] = _substitute(request["body"], context)
   return request


def parametrize(opspec, context={}):
   "assign parameter values to params/body, optionally implicitly using parameter names"

   request = opspec["request"]
   if "params" in request:
      opspec["request"] = _parametrize_request_params(request, context)
   if "body" in request:
      opspec["request"] = _parametrize_request_body(request, context)
   return opspec


def _load_callable(specstr):
   "try to import and return mypkg.mymodule:mycallable"

   try:
      module, callable = specstr.split(":")
   except:
      errmsg = "bad callable string '%s' given (syntax: pkg.module:callable)"
      raise Exception(errmsg % specstr)

   try:
      imported = import_module(module)
   except ModuleNotFoundError:
      raise Exception("no module '%s' found!" % module)

   try:
      callable = getattr(imported, callable)
   except:
      raise Exception("callable '%s' not found in module '%s'!" % (callable, module))

   return callable


def _load_parser(opspec, assign=True):
   "parse & load and (by default) assign response parser callable, if found"

   parser = _load_callable(opspec["response"]["parser"])
   if assign:
      opspec["response"]["parser"] = parser
   return parser


def _load_generator(opspec, assign=True):
   "parse & load and (by default) assign request generator callable, if found"

   generator = _load_callable(opspec["request"]["generator"])
   if assign:
      opspec["request"]["generator"] = generator
   return generator
