#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
test_httpreverse
----------------------------------

Tests for `httpreverse` module.
"""

import sys, os, unittest
import yaml
from httpreverse import expand_jinja, apply_template, parametrize


class Test01_JinjaExpansion(unittest.TestCase):

   def setUp(self):
      fpth = os.path.dirname(__file__) + os.sep + "testapi.yml"
      with open(fpth) as apifile:
         self.source = apifile.read()

   def test1_expansion(self):
      "the Jinja syntax is expanded with given context"
      context = {"sizes": ["family", "suite"]}
      expanded = expand_jinja(self.source, context=context)
      assert ("list-family-rooms" in expanded) and ("list-suite-rooms" in expanded)

   def test2_parsable(self):
      "the expanded API spec can be parsed by YAML"
      context = {"sizes": ["family", "suite"]}
      expanded = expand_jinja(self.source, context=context)
      parsed = yaml.load(expanded)
      assert ("list-family-rooms" in expanded) and ("list-suite-rooms" in expanded)


class Test02_TemplateApplication(unittest.TestCase):

   def setUp(self):
      fpth = os.path.dirname(__file__) + os.sep + "testapi.yml"
      with open(fpth) as apifile:
         self.source = apifile.read()
      self.context = {"sizes": ["family", "suite"]}
      self.expanded = expand_jinja(self.source, context=self.context)
      self.parsed = yaml.load(self.expanded)
      self.templates = self.parsed["templates"]

   def test1_applytemplate_for_all(self):
      for opname, opspec in self.parsed["operations"].items():
         testop = apply_template(self.parsed["operations"][opname], templates=self.templates)
         opspec = apply_template(testop, self.templates)
         assert "response" in opspec and "json" in opspec["response"].get("type", "")


class Test03_Parametrization(unittest.TestCase):

   def _get_expanded_testop(self, name):
      return apply_template(self.parsed["operations"][name], templates=self.templates)

   def setUp(self):
      fpth = os.path.dirname(__file__) + os.sep + "testapi.yml"
      with open(fpth) as apifile:
         self.source = apifile.read()
      self.context = {"sizes": ["family", "suite"]}
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


