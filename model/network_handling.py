from __future__ import absolute_import
from builtins import str
from builtins import range
from builtins import object
import math
from collections import OrderedDict

from qgis.core import QgsFeature, QgsGeometry, QgsVectorDataProvider, QgsProject, QgsTolerance, NULL,\
    QgsVectorLayerEditUtils, QgsFeatureRequest, QgsLineString, QgsPoint, QgsVertexId, QgsSnappingUtils,\
    QgsSnappingConfig, QgsPointXY

from .network import Junction, QJunction, Reservoir, Tank, Pipe, QPipe, Pump, Valve
# from ..tools.parameters import Parameters
from ..geo_utils import raster_utils
from ..geo_utils.points_along_line import PointsAlongLineGenerator, PointsAlongLineUtils


class NodeHandler(object):

    def __init__(self):
        pass

    @staticmethod
    def create_new_junction(params, point, eid, elev, demand, deltaz,
                            pattern_id, emitter_coeff, description, tag,
                            zone_end, pressure, pressure_units):

        junctions_caps = params.junctions_vlay.dataProvider().capabilities()
        if junctions_caps and QgsVectorDataProvider.AddFeatures:

            # New stand-alone node
            params.junctions_vlay.beginEditCommand("Add junction")

            try:
                new_junct_feat = QgsFeature(params.junctions_vlay.fields())
                new_junct_feat.setAttribute(Junction.field_name_eid, eid)
                new_junct_feat.setAttribute(Junction.field_name_elev, elev)
                new_junct_feat.setAttribute(Junction.field_name_demand, demand)
                new_junct_feat.setAttribute(QJunction.field_name_delta_z,
                                            deltaz)
                new_junct_feat.setAttribute(Junction.field_name_pattern,
                                            pattern_id)
                new_junct_feat.setAttribute(Junction.field_name_emitter_coeff,
                                            emitter_coeff)
                new_junct_feat.setAttribute(Junction.field_name_description,
                                            description)
                new_junct_feat.setAttribute(Junction.field_name_tag, tag)
                new_junct_feat.setAttribute(QJunction.field_name_zone_end,
                                            zone_end)
                new_junct_feat.setAttribute(QJunction.field_name_pressure,
                                            pressure)
                new_junct_feat.setAttribute(QJunction.field_name_pressure_units,
                                            pressure_units)

                new_junct_feat.setGeometry(QgsGeometry.fromPointXY(point))

                params.junctions_vlay.addFeatures([new_junct_feat])
                params.nodes_sindex.addFeature(new_junct_feat)

            except Exception as e:
                params.junctions_vlay.destroyEditCommand()
                raise e

            params.junctions_vlay.endEditCommand()

            return new_junct_feat

    @staticmethod
    def create_new_reservoir(params, point, eid, elev, deltaz, pressure_head, pattern_id, description, tag):

        reservoirs_caps = params.reservoirs_vlay.dataProvider().capabilities()
        if reservoirs_caps and QgsVectorDataProvider.AddFeatures:

            # New stand-alone node
            params.reservoirs_vlay.beginEditCommand("Add reservoir")

            try:
                new_reservoir_feat = QgsFeature(params.reservoirs_vlay.fields())
                new_reservoir_feat.setAttribute(Reservoir.field_name_eid, eid)
                new_reservoir_feat.setAttribute(Reservoir.field_name_elev, elev)
                new_reservoir_feat.setAttribute(Reservoir.field_name_delta_z, deltaz)
                new_reservoir_feat.setAttribute(Reservoir.field_name_pressure_head, pressure_head)
                new_reservoir_feat.setAttribute(Reservoir.field_name_pattern, pattern_id)
                new_reservoir_feat.setAttribute(Reservoir.field_name_description, description)
                new_reservoir_feat.setAttribute(Reservoir.field_name_tag, tag)

                new_reservoir_feat.setGeometry(QgsGeometry.fromPointXY(point))

                params.reservoirs_vlay.addFeatures([new_reservoir_feat])
                params.nodes_sindex.addFeature(new_reservoir_feat)

            except Exception as e:
                params.reservoirs_vlay.destroyEditCommand()
                raise e

                params.reservoirs_vlay.endEditCommand()

            return new_reservoir_feat

    @staticmethod
    def create_new_tank(params, point, eid, tank_curve_id, diameter, elev, deltaz, level_init, level_min, level_max, vol_min, description, tag):
        tanks_caps = params.tanks_vlay.dataProvider().capabilities()
        if tanks_caps and QgsVectorDataProvider.AddFeatures:

            params.tanks_vlay.beginEditCommand("Add junction")

            try:
                new_tank_feat = QgsFeature(params.tanks_vlay.fields())

                new_tank_feat.setAttribute(Tank.field_name_eid, eid)
                new_tank_feat.setAttribute(Tank.field_name_curve, tank_curve_id)
                new_tank_feat.setAttribute(Tank.field_name_diameter, diameter)
                new_tank_feat.setAttribute(Tank.field_name_elev, elev)
                new_tank_feat.setAttribute(Tank.field_name_delta_z, deltaz)
                new_tank_feat.setAttribute(Tank.field_name_level_init, level_init)
                new_tank_feat.setAttribute(Tank.field_name_level_min, level_min)
                new_tank_feat.setAttribute(Tank.field_name_level_max, level_max)
                new_tank_feat.setAttribute(Tank.field_name_vol_min, vol_min)
                new_tank_feat.setAttribute(Tank.field_name_description, description)
                new_tank_feat.setAttribute(Tank.field_name_tag, tag)

                new_tank_feat.setGeometry(QgsGeometry.fromPointXY(point))

                params.tanks_vlay.addFeatures([new_tank_feat])
                params.nodes_sindex.addFeature(new_tank_feat)

            except Exception as e:
                params.tanks_vlay.destroyEditCommand()
                raise e

                params.tanks_vlay.endEditCommand()

            return new_tank_feat

    @staticmethod
    def move_element(layer, dem_rlay, node_ft, new_pos_pt):
        caps = layer.dataProvider().capabilities()

        if caps & QgsVectorDataProvider.ChangeGeometries:

            layer.beginEditCommand('Move node')

            try:

                edit_utils = QgsVectorLayerEditUtils(layer)

                edit_utils.moveVertex(
                    new_pos_pt.x(),
                    new_pos_pt.y(),
                    node_ft.id(),
                    0)

                # Elevation
                new_elev = raster_utils.read_layer_val_from_coord(dem_rlay, new_pos_pt, 1)
                if new_elev is None:
                    new_elev = 0

                field_index = layer.dataProvider().fieldNameIndex(Junction.field_name_elev)
                layer.changeAttributeValue(node_ft.id(), field_index, new_elev)

            except Exception as e:

                layer.destroyEditCommand()
                raise e

            layer.endEditCommand()

    @staticmethod
    def _delete_feature(params, layer, feature):
        caps = layer.dataProvider().capabilities()
        if caps & QgsVectorDataProvider.DeleteFeatures:

            layer.beginEditCommand('Delete feature')

            try:
                layer.deleteFeature(feature.id())
                params.nodes_sindex.deleteFeature(feature)

            except Exception as e:
                layer.destroyEditCommand()
                raise e

            layer.endEditCommand()

    @staticmethod
    def delete_node(params, layer, node_ft, del_ad_nodes=True):

        # Delete the node
        NodeHandler._delete_feature(params, layer, node_ft)

        # Delete adjacent links
        adj_links = NetworkUtils.find_adjacent_links(params, node_ft.geometry())
        for adj_pipe in adj_links['pipes']:
            LinkHandler.delete_link(params, params.pipes_vlay, adj_pipe)


        # # The node is a junction
        # if layer == params.junctions_vlay:
        #
        #     # Delete node
        #     NodeHandler._delete_feature(params, layer, node_ft)
        #
        #     # Delete adjacent pipes
        #     if del_ad_nodes:
        #         adj_pipes = NetworkUtils.find_adjacent_links(params, node_ft.geometry())
        #         for adj_pipe in adj_pipes['pipes']:
        #             LinkHandler.delete_link(params, params.pipes_vlay, adj_pipe)
        #
        # # The node is a reservoir or a tank
        # elif layer == params.reservoirs_vlay or layer == params.tanks_vlay:
        #
        #     NodeHandler._delete_feature(params, layer, node_ft)
        #
        #     if del_ad_nodes:
        #         adj_pipes = NetworkUtils.find_adjacent_links(params, node_ft.geometry())
        #         for adj_pipe in adj_pipes['pipes']:
        #             LinkHandler.delete_link(params.pipes_vlay, adj_pipe)


class LinkHandler(object):
    def __init__(self):
        pass

    @staticmethod
    def create_new_pipe(params, eid, length_units, diameter, diameter_units, loss, roughness,
                         status, material, nodes, densify_vertices, description,
                          tag, num_edu, zone_id, velocity, velocity_units,
                           frictionloss, frictionloss_units):

        pipes_caps = params.pipes_vlay.dataProvider().capabilities()
        if pipes_caps and QgsVectorDataProvider.AddFeatures:

            pipe_geom = QgsGeometry.fromPolylineXY(nodes)

            # Densify vertices
            dists_and_points = {}
            if densify_vertices and params.vertex_dist > 0:
                points_gen = PointsAlongLineGenerator(pipe_geom)
                dists_and_points = points_gen.get_points_coords(params.vertex_dist, False)

                # Add original vertices
                for v in range(1, len(pipe_geom.asPolyline()) - 1):
                    dist = PointsAlongLineUtils.distance(pipe_geom, QgsGeometry.fromPointXY(pipe_geom.asPolyline()[v]), params.tolerance)
                    dists_and_points[dist] = pipe_geom.asPolyline()[v]

            else:
                for v in range(len(pipe_geom.asPolyline())):
                    dist = PointsAlongLineUtils.distance(pipe_geom, QgsGeometry.fromPointXY(pipe_geom.asPolyline()[v]),
                                                         params.tolerance)
                    dists_and_points[dist] = pipe_geom.asPolyline()[v]

            dists_and_points = OrderedDict(sorted(dists_and_points.items()))
            pipe_geom_2 = QgsGeometry.fromPolylineXY(list(dists_and_points.values()))
            pipe_geom_2_length = pipe_geom_2.length()

            line_coords = []
            total_dist = 0

            (start_node_ft, end_node_ft) = NetworkUtils.find_start_end_nodes(params, pipe_geom_2)
            if start_node_ft is None:
                start_node_deltaz = 0
            else:
                start_node_deltaz = float(start_node_ft.attribute(Junction.field_name_delta_z))

            if end_node_ft is None:
                end_node_deltaz = 0
            else:
                end_node_deltaz = float(end_node_ft.attribute(Junction.field_name_delta_z))

            for p in range(0, pipe_geom_2.get().vertexCount(0, 0)):

                vertex = pipe_geom_2.get().vertexAt(QgsVertexId(0, 0, p, QgsVertexId.SegmentVertex))
                if p > 0:
                    vertex_prev = pipe_geom_2.get().vertexAt(QgsVertexId(0, 0, p - 1, QgsVertexId.SegmentVertex))

                z = raster_utils.read_layer_val_from_coord(params.dem_rlay, QgsPointXY(vertex.x(), vertex.y()))
                if z is None:
                    z = 0

                # Add deltaz
                if p == 0:
                    delta_z = start_node_deltaz
                else:
                    total_dist += math.sqrt((vertex.x() - vertex_prev.x()) ** 2 + (vertex.y() - vertex_prev.y()) ** 2)
                    delta_z = (total_dist / pipe_geom_2_length * (end_node_deltaz - start_node_deltaz)) + start_node_deltaz

                line_coords.append(QgsPoint(vertex.x(), vertex.y(), z + delta_z))

            linestring = QgsLineString()
            linestring.setPoints(line_coords)

            geom_3d = QgsGeometry(linestring)

            # Calculate 3D length
            if params.dem_rlay is not None:
                length_3d = LinkHandler.calc_3d_length(params, pipe_geom_2)
            else:
                length_3d = pipe_geom_2.length()

                params.pipes_vlay.beginEditCommand("Add new pipes")
            new_pipe_ft = None

            try:
                new_pipe_ft = QgsFeature(params.pipes_vlay.fields())

                new_pipe_ft.setAttribute(Pipe.field_name_eid, eid)
                # new_pipe_ft.setAttribute(Pipe.field_name_demand, demand)
                new_pipe_ft.setAttribute(QPipe.field_name_length_units, length_units)
                new_pipe_ft.setAttribute(Pipe.field_name_diameter, diameter)
                new_pipe_ft.setAttribute(QPipe.field_name_diameter_units, diameter_units)
                new_pipe_ft.setAttribute(Pipe.field_name_length, length_3d)
                new_pipe_ft.setAttribute(Pipe.field_name_minor_loss, loss)
                new_pipe_ft.setAttribute(Pipe.field_name_roughness, roughness)
                new_pipe_ft.setAttribute(Pipe.field_name_status, status)
                new_pipe_ft.setAttribute(Pipe.field_name_material, material)
                new_pipe_ft.setAttribute(Pipe.field_name_description, description)
                new_pipe_ft.setAttribute(Pipe.field_name_tag, tag)
                new_pipe_ft.setAttribute(QPipe.field_name_num_edu, num_edu)
                new_pipe_ft.setAttribute(QPipe.field_name_zone_id, zone_id)
                new_pipe_ft.setAttribute(QPipe.field_name_velocity, velocity)
                new_pipe_ft.setAttribute(QPipe.field_name_velocity_units, velocity_units)
                new_pipe_ft.setAttribute(QPipe.field_name_frictionloss, frictionloss)
                new_pipe_ft.setAttribute(QPipe.field_name_frictionloss_units, frictionloss_units)

                new_pipe_ft.setGeometry(geom_3d)

                # Bug: newly created feature is selected (why?). Register previously created features
                sel_feats = params.pipes_vlay.selectedFeatures()

                params.pipes_vlay.addFeatures([new_pipe_ft])
                params.nodes_sindex.addFeature(new_pipe_ft)

                # Restore previously selected feature
                sel_feats_ids = []
                for sel_feat in sel_feats:
                    sel_feats_ids.append(sel_feat.id())
                params.pipes_vlay.selectByIds(sel_feats_ids)

            except Exception as e:
                params.pipes_vlay.destroyEditCommand()
                raise e

            params.pipes_vlay.endEditCommand()
            return new_pipe_ft

    @staticmethod
    def create_new_pumpvalve(params, data_dock, pipe_ft, closest_junction_ft, position, layer, attributes):

        # Find start and end nodes positions
        # Get vertex along line next to snapped point
        dist = PointsAlongLineUtils.distance(pipe_ft.geometry(), QgsGeometry.fromPointXY(position), params.tolerance)

        dist_before = dist - 0.5  # TODO: softcode based on projection units
        if dist_before <= 0:
            dist_before = 1
        dist_after = dist + 0.5  # TODO: softcode based on projection units
        if dist_after > pipe_ft.geometry().length():
            dist_after = pipe_ft.geometry().length() - 1

        if dist_before >= dist_after:
            raise PumpValveCreationException('Cannot place a pump or valve here.')

        node_before = pipe_ft.geometry().interpolate(dist_before).asPoint()
        node_after = pipe_ft.geometry().interpolate(dist_after).asPoint()

        pipes_caps = params.pipes_vlay.dataProvider().capabilities()
        junctions_caps = params.junctions_vlay.dataProvider().capabilities()
        caps = layer.dataProvider().capabilities()

        if junctions_caps:
            if closest_junction_ft is not None:
                # j_demand = closest_junction_ft.attribute(Junction.field_name_demand)
                deltaz = closest_junction_ft.attribute(Junction.field_name_delta_z)
                pattern_id = closest_junction_ft.attribute(Junction.field_name_pattern)
            else:
                # j_demand = float(data_dock.txt_junction_demand.text())
                deltaz = float(data_dock.txt_junction_deltaz.text())
                pattern = data_dock.cbo_junction_pattern.itemData(data_dock.cbo_junction_pattern.currentIndex())
                if pattern is not None:
                    pattern_id = pattern.id
                else:
                    pattern_id = None

            emitter_coeff_s = data_dock.txt_junction_emit_coeff.text()
            if emitter_coeff_s is None or emitter_coeff_s == '':
                emitter_coeff = float(0)
            else:
                emitter_coeff = float(data_dock.txt_junction_emit_coeff.text())

            # Description
            description = data_dock.txt_junction_desc.text()

            # Tag
            tag = data_dock.cbo_junction_tag.currentText()

            zone_end = 0
            pressure = 0.
            pressure_units = data_dock.cbo_rpt_units_pressure.currentText()

            junction_eid = NetworkUtils.find_next_id(params.junctions_vlay, Junction.prefix)
            elev = raster_utils.read_layer_val_from_coord(params.dem_rlay, node_before, 1)

            NodeHandler.create_new_junction(params, node_before, junction_eid, elev, 0, deltaz, pattern_id, emitter_coeff, description, tag, zone_end, pressure, pressure_units)

            junction_eid = NetworkUtils.find_next_id(params.junctions_vlay, Junction.prefix)
            elev = raster_utils.read_layer_val_from_coord(params.dem_rlay, node_after, 1)
            NodeHandler.create_new_junction(params, node_after, junction_eid, elev, 0, deltaz, pattern_id, emitter_coeff, description, tag, zone_end, pressure, pressure_units)

        # Split the pipe and create gap
        if pipes_caps:
            gap = 1  # TODO: softcode pump length
            LinkHandler.split_pipe(params, pipe_ft, position, gap)

        # Create the new link (the pump or valve)
        if caps:

            prefix = ''
            if layer == params.pumps_vlay:
                prefix = Pump.prefix
            elif layer == params.valves_vlay:
                prefix = Valve.prefix
            eid = NetworkUtils.find_next_id(layer, prefix)  # TODO: softcode

            geom = QgsGeometry.fromPolylineXY([node_before, node_after])

            layer.beginEditCommand("Add new pump/valve")

            # try:
            new_ft = QgsFeature(layer.fields())

            if layer == params.pumps_vlay:
                new_ft = QgsFeature(params.pumps_vlay.fields())
                new_ft.setAttribute(Pump.field_name_eid, eid)
                new_ft.setAttribute(Pump.field_name_param, attributes[Pump.field_name_param])
                new_ft.setAttribute(Pump.field_name_head, attributes[Pump.field_name_head])
                new_ft.setAttribute(Pump.field_name_power, attributes[Pump.field_name_power])
                new_ft.setAttribute(Pump.field_name_speed, attributes[Pump.field_name_speed])
                new_ft.setAttribute(Pump.field_name_speed_pattern, attributes[Pump.field_name_speed_pattern])
                new_ft.setAttribute(Pump.field_name_status, attributes[Pump.field_name_status])
                new_ft.setAttribute(Pump.field_name_description, attributes[Pump.field_name_description])
                new_ft.setAttribute(Pump.field_name_tag, attributes[Pump.field_name_tag])

            elif layer == params.valves_vlay:
                new_ft.setAttribute(Valve.field_name_eid, eid)
                new_ft.setAttribute(Valve.field_name_diameter, attributes[Valve.field_name_diameter])
                new_ft.setAttribute(Valve.field_name_minor_loss, attributes[Valve.field_name_minor_loss])
                new_ft.setAttribute(Valve.field_name_setting, attributes[Valve.field_name_setting])
                new_ft.setAttribute(Valve.field_name_type, attributes[Valve.field_name_type])
                new_ft.setAttribute(Valve.field_name_status, attributes[Valve.field_name_status])
                new_ft.setAttribute(Valve.field_name_description, attributes[Valve.field_name_description])
                new_ft.setAttribute(Valve.field_name_tag, attributes[Valve.field_name_tag])

            new_ft.setGeometry(geom)

            layer.addFeatures([new_ft])
            params.nodes_sindex.addFeature(new_ft)

            # except Exception as e:
            #     layer.destroyEditCommand()
            #     raise e

            layer.endEditCommand()

            return new_ft

    @staticmethod
    def split_pipe(params, pipe_ft, split_point, gap=0):

        # Get vertex along line next to snapped point
        pipe_dist, vertex_coords, next_vertex, side = pipe_ft.geometry().closestSegmentWithContext(split_point)
        a, b, c, d, vertex_dist = pipe_ft.geometry().closestVertex(split_point)

        after_add = 0
        if vertex_dist < params.tolerance:
            # It was clicked on a vertex
            after_add = 1

        # Split only if vertex is not at line ends
        # demand = pipe_ft.attribute(Pipe.field_name_demand)
        length_units = 'm' #TODO: soft code
        p_diameter = pipe_ft.attribute(Pipe.field_name_diameter)
        p_diameter_units = pipe_ft.attribute(QPipe.field_name_diameter_units)
        loss = pipe_ft.attribute(Pipe.field_name_minor_loss)
        roughness = pipe_ft.attribute(Pipe.field_name_roughness)
        status = pipe_ft.attribute(Pipe.field_name_status)
        material = pipe_ft.attribute(Pipe.field_name_material)
        pipe_desc = pipe_ft.attribute(Pipe.field_name_description)
        pipe_tag = pipe_ft.attribute(Pipe.field_name_tag)
        num_edu = pipe_ft.attribute(QPipe.field_name_num_edu)
        zone_id = pipe_ft.attribute(QPipe.field_name_zone_id)
        velocity = pipe_ft.attribute(QPipe.field_name_velocity)
        velocity_units = pipe_ft.attribute(QPipe.field_name_velocity_units)
        frictionloss_units = pipe_ft.attribute(QPipe.field_name_frictionloss_units)
        frictionloss = pipe_ft.attribute(QPipe.field_name_frictionloss)


        # Create two new linestrings
        pipes_caps = params.pipes_vlay.dataProvider().capabilities()

        dist = PointsAlongLineUtils.distance(pipe_ft.geometry(), QgsGeometry.fromPointXY(split_point), params.tolerance)
        print("dist: ", dist)
        print("gap: ", gap)
        dist_before = dist - 0.5 * gap
        if dist_before <= 0:
            dist_before = gap
        dist_after = dist + 0.5 * gap
        if dist_after > pipe_ft.geometry().length():
            dist_after = pipe_ft.geometry().length() - gap

        if dist_before > dist_after:
            raise Exception('Exception caught in splitting pipe.'
                            'Pipe is too short.')

        node_before = pipe_ft.geometry().interpolate(dist_before)
        node_after = pipe_ft.geometry().interpolate(dist_after)

        if pipes_caps:

            params.junctions_vlay.beginEditCommand("Add new node")

            try:
                nodes = pipe_ft.geometry().asPolyline()

                # First new polyline
                pl1_pts = []
                for n in range(next_vertex):
                    pl1_pts.append(QgsPointXY(nodes[n].x(), nodes[n].y()))

                pl1_pts.append(node_before.asPoint())

                pipe_eid = NetworkUtils.find_next_id(params.pipes_vlay, Pipe.prefix)
                pipe_ft_1 = LinkHandler.create_new_pipe(
                    params,
                    pipe_eid,
                    length_units,
                    p_diameter,
                    p_diameter_units,
                    loss,
                    roughness,
                    status,
                    material,
                    pl1_pts,
                    False,
                    pipe_desc,
                    pipe_tag,
                    num_edu,
                    zone_id,
                    velocity,
                    velocity_units,
                    frictionloss,
                    frictionloss_units)

                # Second new polyline
                pl2_pts = []
                pl2_pts.append(node_after.asPoint())
                for n in range(len(nodes) - next_vertex - after_add):
                    pl2_pts.append(QgsPointXY(nodes[n + next_vertex + after_add].x(), nodes[n + next_vertex + after_add].y()))

                pipe_eid = NetworkUtils.find_next_id(params.pipes_vlay, Pipe.prefix)
                pipe_ft_2 = LinkHandler.create_new_pipe(
                    params,
                    pipe_eid,
                    length_units,
                    p_diameter,
                    p_diameter_units,
                    loss,
                    roughness,
                    status,
                    material,
                    pl2_pts,
                    False,
                    pipe_desc,
                    pipe_tag,
                    num_edu,
                    zone_id,
                    velocity,
                    velocity_units,
                    frictionloss,
                    frictionloss_units)

                # Delete old pipe
                params.pipes_vlay.deleteFeature(pipe_ft.id())
                params.nodes_sindex.deleteFeature(pipe_ft)

            except Exception as e:
                params.pipes_vlay.destroyEditCommand()
                raise e

            params.pipes_vlay.endEditCommand()

            return [pipe_ft_1, pipe_ft_2]

    @staticmethod
    def move_link_vertex(params, link_lay, link_ft, new_pos_pt_v2, vertex_index):
        caps = link_lay.dataProvider().capabilities()

        if caps & QgsVectorDataProvider.ChangeGeometries:
            link_lay.beginEditCommand("Update pipes geometry")

            try:
                edit_utils = QgsVectorLayerEditUtils(link_lay)
                edit_utils.moveVertexV2(new_pos_pt_v2, link_ft.id(), vertex_index)
                # Retrieve the feature again, and update attributes

                if link_lay == params.pipes_vlay:

                    request = QgsFeatureRequest().setFilterFid(link_ft.id())
                    feats = list(link_lay.getFeatures(request))

                    field_index = link_lay.dataProvider().fieldNameIndex(Pipe.field_name_length)
                    new_3d_length = LinkHandler.calc_3d_length(params, feats[0].geometry())
                    link_lay.changeAttributeValue(link_ft.id(), field_index, new_3d_length)

            except Exception as e:
                link_lay.destroyEditCommand()
                raise e

            link_lay.endEditCommand()

    @staticmethod
    def move_pump_valve(vlay, feature, delta_vector):
        caps = vlay.dataProvider().capabilities()
        if caps and QgsVectorDataProvider.ChangeGeometries:
            vlay.beginEditCommand('Update pump/valve')
            try:

                old_ft_pts = feature.geometry().asPolyline()
                edit_utils = QgsVectorLayerEditUtils(vlay)

                edit_utils.moveVertex(
                    (QgsPoint(old_ft_pts[0].x() + delta_vector.x(), old_ft_pts[0].y() + delta_vector.y())).x(),
                    (QgsPoint(old_ft_pts[0].x() + delta_vector.x(), old_ft_pts[0].y() + delta_vector.y())).y(),
                    feature.id(),
                    0)
                # In 2.16
                # edit_utils.moveVertex(
                #     (old_ft_pts[0] + delta_vector).x(),
                #     (old_ft_pts[0] + delta_vector).y(),
                #     ft.id(),
                #     0)

                edit_utils.moveVertex(
                    (QgsPoint(old_ft_pts[1].x() + delta_vector.x(), old_ft_pts[1].y() + delta_vector.y())).x(),
                    (QgsPoint(old_ft_pts[1].x() + delta_vector.x(), old_ft_pts[1].y() + delta_vector.y())).y(),
                    feature.id(),
                    1)
                # In 2.16
                # edit_utils.moveVertex(
                #     (old_ft_pts[1] + delta_vector).x(),
                #     (old_ft_pts[1] + delta_vector).y(),
                #     ft.id(),
                #     1)

            except Exception as e:
                vlay.destroyEditCommand()
                raise e

            vlay.endEditCommand()

    @staticmethod
    def _delete_feature(params, layer, link_ft):

        caps = layer.dataProvider().capabilities()
        if caps & QgsVectorDataProvider.DeleteFeatures:

            layer.beginEditCommand('Delete feature')

            try:
                layer.deleteFeature(link_ft.id())
                params.nodes_sindex.deleteFeature(link_ft)

            except Exception as e:
                layer.destroyEditCommand()
                raise e

            layer.endEditCommand()

    @staticmethod
    def delete_link(params, layer, link_ft):

        # The link is a pipe
        if layer == params.pipes_vlay:
            LinkHandler._delete_feature(params, layer, link_ft)

        # The link is a pump or valve
        elif layer == params.pumps_vlay or layer == params.valves_vlay:

            adj_links_fts = NetworkUtils.find_adjacent_links(params, link_ft.geometry())

            if adj_links_fts['pumps']:
                adj_links_ft = adj_links_fts['pumps'][0]
            elif adj_links_fts['valves']:
                adj_links_ft = adj_links_fts['valves'][0]
            else:
                return

            adjadj_links = NetworkUtils.find_links_adjacent_to_link(params, layer,
                                                                    adj_links_ft,
                                                                    False, True, True)
            adj_nodes = NetworkUtils.find_start_end_nodes(params, adj_links_ft.geometry(),
                                                          False, True, True)

            # Stitch...
            if adj_nodes[0] is not None and adj_nodes[1] is not None:
                midpoint = NetworkUtils.find_midpoint(adj_nodes[0].geometry().asPoint(),
                                                      adj_nodes[1].geometry().asPoint())

                if len(adjadj_links['pipes']) == 2:
                    LinkHandler.stitch_pipes(
                        params,
                        adjadj_links['pipes'][0],
                        adj_nodes[0].geometry().asPoint(),
                        adjadj_links['pipes'][1],
                        adj_nodes[1].geometry().asPoint(),
                        midpoint)

            # Delete old links and pipes
            if adj_links_ft is not None:
                LinkHandler._delete_feature(params, layer, adj_links_ft)

            for adjadj_link in adjadj_links['pipes']:
                LinkHandler._delete_feature(params, params.pipes_vlay, adjadj_link)

            if adj_nodes[0] is not None:
                NodeHandler._delete_feature(params, params.junctions_vlay, adj_nodes[0])

            if adj_nodes[1] is not None:
                NodeHandler._delete_feature(params, params.junctions_vlay, adj_nodes[1])

    @staticmethod
    def delete_vertex(params, layer, pipe_ft, vertex_index):
        caps = layer.dataProvider().capabilities()

        if caps & QgsVectorDataProvider.ChangeGeometries:
            layer.beginEditCommand("Update pipe geometry")

            # try:
            edit_utils = QgsVectorLayerEditUtils(params.pipes_vlay)
            edit_utils.deleteVertex(pipe_ft.id(), vertex_index)

            # Retrieve the feature again, and update attributes
            request = QgsFeatureRequest().setFilterFid(pipe_ft.id())
            feats = list(params.pipes_vlay.getFeatures(request))

            field_index = params.pipes_vlay.dataProvider().fieldNameIndex(Pipe.field_name_length)
            new_3d_length = LinkHandler.calc_3d_length(params, feats[0].geometry())
            params.pipes_vlay.changeAttributeValue(pipe_ft.id(), field_index, new_3d_length)

            # except Exception as e:
            #     params.pipes_vlay.destroyEditCommand()
            #     raise e

            params.pipes_vlay.endEditCommand()

    @staticmethod
    def stitch_pipes(parameters, pipe1_ft, stitch_pt1, pipe2_ft, stitch_pt2, stich_pt_new):

        new_geom_pts = []

        # Add points from first adjacent link
        closest_xv1 = pipe1_ft.geometry().closestVertexWithContext(stitch_pt1)
        if closest_xv1[1] == 0:
            new_geom_pts.extend(pipe1_ft.geometry().asPolyline()[::-1])
        else:
            new_geom_pts.extend(pipe1_ft.geometry().asPolyline())

        del new_geom_pts[-1]

        new_geom_pts.append(stich_pt_new)

        # Add points from second adjacent link
        closest_xv2 = pipe2_ft.geometry().closestVertexWithContext(stitch_pt2)
        if closest_xv2[1] == 0:
            new_geom_pts.extend(pipe2_ft.geometry().asPolyline()[1:])
        else:
            new_geom_pts.extend(pipe2_ft.geometry().asPolyline()[::-1][:-1])

        eid = NetworkUtils.find_next_id(parameters.pipes_vlay, Pipe.prefix)

        # TODO: let the user set the attributes
        # demand = pipe1_ft.attribute(Pipe.field_name_demand)
        length_units = pipe1_ft.attribute(QPipe.field_name_length_units)
        diameter = pipe1_ft.attribute(Pipe.field_name_diameter)
        diameter_units = pipe1_ft.attribute(QPipe.field_name_diameter_units)
        loss = pipe1_ft.attribute(Pipe.field_name_minor_loss)
        roughness = pipe1_ft.attribute(Pipe.field_name_roughness)
        status = pipe1_ft.attribute(Pipe.field_name_status)
        material = pipe1_ft.attribute(Pipe.field_name_material)
        pipe_desc = pipe1_ft.attribute(Pipe.field_name_description)
        pipe_tag = pipe1_ft.attribute(Pipe.field_name_tag)
        zone_id = pipe1_ft.attribute(QPipe.field_name_zone_id)
        velocity = pipe1_ft.attribute(QPipe.field_name_velocity)
        velocity_units = pipe1_ft.attribute(QPipe.field_name_velocity_units)
        frictionloss = pipe1_ft.attribute(QPipe.field_name_frictionloss)
        frictionloss_units = pipe1_ft.attribute(QPipe.field_name_frictionloss_units)

        LinkHandler.create_new_pipe(parameters, eid, length_units,  diameter, diameter_units, loss, status, material, new_geom_pts, False, pipe_desc, pipe_tag, num_edu, zone_id, velocity, velocity_units, frictionloss, frictionloss_units)

    @staticmethod
    def calc_3d_length(parameters, pipe_geom):

        # Check whether start and end node exist
        (start_node_ft, end_node_ft) = NetworkUtils.find_start_end_nodes(parameters, pipe_geom)

        distance_elev_od = OrderedDict()

        # Start node
        start_add = 0
        if start_node_ft is not None:
            start_node_elev = float(start_node_ft.attribute(Junction.field_name_elev))
            if start_node_elev is None or start_node_elev == NULL:
                start_node_elev = raster_utils.read_layer_val_from_coord(parameters.dem_rlay, start_node_ft.geometry().asPoint(), 0)
                if start_node_elev is None:
                    start_node_elev = 0

            start_node_deltaz = float(start_node_ft.attribute(Junction.field_name_delta_z))
            if start_node_deltaz is None or start_node_deltaz == NULL:
                start_node_deltaz = 0
            start_add = 1

        # End node
        end_remove = 0
        if end_node_ft is not None:
            end_node_elev = float(end_node_ft.attribute(Junction.field_name_elev))
            if end_node_elev is None or end_node_elev == NULL:
                end_node_elev = raster_utils.read_layer_val_from_coord(parameters.dem_rlay, end_node_ft.geometry().asPoint(), 0)
                if end_node_elev is None:
                    end_node_elev = 0
            end_node_deltaz = float(end_node_ft.attribute(Junction.field_name_delta_z))
            if end_node_deltaz is None or end_node_deltaz == NULL:
                end_node_deltaz = 0
            end_remove = 1

        if start_node_ft is not None:
            distance_elev_od[0] = start_node_elev + start_node_deltaz

        vertices = pipe_geom.asPolyline()

        distances = [0]
        for p in range(1, len(vertices)):
            distances.append(distances[p-1] + QgsGeometry.fromPointXY(vertices[p]).distance(QgsGeometry.fromPointXY(vertices[p-1])))

        for p in range(start_add, len(vertices) - end_remove):
            elev = raster_utils.read_layer_val_from_coord(parameters.dem_rlay, vertices[p], 1)
            if elev is None:
                elev = 0
            distance_elev_od[distances[p]] = elev

        if end_node_ft is not None:
            distance_elev_od[pipe_geom.length()] = end_node_elev + end_node_deltaz

        # Calculate 3D length
        length_3d = 0
        for p in range(1, len(distance_elev_od)):
            run = list(distance_elev_od.keys())[p] - list(distance_elev_od.keys())[p-1]
            rise = list(distance_elev_od.values())[p] - list(distance_elev_od.values())[p-1]

            length_3d += math.sqrt(run**2 + rise**2)

        return length_3d


class NetworkUtils(object):
    def __init__(self):
        pass

    @staticmethod
    def find_start_end_nodes(params, link_geom, exclude_junctions=False, exclude_reservoirs=False, exclude_tanks=False):

        all_feats = []
        if not exclude_junctions:
            all_feats.extend(list(params.junctions_vlay.getFeatures()))
        if not exclude_reservoirs:
            all_feats.extend(list(params.reservoirs_vlay.getFeatures()))
        if not exclude_tanks:
            all_feats.extend(list(params.tanks_vlay.getFeatures()))

        intersecting_fts = [None, None]
        if not all_feats:
            return intersecting_fts

        cands = []
        for node_ft in all_feats:
            if not link_geom.isEmpty() and link_geom.buffer(params.tolerance, 5).boundingBox().contains(node_ft.geometry().asPoint()):
                cands.append(node_ft)

        if cands:
            for node_ft in cands:
                if node_ft.geometry().distance(QgsGeometry.fromPointXY(link_geom.asPolyline()[0])) < params.tolerance:
                    intersecting_fts[0] = node_ft
                if node_ft.geometry().distance(QgsGeometry.fromPointXY(link_geom.asPolyline()[-1])) < params.tolerance:
                    intersecting_fts[1] = node_ft

        return intersecting_fts

    @staticmethod
    def find_start_end_nodes_w_layer(params, link_geom, exclude_junctions=False, exclude_reservoirs=False, exclude_tanks=False):
        """
        This method should replace find_start_end_nodes (refactoring needed though)
        :param params:
        :param link_geom:
        :param exclude_junctions:
        :param exclude_reservoirs:
        :param exclude_tanks:
        :return:
        """

        intersecting_fts = [None, None]

        if not exclude_junctions:
            found = NetworkUtils._find_features(params, params.junctions_vlay, link_geom)
            if found[0] is not None:
                intersecting_fts[0] = found[0]
            if found[1] is not None:
                intersecting_fts[1] = found[1]
        if not exclude_reservoirs:
            found = NetworkUtils._find_features(params, params.reservoirs_vlay, link_geom)
            if found[0] is not None:
                intersecting_fts[0] = found[0]
            if found[1] is not None:
                intersecting_fts[1] = found[1]
        if not exclude_tanks:
            found = NetworkUtils._find_features(params, params.tanks_vlay, link_geom)
            if found[0] is not None:
                intersecting_fts[0] = found[0]
            if found[1] is not None:
                intersecting_fts[1] = found[1]

        return intersecting_fts

    @staticmethod
    def _find_features(params, vlay, link_geom):
        cands = []
        intersecting_fts = [None, None]
        for node_ft in vlay.getFeatures():
            if link_geom.buffer(params.tolerance, 5).boundingBox().contains(node_ft.geometry().asPoint()):
                cands.append(node_ft)
        if cands:
            for node_ft in cands:
                if node_ft.geometry().distance(QgsGeometry.fromPointXY(link_geom.asPolyline()[0])) < params.tolerance:
                    intersecting_fts[0] = (node_ft, vlay)
                if node_ft.geometry().distance(QgsGeometry.fromPointXY(link_geom.asPolyline()[-1])) < params.tolerance:
                    intersecting_fts[1] = (node_ft, vlay)

        return intersecting_fts

    @staticmethod
    def find_start_end_nodes_sindex(params, sindex, link_geom):

        # Find node FIDs that intersect the link bounding box
        bb = link_geom.boundingBox()

        # We grow slighlty the bb to prevent rounding errors: 10% of the link's length
        bb.grow(link_geom.length() * 0.1)
        cand_fids = sindex.intersects(bb)

        request = QgsFeatureRequest()
        request.setFilterFids(cand_fids)

        # Find features that intersect te link bb (from 3 possible layers)
        j_cands = params.junctions_vlay.getFeatures(request)
        r_cands = params.reservoirs_vlay.getFeatures(request)
        t_cands = params.tanks_vlay.getFeatures(request)

        intersecting_fts = [None, None]
        cands = []
        for j_cand in j_cands:
            cands.append(j_cand)
        for r_cand in r_cands:
            cands.append(r_cand)
        for t_cand in t_cands:
            cands.append(t_cand)

        # Check if any candidates are actually start or end nodes
        for node_ft in cands:
            if node_ft.geometry().distance(QgsGeometry.fromPointXY(link_geom.asPolyline()[0])) < params.tolerance:
                intersecting_fts[0] = node_ft
            if node_ft.geometry().distance(QgsGeometry.fromPointXY(link_geom.asPolyline()[-1])) < params.tolerance:
                intersecting_fts[1] = node_ft

        #check to see if both nodes are found:  (MG ADDED)
        for node_ft in intersecting_fts:
            if node_ft == None:  #if no node was found search through all features (even the ones that do not intersect)
                print("Entered New Code")
                intersecting_fts = NetworkUtils.find_start_end_nodes_w_layer(params, link_geom)

        return intersecting_fts

    @staticmethod
    def find_node_layer(params, node_geom):

        for feat in params.reservoirs_vlay.getFeatures():
            if NetworkUtils.points_overlap(node_geom, feat.geometry(), params.tolerance):
                return params.reservoirs_vlay

        for feat in params.tanks_vlay.getFeatures():
            if NetworkUtils.points_overlap(node_geom, feat.geometry(), params.tolerance):
                return params.tanks_vlay

        for feat in params.junctions_vlay.getFeatures():
            if NetworkUtils.points_overlap(node_geom, feat.geometry(), params.tolerance):
                return params.junctions_vlay

    @staticmethod
    def find_adjacent_links(params, node_geom):

        adjacent_links_d = {'pipes': [], 'pumps': [], 'valves': []}

        # Search among pipes
        adjacent_pipes_fts = []
        for pipe_ft in params.pipes_vlay.getFeatures():
            pipe_geom = pipe_ft.geometry()
            nodes = pipe_geom.asPolyline()
            if NetworkUtils.points_overlap(node_geom, QgsGeometry.fromPointXY(nodes[0]), params.tolerance) or\
                    NetworkUtils.points_overlap(node_geom, QgsGeometry.fromPointXY(nodes[len(nodes) - 1]), params.tolerance):
                adjacent_pipes_fts.append(pipe_ft)

        adjacent_links_d['pipes'] = adjacent_pipes_fts

        if len(adjacent_pipes_fts) > 2:
            # It's a pure junction, cannot be a pump or valve
            return adjacent_links_d

        # Search among pumps
        adjacent_pumps_fts = []
        for pump_ft in params.pumps_vlay.getFeatures():
            pump_geom = pump_ft.geometry()
            nodes = pump_geom.asPolyline()
            if NetworkUtils.points_overlap(node_geom, QgsGeometry.fromPointXY(nodes[0]), params.tolerance) or \
                    NetworkUtils.points_overlap(node_geom, QgsGeometry.fromPointXY(nodes[len(nodes) - 1]), params.tolerance):
                adjacent_pumps_fts.append(pump_ft)

        adjacent_links_d['pumps'] = adjacent_pumps_fts

        # Search among valves
        adjacent_valves_fts = []
        for valve_ft in params.valves_vlay.getFeatures():
            valve_geom = valve_ft.geometry()
            nodes = valve_geom.asPolyline()
            if NetworkUtils.points_overlap(node_geom, QgsGeometry.fromPointXY(nodes[0]), params.tolerance) or \
                    NetworkUtils.points_overlap(node_geom, QgsGeometry.fromPointXY(nodes[len(nodes) - 1]), params.tolerance):
                adjacent_valves_fts.append(valve_ft)

        adjacent_links_d['valves'] = adjacent_valves_fts

        return adjacent_links_d

    @staticmethod
    def find_next_id(vlay, prefix):

        features = vlay.getFeatures()
        max_eid = -1
        for feat in features:
            eid = feat.attribute(Junction.field_name_eid)

            # Check whether there's an eid using the prefix-number format
            format_used = False
            if eid.startswith(prefix):
                number = eid[len(prefix):len(eid)]
                try:
                    int(number)
                    format_used = True
                except ValueError:
                    pass

            if format_used:
                eid_val = int(eid[len(prefix):len(eid)])
            else:
                eid_val = 0
            max_eid = max(max_eid, eid_val)

        max_eid += 1
        max_eid = max(max_eid, 1)
        return prefix + str(max_eid)

    @staticmethod
    def set_up_snapper(snap_layers, map_canvas, snap_tolerance=10):

        snapper = QgsSnappingUtils()
        snapper.setMapSettings(map_canvas.mapSettings())

        config = QgsSnappingConfig(QgsProject.instance())
        config.setMode(QgsSnappingConfig.AdvancedConfiguration)
        for layer, snap_type in snap_layers.items():
            settings = QgsSnappingConfig.IndividualLayerSettings(True, snap_type, snap_tolerance, QgsTolerance.Pixels)
            config.setIndividualLayerSettings(layer, settings)

        snapper.setConfig(config)
        return snapper

    @staticmethod
    def points_overlap(point1, point2, tolerance):
        """Checks whether two points overlap. Uses tolerance."""

        if isinstance(point1, QgsPointXY):
            point1 = QgsGeometry.fromPointXY(point1)

        if isinstance(point2, QgsPointXY):
            point2 = QgsGeometry.fromPointXY(point2)

        if point1.distance(point2) < tolerance:
            return TabError
        else:
            return False

    @staticmethod
    def find_pumps_valves_junctions(params):
        """Find junctions adjacent to pumps and valves"""

        adj_points = []

        pump_fts = params.pumps_vlay.getFeatures()
        for pump_ft in pump_fts:
            (start, end) = NetworkUtils.find_start_end_nodes(pump_ft.geometry(), False, True, True)
            if start is not None:
                adj_points.append(start.geometry().asPoint())
            if end is not None:
                adj_points.append(end.geometry().asPoint())

        valve_fts = params.valves_vlay.getFeatures()
        for valve_ft in valve_fts:
            (start, end) = NetworkUtils.find_start_end_nodes(valve_ft.geometry(), False, True, True)
            if start is not None:
                adj_points.append(start.geometry().asPoint())
            if end is not None:
                adj_points.append(end.geometry().asPoint())

        return adj_points

    @staticmethod
    def find_links_adjacent_to_link(
            parameters,
            link_vlay,
            link_ft,
            exclude_pipes=False,
            exclude_pumps=False,
            exclude_valves=False):
        """Finds the links adjacent to a given link"""

        adj_links = dict()
        if not exclude_pipes:
            adj_links['pipes'] = NetworkUtils.look_for_adjacent_links(parameters, link_ft, link_vlay, parameters.pipes_vlay)
        if not exclude_pumps:
            adj_links['pumps'] = NetworkUtils.look_for_adjacent_links(parameters, link_ft, link_vlay, parameters.pumps_vlay)
        if not exclude_valves:
            adj_links['valves'] = NetworkUtils.look_for_adjacent_links(parameters, link_ft, link_vlay, parameters.valves_vlay)

        return adj_links

    @staticmethod
    def look_for_adjacent_links(params, link_ft, link_vlay, search_vlay):

        link_pts = link_ft.geometry().asPolyline()

        adj_links = []
        for ft in search_vlay.getFeatures():
            pts = ft.geometry().asPolyline()
            if NetworkUtils.points_overlap(pts[0], link_pts[0], params.tolerance) or \
                    NetworkUtils.points_overlap(pts[0], link_pts[-1], params.tolerance) or \
                    NetworkUtils.points_overlap(pts[-1], link_pts[0], params.tolerance) or \
                    NetworkUtils.points_overlap(pts[-1], link_pts[-1], params.tolerance):

                # Check that the feature found is not the same as the input
                if not (link_vlay.id() == search_vlay.id() and link_ft.id() != ft.id()):
                    adj_links.append(ft)

        return adj_links

    @staticmethod
    def find_overlapping_nodes(params, point):

        overlap_juncts = []
        overlap_reservs = []
        overlap_tanks = []

        for junct_feat in params.junctions_vlay.getFeatures():
            if NetworkUtils.points_overlap(junct_feat.geometry(), point, params.tolerance):
                overlap_juncts.append(junct_feat)
                break

        for reserv_feat in params.reservoirs_vlay.getFeatures():
            if NetworkUtils.points_overlap(reserv_feat.geometry(), point, params.tolerance):
                overlap_reservs.append(reserv_feat)
                break

        for tank_feat in params.tanks_vlay.getFeatures():
            if NetworkUtils.points_overlap(tank_feat.geometry(), point, params.tolerance):
                overlap_tanks.append(tank_feat)
                break

        return {'junctions': overlap_juncts, 'reservoirs': overlap_reservs, 'tanks': overlap_tanks }

    @staticmethod
    def find_midpoint(point1, point2):

        mid_x = (point1.x() + point2.x()) / 2
        mid_y = (point1.y() + point2.y()) / 2

        return QgsPointXY(mid_x, mid_y)


class PumpValveCreationException(Exception):
    pass
