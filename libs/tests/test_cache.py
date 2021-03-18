# -*- coding: utf-8 -*-
import os
import shelve
import sys
import unittest

import fcache.cache

is_py3 = sys.version_info[0] > 2

if is_py3:
    from io import UnsupportedOperation
else:
    FileNotFoundError = IOError
    UnsupportedOperation = IOError

dirname = os.path.dirname


class TestFileCache(unittest.TestCase):

    def setUp(self):
        self.appname = 'fcache'
        self.cache = fcache.cache.FileCache(self.appname)

    def tearDown(self):
        try:
            self.cache.delete()
        except (ValueError, FileNotFoundError, OSError):
            pass

    def _turn_sync_off(self, cache):
        cache._sync = False
        cache.create()

    def _turn_sync_on(self, cache):
        cache._sync = True
        del cache._buffer

    def test_init(self):
        self.assertTrue(os.path.exists(self.cache.cache_dir))
        self.assertEqual(self.cache._flag, 'wb')
        self.assertEqual(self.cache._keyencoding, 'utf-8')
        self.assertFalse(self.cache._sync)
        self.assertEqual(self.cache._buffer, {})
        self.assertEqual(self.cache._mode, 0o666)
        self.cache.close()
        self.cache = fcache.cache.FileCache(self.appname, flag='ws')
        self.assertTrue(self.cache._sync)
        self.assertFalse(hasattr(self.cache, '_buffer'))

        # test flag validation
        self.assertRaises(TypeError, fcache.cache.FileCache, self.appname, 1)
        self.assertRaises(ValueError, fcache.cache.FileCache, self.appname,
                          'z')
        self.assertRaises(ValueError, fcache.cache.FileCache, self.appname,
                          'rz')

    def test_delete_create(self):
        self.assertTrue(os.path.exists(self.cache.cache_dir))
        self.cache.delete()
        self.assertFalse(os.path.exists(self.cache.cache_dir))
        self.assertFalse(hasattr(self.cache, '_buffer'))
        self.cache.create()
        self.assertTrue(os.path.exists(self.cache.cache_dir))
        self.assertTrue(hasattr(self.cache, '_buffer'))

    def test_clear(self):
        self.cache['foo'] = b'value'
        self.cache.sync()
        self.cache['bar'] = b'value'
        self.cache.clear()
        self.assertTrue(os.path.exists(self.cache.cache_dir))
        self.assertRaises(KeyError, self.cache.__getitem__, 'foo')
        self.assertRaises(KeyError, self.cache.__getitem__, 'bar')

    def test_sync(self):
        self.cache['foo'] = b'value'
        self.assertFalse(os.path.exists(self.cache._key_to_filename(
            self.cache._encode_key('foo'))))
        self.assertTrue(self.cache._encode_key('foo') in self.cache._buffer)
        self.cache.sync()
        self.assertTrue(os.path.exists(self.cache._key_to_filename(
            self.cache._encode_key('foo'))))
        self.assertFalse(self.cache._encode_key('foo') in self.cache._buffer)
        self.cache.clear()
        self.cache = fcache.cache.FileCache(self.appname, flag='cs')
        self.cache['foo'] = b'value'
        self.assertTrue(os.path.exists(self.cache._key_to_filename(
            self.cache._encode_key('foo'))))

    def test_close(self):
        self.cache.close()
        self.assertRaises(ValueError, self.cache.create)
        self.assertRaises(ValueError, self.cache.sync)
        self.assertRaises(ValueError, self.cache.delete)
        self.assertRaises(ValueError, self.cache.close)
        self.assertRaises(ValueError, self.cache.clear)
        self.assertRaises(ValueError, self.cache.__len__)
        self.assertRaises(ValueError, self.cache.__iter__)
        self.assertRaises(ValueError, self.cache.__contains__)
        self.assertRaises(ValueError, self.cache.__getitem__)
        self.assertRaises(ValueError, self.cache.__setitem__)
        self.assertRaises(ValueError, self.cache.__delitem__)

    def test_flag(self):
        self.cache.delete()
        self.assertRaises(FileNotFoundError, fcache.cache.FileCache,
                          self.appname, flag='r')
        self.assertRaises(FileNotFoundError, fcache.cache.FileCache,
                          self.appname, flag='w')
        self.cache = fcache.cache.FileCache(self.appname, flag='ns')
        self.assertTrue(os.path.exists(self.cache.cache_dir))
        self.cache['foo'] = b'value'
        self.cache = fcache.cache.FileCache(self.appname, flag='n')
        self.assertEqual(len(self.cache), 0)
        self.cache = fcache.cache.FileCache(self.appname, flag='rs')
        self.assertRaises(UnsupportedOperation, self.cache.__setitem__,
                          'foo', b'value')

    def test_key_encode_decode(self):
        skey = 'foo'
        skey_hex = '666f6f'
        bkey = skey.encode('utf-8')
        self.assertEqual(self.cache._encode_key(bkey), skey_hex)
        self.assertEqual(self.cache._encode_key(skey), skey_hex)
        self.assertEqual(self.cache._decode_key(skey_hex), skey)
        self.assertRaises(TypeError, self.cache._encode_key, 1)
        self.cache._serialize = False
        self.assertEqual(self.cache._decode_key(skey_hex), bkey)

    def test_unicode_key_encode_decode(self):
        ukey = u'好'
        ukey_hex = 'e5a5bd'
        bkey = ukey.encode('utf-8')
        self.assertEqual(self.cache._encode_key(ukey), ukey_hex)
        self.assertEqual(self.cache._decode_key(ukey_hex), ukey)
        self.cache._serialize = False
        self.assertEqual(self.cache._decode_key(ukey_hex), bkey)

    def test_delitem(self):
        self.cache['a'] = b'1'
        self.assertEqual(self.cache['a'], b'1')
        del self.cache['a']
        self.assertFalse('a' in self.cache)

    def test_iter(self):
        self.cache['a'] = 1
        self.cache.sync()
        keys = [k for k in self.cache.keys()]
        self.assertEqual(['a'], keys)

        self._turn_sync_on(self.cache)
        keys = [k for k in self.cache.keys()]
        self.assertEqual(['a'], keys)

    def test_contains(self):
        self.cache['a'] = 1
        self.cache.sync()
        self.assertTrue('a' in self.cache)
        self.assertFalse('b' in self.cache)

        self._turn_sync_on(self.cache)
        self.assertTrue('a' in self.cache)
        self.assertFalse('b' in self.cache)

    def test_subcache(self):
        subcache1 = fcache.cache.FileCache(self.appname + '.subcache1')
        subcache2 = fcache.cache.FileCache(self.appname +
                                           '.subcache1.subcache2')

        self.assertFalse(self.cache._is_subcache)
        self.assertTrue(subcache1._is_subcache)
        self.assertTrue(subcache2._is_subcache)
        self.assertEqual(dirname(subcache1.cache_dir),
                         dirname(dirname(subcache2.cache_dir)))
        sc1app_cache_dir = dirname(dirname(subcache1.cache_dir))
        sc2app_cache_dir = dirname(dirname(dirname(subcache2.cache_dir)))
        self.assertEqual(dirname(self.cache.cache_dir), sc1app_cache_dir)
        self.assertEqual(dirname(self.cache.cache_dir), sc2app_cache_dir)

        subcache1.delete()
        subcache2.delete()

        self.assertRaises(ValueError, fcache.cache.FileCache, 'fcache.cache')


class TestShelfCache(unittest.TestCase):

    def setUp(self):
        self.appname = 'fcache'
        self.cache = shelve.Shelf(fcache.cache.FileCache(self.appname,
                                  flag='cs', serialize=False))

    def tearDown(self):
        try:
            self.cache.dict.delete()
        except (ValueError, FileNotFoundError, OSError):
            pass

    def test_dump(self):
        self.cache['foo'] = [1, 2, 3, 4, 5]
        self.assertEqual(self.cache['foo'], [1, 2, 3, 4, 5])
        self.cache._sync = False
        self.cache._buffer = {}
        self.cache['bar'] = [1, 2, 3, 4, 5]
        self.cache.sync()
        self.assertEqual(self.cache['bar'], [1, 2, 3, 4, 5])


if __name__ == '__main__':
    unittest.main()
