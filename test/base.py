"Base class for tests."

import argparse
import http.client
import json
import os
import re
import sys
import unittest

import jsonschema
import requests

SCHEMA_LINK_RX = re.compile(r'<([^>])+>; rel="([^"]+)')

JSON_MIMETYPE = 'application/json'

DEFAULT_CONFIG = {
    'root_url': 'http://127.0.0.1:5001/api',
    'username': None,           # Needs to be set! Must have admin privileges.
    'apikey': None              # Needs to be set! For the above user.
}

# The actual configuration values to use.
CONFIG = {}

def process_args(filepath=None):
    """Process command-line arguments for this test suite.
    Reset the configuration and read the given configuration file.
    Return the unused arguments.
    """
    if filepath is None:
        parser = argparse.ArgumentParser()
        parser.add_argument('-C', '--config', dest='config',
                            metavar='FILE', default='config.json',
                            help='Configuration file')
        parser.add_argument('unittest_args', nargs='*')
        options, args = parser.parse_known_args()
        filepath = options.config
        args = [sys.argv[0]] + args
    else:
        args = sys.argv
    CONFIG.update(DEFAULT_CONFIG)
    with open(filepath) as infile:
        CONFIG.update(json.load(infile))
    return args

def run():
    unittest.main(argv=process_args())


class Base(unittest.TestCase):
    "Base class for Symbasis test cases."

    def setUp(self):
        self.schemas = {}
        self.session = requests.Session()
        self.session.headers.update({'x-apikey': CONFIG['apikey']})
        self.addCleanup(self.close_session)

    def close_session(self):
        self.session.close()

    @property
    def root(self):
        "Return the API root data."
        try:
            return self._root
        except AttributeError:
            response = self.session.get(CONFIG['root_url'])
            self.assertEqual(response.status_code, http.client.OK)
            self._root = self.check_schema(response)
            return self._root

    def check_schema(self, response):
        """If there is a schema linked in the response headers,
        check that the response JSON data matches that schema.
        Return the response JSON.
        """
        self.assertEqual(response.status_code, http.client.OK)
        result = response.json()
        try:
            url = response.links['schema']['url']
        except KeyError:
            pass
        else:
            try:
                schema = self.schemas[url]
            except KeyError:
                r = self.session.get(url)
                self.assertEqual(r.status_code, http.client.OK)
                schema = r.json()
                self.schemas[url] = schema
            self.validate_schema(result, schema)
        return result

    def validate_schema(self, instance, schema):
        "Validate the JSON instance versus the given JSON schema."
        jsonschema.validate(instance=instance,
                            schema=schema,
                            format_checker=jsonschema.draft7_format_checker)
