from PyQt5.QtCore import *
from PyQt5.QtGui import *
from qgis.core import *
import qgis.utils
from qgis.utils import iface
from qgis.gui import QgsMessageBar
import sys
import numpy as np
import pandas as pd
from scipy import interpolate
import os


from qepanet.model.network import *       #Pipe, Reservoir, Junction, etc.  variables are defined here
from qepanet.model.network_handling import NetworkUtils
from qepanet.model.inp_writer import InpFile
from qepanet.tools.parameters import Parameters

DEBUG = True

from XPSS.pipedatabase import PipeMaterial, PipeClass
from XPSS.pss import PSS


class DataMod(PSS):
    PipeMaterialName = {}
    PipeMaterialName[PipeMaterial.PVC] = 'PVC'
    PipeMaterialName[PipeMaterial.HDPE] = 'HDPE'
    PipeClassName = {}
    PipeClassName[PipeClass.PVC_Sch40] = 'PVC Sch. 40'
    PipeClassName[PipeClass.HDPE_DR11] = 'HDPE DR11'


    def __init__(self):
        self.qepa = qgis.utils.plugins["qepanet"]
        self.params = self.qepa.params  #refer to the parameters stored in the existing instance of qepanet
        self.pipe_fts = pd.DataFrame(self.params.pipes_vlay.getFeatures(),columns=[field.name() for field in self.params.pipes_vlay.fields() ])  #extract pipe attribute table as a pandas array
        self.junc_fts = pd.DataFrame(self.params.junctions_vlay.getFeatures(),columns=[field.name() for field in self.params.junctions_vlay.fields() ])  #extract pipe attribute table as a pandas array
        self.res_fts = pd.DataFrame(self.params.reservoirs_vlay.getFeatures(),columns=[field.name() for field in self.params.reservoirs_vlay.fields() ])  #extract pipe attribute table as a pandas array


        self.lengthUnits = None



    def check(self, check_pipe_conns, check_node_conns):
        #TODO:  rewrite to use a pandas dataframe

        sindex = QgsSpatialIndex()
        pipe_fts = self.params.pipes_vlay.getFeatures()
        junc_fts = self.params.junctions_vlay.getFeatures()
        res_fts = self.params.reservoirs_vlay.getFeatures()
        tank_fts = self.params.tanks_vlay.getFeatures()
        pump_fts = self.params.pumps_vlay.getFeatures()

        self.log_progress("%%%%%%%%%%% BEGIN CHECK OF PSS SYSTEM %%%%%%%%%%%")

        #get system details from the qgis vector layers (a lot of this taken from in_writer.py in qepanet)

        #self.log_progress("pipe_lst: "+str(np.asarray(pipe_lst).shape))

        # Build nodes spatial index
        #sindex = QgsSpatialIndex()
        res = []
        j=0
        r=0
        t=0
        l=0
        p=0

        has_error = False
        num_entity_err = False
        self.log_progress("Summary of System Components:")
        for feat in junc_fts:
            sindex.addFeature(feat)
            j+=1
        self.log_progress(str(j)+" Junctions")
        for feat in res_fts:
            sindex.addFeature(feat)
            res.append(feat.attribute(Reservoir.field_name_eid))
            r+=1
        self.log_progress(str(r)+" Reservoirs")
        for feat in tank_fts:
            sindex.addFeature(feat)
            t+=1
        self.log_progress(str(t)+" Tanks")
        for feat in pipe_fts:
            l+=1
        self.log_progress(str(l)+" Pipes")
        for feat in pump_fts:
            p+=1
        self.log_progress(str(p)+" Pumps")

        if len(res) != 1:        #check to see if there is a single reservoir.  Analysis assumes that all end nodes are pumps pump to a single outlet
            self.log_error("The number of reserviors in the network must equal 1.")
            has_error = True

        if j != l:        #check to see if the number of pipes equals the number of junctions.  This is true for a directed tree graph with a reservior as its end node.
            self.log_error("The number of junctions is not equal to the number of pipes.")
            #has_error = True  #commented to continue calc to get a more detailed error in "create_conn_matrix()
            num_entity_err = True

        #reset QGIS iterators
        pipe_fts = self.params.pipes_vlay.getFeatures()
        junc_fts = self.params.junctions_vlay.getFeatures()
        res_fts = self.params.reservoirs_vlay.getFeatures()
        tank_fts = self.params.tanks_vlay.getFeatures()
        pump_fts = self.params.pumps_vlay.getFeatures()

        node_lst = [junc_fts, res_fts, tank_fts]
        node_Class = [Junction, Reservoir, Tank]

        pipe_lst = [pipe_fts, pump_fts]
        pipe_Class = [Pipe, Pump]


        disconn_pipes = []
        disconn_juncs = []

        if check_pipe_conns is True:
            self.log_progress("Cycling through all pipes to check connections...")  #TODO:  This is not working properly

            Pipe_nodes = []  #List of start and end nodes for each pipe

            all_pipes = []

            #TODO:  update to include all layers and check if each layer is valid

            for i in range(len(pipe_lst)):
                for ft in pipe_lst[i]:

                    #self.log_progress("Checking pipe connection...")

                    eid = ft.attribute(pipe_Class[i].field_name_eid)

                    if num_entity_err == True:
                        all_pipes.append(eid)

                    #sindex = self.params.nodes_sindex
                    # Find start/end nodes
                    adj_nodes = NetworkUtils.find_start_end_nodes_sindex(self.params, sindex, ft.geometry())

                    #adj_nodes = NetworkUtils.find_start_end_nodes(self.params, ft.geometry())  #TODO:  Determine why the 'sindex' version does not work


                    found_nodes = []

                    try:
                        start_node_id = adj_nodes[0].attribute(Junction.field_name_eid)  #TODO:  Get Reservoir eid name in case it is different.
                        end_node_id = adj_nodes[1].attribute(Junction.field_name_eid)

                        found_nodes.append(start_node_id)
                        found_nodes.append(end_node_id)

                        if start_node_id == end_node_id:
                            self.log_error("Pipe "+eid+" is connected to itself.  Connected nodes are "+start_node_id+" and "+end_node_id+".")
                            has_error = True

                        #check for any very short pipes:  #TODO:  This is not working correctly
                        short_pipes_nodes = []
                        if float(ft.attribute(Pipes.field_name_length)) < 2: #TODO:  units are assumed to be ft
                            self.log_error("Pipe "+eid+" is very short.  Connected nodes are"+start_node_id+" and "+end_node_id+".")
                            if len(short_pipes) != 0:
                                start_node = False
                                end_node = False
                                for i in range(len(short_pipes_nodes)):
                                    if start_node_id == short_pipe_nodes[i]:
                                        short_pipe_nodes.append(start_node_id)
                                        start_node = True
                                    if end_node_id == short_pipe_nodes[i]:
                                        short_pipe_nodes.append(end_node_id)
                                        end_node == True
                                    if (start_node == True) and (end_node == True):
                                        break

                            has_error = True

                        if len(short_pipe_nodes) > 0:
                            self.select_qgis_feature(self.params.junctions_vlay, short_pipe_nodes)

                        Pipe_nodes.append([eid, start_node_id, end_node_id])

                    except:
                        print_str = "Connected nodes are"
                        found_node = False
                        if start_node_id:
                            print_str += " "+start_node_id
                            found_node = True
                        if end_node_id:
                            print_str += " "+end_node_id
                            found_node = True
                        if found_node is False:
                            print_str = "No nodes were found for pipe"
                        self.log_error("Pipe "+eid+" has less than 2 nodes connected.  "+print_str+".")
                        disconn_pipes.append(eid)
                        has_error = True

            if len(disconn_pipes) > 0:
                self.select_qgis_features(self.params.pipes_vlay, disconn_pipes)  #TODO:  assumes the vector layer is Pipes

        else:
            self.log_progress("Pipe connection checks were not performed.")

            #self.log_progress(str(Pipe_nodes))
        if check_node_conns is True:
            self.log_progress("Cycling through all nodes to check connections...") #TODO:  This is not working properly

            for i in range(len(node_lst)):
                for ft in node_lst[i]:
                    #self.log_progress("Checking node connection...")
                    num_conn = 0
                    eid = ft.attribute(node_Class[i].field_name_eid)
                    for j in range(len(found_nodes)):
                        if found_nodes[j] == eid:
                            num_conn += 1
                    self.log_progress("Connections for Node "+eid+": "+str(num_conn))
                    if num_conn == 0:
                        self.log_error("The node "+eid+" is not connected to any pipes.")
                        disconn_juncs.append(eid)
                        has_error = True

            if len(disconn_juncs) > 0:
                self.select_qgis_features(self.params.junctions_vlay, disconn_juncs)  #TODO:  assumes the vector layer is Junctions
        else:
            self.log_progress("Node connection checks were not performed.")

        if num_entity_err:
            self.log_progress("An Error was found!  The number of pipes does not match the number of junctions.  Additional details will be provided after parsing through the system.")

        elif has_error == True:
            self.log_error("Error(s) were found.  Check the system definition and correct.", stop=True)

        else:
            self.log_progress("There are no errors found in the system!")


        self.log_progress("%%%%%%%%%%% END CHECK OF PSS SYSTEM %%%%%%%%%%%")


        return [has_error, num_entity_err, l, j]


    def initialize_from_qepanet(self):

        #get system details from the qgis vector layers (a lot of this taken from in_writer.py in qepanet)


        #Initalize data Matrices and vectors for calculations

        C = []  #Connection matrix:  describes how each pipe the pipes are connected together
        Pipe_props_raw = []  #Pipe Property Matrix:  stores properties of each pipes as
                        # [ id ]
        Pipe_nodes_raw = []  #Pipe Nodes:  stores pipe start and end nodes to build thet connection matrix
        Node_props_raw = []  #Node Property Matrix:  stores properties of each junction as
                        # [ id, elev, zone_end ]

        # Build nodes spatial index
        sindex = QgsSpatialIndex()
        res = []
        res_elev=[]
        j=0
        r=0
        t=0

        pipe_fts = self.params.pipes_vlay.getFeatures()
        junc_fts = self.params.junctions_vlay.getFeatures()
        res_fts = self.params.reservoirs_vlay.getFeatures()
        tank_fts = self.params.tanks_vlay.getFeatures()
        pump_fts = self.params.pumps_vlay.getFeatures()

        for feat in junc_fts:
            sindex.addFeature(feat)
            j+=1
        for feat in res_fts:
            sindex.addFeature(feat)
            res.append(feat.attribute(Reservoir.field_name_eid))
            res_elev.append(feat.attribute(Reservoir.field_name_elev))
            r+=1
        #self.log_progress("Reservoir: "+str(res))
        for feat in tank_fts:
            sindex.addFeature(feat)
            t+=1

        if len(res) != 1:        #check to see if there is a single reservoir.  Analysis assumes that all end nodes are pumps pump to a single outlet
            self.log_error("The number of reserviors in the network must equal 1.")


        for pipe_ft in pipe_fts:


            eid = pipe_ft.attribute(Pipe.field_name_eid)

            # Find start/end nodes
            # adj_nodes = NetworkUtils.find_start_end_nodes(params, pipe_ft.geometry())
            adj_nodes = NetworkUtils.find_start_end_nodes_sindex(self.params, sindex, pipe_ft.geometry())

            start_node_id = adj_nodes[0].attribute(Junction.field_name_eid)
            end_node_id = adj_nodes[1].attribute(Junction.field_name_eid)

            Pipe_nodes_raw.append([eid, start_node_id, end_node_id])

            #length = pipe_ft.attribute(Pipe.field_name_length)
            #diameter = pipe_ft.attribute(Pipe.field_name_diameter)
            #roughness = pipe_ft.attribute(Pipe.field_name_roughness)
            #minor_loss = pipe_ft.attribute(Pipe.field_name_minor_loss)
            #status = pipe_ft.attribute(Pipe.field_name_status)
            #description = pipe_ft.attribute(Pipe.field_name_description)
            #tag_name = pipe_ft.attribute(Pipe.field_name_tag)
            #num_edu = pipe_ft.attribute(Pipe.field_name_num_edu)

            Pipe_props_raw.append([eid])

        #reset the iterator for junc_fts
        junc_fts = self.params.junctions_vlay.getFeatures()

        for junc_ft in junc_fts:

            eid = junc_ft.attribute(Junction.field_name_eid)
            elev = junc_ft.attribute(Junction.field_name_elev)
            zone_end = junc_ft.attribute(Junction.field_name_zone_end)

            Node_props_raw.append([eid, elev, zone_end])


        Pipe_nodes = pd.DataFrame(Pipe_nodes_raw, columns = ['Pipe ID', 'Node 1 ID', 'Node 2 ID'])
        Pipe_props = pd.DataFrame(Pipe_props_raw, columns = ['Pipe ID'], dtype='float')

        Node_props = pd.DataFrame(Node_props_raw, columns = ['Node ID', 'Elevation [ft]', 'Zone End'], dtype='float')

        #self.log_progress("Node_props:\n", Node_props)

        #self.log_progress(str(Pipe_nodes))
        #self.log_progress("Node_props: \n", Node_props)
        #self.log_progress(Node_props.dtypes)
        #self.log_progress("'Pipe_nodes' and 'Pipe_props' vectors populated...")

        return [Pipe_props, Node_props, Pipe_nodes, res, res_elev]

    def get_qepanet_pipe_props(self, Pipe_props, get_lst, pd_names, sort_lst=False):

        #get_lst is the qepanet parameter field name for the attribute

        #sort_lst = map(str, sort_lst)  #convert the array of ints to an array of strings
        df = self.pipe_fts.filter(get_lst, axis=1) #extract columns from qepanet data
        df.columns = pd_names #rename the columns
        if sort_lst:
            df = df.reindex(index=sort_lst)  #rearrange the pipes within the pandas dataframe to be sorted from the Reservoir upstream
        df = df.reset_index(drop=True)  # rename indices to match those pf "Pipe_props" i.e. [0, 1, 2, 3, 4...]

        #Pipe_props, df = [d.reset_index(drop=True) for d in (Pipe_props, df)]

        Pipe_props = pd.concat([Pipe_props, df], axis=1)

        return Pipe_props

    def get_qepanet_pipe_props2(self, Pipe_props, get_lst, pd_names, calc_units=2, sort_lst=False):
        """{function}
            Initialize the Pipe_props dataframe using the derived length values of the Qgs feature

            Parameters
            ----------

            calc_units : QgsDistanceUnit (int)
                The length units to be used in XPSS calculations (default is 2 (feet))

        """
        distance = qgis.core.QgsDistanceArea()

        layer = self.params.pipes_vlay

        lyr_crs = layer.crs()

        elps = QgsProject.instance().ellipsoid()
        elps_crs = QgsCoordinateReferenceSystem()
        elps_crs.createFromUserInput(elps)
        self.log_progress("Map Ellipsoid: "+str(elps))

        #transform = iface.mapCanvas().mapSettings().transformContext()
        trans_context = QgsCoordinateTransformContext()
        trans_context.calculateDatumTransforms(lyr_crs, elps_crs)

        distance.setEllipsoid(elps)
        distance.setSourceCrs(lyr_crs, trans_context)
        units = qgis.core.QgsUnitTypes

        #get_lst is the qepanet parameter field name for the attribute

        #sort_lst = map(str, sort_lst)  #convert the array of ints to an array of strings
        #df = self.pipe_fts.filter(get_lst, axis=1) #extract columns from qepanet data
        len_ = []
        features = layer.getFeatures()
        self.log_progress("Converting from "+units.toString(units.DistanceMeters)+" to "+units.toString(calc_units)+".")
        factor = QgsUnitTypes.fromUnitToUnitFactor(units.DistanceMeters, calc_units) ## TODO: Soft code
        self.log_progress("Conversion factor: "+str(factor))

        for feature in features:
            l_calc = distance.measureLength(feature.geometry())*factor
            len_.append(l_calc)#extract length from the QgsFeature
            self.log_progress(feature['id']+": "+str(l_calc))

        Pipe_props = self.append_col_to_table(Pipe_props, len_, 'Length [ft]', data_type='float', sort=sort_lst)

        #df = pd.Dataframe(data=len_, columns=['Length [ft]'])
        #df.columns = pd_names #rename the columns
        #if sort_lst:
        #    df = df.reindex(index=sort_lst)  #rearrange the pipes within the pandas dataframe to be sorted from the Reservoir upstream
        #df = df.reset_index(drop=True)  # rename indices to match those pf "Pipe_props" i.e. [0, 1, 2, 3, 4...]
#
        ##Pipe_props, df = [d.reset_index(drop=True) for d in (Pipe_props, df)]
#
        #Pipe_props = pd.concat([Pipe_props, df], axis=1)

        return Pipe_props

    def get_qepanet_junc_props(self, Node_props, get_lst, pd_names, sort_lst=False):


        df = self.junc_fts.filter(get_lst, axis=1) #extract columns from qepanet data
        df.columns = pd_names #rename the columns
        #self.log_progress(str(sort_lst))
        if sort_lst:
            df = df.reindex(index=sort_lst)  #rearrange the pipes within the pamdas dataframe to be sorted from the Reservoir upstream
        df = df.reset_index(drop=True)  # rename indices to match those pf "Pipe_props" i.e. [0, 1, 2, 3, 4...]

        #Pipe_props, df = [d.reset_index(drop=True) for d in (Pipe_props, df)]

        Node_props = pd.concat([Pipe_props, df], axis=1)

        return Node_props

    def get_qepanet_elev_data(self, Pipe_props, Pipe_nodes_pd, sort_lst, res):

        Pipe_nodes = Pipe_nodes_pd.to_numpy()

        max_elev = -1e12 #set the initial maximum elevation to a very small value that will be overwritten
        pipe_min_elev = [0 for i in range(len(sort_lst))]
        #node_elev = [0 for i in range(len(Node_props))]
        #node_update = [0 for i in range(len(Node_props))]


        #get the minimum elevation of each pipe section
        p = -1
        for pipe in Pipe_nodes:
            p+=1
            elev = [0,0]
            for i in range(1,3):
                if pipe[i] == res[0]:
                    elev[i-1] = self.res_fts.loc[self.res_fts['id'] == pipe[i], 'elev_dem']
                    elev[i-1] = elev[i-1].iloc[0]
                    elev_out = elev[i-1]
                else:
                    elev[i-1] = self.junc_fts.loc[self.junc_fts['id'] == pipe[i], 'elev_dem']
                    elev[i-1] = elev[i-1].iloc[0]
                    #get nodes
#                    self.log_progress("Pipe: ", pipe[0])
##                    nodes = [ Pipe_nodes_pd.loc[Pipe_nodes_pd['Pipe ID']==pipe[0], 'Node 1 ID'].to_list()[0], \
##                             Pipe_nodes_pd.loc[Pipe_nodes_pd['Pipe ID']==pipe[0], 'Node 2 ID'].to_list()[0] ]
#                    self.log_progress("Node: ", pipe[i])
#                    node_index = Node_props.index[Node_props['Node ID'] == pipe[i]].to_list()[0]
#                    self.log_progress("Node_index: ", node_index)

#
#                #for j in [0,1]:
#                if node_update[node_index] == 0:
#                    node_elev[node_index] = elev[i-1]
#                    node_update[node_index] += 1

            pipe_min_elev[p] = min(elev)
            if max(elev) > max_elev:
                max_elev = max(elev)
            del elev

        #self.log_progress("Node Update Status: ", node_update)

        #check if all node elevations were updated:
        if any(i == 0 for i in node_update):
            self.log_error("Some node elevations were not updated!", stop=True)

#        min_elev_sort = []
#
#        for i in range(len(pipe_min_elev)):
#            min_elev_sort.append(pipe_min_elev[sort_lst[i]])

        #self.log_progress("Pipe_props: ", Pipe_props)
        #self.log_progress("Node_props: ", Node_props)

        Pipe_props = self.append_col_to_table(Pipe_props, pipe_min_elev, ['Minimum Elevation [ft]'], data_type="float", sort=sort_lst)

        Pipe_props = self.append_col_to_table(Pipe_props, np.subtract(max_elev,pipe_min_elev), ['Static Head [ft]'], data_type="float", sort=sort_lst)

       # Node_props = self.append_col_to_table(Node_props, node_elev, "Elevation [ft]", data_type="float")

        return [Pipe_props, Node_props, max_elev, elev_out]




    def get_pipe_elev_data(self, Pipe_props, Node_props, sort_lst, node_srt_lst, In, res_elev):
        """ {Function}
                Extracts the elevation data from the Node_props dataframe and determines the minimum elevation to display for the pipe data.  Minimum elevation is stored within the Pipe_props dataframe.
            {Variables}
                Pipe_props:
                    (Pandas Dataframe) unsorted list of pipe attributes based on ordering of QGIS features.
                Node_props:
                    (Pandas Dataframe) unsorted list of node attributes based on ordering of QGIS features.
            {Outputs}
                Pipe_props
        """


        Elevation = self.sort_dataframe(Node_props, node_srt_lst)['Elevation [ft]'].to_numpy()
        #self.log_progress("Elevation: ", Elevation)
        Elevation = np.insert(Elevation, 0, res_elev)
        #self.log_progress("Elevation: ", Elevation)

        In_ = np.ma.masked_equal(In, 0, copy=False)  # replace all 0 values with NaN

        Min_elevation = (In_.T*Elevation).T
        #self.log_progress("Min elevation: ", Min_elevation)
        #Min_elevation = np.ma.masked_equal(Min_elevation, 0, copy=False) # replace all 0 values with NaN
        #NOTE:  the above line does not work since a node can have a 0 elevation
        Min_elevation = np.amin(Min_elevation, axis=1)

        #self.log_progress("Min_elevation: ", Min_elevation)

        Elevation = Elevation.reshape((len(Elevation),-1)) #recast array as a column vector
        Min_elevation = Min_elevation.reshape((len(Min_elevation),-1)) #recast array as a column vector

        self.log_progress("Elevation shape: "+str(Elevation.shape))

        self.log_progress("In shape: "+str(In.shape))

        self.log_progress(str(Elevation[1:]))

        #- Calculate static head from the downstream node
        Elev_ds = Elevation[1:].T@(In[1:] - np.identity(len(In[1:]))) # Elevation^T * I_{SU}
        Elev_ds = Elev_ds.T
        Elev_ds[0] = res_elev

        self.log_progress("Elev_ds:\n"+str(Elev_ds))

        Static_head = -(Elevation[1:] - Elevation[0][0])
        #Static_head = -(Elev_ds - Elevation[0][0])

        #self.log_progress("Elevation: ", Elevation.shape)
        #self.log_progress("Elevation: ", Elevation)
        #self.log_progress("Min elevation: ", Min_elevation.shape)
        #self.log_progress("Min elevation: ", Min_elevation)
        #self.log_progress("Static head: ", Static_head)

        #Static_head = np.delete(Static_head, 0, axis=0)
        Min_elevation = np.delete(Min_elevation, 0, axis=0)

        self.log_progress(str(Pipe_props.shape))

        self.log_progress("Static head: "+str(Static_head))

        Pipe_props = self.append_col_to_table(Pipe_props, Min_elevation, 'Minimum Elevation [ft]', sort=sort_lst)
        Pipe_props = self.append_col_to_table(Pipe_props, Static_head, 'Static Head [ft]', sort=sort_lst)

        return [Pipe_props]

    def get_pipe_elev_data2(self, Pipe_props, Node_props, sort_lst, node_srt_lst, In, res_elev):
        """ {Function}
                Extracts the elevation data from the Node_props dataframe and determines the minimum elevation to display for the pipe data.  Minimum elevation is stored within the Pipe_props dataframe.
            {Variables}
                Pipe_props:
                    (Pandas Dataframe) unsorted list of pipe attributes based on ordering of QGIS features.
                Node_props:
                    (Pandas Dataframe) unsorted list of node attributes based on ordering of QGIS features.
            {Outputs}
                Pipe_props:
                    with added elevation data
        """
        Elevation = self.sort_dataframe(Node_props, node_srt_lst)['Elevation [ft]'].to_numpy()
        Elevation = np.insert(Elevation, 0, res_elev)

        In_ = np.ma.masked_equal(In, 0, copy=False)  # replace all 0 values with NaN

        Min_elevation = (In_.T*Elevation).T
        Min_elevation = np.amin(Min_elevation, axis=1)

        Elevation = Elevation.reshape((len(Elevation),-1)) #recast array as a column vector
        Min_elevation = Min_elevation.reshape((len(Min_elevation),-1)) #recast array as a column vector


        Static_head = self.sort_dataframe(Node_props, node_srt_lst)['Static Head [ft]'].to_numpy()

        sort_lst_inv = self.get_inv_sort_lst(sort_lst)

        Pipe_props = self.append_col_to_table(Pipe_props, Min_elevation, 'Minimum Elevation [ft]', sort=sort_lst_inv)
        Pipe_props = self.append_col_to_table(Pipe_props, Static_head, 'Static Head [ft]', sort=sort_lst_inv)

        return [Pipe_props]


    def append_col_to_table(self, Pipe_props, col, title, data_type=False, sort=False, replace=False):
        if data_type:
            df = pd.DataFrame(data=col, columns=[title], dtype=data_type)
        else:
            df = pd.DataFrame(data=col, columns=[title])

        if sort:
            df = df.reindex(index=sort)  #rearrange the pipes within the pandas dataframe to be sorted from the Reservoir upstream


        df.reset_index(drop=True, inplace=True)

        if replace is True:
            Pipe_props = Pipe_props.drop([title], axis=1)

        #Pipe_props.reset_index(drop=True, inplace=True)

        Pipe_props = pd.concat([Pipe_props, df], axis=1)

        return Pipe_props

    def get_TDH(self, Pipe_props):

        TDH = []

        for i in range(len(Pipe_props.index)):
            pipe_TDH = Pipe_props.iloc[i]['Accumulated Friction Loss [ft]'] + Pipe_props.iloc[i]['Static Head [ft]']
            TDH.append(pipe_TDH)

            Pipe_props = self.append_col_to_table(Pipe_props, TDH, 'Total Dynamic Head [ft]', data_type='float')

            return Pipe_props

    def get_qepanet_edu_data(self, Pipe_props, sort_lst):

        Pipe_props = self.get_qepanet_pipe_props(Pipe_props, ['num_edu'], ['Number of EDUs'])


        return Pipe_props

    def filter_small_pipes(self, C, In, Pipe_props, Node_props, Pipe_nodes, sort_lst, C_factor, l_material, res, res_elev, node_srt_lst, pipe_dia_based_zones, lateral_conn_dia):

        #extract data from the Pipe_nodes dataframe
        Pipe_nodes = Pipe_nodes.to_numpy()

        End_nodes = self.get_end_zones(In, Pipe_props, Node_props, node_srt_lst, pipe_dia_based_zones, lateral_conn_dia)


        Zone_id = [0 for i in range(len(Pipe_props))]  # vector of Zone ID's sorted according to C matrix

        #get a sparse list of end nodes(i.e. contains only nodes that are end nodes)
        End_nodes_sparse = []
        for i in range(len(End_nodes)):
            if int(End_nodes[i][1]) == 1:  #find nodes that are labeled as end nodes
                End_nodes_sparse.append(End_nodes[i][0])  #get node id

        if len(End_nodes_sparse) == 0:
            self.log_error("No zone ends are defined.  Modify the 'zone_end' property of the junction layer to indicate how the zones should be generated.", stop=True)

        #get sorted list of end_nodes from most downstream
        End_nodes_sort = []
        for i in range(len(sort_lst)):
            if (Pipe_nodes[sort_lst[i]][1] in End_nodes_sparse) and (not Pipe_nodes[sort_lst[i]][1] in End_nodes_sort):
                End_nodes_sort.append(Pipe_nodes[sort_lst[i]][1])
            if (Pipe_nodes[sort_lst[i]][2] in End_nodes_sparse) and (not Pipe_nodes[sort_lst[i]][2] in End_nodes_sort):
                End_nodes_sort.append(Pipe_nodes[sort_lst[i]][2])
        #self.log_progress(str(End_nodes_sort))

        End_pipes_sort = []

        End_pipes = []  #list of pipes that are connected to end nodes

        #parse system from reservoir upstream and assign Zone IDs to pipes
        #for en in range(len(End_nodes_sort)):
        for end_id in End_nodes_sort:
            End_pipes_current = []
            for p, pipe in enumerate(Pipe_nodes):
#                    self.log_progress(str(p))
#                    self.log_progress(str(pipe))
#                    self.log_progress(str(pipe[1]))
#                    self.log_progress(str(pipe[2]))
#                    self.log_progress(str(end_id))
                if pipe[1] == end_id or pipe[2] == end_id:  #find pipes that are connected to the current end node
                    if not p in End_pipes:
                        End_pipes_current.append(p)  #get indices for these pipes in Pipe_nodes
            End_pipes.append(End_pipes_current)
            #self.log_progress("sort_lst: "+str(sort_lst))
            #self.log_progress("List of unsorted end pipe indices: "+str(End_pipes))
        #create a sorted list of pipe indices (according to C) that are connected to end nodes
            #get an unsorted list of C matrix indices
        End_pipes_sort = []
        #for end_id in End_nodes_sort:
        for row in End_pipes:
            End_pipes_sort_row = []
            for j, item  in enumerate(sort_lst):
                if item in row:
                    #self.log_progress("Enter Loop")
                    End_pipes_sort_row.append(j)
            End_pipes_sort.append(End_pipes_sort_row)
        #self.log_progress("List of sorted end pipe indices: "+str(End_pipes_sort))
            #sort the list into ascending order
#        ascend = []
#        for end_id in End_nodes_sort:
#            for i in range(len(End_pipes_sort)):
#                ascend.append(End_pipes_sort[i].sort())
#            #reassign values to End_pipe_sort:
#            End_pipes_sort = []
#            for i, row in enumerate(ascend):
#                End_pipes_sort.append(row)
        for row in End_pipes_sort:
            row.sort()

        #self.log_progress("List of sorted end pipe indices: "+str(End_pipes_sort))


    #parse system from reservoir upstream and assign Zone IDs to pipes
        zone_id = 1  #current zone_id

        #self.log_progress(End_pipes_sort)
        #define zone 1 downstream of the first zone end node
        for i in range(End_pipes_sort[0][0]+1):
            Zone_id[i] = zone_id
            #self.log_progress(zone_id)
        zone_id+=1
        #define all zones upstream of the first end zone node:
        #self.log_progress(str(Zone_id))
#        for i in range (len(End_pipes_sort)):  #loop thru rows of End_pipe_sort
#            for j in range(len(End_pipes_sort[en])):    #loop thru columns of End_pipe_sort
#                if End_pipes_sort[en][i] == 0:
#                    zone_branch = []  #C matrix index of pipes directly connected to current zone end node
#                    for j in range(len(C[End_pipes_sort[en][i]])): #create new zones for all upstream pipes directly connected to the end node
#                        if C[End_pipes_sort[en][i]][j] == 1:  #find all nodes connected to the current pipe
#                            if Zone_id[j] == 0:
#                                Zone_id[j] = zone_id
#                                zone_id += 1
#                            zone_branch.append(j)
#                            self.log_progress("Zone_id: "+str(Zone_id))
#                            self.log_progress("zone_branch: "+str(zone_branch))
#                        #for each new zone iterate to next end nodes pipe and define zone
#                            for br in range(len(zone_branch)):
#                                Zone_conn = [zone_branch[br]]  #array of connected pipes in this zone
#                                b = 0
#                                while True:
#                                    if (C[Zone_conn[b]][Zone_conn[b]] == 1) or (Zone_conn[b] in End_pipes_sort[en+1]) or (b == len(Zone_conn)):
#                                        break
#                                    self.log_progress(str(b))
#                                    if Zone_id[Zone_conn[b]] == 0:
#                                        Zone_id[Zone_conn[b]] = Zone_id[zone_branch[br]]
#                                    for k in range(Zone_conn[b]+1,len(C[End_pipes_sort[en][i]])):
#                                        if C[Zone_conn[b]][k] == 1:
#                                            self.log_progress("Appending to Zone_conn:"+str(Zone_conn))
#                                            Zone_conn.append(k)
#                                    b+=1
#                                    self.log_progress("Zone_id:"+str(Zone_id))
#                                    self.log_progress("Zone_conn:"+str(Zone_conn))
#                                if Zone_id[b] == 0:
#                                    Zone_id[b] = Zone_id[zone_branch[br]]

        for i in range (len(End_pipes_sort)):  #loop thru rows of End_pipe_sort
#            #set zone for most downstream pipe
#            if Zone_id[End_pipes_sort[i][0]] == 0:
#                Zone_id[End_pipes_sort[i][0]] = zone_id
#                zone_id += 1
            for j in range(1,len(End_pipes_sort[i])):    #loop thru columns of End_pipe_sort
                if Zone_id[End_pipes_sort[i][j]] == 0:  #if a zone_id has not already been assigned
                    Zone_id[End_pipes_sort[i][j]] = zone_id
                    zone_id += 1

        #Populate Zone ID values from end nodes upsteam using connection matrix
        for i, row in enumerate(C):
            for j, item in enumerate(row):
                if Zone_id[j] == 0:
                    Zone_id[j] = int(Zone_id[i]*item)

#                zone_branch = []  #C matrix index of pipes directly connected to current zone end node
#                    for j in range(len(C[End_pipes_sort[en][i]])): #create new zones for all upstream pipes directly connected to the end node
#                        if C[End_pipes_sort[en][i]][j] == 1:  #find all nodes connected to the current pipe
#                            if Zone_id[j] == 0:
#                                Zone_id[j] = zone_id
#                                zone_id += 1
#                            zone_branch.append(j)
#                            self.log_progress("Zone_id: "+str(Zone_id))
#                            self.log_progress("zone_branch: "+str(zone_branch))
#                        #for each new zone iterate to next end nodes pipe and define zone
#                            for br in range(len(zone_branch)):
#                                Zone_conn = [zone_branch[br]]  #array of connected pipes in this zone
#                                b = 0
#                                while True:
#                                    if (C[Zone_conn[b]][Zone_conn[b]] == 1) or (Zone_conn[b] in End_pipes_sort[en+1]) or (b == len(Zone_conn)):
#                                        break
#                                    self.log_progress(str(b))
#                                    if Zone_id[Zone_conn[b]] == 0:
#                                        Zone_id[Zone_conn[b]] = Zone_id[zone_branch[br]]
#                                    for k in range(Zone_conn[b]+1,len(C[End_pipes_sort[en][i]])):
#                                        if C[Zone_conn[b]][k] == 1:
#                                            self.log_progress("Appending to Zone_conn:"+str(Zone_conn))
#                                            Zone_conn.append(k)
#                                    b+=1
#                                    self.log_progress("Zone_id:"+str(Zone_id))
#                                    self.log_progress("Zone_conn:"+str(Zone_conn))
#                                if Zone_id[b] == 0:
#                                    Zone_id[b] = Zone_id[zone_branch[br]]


        #self.log_progress("Zone_id: "+str(Zone_id))


        sort_lst_inv = self.get_inv_sort_lst(sort_lst)

        #sort_lst_inv = [0 for i in range(len(sort_lst))]
        #for i, item in enumerate(sort_lst):
        #    sort_lst_inv[sort_lst[i]] = i

        Pipe_props = self.append_col_to_table(Pipe_props, Zone_id, 'Zone ID', data_type='int', sort=sort_lst_inv)

        #Pipe_props[["Zone ID"]+[c for c in Pipe_props if c not in ["Zone ID"]]]
        #self.log_progress(str(Pipe_props))

        #resort columns so that the first column is Zone ID
        cols = list(Pipe_props.columns.values)
        #self.log_progress("cols: ", cols)
        cols.pop(cols.index('Zone ID'))
        Pipe_props = Pipe_props[['Zone ID']+cols]

        #self.log_progress(str(Pipe_props))

        #self.log_progress(" Updating qgis vector layers...")

        self.update_pipes_vlay(Pipe_props, C_factor, l_material)

        #self.log_progress(" ...Done!")

        #Minimize Pipe_prop rows based on Zone ID
        num_zones = zone_id

        exists = False

        for z in range(num_zones-1):
            num_edu = 0
            accum_edu = 0
            op_edu = 0
            max_flow = 0
            dia = 0
            max_v = 0
            length = 0
            hl_f = 0
            hl = 0
            accum_hl = 0
            elev = 1e16  #large value that will be overwritten
            static_head = 0
            tdh = -1e16  #small value to accomodate negative pressures

            df = Pipe_props.loc[Pipe_props['Zone ID'] == z+1]

            #self.log_progress(str(df))

            for i, row in df.iterrows():
                num_edu += int(row['Number of EDUs'])

                if int(row['Number Accumulated EDUs']) > accum_edu:
                    accum_edu = int(row['Number Accumulated EDUs'])
                    op_edu = int(row['Accumulated Operating EDUs'])
                    max_flow = int(row['Max Flowrate [gpm]'])
                    dia = float(row['Diameter [in]'])
                    if z == 0:
                        dstream_zone = res[0]
                    else:
                        dstream_pipe = str(row['Downstream Connected Pipe'])
                        dstream_zone = Pipe_props.loc[Pipe_props['Pipe ID'] == dstream_pipe, 'Zone ID'].item()


                if int(row['Max Velocity [ft/s]']) > max_v:
                    max_v = float(row['Max Velocity [ft/s]'])

                length += float(row['Length [ft]'])

                hl += float(row['Friction Loss [ft]'])

                if float(row['Accumulated Friction Loss [ft]']) > accum_hl:
                    accum_hl = float(row['Accumulated Friction Loss [ft]'])

                if float(row['Minimum Elevation [ft]']) < elev:
                    elev = float(row['Minimum Elevation [ft]'])

                #if float(row['Static Head [ft]']) > static_head:
                #    static_head = float(row['Static Head [ft]'])

                static_head = res_elev[0] - elev

                if float(row['Total Dynamic Head [ft]']) > tdh:
                    tdh = float(row['Total Dynamic Head [ft]'])

            hl_f = hl/length * 100

            d = [[z+1, dstream_zone, num_edu, accum_edu, op_edu, max_flow, dia, max_v, length, hl_f, hl, accum_hl, elev, static_head, tdh]]

            #self.log_progress(str(d))

            c = ['Zone ID', 'Zone Downstream', 'Number EDUs in Zone', 'Accum. EDUs', 'Acuum. Operating EDUs', 'Max Flow [gpm]', 'Max Pipe Diameter [in]', 'Max Velocity [ft/s]', 'Pipe Length [ft]', 'Friction Loss Factor [ft/100ft]', 'Friction Loss [ft]', 'Accum. Friction Loss [ft]', 'Min Elevation [ft]', 'Max Static Head [ft]', 'Max Total Dynamic Head [ft]']

            if not exists:
                Zone_props = pd.DataFrame(data=np.array(d, dtype=object), index=[0], columns=c)
                exists = True
            else:
                Zone_props = Zone_props.append(pd.DataFrame(data=np.array(d, dtype=object), index=[0], columns=c), ignore_index=True)

            self.log_progress("\tZone "+str(z+1)+";\t num_edu: "+str(num_edu))
            self.log_progress("\tZone "+str(z+1)+";\t accum_edu: "+str(accum_edu))
            self.log_progress("\tZone "+str(z+1)+";\t op_edu: "+str(op_edu))
            self.log_progress("\tZone "+str(z+1)+";\t max_flow: "+str(max_flow))
            self.log_progress("\n")

#
#        #extract the number of edus for end pipes into an array
#        pipe_end_v = Pipe_props["Number of EDUs"].tolist()
#
#
#        Accum_edu_new = [0 for i in range(len(Pipe_props_fm.index))]
#
#        #recalculate the number of edus based on the number of "1 EDU" pipes connected to a forcemain pipe
#        for i in range(len(Pipe_props_fm.index)):
#            conn_node = Pipe_props_fm.loc[i, "Downstream Connected Pipe"]
#            num_edu = 0
#            for j in range(len(Pipe_props_end.index)):
#                if Pipe_props_end.loc[j, "Pipe ID"] == conn_node:
#                    num_edu += Pipe_props_end.loc[j, "Number of EDUs"]
#            Accum_edu_new[i] = num_edu
#
#
#        #replace the existing number of edus in the filtered dataframe
#        Pipe_props_fm = Pipe_props_fm.replace('Number of EDUs', Accum_edu_new)

        return Zone_props


    def filter_small_pipes_2(self, C, In, Pipe_props, Node_props, Pipe_nodes, sort_lst, C_factor, l_material, res, node_srt_lst, pipe_dia_based_zones, lateral_conn_dia):

        #extract data from the Pipe_nodes dataframe
        Pipe_nodes = Pipe_nodes.to_numpy()

        End_nodes = self.get_end_zones(In, Pipe_props, Node_props, node_srt_lst, pipe_dia_based_zones, lateral_conn_dia)

        [Zone_id, num_zones] = self.get_zone_id(In, Pipe_props, Node_props, End_nodes, node_srt_lst, pipe_dia_based_zones, lateral_conn_dia) # vector of pipe Zone ID's sorted according to C matrix


        sort_lst_inv = self.get_inv_sort_lst(sort_lst)

        #sort_lst_inv = [0 for i in range(len(sort_lst))]
        #for i, item in enumerate(sort_lst):
        #    sort_lst_inv[sort_lst[i]] = i

        Pipe_props = self.append_col_to_table(Pipe_props, Zone_id, 'Zone ID', data_type='int', sort=sort_lst_inv)

        #Pipe_props[["Zone ID"]+[c for c in Pipe_props if c not in ["Zone ID"]]]
        #self.log_progress(str(Pipe_props))

        #resort columns so that the first column is Zone ID
        cols = list(Pipe_props.columns.values)
        #self.log_progress("cols: ", cols)
        cols.pop(cols.index('Zone ID'))
        Pipe_props = Pipe_props[['Zone ID']+cols]

        self.log_progress(str(Pipe_props))

        #self.log_progress(" Updating qgis vector layers...")

        self.update_pipes_vlay(Pipe_props, C_factor, l_material)

        #self.log_progress(" ...Done!")

        Zone_props = self.get_zone_table_vals(Pipe_props, num_zones, res)

        return Zone_props

    def get_inputs_dataframe(self, inputs):

        index = [0]
        Calc_stats = pd.DataFrame(data=inputs, index=index)

        return Calc_stats

    def update_pipes_vlay(self, Pipe_props, C_factor, l_material):
        """ {Function}
                Exports values stored in the Pipe_props dataframe into the "Pipes" vector layer for viewing in QGIS
            {Variables}
                Pipe_props:
                    (Pandas dataframe) Includes details of the pipe network (must include pipe diameter information)
                C_factor:
                    Hazen-Williams loss coefficient
                l_material:
                    Pipe material
            {Outputs}
                None
        """
#        layers = QgsMapLayerRegistry.instance().mapLayersByName(self.params.pipes_vlay_name)
#        layer = layers[0]
#        it = layer.getFeatures()
        layer = self.params.pipes_vlay
        it = layer.getFeatures()

        # replace any spaces in the material with an underscore since the EPANET file is space delimited
        #l_material = l_material.replace(" ", "_")



        layer.startEditing()

        for i, feat in enumerate(it):
            length =  Pipe_props.loc[i, 'Length [ft]']
            #self.log_progress(str(length))
            diameter =  Pipe_props.loc[i, 'Diameter [in]']
            #self.log_progress(str(diameter))
            num_edu =  Pipe_props.loc[i, 'Number of EDUs']
            #self.log_progress(str(num_edu))
            pipe_id = Pipe_props.loc[i, 'Pipe ID']
            #self.log_progress(str(pipe_id))
            #if Pipe_props.loc[i, 'Zone ID']:
            if 'Zone ID' in Pipe_props.columns:
                zone_id = int(Pipe_props.loc[i, 'Zone ID'])
            else:
                zone_id=0
            #self.log_progress("zone id: "+str(zone_id))
            velocity = Pipe_props.loc[i, 'Max Velocity [ft/s]']
            frictionloss = Pipe_props.loc[i, 'Friction Loss [ft]']

            data = [str(pipe_id), str(length), str(diameter), 'OPEN', str(C_factor), "0", self.PipeMaterialName[l_material], "", "", str(num_edu), str(zone_id), "{:.2f}".format(velocity), "{:.2f}".format(frictionloss)]

            #self.log_progress(str(data))

            for j in range(len(data)):
                #self.log_progress(str(j))
                layer.changeAttributeValue(feat.id(), j, data[j])

        layer.commitChanges()

    def get_pump_curve(self, pump_database, pump_model):
        """ {Function}
                Reads pump curve info stored as excel file, and stores ad pandas dataframe.
            {Variables}
                pump_database:
                    (str) The file name of the excel file containing pump curve
                    information.  Database should store data for each pump as a
                    separate sheet, with the sheet name specified as the pump
                    model number.  Tabular data header information is located on
                    line 6 with.  The first 5 lines of the sheet are ignored.

                pump_model:
                    (str) The specific pump model for which to get data.  This
                    should match the sheet name exactly.
            {Outputs}
                pcurve:
                    (pandas.DataFrame)  The pump curve info as a pandas
                    dataframe.
        """

        pcurve = pd.read_excel(pump_database, sheet_name=pump_model, header=5)

        self.log_debug("Pump curve dataframe:\n"+str(pcurve))

        return pcurve



    def get_zone_id_from_dia(self, Pipe_props, Pipe_nodes):  #INCOMPLETE
        """ {Functiion}
                Automatically defines the location of the split between zones based on changes in the pipe diameter of the forcemain.
            {Variables}
                Pipe_props:
                    (Pandas dataframe) Includes details of the pipe network (must include pipe diameter information)
                Pipe_nodes:
                    (Numpy array)  List of start and end nodes for each pipe.
                Node_lst:
                    (Numpy array)  List of all nodes in the pipe network
            {Output}
                Pipe_props:
                    (Pandas dataframe)  Details of pipe network appended with "zone_end" and "Zone ID" columns
        """
        pass

        #Get the array of Pipe Diameters
        Pipe_dia = Pipe_props['Diameter [in]']
        for node in Node_lst:
            for pipe in Pipe_nodes:
                if Pipe_props:
                    pass
                if (node == Pipe_nodes[1]):
                    adj_node = Pipe_node[1]
                if (node == Pipe_nodes[2]):
                    pass

    def update_junctions_vlay(self, Node_props):  #INCOMPLETE
        """ {Function}
                Exports values stored in the Pipe_props dataframe into the "Junctions" vector layer for viewing in QGIS
            {Variables}
                Node_props:
                    (Pandas dataframe) Junction details of the pipe network .
            {Outputs}
                None
        """

        layer = self.params.junctions_vlay
        it = layer.getFeatures()


        layer.startEditing()

        for i, feat in enumerate(it):
            junc_id =  Node_props.loc[i, 'Node ID']
            elev =  Node_props.loc[i, 'Elevation [ft]']
            zone_end =  Node_props.loc[i, 'Zone End']
            pressure =  Node_props.loc[i, 'Pressure [ft]']
            #self.log_progress(str(length))

            data = [str(junc_id), "{:.2f}".format(elev), "0", "", "0", "0", "", "", "{:.0f}".format(zone_end), "{:.2f}".format(pressure)]

            #self.log_progress(str(data))

            for j in range(len(data)):
                #self.log_progress(str(j))
                layer.changeAttributeValue(feat.id(), j, data[j])

        layer.commitChanges()

    def parse_system(self, Pipe_props, Node_props, C, sort_lst, return_type):  #INCOMPLETE
        """ {Function}
                Parses through the Pipe network and returns nodes in a ordered list from the the Reservior upstream.
            {Variables}
                Pipe_props:
                    (Pandas dataframe) Includes pipe info for the pipe network
                Node_props:
                    (Pandas dataframe) Includes junction info for the pipe network
                sort_lst:
                    (Numpy array)  "Sort list" array which maps the location of the pipe in the Pipe_props dataframe to the location of the pipe in the sorted Pipes_array dataframe.  generated in the create_conn_matrix() function.
                    Integer value is the index location in the sorted dataframe.
                    Index correspnds to the index in the unsorted "Pipe_props" dataframe.
                return_type:
                    (string: "Junctions" or "Pipes")  Specifies which dataframe to parse
            {Outputs}
                Nodes_sort:
                    (Pandas dataframe) Sorted list of junction info from the Reservoir upstream
        """
        pass

    def sort_dataframe(self, df, sort_lst):
        """ {Function}
                Converts an unsorted dataframe indexed based on the QGIS data.
            {Variables}
                df:
                    (Pandas dataframe) unsorted dataframed based on QGIS indices that is to be sorted.
                sort_lst:
                    (Numpy array of ints)  "Sort list" array which maps the location of the pipe in the Pipe_props dataframe to the location of the pipe in the sorted Pipes_array dataframe.  generated in the create_conn_matrix() function.
                    Integer value is the index location in the sorted dataframe.
                    Index correspnds to the index in the unsorted "Pipe_props" dataframe.
            {Outputs}
                df_sort:
                    (Pandas dataframe) Sorted dataframe indexed based on the location from the Reservior.
        """

        df_sort = df.reindex(sort_lst, axis='index')

        return df_sort



    def get_inv_sort_lst(self, sort_lst):
        """ {Function}
                Returns the invert of a sort list to allow for the unsorting of a dataframe / array (e.g.  convert a list ordered from the reservior upstream to a list ordered according the QGIS features)
            {Variables}
                sort_lst:
                    (Numpy array of ints)   "Sort list" array which maps the location of items in the Node_props dataframe to the location of the junction in the sorted the "props_sort" dataframe.  Generated in the create_conn_matrix() function.
                    Integer value is the index location in the sorted dataframe.
                    Index correspnds to the index in the unsorted "Pipe_props" dataframe.
            {Outputs}
                sort_lst_inv:
                    (Numpy array of ints) invert of the sort_lst
        """
        sort_lst_inv = [0 for i in range(len(sort_lst))]
        for i, item in enumerate(sort_lst):
            sort_lst_inv[sort_lst[i]] = i

        return sort_lst_inv


    def validate_inputs(self, all_pumps_on, op_edu_calc, p_calc, l_material, l_class):
        val = True

        vals_all_pumps_on = [True, False]
        if all_pumps_on not in vals_all_pumps_on:
            self.log_progress("    Warning:  The 'all_pumps_on' parameter must be defined as a valid boolean.")
            val = False

        vals_op_edu_calc = ['table', 'EPA', 'all']
        if op_edu_calc not in vals_op_edu_calc:
            self.log_progress("    Warning:  Value for 'op_edu_calc' is not valid.\n")
            self.log_progress("    Valid options are "+str(vals_op_edu_calc))
            val = False

        vals_p_calc = ['forward-sub', 'fixed-point', 'broyden', 'broyden-sp']
        if p_calc not in vals_p_calc:
            self.log_progress("    Warning:  Value for 'p_calc' is not valid.\n")
            self.log_progress("    Valid options are "+str(vals_p_calc))
            val = False

        #vals_l_material = ['HDPE', 'PVC']
        if l_material not in PipeMaterial:
            self.log_progress("    Warning:  Value for 'l_material' is not valid.\n")
            self.log_progress("    Valid options are "+str(PipeMaterial))
            val = False

        if l_class not in list(self.PipeClassName.values()):
            self.log_progress("    Warning:  Value for 'l_material' is not valid.\n")
            self.log_progress("    Valid options are "+str(list(self.PipeClassName.values())))
            val = False
        return val

    def apply_pipe_styling(self):
        layer = self.params.pipes_vlay
        basepath = os.path.dirname(os.path.realpath(__file__))

        layer.loadNamedStyle(basepath+'qml/pipes_dia_labels.qml')

    def get_end_zones(self, In, Pipe_props, Node_props,  node_srt_lst, pipe_dia_based_zones, lateral_conn_dia):

        if pipe_dia_based_zones == False:
            #get array of zone end nodes sorted according to qgis vlayers
            End_nodes = self.junc_fts[['id','zone_end']].to_numpy()
        else:
            #parse through system and mark as zone end if FM diameter changes
            Pipe_dia = self.sort_dataframe(Pipe_props['Diameter [in]'], node_srt_lst).to_numpy()

            #End_nodes = [0 for i in range(len(In)-1)]
            End_nodes = np.zeros(1, len(In)-1)
            for n in range(len(End_nodes)):
                Node_dia = Pipe_dia * In[n]
                Node_dia = Node_dia[np.nonzero(Node_dia)]
                #self.log_progress("Node Pipe Dia: ", Node_dia)
#                for i in range(len(Node_dia)-1):
#                    for j in range(len(Node_dia)):
#                        if i != j \
#                        and Node_dia[i] != Node_dia[j] \
#                        and Node_dia[i] != lateral_conn_dia \
#                        and Node_dia[j] != lateral_conn_dia:
#                            End_nodes[n] = 1
#                            break

                i = 0
                break_outer = False
                while True:
                    if i > len(Node_dia)-1 or break_outer:
                        break
                    for j in range(len(Node_dia)):
                        if Node_dia[i] != lateral_conn_dia:
                            if i != j \
                            and Node_dia[i] != Node_dia[j] \
                            and Node_dia[j] != lateral_conn_dia:
                                End_nodes[n] = 1
                                break_outer = True
                            break
                    i += 1

            Node_id = self.sort_dataframe(Node_props['Node ID'], node_srt_lst).to_numpy()
            #self.log_progress("Node ID: ", type(Node_id), Node_id.shape)
            #self.log_progress("End_Nodes: ", type(End_nodes), End_nodes.shape)


            End_nodes = np.vstack((self.sort_dataframe(Node_props['Node ID'], node_srt_lst).to_numpy(), np.asarray(End_nodes))).T  #add node label to end nodes list

        #self.log_progress("End_nodes:\n", End_nodes)

        return End_nodes

    def get_zone_id(self, In, Pipe_props, Node_props, End_nodes, node_srt_lst, pipe_dia_based_zones, lateral_conn_dia): #INCOMPLETE


        Zone_id_mat = np.delete(In, 0, axis=0) # matrix of Zone ID's in the form of the incidence matrix.

        #Node_zone_id = [0 for i in range(len(Node_props))] # vector of minimum zone id attached to each node

        zone = 1
        #get start index
        s = 0
        while End_nodes[s] != 1 and s < len(End_nodes):
            s += 1

        #self.log_progress("first end node: ", s)

        for i in range(s,len(In)-1):#node index
            if End_nodes[i] == 1:
                Zone_id_mat[i][i] = zone
                j = i+1
                while j < len(Zone_id_mat[i]):
                    if Zone_id_mat[i][j] != 0:
                        zone = zone+1
                        Zone_id_mat[i][j] = zone
                        #update connected node
                        Zone_id_mat[j][j] = zone
                    j += 1
            else:
                if Zone_id_mat[i][i] == 1:
                    Zone_id_mat[i][i] = zone
                    #self.log_progress("HERE!")
                zone_ = Zone_id_mat[i][i]
                #self.log_progress("zone_: ", zone_)
                Zone_id_mat[i] = zone_*In[i+1]

        #self.log_progress("Zone ID Matrix:\n", Zone_id_mat)
#
#        In_U = np.delete(In, 0, axis=0)
#        In_strictU = In_U - np.identity(len(In_U))    #Incidene sub-matrix without first row. This matrix is strictly upper triangular.
#
#
#        #Pipe zone id can be obtained as:
#        #               In_strictU[i] \dot zone_id[i],
#        #                    where "\dot" indicates the scalar multiplication of the matrix row by the scalar entry of a vector.
#
        Zone_id = np.diag(Zone_id_mat)

        #self.log_progress("Pipe Zone ID:\n", Zone_id)

        return [Zone_id, zone] #equivalent to [Pipe_zone_id, num_zones]

    def get_zone_table_vals(self, Pipe_props, num_zones, res):
        #Minimize Pipe_prop rows based on Zone ID

        exists = False

        self.log_progress(" ")

        for z in range(num_zones-1):
            num_edu = 0
            accum_edu = 0
            op_edu = 0
            max_flow = 0
            dia = 0
            max_v = 0
            length = 0
            hl_f = 0
            hl = 0
            accum_hl = 0
            elev = 1e16  #large value that will be overwritten
            static_head = 0
            tdh = 0

            df = Pipe_props.loc[Pipe_props['Zone ID'] == z+1]

            #self.log_progress(str(df))

            for i, row in df.iterrows():
                num_edu += int(row['Number of EDUs'])

                if int(row['Number Accumulated EDUs']) > accum_edu:
                    accum_edu = int(row['Number Accumulated EDUs'])
                    op_edu = int(row['Accumulated Operating EDUs'])
                    max_flow = int(row['Max Flowrate [gpm]'])
                    dia = float(row['Diameter [in]'])
                    if z == 0:
                        dstream_zone = res[0]
                    else:
                        dstream_pipe = str(row['Downstream Connected Pipe'])
                        dstream_zone = Pipe_props.loc[Pipe_props['Pipe ID'] == dstream_pipe, 'Zone ID'].item()


                if int(row['Max Velocity [ft/s]']) > max_v:
                    max_v = float(row['Max Velocity [ft/s]'])

                length += float(row['Length [ft]'])

                hl += float(row['Friction Loss [ft]'])

                if float(row['Accumulated Friction Loss [ft]']) > accum_hl:
                    accum_hl = float(row['Accumulated Friction Loss [ft]'])

                if float(row['Minimum Elevation [ft]']) < elev:
                    elev = float(row['Minimum Elevation [ft]'])

                if float(row['Static Head [ft]']) > static_head:
                    static_head = float(row['Static Head [ft]'])

                if float(row['Total Dynamic Head [ft]']) > tdh:
                    tdh = float(row['Total Dynamic Head [ft]'])



            hl_f = hl/length * 100

            d = [[z+1, dstream_zone, num_edu, accum_edu, op_edu, max_flow, dia, max_v, length, hl_f, hl, accum_hl, elev, static_head, tdh]]

            #self.log_progress(str(d))

            c = ['Zone ID', 'Zone Downstream', 'Number EDUs in Zone', 'Accum. EDUs', 'Acuum. Operating EDUs', 'Max Flow [gpm]', 'Max Pipe Diameter [in]', 'Max Velocity [ft/s]', 'Pipe Length [ft]', 'Friction Loss Factor [ft/100ft]', 'Friction Loss [ft]', 'Accum. Friction Loss [ft]', 'Min Elevation [ft]', 'Max Static Head [ft]', 'Max Total Dynamic Head [ft]']

            if not exists:
                Zone_props = pd.DataFrame(data=np.array(d, dtype=object), index=[0], columns=c)
                exists = True
            else:
                Zone_props = Zone_props.append(pd.DataFrame(data=np.array(d, dtype=object), index=[0], columns=c), ignore_index=True)

            self.log_progress("    Zone "+str(z+1)+";    num_edu: "+str(num_edu))
            self.log_progress("    Zone "+str(z+1)+";    accum_edu: "+str(accum_edu))
            self.log_progress("    Zone "+str(z+1)+";    op_edu: "+str(op_edu))
            self.log_progress("    Zone "+str(z+1)+";    max_flow: "+str(max_flow))
            self.log_progress(" ")


        return Zone_props

    def analyze_system_connectivity(self, Pipe_nodes, pipe_lst, node_lst):

        #progress.setText("\tchecking for disconnected junctions...")
        self.log_progress("    checking for disconnected junctions...")

        all_junc = self.params.junctions_vlay.getFeatures()

        #print("all_junc:\n", all_junc)

        conn_junc = Pipe_nodes[:,1:3]

        #print("conn_junc:\n", conn_junc)

        disconn_junc = []

        for feat in all_junc:
            #print("junction: ", feat.attribute(Junction.field_name_eid), "\ttype: ",type(feat.attribute(Junction.field_name_eid)))

            found=False
            for junc_lst in conn_junc:
                break_outer = False
                for junc in junc_lst:
                    if str(feat.attribute(Junction.field_name_eid)) == junc:
                        found=True
                        break_outer = True
                        break
                if break_outer is True:
                    break

            if found is False:
                disconn_junc.append( str(feat.attribute(Junction.field_name_eid)) )

        if len(disconn_junc) > 0:
            self.log_error("System contains "+str(len(disconn_junc))+" disconnected junctions:\n"+str(disconn_junc))
            max_index = 0
            for i in range(len(conn_junc)):
                for j in range(len(node_lst)):
                    if conn_junc[i] == node_lst[j]:
                        if j > max_index:
                            max_index = j
            if max_index < len(node_lst)-1:
                self.log_error("The last node to be processed correctly was "+node_lst[max_index])
                self.log_error("The next node to be processed should have been "+node_lst[max_index+1])
            else:
                self.log_error("The last node to be processed correctly was "+node_lst[max_index]+".  This is the last node in the sorted list.")
        else:
            self.log_progress("No disconnected junctions found.")

        #progress.setText("\tchecking for disconnected pipes...")
        self.log_progress("    checking for disconnected pipes...")

        #C = np.zeros((c_len,c_len))
        #C_n = np.zeros((c_len+1,c_len+1))
        #In = np.zeros((c_len+1,c_len))
        all_pipes = [Pipe_nodes[i][0] for i in range(len(Pipe_nodes))]
        #all_pipes = np.asarray(all_pipes).astype(str) #convert python list to numpy array

        procd_pipes = []
        for i in range(len(pipe_lst)):
            procd_pipes.append(Pipe_nodes[pipe_lst[i][0]][0])

        #self.log_progress("all_pipes: ", all_pipes)
        #self.log_progress("all_pipes: ", len(all_pipes))

        #self.log_progress("procd_pipes: ", procd_pipes)
        #self.log_progress("procd_pipes: ", len(procd_pipes))

        #mask = np.isin(all_pipes, procd_pipes, invert=True)
        #disconn_pipes = all_pipes[mask]
        disconn_pipes = []
        for i in range(len(all_pipes)):
            break_loop=False
            for j in range(len(procd_pipes)):
                if all_pipes[i] == procd_pipes[j]:
                    break_loop=True
                    break
            if break_loop is False:
                disconn_pipes.append(all_pipes[i])
        if len(disconn_pipes) > 0:
            self.log_error("System contains "+str(len(disconn_pipes))+" disconnected pipes:\n"+str(disconn_pipes))
            #find the last junction to processed correctly
            max_index = 0
            for i in range(len(conn_junc)):
                for j in range(len(node_lst)):
                    if conn_junc[i] == node_lst[j]:
                        if j > max_index:
                            max_index = j
            if max_index < len(pipe_lst)-1:
                self.log_error("The last node to be processed correctly was "+pipe_lst[max_index])
                self.log_error("The next node to be processed should have been "+pipe_lst[max_index+1])
            else:
                self.log_error("The last node to be processed correctly was "+pipe_lst[max_index]+".  This is the last node in the sorted list.")
        else:
            self.log_progress("No disconnected pipes found.")
        #self.log_progress("disconn_pipes: ", disconn_pipes)
        #self.log_progress("disconn_pipes: ", len(disconn_pipes))

            #check if the pipe is connected to the reservoir
#            for n in range(len(c_len)):
#                row = True
#                current_node = C_n[:][len(C_n)-1]
#                while np.sum(current_node) > 1:
#                    for i in range(len(current_node)):
#                        if current_node[i] == 1:
#                            if row:
#                                current_node = C_n[:][i]
#                                row = False
#                                break
#                            else:
#                                current_node = C_n[i]
#                                row = True
#                                break
#
#                if current_node[0] != 1:
#                    for i in range(len(current_node)):
#                        if current_node[i] == 1 and i != n:
#                            break
#                    disconn_pipes.append(Pipe_nodes[pipe][0])
#                    self.log_progress("ERROR:  Node ",node_lst[i], " is disconnected from the Reservior")

        self.select_qgis_features(self.params.junctions_vlay, disconn_junc)

#        ids = []
#
#        #select Junctions in iface
#        layer = self.params.junctions_vlay
#        it = layer.getFeatures()
#
#        iface.setActiveLayer(layer)
#
#        for i, feat in enumerate(it):
#            #self.log_progress("feature eid: ", feat.attribute(Junction.field_name_eid))
#            for j in range(len(disconn_junc)):
#                if str(feat.attribute(Junction.field_name_eid)) == disconn_junc[j]:
#                    ids.append(feat.id())
#
#        layer.selectByIds(ids)
#

        self.select_qgis_features(self.params.pipes_vlay, disconn_pipes)
#        ids = []
#
#        #select Pipes in iface
#        layer = self.params.pipes_vlay
#        it = layer.getFeatures()
#
#        iface.setActiveLayer(layer)
#
#        for i, feat in enumerate(it):
#            #self.log_progress("feature eid: ", feat.attribute(Pipe.field_name_eid))
#            for j in range(len(disconn_pipes)):
#                if str(feat.attribute(Pipe.field_name_eid)) == disconn_pipes[j]:
#                    ids.append(feat.id())
#        #self.log_progress("ids: ", ids)
#
#        layer.selectByIds(ids)
#
#        iface.actionZoomToSelected().trigger()

        raise Exception("System geometry is not correct.  See 'XPSS Progress Log' for additional details.")


    def select_qgis_features(self, layer, eids):
        ids = []

        it = layer.getFeatures()

        iface.setActiveLayer(layer)

        for i, feat in enumerate(it):
            #self.log_progress("feature eid: ", feat.attribute(Junction.field_name_eid))
            for j in range(len(eids)):
                if str(feat.attribute(Junction.field_name_eid)) == eids[j]:
                    ids.append(feat.id())

        layer.selectByIds(ids)

        iface.actionZoomToSelected().trigger()
