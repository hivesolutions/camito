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

class FrameBuffer(list):
    """
    Buffer class meant to be used in the storage of frames
    for buffering purposes, should be able to keep cache of
    a certain amount of frames for latter "peeking".
    """

    def __init__(self, max = 60, *args, **kwargs):
        list.__init__(self, *args, **kwargs)
        self.max = max
        self.index = -1
        for _index in range(self.max): self.append(None)

    def peek_frame(self):
        if self.index == -1: return None
        return self[self.index]

    def put_frame(self, data):
        self.next()
        self[self.index] = data

    def next(self):
        is_limit = self.index == self.max - 1
        if is_limit: self.index = 0
        else: self.index += 1
        return self.index

class CamitoServer(netius.servers.MJPGServer):

    def __init__(self, *args, **kwargs):
        netius.servers.MJPGServer.__init__(self, *args, **kwargs)
        self.client = netius.clients.MJPGClient(
            thread = False,
            auto_release = False
        )
        self.client.bind("frame", self._on_prx_frame)
        self.client.bind("close", self._on_prx_close)
        self.client.bind("error", self._on_prx_error)

        self.container = netius.Container(*args, **kwargs)
        self.container.add_base(self)
        self.container.add_base(self.client)

        self.cameras = dict()
        self.frames = dict()

    def start(self):
        self._boot()

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

    def get_image(self, connection):
        parser = connection.parser
        query = parser.get_query()
        params = parser._parse_query(query)
        camera = params.get("camera") or ["af1"]
        camera = camera[0]
        frames = self.frames.get(camera, None)
        if not frames: return None
        return frames.peek_frame()

    def _on_prx_frame(self, client, parser, data):
        connection = parser.owner
        self._store_frame(connection, data)

    def _on_prx_close(self, client, _connection):
        pass

    def _on_prx_error(self, client, _connection):
        pass

    def _boot(self):
        #@todo: comment and structure this
        self.resources = (
            ("cascam", "http://cascam.ou.edu/axis-cgi/mjpg/video.cgi?resolution=320x240"),
            ("af1", "http://root:hbw7qYoZ@lugardajoiafa.dyndns.org:7000/axis-cgi/mjpg/video.cgi?camera=1&resolution=640x480&compression=30&fps=4&clock=None")
        )
        for info in self.resources:
            name, url = info
            connection = self.client.get(url)
            self.cameras[name] = connection
            self.cameras[url] = connection
            self.cameras[connection] = info

    def _store_frame(self, connection, data):
        info = self.cameras.get(connection, None)
        if not info: return

        name, _url = info
        buffer = self.frames.get(name, FrameBuffer())
        buffer.put_frame(data)
        self.frames[name] = buffer

if __name__ == "__main__":
    server = CamitoServer()
    server.serve(env = True)
