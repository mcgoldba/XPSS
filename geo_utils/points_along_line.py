from builtins import range
from builtins import object
import math
from collections import OrderedDict
from qgis.core import QgsGeometry


class PointsAlongLineGenerator(object):

    def __init__(self, line_geom):
        self.line_geom = line_geom

    def get_points_coords(self, interval, exclude_ends=False):

        # TODO: account for start_node / end_node for direction?

        points = OrderedDict()
        length = self.line_geom.length()
        points_nr = int(math.ceil(length / interval) + 1)
        start = 0
        end = points_nr
        if exclude_ends:
            start += 1
            end -= 1
            if start < 0:
                start = 0
            if end < 1:
                end = 1
            if end > points_nr:
                end = points_nr
        for pt in range(start, end):
            position = pt * interval
            if position > length:
                position = length
            points[position] = self.line_geom.interpolate(position).asPoint()

        return points


class PointsAlongLineUtils(object):

    def __init__(self):
        pass

    @staticmethod
    def pair(line_points):
        for i in range(1, len(line_points)):
            yield line_points[i - 1], line_points[i]

    @staticmethod
    def distance(line_geom, point_geom, tolerance):
        dist_sum = 0
        for seg_start, seg_end in PointsAlongLineUtils.pair(line_geom.asPolyline()):
            if QgsGeometry.fromPolylineXY([seg_start, seg_end]).distance(point_geom) > tolerance:
                dist_sum = dist_sum + QgsGeometry.fromPolylineXY([seg_start, seg_end]).length()
            if QgsGeometry.fromPolylineXY([seg_start, seg_end]).distance(point_geom) < tolerance:
                return dist_sum + QgsGeometry.fromPolylineXY([seg_start, point_geom.asPoint()]).length()

