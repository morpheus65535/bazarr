# Cork - Authentication module for the Bottle web framework
# Copyright (C) 2013 Federico Ceratto and others, see AUTHORS file.
# Released under LGPLv3+ license, see LICENSE.txt

"""
.. module:: sqlite_backend
   :synopsis: SQLite storage backend.
"""

from . import base_backend
from logging import getLogger
log = getLogger(__name__)


class SqlRowProxy(dict):
    def __init__(self, table, key, row):
        li = ((k, v) for (k, ktype), v in zip(table._columns[1:], row[1:]))
        dict.__init__(self, li)
        self._table = table
        self._key = key

    def __setitem__(self, key, value):
        dict.__setitem__(self, key, value)
        self._table[self._key] = self


class Table(base_backend.Table):
    """Provides dictionary-like access to an SQL table."""

    def __init__(self, backend, table_name):
        self._backend = backend
        self._engine = backend.connection
        self._table_name = table_name
        self._column_names = [n for n, t in self._columns]
        self._key_col_num = 0
        self._key_col_name = self._column_names[self._key_col_num]
        self._key_col = self._column_names[self._key_col_num]

    def _row_to_value(self, key, row):
        assert isinstance(row, tuple)
        row_key = row[self._key_col_num]
        row_value = SqlRowProxy(self, key, row)
        return row_key, row_value

    def __len__(self):
        query = "SELECT count() FROM %s" % self._table_name
        ret = self._backend.run_query(query)
        return ret.fetchone()[0]

    def __contains__(self, key):
        #FIXME: count()
        query = "SELECT * FROM %s WHERE %s='%s'" % \
            (self._table_name, self._key_col, key)
        row = self._backend.fetch_one(query)
        return row is not None

    def __setitem__(self, key, value):
        """Create or update a row"""
        assert isinstance(value, dict)
        v, cn = set(value), set(self._column_names[1:])
        assert not v - cn, repr(v - cn)
        assert not cn - v, repr(cn - v)

        assert set(value) == set(self._column_names[1:]), "%s %s" % \
            (repr(set(value)), repr(set(self._column_names[1:])))

        col_values = [key] + [value[k] for k in self._column_names[1:]]

        col_names = ', '.join(self._column_names)
        question_marks = ', '.join('?' for x in col_values)
        query = "INSERT OR REPLACE INTO %s (%s) VALUES (%s)" % \
            (self._table_name, col_names, question_marks)

        ret = self._backend.run_query_using_conversion(query, col_values)


    def __getitem__(self, key):
        query = "SELECT * FROM %s WHERE %s='%s'" % \
            (self._table_name, self._key_col, key)
        row = self._backend.fetch_one(query)
        if row is None:
            raise KeyError(key)

        return self._row_to_value(key, row)[1]
        #return dict(zip(self._column_names, row))

    def __iter__(self):
        """Iterate over table index key values"""
        query = "SELECT %s FROM %s" % (self._key_col, self._table_name)
        result = self._backend.run_query(query)
        for row in result:
            yield row[0]

    def iteritems(self):
        """Iterate over table rows"""
        query = "SELECT * FROM %s" % self._table_name
        result = self._backend.run_query(query)
        for row in result:
            d = dict(zip(self._column_names, row))
            d.pop(self._key_col)

            yield (self._key_col, d)

    def pop(self, key):
        d = self.__getitem__(key)
        query = "DELETE FROM %s WHERE %s='%s'" % \
            (self._table_name, self._key_col, key)
        self._backend.fetch_one(query)
        #FIXME: check deletion
        return d

    def insert(self, d):
        raise NotImplementedError

    def empty_table(self):
        raise NotImplementedError

    def create_table(self):
        """Issue table creation"""
        cc = []
        for col_name, col_type in self._columns:
            if col_type == int:
                col_type = 'INTEGER'
            elif col_type == str:
                col_type = 'TEXT'

            if col_name == self._key_col:
                extras = 'PRIMARY KEY ASC'
            else:
                extras = ''

            cc.append("%s %s %s" % (col_name, col_type, extras))

        cc = ','.join(cc)
        query = "CREATE TABLE %s (%s)" % (self._table_name, cc)
        self._backend.run_query(query)


class SingleValueTable(Table):
    def __init__(self, *args):
        super(SingleValueTable, self).__init__(*args)
        self._value_col = self._column_names[1]

    def __setitem__(self, key, value):
        """Create or update a row"""
        assert not isinstance(value, dict)
        query = "INSERT OR REPLACE INTO %s (%s, %s) VALUES (?, ?)" % \
            (self._table_name, self._key_col, self._value_col)

        col_values = (key, value)
        ret = self._backend.run_query_using_conversion(query, col_values)

    def __getitem__(self, key):
        query = "SELECT %s FROM %s WHERE %s='%s'" % \
            (self._value_col, self._table_name, self._key_col, key)
        row = self._backend.fetch_one(query)
        if row is None:
            raise KeyError(key)

        return row[0]

class UsersTable(Table):
    def __init__(self, *args, **kwargs):
        self._columns = (
            ('username', str),
            ('role', str),
            ('hash', str),
            ('email_addr', str),
            ('desc', str),
            ('creation_date', str),
            ('last_login', str)
        )
        super(UsersTable, self).__init__(*args, **kwargs)

class RolesTable(SingleValueTable):
    def __init__(self, *args, **kwargs):
        self._columns = (
            ('role', str),
            ('level', int)
        )
        super(RolesTable, self).__init__(*args, **kwargs)

class PendingRegistrationsTable(Table):
    def __init__(self, *args, **kwargs):
        self._columns = (
            ('code', str),
            ('username', str),
            ('role', str),
            ('hash', str),
            ('email_addr', str),
            ('desc', str),
            ('creation_date', str)
        )
        super(PendingRegistrationsTable, self).__init__(*args, **kwargs)




class SQLiteBackend(base_backend.Backend):

    def __init__(self, filename, users_tname='users', roles_tname='roles',
            pending_reg_tname='register', initialize=False):

        self._filename = filename

        self.users = UsersTable(self, users_tname)
        self.roles = RolesTable(self, roles_tname)
        self.pending_registrations = PendingRegistrationsTable(self, pending_reg_tname)

        if initialize:
            self.users.create_table()
            self.roles.create_table()
            self.pending_registrations.create_table()
            log.debug("Tables created")

    @property
    def connection(self):
        try:
            return self._connection
        except AttributeError:
            import sqlite3
            self._connection = sqlite3.connect(self._filename)
            return self._connection

    def run_query(self, query):
        return self._connection.execute(query)

    def run_query_using_conversion(self, query, args):
        return self._connection.execute(query, args)

    def fetch_one(self, query):
        return self._connection.execute(query).fetchone()

    def _initialize_storage(self, db_name):
        raise NotImplementedError

    def _drop_all_tables(self):
        raise NotImplementedError

    def save_users(self): pass
    def save_roles(self): pass
    def save_pending_registrations(self): pass
