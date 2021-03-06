"""
    A simple rest client implementation enabling easy round trip usage of rest services.

    Example Usage:
        rc = RestClient('https://tcrosley.dev.arincdirect.net/swift/', 'ca1', 'ca1')
        rc.get('heartbeat')
        >> {'received': '15-May-2012 11:53'}

"""

import base64
import cookielib
import json
import urllib
import urllib2
from urlparse import urlparse

#Authentication Types
BASIC = 0
DIGEST = 1
GOOGLE = 2

class RestClient(object):
    """
        Provides a simple interface to make multiple calls to a rest service, while remembering authentication.
    """
    opener = urllib2.build_opener()

    def __init__(self, baseUrl, username=None, password=None, version=None, realm=None, authType=BASIC, proxy=None):
        self.baseUrl = baseUrl
        self.__authCredentials__ = None
        self.proxy = proxy
        self.setCredentials(username, password, realm, authType)
        self.version = version
        self.response = None
        if proxy and authType == BASIC:
            self.opener = urllib2.build_opener(urllib2.ProxyHandler(proxy))

    def setCredentials(self, username, password, realm=None, authType=BASIC):
        """
            Sets the login user name and password to be passed with each call
        """
        self.authType = authType
        if authType == DIGEST:
            passwordManager = urllib2.HTTPPasswordMgr()
            passwordManager.add_password(realm, self.baseUrl, username, password)
            authhandler = urllib2.HTTPDigestAuthHandler(passwordManager)
            if self.proxy:
                self.opener = urllib2.build_opener(urllib2.ProxyHandler(self.proxy), authhandler)
            else:
                self.opener = urllib2.build_opener(authhandler)
        elif authType == GOOGLE:
            cookiejar = cookielib.LWPCookieJar()
            opener = urllib2.build_opener(urllib2.ProxyHandler(self.proxy), urllib2.HTTPCookieProcessor(cookiejar))
            urllib2.install_opener(opener)
            authRequestData = urllib.urlencode({ "Email":   username,
                                  "Passwd":  password,
                                  "service": "ah",
                                  "source":  urlparse(self.baseUrl).netloc,
                                  "accountType": "HOSTED_OR_GOOGLE" })
            authRequest = urllib2.Request('https://www.google.com/accounts/ClientLogin', data=authRequestData)
            authResponse = urllib2.urlopen(authRequest)
            authResponseBody = authResponse.read()

            authResponseDict = dict(x.split("=")
                                for x in authResponseBody.split("\n") if x)
            authtoken = authResponseDict["Auth"]
            self.opener = opener
            self.__authCredentials__ = authtoken
        else: # Basic Authentication
            self.__authCredentials__ = None
            if username and password:
                self.__authCredentials__ =  ('%s:%s' % (username, password)).encode('base64')[:-1]

    def __open__(self, apiCall, method, data=None):
        if self.authType == GOOGLE:
            serv_args = {}
            serv_args['continue'] = self.baseUrl + apiCall
            serv_args['auth'] = self.__authCredentials__

            full_serv_uri = "http://" + urlparse(self.baseUrl).netloc + "/_ah/login?%s" % (urllib.urlencode(serv_args))

            request = urllib2.Request(full_serv_uri)
            self.opener.open(request).read()
            request = urllib2.Request(self.baseUrl + apiCall)
        else:
            request = urllib2.Request(self.baseUrl + apiCall)
        request.get_method = lambda: method
        if data != None:
            request.add_data(json.dumps(data).replace("\\\\/", "\/"))

        if self.__authCredentials__:
            request.add_header("Authorization", "Basic %s" % self.__authCredentials__)

        request.add_header('Content-Type', 'application/json')
        if self.version:
            request.add_header('X-Version', self.version)

        self.response = self.opener.open(request)
        typeHeader = self.response.headers.get('Content-Type')
        if typeHeader and 'json' in typeHeader:
            return json.loads(self.response.read())
        else:
            return self.response.read()

    def get(self, apiCall, data=None):
        """
            Makes a rest GET call: appending 'apiCall' to the end of the URL
        """
        return self.__open__(apiCall, "GET", data)

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
