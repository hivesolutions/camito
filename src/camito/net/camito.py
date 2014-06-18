#!/usr/bin/python
# -*- coding: utf-8 -*-

# Hive Camito System
# Copyright (C) 2008-2014 Hive Solutions Lda.
#
# This file is part of Hive Camito System.
#
# Hive Camito System is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Hive Camito System is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Hive Camito System. If not, see <http://www.gnu.org/licenses/>.

__author__ = "João Magalhães joamag@hive.pt>"
""" The author(s) of the module """

__version__ = "1.0.0"
""" The version of the module """

__revision__ = "$LastChangedRevision$"
""" The revision number of the module """

__date__ = "$LastChangedDate$"
""" The last change date of the module """

__copyright__ = "Copyright (c) 2008-2014 Hive Solutions Lda."
""" The copyright for the module """

__license__ = "GNU General Public License (GPL), Version 3"
""" The license for the module """

import netius.clients
import netius.servers

class CamitoServer(netius.servers.MJPGServer):

    def __init__(self, *args, **kwargs):
        netius.servers.MJPGServer.__init__(self, *args, **kwargs)
        self.client = netius.clients.MJPGClient()
        self.client.bind("frame", self._on_prx_frame)
        self.client.bind("close", self._on_prx_close)
        self.client.bind("error", self._on_prx_error)

        self.container = netius.Container(*args, **kwargs)
        self.container.add_base(self)
        self.container.add_base(self.http_client)
        self.container.add_base(self.raw_client)

    def start(self):
        # starts the container this should trigger the start of the
        # event loop in the container and the proper listening of all
        # the connections in the current environment
        self.container.start(self)

    def stop(self):
        # verifies if there's a container object currently defined in
        # the object and in case it does exist propagates the stop call
        # to the container so that the proper stop operation is performed
        if not self.container: return
        self.container.stop()

    def cleanup(self):
        netius.servers.MJPGServer.cleanup(self)
        self.container = None
        self.client.destroy()

    def _on_prx_frame(self, client, _connection, data):
        print(data)

        #@todo tenho de arquivar em buffer este novo frame

    def _on_prx_close(self, client, _connection):
        pass

    def _on_prx_error(self, client, _connection):
        pass

if __name__ == "__main__":
    server = CamitoServer()
    server.serve()
