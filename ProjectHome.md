NOTE: This project is experimental and not ready for "production" use.

`pyb` is a minimal, dynamic, pure Python implementation of [Protocol Buffers](http://code.google.com/p/protobuf).

What does this mean?

  * **minimal**: Aiming for 1000-1500 total lines of code.  Less code is faster code, especially in Python.
  * **dynamic**: no code generation, no build step
  * **pure Python**: usable without compiling any dependencies; usable in restricted environments like App Engine

See [\_\_init\_\_.py](http://code.google.com/p/protobuf-pyb/source/browse/pyb/__init__.py) for some comments.

Compare [pyb's list\_people.py](http://code.google.com/p/protobuf-pyb/source/browse/pyb/examples/list_people.py) with [the official protobuf list\_people.py](http://code.google.com/p/protobuf/source/browse/trunk/examples/list_people.py).  They are quite similar.

TODO:

  * Switch to lazy decoding.  Only decode a level of the message tree when an attribute at that level has been accessed.