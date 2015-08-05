#!/usr/bin/python
# -*- coding: utf-8 -*-

# Hive Camito System
# Copyright (c) 2008-2015 Hive Solutions Lda.
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

__version__ = "1.0.0"
""" The version of the module """

__revision__ = "$LastChangedRevision$"
""" The revision number of the module """

__date__ = "$LastChangedDate$"
""" The last change date of the module """

__copyright__ = "Copyright (c) 2008-2015 Hive Solutions Lda."
""" The copyright for the module """

__license__ = "GNU General Public License (GPL), Version 3"
""" The license for the module """

try: import cv2
except: cv2 = None

class Analysis(object):

    def __init__(self):
        self.camera = None
        self.previous = None
        self.win_image = "Raw Image"
        self.win_delta = "Delta Image"
        self.load()

    def load(self):
        pass

    def detect(self, image, cascade):
        rects = cascade.detectMultiScale(
            image,
            scaleFactor = 1.3,
            minNeighbors = 4,
            minSize = (30, 30),
            flags = cv2.CASCADE_SCALE_IMAGE
        )
        if len(rects) == 0: return []
        rects[:,2:] += rects[:,:2]
        return rects

    def draw_rects(self, image, rects, color):
        for x1, y1, x2, y2 in rects:
            cv2.rectangle(image, (x1, y1), (x2, y2), color, 2)

    def tick(self):
        # tries to read an image from the camera and in case
        # there's an issue with the reading breaks the cycle
        status, image = self.camera.read()
        if not status: return False

        # verifies if there's a previous image defined so that
        # we can calculate the proper delta values between images
        if not self.previous == None: delta = cv2.absdiff(
            cv2.cvtColor(self.previous, cv2.COLOR_RGB2GRAY),
            cv2.cvtColor(image, cv2.COLOR_RGB2GRAY)
        )
        else: delta = None

        # updates both of the images so that the proper contents
        # are presented to the final user
        cv2.imshow(self.win_image, image)
        if not delta == None: cv2.imshow(self.win_delta, delta)

        # updates the previous image so that the new image is set
        # as the "new" previous image (as requested)
        self.previous = image
        return True

    def start(self):
        # in case the cv library is not available must return
        # immediately in order to avoid any problems (required)
        if not cv2: return

        # retrieves the reference to the first video device
        # present in the current system, this is going to be
        # used for the capture of the image and delta calculus
        self.camera = cv2.VideoCapture(0)

        # creates both windows that are going to be used in the
        # display of the current results,
        cv2.namedWindow(self.win_image, cv2.CV_WINDOW_AUTOSIZE)
        cv2.namedWindow(self.win_delta, cv2.CV_WINDOW_AUTOSIZE)

        # sets the initial previous image as an invalid image as
        # there's no initial image when the loop starts
        self.previous = None

        # iterates continuously for the running of the main loop
        # of the current program (this is the normal behavior)
        while True:
            result = self.tick()
            if not result: break
            key = cv2.waitKey(10)
            if key == 27: break

        # destroys the currently displayed windows on the screen
        # so that they can no longer be used in the current screen
        cv2.destroyWindow(self.win_image)
        cv2.destroyWindow(self.win_delta)

if __name__ == "__main__":
    analysis = Analysis()
    analysis.start()
