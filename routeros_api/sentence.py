import re

from routeros_api import exceptions
from routeros_api import query
from six import string_types

response_re = re.compile(rb'^!(re|trap|fatal|done)$')
attribute_re = re.compile(rb'^=([^=]+)=(.*)$', re.DOTALL)
tag_re = re.compile(rb'^\.tag=(.*)$')


class ResponseSentence(object):
    def __init__(self, type):
        self.attributes = {}
        self.type = type
        self.tag = None

    @classmethod
    def parse(cls, sentence):
        response_match = response_re.match(sentence[0])
        if response_match:
            response = cls(response_match.group(1))
            response.parse_attributes(sentence[1:])
        else:
            raise exceptions.RouterOsApiParsingError("Malformed sentence %s",
                                                     sentence)
        return response

    def parse_attributes(self, serialized_attributes):
        for serialized in serialized_attributes:
            attribute_match = attribute_re.match(serialized)
            tag_match = tag_re.match(serialized)
            if attribute_match:
                key, value = attribute_match.groups()
                self.attributes[key] = self.process_value(value)
            elif tag_match:
                self.tag = tag_match.group(1)
            else:
                raise exceptions.RouterOsApiParsingError(
                    "Malformed attribute %s", serialized)

    def process_value(self, value):
        return value


class CommandSentence(object):
    def __init__(self, path, command, tag=None):
        self.path = path
        self.command = command
        self.attributes = {}
        self.api_attributes = {}
        self.queries = set()
        self.tag = tag

    def get_api_format(self):
        formated = [self.path + self.command]
        for key, value in self.attributes.items():
            if isinstance(key, string_types):
                key = key.encode()
            if isinstance(value, string_types):
                value = value.encode()
            formated.append(b'=' + key + b'=' + value)
        for _query in self.queries:
            formated.extend(_query.get_api_format())
        if self.tag is not None:
            formated.append(b'.tag=' + self.tag)
        return formated

    def set(self, key, value):
        self.attributes[key] = value

    def filter(self, *args, **kwargs):
        for arg in args:
            if hasattr(arg, 'get_api_format'):
                self.queries.add(arg)
            else:
                self.queries.add(query.HasValueQuery(arg))

        for key, value in kwargs.items():
            self.queries.add(query.IsEqualQuery(key, value))

    def __str__(self):
        return str(b' '.join(self.get_api_format()))
