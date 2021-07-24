from qgis.core import QgsSpatialIndex
import qgis.utils

import pandas as pd

from XPSS.model.network import Pipe, Junction, Reservoir
from XPSS.model.network_handling import NetworkUtils

from XPSS.logger import Logger

logger = Logger(debug=True)

class PSS:

    def __init__(self, dockwidget):
        #self.pipeProps = pd.DataFrame()
        #self.nodeProps = pd.DataFrame()
        self.xpss = qgis.utils.plugins["XPSS"]
        self.params = self.xpss.params  #refer to the parameters stored in the existing instance of qepanet
        self.pipe_fts = pd.DataFrame(self.params.pipes_vlay.getFeatures(),columns=[field.name() for field in self.params.pipes_vlay.fields() ])  #extract pipe attribute table as a pandas array
        self.junc_fts = pd.DataFrame(self.params.junctions_vlay.getFeatures(),columns=[field.name() for field in self.params.junctions_vlay.fields() ])  #extract pipe attribute table as a pandas array
        self.res_fts = pd.DataFrame(self.params.reservoirs_vlay.getFeatures(),columns=[field.name() for field in self.params.reservoirs_vlay.fields() ])  #extract pipe attribute table as a pandas array
        self.checkPipeConns = dockwidget.chk_check_pipes.isChecked()
        self.checkNodeConns = dockwidget.chk_check_nodes.isChecked()

        [self.pipeProps, self.nodeProps, self.pipeNodeProps,
         self.res, self.res_elev] = self.initialize_from_qepanet()

        [self.sysGeomError, self.numEntityErr, self.nPipes, self.nNodes] = \
            self.check(self.checkPipeConns, self.checkNodeConns)

    def check(self, check_pipe_conns, check_node_conns):
        #TODO:  rewrite to use a pandas dataframe

        sindex = QgsSpatialIndex()
        pipe_fts = self.params.pipes_vlay.getFeatures()
        junc_fts = self.params.junctions_vlay.getFeatures()
        res_fts = self.params.reservoirs_vlay.getFeatures()
        # tank_fts = self.params.tanks_vlay.getFeatures()
        # pump_fts = self.params.pumps_vlay.getFeatures()

        logger.progress("%%%%%%%%%%% BEGIN CHECK OF PSS SYSTEM %%%%%%%%%%%")

        #get system details from the qgis vector layers (a lot of this taken from in_writer.py in qepanet)

        #logger.progress("pipe_lst: "+str(np.asarray(pipe_lst).shape))

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
        logger.progress("Summary of System Components:")
        for feat in junc_fts:
            sindex.addFeature(feat)
            j+=1
        logger.progress(str(j)+" Junctions")

        for feat in res_fts:
            sindex.addFeature(feat)
            res.append(feat.attribute(Reservoir.field_name_eid))
            r+=1
        logger.progress(str(r)+" Reservoirs")

        # for feat in tank_fts:
        #     sindex.addFeature(feat)
        #     t+=1
        # logger.progress(str(t)+" Tanks")

        for feat in pipe_fts:
            l+=1
        logger.progress(str(l)+" Pipes")

        # for feat in pump_fts:
        #     p+=1
        # logger.progress(str(p)+" Pumps")

        if len(res) != 1:        #check to see if there is a single reservoir.  Analysis assumes that all end nodes are pumps pump to a single outlet
            logger.error("The number of reserviors in the network must equal 1.")
            has_error = True

        if j != l:        #check to see if the number of pipes equals the number of junctions.  This is true for a directed tree graph with a reservior as its end node.
            logger.error("The number of junctions is not equal to the number of pipes.")
            #has_error = True  #commented to continue calc to get a more detailed error in "create_conn_matrix()
            num_entity_err = True

        #reset QGIS iterators
        pipe_fts = self.params.pipes_vlay.getFeatures()
        junc_fts = self.params.junctions_vlay.getFeatures()
        res_fts = self.params.reservoirs_vlay.getFeatures()
        # tank_fts = self.params.tanks_vlay.getFeatures()
        # pump_fts = self.params.pumps_vlay.getFeatures()

        node_lst = [junc_fts, res_fts]
        node_Class = [Junction, Reservoir]

        pipe_lst = [pipe_fts]
        pipe_Class = [Pipe]


        disconn_pipes = []
        disconn_juncs = []

        if check_pipe_conns is True:
            logger.progress("Cycling through all pipes to check connections...")  #TODO:  This is not working properly

            Pipe_nodes = []  #List of start and end nodes for each pipe

            all_pipes = []

            #TODO:  update to include all layers and check if each layer is valid

            for i in range(len(pipe_lst)):
                for ft in pipe_lst[i]:

                    #logger.progress("Checking pipe connection...")

                    eid = ft.attribute(pipe_Class[i].field_name_eid)

                    if num_entity_err == True:
                        all_pipes.append(eid)

                    #sindex = self.params.nodes_sindex
                    # Find start/end nodes
                    adj_nodes = NetworkUtils.find_start_end_nodes_sindex(self.params, sindex, ft.geometry())

                    #adj_nodes = NetworkUtils.find_start_end_nodes(self.params, ft.geometry())  #TODO:  Determine why the 'sindex' version does not work


                    found_nodes = []

                    #try:
                    start_node_id = adj_nodes[0].attribute(Junction.field_name_eid)  #TODO:  Get Reservoir eid name in case it is different.
                    end_node_id = adj_nodes[1].attribute(Junction.field_name_eid)

                    found_nodes.append(start_node_id)
                    found_nodes.append(end_node_id)

                    if start_node_id == end_node_id:
                        logger.error("Pipe "+eid+" is connected to itself.  Connected nodes are "+start_node_id+" and "+end_node_id+".")
                        has_error = True

                    #check for any very short pipes:  #TODO:  This is not working correctly
                    short_pipes_nodes = []
                    if float(ft.attribute(Pipe.field_name_length)) < 2: #TODO:  units are assumed to be ft
                        logger.error("Pipe "+eid+" is very short.  Connected nodes are"+start_node_id+" and "+end_node_id+".")
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

                    # except:
                    #     print_str = "Connected nodes are"
                    #     found_node = False
                    #     if start_node_id:
                    #         print_str += " "+start_node_id
                    #         found_node = True
                    #     if end_node_id:
                    #         print_str += " "+end_node_id
                    #         found_node = True
                    #     if found_node is False:
                    #         print_str = "No nodes were found for pipe"
                    #     logger.error("Pipe "+eid+" has less than 2 nodes connected.  "+print_str+".")
                    #     disconn_pipes.append(eid)
                    #     has_error = True

            if len(disconn_pipes) > 0:
                self.select_qgis_features(self.params.pipes_vlay, disconn_pipes)  #TODO:  assumes the vector layer is Pipes

        else:
            logger.progress("Pipe connection checks were not performed.")

            #logger.progress(str(Pipe_nodes))
        if check_node_conns is True:
            if check_pipe_conns is False:
                logger.warning("Pipe checks must be performed before checking nodes.")
                return [False, False, l, j]
            logger.progress("Cycling through all nodes to check connections...") #TODO:  This is not working properly

            for i in range(len(node_lst)):
                for ft in node_lst[i]:
                    #logger.progress("Checking node connection...")
                    num_conn = 0
                    eid = ft.attribute(node_Class[i].field_name_eid)
                    for j in range(len(found_nodes)):
                        if found_nodes[j] == eid:
                            num_conn += 1
                    logger.progress("Connections for Node "+eid+": "+str(num_conn))
                    if num_conn == 0:
                        logger.error("The node "+eid+" is not connected to any pipes.")
                        disconn_juncs.append(eid)
                        has_error = True

            if len(disconn_juncs) > 0:
                self.select_qgis_features(self.params.junctions_vlay, disconn_juncs)  #TODO:  assumes the vector layer is Junctions
        else:
            logger.progress("Node connection checks were not performed.")

        if num_entity_err:
            logger.progress("An Error was found!  The number of pipes does not match the number of junctions.  Additional details will be provided after parsing through the system.")

        elif has_error == True:
            logger.error("Error(s) were found.  Check the system definition and correct.", stop=True)

        else:
            logger.progress("There are no errors found in the system!")


        logger.progress("%%%%%%%%%%% END CHECK OF PSS SYSTEM %%%%%%%%%%%")


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
        #tank_fts = self.params.tanks_vlay.getFeatures()
        #pump_fts = self.params.pumps_vlay.getFeatures()

        for feat in junc_fts:
            sindex.addFeature(feat)
            j+=1
        for feat in res_fts:
            sindex.addFeature(feat)
            res.append(feat.attribute(Reservoir.field_name_eid))
            res_elev.append(feat.attribute(Reservoir.field_name_elev))
            r+=1
        #logger.progress("Reservoir: "+str(res))
        # for feat in tank_fts:
        #     sindex.addFeature(feat)
        #     t+=1

        if len(res) != 1:        #check to see if there is a single reservoir.  Analysis assumes that all end nodes are pumps pump to a single outlet
            logger.error("The number of reserviors in the network must equal 1.")


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

        #logger.progress("Node_props:\n", Node_props)

        #logger.progress(str(Pipe_nodes))
        #logger.progress("Node_props: \n", Node_props)
        #logger.progress(Node_props.dtypes)
        #logger.progress("'Pipe_nodes' and 'Pipe_props' vectors populated...")

        return [Pipe_props, Node_props, Pipe_nodes, res, res_elev]


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
