# Cork - Authentication module for the Bottle web framework
# Copyright (C) 2013 Federico Ceratto and others, see AUTHORS file.
# Released under LGPLv3+ license, see LICENSE.txt

"""
.. module:: sqlalchemy_backend
   :synopsis: SQLAlchemy storage backend.
"""

import sys
from logging import getLogger

from . import base_backend

log = getLogger(__name__)
is_py3 = (sys.version_info.major == 3)

try:
    from sqlalchemy import create_engine, delete, select, \
        Column, ForeignKey, Integer, MetaData, String, Table, Unicode
    sqlalchemy_available = True
except ImportError:  # pragma: no cover
    sqlalchemy_available = False


class SqlRowProxy(dict):
    def __init__(self, sql_dict, key, *args, **kwargs):
        dict.__init__(self, *args, **kwargs)
        self.sql_dict = sql_dict
        self.key = key

    def __setitem__(self, key, value):
        dict.__setitem__(self, key, value)
        if self.sql_dict is not None:
            self.sql_dict[self.key] = {key: value}


class SqlTable(base_backend.Table):
    """Provides dictionary-like access to an SQL table."""

    def __init__(self, engine, table, key_col_name):
        self._engine = engine
        self._table = table
        self._key_col = table.c[key_col_name]

    def _row_to_value(self, row):
        row_key = row[self._key_col]
        row_value = SqlRowProxy(self, row_key,
            ((k, row[k]) for k in row.keys() if k != self._key_col.name))
        return row_key, row_value

    def __len__(self):
        query = self._table.count()
        c = self._engine.execute(query).scalar()
        return int(c)

    def __contains__(self, key):
        query = select([self._key_col], self._key_col == key)
        row = self._engine.execute(query).fetchone()
        return row is not None

    def __setitem__(self, key, value):
        if key in self:
            values = value
            query = self._table.update().where(self._key_col == key)

        else:
            values = {self._key_col.name: key}
            values.update(value)
            query = self._table.insert()

        self._engine.execute(query.values(**values))

    def __getitem__(self, key):
        query = select([self._table], self._key_col == key)
        row = self._engine.execute(query).fetchone()
        if row is None:
            raise KeyError(key)
        return self._row_to_value(row)[1]

    def __iter__(self):
        """Iterate over table index key values"""
        query = select([self._key_col])
        result = self._engine.execute(query)
        for row in result:
            key = row[0]
            yield key

    def iteritems(self):
        """Iterate over table rows"""
        query = select([self._table])
        result = self._engine.execute(query)
        for row in result:
            key = row[0]
            d = self._row_to_value(row)[1]
            yield (key, d)

    def pop(self, key):
        query = select([self._table], self._key_col == key)
        row = self._engine.execute(query).fetchone()
        if row is None:
            raise KeyError

        query = delete(self._table, self._key_col == key)
        self._engine.execute(query)
        return row

    def insert(self, d):
        query = self._table.insert(d)
        self._engine.execute(query)
        log.debug("%s inserted" % repr(d))

    def empty_table(self):
        query = self._table.delete()
        self._engine.execute(query)
        log.info("Table purged")


class SqlSingleValueTable(SqlTable):
    def __init__(self, engine, table, key_col_name, col_name):
        SqlTable.__init__(self, engine, table, key_col_name)
        self._col_name = col_name

    def _row_to_value(self, row):
        return row[self._key_col], row[self._col_name]

    def __setitem__(self, key, value):
        SqlTable.__setitem__(self, key, {self._col_name: value})



class SqlAlchemyBackend(base_backend.Backend):

    def __init__(self, db_full_url, users_tname='users', roles_tname='roles',
            pending_reg_tname='register', initialize=False):

        if not sqlalchemy_available:
            raise RuntimeError("The SQLAlchemy library is not available.")

        self._metadata = MetaData()
        if initialize:
            # Create new database if needed.
            db_url, db_name = db_full_url.rsplit('/', 1)
            if is_py3 and db_url.startswith('mysql'):
                print("WARNING: MySQL is not supported under Python3")

            self._engine = create_engine(db_url, encoding='utf-8')
            try:
                self._engine.execute("CREATE DATABASE %s" % db_name)
            except Exception as e:
                log.info("Failed DB creation: %s" % e)

            # SQLite in-memory database URL: "sqlite://:memory:"
            if db_name != ':memory:' and not db_url.startswith('postgresql'):
                self._engine.execute("USE %s" % db_name)

        else:
            self._engine = create_engine(db_full_url, encoding='utf-8')


        self._users = Table(users_tname, self._metadata,
            Column('username', Unicode(128), primary_key=True),
            Column('role', ForeignKey(roles_tname + '.role')),
            Column('hash', String(256), nullable=False),
            Column('email_addr', String(128)),
            Column('desc', String(128)),
            Column('creation_date', String(128), nullable=False),
            Column('last_login', String(128), nullable=False)

        )
        self._roles = Table(roles_tname, self._metadata,
            Column('role', String(128), primary_key=True),
            Column('level', Integer, nullable=False)
        )
        self._pending_reg = Table(pending_reg_tname, self._metadata,
            Column('code', String(128), primary_key=True),
            Column('username', Unicode(128), nullable=False),
            Column('role', ForeignKey(roles_tname + '.role')),
            Column('hash', String(256), nullable=False),
            Column('email_addr', String(128)),
            Column('desc', String(128)),
            Column('creation_date', String(128), nullable=False)
        )

        self.users = SqlTable(self._engine, self._users, 'username')
        self.roles = SqlSingleValueTable(self._engine, self._roles, 'role', 'level')
        self.pending_registrations = SqlTable(self._engine, self._pending_reg, 'code')

        if initialize:
            self._initialize_storage(db_name)
            log.debug("Tables created")


    def _initialize_storage(self, db_name):
        self._metadata.create_all(self._engine)

    def _drop_all_tables(self):
        for table in reversed(self._metadata.sorted_tables):
            log.info("Dropping table %s" % repr(table.name))
            self._engine.execute(table.delete())

    def save_users(self): pass
    def save_roles(self): pass
    def save_pending_registrations(self): pass
