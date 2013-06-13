#!/usr/bin/python

from __future__ import print_function

import logging

from dwarf import db

from dwarf.common import utils

LOG = logging.getLogger(__name__)

IMAGES_INFO = ('created_at', 'id', 'is_public', 'links', 'name', 'size',
               'status', 'updated_at', 'location')


class Controller(object):

    def __init__(self):
        self.db = db.Controller()

    def list(self):
        """
        List all images
        """
        LOG.info('list()')

        images = self.db.images.list()
        return utils.sanitize(images, IMAGES_INFO)

    def show(self, image_id):
        """
        Show image details
        """
        LOG.info('show(image_id=%s)', image_id)

        image = self.db.images.show(id=image_id)
        return utils.sanitize(image, IMAGES_INFO)
