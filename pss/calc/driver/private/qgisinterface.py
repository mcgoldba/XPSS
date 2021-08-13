def update_vlay(pssvars):
    """Updates vector layer from pss calculation data"""
    
#        layers = QgsMapLayerRegistry.instance().mapLayersByName(self.params.pipes_vlay_name)
#        layer = layers[0]
#        it = layer.getFeatures()
    layer = self.params.pipes_vlay
    it = layer.getFeatures()

    # replace any spaces in the material with an underscore since the EPANET file is space delimited
    #l_material = l_material.replace(" ", "_")

    layer.startEditing()

    for i, feat in enumerate(it):
        length =  pssvars.pipeProps.loc[i, 'Length [ft]']
        #self.log_progress(str(length))
        diameter =  pssvars.d[i]
        #self.log_progress(str(diameter))
        num_edu =  pssvars.nEDU[i]
        #self.log_progress(str(num_edu))
        pipe_id = pssvars.pipeProps.loc[i, 'Pipe ID']
        #self.log_progress(str(pipe_id))
        #if Pipe_props.loc[i, 'Zone ID']:
        #TODO: Implement zones
        if 'Zone ID' in pssvars.pipeProps.columns:
            zone_id = int(pssvars.pipeProps.loc[i, 'Zone ID'])
        else:
            zone_id=0
        #self.log_progress("zone id: "+str(zone_id))
        velocity = pssvars.v[i]
        frictionloss = pssvars.fl[i]

        data = [str(pipe_id), str(length), str(diameter), 'OPEN', str(C_factor), "0", self.PipeMaterialName[l_material], "", "", str(num_edu), str(zone_id), "{:.2f}".format(velocity), "{:.2f}".format(frictionloss)]

        #self.log_progress(str(data))

        for j in range(len(data)):
            #self.log_progress(str(j))
            layer.changeAttributeValue(feat.id(), j, data[j])

    layer.commitChanges()
