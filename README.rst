===============================
httpreverse
===============================


.. image:: https://img.shields.io/pypi/v/httpreverse.svg
        :target: https://pypi.python.org/pypi/httpreverse

Reverse-engineer legacy HTTP APIs.

Rationale and scope
--------------------

This package was born of a need to wrap a lot of different kinds of existing,
undocumented legacy HTTP APIs not following any kind of consistent, well
planned design, and to add a little bit of documentation to have some idea
what those legacy APIs do.

This package is NOT meant for defining new APIs. Use e.g. Swagger for that.

Why then not just use Swagger or some other such tool? They are really meant for
creating new APIs from scratch and as such cater to a bit different use case.
For example they tend to be geared toward the verbose. When reverse-engineering
and documenting existing APIs, all the details are not that important. We just
need to make it easy to use the APIs and be able to add an explanation of what
they do, rather than documenting everything. The docs hopefully help to clarify
the difference.

Note that this package does NOT make HTTP requests using some client library.
That is up to you; use something from the Python standard library, or the
'requests' package, or something asynchronous, whatever.

Example uses
-------------

An example templated API definition in YAML::

  label: Hotel API
  description: An API to check room reservations

  templates:

    roomapi:
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
      template: roomapi
      request:
        params:
          size: single

    list-doublerooms:
      label: List double room reservations
      description: List all reserved double rooms
      template: roomapi
      request:
        params:
          size: double

In the above example, a template is defined and then used to specify
two API operations that only need to specify some descriptive metadata,
the template to use, and any template overrides specific to the particular
API; such as a API-specific request parameter (room size).

Besides the template mechanism outlined here, the Regular YAML anchor/alias
mechanism can of course be used as well.

To generate actual HTTP requests, the API definitions can be parametrized.
For example, the API parser accepts an optional context argument that is
simply a dictionary that is mapped against all the parameter names found in
the API templates or operations. So in the above example it would be
possible to also have a single dynamically invoked operation for listing
the rooms::

  operations:

    list-rooms:
      label: List room reservations
      description: List reserved rooms
      template: roomapi
      request:
        params:
          size:

The API for single or double rooms would then be chosen at runtime by passing a
context, either ``{"size":"single"}`` or ``{"size": "double"}``. The parser would
fill the room size into the API spec.

Jinja2 templating can also be used anywhere within the YAML document. The same
context is passed to Jinja. The above example could thus be written::
 
  operations:

    list-rooms:
      label: List room reservations
      description: List reserved rooms
      template: roomapi
      request:
        params:
          size: {{roomsize}}

Assuming a context ``{"roomsize":"single"}``, we'd then have an API for querying
single rooms. Jinja templates can also be used to assign complex Python data
structures to the API. For example::

  operations:

    add-reservation:
      label: Add reservation
      description: Add a room reservation
      template: roomapi
      request:
        method: POST
        body: {{ {"size": roomsize, "customers": customers} }}
        type: application/json
  
The parser could then be called with a context that has both the room size and
occupant names: ``{"roomsize":"double", "customers":["John Doe", "Jane Doe"]}``,
to define a payload and have it encoded into JSON. XML is also supported.
