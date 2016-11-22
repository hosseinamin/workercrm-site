# [Worker CRM](https://github.com/aminbros/workercrm-site)
A demo django site, Intended to provide service via it's api functions.
You can look at api definition at service/api.py

## Requirements

1. python 3.4 or higher
2. django 1.10
3. PyCrypto (Can get installed with ./setup.py)

## Installation

1. install the requirements
2. generate rsa `public/private key` in pem format, place it at `keys/userauth-pub.pem` and `keys/userauth-key.pem` (You can change this in settings)
3. Make a copy of `workercrm/settings-sample.py` with name `settings.py`
4. Set settings appropriately at `settings.py` (mysql and SECRET_KEY)

