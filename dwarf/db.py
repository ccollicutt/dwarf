#!/usr/bin/python

from __future__ import print_function

import os
import sqlite3 as sq3
from time import gmtime, strftime

from dwarf import exception

from dwarf.common import config

CONFIG = config.CONFIG

_DB_COLS = ['created_at', 'updated_at', 'deleted_at', 'deleted', 'id']

DB_SERVERS_COLS = _DB_COLS + ['name', 'status', 'key']
DB_KEYPAIRS_COLS = _DB_COLS + ['name', 'fingerprint', 'public_key']
DB_IMAGES_COLS = _DB_COLS + ['name', 'disk_format', 'container_format', 'size',
                             'status', 'is_public', 'location', 'checksum',
                             'min_disk', 'min_ram', 'owner', 'protected']


def _dump_table(name):
    """
    Return all table rows
    """
    con = sq3.connect(CONFIG.dwarf_db)
    with con:
        cur = con.cursor()
        cur.execute('SELECT * FROM %s' % name)
        rows = cur.fetchall()
    return rows


def get_from_dict(keys, **kwargs):
    """
    Find key in dict and return (key, val) pair
    """
    for key in keys:
        val = kwargs.get(key, None)
        if val:
            return (key, val)


class Table(object):

    def __init__(self, table, cols, unique=None):
        self.table = table
        self.cols = cols
        self.unique = unique

    def init(self):
        """
        Initialize (create) the table
        """
        # Convert the cols array to an sqlite formatting string, i.e.,:
        # 'id TEXT, name TEXT, status TEXT, key TEXT'
        fmt = ','.join(['%s TEXT' % c for c in self.cols])

        con = sq3.connect(CONFIG.dwarf_db)
        with con:
            cur = con.cursor()
            cur.execute('CREATE TABLE %s (%s)' % (self.table, fmt))

    def dump(self):
        """
        Return all table rows
        """
        return _dump_table(self.table)

    def add(self, **kwargs):
        """
        Add a new table row
        """
        print('db.%s.add()' % self.table)

        con = sq3.connect(CONFIG.dwarf_db)
        with con:
            cur = con.cursor()

            # Check if the row exists already
            if self.unique:
                key = self.unique
                val = kwargs.get(key, None)
                if val:
                    cur.execute('SELECT * FROM %s WHERE %s=? AND deleted=?' %
                                (self.table, key), (val, 0))
                    if cur.fetchone():
                        raise exception.Failure(reason='%s %s already exists' %
                                                (self.table.rstrip('s'), val),
                                                code=400)

            # Get the highest row ID
            eid = 1
            cur.execute('SELECT max(id) FROM %s' % self.table)
            row = cur.fetchone()
            if row[0] is not None:
                eid = int(row[0]) + 1
            kwargs['id'] = eid

            # Fill in the missing row properties
            now = strftime('%Y-%m-%d %H:%M:%S', gmtime())
            kwargs['created_at'] = now
            kwargs['updated_at'] = now
            kwargs['deleted'] = 0

            # Create the array of table row values (in the right column order)
            vals = []
            for c in self.cols:
                vals.append(kwargs.get(c, ''))

            # Create the sqlite formatting string, i.e., '?,?,?,?'
            fmt = ('?,' * len(self.cols)).rstrip(',')

            # Insert the new row
            cur.execute('INSERT into %s values (%s)' % (self.table, fmt), vals)

        return self.show(id=eid)

    def delete(self, **kwargs):
        """
        Delete a table row
        """
        print('db.%s.delete()' % self.table)
        (key, val) = get_from_dict(['id', 'name'], **kwargs)

        con = sq3.connect(CONFIG.dwarf_db)
        with con:
            cur = con.cursor()

            # Check if the row exists
            cur.execute('SELECT * FROM %s WHERE %s=? AND deleted=?' %
                        (self.table, key), (val, 0))
            if not cur.fetchone():
                raise exception.Failure(reason='%s %s not found' %
                                        (self.table.rstrip('s'), val),
                                        code=404)

            # Delete the row
            now = strftime('%Y-%m-%d %H:%M:%S', gmtime())
            cur.execute('UPDATE %s SET deleted_at=?, deleted=? WHERE %s=?' %
                        (self.table, key), (now, 1, val))

    def list(self):
        """
        Get all table rows, converted to an array of dicts
        """
        print('db.%s.list()' % self.table)

        con = sq3.connect(CONFIG.dwarf_db)
        with con:
            con.row_factory = sq3.Row
            cur = con.cursor()
            cur.execute('SELECT * FROM %s WHERE deleted=?' % self.table, (0, ))
            sq3_rows = cur.fetchall()

        # Convert to an array of dicts
        rows = []
        for row in sq3_rows:
            rows.append(dict(zip(row.keys(), row)))

        return rows

    def show(self, **kwargs):
        """
        Get a single table row, converted to a dict
        """
        print('db.%s.show()' % self.table)
        (key, val) = get_from_dict(['id', 'name'], **kwargs)

        con = sq3.connect(CONFIG.dwarf_db)
        with con:
            con.row_factory = sq3.Row
            cur = con.cursor()
            cur.execute('SELECT * FROM %s WHERE %s=? AND deleted=?' %
                        (self.table, key), (val, 0))
            sq3_row = cur.fetchone()

        if not sq3_row:
            raise exception.Failure(reason='%s %s not found' %
                                    (self.table.rstrip('s'), val),
                                    code=404)

        # Convert to a dict
        return dict(zip(sq3_row.keys(), sq3_row))


class Controller(object):

    def __init__(self):
        self.servers = Table('servers', DB_SERVERS_COLS)
        self.keypairs = Table('keypairs', DB_KEYPAIRS_COLS, unique='name')
        self.images = Table('images', DB_IMAGES_COLS)

    def init(self):
        if os.path.exists(CONFIG.dwarf_db):
            print('Database exists already')
            return
        self.servers.init()
        self.keypairs.init()
        self.images.init()

    def delete(self):
        if not os.path.exists(CONFIG.dwarf_db):
            print('Database does not exist')
            return
        os.remove(CONFIG.dwarf_db)

    def dump(self, table=None):
        if not table:
            return _dump_table('sqlite_master')

        try:
            obj = getattr(self, table)
        except AttributeError:
            return 'Table %s not found' % table

        return obj.dump()
