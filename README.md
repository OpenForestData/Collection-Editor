
# OpenForest Harvester
Application allows basic edition and filtering of tabular data

## Installation

### Requirements
All requirements all stored in requirements.txt file.

To run in container environment you need to install docker and docker-compose

### Application external dependencies
- Dataverse ➤ https://dataverse.org/

### Application environment variables

#### General 

- `SECRET_KEY` - secret key for django framework. (Default: SECRET_KEY_REPLACE)

#### Databases

- `DB_NAME` - general Django database name. (Default: collection_editor)
- `DB_HOST` - host address for database. (Default: ce_db)
- `DB_USER` - username for database. (Default: ce_user)
- `DB_PASSWORD` - password for database user. (Default: ce_password)

- `MONGO_DATABASE` - datatables designated Django database name, should be MongoDB database (Default: collection_editor)
- `MONGO_HOST` - host address for MongoDB database. (Default: ce_mongo)
- `MONGO_USER` - username for MongoDB database. (Default: ce_user)
- `MONGO_PASSWORD` - password for MongoDB database user. (Default: ce_password)  

#### Dataverse

- `LDAP_HOST` - server host address
- `LDAP_USERNAME` - username for LDAP user.
- `LDAP_PASSWORD` - password for LDAP user.
- `LDAP_SEARCH_HOST` - distinguished name of the search base. (Default: '')
- `LDAP_FORMAT` - user naming attribute (Default: 'sAMAccountName')  

Detailed LDAP documentation: https://django-auth-ldap.readthedocs.io/en/latest/  

#### Dataverse

- `DATAVERSE_URL` - URL of a Dataverse data should be exported to.
- `DATAVERSE_ACCESS_TOKEN` - Access Token of given Dataverse

#### Development

- `DEBUG` - run application in debug mode. (Default: False)
- `TESTING` - run application in testing mode. (Default: False)

### Application installation (local)

- Run project (GNU/Linux, macOS)::
```
URL="localhost" docker-compose pull
URL="localhost" docker-compose build
URL="localhost" docker-compose up -d
```

- Run project (Windows)
```
$env:URL="localhost"; docker-compose pull
$env:URL="localhost"; docker-compose build
$env:URL="localhost"; docker-compose up -d
```

## Application tests
You need to install testing dependencies within suitable environment (eg. inside Docker container):
```
pip install -r testing_requirements.txt
```

and set enviromental variable `TESTING` to `True`.


To run tests write:
```
python manage.py test
```
## Deployment

## Contribution
The project was performed by Whiteaster sp.z o.o., with register office in Chorzów, Poland - www.whiteaster.com and provided under the GNU GPL v.3 license to the Contracting Entity - Mammal Research Institute Polish Academy of Science in Białowieża, Poland. We are proud to release this project under an Open Source license. If you want to share your comments, impressions or simply contact us, please write to the following e-mail address: info@whiteaster.com
