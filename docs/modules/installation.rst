Installation
============

Installation page

Requirements
-------------

You need installed Docker and Docker-Compose to start project.

Docker
^^^^^^

- `Windows/macOS`_
- `GNU/Linux`_

`Docker Compose`_
^^^^^^^^^^^^^^^^^


Development
-----------

- Run project (GNU/Linux, macOS)::

    $ docker login registry.gitlab.whiteaster.com
    $ URL="localhost" docker-compose -f docker-compose.dev.yml pull
    $ URL="localhost" docker-compose -f docker-compose.dev.yml build
    $ URL="localhost" docker-compose -f docker-compose.dev.yml up -d

- Run project (Windows)::

    $ docker login registry.gitlab.whiteaster.com
    $ $env:URL="localhost"; docker-compose -f docker-compose.dev.yml pull
    $ $env:URL="localhost"; docker-compose -f docker-compose.dev.yml build
    $ $env:URL="localhost"; docker-compose -f docker-compose.dev.yml up -d

Deployment
----------

- Run project (GNU/Linux, macOS)::

    $ docker login registry.gitlab.whiteaster.com
    $ URL="localhost" docker-compose -f docker-compose.prod.yml pull
    $ URL="localhost" docker-compose -f docker-compose.prod.yml up -d

- Run project (Windows)::

    $ docker login registry.gitlab.whiteaster.com
    $ $env:URL="localhost"; docker-compose -f docker-compose.prod.yml pull
    $ $env:URL="localhost"; docker-compose -f docker-compose.prod.yml up -d


.. _Windows/macOS: https://docs.docker.com/desktop/
.. _GNU/Linux: https://docs.docker.com/engine/install/
.. _Docker Compose: https://docs.docker.com/compose/

