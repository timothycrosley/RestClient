"""
    An implementation of RestClient made specifically to locally interact with django-piston rest api's
    enabling insertion of print statements and break points.

    Note: Use this from the djangoapps directory associated with your piston api

    Example Usage:
        lc = LocalRestClient('/swift/', 'ca1', 'ca1')
        lc.get('heartbeat')
        >> {'received': '15-May-2012 11:53'}
"""

import json

from django.core.handlers.wsgi import WSGIRequest
from django.core.urlresolvers import resolve
from django.http import HttpResponse

from djangoapps.swift.ApiAuthentication import ApiAuthenticationFunction
from RestClient import RestClient


CALL_MAP = {'DELETE': 'delete', 'GET': 'read', 'POST': 'create', 'PUT': 'update'}

class LocalRestClient(RestClient):
    """
        Overrides the RestClient class to make local rest client calls more efficient - by not making round trip calls.
    """

    def __init__(self, baseUrl="/", username=None, password=None, version=None):
        self.baseUrl = baseUrl
        self.version = version
        self.__user__ = None
        self.setCredentials(username, password)

    def setCredentials(self, username, password):
        """
            Sets the login user name and password to be passed with each call
        """
        self.__user__ = ApiAuthenticationFunction(username=username, password=password)

    def __open__(self, apiCall, method, data=None):
        request = {'REQUEST_METHOD':method}
        if self.version:
            request['HTTP_X_VERSION'] = self.version

        request = WSGIRequest(request)
        request.data = data or {}

        if self.__user__:
            request.user = self.__user__

        (handler, ignored, kwargs) = resolve(self.baseUrl + apiCall)

        emitterFormat = kwargs.pop('emitter_format', 'json')

        result = handler.handler.__getattribute__(CALL_MAP[method])(request, **kwargs)
        if isinstance(result, HttpResponse):
            return result.content
        return result

    def get(self, apiCall):
        """
            Makes a rest GET call: appending 'apiCall' to the end of the URL
        """
        return self.__open__(apiCall, "GET")

    def post(self, apiCall, data):
        """
            Makes a rest POST call: appending 'apiCall' to the end of the URL, and serializing 'data'
        """
        return self.__open__(apiCall, "POST", data)

    def delete(self, apiCall, data=None):
        """
            Makes a rest DELETE call: appending 'apiCall' to the end of the URL
        """
        return self.__open__(apiCall, "DELETE", data)

    def put(self, apiCall, data):
        """
            Makes a rest PUT call: appending 'apiCall' to the end of the URL, and serializing 'data'
        """
        return self.__open__(apiCall, "PUT", data)
