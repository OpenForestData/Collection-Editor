Configuration
=============

Configuration page

Docker-compose environments
---------------------------

General
^^^^^^^

- ``SECRET_KEY`` - secret key for django framework. (Default: SECRET_KEY_REPLACE)

Django default database
^^^^^^^^^^^^^^^^^^^^^^^

- ``DB_NAME`` - general Django database name. (Default: collection_editor)
- ``DB_USER`` - username for database.  (Default: ce_user)
- ``DB_PASSWORD`` - password for database user. (Default: ce_password)
- ``DB_HOST`` - host address for database. (Default: ce_db)

Datable storage database
^^^^^^^^^^^^^^^^^^^^^^^^

- ``MONGO_DATABASE`` - datatables designated Django database name (Default: collection_editor)
- ``MONGO_HOST`` - ... (Default: ce_mongo)
- ``MONGO_USER`` - ... (Default: ce_user)
- ``MONGO_PASSWORD`` - ... (Default: ce_password)

LDAP
^^^^
Detailed documentation: https://django-auth-ldap.readthedocs.io/en/latest/

- ``LDAP_HOST`` - server host address
- ``LDAP_USERNAME`` - username for LDAP user.
- ``LDAP_PASSWORD`` - password for LDAP user.
- ``LDAP_SEARCH_HOST`` - distinguished name of the search base. (Default: '')
- ``LDAP_FORMAT`` - user naming attribute (Default: 'sAMAccountName')

Dataverse
^^^^^^^^^

- ``DATAVERSE_URL`` - URL of a Dataverse data should be exported to.
- ``DATAVERSE_ACCESS_TOKEN`` - Access Token of given Dataverse

Development settings
^^^^^^^^^^^^^^^^^^^^

- ``DEBUG`` - run application in debug mode. (Default: False)
- ``TESTING`` - run application in testing mode. (Default: False)


Settings
--------
Default, created on the start of an application permissions group names:

| ``READONLY_GROUP_NAME = 'ReadOnly'``
| ``READWRITE_GROUP_NAME = 'ReadWrite'``

In case of changing those names the change has to be also implemented in ``core/fixtures/initial_groups.json`` file.
