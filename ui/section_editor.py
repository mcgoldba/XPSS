from __future__ import absolute_import
from builtins import str
from builtins import zip
from builtins import range
from qgis.core import QgsPoint, QgsVertexId, NULL
from qgis.PyQt import QtCore
from qgis.PyQt.QtWidgets import QDialog, QVBoxLayout, QFrame, QHBoxLayout, QPushButton
from .graphs import MyMplCanvas
from ..geo_utils import bresenham, raster_utils, vector_utils
from ..model.network_handling import LinkHandler, NetworkUtils, Junction, Pipe
from matplotlib.path import Path
from matplotlib.backends.backend_qt5agg import NavigationToolbar2QT
from collections import OrderedDict
import matplotlib.patches as patches
import numpy as np
import math
import os
from .utils import set_up_button


class PipeSectionDialog(QDialog):

    def __init__(self, parent, iface, params, pipe_ft):

        QDialog.__init__(self, parent)
        main_lay = QVBoxLayout(self)

        self.parent = parent
        self.params = params
        self.pipe_ft = pipe_ft

        self.setMinimumWidth(600)
        self.setMinimumHeight(400)
        self.setWindowTitle('Pipe section editor')  # TODO: softcode
        self.setWindowModality(QtCore.Qt.ApplicationModal)

        curr_dir = os.path.dirname(os.path.abspath(__file__))

        self.fra_toolbar = QFrame(self)
        fra_toolbar_lay = QHBoxLayout(self.fra_toolbar)
        self.btn_zoom = QPushButton('Zoom')
        self.btn_zoom.clicked.connect(self.btn_zoom_clicked)
        set_up_button(self.btn_zoom, os.path.join(curr_dir, 'i_zoom.png'), True, 13, 13,
                      'Zoom')  # TODO: softcode

        self.btn_pan = QPushButton('Pan')
        self.btn_pan.clicked.connect(self.btn_pan_clicked)
        set_up_button(self.btn_pan, os.path.join(curr_dir, 'i_pan.png'), True, 15, 15,
                      'Pan')  # TODO: softcode

        self.btn_home = QPushButton('Full extent')
        self.btn_home.clicked.connect(self.btn_home_clicked)

        self.btn_back = QPushButton('Back')
        self.btn_back.clicked.connect(self.btn_back_clicked)
        set_up_button(self.btn_back, os.path.join(curr_dir, 'i_back.png'), False, 7, 13, 'Back')  # TODO: softcode

        self.btn_forth = QPushButton('Forth')
        self.btn_forth.clicked.connect(self.btn_forth_clicked)
        set_up_button(self.btn_forth, os.path.join(curr_dir, 'i_forth.png'), False, 7, 13, 'Forward')  # TODO: softcode

        self.btn_edit = QPushButton('Edit')
        self.btn_edit.clicked.connect(self.btn_edit_clicked)

        fra_toolbar_lay.addWidget(self.btn_zoom)
        fra_toolbar_lay.addWidget(self.btn_pan)
        fra_toolbar_lay.addWidget(self.btn_home)
        fra_toolbar_lay.addWidget(self.btn_back)
        fra_toolbar_lay.addWidget(self.btn_forth)
        fra_toolbar_lay.addWidget(self.btn_edit)

        # Graph canvas
        self.fra_graph = QFrame(self)
        self.static_canvas = SectionCanvas(iface, params, self)

        # Toolbar
        self.toolbar = NavigationToolbar2QT(self.static_canvas, self)
        self.toolbar.hide()

        # OK/Cancel buttons
        self.fra_buttons = QFrame(self)
        fra_buttons_lay = QHBoxLayout(self.fra_buttons)
        self.btn_Cancel = QPushButton('Cancel')
        self.btn_Ok = QPushButton('OK')
        fra_buttons_lay.addWidget(self.btn_Ok)
        fra_buttons_lay.addWidget(self.btn_Cancel)

        main_lay.addWidget(self.fra_toolbar)
        main_lay.addWidget(self.static_canvas)
        main_lay.addWidget(self.fra_buttons)

        self.setup()
        self.initialize()

    def setup(self):

        # Buttons
        self.btn_Cancel.clicked.connect(self.btn_cancel_clicked)
        self.btn_Ok.clicked.connect(self.btn_ok_clicked)

    def initialize(self):

        dem_xz = self.find_raster_distz()
        pipe_xz = self.find_line_distz()
        self.static_canvas.draw_pipe_section(dem_xz, pipe_xz)

    def btn_home_clicked(self):
        self.toolbar.home()

    def btn_zoom_clicked(self):
        self.toolbar.zoom()
        self.btn_pan.setChecked(False)

    def btn_pan_clicked(self):
        self.toolbar.pan()
        self.btn_zoom.setChecked(False)

    def btn_back_clicked(self):
        self.toolbar.back()

    def btn_forth_clicked(self):
        self.toolbar.forward()

    def btn_edit_clicked(self):
        # Deactivate tools
        if self.toolbar._active == "PAN":
            self.toolbar.pan()
        elif self.toolbar._active == "ZOOM":
            self.toolbar.zoom()

    def btn_cancel_clicked(self):
        self.setVisible(False)

    def btn_ok_clicked(self):
        new_zs = self.static_canvas.pipe_line.get_ydata()
        pipe_geom_v2 = self.pipe_ft.geometry().get()
        for p in range(pipe_geom_v2.vertexCount(0, 0)):
            vertex_id = QgsVertexId(0, 0, p, QgsVertexId.SegmentVertex)
            vertex = pipe_geom_v2.vertexAt(vertex_id)
            new_pos_pt = QgsPoint(vertex.x(), vertex.y())
            new_pos_pt.addZValue(new_zs[p])

            LinkHandler.move_link_vertex(self.params, self.params.pipes_vlay, self.pipe_ft, new_pos_pt, p)

        # Update delta z for nodes
        (start_node_ft, end_node_ft) = NetworkUtils.find_start_end_nodes(self.params, self.pipe_ft.geometry())
        start_node_elev = start_node_ft.attribute(Junction.field_name_elev)
        # end_node_deltaz = end_node_ft.attribute(Junction.field_name_delta_z)
        end_node_elev = end_node_ft.attribute(Junction.field_name_elev)

        start_node_new_deltaz = new_zs[0] - start_node_elev
        end_node_new_deltaz = new_zs[-1] - end_node_elev

        start_node_ft.setAttribute(start_node_ft.fieldNameIndex(Junction.field_name_delta_z), start_node_new_deltaz)
        end_node_ft.setAttribute(end_node_ft.fieldNameIndex(Junction.field_name_delta_z), end_node_new_deltaz)

        # Update start node elevation attribute
        start_node_lay = NetworkUtils.find_node_layer(self.params, start_node_ft.geometry())
        vector_utils.update_attribute(start_node_lay, start_node_ft, Junction.field_name_delta_z, float(start_node_new_deltaz))

        # Update end node elevation attribute
        end_node_lay = NetworkUtils.find_node_layer(self.params, end_node_ft.geometry())
        vector_utils.update_attribute(end_node_lay, end_node_ft, Junction.field_name_delta_z, float(end_node_new_deltaz))

        # Update pipe length
        # Calculate 3D length
        pipe_geom_2 = self.pipe_ft.geometry()
        if self.params.dem_rlay is not None:
            length_3d = LinkHandler.calc_3d_length(self.params, pipe_geom_2)
        else:
            length_3d = pipe_geom_2.length()
        vector_utils.update_attribute(self.params.pipes_vlay, self.pipe_ft, Pipe.field_name_length, length_3d)

        self.setVisible(False)

    def find_line_distz(self):

        # Get start and end nodes zs and deltazs from table
        pipe_geom = self.pipe_ft.geometry()
        (start_node_ft, end_node_ft) = NetworkUtils.find_start_end_nodes(self.params, self.pipe_ft.geometry())
        start_node_z = start_node_ft.attribute(Junction.field_name_elev)
        if start_node_z == NULL:
            start_node_z = 0
        start_node_deltaz = start_node_ft.attribute(Junction.field_name_delta_z)
        end_node_z = end_node_ft.attribute(Junction.field_name_elev)
        if end_node_z == NULL:
            end_node_z = 0
        end_node_deltaz = end_node_ft.attribute(Junction.field_name_delta_z)

        total_dist = 0
        dist_z = OrderedDict()
        pipe_geom_v2 = pipe_geom.get()
        dist_z[0] = start_node_z + start_node_deltaz

        # Interpolate deltaZs for remaining vertices
        for p in range(1, pipe_geom_v2.vertexCount(0, 0)):
            vertex = pipe_geom_v2.vertexAt(QgsVertexId(0, 0, p, QgsVertexId.SegmentVertex))
            vertex_prev = pipe_geom_v2.vertexAt(QgsVertexId(0, 0, p - 1, QgsVertexId.SegmentVertex))
            total_dist += math.sqrt((vertex.x() - vertex_prev.x()) ** 2 + (vertex.y() - vertex_prev.y()) ** 2)

            # Interpolate delta z for vertex using distance from nodes and delta z of nodes
            z = (total_dist / self.pipe_ft.geometry().length() * (end_node_z - start_node_z)) + start_node_z

            # z = raster_utils.read_layer_val_from_coord(self.params.dem_rlay, QgsPoint(vertex.x(), vertex.y()))
            delta_z = (total_dist / self.pipe_ft.geometry().length() * (end_node_deltaz - start_node_deltaz)) + start_node_deltaz
            dist_z[total_dist] = z + delta_z

        return dist_z

    def find_line_distz3D(self):

        pipe_geom_v2 = self.pipe_ft.geometry().get()

        # Find start and end nodes (needed to know delta z)
        (start_node_ft, end_node_ft) = NetworkUtils.find_start_end_nodes(self.params, self.pipe_ft.geometry())
        start_node_deltaz = start_node_ft.attribute(Junction.field_name_delta_z)
        end_node_deltaz = end_node_ft.attribute(Junction.field_name_delta_z)

        total_dist = 0
        dist_z = OrderedDict()
        dist_z[0] = pipe_geom_v2.vertexAt(QgsVertexId(0, 0, 0, QgsVertexId.SegmentVertex)).z() #+ start_node_deltaz

        for p in range(1, pipe_geom_v2.vertexCount(0, 0)):
            vertex = pipe_geom_v2.vertexAt(QgsVertexId(0, 0, p, QgsVertexId.SegmentVertex))
            vertex_prev = pipe_geom_v2.vertexAt(QgsVertexId(0, 0, p-1, QgsVertexId.SegmentVertex))
            total_dist += math.sqrt((vertex.x() - vertex_prev.x())**2 + (vertex.y() - vertex_prev.y())**2)

            # Interpolate delta z for vertex using distance from nodes and delta z of nodes
            delta_z = (total_dist / self.pipe_ft.geometry().length() * (end_node_deltaz - start_node_deltaz)) + start_node_deltaz
            dist_z[total_dist] = vertex.z() #+ delta_z

        return dist_z

    def find_raster_distz(self):

        dem_extent = self.params.dem_rlay.extent()
        ul_coord = QgsPoint(dem_extent.xMinimum(), dem_extent.yMaximum())
        x_cell_size = self.params.dem_rlay.rasterUnitsPerPixelX()
        y_cell_size = -self.params.dem_rlay.rasterUnitsPerPixelY()

        points = []

        pipe_pts = self.pipe_ft.geometry().asPolyline()
        for p in range(1, len(pipe_pts)):
            start_col_row = raster_utils.get_col_row(pipe_pts[p-1], ul_coord, x_cell_size, y_cell_size)
            end_col_row = raster_utils.get_col_row(pipe_pts[p], ul_coord, x_cell_size, y_cell_size)

            points.extend(bresenham.get_line((start_col_row.x, start_col_row.y), (end_col_row.x, end_col_row.y)))

        total_dist = 0
        dist_z = OrderedDict()
        dist_z[total_dist] = raster_utils.read_layer_val_from_coord(
            self.params.dem_rlay,
            raster_utils.get_coords(points[0][0], points[0][1], ul_coord, x_cell_size, y_cell_size))

        for p in range(1, len(points)):

            total_dist += math.sqrt(((points[p][0] - points[p - 1][0]) * x_cell_size) ** 2 +
                                    ((points[p][1] - points[p - 1][1]) * y_cell_size) ** 2)
            dist_z[total_dist] = raster_utils.read_layer_val_from_coord(
                self.params.dem_rlay,
                raster_utils.get_coords(points[p][0], points[p][1], ul_coord, x_cell_size, y_cell_size))

        return dist_z


class SectionCanvas(MyMplCanvas):

    showverts = True

    def __init__(self, iface, params, parent):

        super(self.__class__, self).__init__()

        self.iface = iface
        self.params = params
        self.parent = parent
        self.pipe_ft = self.parent.pipe_ft

        self._ind = 0
        self.dem_line = None
        self.pipe_patch = None
        self.pipe_line = None
        self.background = None

        self.epsilon = 10

        self.mpl_connect('draw_event', self.draw_callback)
        self.mpl_connect('button_press_event', self.button_press_callback)
        self.mpl_connect('button_release_event', self.button_release_callback)
        self.mpl_connect('motion_notify_event', self.motion_notify_callback)

    def draw_pipe_section(self, dem_xy, pipe_xy):

        self.figure.clf()
        self.axes = self.figure.add_subplot(1, 1, 1)

        # DEM line
        self.dem_line, = self.axes.plot(list(dem_xy.keys()), list(dem_xy.values()), color='brown', lw=1)

        # Pipe patch
        path, maxs = self.build_path(list(pipe_xy.keys()), list(pipe_xy.values()))
        self.pipe_patch = patches.PathPatch(path, edgecolor='b', facecolor='none')
        # self.pipe_patch.set_animated(True)

        # Pipe line
        x, y = list(zip(*self.pipe_patch.get_path().vertices))
        self.pipe_line, = self.axes.plot(x, y, color='r', lw=0.5, marker='o', markerfacecolor='r', animated=True)

        self.axes.add_line(self.dem_line)
        self.axes.add_line(self.pipe_line)
        self.axes.add_patch(self.pipe_patch)

        self.axes.set_xlim(0, maxs['x'])
        self.axes.set_ylim(0, maxs['y'])

        self.pipe_line.add_callback(self.pipe_changed)

        # self.axes.set_title('Coatuib')
        map_units = self.iface.mapCanvas().mapUnits() if self.iface is not None else '?'
        self.axes.set_xlabel('Distance [' + str(map_units) + ']')
        self.axes.set_ylabel('Elevation')
        self.axes.tick_params(axis=u'both', which=u'both', bottom=u'off', top=u'off', left=u'off', right=u'off')
        self.figure.tight_layout()
        self.draw()

    def draw_callback(self, event):
        self.background = self.copy_from_bbox(self.axes.bbox)
        self.axes.draw_artist(self.pipe_patch)
        self.axes.draw_artist(self.pipe_line)
        # self.blit(self.axes.bbox)

    def pipe_changed(self):
        vis = self.pipe_line.get_visible()
        self.Artist.update_from(self.pipe_line, self.pipe_patch)
        self.pipe_line.set_visible(vis)  # don't use the pathpatch visibility state

    def get_ind_under_point(self, event):

        # display coords
        xy = np.asarray(self.pipe_patch.get_path().vertices)
        xyt = self.pipe_patch.get_transform().transform(xy)
        xt, yt = xyt[:, 0], xyt[:, 1]
        d = np.sqrt((xt - event.x)**2 + (yt - event.y)**2)
        ind = d.argmin()

        if d[ind] >= self.epsilon:
            ind = None

        return ind

    def button_press_callback(self, event):

        if self.parent.toolbar._active is not None:
            return

        if not self.showverts:
            return
        if event.inaxes is None:
            return
        if event.button != 1 and event.button != 3:
            return
        self._ind = self.get_ind_under_point(event)

    def button_release_callback(self, event):

        if self.parent.toolbar._active is not None:
            return

        if not self.showverts:
            return
        if event.button == 2:
            return
        if event.button == 3:
            return
            #
            # if self._ind is None:
            #     # Find the distance to the closest vertex
            #     min_dist = 1E10
            #     min_pos = -1
            #     xy = np.asarray(self.pipe_patch.get_path().vertices)
            #     xyt = self.pipe_patch.get_transform().transform(xy)
            #     for v in range(1, len(xyt)):
            #         dist = utils.dist(xyt[v-1][0], xyt[v-1][1], xyt[v][0], xyt[v][1], event.x, event.y)
            #         if dist < min_dist:
            #             min_dist = dist
            #             min_pos = v
            #
            #     if min_dist <= self.epsilon:
            #         # Create new vertex
            #         xy = np.asarray((event.x, event.y))
            #         xyt = self.pipe_patch.get_transform().inverted().transform(xy)
            #         vertices = self.pipe_patch.get_path().vertices
            #         vertices = np.insert(vertices, min_pos, xyt, 0)
            #
            #         codes = []
            #         for v in range(len(vertices)):
            #             codes.append(Path.LINETO)
            #         codes[0] = Path.MOVETO
            #         path = Path(vertices, codes)
            #
            #         self.axes.patches.remove(self.pipe_patch)
            #         self.pipe_patch = patches.PathPatch(path, edgecolor='b', facecolor='none')
            #         self.axes.add_patch(self.pipe_patch)
            #
            #         self.pipe_line.set_data(zip(*vertices))
            #
            #         self.restore_region(self.background)
            #         self.axes.draw_artist(self.pipe_patch)
            #         self.axes.draw_artist(self.pipe_line)
            #         self.blit(self.axes.bbox)
            #
            # else:
            #     # Delete vertex
            #     vertices = self.pipe_patch.get_path().vertices
            #     vertices = np.delete(vertices, self._ind, axis=0)
            #     codes = []
            #     for v in range(len(vertices)):
            #         codes.append(Path.LINETO)
            #     codes[0] = Path.MOVETO
            #     path = Path(vertices, codes)
            #
            #     self.axes.patches.remove(self.pipe_patch)
            #     self.pipe_patch = patches.PathPatch(path, edgecolor='b', facecolor='none')
            #     self.axes.add_patch(self.pipe_patch)
            #
            #     self.pipe_line.set_data(zip(*vertices))
            #
            #     self.restore_region(self.background)
            #     self.axes.draw_artist(self.pipe_patch)
            #     self.axes.draw_artist(self.pipe_line)
            #     self.blit(self.axes.bbox)

        self._ind = None

    def motion_notify_callback(self, event):

        if self.parent.toolbar._active is not None:
            return

        if not self.showverts:
            return
        if self._ind is None:
            return
        if event.inaxes is None:
            return
        if event.button != 1:
            return

        vertices = self.pipe_patch.get_path().vertices
        x, y = vertices[self._ind][0], event.ydata
        if self._ind != 0 and self._ind != len(vertices) - 1:
            return

        vertices[self._ind] = x, y

        pipe_geom_v2 = self.pipe_ft.geometry().get()

        # Interpolate remaining vertices
        for v in range(1, len(vertices) - 1):
            distance = self.find_distance(self.pipe_ft.geometry().get(), v)
            vertex = pipe_geom_v2.vertexAt(QgsVertexId(0, 0, v, QgsVertexId.SegmentVertex))
            z = raster_utils.read_layer_val_from_coord(self.params.dem_rlay, QgsPoint(vertex.x(), vertex.y()))

            # Inteporlate deltaZs
            (start_node_ft, end_node_ft) = NetworkUtils.find_start_end_nodes(self.params, self.pipe_ft.geometry())
            start_node_elev = start_node_ft.attribute(Junction.field_name_elev)
            # end_node_deltaz = end_node_ft.attribute(Junction.field_name_delta_z)
            end_node_elev = end_node_ft.attribute(Junction.field_name_elev)
            start_node_deltaz = vertices[0][1] - start_node_elev
            end_node_deltaz = vertices[-1][1] - end_node_elev

            delta_z = (distance / self.pipe_ft.geometry().length() * (end_node_deltaz - start_node_deltaz)) + start_node_deltaz

            # z = (distance / self.pipe_ft.geometry().length() * (vertices[-1][1] - vertices[0][1])) + vertices[0][1]
            vertices[v] = vertices[v][0], z + delta_z

        self.pipe_line.set_data(list(zip(*vertices)))

        self.restore_region(self.background)
        self.axes.draw_artist(self.pipe_patch)
        self.axes.draw_artist(self.pipe_line)
        self.blit(self.axes.bbox)

    def build_path(self, xs, ys):

        maxs = {'x': 0, 'y': 0}
        vertices = []
        codes = []
        for v in range(len(xs)):
            vertices.append((xs[v], ys[v]))
            maxs['x'] = max(maxs['x'], xs[v])
            maxs['y'] = max(maxs['y'], ys[v])
            codes.append(Path.LINETO)
        codes[0] = Path.MOVETO

        path = Path(vertices, codes)
        return path, maxs

    def find_distance(self, pipe_geom_v2, vertex_nr):
        total_dist = 0
        for p in range(1, vertex_nr + 1):
            vertex = pipe_geom_v2.vertexAt(QgsVertexId(0, 0, p, QgsVertexId.SegmentVertex))
            vertex_prev = pipe_geom_v2.vertexAt(QgsVertexId(0, 0, p - 1, QgsVertexId.SegmentVertex))
            total_dist += math.sqrt((vertex.x() - vertex_prev.x()) ** 2 + (vertex.y() - vertex_prev.y()) ** 2)

        return total_dist
