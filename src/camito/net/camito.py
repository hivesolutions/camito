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

    def transcode(self, data, size = None, quality = 100):
        import PIL.Image
        if not data: return data

        in_buffer = netius.BytesIO(data)
        out_buffer = netius.BytesIO()
        try:
            image = PIL.Image.open(in_buffer)
            if size: image = self._resize(image, size)
            image.save(
                out_buffer,
                format = "jpeg",
                quality = quality,
                optimize = True,
                progressive = True
            )
            data = out_buffer.getvalue()
        finally:
            in_buffer.close()
            out_buffer.close()

        return data

    def _resize(self, image, size):
        import PIL.Image

        # unpacks the provided tuple containing the size dimension into the
        # with and the height an in case one of these values is not defined
        # an error is raises indicating the problem
        width, height = size
        if not height and not width: raise AttributeError("invalid values")

        # retrieves the size of the loaded image and uses the values to calculate
        # the aspect ration of the provided image, this value is going to be
        # used latter for some of the resizing calculus
        image_width, image_height = image.size
        image_ratio = float(image_width) / float(image_height)

        # in case one of the size dimensions has not been specified
        # it must be calculated from the base values taking into account
        # that the aspect ration should be preserved
        if not height: height = int(image_height * width / float(image_width))
        if not width: width = int(image_width * height / float(image_height))

        # re-constructs the size tuple with the new values for the width
        # the height that have been calculated from the ratios
        size = (width, height)

        # calculates the target aspect ration for the image that is going
        # to be resized, this value is going to be used in the comparison
        # with the original image's aspect ration for determining the type
        # of image (horizontal or vertical) that we're going to resize
        size_ratio = width / float(height)

        # in case the image ratio is bigger than the size ratio this image
        # should be cropped horizontally meaning that some of the horizontal
        # image is going to disappear (horizontal cropping)
        if image_ratio > size_ratio:
            x_offset = int((image_width - size_ratio * image_height) / 2.0)
            image = image.crop((x_offset, 0, image_width - x_offset, image_height))

        # otherwise, in case the image ratio is smaller than the size ratio
        # the image is going to be cropped vertically
        elif image_ratio < size_ratio:
            y_offset = int((image_height - image_width / size_ratio) / 2.0)
            image = image.crop((0, y_offset, image_width, image_height - y_offset))

        # resizes the already cropped image into the target size using an
        # anti alias based algorithm (default expectations)
        image = image.resize(size, PIL.Image.ANTIALIAS)
        return image

class CamitoServer(netius.servers.MJPGServer):
    """
    Main class for the camito server responsible for the serving
    of proxy based mjpeg streams through a pipeline of changes
    that should be cached for performance.
    """

    def __init__(self, resources = (), *args, **kwargs):
        netius.servers.MJPGServer.__init__(self, *args, **kwargs)
        self.resources = resources
        self.cameras = dict()
        self.frames = dict()
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

    def on_send_mjpg(self, connection):
        netius.servers.MJPGServer.on_send_mjpg(self, connection)
        parser = connection.parser
        query = parser.get_query()
        params = parser._parse_query(query)
        connection.params = params

    def get_delay(self, connection):
        params = connection.params
        fps = params.get("fps", ["1"])[0]
        fps = int(fps)
        delay = 1.0 / fps
        return delay

    def get_image(self, connection):
        params = connection.params
        first = self.resources[0][0]
        camera = params.get("camera", [first])[0]
        resolution = params.get("resolution", [None])[0]
        quality = params.get("quality", ["60"])[0]
        frames = self.frames.get(camera, None)
        if not frames: return None
        if resolution:
            width, height = resolution.split("x", 1)
            size = (int(width), int(height))
        else: size = None
        quality = int(quality)
        frame = frames.peek_frame()
        frame = frames.transcode(
            frame,
            size = size,
            quality = quality
        )
        frame_l = len(frame)
        self.debug("Serving '%s' frame with %d bytes" % (camera, frame_l))
        return frame

    def _on_prx_frame(self, client, parser, data):
        connection = parser.owner
        self._store_frame(connection, data)

    def _on_prx_close(self, client, _connection):
        pass

    def _on_prx_error(self, client, _connection):
        pass

    def _boot(self):
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
    server = CamitoServer(
        resources = (
            ("cascam", "http://cascam.ou.edu/axis-cgi/mjpg/video.cgi"),
            ("iris", "http://iris.not.iac.es/axis-cgi/mjpg/video.cgi")
        )
    )
    server.serve(env = True)
