"""
    A simple rest client implementation enabling easy round trip usage of rest services.

    Example Usage:
        rc = RestClient('https://tcrosley.dev.arincdirect.net/swift/', 'ca1', 'ca1')
        rc.get('heartbeat')
        >> {'received': '15-May-2012 11:53'}

"""

import base64
import json

import logging as log
from GEARestClient.gae_restful_lib import GAE_Connection as Connection

class RestClient(object):
    """
        Provides a simple interface to make multiple calls to a rest service, while remembering authentication.
    """

    def __init__(self, baseUrl, username=None, password=None, version=None, realm=None, useDigest=False):
        self.version = version
        self.__connectionData__ = {'base_url':baseUrl, 'username':username, 'password':password}
        self.__connection__ = Connection(**self.__connectionData__)

    def __open__(self, apiCall, method, data=None):
        if data != None:
            data = json.dumps(data).replace("\\\\/", "\/")

        headers = {'Content-Type':'application/json'}
        if self.version:
            headers['X-Version'] = self.version

        response = {'headers': {'status': 401}}
        tries = 0
        while response['headers']['status'] == 401 and tries < 50:
            try:
                if method in ['post', 'put', 'delete']:
                    response = getattr(self.__connection__, 'request_' + method)(apiCall, body=data, headers=headers)
                else:
                    response = getattr(self.__connection__, 'request_' + method)(apiCall, args=data, headers=headers)
            except NameError:
                self.__connection__ = Connection(**self.__connectionData__)
            tries += 1

        typeHeader = response['headers'].get('content-type')
        log.debug("RESPONSE:" + str(response))
        if typeHeader and 'json' in typeHeader:
            return json.loads(response['body'])
        else:
            return response['body']

    def get(self, apiCall, data=None):
        """
            Makes a rest GET call: appending 'apiCall' to the end of the URL
        """
        return self.__open__(apiCall, "get", data)

    def post(self, apiCall, data):
        """
            Makes a rest POST call: appending 'apiCall' to the end of the URL, and serializing 'data'
        """
        return self.__open__(apiCall, "post", data)

    def delete(self, apiCall, data=None):
        """
            Makes a rest DELETE call: appending 'apiCall' to the end of the URL
        """
        return self.__open__(apiCall, "delete", data)

    def put(self, apiCall, data):
        """
            Makes a rest PUT call: appending 'apiCall' to the end of the URL, and serializing 'data'
        """
        return self.__open__(apiCall, "put", data)
