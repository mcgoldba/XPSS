from XPSS.logger import Logger

logger = Logger(debug=True)

def update_vlay(pssvars):

    _update_pipes_vlay(pssvars)
    _update_junctions_vlay(pssvars)

def _update_pipes_vlay(pssvars):
    """Updates the pipe vector layer with pss calculation data"""

    units = pssvars.params.reportUnits

    layer = pssvars.qgisparams.pipes_vlay
    it = layer.getFeatures()

    layer.startEditing()

    logger.debugger("velocity:\n"+str(pssvars.data.v))
    logger.debugger("friction loss:\n"+str(pssvars.data.fl))

    for i, feat in enumerate(it):
        length =  pssvars.data.L[i][0].to(units['length']).magnitude
        length_units = pssvars.data.L[i][0].units
        #logger.debugger(str(length))
        diameter =  pssvars.data.d[i][0].to(units['diameter']).magnitude
        diameter_units = pssvars.data.d[i][0].units
        #logger.debugger(str(diameter))
        num_edu =  pssvars.data.nEDU[i][0]
        #logger.debugger(str(num_edu))
        pipe_id = pssvars.pipeProps.loc[i, 'Pipe ID']
        #logger.debugger(str(pipe_id))
        #if Pipe_props.loc[i, 'Zone ID']:
        #TODO: Implement zones
        if 'Zone ID' in pssvars.pipeProps.columns:
            zone_id = int(pssvars.pipeProps.loc[i, 'Zone ID'])
        else:
            zone_id=0
        #pssvars.log_progress("zone id: "+str(zone_id))
        velocity = pssvars.data.v[i][0].to(units["velocity"]).magnitude
        velocity_units = pssvars.data.v[i][0].units
        frictionloss = pssvars.data.fl[i][0].to(units["pressure"]).magnitude
        frictionloss_units = pssvars.data.fl[i][0].units
        logger.debugger("frictionloss_units: "+str(frictionloss_units))
        if pssvars.params.lossEqn == 'HazenWilliams':
            roughness = pssvars.data.C[i]
        elif pssvars.params.lossEqn == 'DarcyWeisbach':
            roughness = pssvars.data.roughness[i]
        else:
            logger.error("Invalid friction loss equation specified.")
        material = pssvars.data.matl[i][0]
        #logger.debugger("material: "+str(material))


        data = [str(pipe_id), str(length), str(diameter), 'OPEN', str(roughness),
                 "0", material, "", "", str(num_edu), str(zone_id),
                 "{:.2f}".format(velocity), "{:.2f}".format(frictionloss),
                 str(length_units), str(diameter_units), str(velocity_units),
                 str(frictionloss_units)]

        #pssvars.log_progress(str(data))

        for j in range(len(data)):
            #pssvars.log_progress(str(j))
            layer.changeAttributeValue(feat.id(), j, data[j])

    layer.commitChanges()

def _update_junctions_vlay(pssvars):  #INCOMPLETE
    """Updates the junctions vector layer with pss calculation data"""

    units = pssvars.params.reportUnits

    layer = pssvars.qgisparams.junctions_vlay
    it = layer.getFeatures()


    layer.startEditing()

    for i, feat in enumerate(it):
        junc_id =  pssvars.nodeProps.loc[i, 'Node ID']
        elev =  pssvars.nodeProps.loc[i, 'Elevation [ft]']
        #zone_end =  Node_props.loc[i, 'Zone End']
        zone_end = 0 #TODO: Implement zones
        pressure =  pssvars.data.p[i][0].to(units["pressure"]).magnitude
        pressure_units =  pssvars.data.p[i][0].units
        #self.log_progress(str(length))

        data = [str(junc_id), "{:.2f}".format(elev), "0", "", "0", "0", "", "",
                "{:.0f}".format(zone_end), "{:.2f}".format(pressure),
                str(pressure_units)]

        #self.log_progress(str(data))

        for j in range(len(data)):
            #self.log_progress(str(j))
            layer.changeAttributeValue(feat.id(), j, data[j])

    layer.commitChanges()
