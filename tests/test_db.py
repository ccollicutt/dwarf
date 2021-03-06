#!/usr/bin/env python
#
# Copyright (c) 2014 Hewlett-Packard Development Company, L.P.
# Copyright (c) 2013 OpenStack Foundation
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or
# implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import mock
import sys
import unittest
import uuid

from copy import deepcopy

from dwarf import db as dwarf_db
from dwarf import exception

NOW = '2013-12-17 11:04:21'
UUID = '11111111-2222-3333-4444-555555555555'

FLAVOR_LIST = [
    {
        'created_at': NOW,
        'updated_at': NOW,
        'deleted_at': '',
        'deleted': '0',
        'id': '100',
        'int_id': '1',
        'name': 'standard.xsmall',
        'disk': '10',
        'ram': '512',
        'vcpus': '1',
    },
    {
        'created_at': NOW,
        'updated_at': NOW,
        'deleted_at': '',
        'deleted': '0',
        'id': '101',
        'int_id': '2',
        'name': 'standard.small',
        'disk': '30',
        'ram': '768',
        'vcpus': '1',
    },
    {
        'created_at': NOW,
        'updated_at': NOW,
        'deleted_at': '',
        'deleted': '0',
        'id': '102',
        'int_id': '3',
        'name': 'standard.medium',
        'disk': '30',
        'ram': '1024',
        'vcpus': '1',
    },
]

SERVER = {
    'name': 'My name',
    'status': 'My status',
    'image_id': 'My image',
    'flavor_id': 'My flavor',
    'key_name': 'My key',
    'mac_address': 'My mac',
    'ip': 'My ip',
}

SERVER_DETAIL = deepcopy(SERVER)
SERVER_DETAIL.update(
    {
        'created_at': NOW,
        'updated_at': NOW,
        'deleted_at': '',
        'deleted': '0',
        'int_id': '1',
        'id': UUID,
    }
)

KEYPAIR = {
    'name': 'My name',
    'fingerprint': 'My fingerprint',
    'public_key': 'My public key',
}

KEYPAIR_DETAIL = deepcopy(KEYPAIR)
KEYPAIR_DETAIL.update(
    {
        'created_at': NOW,
        'updated_at': NOW,
        'deleted_at': '',
        'deleted': '0',
        'int_id': '1',
        'id': UUID,
    }
)

IMAGE = {
    'name': 'My name',
    'disk_format': 'My disk format',
    'container_format': 'My container format',
    'size': 'My size',
    'status': 'My status',
    'is_public': 'My public',
    'location': 'My location',
    'checksum': 'My checksum',
    'min_disk': 'My disk',
    'min_ram': 'My ram',
    'owner': 'My owner',
    'protected': 'My protected',
}

IMAGE_DETAIL = deepcopy(IMAGE)
IMAGE_DETAIL.update(
    {
        'created_at': NOW,
        'updated_at': NOW,
        'deleted_at': '',
        'deleted': '0',
        'int_id': '1',
        'id': UUID,
    }
)

# For code coverage
dwarf_db._now()

# Mock methods
dwarf_db._now = mock.Mock(return_value=NOW)
uuid.uuid4 = mock.Mock(return_value=UUID)


class DbTestCase(unittest.TestCase):

    def setUp(self):
        super(DbTestCase, self).setUp()
        self.db = dwarf_db.Controller(db='test_db')
        self.db.delete()
        self.db.init()

    def tearDown(self):
        super(DbTestCase, self).setUp()
        self.db.delete()

    def test_db_init(self):
        self.assertEqual(self.db.servers.list(), [])
        self.assertEqual(self.db.keypairs.list(), [])
        self.assertEqual(self.db.images.list(), [])
        self.assertEqual(self.db.flavors.list(), FLAVOR_LIST)

    def test_db_dump(self):
        self.db.dump()
        self.db.dump(table='flavors')

    #
    # Flavor
    #

    def test_db_show_flavor(self):
        self.assertEqual(self.db.flavors.show(id='100'), FLAVOR_LIST[0])
        self.assertEqual(self.db.flavors.show(name='standard.xsmall'),
                         FLAVOR_LIST[0])
        self.assertEqual(self.db.flavors.show(id='101'), FLAVOR_LIST[1])
        self.assertEqual(self.db.flavors.show(name='standard.small'),
                         FLAVOR_LIST[1])

    def test_db_delete_flavor_by_id(self):
        self.db.flavors.delete(id='100')
        flavors = deepcopy(FLAVOR_LIST)
        del flavors[0]
        self.assertEqual(self.db.flavors.list(), flavors)

    def test_db_delete_flavor_by_name(self):
        self.db.flavors.delete(name='standard.xsmall')
        flavors = deepcopy(FLAVOR_LIST)
        del flavors[0]
        self.assertEqual(self.db.flavors.list(), flavors)

    def test_db_delete_flavor_not_found(self):
        self.assertRaises(exception.NotFound, self.db.flavors.delete,
                          id='no_such_id')

    def test_db_create_flavor_conflict(self):
        self.assertRaises(exception.Conflict, self.db.flavors.create, id='100')

    def test_db_update_flavor(self):
        flavor = self.db.flavors.update(id='100', name='new name',
                                        disk='new disk', foo='bar')
        result = deepcopy(FLAVOR_LIST[0])
        result['name'] = 'new name'
        result['disk'] = 'new disk'
        self.assertEqual(flavor, result)

    #
    # Server
    #

    def test_db_create_server(self):
        server = self.db.servers.create(**SERVER)
        self.assertEqual(server, SERVER_DETAIL)
        self.assertEqual(self.db.servers.show(name='My name'), SERVER_DETAIL)
        self.assertEqual(self.db.servers.show(ip='My ip'), SERVER_DETAIL)

    #
    # Keypair
    #

    def test_db_create_keypair(self):
        keypair = self.db.keypairs.create(**KEYPAIR)
        self.assertEqual(keypair, KEYPAIR_DETAIL)

    #
    # Image
    #

    def test_db_create_image(self):
        image = self.db.images.create(**IMAGE)
        self.assertEqual(image, IMAGE_DETAIL)

    def test_db_delete_protected_image(self):
        protected = deepcopy(IMAGE)
        protected['protected'] = 'True'
        image = self.db.images.create(**protected)
        self.assertRaises(exception.Forbidden, self.db.images.delete,
                          id=image['id'])

    #
    # Code coverage
    #

    def test_db_init_cc(self):
        self.db.init()

    def test_db_delete_cc(self):
        self.db.delete()

    def test_db_dump_cc(self):
        self.db.dump(table='no_such_table')
