# Copyright (c) 2013 OpenStack, LLC.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or
# implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""
HTTPS/SSL related functionality
"""

import socket
import struct

from httplib import HTTPSConnection as _HTTPSConnection
import OpenSSL


class SSLCertificateError(BaseException):
    pass


class SSLConfigurationError(BaseException):
    pass


class HTTPSConnection(_HTTPSConnection):
    """
    Extended HTTPSConnection which attempts to use the OpenSSL
    library for enhanced SSL support
    Note: Much of this functionality can eventually be replaced
          with native Python 3.3 code.
    """
    def __init__(self, host, port=None, key_file=None, cert_file=None,
                 cacert=None, timeout=None, insecure=False,
                 ssl_compression=True):
        _HTTPSConnection.__init__(self, host, port,
                                  key_file=key_file,
                                  cert_file=cert_file)
        self.key_file = key_file
        self.cert_file = cert_file
        self.timeout = timeout
        self.insecure = insecure
        self.ssl_compression = ssl_compression
        self.cacert = cacert
        self.setcontext()

    @staticmethod
    def host_matches_cert(host, x509):
        """
        Verify that the the x509 certificate we have received
        from 'host' correctly identifies the server we are
        connecting to, ie that the certificate's Common Name
        or a Subject Alternative Name matches 'host'.
        """
        # First see if we can match the CN
        if x509.get_subject().commonName == host:
            return True

        # Also try Subject Alternative Names for a match
        san_list = None
        for i in xrange(x509.get_extension_count()):
            ext = x509.get_extension(i)
            if ext.get_short_name() == 'subjectAltName':
                san_list = str(ext)
                for san in ''.join(san_list.split()).split(','):
                    if san == "DNS:%s" % host:
                        return True

        # Server certificate does not match host
        msg = ('Host "%s" does not match x509 certificate contents: '
               'CommonName "%s"' % (host, x509.get_subject().commonName))
        if san_list is not None:
            msg = msg + ', subjectAltName "%s"' % san_list
        raise SSLCertificateError(msg)

    def verify_callback(self, connection, x509, errnum,
                        depth, preverify_ok):
        # NOTE(leaman): preverify_ok may be a non-boolean type
        preverify_ok = bool(preverify_ok)
        if x509.has_expired():
            msg = "SSL Certificate expired on '%s'" % x509.get_notAfter()
            raise SSLCertificateError(msg)

        if depth == 0 and preverify_ok:
            # We verify that the host matches against the last
            # certificate in the chain
            return self.host_matches_cert(self.host, x509)
        else:
            # Pass through OpenSSL's default result
            return preverify_ok

    def setcontext(self):
        """
        Set up the OpenSSL context.
        """
        self.context = OpenSSL.SSL.Context(OpenSSL.SSL.SSLv23_METHOD)

        if self.ssl_compression is False:
            self.context.set_options(0x20000)  # SSL_OP_NO_COMPRESSION

        if self.insecure is not True:
            self.context.set_verify(OpenSSL.SSL.VERIFY_PEER,
                                    self.verify_callback)
        else:
            self.context.set_verify(OpenSSL.SSL.VERIFY_NONE,
                                    lambda *args: True)

        if self.cert_file:
            try:
                self.context.use_certificate_file(self.cert_file)
            except Exception as e:
                msg = 'Unable to load cert from "%s" %s' % (self.cert_file, e)
                raise SSLConfigurationError(msg)
            if self.key_file is None:
                # We support having key and cert in same file
                try:
                    self.context.use_privatekey_file(self.cert_file)
                except Exception as e:
                    msg = ('No key file specified and unable to load key '
                           'from "%s" %s' % (self.cert_file, e))
                    raise SSLConfigurationError(msg)

        if self.key_file:
            try:
                self.context.use_privatekey_file(self.key_file)
            except Exception as e:
                msg = 'Unable to load key from "%s" %s' % (self.key_file, e)
                raise SSLConfigurationError(msg)

        if self.cacert:
            try:
                self.context.load_verify_locations(self.cacert)
            except Exception as e:
                msg = 'Unable to load CA from "%s"' % (self.cacert, e)
                raise SSLConfigurationError(msg)
        else:
            self.context.set_default_verify_paths()

    def connect(self):
        """
        Connect to an SSL port using the OpenSSL library and apply
        per-connection parameters.
        """
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        if self.timeout is not None:
            # '0' microseconds
            sock.setsockopt(socket.SOL_SOCKET, socket.SO_RCVTIMEO,
                            struct.pack('fL', self.timeout, 0))
        self.sock = OpenSSLConnectionDelegator(self.context, sock)
        self.sock.connect((self.host, self.port))

    def close(self):
        if self.sock:
            # Removing reference to socket but don't close it yet.
            # Response close will close both socket and associated
            # file. Closing socket too soon will cause response
            # reads to fail with socket IO error 'Bad file descriptor'.
            self.sock = None

        # Calling close on HTTPSConnection to continue doing that cleanup.
        HTTPSConnection.close(self)


class OpenSSLConnectionDelegator(object):
    """
    An OpenSSL.SSL.Connection delegator.

    Supplies an additional 'makefile' method which httplib requires
    and is not present in OpenSSL.SSL.Connection.

    Note: Since it is not possible to inherit from OpenSSL.SSL.Connection
    a delegator must be used.
    """
    def __init__(self, *args, **kwargs):
        self.connection = OpenSSL.SSL.Connection(*args, **kwargs)

    def __getattr__(self, name):
        return getattr(self.connection, name)

    def makefile(self, *args, **kwargs):
        # Making sure socket is closed when this file is closed
        # since we now avoid closing socket on connection close
        # see new close method under VerifiedHTTPSConnection
        kwargs['close'] = True

        return socket._fileobject(self.connection, *args, **kwargs)
