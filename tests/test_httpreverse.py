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

   def setUp(self):
      super().setUp()
      self.expanded = expand_jinja(self.source, context=self.context)
      self.parsed = yaml.load(self.expanded)
      self.templates = self.parsed["templates"]

   def test1_applytemplate_for_all(self):
      for opname, opspec in self.parsed["operations"].items():
         opspec = apply_template(opspec, templates=self.templates)
         assert "response" in opspec and "json" in opspec["response"].get("type", "")


class Test03_Parametrization(BaseTestCase):

   def setUp(self):
      super().setUp()
      self.expanded = expand_jinja(self.source, context=self.context)
      self.parsed = yaml.load(self.expanded)
      self.templates = self.parsed["templates"]
      self.contexts = self.parsed["contexts"]

   def test1_explicit_parametrization(self):
      testopname = "add-reservation"
      testop = self._get_expanded_testop(testopname)
      testcontext = {"size":"double", "customers":["John Doe", "Jane Doe"]}
      parametrized = parametrize(testop, context=testcontext)
      assert parametrized["request"]["body"] == testcontext

   def test2_parametrize_from_static_context(self):
      testopname = "add-reservation"
      testop = self._get_expanded_testop(testopname)
      testcontext = self.contexts[testop["context"]]
      parametrized = parametrize(testop, context=testcontext)
      assert parametrized["request"]["body"] == testcontext

   def test3_parametrize_partially_from_static_context_nofail(self):
      "can handle partial parametrization from larger static context"
      testopname = "list-doublerooms"
      testop = self._get_expanded_testop(testopname)
      testcontext = self.contexts[testop["context"]]
      parametrized = parametrize(testop, context=testcontext)
      assert parametrized["request"]["params"]["size"] == testcontext["size"]


class Test04_loader(BaseTestCase):

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

   def setUp(self):
      super().setUp()
      self.expanded = expand_jinja(self.source, context=self.context)
      self.parsed = yaml.load(self.expanded)

      # this will be converted to JSON and XML
      self.data = {"root": {"size": "double", "customer": ["John", "Jane"]}}

      testopname = "list-singlerooms"
      opspec = self.parsed["operations"][testopname]
      self.opspec = apply_template(opspec, templates=self.parsed["templates"])
      self.opspec["request"]["body"] = self.data

   def test1_json_convert(self):
      self.opspec["request"]["type"] = "application/json"
      parametrize(self.opspec, tojson=True)
      body = self.opspec["request"]["body"]
      assert self.data == json.loads(body)

   def test2_xml_convert(self):
      self.opspec["request"]["type"] = "application/xml"
      parametrize(self.opspec)
      body = self.opspec["request"]["body"]
      assert self.data == xmltodict.parse(body)
