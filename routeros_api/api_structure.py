import abc
import collections
import datetime
import ipaddress
import re


class Field(object):
    __metaclass__ = abc.ABCMeta

    @abc.abstractmethod
    def get_mikrotik_value(self, arg):
        """
        :rtype: bytes
        """
        raise NotImplementedError()

    @abc.abstractmethod
    def get_python_value(self, bytes):
        """
        :type bytes: bytes
        """
        raise NotImplementedError()


class StringField(Field):
    def get_mikrotik_value(self, string):
        return string.encode()

    def get_python_value(self, bytes):
        return bytes.decode('latin-1')


class BytesField(Field):
    def get_mikrotik_value(self, bytes):
        return bytes

    def get_python_value(self, bytes):
        return bytes


class BooleanField(Field):
    def get_mikrotik_value(self, condition):
        return b'yes' if condition else b'no'

    def get_python_value(self, bytes):
        assert bytes in (b'yes', b'true', b'no', b'false')
        return bytes in (b'yes', b'true')


class IntegerField(Field):
    def get_mikrotik_value(self, number):
        return str(number).encode()

    def get_python_value(self, bytes):
        return int(bytes.decode('latin-1'))


class TimedeltaField(Field):
    def get_mikrotik_value(self, timedelta):
        if timedelta is None:
            return b'none'
        else:
            seconds = int(timedelta.total_seconds())
            return '{}s'.format(seconds).encode()

    def get_python_value(self, bytes):
        if bytes == b'none':
            return None
        else:
            return self.parse_mikrotik_timedelta(bytes.decode('latin-1'))

    def parse_mikrotik_timedelta(self, time_string):
        new_timedelta_format = (
            r'^((?P<weeks>\d+)w)?((?P<days>\d+)d)?'
            r'((?P<hours>\d+)h)?((?P<minutes>\d+)m)?((?P<seconds>\d+)s)?'
            r'((?P<milliseconds>\d+)ms)?$')
        old_timedelta_format = (
            r'^((?P<weeks>\d+)w)?((?P<days>\d+)d)?'
            r'(?P<hours>\d+):(?P<minutes>\d+):(?P<seconds>\d+)'
            r'(\.(?P<milliseconds>\d+))?$')

        match = re.match(new_timedelta_format, time_string)
        if not match:
            match = re.match(old_timedelta_format, time_string)
        if match:
            groups = dict((k, int(v)) for k, v in match.groupdict('0').items())
            return datetime.timedelta(**groups)
        else:
            raise ValueError('{} does not match any mikrotik uptime format'
                             .format(time_string))


class IpNetworkField(Field):
    def get_mikrotik_value(self, ip_network):
        if ip_network:
            return str(ip_network).encode()
        else:
            return b''

    def get_python_value(self, bytes):
        if bytes:
            return ipaddress.ip_network(bytes.decode('latin-1'))
        else:
            return None


class ListField(Field):
    def __init__(self, subfield):
        self.subfield = subfield

    def get_mikrotik_value(self, objects):
        return b','.join(
            self.subfield.get_mikrotik_value(obj) for obj in objects)

    def get_python_value(self, bytes):
        separator = b',' if b';' not in bytes else b';'
        return [
            self.subfield.get_python_value(serialized)
            for serialized in bytes.split(separator)]


default_structure = collections.defaultdict(StringField)
