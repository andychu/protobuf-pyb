  1. Check out the source tree.
  1. simplejson must be installed.
  1. To run the tests, you also need the test framework, located at this public repository:
    1. `svn checkout http://svn.chubot.org/pan/`
  1. Set PYTHONPATH to the parent of the "trunk/pan" dir, so that "from pan.core ..." works.

I use the directory structure `hg/protobuf-pyb`, and `svn/pan`, so that `scripts/deps.{sh,bat}` works.