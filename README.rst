===============================
httpreverse
===============================


.. image:: https://img.shields.io/pypi/v/httpreverse.svg
        :target: https://pypi.python.org/pypi/httpreverse

.. image:: https://readthedocs.org/projects/httpreverse/badge/?version=latest
        :target: https://httpreverse.readthedocs.io/en/latest/?badge=latest
        :alt: Documentation Status

.. image:: https://pyup.io/repos/github/petri/httpreverse/shield.svg
     :target: https://pyup.io/repos/github/petri/httpreverse/
     :alt: Updates


Reverse-engineer legacy HTTP APIs.

This package was born of a need to wrap a lot of different kinds of existing,
undocumented legacy HTTP APIs not following any kind of consistent, well
planned design, and to add a little bit of documentation to have some idea
what those legacy APIs do.

This package is NOT meant for defining new APIs. Use e.g. Swagger for that.

Example API definition in YAML::

  label: Short name of the API
  description: A description of the API

  templates:

    getinfo:
       request:
          method: GET
          path: /hotel/reservations
       response:
         type: application/json
          parser: hotelapi.parseresponse

  operations:

    list-singlerooms:
      label: List single room reservations
      description: List all reserved single rooms
      template: getinfo
      request:
         params:
            size: single

    list-doublerooms:
      label: List double room reservations
      description: List all reserved double rooms
      template: getinfo
      request:
        params:
          size: double

* Free software: GNU General Public License v3
* Documentation: https://httpreverse.readthedocs.io.


Features
--------

* TODO

Credits
---------

This package was created with Cookiecutter_ and the `audreyr/cookiecutter-pypackage`_ project template.

.. _Cookiecutter: https://github.com/audreyr/cookiecutter
.. _`audreyr/cookiecutter-pypackage`: https://github.com/audreyr/cookiecutter-pypackage

