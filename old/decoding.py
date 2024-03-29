#!/usr/bin/python -S
"""
decoding.py

Speed optimizations:

  Compile the schema into tag -> decoding function?
  Then just dispatch on the tag.

  Would need a benchmark to do that first.  The existing method is not too slow.

"""

__author__ = 'Andy Chu'


import struct


class Error(Exception):
  pass


class DecodeError(Error):
  pass


INT64_MAX = (1 << 63) - 1


def ZigZagDecode(value):
  """Inverse of ZigZagEncode()."""
  if not value & 0x1:
    return value >> 1
  return (value >> 1) ^ (~0)


def DecodeVarInt(s, pos):
  """Returns the decoded variable integer and the new position in buffer s."""
  i = 0
  bitpos = 0
  while True:
    byte = ord(s[pos])
    # TODO: See if removing internal variables helps
    bits = byte & 0x7F
    i |= bits << bitpos
    pos += 1
    if not byte & 0x80:  # High bit tells whether to continue
      break
    bitpos += 7
    if bitpos >= 64:  # TODO: Is this check really necessary?
      raise DecodeError('Too many bytes when decoding varint')

  return i, pos


def DecodePart(s, pos, message_type, root, indent=0):
  """Decode a byte string, using the given message type.

  Args:
    s: Byte string to decode
    pos: index to start decoding from
    message_type: A subclass of Message for decoding this level of the tree
    root: The root object, instance of message_type (TODO: simplify)
  """
  fields = message_type._fields_by_tag

  space = indent * ' '
  #print space, 'Decoding message of length %s, pos %s' % (len(s), pos)

  n = len(s)
  while pos < n:
    key, pos = DecodeVarInt(s, pos)
    tag = key >> 3
    wire_type = key & 0x07

    if wire_type == 4:  # End group
      return root, pos  # EARLY RETURN

    try:
      field = fields[tag]
    except KeyError:
      # IGNORE unknown field
      #print 'IGNORE unknown tag %s' % tag
      continue

    name = field['name']
    field_type = field['type']

    #print space, '---', 'tag:', tag, name, 'wire_type:', wire_type,
    #'field_type:', field_type

    if wire_type == 0:  # varint
      value, pos = DecodeVarInt(s, pos)

      # TODO: what to do with TYPE_SFIXED{32, 64}, they pass the tests
      #if field_type == 'TYPE_SFIXED32':
      #  value = ZigZagDecode(value)
      #if field_type == 'TYPE_SFIXED64':
      #  value = ZigZagDecode(value)
      
      if field_type == 'TYPE_ENUM':
        pass  # Do nothing; keep it an integer

      elif field_type in ('TYPE_INT32', 'TYPE_INT64'):
        # TODO: Is this right?
        if value > INT64_MAX:
          value -= (1 << 64)

      elif field_type in ('TYPE_SINT32', 'TYPE_SINT64'):
        value = ZigZagDecode(value)

      elif field_type == 'TYPE_BOOL':
        value = bool(value)

      # Must be: TYPE_UINT64, TYPE_UINT32.  Do nothing

    elif wire_type == 1:  # 64 bit
      if field_type == 'TYPE_DOUBLE':
        format = 'd'
      else:
        format = '<Q'  # little endian 64 bit

      try:
        (value,) = struct.unpack(format, s[pos : pos+8])
      except struct.error, e:
        raise DecodeError(e)
      pos += 8

    elif wire_type == 2:  # bytes

      length, pos = DecodeVarInt(s, pos)
      value = s[pos : pos+length]
      # Recursively decode the message.
      if field_type == 'TYPE_MESSAGE':
        # The name will be something like '.tutorial.Person.PhoneNumber'
        try:
          subtype = message_type.type_index[field['type_name']]
        except KeyError:
          raise DecodeError(
              "Couldn't find a type named %r" % field['type_name'])
        child = subtype()
        value, _ = DecodePart(value, 0, subtype, child, indent=indent+2)
      elif field_type == 'TYPE_STRING':
        try:
          value = unicode(value, 'utf-8')  # UTF-8 encoding
        except UnicodeDecodeError, e:
          raise DecodeError(
              "Couldn't decode string %r (position %s)" % (s[pos:pos+20], pos))
      elif field_type == 'TYPE_BYTES':
        # Leave it alone.  NOTE: When encoding as JSON, bytes are
        # base64-encoded?
        pass
      else:
        raise DecodeError('Unknown field_type %s' % field_type)

      pos += length

    elif wire_type == 3:  # Start group
      # These are deprecated in proto2, but have to support old messages.
      if field_type == 'TYPE_GROUP':
        try:
          subtype = message_type.type_index[field['type_name']]
        except KeyError:
          raise DecodeError(
              "Couldn't find a type named %r" % field['type_name'])
        child = subtype()
        # NOTE: we pass the ORIGINAL string and the current position, since we
        # don't know how long the group is.
        value, pos = DecodePart(s, pos, subtype, child, indent=indent+2)
      else:
        raise DecodeError('Unknown field_type %s' % field_type)

    elif wire_type == 5:  # 32 bit
      if field_type == 'TYPE_FLOAT':
        format = 'f'
      else:
        format = '<I'  # little endian 32 bit

      try:
        (value,) = struct.unpack(format, s[pos : pos+4])
      except struct.error, e:
        raise DecodeError(e)
      pos += 4

    else:
      raise DecodeError('Invalid wire type %s' % wire_type)

    # TODO: Instead of setattr, have a callback here

    if field['label'] == 'LABEL_REPEATED':
      oldvalue = getattr(root, name)  # Will return [] if not set yet
      oldvalue.append(value)
    else:
      setattr(root, name, value)

  return root, pos
