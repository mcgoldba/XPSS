from __future__ import absolute_import
# Modified from https://plugins.qgis.org/plugins/ImportEpanetInpFiles/
# (C)Marios Kyriakou 2016
# University of Cyprus, KIOS Research Center for Intelligent Systems and Networks

from builtins import str
from builtins import range
from builtins import object
from collections import OrderedDict
from qgis.core import QgsFeature, QgsGeometry, NULL, QgsPoint, QgsPointXY, QgsLineString
from .network import Junction, Reservoir, Tank, Pipe, Pump, Valve, QJunction, QReservoir, QTank, QPipe, QVertices

# import readEpanetFile as ref
from . import read_epanet_file
import os
from .inp_writer import InpFile
from ..tools.data_stores import MemoryDS
from .options_report import Options, Unbalanced, Quality, Report, Hour, Times
from .system_ops import Rule
import codecs
import re


class InpReader(object):

    def __init__(self, inp_path):
        self.params = None
        self.inp_path = inp_path

        with codecs.open(self.inp_path, 'r', encoding='UTF-8') as inp_f:
            self.lines = inp_f.read().splitlines()

    def read(self, params):

        self.inp_path = self.inp_path
        self.params = params

        statinfo = os.stat(self.inp_path)
        file_size = statinfo.st_size
        if file_size == 0:
            return None

        ref = read_epanet_file.InpReader(self.inp_path)

        # ref.LoadFile(self.inp_path)
        # ref.BinUpdateClass()
        links_count = ref.getBinLinkCount()

        # Get all Sections
        mixing = ref.getMixingSection()
        reactions = ref.getReactionsSection()
        sources = ref.getSourcesSection()
        rules = ref.getRulesSection()
        quality = ref.getQualitySection()
        curves = ref.getCurvesSection()
        patterns = ref.getPatternsSection()
        controls = ref.getControlsSection()
        emitters = ref.getEmittersSection()
        emitters_d = {}
        for emitter in emitters:
            emitters_d[emitter[0]] = emitter[1]

        status = ref.getStatusSection()
        demands = ref.getDemandsSection()
        energy = ref.getEnergySection()
        opt_reactions = ref.getReactionsOptionsSection()
        times = ref.getTimesSection()
        report = ref.getReportSection()
        options = ref.getOptionsSection()
        tags = ref.get_tags()
        tags_d = {}

        # Check for QEPANET section in inp file. If it's there, update layer attributes
        qepanet_junctions_elevcorr_od, qepanet_junctions_zone_end_od, \
            qepanet_junctions_pressure_od, qepanet_junctions_pressure_units_od = \
            self.read_qepanet_junctions()
        qepanet_tanks_od = self.read_qepanet_tanks()
        (qepanet_reservoirs_deltaz_od, qepanet_reservoirs_press_head_od) = self.read_qepanet_reservoirs()
        (qepanet_pipes_material_od, qepanet_pipes_edu_od,
         qepanet_pipes_zone_id_od, qepanet_pipes_velocity_od,
          qepanet_pipes_frictionloss_od, qepanet_pipes_length_units_od,
          qepanet_pipes_diameter_units_od, qepanet_pipes_velocity_units_od,
          qepanet_pipes_frictionloss_units_od) = self.read_qepanet_pipes()
        qepanet_vertices_od = self.read_qepanet_vertices()

        # Create layers and update
        if mixing:
            self.update_mixing(mixing)
        if reactions:
            self.update_reactions(reactions)
        if sources:
            self.update_sources(sources)
        if rules:
            self.update_rules(rules)
        if quality:
            self.update_quality(quality)
        if controls:
            self.update_controls(controls)
        if demands:
            self.update_demands(demands)
        if energy:
            self.update_energy(energy)
        if opt_reactions:
            self.update_opt_reactions(opt_reactions)
        if times:
            self.update_times(times)
        if report:
            self.update_report(report)
        if options:
            self.update_options(options)

        # Get all Section lengths
        all_sections = [len(energy), len(opt_reactions), len(demands), len(status), len(emitters), len(controls),
                        len(patterns),
                        len(curves[0]), len(quality), len(rules), len(sources), len(reactions), len(mixing), len(times),
                        len(report),
                        len(options), ref.getBinNodeCount(), ref.getBinLinkCount()]
        ss = max(all_sections)

        if tags:
            for tag in tags:
                tags_d[tag.element_id] = tag.tag
            self.params.tag_names = set(tags_d.values())

        xy = ref.getBinNodeCoordinates()

        x = xy[0]
        y = xy[1]
        vertx = xy[2]
        verty = xy[3]
        vertxyFinal = []
        for i in range(len(vertx)):
            vertxy = []
            for u in range(len(vertx[i])):
                vertxy.append([float(vertx[i][u]), float(verty[i][u])])
            if vertxy != []:
                vertxyFinal.append(vertxy)

        # Get data of Junctions
        ndEle = ref.getBinNodeJunctionElevations()
        ndBaseD = ref.getBinNodeBaseDemands()

        ndID = ref.getBinNodeNameID()
        nodes_desc = ref.get_nodes_desc()

        ndPatID = ref.getBinNodeDemandPatternID()

        junctions_lay = None
        if ref.getBinNodeJunctionCount() > 0:

            junctions_lay = MemoryDS.create_junctions_lay(crs=params.crs)
            junctions_lay_dp = junctions_lay.dataProvider()

        # Get data of Pipes
        pipes_lay = None
        pumps_lay = None
        valves_lay = None

        if links_count > 0:

            # Pipes
            pipes_lay = MemoryDS.create_pipes_lay(crs=params.crs)
            pipes_lay_dp = pipes_lay.dataProvider()

            # Pumps
            pumps_lay = MemoryDS.create_pumps_lay(crs=params.crs)
            pumps_lay_dp = pumps_lay.dataProvider()

            # Valves
            valves_lay = MemoryDS.create_valves_lay(crs=params.crs)
            valves_lay_dp = valves_lay.dataProvider()

            pump_index = ref.getBinLinkPumpIndex()
            valve_index = ref.getBinLinkValveIndex()
            ndlConn = ref.getBinNodesConnectingLinksID()
            x1 = []
            x2 = []
            y1 = []
            y2 = []
            stat = ref.getBinLinkInitialStatus()

            kk = 0
            ch = 0
            linkID = ref.getBinLinkNameID()
            link_descs = ref.get_links_desc()
            linkLengths = ref.getBinLinkLength()
            linkDiameters = ref.getBinLinkDiameter()
            linkRough = ref.getBinLinkRoughnessCoeff()
            linkMinorloss = ref.getBinLinkMinorLossCoeff()

        # Write Tank Shapefile and get tank data
        tanks_lay = None
        if ref.getBinNodeTankCount() > 0:
            tanks_lay = MemoryDS.create_tanks_lay(crs=params.crs)
            tanks_lay_dp = tanks_lay.dataProvider()

            ndTankelevation = ref.getBinNodeTankElevations()
            initiallev = ref.getBinNodeTankInitialLevel()
            minimumlev = ref.getBinNodeTankMinimumWaterLevel()
            maximumlev = ref.getBinNodeTankMaximumWaterLevel()
            diameter = ref.getBinNodeTankDiameter()
            minimumvol = ref.getBinNodeTankMinimumWaterVolume()
            volumecurv = ref.getBinNodeTankVolumeCurveID()
            ndTankID = ref.getBinNodeTankNameID()

        reservoirs_lay = None
        if ref.getBinNodeReservoirCount() > 0:
            reservoirs_lay = MemoryDS.create_reservoirs_lay(crs=params.crs)
            reservoirs_lay_dp = reservoirs_lay.dataProvider()

            reservoirs_elev = ref.getBinNodeReservoirElevations()
            # posReservoirs.startEditing()

        vvLink = 68
        bbLink = 1

        vPos = 0
        pPos = 0
        pPosPower = 0
        pPosHead = 0
        pPosSpeed = 0
        pPosSpeedPattern = 0

        for i in range(ss):
            if i == ss / vvLink and vvLink > -1:
                vvLink = vvLink - 1
                bbLink = bbLink + 1

            if i < ref.getBinNodeJunctionCount():
                featJ = QgsFeature()
                point = QgsPointXY(float(x[i]), float(y[i]))

                delta_z = 0
                if qepanet_junctions_elevcorr_od:
                    delta_z = float(qepanet_junctions_elevcorr_od[ndID[i]])

                featJ.setGeometry(QgsGeometry.fromPointXY(point))

                # Emitter
                emitter_coeff = NULL
                if ndID[i] in emitters_d:
                    emitter_coeff = float(emitters_d[ndID[i]])

                # Tag
                tag = ''
                if ndID[i] in tags_d:
                    tag = tags_d[ndID[i]]

                zone_end = 0
                if ndID[i] in qepanet_junctions_zone_end_od:
                    zone_end = int(qepanet_junctions_zone_end_od[ndID[i]])

                pressure = 0
                if ndID[i] in qepanet_junctions_pressure_od:
                    pressure = float(qepanet_junctions_pressure_od[ndID[i]])

                pressure_units = 'meter'
                if ndID[i] in qepanet_junctions_pressure_units_od:
                    pressure_units = qepanet_junctions_pressure_units_od[ndID[i]]

                featJ.setAttributes([ndID[i], ndEle[i] - delta_z, delta_z,
                                     ndPatID[i], ndBaseD[i], emitter_coeff,
                                     nodes_desc[i], tag, zone_end, pressure,
                                     pressure_units])
                junctions_lay_dp.addFeatures([featJ])
                self.params.nodes_sindex.addFeature(featJ)

            if i < links_count:
                if len(stat) == i:
                    ch = 1
                if ch == 1:
                    stat.append('OPEN')

                x1.append(x[ndID.index(ref.getBinLinkFromNode()[i])])
                y1.append(y[ndID.index(ref.getBinLinkFromNode()[i])])
                x2.append(x[ndID.index(ref.getBinLinkToNode()[i])])
                y2.append(y[ndID.index(ref.getBinLinkToNode()[i])])

                if i in pump_index:

                    # Pump
                    point1 = QgsPointXY(float(x1[i]), float(y1[i]))
                    point2 = QgsPointXY(float(x2[i]), float(y2[i]))

                    chPowerPump = ref.getBinLinkPumpPower()
                    cheadpump = ref.getBinLinkPumpCurveNameID()
                    pumpID = ref.getBinLinkPumpNameID()
                    patternsIDs = ref.getBinLinkPumpPatterns()
                    ppatt = ref.getBinLinkPumpPatternsPumpID()
                    linkID = ref.getBinLinkNameID()

                    Head = []
                    Flow = []
                    curve = []
                    power = []
                    pattern = []
                    pumpNameIDPower = ref.getBinLinkPumpNameIDPower()

                    param = None
                    head = None
                    power = None
                    speed = None

                    if pumpID[pPos] in pumpNameIDPower:
                        param = 'POWER'
                        power = float(chPowerPump[pPosPower])
                        pPosPower += 1
                    else:
                        param = 'HEAD'
                        if len(cheadpump) > pPosHead:
                            head = cheadpump[pPosHead]
                            pPosHead += 1
                        else:
                            head = NULL

                    if len(pumpNameIDPower) > 0:
                        for uu in range(0, len(pumpNameIDPower)):
                            if pumpNameIDPower[uu] == pumpID[pPos]:
                                power = float(chPowerPump[uu])
                    if len(patternsIDs) > 0:
                        for uu in range(0, len(ppatt)):
                            if ppatt[uu] == pumpID[pPos]:
                                pattern = patternsIDs[uu]

                    if ref.getBinCurveCount() > 0 and len(pumpNameIDPower) == 0:
                        curveXY = ref.getBinCurvesXY()
                        curvesID = ref.getBinCurvesNameID()
                        for uu in range(0, len(curveXY)):
                            if curvesID[uu] == cheadpump[pPos]:
                                Head.append(str(curveXY[uu][0]))
                                Flow.append(str(curveXY[uu][1]))
                        curve = ref.getBinLinkPumpCurveNameID()[pPos]

                    if pumpID[pPos] in ref.getBinLinkPumpSpeedID():
                        speed = float(ref.getBinLinkPumpSpeed()[pPosSpeed])
                        pPosSpeed += 1

                    pump_pattern = None
                    if pumpID[pPos] in ppatt:
                        pump_pattern = ref.getBinLinkPumpPatterns()[pPosSpeedPattern]
                        pPosSpeedPattern += 1

                    pump_status = Pump.status_open
                    for statuss in status:
                        if statuss[0] == pumpID[pPos]:
                            if statuss[1].strip().upper() == Pump.status_closed or statuss[1].strip().upper() == Pump.status_open:
                                pump_status = statuss[1].strip().upper()
                                break

                    featPump = QgsFeature()
                    featPump.setGeometry(QgsGeometry.fromPolylineXY([point1, point2]))

                    tag = ''
                    if linkID[i] in tags_d:
                        tag = tags_d[linkID[i]]

                    featPump.setAttributes([linkID[i], param, head, power, speed, pump_pattern, pump_status,
                                            link_descs[i], tag])
                    pumps_lay_dp.addFeatures([featPump])
                    self.params.nodes_sindex.addFeature(featPump)

                    pPos += 1

                elif i in valve_index:
                    # Valve
                    point1 = QgsPointXY(float(x1[i]), float(y1[i]))
                    point2 = QgsPointXY(float(x2[i]), float(y2[i]))

                    length = 0
                    diameter = 0
                    roughness = 0
                    minorloss = 0
                    featValve = QgsFeature()
                    featValve.setGeometry((QgsGeometry.fromPolylineXY([point1, point2])))

                    linkID = ref.getBinLinkValveNameID()
                    descs = ref.get_valves_desc()
                    linkType = ref.getBinLinkValveType()
                    linkDiameter = ref.getBinLinkValveDiameters()
                    linkInitSett = ref.getBinLinkValveSetting()
                    linkMinorloss = ref.getBinLinkValveMinorLoss()

                    valve_status = Valve.status_none
                    for statuss in status:
                        if statuss[0] == linkID[vPos]:
                            valve_status = statuss[1]
                            break

                    # Tag
                    tag = ''
                    if linkID[vPos] in tags_d:
                        tag = tags_d[linkID[vPos]]

                    featValve.setAttributes(
                         [linkID[vPos], linkDiameter[vPos], linkType[vPos], linkInitSett[vPos], linkMinorloss[vPos],
                          valve_status, descs[vPos], tag])
                    valves_lay_dp.addFeatures([featValve])
                    self.params.nodes_sindex.addFeature(featValve)

                    vPos += 1

                else:
                    # Pipe

                    # Last point
                    start_node_id = ndlConn[0][i]
                    end_node_id = ndlConn[1][i]

                    # Z
                    start_node_elev = 0
                    end_node_elev = 0
                    for j in range(ref.getBinNodeJunctionCount()):

                        delta_z = 0
                        if qepanet_junctions_elevcorr_od and ndID[j] in qepanet_junctions_elevcorr_od:
                            delta_z = qepanet_junctions_elevcorr_od[ndID[j]]
                        if qepanet_reservoirs_deltaz_od and ndID[j] in qepanet_reservoirs_deltaz_od:
                            delta_z = qepanet_reservoirs_deltaz_od[ndID[j]]
                        if qepanet_tanks_od and ndID[j] in qepanet_tanks_od:
                            delta_z = qepanet_tanks_od[ndID[j]]

                        if ndID[j] == start_node_id:
                            start_node_elev = ndEle[j] + delta_z

                        if ndID[j] == end_node_id:
                            end_node_elev = ndEle[j] + delta_z

                    point1 = QgsPoint(float(x1[i]), float(y1[i]), start_node_elev)
                    point2 = QgsPoint(float(x2[i]), float(y2[i]), end_node_elev)

                    if vertx[i]:
                        parts = [point1]
                        for mm in range(len(vertxyFinal[kk])):
                            a = vertxyFinal[kk][mm]

                            z = 0
                            if linkID[i] in qepanet_vertices_od:
                                z = qepanet_vertices_od[linkID[i]]

                            parts.append(QgsPoint(a[0], a[1], z))

                        parts.append(point2)
                        featPipe = QgsFeature()
                        linestring = QgsLineString()
                        linestring.setPoints(parts)
                        geom_3d = QgsGeometry(linestring)
                        featPipe.setGeometry(geom_3d)

                        kk += 1
                    else:
                        featPipe = QgsFeature()
                        # point1 = QgsPoint(float(x1[i]), float(y1[i]))
                        # point2 = QgsPoint(float(x2[i]), float(y2[i]))

                        linestring = QgsLineString()
                        linestring.setPoints([point1, point2])
                        geom_3d = QgsGeometry(linestring)
                        featPipe.setGeometry(geom_3d)

                        # featPipe.setGeometry(QgsGeometry.fromPolyline([point1, point2]))

                    material = None
                    if linkID[i] in qepanet_pipes_material_od:
                        material = qepanet_pipes_material_od[linkID[i]]

                    tag = ''
                    if linkID[i] in tags_d:
                        tag = tags_d[linkID[i]]

                    num_edu = 0
                    if linkID[i] in qepanet_pipes_edu_od:
                        num_edu = int(qepanet_pipes_edu_od[linkID[i]])

                    zone_id = 0
                    if linkID[i] in qepanet_pipes_zone_id_od:
                        zone_id = int(qepanet_pipes_zone_id_od[linkID[i]])

                    velocity = 0
                    if linkID[i] in qepanet_pipes_velocity_od:
                        velocity = float(qepanet_pipes_velocity_od[linkID[i]])

                    frictionloss = 0
                    if linkID[i] in qepanet_pipes_frictionloss_od:
                        frictionloss = float(qepanet_pipes_frictionloss_od[linkID[i]])

                    length_units = 'meters'
                    if linkID[i] in qepanet_pipes_length_units_od:
                        length_units = qepanet_pipes_length_units_od[linkID[i]]

                    diameter_units = 'mm'
                    if linkID[i] in qepanet_pipes_diameter_units_od:
                        diameter_units = qepanet_pipes_diameter_units_od[linkID[i]]

                    velocity_units = 'm/s'
                    if linkID[i] in qepanet_pipes_velocity_units_od:
                        velocity_units = qepanet_pipes_velocity_units_od[linkID[i]]

                    frictionloss_units = 'm'
                    if linkID[i] in qepanet_pipes_frictionloss_units_od:
                        frictionloss_units = qepanet_pipes_frictionloss_units_od[linkID[i]]

                    featPipe.setAttributes(
                        [linkID[i], linkLengths[i], linkDiameters[i], stat[i],
                         linkRough[i], linkMinorloss[i], material,
                         link_descs[i], tag, num_edu, zone_id, velocity,
                         frictionloss, length_units, diameter_units,
                         velocity_units, frictionloss_units])
                    pipes_lay_dp.addFeatures([featPipe])
                    self.params.nodes_sindex.addFeature(featPipe)

            if i < ref.getBinNodeTankCount():
                p = ref.getBinNodeTankIndex()[i] - 1
                featTank = QgsFeature()
                point = QgsPointXY(float(x[p]), float(y[p]))
                featTank.setGeometry(QgsGeometry.fromPointXY(point))

                delta_z = 0
                if ndTankID[i] in qepanet_tanks_od:
                    delta_z = qepanet_tanks_od[ndTankID[i]]

                # Tag
                tag = ''
                if ndTankID[i] in tags_d:
                    tag = tags_d[ndTankID[i]]

                featTank.setAttributes(
                    [ndTankID[i], ndTankelevation[i] - delta_z, delta_z, initiallev[i], minimumlev[i], maximumlev[i], diameter[i],
                     minimumvol[i], volumecurv[i], nodes_desc[i], tag])
                tanks_lay_dp.addFeatures([featTank])
                self.params.nodes_sindex.addFeature(featTank)

            if i < ref.getBinNodeReservoirCount():
                p = ref.getBinNodeReservoirIndex()[i] - 1

                feat_reserv = QgsFeature()
                point = QgsPointXY(float(x[p]), float(y[p]))
                feat_reserv.setGeometry(QgsGeometry.fromPointXY(point))

                delta_z = 0
                if ndID[p] in qepanet_reservoirs_deltaz_od:
                    delta_z = qepanet_reservoirs_deltaz_od[ndID[p]]

                pressure_head = 0
                if ndID[p] in qepanet_reservoirs_press_head_od:
                    pressure_head = qepanet_reservoirs_press_head_od[ndID[p]]

                # Tag
                tag = ''
                if ndID[p] in tags_d:
                    tag = tags_d[ndID[p]]

                feat_reserv.setAttributes([ndID[p], reservoirs_elev[i] - delta_z - pressure_head, delta_z,
                                           pressure_head, ndPatID[p], nodes_desc[i], tag])
                reservoirs_lay_dp.addFeatures([feat_reserv])
                self.params.nodes_sindex.addFeature(feat_reserv)

        if curves:
            self.update_curves()
        if patterns:
            self.update_patterns()

        return {Junction.section_name: junctions_lay,
                Reservoir.section_name: reservoirs_lay,
                Tank.section_name: tanks_lay,
                Pipe.section_name: pipes_lay,
                Pump.section_name: pumps_lay,
                Valve.section_name: valves_lay}

    def update_mixing(self, mixing):
        # TODO
        pass

    def update_reactions(self, reactions):
        # TODO
        pass

    def update_sources(self, sources):
        # TODO
        pass

    def update_rules(self, rules):
        rules_out = []
        for rule in rules:
            rules_out.append(Rule(rule[0][0].rstrip('\r\n'), rule[1][0], rule[2][0]))
        self.params.rules = rules_out

    def update_quality(self, quality):
        # TODO
        pass

    def update_curves(self):
        InpFile.read_curves(self.params, self.inp_path)

    def update_patterns(self):
        InpFile.read_patterns(self.params, self.inp_path)

    def update_controls(self, controls):
        # TODO
        pass

    def update_demands(self, demands):
        # TODO
        pass

    def update_energy(self, energy):
        for e in energy:
            if e[1].upper() == 'EFFICIENCY':
                self.params.energy.pump_efficiency = e[2]
            elif e[1].upper() == 'PRICE':
                self.params.energy.energy_price = e[2]
            elif e[1].upper() == 'CHARGE':
                self.params.energy.demand_charge = e[2]
        # TODO: price pattern and single pumps

    def update_opt_reactions(self, opt_reactions):
        for r in opt_reactions:
            if r[0].upper() == 'ORDER':
                if r[1].upper() == 'BULK':
                    self.params.reactions.order_bulk = r[2]
                elif r[1].upper() == 'TANK':
                    self.params.reactions.order_tank = r[2]
                elif r[1].upper() == 'WALL':
                    self.params.reactions.order_wall = r[2]
            elif r[0].upper() == 'GLOBAL':
                if r[1].upper() == 'BULK':
                    self.params.reactions.global_bulk = r[2]
                elif r[1].upper() == 'WALL':
                    self.params.reactions.global_wall = r[2]
            elif r[0].upper() == 'LIMITING' and r[1].upper() == 'POTENTIAL':
                    self.params.reactions.limiting_potential = r[2]
            elif r[0].upper() == 'ROUGHNESS' and r[1].upper() == 'CORRELATION':
                    self.params.reactions.roughness_corr = r[2]

    def update_times(self, times):
        for t in times:
            if t[0].upper() == 'DURATION':
                self.params.times.duration = self.hour_from_text(t[1])
            elif t[0].upper() == 'HYDRAULIC' and t[1].upper() == 'TIMESTEP':
                self.params.times.hydraulic_timestep = self.hour_from_text(t[2])
            elif t[0].upper() == 'QUALITY' and t[1].upper() == 'TIMESTEP':
                self.params.times.quality_timestep = self.hour_from_text(t[2])
            elif t[0].upper() == 'PATTERN' and t[1].upper() == 'TIMESTEP':
                self.params.times.pattern_timestep = self.hour_from_text(t[2])
            elif t[0].upper() == 'PATTERN' and t[1].upper() == 'START':
                self.params.times.pattern_start = self.hour_from_text(t[2])
            elif t[0].upper() == 'REPORT' and t[1].upper() == 'TIMESTEP':
                self.params.times.report_timestep = self.hour_from_text(t[2])
            elif t[0].upper() == 'REPORT' and t[1].upper() == 'START':
                self.params.times.report_start = self.hour_from_text(t[2])
            elif t[0].upper() == 'START' and t[1].upper() == 'CLOCKTIME':
                time = self.hour_from_text(t[2])
                if len(t) > 3 and t[3].upper() == 'PM':
                    time += 12
                self.params.times.clocktime_start = time
            elif t[0].upper() == 'STATISTIC':
                for key, text in Times.stats_text.items():
                    if t[1].upper() == text.upper():
                        self.params.times.statistic = key
                        break

    def update_report(self, report):
        for r in report:
            if r[0].upper() == 'STATUS':
                if r[1].upper() == 'YES':
                    self.params.report.status = Report.status_yes
                elif r[1].upper() == 'NO':
                    self.params.report.status = Report.status_no
                elif r[1].upper() == 'FULL':
                    self.params.report.status = Report.status_full
            elif r[0].upper() == 'SUMMARY':
                if r[1].upper() == 'YES':
                    self.params.report.summary = Report.summary_yes
                else:
                    self.params.report.summary = Report.summary_no
            elif r[0].upper() == 'PAGE':
                self.params.report.page_size = r[1]
            elif r[0].upper() == 'ENERGY':
                if r[1].upper() == 'YES':
                    self.params.report.energy = Report.energy_yes
                else:
                    self.params.report.energy = Report.energy_no
            elif r[0].upper() == 'NODES':
                if r[1].upper() == 'ALL':
                    self.params.report.nodes = Report.nodes_all
                else:
                    self.params.report.nodes = Report.nodes_none
            elif r[0].upper() == 'LINKS':
                if r[1].upper() == 'ALL':
                    self.params.report.links = Report.links_all
                else:
                    self.params.report.links = Report.links_none

    def update_options(self, options):
        for o in options:
            if o[0].upper() == 'UNITS':

                if o[1].upper() in Options.units_flow[Options.unit_sys_si]:
                    self.params.options.units = Options.unit_sys_si
                elif o[1].upper() in Options.units_flow[Options.unit_sys_us]:
                    self.params.options.units = Options.unit_sys_us

                self.params.options.flow_units = o[1].upper()

            elif o[0].upper() == 'HEADLOSS':
                self.params.options.headloss = o[1].upper()
            elif o[0].upper() == 'SPECIFIC' and o[1].upper() == 'GRAVITY':
                self.params.options.spec_gravity = float(o[2])
            elif o[0].upper() == 'VISCOSITY':
                self.params.options.viscosity = float(o[1])
            elif o[0].upper() == 'TRIALS':
                self.params.options.trials = int(o[1])
            elif o[0].upper() == 'ACCURACY':
                self.params.options.accuracy = float(o[1])
            elif o[0].upper() == 'MAXCHECK':
                pass
            elif o[0].upper() == 'DAMPLIMIT':
                pass
            elif o[0].upper() == 'UNBALANCED':
                unbalanced = Unbalanced()
                if o[1].upper() == 'CONTINUE':
                    trials = int(o[2])
                    unbalanced.unbalanced = Unbalanced.unb_continue
                    unbalanced.trials = trials
                else:
                    unbalanced.unbalanced = Unbalanced.unb_stop
                self.params.options.unbalanced = unbalanced
            elif o[0].upper() == 'PATTERN':
                if o[1] in self.params.patterns:
                    self.params.options.pattern = self.params.patterns[o[1]]
                else:
                    self.params.options.pattern = None
            elif o[0].upper() == 'DEMAND' and o[1].upper() == 'MULTIPLIER':
                self.params.options.demand_mult = float(o[2])
            elif o[0].upper() == 'EMITTER' and o[1].upper() == 'EXPONENT':
                self.params.options.emitter_exp = float(o[2])
            elif o[0].upper() == 'QUALITY':
                quality = Quality()
                if o[1].upper() == 'NONE':
                    quality.parameter = Quality.quality_none
                elif o[1].upper() == 'AGE':
                    quality.parameter = Quality.quality_age
                elif o[1].upper() == 'TRACE':
                    quality.parameter = Quality.quality_trace
                else:
                    quality.parameter = Quality.quality_chemical
                    quality.quality_chemical = o[1]

                    units = o[2]
                    if units == 'mg/L':
                        quality.mass_units = Quality.quality_units_mgl
                    elif units == 'ug/L':
                        quality.mass_units = Quality.quality_units_ugl

                self.params.options.quality = quality

            # elif o[0].upper() == '':
            #     self.params.options.units = ?
            # elif o[0].upper() == '':
            #     self.params.options.units = ?
            # elif o[0].upper() == '':
            #     self.params.options.units = ?

    def hour_from_text(self, hhmm):

        hrs_min = hhmm.split(':')

        if hrs_min[0]:
            hrs = int(hrs_min[0])
            mins = 0
        if len(hrs_min) > 1 and hrs_min[1]:
            mins = int(hrs_min[1])

        hour = Hour(hrs, mins)

        return hour

    def read_section(self, section_name):

        section_name = '[' + section_name + ']'

        section_started = False
        start_line = None
        end_line = None
        for l in range(len(self.lines)):
            if section_name.upper() in self.lines[l].upper():
                section_started = True
                start_line = l + 1
                continue
            if self.lines[l].startswith('[') and section_started:
                end_line = l - 1
                break

        if start_line is None:
            return None

        if end_line is None:
            end_line = len(self.lines)

        return self.lines[start_line:end_line]

    def read_qepanet_junctions(self):

        lines = self.read_section(QJunction.section_name)

        junctions_elevcorr_od = OrderedDict()
        junctions_zone_end_od = OrderedDict()
        junctions_pressure_od = OrderedDict()
        junctions_pressure_units_od = OrderedDict()
        if lines is not None:
            for line in lines:
                if line.strip().startswith(';'):
                    continue
                words = line.split()
                if len(words) > 1:
                    junctions_elevcorr_od[words[0].strip()] = float(words[1].strip())
                if len(words) > 2:
                    junctions_zone_end_od[words[0].strip()] = int(words[2].strip())
                if len(words) > 3:
                    junctions_pressure_od[words[0].strip()] = float(words[3].strip())
                if len(words) > 4:
                    junctions_pressure_units_od[words[0].strip()] = \
                        words[4].strip()

        return junctions_elevcorr_od, junctions_zone_end_od, \
                junctions_pressure_od, junctions_pressure_units_od

    def read_qepanet_reservoirs(self):

        lines = self.read_section(QReservoir.section_name)
        reservoirs_elevcorr_od = OrderedDict()
        reservoirs_press_heads_od = OrderedDict()
        if lines is not None:
            for line in lines:
                if line.strip().startswith(';'):
                    continue
                words = line.split()
                if len(words) > 1:
                    reservoirs_elevcorr_od[words[0].strip()] = float(words[1].strip())
                if len(words) > 2:
                    reservoirs_press_heads_od[words[0].strip()] = float(words[2].strip())

        return reservoirs_elevcorr_od, reservoirs_press_heads_od

    def read_qepanet_tanks(self):

        lines = self.read_section(QTank.section_name)
        tanks_elevcorr_od = OrderedDict()
        if lines is not None:
            for line in lines:
                if line.strip().startswith(';'):
                    continue
                words = line.split()
                if len(words) > 1:
                    tanks_elevcorr_od[words[0].strip()] = float(words[1].strip())

        return tanks_elevcorr_od

    def read_qepanet_pipes(self):

        lines = self.read_section(QPipe.section_name)
        pipes_material_od = OrderedDict()
        pipes_edu_od = OrderedDict()
        pipes_zone_id_od = OrderedDict()
        pipes_velocity_od = OrderedDict()
        pipes_velocity_units_od = OrderedDict()
        pipes_frictionloss_od = OrderedDict()
        pipes_frictionloss_units_od = OrderedDict()
        pipes_length_units_od = OrderedDict()
        pipes_diameter_units_od = OrderedDict()
        if lines is not None:
            for line in lines:
                if line.strip().startswith(';'):
                    continue
                words = [l.strip() for l in line.split('  ') if l] # split on 2 or more spaces and discard empty strings
                #print("words: ", words)
                spaces = re.findall(' +', line)  #extract the white space between words
                #print("spaces: ", spaces)
                if len(words) > 1:
                    pipes_material_od[words[0].strip()] = words[1].strip()
                if len(words) > 2:  #parses through line to find all words separted by a single space
                    pipes_edu_od[words[0].strip()] = words[2].strip()
                if len(words) > 3:
                    pipes_zone_id_od[words[0].strip()] = words[3].strip()
                if len(words) > 4:
                    pipes_velocity_od[words[0].strip()] = words[4].strip()
                if len(words) > 5:
                    pipes_frictionloss_od[words[0].strip()] = words[5].strip()
                if len(words) > 6:
                    pipes_length_units_od[words[0].strip()] = \
                        words[6].strip()
                if len(words) > 7:
                    pipes_diameter_units_od[words[0].strip()] = \
                        words[7].strip()
                if len(words) > 8:
                    pipes_velocity_units_od[words[0].strip()] = words[8].strip()
                if len(words) > 9:
                    pipes_frictionloss_units_od[words[0].strip()] = \
                        words[9].strip()
                # if len(words) > 2:  #parses through line to find all words separted by a single space
                #     i=1
                #     while spaces[i-1] is ' ':
                #         pipes_material_od[words[0].strip()] = pipes_material_od[words[0].strip()] + (" "+words[i].strip())
                #         i +=1
                #     pipes_edu_od[words[0].strip()] = words[i].strip()
                # if len(words) > i+1:
                #     pipes_zone_id_od[words[0].strip()] = words[3].strip()
                # if len(words) > i+2:
                #     pipes_velocity_od[words[0].strip()] = words[4].strip()
                # if len(words) > i+3:
                #     pipes_frictionloss_od[words[0].strip()] = words[5].strip()

        #print("pipe_material: ", pipes_material_od)

        return pipes_material_od, pipes_edu_od, pipes_zone_id_od, \
            pipes_velocity_od, pipes_frictionloss_od, pipes_length_units_od, \
            pipes_diameter_units_od, pipes_velocity_units_od, \
            pipes_frictionloss_units_od

    def read_qepanet_vertices(self):

        lines = self.read_section(QVertices.section_name)
        vertices_zs_od = OrderedDict()
        if lines is not None:
            for line in lines:
                if line.strip().startswith(';'):
                    continue
                words = line.split()
                if len(words) > 1:
                    vertices_zs_od[words[0].strip()] = float(words[1].strip())

        return vertices_zs_od


# ir = InpReader('D:/temp/5.inp')
# print ir.read_qepanet_tanks()
