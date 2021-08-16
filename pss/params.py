from .db.units import LengthUnits, VelocityUnits, FlowUnits

class PSSParams:
    def __init__(self, dockwidget):

        self.elevUnits = dockwidget.cbo_dem_units.currentText()

        self.pumpDbLoc = dockwidget.txt_pump_db.text()
        self.pipeDiaDbLoc = dockwidget.txt_pipe_db.text()
        self.pipeRghDbLoc = dockwidget.txt_pipe_rgh_db.text()
        self.opEduTableLoc = dockwidget.txt_op_edu_table.text()

        self.pipeMaterial = dockwidget.cbo_pipe_mtl.currentText()
        self.pipeSchedule = dockwidget.cbo_pipe_sch.currentText()
        self.pumpStationDepth = float(dockwidget.txt_station_depth.text())
        self.pumpStationDepth *= LengthUnits[
            dockwidget.cbo_depth_units.currentText()]
        self.pumpStationDepth = self.pumpStationDepth.to_base_units()
        self.checkPipeConns = dockwidget.chk_check_pipes.isChecked()
        self.checkNodeConns = dockwidget.chk_check_nodes.isChecked()

        self.solver = dockwidget.cbo_solver.currentText()
        self.flowrate = float(dockwidget.txt_flowrate.text())
        self.flowrate *= FlowUnits[dockwidget.cbo_flow_units.currentText()]
        self.flowrate = self.flowrate.to_base_units()
        self.minV = float(dockwidget.txt_min_vel.text())
        self.minV *= VelocityUnits[dockwidget.cbo_min_vel_units.currentText()]
        self.minV = self.minV.to_base_units()
        self.maxV = float(dockwidget.txt_max_vel.text())
        self.maxV *= VelocityUnits[dockwidget.cbo_max_vel_units.currentText()]
        self.maxV = self.maxV.to_base_units()
        self.lossEqn = dockwidget.cbo_friction_loss_eq.currentText()
        self.opEduCalcMethod = dockwidget.cbo_op_edu_method.currentText()
        self.epaA = float(dockwidget.txt_epa_a.text())
        self.epaB = float(dockwidget.txt_epa_b.text())
        self.nomDiaMethod = dockwidget.cbo_dia_method.currentText()
        self.latConnMaterial = dockwidget.cbo_lat_pipe_mtl.currentText()
        self.latConnPipeSch = dockwidget.cbo_lat_pipe_sch.currentText()
        self.latConnDia = float(dockwidget.cbo_lat_pipe_dia.currentText())
        self.latConnDiaUnits = dockwidget.cbo_lat_pipe_dia_units.currentText()

        self.logoLoc = dockwidget.txt_logo.text()
        self.reportContents = {
            "systemLayout": dockwidget.chk_layout.isChecked(),
            "pipeLabels": dockwidget.chk_pipe_lbl.isChecked(),
            "nodeLabels": dockwidget.chk_node_lbl.isChecked(),
            "resultsTable": dockwidget.chk_table_summary.isChecked(),
            "resultsMap": dockwidget.chk_results_map.isChecked()
        }
        self.reportUnits = {
            "length": dockwidget.cbo_rpt_units_pipe_length.currentText(),
            "diameter": dockwidget.cbo_rpt_units_diameter.currentText(),
            "pressure": dockwidget.cbo_rpt_units_pressure.currentText(),
            "flow": dockwidget.cbo_rpt_units_flow.currentText(),
            "velocity": dockwidget.cbo_rpt_units_velocity.currentText()
        }
