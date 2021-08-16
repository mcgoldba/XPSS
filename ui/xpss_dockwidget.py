# -*- coding: utf-8 -*-
"""
/***************************************************************************
 XPSSDockWidget
                                 A QGIS plugin
 This plugin performs pressure sewer system calculations within QGIS.
                             -------------------
        begin                : 2021-07-21
        git sha              : $Format:%H$
        email                : mcgoldba@gmail.com
 ***************************************************************************/

/***************************************************************************
 *                                                                         *
 *   This program is free software; you can redistribute it and/or modify  *
 *   it under the terms of the GNU General Public License as published by  *
 *   the Free Software Foundation; either version 2 of the License, or     *
 *   (at your option) any later version.                                   *
 *                                                                         *
 ***************************************************************************/
"""
from __future__ import print_function
from __future__ import absolute_import

from builtins import str
import os

from qgis.PyQt import QtCore, uic, QtGui
from qgis.PyQt.QtCore import Qt, pyqtSignal
from qgis.PyQt.QtWidgets import QFileDialog, QMessageBox, QApplication, QLabel, QToolTip, QDockWidget
from qgis.PyQt.QtGui import QPixmap, QCursor, QDoubleValidator
from qgis.gui import QgsProjectionSelectionDialog
from qgis.core import QgsProject, QgsFeatureRequest, QgsMapLayer, Qgis

from ..geo_utils.utils import LayerUtils as lay_utils
from .options_dialogs import HydraulicsDialog, QualityDialog, ReactionsDialog, TimesDialog, EnergyDialog, ReportDialog
from .output_ui import OutputAnalyserDialog, LogDialog
from ..model.options_report import Options
from .curvespatterns_ui import GraphDialog
from ..model.inp_writer import InpFile
from ..model.inp_reader import InpReader
from ..model.network import Junction, Reservoir, Tank, Pipe, Pump, Valve
from ..model.network_handling import NetworkUtils
from ..model.network_handling import LinkHandler
from ..pss.driver import Driver
from ..rendering import symbology
from ..tools.add_junction_tool import AddJunctionTool
from ..tools.add_pipe_tool import AddPipeTool
from ..tools.add_pump_tool import AddPumpTool
from ..tools.add_reservoir_tool import AddReservoirTool
from ..tools.add_tank_tool import AddTankTool
from ..tools.add_valve_tool import AddValveTool
from ..tools.move_tool import MoveTool
from ..tools.data_stores import MemoryDS
from ..tools.delete_tool import DeleteTool
from ..tools.parameters import Parameters, RegExValidators, ConfigFile
from .tags_dialog import TagsDialog
from .utils import prepare_label as pre_l, set_up_button
from . import misc

from ..pss.driver import Driver
from ..pss.calc.solvers.solverfactory import SolverFactory
from ..pss.calc.nomdia.nomdiafactory import NomDiaFactory
from ..pss.calc.flowheadrelations.flowheadrelationsfactory import FlowHeadRelationsFactory
from ..pss.calc.opedumethod.opedumethodfactory import OpEduMethodFactory
from ..pss.db.pipedatabase import PipeDatabase, PipeMaterial
from ..pss.db.units import LengthUnits, FlowUnits, VelocityUnits, PressureUnits, \
    MetricSystem, USSystem, ImperialSystem

from XPSS.logger import Logger

logger = Logger(debug=True)

FORM_CLASS, _ = uic.loadUiType(os.path.join(
    os.path.dirname(__file__), 'xpss_dockwidget.ui'))


class XPSSDockWidget(QDockWidget, FORM_CLASS):

    closingPlugin = pyqtSignal()

    def __init__(self, iface, params, config):
        """Constructor."""
        super(XPSSDockWidget, self).__init__(iface.mainWindow())
        self.iface = iface
        self.params = params
        self.inp_file_path = config['EPANET']['inp_file_path']
        self.pump_db_file_path = config['XPSS']['pump_db_file_path']
        self.pipe_db_file_path = config['XPSS']['pipe_db_file_path']
        self.pipe_rgh_db_file_path = config['XPSS']['pipe_rgh_db_file_path']
        self.op_edu_table_path = config['XPSS']['op_edu_table_path']
        #self.flow_units = config['XPSS']['flow_units'].split()
        #self.length_units = config['XPSS']['length_units'].split()
        self.pipedb = PipeDatabase().load(self.pipe_db_file_path,
                                        self.pipe_rgh_db_file_path)

        logger.debugger(str(self.pipedb.materials))

        self.params.attach(self)

        self.setupUi(self)
        self.setWindowTitle(params.plug_in_name)

        self.decimals = 1

        self.tool = None

        # Dialogs
        self.hydraulics_dialog = None
        self.quality_dialog = None
        self.reactions_dialog = None
        self.times_dialog = None
        self.energy_dialog = None
        self.report_dialog = None
        self.output_dialog = None

        self.log_dialog = None

        # Inp file
        self.btn_project_new.clicked.connect(self.project_new_clicked)
        self.btn_project_load.clicked.connect(self.project_load_clicked)
        self.btn_project_save.clicked.connect(self.project_save_clicked)
        self.btn_project_saveas.clicked.connect(self.project_saveas_clicked)

        curr_dir = os.path.dirname(os.path.abspath(__file__))

        # Project buttons
        set_up_button(self.btn_project_new, os.path.join(curr_dir, 'i_new.png',), tooltip_text='New project')
        set_up_button(self.btn_project_load, os.path.join(curr_dir, 'i_load.png'), tooltip_text='Open project')
        set_up_button(self.btn_project_save, os.path.join(curr_dir, 'i_save.png'), tooltip_text='Save project')
        set_up_button(self.btn_project_saveas, os.path.join(curr_dir, 'i_saveas.png'), tooltip_text='Save project as')

        # Tools buttons
        set_up_button(self.btn_add_junction, os.path.join(curr_dir, 'i_junction.png'), True, 12, 12,
                      'Create junction')  # TODO: softcode
        set_up_button(self.btn_add_reservoir, os.path.join(curr_dir, 'i_reservoir.png'), True, 14, 14,
                      'Create reservoir')  # TODO: softcode
        # set_up_button(self.btn_add_tank, os.path.join(curr_dir, 'i_tank.png'), True, 14, 12,
        #               'Create tank')  # TODO: softcode
        set_up_button(self.btn_add_pipe, os.path.join(curr_dir, 'i_pipe.png'), True, 13, 5,
                      'Create/edit pipe')  # TODO: softcode
        # set_up_button(self.btn_add_pump, os.path.join(curr_dir, 'i_pump.png'), True, 15, 11,
        #               'Create pump')  # TODO: softcode
        # set_up_button(self.btn_add_valve, os.path.join(curr_dir, 'i_valve.png'), True, 13, 14,
        #               'Create valve')  # TODO: softcode
        set_up_button(self.btn_move_element, os.path.join(curr_dir, 'i_move.png'), True, 15, 15,
                      'Move element')  # TODO: softcode
        set_up_button(self.btn_delete_element, os.path.join(curr_dir, 'i_delete2.png'), True, 13, 15,
                      'Delete element(s)')  # TODO: softcode

        # EPANET button
        set_up_button(self.btn_xpss_run, os.path.join(curr_dir, 'i_run.png'), tooltip_text='Run')

        self.btn_move_element.setCheckable(True)
        self.btn_delete_element.setCheckable(True)

        self.btn_add_junction.clicked.connect(self.add_junction)
        self.btn_add_reservoir.clicked.connect(self.add_reservoir)
        # self.btn_add_tank.clicked.connect(self.add_tank)

        self.btn_add_pipe.clicked.connect(self.add_pipe)
        # self.btn_add_pump.clicked.connect(self.add_pump)
        # self.btn_add_valve.clicked.connect(self.add_valve)

        self.btn_move_element.clicked.connect(self.move_element)
        self.btn_delete_element.clicked.connect(self.delete_element)

        # Layers
        self.cbo_dem.activated.connect(self.cbo_dem_activated)

        QgsProject.instance().legendLayersAdded.connect(self.update_layers_combos)
        QgsProject.instance().layerRemoved.connect(self.update_layers_combos)
        self.update_layers_combos()
        self.preselect_layers_combos()

        # XPSS
        self.btn_xpss_run.clicked.connect(self.btn_xpss_run_clicked)

        #self.btn_xpss_output.clicked.connect(self.btn_xpss_output_clicked)

        self.btn_xpss_run.setEnabled(True)

        # Settings
        #- General

        self.txt_pump_db.setText(self.pump_db_file_path)
        self.txt_pipe_db.setText(self.pipe_db_file_path)
        self.txt_pipe_rgh_db.setText(self.pipe_rgh_db_file_path)
        self.txt_op_edu_table.setText(self.op_edu_table_path)

        #- Pipe Network

        self.cbo_pipe_mtl.activated.connect(
            self.cbo_pipe_mtl_activated)

        self.cbo_pipe_dia_units.activated.connect(
            self.cbo_pipe_dia_units_activated
        )

        self.cbo_pipe_dia.activated.connect(
            self.cbo_pipe_dia_activated
        )

        self.txt_station_depth.setText("{:.1f}".format(6))
        self.txt_station_depth.setValidator(QDoubleValidator())

        #- Solver

        driver = self.cbo_solver.currentText()

        self.txt_flowrate.setValidator(QDoubleValidator())

        if driver == "Constant Flow":  #TODO:  Soft code
            self.txt_flowrate.setText("11.0")
        else:
            self.txt_flowrate.setText("20.0")

        self.cbo_flow_units.setCurrentIndex(0)

        #TODO: Update value on unit change
        # self.cbo_flow_units.activated.connect(
        #     self.cbo_flow_units_activated
        # )

        self.cbo_friction_loss_eq.activated.connect(
            self.cbo_fricton_loss_eq_activated)

        self.cbo_op_edu_method.activated.connect(
            self.cbo_op_edu_method_activated)

        #TODO: soft code
        self.txt_epa_a.setText("{:.1f}".format(0.5))
        self.txt_epa_b.setText("{:.1f}".format(20))

        self.txt_epa_a.setValidator(QDoubleValidator())
        self.txt_epa_b.setValidator(QDoubleValidator())

        self.cbo_lat_pipe_sch.activated.connect(
            self.cbo_lat_pipe_dia_activated
        )

        self.cbo_lat_pipe_dia_units.activated.connect(
            self.cbo_lat_pipe_dia_units_activated
        )

        self.cbo_lat_pipe_dia.activated.connect(
            self.cbo_lat_pipe_dia_activated
        )
        #self.cbo_lat_pipe_dia.setValidator(QDoubleValidator())

        self.txt_min_vel.setText("{:.1f}".format(2.0))
        self.txt_min_vel.setValidator(QDoubleValidator())

        self.txt_max_vel.setText("{:.1f}".format(5.0))
        self.txt_max_vel.setValidator(QDoubleValidator())

        self.cbo_lat_pipe_mtl.activated.connect(
            self.cbo_lat_pipe_mtl_activated)

        # Reporting

        self.bto_metric.clicked.connect(self.bto_metric_clicked)
        self.bto_us.clicked.connect(self.bto_us_clicked)
        self.bto_imperial.clicked.connect(self.bto_imperial_clicked)

        #TODO: This does nothing because combo boxes are not populated yet
        self.update_report_units(USSystem)


        # Project File

        self.txt_prj_file.setText(self.inp_file_path)

        self.read_inp_file()

     # This method needed by Observable
    def update(self, observable):
    #     # Update components
        #self.update_drivers_combo()
        self.update_combo_from_factory_method(self.cbo_solver, SolverFactory)
        self.update_flow_units_combo(self.cbo_flow_units)
        self.update_velocity_units_combo(self.cbo_min_vel_units)
        self.update_velocity_units_combo(self.cbo_max_vel_units)
        self.update_pipe_material_combo(self.cbo_pipe_mtl,
                                        self.cbo_pipe_dia_units)
        self.update_pipe_material_combo(self.cbo_lat_pipe_mtl,
                                        self.cbo_lat_pipe_dia_units)
        self.update_pipe_schedule_combo(self.cbo_pipe_sch,
                                        self.cbo_pipe_mtl.currentText())
        self.update_pipe_schedule_combo(self.cbo_lat_pipe_sch,
                                        self.cbo_lat_pipe_mtl.currentText())
        self.update_length_units_combo(self.cbo_pipe_dia_units)
        self.update_length_units_combo(self.cbo_lat_pipe_dia_units)
        self.update_length_units_combo(self.cbo_depth_units)
        self.update_length_units_combo(self.cbo_dem_units)
        self.update_pipe_diameter_combo(
            self.cbo_pipe_dia,
            self.cbo_pipe_mtl.currentText(),
            self.cbo_pipe_sch.currentText(),
            self.cbo_pipe_dia_units.currentText()
            )
        self.update_pipe_diameter_combo(
            self.cbo_lat_pipe_dia,
            self.cbo_lat_pipe_mtl.currentText(),
            self.cbo_lat_pipe_sch.currentText(),
            self.cbo_lat_pipe_dia_units.currentText()
            )
        self.update_friction_loss_eq_combo()
        self.update_combo_from_factory_method(self.cbo_dia_method, NomDiaFactory)
        self.update_op_edu_method_combo()
        self.update_roughness_params()
    #     self.update_patterns_combo()
    #     self.update_curves_combo()
    #     self.update_tags_combos()
        self.update_length_units_combo(self.cbo_rpt_units_pipe_length)
        self.update_length_units_combo(self.cbo_rpt_units_diameter)
        self.update_flow_units_combo(self.cbo_rpt_units_flow)
        self.update_pressure_units_combo(self.cbo_rpt_units_pressure)
        self.update_velocity_units_combo(self.cbo_rpt_units_velocity)

    def closeEvent(self, event):
        self.closingPlugin.emit()
        event.accept()

    def count_elements(self):

        jun_count = self.params.junctions_vlay.featureCount()
        res_count = self.params.reservoirs_vlay.featureCount()
        tan_count = self.params.tanks_vlay.featureCount()
        pip_count = self.params.pipes_vlay.featureCount()
        pum_count = self.params.pumps_vlay.featureCount()
        val_count = self.params.valves_vlay.featureCount()

        text = 'Load OK. ' +\
               str(jun_count) + ' junction(s), ' + \
               str(res_count) + ' reservoir(s), ' + \
               str(tan_count) + ' tank(s), ' + \
               str(pip_count) + ' pipe(s), ' + \
               str(pum_count) + ' pump(s) and ' + \
               str(val_count) + ' valve(s) were loaded.'

        msg_box = QMessageBox(self)
        msg_box.setWindowTitle(Parameters.plug_in_name)
        msg_box.setIcon(QMessageBox.Information)
        msg_box.setText(text)
        msg_box.exec_()

    # def create_layers_clicked(self):
    #     self.create_layers(None, self.params.crs)

    def create_layers(self, new_layers_d, crs):

        if new_layers_d is not None and new_layers_d[Junction.section_name] is not None:
            self.params.junctions_vlay = new_layers_d[Junction.section_name]
        else:
            self.params.junctions_vlay = MemoryDS.create_junctions_lay(crs=crs)
            self.params.junctions_vlay = MemoryDS.create_junctions_lay(crs=crs)
        self.params.junctions_vlay.attributeValueChanged.connect(self.ju_attrib_val_changed)

        if new_layers_d is not None and new_layers_d[Reservoir.section_name] is not None:
            self.params.reservoirs_vlay = new_layers_d[Reservoir.section_name]
        else:
            self.params.reservoirs_vlay = MemoryDS.create_reservoirs_lay(crs=crs)
        self.params.reservoirs_vlay.attributeValueChanged.connect(self.re_attrib_val_changed)

        if new_layers_d is not None and new_layers_d[Tank.section_name] is not None:
            self.params.tanks_vlay = new_layers_d[Tank.section_name]
        else:
            self.params.tanks_vlay = MemoryDS.create_tanks_lay(crs=crs)
        self.params.tanks_vlay.attributeValueChanged.connect(self.ta_attrib_val_changed)

        if new_layers_d is not None and new_layers_d[Pipe.section_name] is not None:
            self.params.pipes_vlay = new_layers_d[Pipe.section_name]
        else:
            self.params.pipes_vlay = MemoryDS.create_pipes_lay(crs=crs)

        if new_layers_d is not None and new_layers_d[Pump.section_name] is not None:
            self.params.pumps_vlay = new_layers_d[Pump.section_name]
        else:
            self.params.pumps_vlay = MemoryDS.create_pumps_lay(crs=crs)

        if new_layers_d is not None and new_layers_d[Valve.section_name] is not None:
            self.params.valves_vlay = new_layers_d[Valve.section_name]
        else:
            self.params.valves_vlay = MemoryDS.create_valves_lay(crs=crs)

        QgsProject.instance().addMapLayers([self.params.junctions_vlay,
                                                    self.params.reservoirs_vlay,
                                                    self.params.tanks_vlay,
                                                    self.params.pipes_vlay,
                                                    self.params.pumps_vlay,
                                                    self.params.valves_vlay])

        # Apply symbologies
        self.apply_symbologies()

        # Zoom to layer
        extent = self.params.pipes_vlay.extent()

        if not extent.isNull():
            canvas = self.iface.mapCanvas()
            canvas.setExtent(extent)
            canvas.refresh()

    def add_junction(self):

        if type(self.iface.mapCanvas().mapTool()) is AddJunctionTool:
            self.iface.mapCanvas().unsetMapTool(self.tool)
            self.params.detach(self.tool)

        else:
            self.tool = AddJunctionTool(self, self.params)
            self.params.attach(self.tool)
            self.iface.mapCanvas().setMapTool(self.tool)
            self.setCursor()

    def add_reservoir(self):

        if type(self.iface.mapCanvas().mapTool()) is AddReservoirTool:
            self.iface.mapCanvas().unsetMapTool(self.tool)
            self.params.detach(self.tool)

        else:
            self.tool = AddReservoirTool(self, self.params)
            self.params.attach(self.tool)
            self.iface.mapCanvas().setMapTool(self.tool)
            self.setCursor()

    def add_tank(self):

        if type(self.iface.mapCanvas().mapTool()) is AddTankTool:
            self.iface.mapCanvas().unsetMapTool(self.tool)
            self.params.detach(self.tool)

        else:
            tool = AddTankTool(self, self.params)
            self.params.attach(self.tool)
            self.iface.mapCanvas().setMapTool(tool)
            self.setCursor()

    def add_pipe(self):

        if type(self.iface.mapCanvas().mapTool()) is AddPipeTool:
            self.iface.mapCanvas().unsetMapTool(self.tool)
            self.params.detach(self.tool)

        else:
            self.tool = AddPipeTool(self, self.params)
            self.params.attach(self.tool)
            self.iface.mapCanvas().setMapTool(self.tool)
            self.setCursor()

    def add_pump(self):

        if type(self.iface.mapCanvas().mapTool()) is AddPumpTool:
            self.iface.mapCanvas().unsetMapTool(self.tool)
            self.params.detach(self.tool)

        else:
            self.tool = AddPumpTool(self, self.params)
            self.params.attach(self.tool)
            self.iface.mapCanvas().setMapTool(self.tool)
            self.setCursor()

    def add_valve(self):

        if type(self.iface.mapCanvas().mapTool()) is AddValveTool:
            self.iface.mapCanvas().unsetMapTool(self.tool)
            self.params.detach(self.tool)

        else:
            self.tool = AddValveTool(self, self.params)
            self.params.attach(self.tool)
            self.iface.mapCanvas().setMapTool(self.tool)
            self.setCursor()

    def setCursor(self):
        self.my_cursor_xpm = [
            "16 16 3 1",
            "       c None",
            ".      c #000000",
            "+      c #FFFFFF",
            "                ",
            "       +.+      ",
            "      ++.++     ",
            "     +.....+    ",
            "    +.     .+   ",
            "   +.   .   .+  ",
            "  +.    .    .+ ",
            " ++.    .    .++",
            " ... ...+... ...",
            " ++.    .    .++",
            "  +.    .    .+ ",
            "   +.   .   .+  ",
            "   ++.     .+   ",
            "    ++.....+    ",
            "      ++.++     ",
            "       +.+      "]

        self.my_pixmap = QPixmap(self.my_cursor_xpm)
        self.my_cursor = QCursor(self.my_pixmap, 8, 8)
        self.iface.mapCanvas().setCursor(self.my_cursor)

    def move_element(self):

        if type(self.iface.mapCanvas().mapTool()) is MoveTool:
            self.iface.mapCanvas().unsetMapTool(self.tool)
            # self.btn_move_element.setChecked(True)

        else:
            self.tool = MoveTool(self, self.params)
            self.iface.mapCanvas().setMapTool(self.tool)
            self.set_cursor(QtCore.Qt.CrossCursor)

    def delete_element(self):

        if type(self.iface.mapCanvas().mapTool()) is DeleteTool:
            self.iface.mapCanvas().unsetMapTool(self.tool)
            # self.btn_delete_element.setChecked(True)

        else:
            self.tool = DeleteTool(self, self.params)
            self.iface.mapCanvas().setMapTool(self.tool)
            self.set_cursor(QtCore.Qt.CrossCursor)

    def ju_attrib_val_changed(self, fid, idx, new_val):
        self.node_attrib_val_changed(fid, idx, self.params.junctions_vlay,
                                     [Junction.field_name_elev, Junction.field_name_delta_z])

    def re_attrib_val_changed(self, fid, idx, new_val):
        self.node_attrib_val_changed(fid, idx, self.params.reservoirs_vlay,
                                     [Reservoir.field_name_elev, Reservoir.field_name_delta_z])

    def ta_attrib_val_changed(self, fid, idx, new_val):
        self.node_attrib_val_changed(fid, idx, self.params.tanks_vlay,
                                     [Tank.field_name_elev, Tank.field_name_delta_z])

    def node_attrib_val_changed(self, fid, idx, layer, elev_field_names):

        # If attibute changed is elev or deltaz, update pipe length
        for elev_field_name in elev_field_names:
            if idx == layer.fields().lookupField(elev_field_name):
                # Get feature
                for feat in layer.getFeatures(QgsFeatureRequest().setFilterFid(fid)):
                    # Get adjacent links and update length
                    adj_links = NetworkUtils.find_adjacent_links(self.params, feat.geometry())
                    for adj_link in adj_links['pipes']:
                        self.update_link_length(adj_link, self.params.pipes_vlay, Pipe.field_name_length)

    def update_link_length(self, link, layer, length_field_name):
        new_3d_length = LinkHandler.calc_3d_length(self.params, link.geometry())

        field_index = layer.dataProvider().fieldNameIndex(length_field_name)

        if not layer.isEditable():
            layer.startEditing()

        layer.changeAttributeValue(link.id(), field_index, new_3d_length)

    def cbo_pump_param_activated(self):
        selected_param = self.cbo_pump_param.itemText(self.cbo_pump_param.currentIndex())
        self.lbl_pump_power.setEnabled(selected_param == Pump.parameters_power)
        self.txt_pump_power.setEnabled(selected_param == Pump.parameters_power)
        self.lbl_pump_head.setEnabled(selected_param == Pump.parameters_head)
        self.cbo_pump_head.setEnabled(selected_param == Pump.parameters_head)

    def cbo_valve_type_activated(self):
        selected_type = self.cbo_valve_type.itemData(self.cbo_valve_type.currentIndex())

        setting_on = True
        setting_label = '-'
        if selected_type == Valve.type_pbv or selected_type == Valve.type_prv or selected_type == Valve.type_psv:
            setting_label = 'Pressure' + ' [' + self.params.options.units_deltaz[self.params.options.units] + ']' # TODO: softcode
        elif selected_type == Valve.type_fcv:
            setting_label = 'Flow:' + ' [' + self.params.options.flow_units + ']' # TODO: softcode
        elif selected_type == Valve.type_tcv:
            setting_label = 'Loss coeff. [-]:' # TODO: softcode
        elif selected_type == Valve.type_gpv:
            setting_on = False

        self.lbl_valve_setting.setEnabled(setting_on)
        self.txt_valve_setting.setEnabled(setting_on)
        self.lbl_valve_curve.setEnabled(not setting_on)
        self.cbo_valve_curve.setEnabled(not setting_on)

        if setting_on:
            self.lbl_valve_setting.setText(setting_label)

    # def btn_hydraulics_clicked(self):
    #     if self.hydraulics_dialog is None:
    #         self.hydraulics_dialog = HydraulicsDialog(self, self.params)
    #     self.hydraulics_dialog.show()

    def btn_quality_clicked(self):
        if self.quality_dialog is None:
            self.quality_dialog = QualityDialog(self, self.params)
        self.quality_dialog.show()

    def btn_reactions_clicked(self):
        if self.reactions_dialog is None:
            self.reactions_dialog = ReactionsDialog(self, self.params)
        self.reactions_dialog.show()

    def btn_times_clicked(self):
        if self.times_dialog is None:
            self.times_dialog = TimesDialog(self, self.params)
        self.times_dialog.show()

    def btn_energy_clicked(self):
        if self.energy_dialog is None:
            self.energy_dialog = EnergyDialog(self, self.params)
        self.energy_dialog.show()

    def btn_report_clicked(self):
        if self.report_dialog is None:
            self.report_dialog = ReportDialog(self, self.params)
        self.report_dialog.show()

    def roughness_slider_changed(self):
        self.lbl_pipe_roughness_val_val.setText(str(float(self.sli_pipe_roughness.value()) / 10**self.decimals))

    # TODO: update snappers in all the tools that use snapping
    def cbo_dem_activated(self, index):
        layer_id = self.cbo_dem.itemData(index)
        self.params.dem_rlay = QgsProject.instance().mapLayer(layer_id)

    def cbo_pipe_roughness_activated(self):
        self.update_roughness_params(self.get_combo_current_data(self.cbo_pipe_roughness)[self.params.options.headloss])

    def cbo_pipe_mtl_activated(self):
        self.update_pipe_schedule_combo(self.cbo_pipe_sch,
                                        self.cbo_pipe_mtl.currentText())
    def cbo_lat_pipe_mtl_activated(self):
        self.update_pipe_schedule_combo(self.cbo_lat_pipe_sch,
                                        self.cbo_lat_pipe_mtl.currentText())
        self.update_pipe_diameter_combo(self.cbo_lat_pipe_dia,
                                        self.cbo_lat_pipe_mtl.currentText(),
                                        self.cbo_lat_pipe_sch.currentText(),
                                        self.cbo_lat_pipe_dia_units.currentText()
                                        )

    def cbo_pipe_dia_activated(self):
        self.update_pipe_diameter_combo(self.cbo_pipe_dia,
                                        self.cbo_pipe_mtl.currentText(),
                                        self.cbo_pipe_sch.currentText(),
                                        self.cbo_pipe_dia_units.currentText())

    def cbo_lat_pipe_dia_activated(self):
        self.update_pipe_diameter_combo(self.cbo_lat_pipe_dia,
                                        self.cbo_lat_pipe_mtl.currentText(),
                                        self.cbo_lat_pipe_sch.currentText(),
                                        self.cbo_lat_pipe_dia_units.currentText()
                                        )
    def cbo_lat_pipe_dia_units_activated(self):
        self.update_pipe_diameter_combo(self.cbo_lat_pipe_dia,
                                        self.cbo_lat_pipe_mtl.currentText(),
                                        self.cbo_lat_pipe_sch.currentText(),
                                        self.cbo_lat_pipe_dia_units.currentText()
                                        )
    def cbo_pipe_dia_activated(self):
        self.update_pipe_diameter_combo(self.cbo_pipe_dia,
                                        self.cbo_pipe_mtl.currentText(),
                                        self.cbo_pipe_sch.currentText(),
                                        self.cbo_pipe_dia_units.currentText()
                                        )
    def cbo_pipe_dia_units_activated(self):
        self.update_pipe_diameter_combo(self.cbo_pipe_dia,
                                        self.cbo_pipe_mtl.currentText(),
                                        self.cbo_pipe_sch.currentText(),
                                        self.cbo_pipe_dia_units.currentText()
                                        )

    def snap_tolerance_changed(self):
        if self.txt_snap_tolerance.text():
            self.params.snap_tolerance = (float(self.txt_snap_tolerance.text()))

    def cbo_fricton_loss_eq_activated(self):
        self.update_roughness_params()

    def cbo_op_edu_method_activated(self):
        self.update_epa_coeff_status()

    def bto_metric_clicked(self):
        self.update_report_units(MetricSystem)

    def bto_us_clicked(self):
        self.update_report_units(USSystem)

    def bto_imperial_clicked(self):
        self.update_report_units(ImperialSystem)

    def update_report_units(self, system):
        idx = self.cbo_rpt_units_pipe_length.findText(system["length"])
        self.cbo_rpt_units_pipe_length.setCurrentIndex(idx)

        idx = self.cbo_rpt_units_flow.findText(system["flow"])
        self.cbo_rpt_units_flow.setCurrentIndex(idx)

        idx = self.cbo_rpt_units_pressure.findText(system["pressure"])
        self.cbo_rpt_units_pressure.setCurrentIndex(idx)

        idx = self.cbo_rpt_units_velocity.findText(system["velocity"])
        self.cbo_rpt_units_velocity.setCurrentIndex(idx)

        idx = self.cbo_rpt_units_diameter.findText(system["diameter"])
        self.cbo_rpt_units_diameter.setCurrentIndex(idx)

    def pattern_editor(self):
        pattern_dialog = GraphDialog(self, self.iface.mainWindow(), self.params, edit_type=GraphDialog.edit_patterns)
        pattern_dialog.exec_()

    def curve_editor(self):

        curve_dialog = GraphDialog(self, self.iface.mainWindow(), self.params, edit_type=GraphDialog.edit_curves)
        curve_dialog.exec_()

    def tags_editor(self):

        tags_dialog = TagsDialog(self, self.iface.mainWindow(), self.params)
        tags_dialog.exec_()



    def project_new_clicked(self):

        self.btn_project_new.setChecked(False)

        file_dialog = QFileDialog()
        file_dialog.setWindowTitle('New project')
        file_dialog.setLabelText(QFileDialog.Accept, 'Create')
        file_dialog.setNameFilter('Inp files (*.inp)')
        if file_dialog.exec_():

            inp_file_path = file_dialog.selectedFiles()[0]
            if not inp_file_path.lower().endswith('.inp'):
                inp_file_path += '.inp'

            self.inp_file_path = inp_file_path
            self.params.last_project_dir = os.path.dirname(inp_file_path)

            lay_utils.remove_layers(self.params)

            # Request CRS for layers
            self.crs_selector()
            self.create_layers(None, self.params.crs)

            self.txt_prj_file.setText(self.inp_file_path)

            # Prompt for hydaulic options
            # if self.hydraulics_dialog is None:
            #     self.hydraulics_dialog = HydraulicsDialog(self, self.params, True)
            # self.hydraulics_dialog.show()

    def project_load_clicked(self):

        self.btn_project_load.setChecked(False)

        inp_file_path, __ = QFileDialog.getOpenFileName(self, 'Open inp file', self.params.last_project_dir, 'Inp files (*.inp)')

        if inp_file_path is not None and inp_file_path:
            self.inp_file_path = inp_file_path

            self.txt_prj_file.setText(self.inp_file_path)
            self.params.last_project_dir = os.path.dirname(inp_file_path)
            self.read_inp_file(False)

    def read_inp_file(self, hydraulics_dialog=True):

        # Request CRS for layers
        self.crs_selector()

        # Read inp file
        if os.path.isfile(self.inp_file_path):

            try:

                QApplication.setOverrideCursor(Qt.WaitCursor)

                inp_reader = InpReader(self.inp_file_path)
                new_layers_d = inp_reader.read(self.params)

                lay_utils.remove_layers(self.params)

                self.create_layers(new_layers_d, self.params.crs)
                self.count_elements()

                if not new_layers_d:
                    if hydraulics_dialog:
                        pass
                        # Prompt for hydaulic options
                        # if self.hydraulics_dialog is None:
                        #     self.hydraulics_dialog = HydraulicsDialog(self, self.params, True)
                        # self.hydraulics_dialog.show()

            finally:

                QApplication.restoreOverrideCursor()

    def project_save_clicked(self):

        self.btn_project_save.setChecked(False)

        try:
            QApplication.setOverrideCursor(Qt.WaitCursor)

            inp_file = InpFile()
            inp_file.write_inp_file(self.params, self.inp_file_path, '')

            QApplication.restoreOverrideCursor()


            self.iface.messageBar().pushMessage(
                Parameters.plug_in_name,
                'Project saved.',
                Qgis.Info,
                5)  # TODO: softcode

        finally:
            QApplication.restoreOverrideCursor()

    def project_saveas_clicked(self):

        self.btn_project_saveas.setChecked(False)

        inp_file_path, __ = QFileDialog.getSaveFileName(
            self, 'Save project as...', self.params.last_project_dir, 'INP files (*.inp)')

        if inp_file_path is not None and inp_file_path:
            self.inp_file_path = inp_file_path
            self.txt_prj_file.setText(self.inp_file_path)

            try:
                QApplication.setOverrideCursor(Qt.WaitCursor)
                inp_file = InpFile()
                inp_file.write_inp_file(self.params, self.inp_file_path, '')
                QApplication.restoreOverrideCursor()

                self.iface.messageBar().pushMessage(
                    Parameters.plug_in_name,
                    'Project saved.',
                    Qgis.Info,
                    5)  # TODO: softcode

            finally:
                QApplication.restoreOverrideCursor()

    def btn_xpss_run_clicked(self):

        config_file = ConfigFile(Parameters.config_file_path)
        if self.inp_file_path is None:
            self.inp_file_path, __ = QFileDialog.getOpenFileName(
                self,
                'Select INP file',
                config_file.get_last_inp_file(),
                'INP files (*.inp)')

        if self.inp_file_path is not None and self.inp_file_path != '':

            # Remove previous output layers
            for out_layer in self.params.out_layers:
                lay_utils.remove_layer(out_layer)

            config_file.set_last_inp_file(self.inp_file_path)
            # driver = SolverFactory(self).create(self.cbo_solver.currentText())
            #
            rpt_file = os.path.splitext(self.inp_file_path)[0] + '.rpt'
            out_binary_file = os.path.splitext(self.inp_file_path)[0] + '.out'
            #
            # driver.run()
            driver = Driver(self)

            driver.run()

            # Open log
            if not os.path.isfile(rpt_file):
                QMessageBox.warning(
                    self,
                    Parameters.plug_in_name,
                    rpt_file + u' not found!',  # TODO: softcode
                    QMessageBox.Ok)
                return

            self.log_dialog = LogDialog(self.iface.mainWindow(), rpt_file)
            self.log_dialog.exec_()

    def btn_xpss_output_clicked(self):
        if self.output_dialog is None:
            self.output_dialog = OutputAnalyserDialog(self.iface, self.iface.mainWindow(), self.params)
        self.output_dialog.setVisible(True)

    def update_layers_combos(self):

        # prev_dem_lay_id = self.cbo_dem.itemData(self.cbo_dem.currentIndex())
        prev_dem_lay_text = self.get_combo_current_text(self.cbo_dem)

        self.cbo_dem.clear()
        self.cbo_dem.addItem('', None)

        layers = QgsProject.instance().mapLayers()
        raster_count = 0

        for id, layer in layers.items():
            if layer is not None:
                if QgsMapLayer is not None:
                    if layer.type() == QgsMapLayer.RasterLayer:
                        raster_count += 1
                        self.cbo_dem.addItem(layer.name(), layer.id())

        self.set_layercombo_index(self.cbo_dem, prev_dem_lay_text)

    def preselect_layers_combos(self):

        for layer_id in QgsProject.instance().mapLayers():

            layer = QgsProject.instance().mapLayer(layer_id)

            names = ['dtm', 'dem']
            if any([x.lower() in QgsProject.instance().mapLayer(layer_id).name().lower() for x in names]):
                self.params.dem_rlay = layer
                self.set_layercombo_index(self.cbo_dem, layer.name())

    def apply_symbologies(self):

        if self.params.junctions_vlay is not None:
            ns = symbology.NodeSymbology()
            renderer = ns.make_simple_node_sym_renderer(2)
            self.params.junctions_vlay.setRenderer(renderer)

        if self.params.reservoirs_vlay is not None:
            ns = symbology.NodeSymbology()
            renderer = ns.make_svg_node_sym_renderer(self.params.reservoirs_vlay, misc.reservoir_icon_svg_name, 7)
            self.params.reservoirs_vlay.setRenderer(renderer)

        if self.params.tanks_vlay is not None:
            ns = symbology.NodeSymbology()
            renderer = ns.make_svg_node_sym_renderer(self.params.tanks_vlay, misc.tank_icon_svg_name, 7)
            self.params.tanks_vlay.setRenderer(renderer)

        if self.params.pipes_vlay is not None:
            ls = symbology.LinkSymbology()
            renderer = ls.make_simple_link_sym_renderer()
            self.params.pipes_vlay.setRenderer(renderer)

        if self.params.pumps_vlay is not None:
            ls = symbology.LinkSymbology()
            renderer = ls.make_svg_link_sym_renderer(misc.pump_icon_svg_name, 7)
            self.params.pumps_vlay.setRenderer(renderer)

        if self.params.valves_vlay is not None:
            ls = symbology.LinkSymbology()
            renderer = ls.make_svg_link_sym_renderer(misc.valve_icon_svg_name, 7)
            self.params.valves_vlay.setRenderer(renderer)

        symbology.refresh_layer(self.iface.mapCanvas(), self.params.junctions_vlay)
        symbology.refresh_layer(self.iface.mapCanvas(), self.params.reservoirs_vlay)
        symbology.refresh_layer(self.iface.mapCanvas(), self.params.tanks_vlay)
        symbology.refresh_layer(self.iface.mapCanvas(), self.params.pipes_vlay)
        symbology.refresh_layer(self.iface.mapCanvas(), self.params.pumps_vlay)
        symbology.refresh_layer(self.iface.mapCanvas(), self.params.valves_vlay)

    # def update_drivers_combo(self):
    #     self.cbo_solver.clear()
    #     for driver in SolverFactory._registry.keys():
    #         self.cbo_solver.addItem(driver)

    def update_flow_units_combo(self, cbo):
        cbo.clear()
        for unit in FlowUnits.keys():
            cbo.addItem(str(unit))

    def update_pressure_units_combo(self, cbo):
        cbo.clear()
        for unit in PressureUnits.keys():
            cbo.addItem(str(unit))

    def update_length_units_combo(self, cbo):
        cbo.clear()
        for unit in LengthUnits.keys():
            cbo.addItem(str(unit))

    def update_combo_from_factory_method(self, cbo, factorymethod):
        cbo.clear()
        for driver in factorymethod.registry.keys():
            cbo.addItem(driver)

    def update_pipe_diameter_combo(self, cbo, material, schedule, unitStr):
        cbo.clear()
        sch = self.pipedb.get(material, schedule)
        units = LengthUnits[sch.baseunits]
        logger.debugger("unitStr: "+str(unitStr))
        for dia in sch.diameters.keys():
            logger.debugger("dia: "+str(dia))
            displayDia = (dia*units).to(LengthUnits[unitStr]).magnitude
            cbo.addItem("{:.2f}".format(displayDia))

    def update_velocity_units_combo(self, cbo):
        cbo.clear()
        for unit in VelocityUnits.keys():
            cbo.addItem(str(unit))



    def update_pipe_material_combo(self, cbo, cbo_units):
        cbo.clear()

        for material in self.pipedb.materials.keys():
            cbo.addItem(material)


        for unit in LengthUnits:
            cbo_units.addItem(str(unit))

    def update_pipe_schedule_combo(self, cbo, material):
        cbo.clear()

        for sch in self.pipedb.materials[material].schedules.keys():
            cbo.addItem(sch)


    def update_friction_loss_eq_combo(self):
        self.cbo_friction_loss_eq.clear()

        for eq in FlowHeadRelationsFactory.registry.keys():
            self.cbo_friction_loss_eq.addItem(eq)

    def update_op_edu_method_combo(self):
        self.cbo_op_edu_method.clear()

        for method in OpEduMethodFactory.registry.keys():
            self.cbo_op_edu_method.addItem(method)

    def select_pipedb_path_clicked(self):

        #self.btn_project_load.setChecked(False)

        db_file_path, __ = SelectFolderDialog.getOpenFileName(self, 'Open inp file', self.params.last_project_dir, 'Inp files (*.inp)')

        self.le_db_folder.setText(db_file_path)


    def get_combo_current_data(self, combo):
        index = combo.currentIndex()
        return combo.itemData(index)

    def get_combo_current_text(self, combo):
        return combo.currentText()

    def set_layercombo_index(self, combo, combo_text):
        index = combo.findText(combo_text)
        if index >= 0:
            combo.setCurrentIndex(index)
        else:
            if combo.count() > 0:
                combo.setCurrentIndex(0)

    def pipe_vertex_dist_changed(self, vertex_dist):
        if vertex_dist is not None and vertex_dist:
            self.params.vertex_dist = float(vertex_dist)

    def find_decimals(self, float_value):
        float_string = str(float_value)
        float_string.replace(',', '.')
        if '.' in float_string:
            decimals = len(float_string[float_string.index('.'):])
        else:
            decimals = 1
        return decimals

    # def update_roughness_params(self, roughness_range):
    #
    #     min_roughness = roughness_range[0]
    #     max_roughness = roughness_range[1]
    #
    #     self.decimals = max(self.find_decimals(min_roughness), self.find_decimals(max_roughness))
    #
    #     min_roughness_mult = min_roughness * 10 ** self.decimals
    #     max_roughness_mult = max_roughness * 10 ** self.decimals
    #
    #     # If US units and D-W, convert mm to feet*10-3
    #     if self.params.options.headloss == Options.headloss_dw and self.params.options.units == Options.unit_sys_us:
    #         min_roughness = min_roughness / 304.8 * 1000
    #         max_roughness = max_roughness / 304.8 * 1000
    #
    #     # To string
    #     self.lbl_pipe_roughness_min.setText(str(min_roughness))
    #     self.lbl_pipe_roughness_max.setText(str(max_roughness))
    #     self.lbl_pipe_roughness_val_val.setText(str(min_roughness))
    #
    #     # Multipliers
    #     self.sli_pipe_roughness.setMinimum(min_roughness_mult)
    #     self.sli_pipe_roughness.setMaximum(max_roughness_mult)
    #     self.sli_pipe_roughness.setValue(min_roughness_mult)

    def update_roughness_params(self):

        flowheadrelation = self.cbo_friction_loss_eq.currentText()
        material = self.cbo_pipe_mtl.currentText()

        material = self.pipedb.materials[material]

        if flowheadrelation == "DarcyWeisbach":
            roughness = str(material.roughness)
            roughness_lbl = "Roughness"
            roughness_unit = str(material.roughness_unit.units)
        elif flowheadrelation == 'HazenWilliams':
            roughness = "{:.1f}".format(material.cfactor)
            roughness_lbl = "C Factor"
            roughness_unit = " "
        else:
            logger.error("Unknown friction loss relation.")

        self.lbl_roughness.setText(roughness_lbl)
        self.txt_roughness.setText(roughness)
        self.txt_roughness_unit.setText(roughness_unit)

    def update_epa_coeff_status(self):
        if self.cbo_op_edu_method.currentText() == 'EPA':
            self.frm_epa.setEnabled(True)
        else:
            self.frm_epa.setEnabled(False)

    def set_cursor(self, cursor_shape):
        cursor = QtGui.QCursor()
        cursor.setShape(cursor_shape)
        self.iface.mapCanvas().setCursor(cursor)

    def crs_selector(self):

        # Request CRS for layers
        proj_selector = QgsProjectionSelectionDialog()
        proj_selector.exec_()
        # crs = QgsCoordinateReferenceSystem(proj_id)
        self.params.crs = proj_selector.crs()

class NewFileDialog(QFileDialog):
    def __init__(self):
        super(NewFileDialog, self).__init__()

        self.setWindowTitle('Pick a name for your project...')
        self.setFileMode(QFileDialog.AnyFile)
        self.setLabelText(QFileDialog.Accept, 'OK')

    def accept(self):
        try:
            file_path = self.selectedFiles()[0]
            if os.path.isfile(file_path):
                ret = QtGui.QMessageBox.question(
                    self.iface.mainWindow(),
                    Parameters.plug_in_name,
                    u'The file already exists. Overwrite?',
                    # TODO: softcode
                    QtGui.QMessageBox.Yes | QtGui.QMessageBox.No)

                if ret == QtGui.QMessageBox.No:
                    return
            QFileDialog.accept(self)

        except Exception as e:
            # fix_print_with_import
            print(e)
            return

class SelectFolderDialog(QFileDialog):
    def __init__(self):
        super(NewFileDialog, self).__init__()

        self.setWindowTitle('Select location of database files...')
        self.setFileMode(QFileDialog.Directory)
        self.setLabelText(QFileDialog.Accept, 'OK')

        QFileDialog.accept(self)

    # def accept(self):
    #     try:
    #         file_path = self.selectedFiles()[0]
    #         if os.path.isfile(file_path):
    #             ret = QtGui.QMessageBox.question(
    #                 self.iface.mainWindow(),
    #                 Parameters.plug_in_name,
    #                 u'The file already exists. Overwrite?',
    #                 # TODO: softcode
    #                 QtGui.QMessageBox.Yes | QtGui.QMessageBox.No)
    #
    #             if ret == QtGui.QMessageBox.No:
    #                 return
    #         QFileDialog.accept(self)
    #
    #     except Exception as e:
    #         # fix_print_with_import
    #         print(e)
    #         return

class MyQFileDialog(QFileDialog):
    def __init__(self):
        super(MyQFileDialog, self).__init__()

    def accept(self):

        try:
            file_path = self.selectedFiles()[0]
            if not os.path.isfile(file_path):
                if not file_path.lower().endswith('.inp'):
                    file_path += '.inp'
                f = open(file_path, 'w')
                f.close()
            QFileDialog.accept(self)
        except Exception as e:
            # fix_print_with_import
            print(e)
            return
