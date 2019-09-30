from qgis.core import *
import qgis.utils
import sys
import numpy as np
import pandas as pd


from qepanet.model.network import *       #Pipe, Reservoir, Junction, etc.  variables are defined here
from qepanet.model.network_handling import NetworkUtils
from qepanet.model.inp_writer import InpFile
from qepanet.tools.parameters import Parameters


class PSSDataMod:

    def __init__(self):
        self.qepa = qgis.utils.plugins["qepanet"]
        self.params = self.qepa.params  #refer to the parameters stored in the existing instance of qepanet
        self.pipe_fts = pd.DataFrame(self.params.pipes_vlay.getFeatures(),columns=[field.name() for field in self.params.pipes_vlay.pendingFields() ])  #extract pipe attribute table as a pandas array
        self.junc_fts = pd.DataFrame(self.params.junctions_vlay.getFeatures(),columns=[field.name() for field in self.params.junctions_vlay.pendingFields() ])  #extract pipe attribute table as a pandas array
        self.res_fts = pd.DataFrame(self.params.reservoirs_vlay.getFeatures(),columns=[field.name() for field in self.params.reservoirs_vlay.pendingFields() ])  #extract pipe attribute table as a pandas array
        
    def check(self):
        #TODO:  rewrite to use a pandas dtaframe
        
        pipe_fts = self.params.pipes_vlay.getFeatures()
        junc_fts = self.params.junctions_vlay.getFeatures()
        res_fts = self.params.reservoirs_vlay.getFeatures()
        tank_fts = self.params.tanks_vlay.getFeatures()
        pump_fts = self.params.pumps_vlay.getFeatures()
        

        print("%%%%%%%%%%% BEGIN CHECK OF PSS SYSTEM %%%%%%%%%%%")
        
        #get system details from the qgis vector layers (a lot of this taken from in_writer.py in qepanet)

        node_lst = [junc_fts, res_fts, tank_fts]
        node_Class = [Junction, Reservoir, Tank]

        pipe_lst = [pipe_fts, pump_fts]
        pipe_Class = [Pipe, Pump]


        # Build nodes spatial index
        #sindex = QgsSpatialIndex()
        res = []
        j=0
        r=0
        t=0
        l=0
        p=0

        has_error = False
        print("Summary of System Components:")
        for feat in junc_fts:
            #sindex.insertFeature(feat)
            j+=1
        print(str(j)+" Junctions")
        for feat in res_fts:
            #sindex.insertFeature(feat)
            res.append(feat.attribute(Reservoir.field_name_eid))
            r+=1
        print(str(r)+" Reservoirs")
        for feat in tank_fts:
            #sindex.insertFeature(feat)
            t+=1
        print(str(t)+" Tanks")
        for feat in pipe_fts:
            l+=1
        print(str(l)+" Pipes")
        for feat in pump_fts:
            p+=1
        print(str(p)+" Pumps")

        if len(res) != 1:        #check to see if there is a single reservoir.  Analysis assumes that all end nodes are pumps pump to a single outlet
            print("ERROR:  The number of reserviors in the network must equal 1.")
            has_error = True
        
        print("Cycling through all pipes to check connections...")

        Pipe_nodes = []

        for i in range(len(pipe_lst)):
            for pipe_ft in pipe_lst[i]:


                eid = pipe_ft.attribute(pipe_Class[i].field_name_eid)
                #print(eid)

                # Find start/end nodes
                # adj_nodes = NetworkUtils.find_start_end_nodes(params, pipe_ft.geometry())
                adj_nodes = NetworkUtils.find_start_end_nodes_sindex(self.params, sindex, pipe_ft.geometry())

                try:    
                    start_node_id = adj_nodes[0].attribute(Junction.field_name_eid)
                    end_node_id = adj_nodes[1].attribute(Junction.field_name_eid)

                    Pipe_nodes.append([eid, start_node_id, end_node_id]) 

                except:
                    print_str = "" 
                    if start_node_id:
                        print_str += " "+start_node_id
                    if end_node_id:
                        print_str += " "+end_node_id
                    print("ERROR: Pipe "+eid+" has less than 2 nodes connected.  Connected nodes are"+print_str+".")
                    has_error = True

        print(str(Pipe_nodes))
                    
        print("Cycling through all nodes to check connections...")
        for i in range(len(node_lst)):        
            for node in node_lst[i]:
                num_conn = 0
                eid = node.attribute(node_Class[i].field_name_eid)
                for j in range(len(Pipe_nodes)):
                    if Pipe_nodes[j][1] == eid:
                        num_conn += 1
                    if Pipe_nodes[j][2] == eid:
                        num_conn += 1
                if num_conn == 0:
                    print("ERROR:  The node "+eid+" is not connected to any pipes.")
                    has_error = True


        if has_error != True:
            print("There are no errors found in the system!")
        else:
            print("Error(s) were found.  Check the system definition and correct.")
        
        print("%%%%%%%%%%% END CHECK OF PSS SYSTEM %%%%%%%%%%%")
        
        return has_error

    
    def initialize_from_qepanet(self):

        #get system details from the qgis vector layers (a lot of this taken from in_writer.py in qepanet)
        

        #Initalize data Matrices and vectors for calculations

        C = []  #Connection matrix:  describes how each pipe the pipes are connected together
        Pipe_props_raw = []  #Pipe Property Matrix:  stores properties of each pipes as 
                        # [ id, length, diameter, C, minor_loss, num_edu ]
        Pipe_nodes_raw = []  #Pipe Nodes:  stores pipe start and end nodes to build thet connection matrix

        # Build nodes spatial index
        sindex = QgsSpatialIndex()
        res = []
        j=0
        r=0
        t=0
        
        pipe_fts = self.params.pipes_vlay.getFeatures()
        junc_fts = self.params.junctions_vlay.getFeatures()
        res_fts = self.params.reservoirs_vlay.getFeatures()
        tank_fts = self.params.tanks_vlay.getFeatures()
        pump_fts = self.params.pumps_vlay.getFeatures()
        
        for feat in junc_fts:
            sindex.insertFeature(feat)
            j+=1
        for feat in res_fts:
            sindex.insertFeature(feat)
            res.append(feat.attribute(Reservoir.field_name_eid))
            r+=1
        print("Reservoir: "+str(res))
        for feat in tank_fts:
            sindex.insertFeature(feat)
            t+=1

        if len(res) != 1:        #check to see if there is a single reservoir.  Analysis assumes that all end nodes are pumps pump to a single outlet
            raise Exception("ERROR:  The number of reserviors in the network must equal 1.")


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
        
        #Node_props = self.junc_fts['id', 'elev_dem', 'zone_end']
        
        Pipe_nodes = pd.DataFrame(Pipe_nodes_raw, columns = ['Pipe ID', 'Node 1 ID', 'Node 2 ID'])
        Pipe_props = pd.DataFrame(Pipe_props_raw, columns = ['Pipe ID'], dtype='float')

        print(str(Pipe_nodes))
        print(str(Pipe_props))
        print("'Pipe_nodes' and 'Pipe_props' vectors populated...")
        
        return [Pipe_props, Pipe_nodes, res]
    
    def get_qepanet_pipe_props(self, Pipe_props, get_lst, pd_names, sort_lst=False):
        
#        add_atri = []
#        
#        for j in range(len(get_lst)):
#            for pipe_ft in self.params.pipes_vlay.getFeatures():
#                pipe_atri = []
#                if get_lst[j] == 'length':
#                    pipe_atri.append(pipe_ft.attribute(Pipe.field_name_length))
#                elif get_lst[j] =='diameter':
#                    add_atri[i][j] = pipe_ft[i].attribute(Pipe.field_name_diameter)
#                elif get_lst[j] == 'roughness':
#                    add_atri[i][j] = pipe_ft[i].attribute(Pipe.field_name_roughness)
#                elif get_lst[j] == 'minor_loss':
#                    add_atri[i][j] = pipe_ft[i].attribute(Pipe.field_name_minor_loss)
#                elif get_lst[j] == 'status':
#                    add_atri[i][j] = pipe_ft[i].attribute(Pipe.field_name_status)
#                elif get_lst[j] == 'description':
#                    add_atri[i][j] = pipe_ft[i].attribute(Pipe.field_name_description)
#                elif get_lst[j] == 'tag_name':
#                    add_atri[i][j] = pipe_ft.attribute(Pipe.field_name_tag)
#                else:
#                    raise Exception("ERROR: Specified value does not match any vector layer attribute")
                #num_edu = pipe_ft.attribute(Pipe.field_name_num_edu)

        #sort_lst = map(str, sort_lst)  #convert the array of ints to an array of strings
        df = self.pipe_fts.filter(get_lst, axis=1) #extract columns from qepanet data
        df.columns = pd_names #rename the columns
        if sort_lst:
            df = df.reindex(index=sort_lst)  #rearrange the pipes within the pamdas dataframe to be sorted from the Reservoir upstream
        df = df.reset_index(drop=True)  # rename indices to match those pf "Pipe_props" i.e. [0, 1, 2, 3, 4...]
    
        #Pipe_props, df = [d.reset_index(drop=True) for d in (Pipe_props, df)]

        Pipe_props = pd.concat([Pipe_props, df], axis=1)
#        for i in range(len(get_lst)):
#            add_atri = self.pipe_fts.iloc[:,self.pipe_fts.columns.get_loc(get_lst[0])].to_numpy        
#                            
#            df = pd.DataFrame(data=add_atri, columns=[pd_name[i]])
#        
#            df.reset_index(drop=True, inplace=True)
#            Pipe_props.reset_index(drop=True, inplace=True)
#    
#            Pipe_props = pd.concat([Pipe_props, df], axis=1)
        
        return Pipe_props
    
    def get_qepanet_junc_props(self, Node_props, get_lst, pd_names, sort_lst):
        
        
        df = self.junc_fts.filter(get_lst, axis=1) #extract columns from qepanet data
        df.columns = pd_names #rename the columns
        print(str(sort_lst))
        df = df.reindex(index=sort_lst)  #rearrange the pipes within the pamdas dataframe to be sorted from the Reservoir upstream
        df = df.reset_index(drop=True)  # rename indices to match those pf "Pipe_props" i.e. [0, 1, 2, 3, 4...]
    
        #Pipe_props, df = [d.reset_index(drop=True) for d in (Pipe_props, df)]

        Node_props = pd.concat([Pipe_props, df], axis=1)
    
    def create_conn_matrix(self, Pipe_nodes_pd, Pipe_props_pd, res):
        
        Pipe_nodes = Pipe_nodes_pd.to_numpy()
        Pipe_props = Pipe_props_pd.to_numpy()
        
        print(str(Pipe_nodes))
        print(str(Pipe_props))
        
        #BUILD THE CONNECTION MATRIX

        #C = [ [0] * len(Pipe_nodes) for _ in range(len(Pipe_nodes))]
        C = np.zeros((len(Pipe_nodes),len(Pipe_nodes)))

        print("Connection matrix initialized...")
        #1.  Find the pipes that contain a node that has only one pipe connected (i.e.  end nodes)
        #2.  loop through each of these pipes and determine how many junctions are between the end node and the reservior
        #3.  determine the maximum value of #2 for all end nodes, (label this "N")
        #(May be able to revise so that steps above this line are not needed)
        #4a.  initialize an loop counter "count = 0"
        count = 0
        #4b.  create an array "pipe_list" that contains a list of the row location of the pipes connected to the reservior
        
        pipe_lst = []  #sorted list of pipes from the discharge reservior upstream
        node_lst = []  #sorted list of nodes from the discharge reservior upstream
        Dstream_pipe = [res[0]] #sorted list of the pipe that is downstream of the current pipe
        
        #get edu info from qepanet
        num_edu = self.pipe_fts['num_edu'].to_numpy(dtype='int')
        
        print(str(num_edu))
        
        for i in range(len(Pipe_nodes)):
            if (Pipe_nodes[i][1] == res[0]):
                pipe_lst.append([i, 1])            
            elif (Pipe_nodes[i][2] == res[0]):
                pipe_lst.append([i, 2])
        print("Sorted list of Pipes from reservior: "+str(pipe_lst))
        #5.  If count < len(pipe_list):
        #while count < len(pipe_lst):
        #for count in range(len(pipe_lst)):
        while True:
            
            if ((C.sum(axis=1)!=0).all()):   #check to see if any rows in the C matrix have all zeros (axis=1 are rows for numpy)
                break
            C[count][count] = 1  #set all diagonal elements to 1 indicating it is an end branch
        #   find the upstream node node corresponding to the current pipe
            found = 0
#            for i in range(2):
#                if Pipe_nodes[pipe_lst[count][i+1] != pipe_lst[count]:
#                    node_in = Pipe_nodes[count][i+1]
#                    if found == 1:
#                        print("ERROR:  Something went wrong while searching for upstream node connection for Pipe "+ Pipe_nodes[count][1] )
#                        sys.exit()
#                    found = 1
            if pipe_lst[count][1] == 1:  #get the index of the upstream node for the current pipe
                j = 2
            elif pipe_lst[count][1] == 2:
                j = 1
            else:
                raise Exception("ERROR:  Something went wrong while searching for upstream node connection for Pipe "+ Pipe_nodes[count][1])
            node_in = Pipe_nodes[pipe_lst[count][0]][j]  #store the qepanet name of the upstream node
            
        #   a.  (Work from the reservior / Outlet upstream) for each entry # "count" in the pipe list determine the number of pipes connected to the junction.
            for pipe in range(len(Pipe_nodes)):
                for j in range(1,3):
                    if (Pipe_nodes[pipe][j] == node_in  and pipe != pipe_lst[count][0]):
                        pipe_lst.append([pipe, j])
                        Dstream_pipe.append(Pipe_nodes[pipe_lst[count][0]][0])
                        C[count][len(pipe_lst)-1] = 1
                        C[count][count] = 0 #If the pipe has a pipe connected to the upstream node, it is not a branch of the system and does not have a pump attached.
                #if (C[count][count] == 1 and num_edu[pipe_lst[count][0]]):  #if the pipe is an end branch and the number of EDUs is defined in qepanet, overwrite the default value of num_edu
                    #C[count][count] = num_edu[pipe_lst[count][0]]
            print(str(C))
            print("pipe_lst = "+str(pipe_lst))
            print("Downstream_pipe = "+str(Dstream_pipe))
            count += 1

        #       -  for each pipe:
        #           -  determine its location within the connection matrix (based on location within "Pipe_Node" Matrix)
        #           -  set the diagonal entry to 1
        #           -  find all pipes that share the same node as the upstream node within the pipe
        #           -  for each pipe:  
        #               -  find the row location of the pipe within the "Pipe_Node" matrix 
        #               -  set the corresponding column entry within the connection matrix for the current node in "node_list" equal to "-1".
        #               -  append the row location in "Node_List" to the "pipe_list" array.

        #df = pd.DataFrame(Dstream_pipe, columns="Downstream Connected Pipe")
        
        new_index = []
        
        for i in range(len(pipe_lst)):
            new_index.append(pipe_lst[i][0])

        
        Pipe_props_pd = Pipe_props_pd.reindex(new_index)  #reorder the rows in decending order from the reservior to the branches (same as connection matrix)
        
        Pipe_props_pd.insert(loc=1, column='Downstream Connected Pipe', value=Dstream_pipe)
        
        print(str(Pipe_props_pd))

        print("Connection matrix populated...")
            
        for i in range(len(C)):  #check to see that all diagonal elements of the connection matrix are  = 1.
                                 #this also ensures that all of the pipe elements were lopped through in the while loop above.
            if np.sum(C[i]) == 0:
                raise Exception("ERROR: The connection matrix was not populated completely.")

        sort_lst = [0 for row in range(len(pipe_lst))]  #create list to map location of qepanet features to pandas index format
        for i in range(len(pipe_lst)):
            sort_lst[i] = pipe_lst[i][0]
            
        return [C, Pipe_props_pd, sort_lst]
        

    def get_qepanet_elev_data(self, Pipe_props, Pipe_nodes, sort_lst, res):
        
        Pipe_nodes = Pipe_nodes.to_numpy()
        
        max_elev = -1e12 #set the initial maximum elevation to a very small value that will be overwritten
        pipe_min_elev = [0 for i in range(len(sort_lst))]
        
        #get the minimum elevation of each pipe section
        p=-1
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
            pipe_min_elev[p] = min(elev)
            if max(elev) > max_elev:
                max_elev = max(elev)
            del elev
        
#        min_elev_sort = []
#        
#        for i in range(len(pipe_min_elev)):
#            min_elev_sort.append(pipe_min_elev[sort_lst[i]])
        
        Pipe_props = self.append_col_to_table(Pipe_props, pipe_min_elev, "Minimum Elevation [ft]", data_type="float", sort=sort_lst)
        
        Pipe_props = self.append_col_to_table(Pipe_props, np.subtract(max_elev,pipe_min_elev), "Static Head [ft]", data_type="float", sort=sort_lst)
        
        return [Pipe_props, max_elev, elev_out]
        
        
    def append_col_to_table(self, Pipe_props, col, title, data_type=False, sort=False):
        if data_type:
            df = pd.DataFrame(data=col, columns=[title], dtype=data_type)
        else:
            df = pd.DataFrame(data=col, columns=[title])
            
        if sort:
            df = df.reindex(index=sort)  #rearrange the pipes within the pandas dataframe to be sorted from the Reservoir upstream

        
        df.reset_index(drop=True, inplace=True)
        Pipe_props.reset_index(drop=True, inplace=True)
    
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
    
    def filter_small_pipes(self, C, Pipe_props, Pipe_nodes, sort_lst, C_factor, l_material, res):
        
        #extract data from the Pipe_nodes dataframe
        Pipe_nodes = Pipe_nodes.to_numpy()
        
        #get array of zone end nodes sorted according to qgis vlayers
        End_nodes = self.junc_fts[['id','zone_end']]
        Zone_id = [0 for i in range(len(Pipe_props))]  # vector of Zone ID's sorted according to C matrix          

        #get a sparse list of end nodes(i.e. contains only nodes that are end nodes)
        End_nodes_sparse = []
        for en in range(len(End_nodes.index)):
            if End_nodes.loc[en,'zone_end'] == 1:  #find nodes that are labeled as end nodes
                End_nodes_sparse.append(End_nodes.loc[en,'id'])  #get node id
                
        #get sorted list of end_nodes from most upstream
        End_nodes_sort = []
        for i in range(len(sort_lst)):
            if (Pipe_nodes[sort_lst[i]][1] in End_nodes_sparse) and (not Pipe_nodes[sort_lst[i]][1] in End_nodes_sort):
                End_nodes_sort.append(Pipe_nodes[sort_lst[i]][1])
            if (Pipe_nodes[sort_lst[i]][2] in End_nodes_sparse) and (not Pipe_nodes[sort_lst[i]][2] in End_nodes_sort):
                End_nodes_sort.append(Pipe_nodes[sort_lst[i]][2])
        print(str(End_nodes_sort))
        
        End_pipes_sort = []

        End_pipes = []  #list of pipes that are connected to end nodes
        
        #parse system from reservoir upstream and assign Zone IDs to pipes        
        #for en in range(len(End_nodes_sort)):
        for end_id in End_nodes_sort:
            End_pipes_current = []
            for p, pipe in enumerate(Pipe_nodes):
#                    print(str(p))
#                    print(str(pipe))
#                    print(str(pipe[1]))
#                    print(str(pipe[2]))
#                    print(str(end_id))
                if pipe[1] == end_id or pipe[2] == end_id:  #find pipes that are connected to the current end node
                    if not p in End_pipes:
                        End_pipes_current.append(p)  #get indices for these pipes in Pipe_nodes
            End_pipes.append(End_pipes_current)
            print("sort_lst: "+str(sort_lst))
            print("List of unsorted end pipe indices: "+str(End_pipes))
        #create a sorted list of pipe indices (according to C) that are connected to end nodes
            #get an unsorted list of C matrix indices
        End_pipes_sort = []
        #for end_id in End_nodes_sort:        
        for row in End_pipes:
            End_pipes_sort_row = []
            for j, item  in enumerate(sort_lst):
                if item in row:
                    print("Enter Loop")
                    End_pipes_sort_row.append(j)
            End_pipes_sort.append(End_pipes_sort_row)
        print("List of sorted end pipe indices: "+str(End_pipes_sort))   
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
                
        print("List of sorted end pipe indices: "+str(End_pipes_sort))        

        
    #parse system from reservoir upstream and assign Zone IDs to pipes  
        zone_id = 1  #current zone_id
    
        #define zone 1 downstream of the first zone end node
        for i in range(End_pipes_sort[0][0]+1):
            Zone_id[i] = zone_id
        zone_id+=1
        #define all zones upstream of the first end zone node:
        print(str(Zone_id))
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
#                            print("Zone_id: "+str(Zone_id))
#                            print("zone_branch: "+str(zone_branch))
#                        #for each new zone iterate to next end nodes pipe and define zone
#                            for br in range(len(zone_branch)):
#                                Zone_conn = [zone_branch[br]]  #array of connected pipes in this zone
#                                b = 0
#                                while True:
#                                    if (C[Zone_conn[b]][Zone_conn[b]] == 1) or (Zone_conn[b] in End_pipes_sort[en+1]) or (b == len(Zone_conn)):
#                                        break
#                                    print(str(b))
#                                    if Zone_id[Zone_conn[b]] == 0:
#                                        Zone_id[Zone_conn[b]] = Zone_id[zone_branch[br]]
#                                    for k in range(Zone_conn[b]+1,len(C[End_pipes_sort[en][i]])):
#                                        if C[Zone_conn[b]][k] == 1:
#                                            print("Appending to Zone_conn:"+str(Zone_conn))
#                                            Zone_conn.append(k)                
#                                    b+=1
#                                    print("Zone_id:"+str(Zone_id))
#                                    print("Zone_conn:"+str(Zone_conn))
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
#                            print("Zone_id: "+str(Zone_id))
#                            print("zone_branch: "+str(zone_branch))
#                        #for each new zone iterate to next end nodes pipe and define zone
#                            for br in range(len(zone_branch)):
#                                Zone_conn = [zone_branch[br]]  #array of connected pipes in this zone
#                                b = 0
#                                while True:
#                                    if (C[Zone_conn[b]][Zone_conn[b]] == 1) or (Zone_conn[b] in End_pipes_sort[en+1]) or (b == len(Zone_conn)):
#                                        break
#                                    print(str(b))
#                                    if Zone_id[Zone_conn[b]] == 0:
#                                        Zone_id[Zone_conn[b]] = Zone_id[zone_branch[br]]
#                                    for k in range(Zone_conn[b]+1,len(C[End_pipes_sort[en][i]])):
#                                        if C[Zone_conn[b]][k] == 1:
#                                            print("Appending to Zone_conn:"+str(Zone_conn))
#                                            Zone_conn.append(k)                
#                                    b+=1
#                                    print("Zone_id:"+str(Zone_id))
#                                    print("Zone_conn:"+str(Zone_conn))
#                                if Zone_id[b] == 0:
#                                    Zone_id[b] = Zone_id[zone_branch[br]]
                                    
                                    
        print("Zone_id: "+str(Zone_id))
        

        sort_lst_inv = [0 for i in range(len(sort_lst))]
        for i, item in enumerate(sort_lst):
            sort_lst_inv[sort_lst[i]] = i


        Pipe_props = self.append_col_to_table(Pipe_props, Zone_id, 'Zone ID', data_type='int', sort=sort_lst_inv)

        #Pipe_props[["Zone ID"]+[c for c in Pipe_props if c not in ["Zone ID"]]]
        print(str(Pipe_props))

        #resort columns so that the first column is Zone ID        
        cols = list(Pipe_props.columns.values)
        cols.pop(cols.index('Zone ID'))
        Pipe_props = Pipe_props[['Zone ID']+cols]
        
        print(str(Pipe_props))                     

        print(" Updating qgis vector layers...")

        self.update_pipes_vlay(Pipe_props, C_factor, l_material)

        print(" ...Done!")   
        
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
            tdh = 0
            
            df = Pipe_props.loc[Pipe_props['Zone ID'] == z+1]
            
            print(str(df))
            
            for i, row in df.iterrows():
                num_edu += int(row['Number of EDUs'])
                
                if int(row['Number Accumulated EDUs']) > accum_edu:
                    accum_edu = int(row['Number Accumulated EDUs'])
                    op_edu = int(row['Accumlated Operating EDUs'])
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
            
            print(str(d))
            
            c = ['Zone ID', 'Zone Downstream', 'Number EDUs in Zone', 'Accum. EDUs', 'Acuum. Operating EDUs', 'Max Flow [gpm]', 'Max Pipe Diameter [in]', 'Max Velocity [ft/s]', 'Pipe Length [ft]', 'Friction Loss Factor [ft/100ft]', 'Friction Loss [ft]', 'Accum. Friction Loss [ft]', 'Min Elevation [ft]', 'Max Static Head [ft]', 'Max Total Dynamic Head [ft]']
            
            if not exists:
                Zone_props = pd.DataFrame(data=np.array(d, dtype=object), index=[0], columns=c)
                exists = True
            else:
                Zone_props = Zone_props.append(pd.DataFrame(data=np.array(d, dtype=object), index=[0], columns=c), ignore_index=True)
            
#            print("for Zone "+str(z+1)+", num_edu: "+str(num_edu))
#            print("for Zone "+str(z+1)+", accum_edu: "+str(accum_edu))
#            print("for Zone "+str(z+1)+", op_edu: "+str(op_edu))
#            print("for Zone "+str(z+1)+", max_flow: "+str(max_flow))
        
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
    
    def get_inputs_dataframe(self, inputs):
        
        index = [0]
        Calc_stats = pd.DataFrame(data=inputs, index=index)
        
        return Calc_stats
    
    def update_pipes_vlay(self, Pipe_props, C_factor, l_material):
        
#        layers = QgsMapLayerRegistry.instance().mapLayersByName(self.params.pipes_vlay_name) 
#        layer = layers[0]
#        it = layer.getFeatures()
        layer = self.params.pipes_vlay 
        it = layer.getFeatures()
        
        layer.startEditing()
            
        for i, feat in enumerate(it):
            length =  Pipe_props.loc[i, 'Length [ft]']
            print(str(length))
            diameter =  Pipe_props.loc[i, 'Diameter [in]']
            print(str(diameter))
            num_edu =  Pipe_props.loc[i, 'Number of EDUs']
            print(str(num_edu))
            pipe_id = Pipe_props.loc[i, 'Pipe ID']
            print(str(pipe_id))
            if Pipe_props.loc[i, 'Zone ID']:
            #if 'Zone ID' in Pipe_props.columns:
                zone_id = int(Pipe_props.loc[i, 'Zone ID'])
            else:
                zone_id=0
            print("zone id: "+str(zone_id))
            
            data = [str(pipe_id), str(length), str(diameter), 'OPEN', str(C_factor), 0, l_material, "", "", str(num_edu), str(zone_id)]
            
            print(str(data))
            
            for j in range(len(data)):
                print(str(j))
                layer.changeAttributeValue(feat.id(), j, data[j])
                
        layer.commitChanges()
        
        