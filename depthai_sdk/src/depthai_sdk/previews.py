import enum
import math
from functools import partial

import cv2
import numpy as np


class PreviewDecoder:
    @staticmethod
    def nn_input(packet, manager=None):
        """
        Produces NN passthough frame from raw data packet

        Args:
            packet (depthai.ImgFrame): Packet received from output queue
            manager (depthai_sdk.managers.PreviewManager, optional): PreviewManager instance

        Returns:
            numpy.ndarray: Ready to use OpenCV frame
        """
        # if manager is not None and manager.lowBandwidth: TODO change once passthrough frame type (8) is supported by VideoEncoder
        if False:
            frame = cv2.imdecode(packet.getData(), cv2.IMREAD_COLOR)
        else:
            frame = packet.getCvFrame()
        if hasattr(manager, "nn_source") and manager.nn_source in (Previews.rectified_left.name, Previews.rectified_right.name):
            frame = cv2.flip(frame, 1)
        return frame

    @staticmethod
    def color(packet, manager=None):
        """
        Produces color camera frame from raw data packet

        Args:
            packet (depthai.ImgFrame): Packet received from output queue
            manager (depthai_sdk.managers.PreviewManager, optional): PreviewManager instance

        Returns:
            numpy.ndarray: Ready to use OpenCV frame
        """
        if manager is not None and manager.lowBandwidth and not manager.sync:  # TODO remove sync check once passthrough is supported for MJPEG encoding
            return cv2.imdecode(packet.getData(), cv2.IMREAD_COLOR)
        else:
            return packet.getCvFrame()

    @staticmethod
    def left(packet, manager=None):
        """
        Produces left camera frame from raw data packet

        Args:
            packet (depthai.ImgFrame): Packet received from output queue
            manager (depthai_sdk.managers.PreviewManager, optional): PreviewManager instance

        Returns:
            numpy.ndarray: Ready to use OpenCV frame
        """
        if manager is not None and manager.lowBandwidth and not manager.sync:  # TODO remove sync check once passthrough is supported for MJPEG encoding
            return cv2.imdecode(packet.getData(), cv2.IMREAD_GRAYSCALE)
        else:
            return packet.getCvFrame()

    @staticmethod
    def right(packet, manager=None):
        """
        Produces right camera frame from raw data packet

        Args:
            packet (depthai.ImgFrame): Packet received from output queue
            manager (depthai_sdk.managers.PreviewManager, optional): PreviewManager instance

        Returns:
            numpy.ndarray: Ready to use OpenCV frame
        """
        if manager is not None and manager.lowBandwidth and not manager.sync:  # TODO remove sync check once passthrough is supported for MJPEG encoding
            return cv2.imdecode(packet.getData(), cv2.IMREAD_GRAYSCALE)
        else:
            return packet.getCvFrame()

    @staticmethod
    def rectified_left(packet, manager=None):
        """
        Produces rectified left frame (:obj:`depthai.node.StereoDepth.rectifiedLeft`) from raw data packet

        Args:
            packet (depthai.ImgFrame): Packet received from output queue
            manager (depthai_sdk.managers.PreviewManager, optional): PreviewManager instance

        Returns:
            numpy.ndarray: Ready to use OpenCV frame
        """
        if manager is not None and manager.lowBandwidth and not manager.sync:  # TODO remove sync check once passthrough is supported for MJPEG encoding
            return cv2.flip(cv2.imdecode(packet.getData(), cv2.IMREAD_GRAYSCALE), 1)
        else:
            return cv2.flip(packet.getCvFrame(), 1)

    @staticmethod
    def rectified_right(packet, manager=None):
        """
        Produces rectified right frame (:obj:`depthai.node.StereoDepth.rectifiedRight`) from raw data packet

        Args:
            packet (depthai.ImgFrame): Packet received from output queue
            manager (depthai_sdk.managers.PreviewManager, optional): PreviewManager instance

        Returns:
            numpy.ndarray: Ready to use OpenCV frame
        """
        if manager is not None and manager.lowBandwidth:  # TODO remove sync check once passthrough is supported for MJPEG encoding
            return cv2.flip(cv2.imdecode(packet.getData(), cv2.IMREAD_GRAYSCALE), 1)
        else:
            return cv2.flip(packet.getCvFrame(), 1)

    @staticmethod
    def depth_raw(packet, manager=None):
        """
        Produces raw depth frame (:obj:`depthai.node.StereoDepth.depth`) from raw data packet

        Args:
            packet (depthai.ImgFrame): Packet received from output queue
            manager (depthai_sdk.managers.PreviewManager, optional): PreviewManager instance

        Returns:
            numpy.ndarray: Ready to use OpenCV frame
        """
        # if manager is not None and manager.lowBandwidth:  TODO change once depth frame type (14) is supported by VideoEncoder
        if False:
            return cv2.imdecode(packet.getData(), cv2.IMREAD_UNCHANGED)
        else:
            return packet.getFrame()

    @staticmethod
    def depth(depth_raw, manager=None):
        """
        Produces depth frame from raw depth frame (converts to disparity and applies color map)

        Args:
            depth_raw (numpy.ndarray): OpenCV frame containing raw depth frame
            manager (depthai_sdk.managers.PreviewManager, optional): PreviewManager instance

        Returns:
            numpy.ndarray: Ready to use OpenCV frame
        """
        dispScaleFactor = getattr(manager, "dispScaleFactor", None)
        if dispScaleFactor is None:
            baseline = getattr(manager, 'baseline', 75)  # mm
            fov = getattr(manager, 'fov', 71.86)
            focal = getattr(manager, 'focal', depth_raw.shape[1] / (2. * math.tan(math.radians(fov / 2))))
            dispScaleFactor = baseline * focal
            if manager is not None:
                setattr(manager, "dispScaleFactor", dispScaleFactor)

        with np.errstate(divide='ignore'):  # Should be safe to ignore div by zero here
            disp_frame = dispScaleFactor / depth_raw
        disp_frame = (disp_frame * manager.dispMultiplier).astype(np.uint8)
        return PreviewDecoder.disparity_color(disp_frame, manager)

    @staticmethod
    def disparity(packet, manager=None):
        """
        Produces disparity frame (:obj:`depthai.node.StereoDepth.disparity`) from raw data packet

        Args:
            packet (depthai.ImgFrame): Packet received from output queue
            manager (depthai_sdk.managers.PreviewManager, optional): PreviewManager instance

        Returns:
            numpy.ndarray: Ready to use OpenCV frame
        """
        if manager is not None and manager.lowBandwidth:
            raw_frame = cv2.imdecode(packet.getData(), cv2.IMREAD_GRAYSCALE)
        else:
            raw_frame = packet.getFrame()
        return (raw_frame*(manager.dispMultiplier if manager is not None else 255/96)).astype(np.uint8)

    @staticmethod
    def disparity_color(disparity, manager=None):
        """
        Applies color map to disparity frame

        Args:
            disparity (numpy.ndarray): OpenCV frame containing disparity frame
            manager (depthai_sdk.managers.PreviewManager, optional): PreviewManager instance

        Returns:
            numpy.ndarray: Ready to use OpenCV frame
        """
        return cv2.applyColorMap(disparity, manager.colorMap if manager is not None else cv2.COLORMAP_JET)


class Previews(enum.Enum):
    """
    Enum class, assigning preview name with decode function.

    Usually used as e.g. :code:`Previews.color.name` when specifying color preview name.

    Can be also used as e.g. :code:`Previews.color.value(packet)` to transform queue output packet to color camera frame
    """
    nn_input = partial(PreviewDecoder.nn_input)
    color = partial(PreviewDecoder.color)
    left = partial(PreviewDecoder.left)
    right = partial(PreviewDecoder.right)
    rectified_left = partial(PreviewDecoder.rectified_left)
    rectified_right = partial(PreviewDecoder.rectified_right)
    depth_raw = partial(PreviewDecoder.depth_raw)
    depth = partial(PreviewDecoder.depth)
    disparity = partial(PreviewDecoder.disparity)
    disparity_color = partial(PreviewDecoder.disparity_color)


class MouseClickTracker:
    """
    Class that allows to track the click events on preview windows and show pixel value of a frame in coordinates pointed
    by the user.

    Used internally by :obj:`depthai_sdk.managers.PreviewManager`
    """

    #: dict: Stores selected point position per frame
    points = {}
    #: dict: Stores values assigned to specific point per frame
    values = {}

    def select_point(self, name):
        """
        Returns callback function for :code:`cv2.setMouseCallback` that will update the selected point on mouse click
        event from frame.

        Usually used as

        .. code-block:: python

            mct = MouseClickTracker()
            # create preview window
            cv2.setMouseCallback(window_name, mct.select_point(window_name))

        Args:
            name (str): Name of the frame

        Returns:
            Callback function for :code:`cv2.setMouseCallback`
        """
        def cb(event, x, y, flags, param):
            if event == cv2.EVENT_LBUTTONUP:
                if self.points.get(name) == (x, y):
                    del self.points[name]
                    if name in self.values:
                        del self.values[name]
                else:
                    self.points[name] = (x, y)
        return cb

    def extract_value(self, name, frame: np.ndarray):
        """
        Extracts value from frame for a specific point

        Args:
            name (str): Name of the frame
        """
        point = self.points.get(name, None)
        if point is not None:
            if name in (Previews.depth_raw.name, Previews.depth.name):
                self.values[name] = "{}mm".format(frame[point[1]][point[0]])
            elif name in (Previews.disparity_color.name, Previews.disparity.name):
                self.values[name] = "{}px".format(frame[point[1]][point[0]])
            elif len(frame.shape) == 3:
                self.values[name] = "R:{},G:{},B:{}".format(*frame[point[1]][point[0]][::-1])
            elif len(frame.shape) == 2:
                self.values[name] = "Gray:{}".format(frame[point[1]][point[0]])
            else:
                self.values[name] = str(frame[point[1]][point[0]])