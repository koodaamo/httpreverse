#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
test_httpreverse
----------------------------------

Tests for `httpreverse` module.
"""

import sys, os, unittest, json
import yaml
import xmltodict
from httpreverse import expand_jinja, apply_template, parametrize
from httpreverse import marshal_request_params, marshal_request_body
from httpreverse import _load_parser, _load_generator


class BaseTestCase(unittest.TestCase):

   def setUp(self):

      fpth = os.path.dirname(__file__) + os.sep + "testapi.yml"
      with open(fpth) as apifile:
         self.source = apifile.read()

      self.context = {"sizes": ["family", "suite"]}

   def _get_expanded_testop(self, name):
      return apply_template(self.parsed["operations"][name], templates=self.templates)


class Test01_JinjaExpansion(BaseTestCase):
   "test API expansion using Jinja templating"

   def test1_expansion(self):
      "the Jinja syntax is expanded with given context"
      expanded = expand_jinja(self.source, context=self.context)
      assert ("list-family-rooms" in expanded) and ("list-suite-rooms" in expanded)

   def test2_parsable(self):
      "the expanded API spec can be parsed by YAML"
      expanded = expand_jinja(self.source, context=self.context)
      parsed = yaml.load(expanded)
      assert ("list-family-rooms" in expanded) and ("list-suite-rooms" in expanded)


class Test02_TemplateApplication(BaseTestCase):
   "test request template system"

   def setUp(self):
      super().setUp()
      self.expanded = expand_jinja(self.source, context=self.context)
      self.parsed = yaml.load(self.expanded)
      self.templates = self.parsed["templates"]

   def test1_applytemplate_for_all(self):
      "the request remplates are expanded"
      for opname, opspec in self.parsed["operations"].items():
         opspec = apply_template(opspec, templates=self.templates)
         assert "response" in opspec and "json" in opspec["response"].get("type", "")


class Test03_Parametrization(BaseTestCase):
   "test API operation spec parametrization"

   def setUp(self):
      super().setUp()
      self.expanded = expand_jinja(self.source, context=self.context)
      self.parsed = yaml.load(self.expanded)
      self.templates = self.parsed["templates"]
      self.contexts = self.parsed["contexts"]

   def test1_explicit_parametrization(self):
      "data structure is correctly parametrized"
      testopname = "add-reservation"
      testop = self._get_expanded_testop(testopname)
      testcontext = {"customers":["John Doe", "Jane Doe"], "size":"double"}
      parametrize(testop, context=testcontext)
      result = testop["request"]["body"]["value"]
      assert testop["request"]["body"]["value"] == testcontext

   def test2_parametrize_from_static_context(self):
      "data structure is correctly parametrized from context embedded in API"
      testopname = "add-reservation"
      testop = self._get_expanded_testop(testopname)
      testcontext = self.contexts[testop["context"]]
      parametrized = parametrize(testop, context=testcontext)
      assert parametrized["request"]["body"]["value"] == testcontext

   def test3_parametrize_partially_from_static_context_nofail(self):
      "can handle partial parametrization from larger static context"
      testopname = "list-doublerooms"
      testop = self._get_expanded_testop(testopname)
      testcontext = self.contexts[testop["context"]]
      parametrized = parametrize(testop, context=testcontext)
      assert parametrized["request"]["params"]["size"] == testcontext["size"]

   def test4_parametrize_two_variables(self):
      "can replace $name1 $name2"
      testopname = "add-note"
      testop = self._get_expanded_testop(testopname)
      testcontext = self.contexts[testop["context"]]
      parametrized = parametrize(testop, context=testcontext)
      assert parametrized["request"]["body"] == " ".join(testcontext.values())


class Test04_loader(BaseTestCase):
   "test loading of request generators and response parsers"

   def setUp(self):
      super().setUp()
      self.expanded = expand_jinja(self.source, context=self.context)
      self.parsed = yaml.load(self.expanded)

   def test1_parser_loading(self):
      testopname = "list-singlerooms"
      opspec = self.parsed["operations"][testopname]
      opspec = apply_template(opspec, templates=self.parsed["templates"])

      _load_parser(opspec, assign=True)
      assert opspec["response"]["parser"].__name__ == "parse_json"

   def test2_generator_loading(self):

      # this is faked, but for testing purposes it's ok, it still tests
      # _load_generator as it should

      testopname = "list-singlerooms"
      opspec = self.parsed["operations"][testopname]
      opspec = apply_template(opspec, templates=self.parsed["templates"])
      opspec["request"]["generator"] = "httpreverse.util:parse_json"
      _load_generator(opspec, assign=True)
      assert opspec["request"]["generator"].__name__ == "parse_json"


class Test05_body_conversion(BaseTestCase):
   "test body marshaling by setting body explicitly and then marshaling it"

   def setUp(self):
      super().setUp()
      self.expanded = expand_jinja(self.source, context=self.context)
      self.parsed = yaml.load(self.expanded)

      # the test API operation
      testopname = "list-singlerooms"
      opspec = self.parsed["operations"][testopname]
      self.opspec = apply_template(opspec, templates=self.parsed["templates"])

      # yes, neither the API spec nor the template has a body, we assign the body value
      # explicitly in the test here, so that this will be converted (type is set by tests)
      self.bodyvalue = {"root": {"size": "double", "customer": ["John", "Jane"]}}
      self.opspec["request"]["body"] = {"value": self.bodyvalue}

   def test1_body_json_marshal(self):
      "request body is correctly marshalled to JSON"
      self.opspec["request"]["body"]["type"] = "application/json"
      marshal_request_body(self.opspec, self.parsed.get("defaults", {}))
      result = self.opspec["request"]["body"]["value"]
      assert self.bodyvalue == json.loads(result)

   def test2_body_xml_marshal(self):
      "request body is correctly marshalled to XML"
      self.opspec["request"]["body"]["type"] = "application/xml"
      marshal_request_body(self.opspec, self.parsed.get("defaults", {}))
      result = self.opspec["request"]["body"]["value"] # this should now be XML ...
      assert self.bodyvalue == xmltodict.parse(result)



class Test06_params_marshaling(BaseTestCase):
   "test params marshaling"

   def setUp(self):
      super().setUp()
      self.expanded = expand_jinja(self.source, context=self.context)
      self.parsed = yaml.load(self.expanded)

      # the test API operation
      testopname = "add-note"
      opspec = self.parsed["operations"][testopname]
      self.opspec = apply_template(opspec, templates=self.parsed["templates"])

   def test1_param_json_marshal(self):
      "request param is correctly marshalled to JSON"
      context = self.parsed["contexts"][self.opspec["context"]]
      parametrize(self.opspec, context=context)
      marshal_request_params(self.opspec, self.parsed.get("defaults", {}))
      result = self.opspec["request"]["params"]["note"]
      assert self.opspec["request"]["params"]["note"] == result
