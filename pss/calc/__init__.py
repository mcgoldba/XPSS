from qgis.core import *
import qgis.utils
import sys
import numpy as np
import pandas as pd
import warnings

import scipy.interpolate as interp
import scipy.linalg as sla
from scipy import optimize
from scipy.optimize import curve_fit
from scipy.sparse import csr_matrix
from XPSS.pss.report import Report
from XPSS.pipedatabase import PipeMaterial, PipeClass

from XPSS.pss import PSS

from XPSS.logger import Logger

logger = Logger()

class Calc(PSS):
    PipeMaterialName = {}
    PipeMaterialName[PipeMaterial.PVC] = 'PVC'
    PipeMaterialName[PipeMaterial.HDPE] = 'HDPE'
    PipeClassName = {}
    PipeClassName[PipeClass.PVC_Sch40] = 'PVC Sch. 40'
    PipeClassName[PipeClass.HDPE_DR11] = 'HDPE DR11'
    def __init__(self, dockwidget):
        super().__init__(dockwidget)
        self.Q = None # flowrates
        self.P = None # pressures
        self.Qc = None # flowrate corrections
        self.Pc = None #pressure corrections
        self.S = None #Static heads (elevations)

        [self.C, self.C_n, self.B, self.pipeProps,
        self.pipeSortList, self.nodeSortList] = \
        self.create_conn_matrix(self.pipeNodeProps, self.pipeProps,
                       self.nodeProps, self.res,
                       self.numEntityErr, self.nPipes, self.nNodes)

        self.A = self.B[1:] 

    from .linearsolver import linearsolver
    #from .get_pump_curve import get_pump_curve
    #from .get_flow_pump_curve import get_flow_pump_curve

    def create_conn_matrix(self, Pipe_nodes_pd, Pipe_props_pd, Node_props_pd, res, num_entity_err, num_pipes, num_nodes): #TODO:  Convert C to be equivalent to the incidence matrix in graph theory.
        #TODO:  Currently, C is represented as an upper triangular matrix.  This should be modified so that it is Symmetric, i.e C = C + C^T.  Need to see if the affects anything in the existing code.
        """ {Function}
                Create two matrices, "C" and "C_n" that define the geometry of a connected graph system, ordered from the reservior upstream.  C, is the connection matric for pipes, and C_n is the connection matrix of nodes.  Each defines which pipes / nodes are immediately downstream of the current pipe / node. "C_n", is essentilly the adjacency matrix in graph theory.
            {Variables}
                Pipe_nodes_pd:
                    (Pandas Dataframe) unsorted list of Pipes and connected junctions based on ordering of QGIS features.
                Pipe_props_pd:
                    (Pandas Dataframe) unsorted list of Pipe attributes based on ordering of QGIS features.
                Node_props_pd:
                    (Pandas Dataframe) unsorted list of node attributes based on ordering of QGIS features.  This includes all junctions, but not the reservoir
                res:
                    ()

            {Outputs}
                C:
                    (2D Numpy array) Pipe connection matrix.  A square symmetric matrix that defines how pipes are connected within the network.  Each row indicates the current pipe, and each column represents potentially connected pipes.  a value of 1 indicates the pipes are connected.  A value of 0 indicates no connection.  All digonal entries are 0.  Sorted from the reservoir upstream (breadth-first search).
                C_n:
                    (2D Numpy array)  Node connection matrix (adjacency matrix) A square matrix with dimension equal to the number of nodes.  Rows indicate the current node.  Columns indicate the nodes with edges connecting the current node.  Sorted from the reservoir upstream (breadth-first search).  For directed tree graphs, this matrix is strictly upper triangular.
                In:
                    (2D Numpy array) Incidence matrix.  Rows are an ordered list of all nodes.  Columns are an ordered list of all edges.  Matrix entry In_{ij} is 1 if the ith node is connected to the jth edge, and zero otherwise.
        """

        Pipe_nodes = Pipe_nodes_pd.to_numpy()
        Pipe_props = Pipe_props_pd.to_numpy()
        Node_props = Node_props_pd.to_numpy()


        #self.log_progress("num_entity_err: ", num_entity_err)
        #self.log_progress("Pipe_nodes: ", Pipe_nodes)
        #self.log_progress("Pipe_props: ", Pipe_props)

        #BUILD THE CONNECTION MATRIX

        #C = [ [0] * len(Pipe_nodes) for _ in range(len(Pipe_nodes))]
        C = np.zeros((len(Pipe_nodes),len(Pipe_nodes)))
        #self.log_progress("Pipe_nodes: ", len(Pipe_nodes))
        #self.log_progress("C: ", len(C))

        #self.log_progress("Connection matrix initialized...")
        #1.  Find the pipes that contain a node that has only one pipe connected (i.e.  end nodes)
        #2.  loop through each of these pipes and determine how many junctions are between the end node and the reservior
        #3.  determine the maximum value of #2 for all end nodes, (label this "N")
        #(May be able to revise so that steps above this line are not needed)
        #4a.  initialize an loop counter "count = 0"
        count = 0
        #4b.  create an array "pipe_list" that contains a list of the row location of the pipes connected to the reservior

        pipe_lst = []  #sorted list of pipes from the discharge reservior upstream
        node_lst = [res[0]]  #sorted list of nodes from the discharge reservior upstream
        Dstream_pipe = [res[0]] #sorted list of the pipe that is downstream of the current pipe

        num_pipes = len(self.pipe_fts.index)
        num_nodes = len(self.junc_fts.index) + len(self.res_fts.index)

        if num_pipes > num_nodes-1:
            C_n = np.zeros((num_pipes+1, num_pipes+1))  #initialization if there is a geometry error.
            In = np.zeros((num_pipes+1, num_pipes))
        else:
            C_n = np.zeros((num_nodes, num_nodes))  #typical initialization
            In = np.zeros((num_nodes, num_pipes))



            #all_pipes = Pipe_props

        In[0][0] = 1 # The first pipe in the list is connected to the reservoir

        #self.log_progress(C_n)

        #get edu info from qepanet
        num_edu = self.pipe_fts['num_edu'].to_numpy(dtype='int')

        #self.log_progress(str(num_edu))

        for i in range(len(Pipe_nodes)):  #NOTE:  Does this work if more than 1 pipe is connected to the reservoir?
            if (Pipe_nodes[i][1] == res[0]):
                pipe_lst.append([i, 1])
                node_lst.append(Pipe_nodes[i,2])  # add the upstream node of the first pipe to the node list
                C_n[0][1] = 1  #The node jut added to "node_lst is adjacent to the reservoir
            elif (Pipe_nodes[i][2] == res[0]):
                pipe_lst.append([i, 2])
                node_lst.append(Pipe_nodes[i,1])
                C_n[0][1] = 1
        #self.log_progress("Sorted list of Pipes from reservior: "+str(pipe_lst))
        #5.  If count < len(pipe_list):
        #while count < len(pipe_lst):
        #for count in range(len(pipe_lst)):
        error_lst = []


        try:
            while True:
                #self.log_progress("Pipe_lst: ", len(pipe_lst))
                #self.log_progress("count: ", count)
                if (C.sum(axis=1) != 0).all():   #check to see if any rows in the C matrix have all zeros (axis=1 are rows for numpy)
                    break
                #if (count >= len(pipe_lst)) or (count >= len(C)): # or count >= len(node_lst)-2:
                    #num_entity_err=True
                    #self.log_progress("Processed ", count, " out of ", len(C), " pipes.")
                    #break
                C[count][count] = 1  #set all diagonal elements to 1 indicating it is an end branch
            #   find the upstream node node corresponding to the current pipe
                found = 0
    #            for i in range(2):
    #                if Pipe_nodes[pipe_lst[count][i+1] != pipe_lst[count]:
    #                    node_in = Pipe_nodes[count][i+1]
    #                    if found == 1:
    #                        self.log_progress("ERROR:  Something went wrong while searching for upstream node connection for Pipe "+ Pipe_nodes[count][1] )
    #                        raise ValueError()
    #                    found = 1

                if pipe_lst[count][1] == 1:  #get the index of the downstream node for the current pipe
                    j = 2  #upstream node index
                elif pipe_lst[count][1] == 2:
                    j = 1
                else:
                    self.log_error("Something went wrong while searching for upstream node connection for Pipe " + str(Pipe_nodes[count][1]))
                node_in = Pipe_nodes[pipe_lst[count][0]][j]  #store the qepanet name of the upstream(?) node
                #node_lst.append(node_in)
                In[count+1][count] = 1  #upstream node For a directed tree graph, the diagonal entries of the squrae matrix with the first row removed is always 1.
                #self.log_progress("Incidence Matrix: \n", In)

            #   a.  (Work from the reservior / Outlet upstream) for each entry # "count" in the pipe list determine the number of pipes connected to the junction.
                for pipe in range(len(Pipe_nodes)):
                    for j in range(1,3):
                        if (Pipe_nodes[pipe][j] == node_in  and pipe != pipe_lst[count][0]):
                            pipe_lst.append([pipe, j])
                            if j == 1:
                                node_lst.append(Pipe_nodes[pipe][2])
                            else:
                                node_lst.append(Pipe_nodes[pipe][1])
                            Dstream_pipe.append(Pipe_nodes[pipe_lst[count][0]][0])
                            C[count][len(pipe_lst)-1] = 1
                            C[count][count] = 0 #If the pipe has a pipe connected to the upstream node, it is not a branch of the system and does not have a pump attached.

                            C_n[count+1][len(node_lst)-1] = 1  #Polulate the node connection matrix (this only works for directed tree graphs where the #nodes = #pipes+1)
                            In[count+1][ len(node_lst)-2 ] = 1  #downstream node
                            #self.log_progress("Adjacency Matrix \n", C_n)
                            #self.log_progress("Pipe List: ", pipe_lst)
                            #self.log_progress("Node List: ", node_lst)
                            #self.log_progress("Pipe Nodes \n", Pipe_nodes)
                            #self.log_progress(C_n)
                            #self.log_progress("Incidence Matrix:\n", In)
                            #Collect all connected pipes


                    #if (C[count][count] == 1 and num_edu[pipe_lst[count][0]]):  #if the pipe is an end branch and the number of EDUs is defined in qepanet, overwrite the default value of num_edu
                        #C[count][count] = num_edu[pipe_lst[count][0]]
                #self.log_progress(str(C))
                #self.log_progress("pipe_lst = "+str(pipe_lst))
                #self.log_progress("Downstream_pipe = "+str(Dstream_pipe))

                #check if the current pipe is connected back to the reservoir
    #            row = True
    #            current_node = C_n[:][count+1]
    #
    #            while np.sum(current_node) > 1:
    #                for i in range(len(current_node)):
    #                    if current_node[i] == 1:
    #                        if row:
    #                            current_node = C_n[:][i]
    #                            row = False
    #                            break
    #                        else:
    #                            current_node = C_n[i]
    #                            row = True
    #                            break
    #
    #            if current_node[0] != 1:
    #                i = 0
    #                while current_node[i] != 1:
    #                    if i < len(current_node) - 1:
    #                        not_found = True
    #                        break
    #                    i += 1
    #                if not not_found:
    #                    raise Exception("ERROR:  Node ",node_lst[i], " is disconnected from the Reservior")

                count += 1



        except:
            self.log_progress("Processed "+str(count)+" out of "+ str(len(C))+" pipes.")
            self.log_progress("Errors found in the system geometry:")
            self.log_progress("\tNumber of Pipes: "+str(num_pipes))
            self.log_progress("\tNumber of Nodes: "+str(num_nodes))
            self.log_progress("Locating discontinuities...")
            self.analyze_system_connectivity(Pipe_nodes, pipe_lst, node_lst)
            #raise Exception("ERROR:  The system geometry is not correct!")
        if num_entity_err is True:  #if an error was raised during check(),check for overlaps, then do the same as above

            #loop through qgis features and check for overlap
            overlap_nodes = []

            for col in range(len(In[0])):
                junc_fts = self.params.junctions_vlay.getFeatures()
                index = 0
                while In[index][col] == 0:
                    index += 1
                upstream_eid = node_lst[col+1]
                downstream_eid = node_lst[index]

                #self.log_progress("Checking overlap on Nodes "+upstream_eid+" and "+downstream_eid+"...")

                upstream_found = False
                downstream_found = False

                if downstream_eid == res[0]:
                    for feat in self.params.reservoirs_vlay.getFeatures():  #assumes there is only 1 reservoir
                        downstream_pt = feat.geometry()
                        downstream_found = True
                        break

                for feat in junc_fts:           #TODO:  Is there a better way to do this?
                    if (upstream_found == False) and (str(feat.attribute(Junction.field_name_eid)) == upstream_eid):
                        upstream_pt = feat.geometry()
                        upstream_found = True
                    if (downstream_found == False) and (str(feat.attribute(Junction.field_name_eid)) == downstream_eid):
                        downstream_pt = feat.geometry()
                        downstream_found = True
                    if (upstream_found is True) and (downstream_found is True):
                        break

                if upstream_found is False:
                    self.log_error("Point not found for junction "+upstream_eid, stop=True)

                if downstream_found is False:
                    self.log_error("Downstream point not found for junction "+downstream_eid, stop=True)

                if NetworkUtils.points_overlap(upstream_pt, downstream_pt, self.params.tolerance) is not False:
                    overlap_nodes.append(upstream_eid)  #TODO: improve so that it doesnt append the same feature twice
                    overlap_nodes.append(downstream_eid)

            if len(overlap_nodes) > 0:
                self.select_qgis_features(self.params.junctions_vlay, overlap_nodes)
                self.log_error("Overlapping features were found:")
                self.log_error(str(overlap_nodes), stop=True)

            self.log_progress("Processed "+str(count)+" out of "+ str(len(C))+" pipes.")
            self.log_progress("Errors found in the system geometry:")
            self.log_progress("\tNumber of Pipes: "+str(num_pipes))
            self.log_progress("\tNumber of Nodes: "+str(num_nodes))
            self.log_progress("Locating discontinuities...")
            self.analyze_system_connectivity(Pipe_nodes, pipe_lst, node_lst)
            #raise Exception("ERROR:  The system geometry is not co

        #       -  for each pipe:
        #           -  determine its location within the connection matrix (based on location within "Pipe_Node" Matrix)
        #           -  set the diagonal entry to 1
        #           -  find all pipes that share the same node as the upstream node within the pipe
        #           -  for each pipe:
        #               -  find the row location of the pipe within the "Pipe_Node" matrix
        #               -  set the corresponding column entry within the connection matrix for the current node in "node_list" equal to "-1".
        #               -  append the row location in "Node_List" to the "pipe_list" array.

        #df = pd.DataFrame(Dstream_pipe, columns="Downstream Connected Pipe")

        C_n = C_n + C_n.T  #Get a symmetric matrix
        #self.log_progress("Adjacency Matrix \n", C_n)
        #self.log_progress("Pipe List: ", pipe_lst)
        #self.log_progress("Node List: ", node_lst)
        #self.log_progress("Pipe Nodes \n", Pipe_nodes)
        new_index = []

        for i in range(len(pipe_lst)):
            new_index.append(pipe_lst[i][0])


        Pipe_props_pd = Pipe_props_pd.reindex(new_index)  #reorder the rows in decending order from the reservior to the branches (same as connection matrix)

        Pipe_props_pd.insert(loc=1, column='Downstream Connected Pipe', value=Dstream_pipe)

        #self.log_progress(str(Pipe_props_pd))

        #self.log_progress("Connection matrix populated...")

        for i in range(len(C)):  #check to see that all diagonal elements of the connection matrix are  = 1.
                                 #this also ensures that all of the pipe elements were lopped through in the while loop above.
            if np.sum(C[i]) == 0:
                self.log_error("The connection matrix was not populated completely.", stop=True)

        sort_lst = [0 for row in range(len(pipe_lst))]  #create list to map location of qepanet features to pandas index format
        for i in range(len(pipe_lst)):
            sort_lst[i] = pipe_lst[i][0]


        #self.log_progress("node_lst: ", node_lst)

        node_srt_lst = [ 0 for i in range(len(node_lst)-1)]
        node_prop_np = Node_props_pd['Node ID'].astype(str)

        #self.log_progress("Node list:\n", node_lst)
        #self.log_progress("Node props:\n", node_prop_np)

        for i in range(1,len(node_lst)):
            #index = Node_props_pd.index[Node_props_pd['Node ID'].astype(str)==node_lst[i]].tolist()
            for j in range(len(node_prop_np)):
                if node_prop_np[j] == node_lst[i]:
                #    break
                #self.log_progress(index)
                    node_srt_lst[i-1] = j

        #self.log_progress("Node sort list:\n", node_srt_lst)

        return [C, C_n, In, Pipe_props_pd, sort_lst, node_srt_lst]
