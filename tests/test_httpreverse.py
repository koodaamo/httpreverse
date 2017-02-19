#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
test_httpreverse
----------------------------------

Tests for `httpreverse` module.
"""

import sys, os, unittest
import yaml
from httpreverse import expand_jinja, apply_templates, parametrize


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

   def test1_applytemplates(self):
      operations = apply_templates(self.parsed, self.context)
      for opname, opspec in operations.items():
         assert "response" in opspec and "json" in opspec["response"].get("type", "")


class Test03_Parametrization(unittest.TestCase):

   def setUp(self):
      fpth = os.path.dirname(__file__) + os.sep + "testapi.yml"
      with open(fpth) as apifile:
         self.source = apifile.read()
      self.context = {"sizes": ["family", "suite"]}
      self.expanded = expand_jinja(self.source, context=self.context)
      self.parsed = yaml.load(self.expanded)
      self.templated = apply_templates(self.parsed, self.context)

   def test1_parametrize(self):
      context = {"roomsize":"double", "customers":["John Doe", "Jane Doe"]}
      ops = parametrize(self.templated, context=context)
      expected = {"size": "double", "customers": ["John Doe", "Jane Doe"]}
      assert ops["add-reservation"]["request"]["body"] == expected
