import logging, asyncio
from string import Template
from collections.abc import Callable
from urllib.parse import quote_plus, urlencode

import aiohttp
from aiohttp import ClientOSError
import xmltodict

from .httpreverse import parametrize, marshal, apply_template


class AuthException(Exception):
   "raised when client authentication fails"


class AsyncioAPIClient:

   def __init__(self, hostinfo, authinfo=None, loglevel=None):

      self._host, self._port = hostinfo

      if authinfo:
         self._user, self._pass = authinfo
         self._auth = aiohttp.BasicAuth(*authinfo)
      else:
         self._user = self._pass = self._auth = None

      self._loop = asyncio.get_event_loop()
      self._logger = logging.getLogger(self.__class__.__name__)
      self._logger.setLevel(loglevel or logging.INFO)

   @property
   def session(self):
      try:
         return self._session
      except:
         self._session = aiohttp.ClientSession(loop=self._loop)
         return self._session

   def close(self):
      self.session.close()

   @property
   def sessionid(self):
      for c in self.session.cookie_jar:
         if c.key == "JSESSIONID":
            return c.value
      return None


   async def _caller(self, opspec):
      "make an API call according to operation spec and given named parameters"

      _params = opspec["request"]["params"]

      req = opspec["request"]
      httpmethod = getattr(self.session, req["method"].lower())
      url = "http://%s:%i/%s" % (self._host, self._port, req["location"].lstrip('/'))

      body = hdrs = None

      # add POST payload if present
      if "body" in req:
         body = req["body"]["value"]
         hdrs = {'content-type': req["body"]["type"]}

      self._logger.debug('request: ' + req["method"] + ' ' + url + '?' + urlencode(_params))
      self._logger.debug('body: ' + str(body))
      self._logger.debug('headers: ' + str(hdrs))

      # send the request with query params, body data & headers
      async with httpmethod(url, params=_params, data=body, headers=hdrs) as resp:
         result = await resp.text()
         self._logger.debug('response: %s %s' % (resp.status, result))
      return result


   def call(self, opname, api, params=None):
      "public api: call an API in a blocking manner"

      opspec = api["operations"][opname]

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

      # run the API operation HTTP request, optional auth first

      if self._auth:
         auther = self._auther()
         try:
            self._loop.run_until_complete(auther)
         except (AuthException, ClientOSError) as exc:
            self._logger.error(exc)
            return

      coro = self._caller(opspec)
      task = asyncio.ensure_future(coro, loop=self._loop)
      self._loop.run_until_complete(task)
      return task.result()
