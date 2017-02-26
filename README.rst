===============================
httpreverse
===============================

.. image:: https://img.shields.io/pypi/v/httpreverse.svg
        :target: https://pypi.python.org/pypi/httpreverse

Tool to help reverse-engineer legacy HTTP APIs.

Rationale and scope
--------------------

This package was born of a need to be able to use multiple different kinds of
existing, undocumented legacy HTTP APIs not following any kind of consistent,
well planned design. It was also thought helpful to be able to add a little bit
of documentation about what those legacy APIs do.

This package is NOT meant for defining new APIs. Use e.g. Swagger for that.

Why then not just use Swagger or some other such tool? They are really meant for
creating new APIs from scratch and as such cater to a bit different use case.
For example they tend to be geared toward the verbose. When reverse-engineering
and documenting existing APIs, all the details are not that important. We just
need to make it easy to use the APIs and be able to add an explanation of what
they do, rather than documenting everything.

The examples hopefully clarify the difference and some of the benefits of this
package.

Note that this package does NOT make HTTP requests using some client library.
That is up to you; use something from the Python standard library, or the
'requests' package, or something asynchronous, whatever.

API specification examples
------------------------

Note: these examples are illustrative. For working examples, see the tests.

**Simple example**

An example API definition in YAML that specifies two operations for querying
single and double rooms reservations, respectively::

  label: Hotel API
  description: An API to check room reservations

  operations:

    list-singlerooms:
      label: List single room reservations
      description: List all reserved single rooms

      request:
        method: GET
        path: /hotel/reservations
        params:
          size: single

      response:
        type: application/json
        parser: hotelapi.util:parseresponse

    list-doublerooms:
      label: List double room reservations
      description: List all reserved double rooms

      request:
        method: GET
        path: /hotel/reservations
        params:
          size: double

      response:
        type: application/json
        parser: hotelapi.parseresponse


This is similar to how many specification syntaxes express HTTP APIs. Clear,
but often lots of boilerplate and repetition. Parses into a plain dict using
PyYaml as-is. Now let's see how to save some effort.


**Using Jinja templating for API spec expansion**

The API document can be expanded using Jinja2 templating. Using our room
reservation example, we could generate an API operation for each room size
variation::

  operations:

    {% for size in sizes %}

    list-{{size}}-rooms:
      label: List {{size}} room reservations
      description: List all reserved {{size}} rooms
        request:
          method: GET
          path: /hotel/reservations
          params:
            size: {{size}}

    {% endfor %}

Two different API operations would be generated, such as with this code, assuming
the api spec has been read into a string variable called 'yamlsource':

>>> from httpreverse import expand_jinja
>>> expanded = expand_jinja(yamlsource, context={"sizes":["single", "double"]})
>>>

For blunt copying of parts of the YAML document to another place, the standard
YAML anchor/alias mechanism can of course be used as well.

**Templated request specifications**

Besides Jinja templating, a custom templating mechanism is provided for request
and response specification convenience. Here's an example with a ``roomapi``
request/response template that is used to move repetitive request and response
specifications into a common template, referred to from the actual specs::

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

Here's how to apply the request/response template in Python:

>>> from httpreverse import apply_template
>>> api = yaml.load(yamlsource)
>>> templates = api["templates"]
>>> operation = api["operations"]["list-doublerooms"]
>>> applied = apply_template(operation, templates)
>>>

**Simple parametrization**

The API definitions can also be parametrized for convenient run-time use. The
parametrization function accepts an optional context argument that is simply
a dictionary that is used to assign values to all the named parameters found
in the operations. Parameters are prefixed with the dollar sign ('$'). So it
would be possible to also specify a single dynamically invoked operation for
listing the rooms::

  operations:

    list-rooms:
      label: List room reservations
      description: List reserved rooms
      template: roomapi
      request:
        params:
          size: $size

By passing either ``{"size":"single"}`` or ``{"size": "double"}`` as context,
room size values would then be assigned:

>>> from httpreverse import parametrize
>>> api = yaml.load(yamlsource)
>>> operation = api["operations"]["list-rooms"]
>>> parametrized = parametrize(operation, context={"size":single})
>>>

More complex parametrizations are possible using the same simple mechanism::

  operations:

    add-reservation:
      label: Add reservation
      description: Add a room reservation
      template: roomapi
      request:
        method: POST
        body:
          value: {"size": $roomsize, "customers": $customers}
          type: application/json

The context would then have to include both the room size and occupants, ie.
``{"roomsize":"double", "customers":["John Doe", "Jane Doe"]}``.

Consult the YAML documentation for more on what kind of data structures are
possible to express.

When a `type` + `value` is given for a parameter or body (as above), the
value is automatically marshaled to the given type (json in above example).
If a parameter or body is given directly (no type+value syntax), a default
must be given thus:

  defaults:

    structured_param_type: json
    structured_body_type: json

The above API snippet would specify that whenever a structured parameter
or body value is encountered (such as a container or mapping), it will be
marshalled to json. Simple values (strings, numbers etc) are used as-is.

**Request generator and response parser loading**

There are two convenience functions, ``_load_generator`` for loading the
request generator and ``_load_parser`` for loading the response parser:

>>> from httpreverse import _load_parser
>>> api = yaml.load(yamlsource)
>>> parser = _load_parser(api["list-rooms"])
>>>

**Recommended API operations spec generation and use**

Typically, when using httpreverse to e.g. make http requests using whatever
http client you have, you might want to first run just the Jinja expansion
first and parse the resulting YAML string. Then, apply the request/response
templates for the operations you expect to be using (or maybe all of them).
Keep a copy of the the result. Finally, for each HTTP request, just parametrize
the API operation being used, marshal parameters and body and fire away!
