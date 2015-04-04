#!/usr/bin/env python 
# -*- coding: utf-8 -*-

#-----------------------------------------------------------------------------
# Copyright (c) 2013, NeXpy Development Team.
#
# Distributed under the terms of the Modified BSD License.
#
# The full license is in the file COPYING, distributed with this software.
#-----------------------------------------------------------------------------

import logging
import os

from nexusformat.nexus import (NeXusError, NXgroup, NXfield, NXattr,
                               NXroot, NXentry, NXdata, NXparameters)
from nexusformat.pyro.ssh import NeXPyroSSH
from nexusformat.pyro.session import NeXPyroSession
from nexusformat.pyro.nxfileremote import nxloadremote

from globusonline.catalog.client.examples.catalog_wrapper import CatalogWrapper


class GlobusCatalog(object):
    """Class to interrogate Globus Catalogs
    """ 
    def __init__(self, token_file=None):

        if token_file is None:
            token_file = os.path.join(os.path.expanduser('~'),'.nexpy',
                                      'globusonline', 'gotoken.txt')                                      
        self.wrap = CatalogWrapper(token='file', token_file=token_file)
        self.catalog = None
        self.catalog_id = None
        self.dataset = None
        self.dataset_id = None
        self.member = None
        self.member_id = None
        self.ssh_session = None

    def get_catalogs(self):
        _, catalogs = self.wrap.catalogClient.get_catalogs()
        return sorted(catalogs)

    def get_catalog(self, catalog_name):
        self.catalog = catalog_name
        self.catalog_id = None
        for catalog in self.get_catalogs():
            if catalog['config']['name'] == catalog_name:
                self.catalog_id = catalog['id']
        return self.catalog_id

    def get_datasets(self, catalog_name):
        self.get_catalog(catalog_name)
        _, datasets = self.wrap.catalogClient.get_datasets(self.catalog_id)
        return sorted(datasets)

    def get_dataset(self, dataset_name):
        self.dataset = dataset_name
        self.dataset_id = None
        for dataset in self.get_datasets(self.catalog):
            if dataset['name'] == dataset_name:
                self.dataset_id = dataset['id']
        return self.dataset_id

    def get_members(self, dataset_name):
        self.get_dataset(dataset_name)
        _, members = self.wrap.catalogClient.get_members(self.catalog_id,
                                                         self.dataset_id)
        return sorted(members)

    def get_member(self, member_name):
        self.member = member_name
        self.member_id = None
        for member in self.get_members(self.dataset):
            if member['data_uri'] == member_name:
                self.member_id = member['id']
        return self.member_id

    def get_annotations_present(self):
        # Retrieve a list of annotations present on the given member
        request_string = \
 "/catalog/id=%s/dataset/id=%s/member/id=%s/annotation/annotations_present" % \
            (self.catalog_id, self.dataset_id, self.member_id)
        _, result = self.wrap.catalogClient._request('GET', request_string)
        if len(result) == 0:
            print "No annotations!"
            return None
        annotations_present = result[0]['annotations_present']
        return annotations_present

    def get_member_annotation(self, tag):
        annotations = self.get_annotations_present()
        assert annotations != None
        _, results = self.wrap.catalogClient.get_member_annotations(
            self.catalog_id, self.dataset_id, self.member_id, annotations)
        record = results[0]
        return record[tag][0]

    def load(self, user=None, port=8801):
        if user is None:
            user = os.getenv('USER')
        uri = "PYRO:%s@localhost:%i" % (user, port)
        logging.info("Pyro URI: " + uri)
        remote_path = self.get_member_annotation("path")
        logging.info("Pyro file name: " + remote_path)
        hostname = self.get_member_annotation("host")
        if self.ssh_session is None:
            self.ssh_start(user, port)
        return nxloadremote(remote_path, uri, hostname=hostname)

    def ssh_start(self, user=None, port=8801):
        if user is None:
            user = os.getenv('USER')
        logging.info("")
        hostname = self.get_member_annotation("host")
        self.ssh_session = NeXPyroSession(user, hostname, port)
        self.ssh_session.run()

    def ssh_stop(self):
        logging.info("")
        assert(self.ssh_session != None)
        self.ssh_session.terminate()
        self.ssh_session = None

    def finalize(self):
        if self.ssh_session != None:
            self.ssh_session.terminate()
