try:
    from unittest import mock
except ImportError:
    import mock

import unittest

from routeros_api import api_structure as structure
from routeros_api import resource
from routeros_api.api_communicator import base

BYTES_STRUCTURE = {'bytes': structure.BytesField()}
BOOLEAN_STRUCTURE = {'boolean': structure.BooleanField()}


class TestTypedResource(unittest.TestCase):
    def test_unknown_resource_get(self):
        communicator = mock.Mock()
        response = base.AsynchronousResponse([{'x': b'y'}], command='')
        communicator.call.return_value.get.return_value = response
        some_resource = resource.RouterOsResource(communicator, '/unknown',
                                                  structure.default_structure)
        result = some_resource.get()
        self.assertEqual(result, [{'x': 'y'}])

    def test_unknown_resource_set(self):
        communicator = mock.Mock()
        some_resource = resource.RouterOsResource(communicator, '/unknown',
                                                  structure.default_structure)
        some_resource.set(x='y')
        communicator.call.assert_called_with(
            '/unknown/', 'set', arguments={'x': b'y'}, queries={},
            additional_queries=())

    def test_bytes_resource_get(self):
        communicator = mock.Mock()
        response = base.AsynchronousResponse([{'bytes': b'y'}], command='')
        communicator.call.return_value.get.return_value = response
        some_resource = resource.RouterOsResource(communicator, '/bytes',
                                                  BYTES_STRUCTURE)
        result = some_resource.get()
        self.assertEqual(result, [{'bytes': b'y'}])

    def test_bytes_resource_set(self):
        communicator = mock.Mock()
        some_resource = resource.RouterOsResource(communicator, '/bytes',
                                                  BYTES_STRUCTURE)
        some_resource.set(bytes=b'y')
        communicator.call.assert_called_with(
            '/bytes/', 'set', arguments={'bytes': b'y'}, queries={},
            additional_queries=())

    def test_boolean_resource_get(self):
        communicator = mock.Mock()
        response = base.AsynchronousResponse([{'boolean': b'yes'}], command='')
        communicator.call.return_value.get.return_value = response
        some_resource = resource.RouterOsResource(communicator, '/boolean',
                                                  BOOLEAN_STRUCTURE)
        result = some_resource.get()
        self.assertEqual(result, [{'boolean': True}])

    def test_boolean_resource_set(self):
        communicator = mock.Mock()
        some_resource = resource.RouterOsResource(communicator, '/boolean',
                                                  BOOLEAN_STRUCTURE)
        some_resource.set(boolean=True)
        communicator.call.assert_called_with(
            '/boolean/', 'set', arguments={'boolean': b'yes'}, queries={},
            additional_queries=())

        
    def test_unicode_decode_error(self):
        string = structure.StringField
        output = string.get_python_value(string,bytes=b'\xc2')
        self.assertEqual(output, 'Â')
        
        
    
    def test_blank_decode_byte(self):
        string = structure.StringField
        output = string.get_python_value(string,bytes=b'')
        self.assertEqual(output, '')
