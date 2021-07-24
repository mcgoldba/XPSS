class Operations:
    def get_num_upstream_conn(self, C):
        C = -1*C
        #PSSDataMod().log_progress(str(C))
        upstream_conn = np.sum(C, axis=1) + 1
#        upstream_conn = np.zeros(len(C))
#        for i in range(len(C)):
#            for j in range(len(C)):
#                if C[i][j] = -1:
#                    upstream_conn[i] += 1
        return upstream_conn



    def populate_edus(self, C, Pipe_props, sort_lst):

        Num_edu = np.zeros(len(C))

        # read edu value from qepanet
        dataMod = PSSDataMod()

        #get "num_edu" field from qepanet
        Pipe_props = dataMod.get_qepanet_edu_data(Pipe_props, sort_lst)

        num_edu = Pipe_props['Number of EDUs'].to_numpy(dtype='int') #number of edus from qepanet

        #PSSDataMod().log_progress(str(num_edu))

        for i in range(len(C)):
            if not num_edu[sort_lst[i]]:  #if "num_edu" is not defined in qepanet
                Num_edu[i] = C[i][i]
            else: # if "num_edu" is defined in qepanet
                Num_edu[i] = C[i][i]*num_edu[sort_lst[i]]

        #PSSDataMod().log_progress("Num_edu: "+str(Num_edu))

        # initialize the "Accum_edu vector as the existing "Num_edu" vectors
        Accum_edu = [0 for i in range(len(Num_edu))]

        for i in range(len(Num_edu)):
            Accum_edu[i] = Num_edu[i]

        #PSSDataMod().log_progress(" ")
        #PSSDataMod().log_progress("Num_edu: "+str(Num_edu))
        #PSSDataMod().log_progress("Accum_edu: "+str(Accum_edu))

        Accum_edu[len(Accum_edu)-1] = 1  #the last item in the ordered list should always be a end branch with 1 EDU

        for i in range(1,len(Num_edu)):
            row = C[len(Num_edu)-i-1]  #iterate from the last row of the matrix up to the first
            Accum_edu[len(Num_edu)-i-1] = np.dot(row,Accum_edu)
            #PSSDataMod().log_progress(" ")
            #PSSDataMod().log_progress("Num_edu: "+str(Num_edu))
            #PSSDataMod().log_progress("Accum_edu: "+str(Accum_edu))

        #create unsorted arrays of Accum and Num edus for pandas array
        Accum_edu_unsort = [ 0 for i in range(len(Accum_edu))]
        Num_edu_unsort = [ 0 for i in range(len(Num_edu))]

        for i in range(len(Num_edu)):
            Accum_edu_unsort[sort_lst[i]] = Accum_edu[i]
            Num_edu_unsort[sort_lst[i]] = Num_edu[i]

        #remove the "Number of EDUs" row that was generated from 'get_qepanet_edu_data()'
        Pipe_props = Pipe_props.drop(columns=["Number of EDUs"])

        Pipe_props = self.append_col_to_table(Pipe_props, Num_edu_unsort, ['Number of EDUs'], data_type='int')

        Pipe_props = self.append_col_to_table(Pipe_props, Accum_edu_unsort, ['Number Accumulated EDUs'], data_type='int')

        return Pipe_props


    def get_num_edu(self, C, Pipe_props):
        #upstream_conn = vector of the number of upstream connections for each pipe

        Num_edu = np.zeros(len(C))
        for i in range(len(C)):
            Num_edu[i] = C[i][i]


        Pipe_props = self.append_col_to_table(Pipe_props, Num_edu, ['Number of EDUs'], data_type='int')

#        df = pd.DataFrame(data=Num_edu, columns=['Number of EDUs'], dtype='int')
#
#        df.reset_index(drop=True, inplace=True)
#        Pipe_props.reset_index(drop=True, inplace=True)
#
#        Pipe_props = pd.concat([Pipe_props, df], axis=1)
#
        return Pipe_props

    def get_accum_edu(self, C, Pipe_props):
        #C = Connection matrix

        #initialize the vector to all zeros
        Num_edu = Pipe_props.iloc[:,Pipe_props.columns.get_loc('Number of EDUs')].to_numpy(dtype='int')

        Accum_edu = [0 for i in range(len(Num_edu))]

        for i in range(len(Num_edu)):
            Accum_edu[i] = Num_edu[i] # initialize the "Accum_edu vector as the existing "Num_edu" vectors

        for i in range(len(Num_edu)):
            row = C[len(Num_edu)-i-1]  #iterate from the last row of the matrix up to the first
            Accum_edu[len(Num_edu)-i-1] = np.dot(row,Accum_edu)


        Pipe_props = self.append_col_to_table(Pipe_props, Accum_edu, ['Number Accumulated EDUs'], data_type='int')

#        df = pd.DataFrame(data=Accum_edu, columns=['Number Accumulated EDUs'], dtype='int')
#
#        df.reset_index(drop=True, inplace=True)
#        Pipe_props.reset_index(drop=True, inplace=True)
#
#        Pipe_props = pd.concat([Pipe_props, df], axis=1)

        return Pipe_props

        #check to see that every pipe within the connection matrix has been evaluated


    def get_flow_gen(self, Pipe_props, p_flow):

        Op_edu = Pipe_props.iloc[:,Pipe_props.columns.get_loc('Accumulated Operating EDUs')].to_numpy()

        Flow_gen = np.multiply(p_flow,Op_edu)

        df = pd.DataFrame(data=Flow_gen, columns=['Max Flowrate [gpm]'], dtype='float')

        df.reset_index(drop=True, inplace=True)
        Pipe_props.reset_index(drop=True, inplace=True)

        Pipe_props = pd.concat([Pipe_props, df], axis=1)

        return Pipe_props

    def get_accum_flow(self, C, Pipe_props):

        Accum_flow = self.get_accum_edu(C, Flow_gen)
        return Accum_flow

    def get_pipe_dia(self, Pipe_props, l_table, l_class, v_min, v_max, calc_pipe_dia):
        # l_table =  pandas table imported from csv file
        # TODO:  Split this into two methods, one for calc_pipe_dia = True, and one for calc_pipe_dia = False
        Accum_flow = Pipe_props.iloc[:,Pipe_props.columns.get_loc('Max Flowrate [gpm]')].to_numpy()
        # verify that a valid pipe material was specified
        l_classes = l_table['Material'].unique().tolist()
        PSSDataMod().log_progress(str(l_classes))
        #for pClass in PipeClass:
        error = True
        if any( s == l_class for s in list(self.PipeClassName.values())):
            error = False
        if error is True:
             PSSDataMod().log_error("Pipe class specified is not one of the available options: "+str(list(self.PipeClassName.values())))
        Pipe_v = np.zeros(len(Accum_flow))
        if calc_pipe_dia is True:
            Pipe_dia = np.zeros(len(Accum_flow))
        else:
            Pipe_props = PSSDataMod().get_qepanet_pipe_props(Pipe_props, ['diameter'], ['Diameter [in]'])
            Pipe_dia = pd.to_numeric(Pipe_props['Diameter [in]']).to_list()

        # populate the list of nominal diameters
        l_table_sp = l_table.loc[l_table['Material'] == l_class]  # The pipe table that is specific to the selected material

        nom_dia = pd.to_numeric(l_table_sp["Nominal Diameter [in]"]).tolist()
        in_dia = pd.to_numeric(l_table_sp["Actual ID [in]"]).tolist()

        PSSDataMod().log_progress('Pipe Inner Diameter [in]:  '+str(in_dia))
        if calc_pipe_dia is True:
            for p in range(len(Accum_flow)):
                i = 0
                v = self.convert_gpm_to_ft3_per_s(Accum_flow[p]) / self.calc_pipe_area(in_dia[i])
                while v > v_max:
                    i += 1
                    if (i > len(in_dia)-1):
                        PSSDataMod().log_error("ERROR:  Pipe velocity is too large for the available diameters.")
                    v = self.convert_gpm_to_ft3_per_s(Accum_flow[p]) / self.calc_pipe_area(in_dia[i])
                if v < v_min:
                    PSSDataMod().log_warning("No pipe diameter available that is small enough to meet minimum velocity requirement.")
                Pipe_dia[p] = nom_dia[i]
                Pipe_v[p] = v
        else:
            for p in range(len(Accum_flow)):
                d = in_dia[nom_dia.index(Pipe_dia[p])]
                v = self.convert_gpm_to_ft3_per_s(Accum_flow[p]) / self.calc_pipe_area(d)
                Pipe_v[p] = v
        df = pd.DataFrame(data=Pipe_dia, columns=['Diameter [in]'], dtype='float')
        if calc_pipe_dia is True:
            df.reset_index(drop=True, inplace=True)
            Pipe_props.reset_index(drop=True, inplace=True)

            Pipe_props = pd.concat([Pipe_props, df], axis=1)

        df = pd.DataFrame(data=Pipe_v, columns=['Max Velocity [ft/s]'], dtype='float')

        df.reset_index(drop=True, inplace=True)
        Pipe_props.reset_index(drop=True, inplace=True)

        Pipe_props = pd.concat([Pipe_props, df], axis=1)

        return Pipe_props

    def convert_gpm_to_ft3_per_s(self, gpm):
        ftc = gpm*0.002228009

        return ftc

    def convert_ft3_per_s_to_gpm(self, ftc):
        gpm = ftc*448.8312211

        return gpm

    def calc_pipe_area(self, d):
        area = np.pi*d*d/144.0/4
        return area


    def ft_per_s_to_gpm(self, v, d):
        #v = pipe velocity in ft/s
        #d = actual pipe S in inches

        A = np.pi*d*d/4.0/144.0 #Pipe area [ft2]
        flow = v*A  #flowrate in [ft3/s]
        gpm = self.convert_ft3_per_s_to_gpm(flow)

        return gpm


    def get_op_edu_epa(self, Pipe_props, A, B, p_flow):

        Accum_edu = Pipe_props.iloc[:,Pipe_props.columns.get_loc('Number Accumulated EDUs')].to_numpy()

        Op_edu = []

        for i in range(len(Accum_edu)):
            if Accum_edu[i] == 1:
                Op_edu.append(1)
            else:
                Op_edu.append(np.ceil((A*Accum_edu[i]+20) / p_flow))

        df = pd.DataFrame(data=Op_edu, columns=['Accumulated Operating EDUs'], dtype='int')

        df.reset_index(drop=True, inplace=True)
        Pipe_props.reset_index(drop=True, inplace=True)

        Pipe_props = pd.concat([Pipe_props, df], axis=1)

        return Pipe_props

    def get_op_edu_gpd(self):
        pass

    def get_op_edu_table(self, Pipe_props, table):
        #Determines the number of operating EDUs fro the total EDUs based on the table published by E-One

        table = table.set_index('total_edus')

        PSSDataMod().log_progress('Op EDU Table:\n')
        PSSDataMod().log_progress(str(table))

        Op_edus = [0 for i in range(len(Pipe_props.index))]

        Accum_edus = Pipe_props.iloc[:,Pipe_props.columns.get_loc('Number Accumulated EDUs')].to_numpy(int)

        #Pipe_props['Number Operating EDUs'] = Pipe_props['Number Accumulated EDUs'].map(Accum_edus)
        check_large_edus = False
        if max(Accum_edus) > 1004:
            PSSDataMod().log_warning("For pipes with more than 1004 accumulated EDUs, operating EDUs are extrapolated from table values")
            check_large_edus = True

        #PSSDataMod().log_progress("Total EDUs: "+str(max(Accum_edus)))

        if check_large_edus is True:        #if total edus is larger than the maximum table value, extraploate the large data
            #fit the table data to a polynomial, popt
            PSSDataMod().log_warning("While reading the number of operating EDUs, \
                                            extrapolating table values for large number of \
                                            accumulated EDUs")
            def func(x, a, b, c):
                return a*x**2 + b*x + c
            popt, pcov = curve_fit(func, table['total_edus'].to_numpy(), table['op_edus'].to_numpy() )
            #op_edu_func = interp.interp1d(table['total_edus'].to_numpy(), table['op_edus'].to_numpy(), fill_value="extrapolate")
            for i in range(len(Accum_edus)):
                if Accum_edus[i] > 1004:
                    #Op_edus[i] = op_edu_func(Accum_edus[i])
                    Op_edus[i] = np.ceil(np.polyval(popt, Accum_edus[i])) #evaluate the polynomial for the num_accum_edus
                else:
                    Op_edus[i] = table.loc[table['total_edus'] == Accum_edus[i], 'op_edus'].to_numpy(int)[0]
        else:
            for i in range(len(Accum_edus)):
                #Op_edus[i] = table.loc[table['total_edus'] == Accum_edus[i], 'op_edus'].to_numpy(int)[0]
                Op_edus[i] = table.at[Accum_edus[i], 'op_edus']

        PSSDataMod().log_progress("Op_edus:\n"+str(Op_edus))

        Pipe_props = self.append_col_to_table(Pipe_props, Op_edus, ['Accumulated Operating EDUs'])

        return Pipe_props


    def calc_pipe_loss_hazwil(self, Pipe_props, l_dia_table, l_material, l_class, l_C_table):
        #extract pipe velocity from "Pipe_props" in [ft/s]
        v = Pipe_props['Max Velocity [ft/s]']
        #v = v.transpose()
        v = v.to_numpy(dtype='float')
        #v = np.vstack(v[0])
        #extract actual ID in [in]
        dia_nom = Pipe_props[['Diameter [in]']]
        #PSSDataMod().log_progress(str(dia_nom))
        dia = l_dia_table[l_dia_table['Material'] == l_class]

        PSSDataMod().log_progress(str(dia_nom))

        PSSDataMod().log_progress(str(dia))

        dia_nom = dia_nom.merge(dia, how='left', left_on='Diameter [in]', right_on='Nominal Diameter [in]')
        #dia_nom = pd.concat([dia_nom, dia])
        dia = dia_nom['Actual ID [in]']
        #dia = pd.to_numeric(dia)
        #dia = dia.transpose()
        dia = dia.to_numpy(dtype='float')
        #dia = np.vstack(dia[0])

        #calculate flowrate in [gpm]
        Q = self.ft_per_s_to_gpm(v,dia)
        #extract pipe length in [ft]
        L = Pipe_props['Length [ft]']
        #L = L.transpose()
        L = L.to_numpy(dtype='float')
        #PSSDataMod().log_progress(str(L))
        #L = L[0]

        PSSDataMod().log_progress('Pipe material:'+str(self.PipeMaterialName[l_material]))

        #get C value
        C = l_C_table.loc[self.PipeMaterialName[l_material],'C Factor']

        PSSDataMod().log_progress('C factor:  '+str(C))

        #PSSDataMod().log_progress('Velocity: '+str(v))
        #PSSDataMod().log_progress('Flow: '+str(Q))
        #PSSDataMod().log_progress(str(Q[0][0]))
        #PSSDataMod().log_progress('Diameter: '+str(dia))
        #PSSDataMod().log_progress('Length: '+str(L))

        hl_f = [0.0 for i in range(len(Q))]
        #PSSDataMod().log_progress(str(hl_f))
        hl = [0.0 for i in range(len(Q))]

        #Calculate total headloss in [ft]
        #for i in range(len(hl_f)):
        #    hl_f[i] = (0.2083*((100.0/C)**1.85)*(Q[i]**1.85))/(dia[i]**4.8655)
            #PSSDataMod().log_progress(str(hl_f))
            #Calculate headloss per 100 ft
        #    hl[i] = hl_f[i]*L[i]/100.0

        hl_f = (0.2083*((100.0/C)**1.85)*(Q**1.85))/(dia**4.8655)

        hl = hl_f*L/100

        #append to pandas dataframe
        df = pd.DataFrame(data=hl_f, columns=['Friction Loss Factor [ft/100ft]'])

        df.reset_index(drop=True, inplace=True)
        Pipe_props.reset_index(drop=True, inplace=True)

        Pipe_props = pd.concat([Pipe_props, df], axis=1)

        df = pd.DataFrame(data=hl, columns=['Friction Loss [ft]'], dtype='float')

        df.reset_index(drop=True, inplace=True)
        Pipe_props.reset_index(drop=True, inplace=True)

        Pipe_props = pd.concat([Pipe_props, df], axis=1)

        return [Pipe_props, C]

    def get_accum_loss(self, Pipe_props, Node_props, Pipe_nodes, res, sort_lst, node_sort_lst=False):

        datamod = PSSDataMod()

        Pipe_id = Pipe_props['Pipe ID'].to_numpy()
        Pipe_props = datamod.sort_dataframe(Pipe_props, sort_lst)

        Conn = Pipe_props['Downstream Connected Pipe'].to_numpy()
        Loss = Pipe_props['Friction Loss [ft]'].to_numpy()

        Accum_loss = [0.0 for i in range(len(Pipe_id))]
        Node_pressures = np.zeros(len(Pipe_props.index))
        Node_ID = np.zeros(len(Pipe_props.index))
        Node_ID[0] = res[0]

        Node_update = np.zeros(len(Pipe_props.index))
        #PSSDataMod().log_progress("Pipe ID: ", Pipe_id)

        for i in range(len(Pipe_id)):
            #get info on connected pipe:
            loss = 0
            for j in range(len(Conn)):
                if Pipe_id[j][0] == Conn[i][0]:
                    loss = Accum_loss[j]
                    break
            Accum_loss[i] = Loss[i]+loss
            #populate node pressure data
            upstream_node = datamod.get_upstream_node(Pipe_id[i], Pipe_nodes, Node_props, res, sort_lst, node_sort_lst)
            downstream_node = datamod.get_downstream_node(Pipe_id[i], Pipe_nodes, upstream_node)
            Node_pressures[i] = [upstream_node, Accum_loss[i]]

        Pipe_props = self.append_col_to_table(Pipe_props, Accum_loss, ['Accumulated Friction Loss [ft]'])

        #sort node list TODO
        PSSDataMod().log_progress("Node_pressures: ", Node_pressures)

        Node_props = self.append_col_to_table(Node_props, Node_pressures[:][1], ['Pressure [ft]'])

        return [Pipe_props, Node_props]

    def get_end_pipes(self, In):
        """ {Function}
                Finds pipes connected to only one pipe based on the incidence matrix.
            {Variables}
                In:
                    (2D Numpy array) Incidence matrix.  Rows are an ordered list
                    of all nodes.  Columns are an ordered list of all edges.
                    Matrix entry In_{ij} is 1 if the ith node is connected to the
                    jth edge, and zero otherwise.
                node_srt_lst:
                    (Numpy array of ints)   "Sort list" array which maps the location
                    of the junction in the Node_props dataframe to the location
                    of the junction in the sorted Node_props_sort dataframe.
                    Generated in the create_conn_matrix() function.
                    Integer value is the index location in the sorted dataframe.
                    Index correspnds to the index in the unsorted "Pipe_props" dataframe.
            {Outputs}
                End_pipes:
                    (1D Numpy array) List of end pipes sorted according to "Pipe_props".
                    "1" designates an end .  "0" designates a pipe connected to two other pipes.
        """
        pass


    def get_accum_loss_ind(self, Pipe_props, Node_props, In, sort_lst, node_srt_lst, res_elev, p_calc, station_depth): #Same as "get_accum_loss" modified to calculate losses based on graph theory with an incidence matrix.  Added calculation of Static head.
        """ {Function}
                Calculates the pressure in each node of the system and evaluates
                the maximum accumulated loss to include in the results table output.
            {Variables}
                Pipe_nodes:
                    (Pandas Dataframe) unsorted list of Pipes and connected junctions
                    based on ordering of QGIS features.
                Pipe_props:
                    (Pandas Dataframe) unsorted list of Pipe attributes based on
                    ordering of QGIS features.
                Node_props:
                    (Pandas Dataframe) unsorted list of node attributes based on
                    ordering of QGIS features.
                In:
                    (2D Numpy array) Incidence matrix.  Rows are an ordered list
                    of all nodes.  Columns are an ordered list of all edges.
                    Matrix entry In_{ij} is 1 if the ith node is connected to the
                    jth edge, and zero otherwise.
                sort_lst:
                    (Numpy array of ints)  "Sort list" array which maps the location
                    of the pipe in the Pipe_props dataframe to the location of the
                    pipe in the sorted Pipes_array dataframe.  generated in the
                    create_conn_matrix() function.
                    Integer value is the index location in the sorted dataframe.
                    Index correspnds to the index in the unsorted "Pipe_props" dataframe.
                node_srt_lst:
                    (Numpy array of ints)   "Sort list" array which maps the location
                    of the junction in the Node_props dataframe to the location
                    of the junction in the sorted Node_props_sort dataframe.
                    Generated in the create_conn_matrix() function.
                    Integer value is the index location in the sorted dataframe.
                    Index correspnds to the index in the unsorted "Pipe_props" dataframe.
            {Outputs}
                C:
                    (2D Numpy array) Pipe connection matrix.  A square symmetric matrix that defines how pipes are connected within the network.  Each row indicates the current pipe, and each column represents potentially connected pipes.  a value of 1 indicates the pipes are connected.  A value of 0 indicates no connection.  All digonal entries are 0.  Sorted from the reservoir upstream (breadth-first search).
                C_n:
                    (2D Numpy array)  Node connection matrix (adjacency matrix) A square matrix with dimension equal to the number of nodes.  Rows indicate the current node.  Columns indicate the nodes with edges connecting the current node.  Sorted from the reservoir upstream (breadth-first search).  For directed tree graphs, this matrix is strictly upper triangular.
        """

        datamod = PSSDataMod()
        print(In)
        #get the headloss per pipe, sorted according to the incidence matrix
        F = datamod.sort_dataframe(Pipe_props, sort_lst)['Friction Loss [ft]'].to_numpy()
        F = np.reshape(F, (len(F), -1))
        #get the node elevation sorted according to the incidence matrix
        #PSSDataMod().log_progress("Node_props: ", Node_props)
        #PSSDataMod().log_progress("Pipe_props: ", Pipe_props)
        Elevation = datamod.sort_dataframe(Node_props, node_srt_lst)['Elevation [ft]'].to_numpy()

        #PSSDataMod().log_progress("Elevation: ", Elevation)
        #PSSDataMod().log_progress("node_sort:", node_srt_lst)
        #PSSDataMod().log_progress("Node Sort List: ", node_srt_lst)
        #PSSDataMod().log_progress("Elevation: ", Node_props["Elevation [ft]"].to_numpy().shape)
        #PSSDataMod().log_progress("Elevation: ", Elevation.shape)
        Elevation = np.reshape(Elevation, (len(Elevation), -1))

        #PSSDataMod().log_progress("Elevation: ", Elevation)
        #PSSDataMod().log_progress("Node props: \n", Node_props)

        P = np.zeros((len(In)-1,1), dtype='float')  #node pressure.  assumes 1 reservior
        #Node pressure sorted according to the incidence matrix
        #for l in range(len(In.T)): #cylce thru the columns of the incidence matrix (pipes)
        #    for j in range(len(In)):
        #        if In[j][l] == 1:


        #In_strictu = np.insert( np.identity(len(In)-1), 0, [0 for i in range(len(In)-1)], axis=0 )
        In_U = np.delete(In, 0, axis=0)
        In_strictU = In_U - np.identity(len(In_U))    #Incidence sub-matrix without first row or diagonal. This matrix is strictly upper triangular.

        #PSSDataMod().log_progress("Elevation: ", type(Elevation))
        #PSSDataMod().log_progress("res_elev: ", type(res_elev))

        #- List of added station depts for end nodes (Assumes all end nodes hvae 1 EDU)
        Station_depth = Pipe_props['Number of EDUs'].to_numpy()*station_depth

        dm.log_progress("Station_depth: "+str(Station_depth))

        #S = -(Elevation - (res_elev+station_depth)) # Static head.  -1* the elevation relative to the outlet
        S = -(Elevation - Station_depth - res_elev) # Static head.  -1* the elevation relative to the outlet
        #PSSDataMod().log_progress("Headloss: ", Headloss)
        #PSSDataMod().log_progress("Static head: ", Static_head)
        #PSSDataMod().log_progress("Pressure: ", Pressure_old)
        #PSSDataMod().log_progress("Headloss: ", Headloss.shape)
        #PSSDataMod().log_progress("Static_head: ", S)
        #PSSDataMod().log_progress("Starting iterative solution of node pressures...")

        # solve the equation for pressure:
        #   In_strictU.T*P.T = P - F - S
        #           F = friction loss
        #           S = Static Head


        #(Option 1)fixed point iteration (convergence is not guaranteed)
        if p_calc == 'fixed-point':
            PSSDataMod().log_progress("\tSolving pressure using fixed-point iterations....")
            #calculate pressures iteratively:
            max_it = 50
            err_limit = 1e-4
            it = 0
            err = 1e5
            P_old = np.zeros((len(In)-1,1), dtype='float') #convert to numpy array

            while err > err_limit:
                if it > max_it-1:
                    warnings.warn("Node pressure iterative solver did not converge")
                    PSSDataMod().log_progress("\tWarning!: Node pressure iterative solver did not converge")
                    break
                #PSSDataMod().log_progress(Headloss + Static_head)
                P = np.dot(P_old.T,In_strictU).T + F

                err = np.abs(np.sum(P - P_old))

                P_old = P
                it+=1

                PSSDataMod().log_progress("\titeration "+ str(it)+" residual error: {:.6f}".format(err))
                #PSSDataMod().log_progress("Pressure:\n", P)

        #(Option 2) Broyden's method (quasi-Newton) #INCOMPLETE
        if p_calc == 'broyden':
            PSSDataMod().log_progress("\tSolving pressure using Broyden's method...")

            P = self.broyden_good()

        #(Option 3) calculate using built-in scipy method
        if p_calc == 'broyden-sp':
            import decimal
            #Data conversions to prevent overflow
            decimal.getcontext().prec = 100
            for i in range(len(In_strictU)):
                for j in range(len(In_strictU[i])):
                    In_strictU[i][j] = decimal.Decimal(In_strictU[i][j])
            for i in range(len(F)):
                for j in range(len(F[i])):
                    F[i][j] = decimal.Decimal(F[i][j])

            PSSDataMod().log_progress("\tSolving pressure using scipy's built-in Broyden method solver...")
#            def f(P):
#                for i in range(len(P)):
#                    for j in range(len(P[i])):
#                        P[i][j] = decimal.Decimal(P[i][j])
#
#                f_ = (In_strictU.T@P - P + F)
#                for i in range(len(f_)):
#                    for j in range(len(f_[i])):
#                        f_[i][j] = decimal.Decimal(f_[i][j])
#                return f_
            def f(P_):
                return (In_strictU.T@P_ - P_ + F)
            P = optimize.broyden1(f, P)

        #(Option 4) solve the system using forward subsitution
        if p_calc == 'forward-sub':
            PSSDataMod().log_progress("\tSolving pressure using forward substitution...")
            #set the reservoir pressure to equal the elevation:
            P[0][0] = res_elev

            #PSSDataMod().log_progress("Pressure: ",Pressure.shape)
            #PSSDataMod().log_progress("Frictionloss: ",Frictionloss.shape)
            #PSSDataMod().log_progress("Incidence Matrix: ", In_strictU.T[0].shape)

            for n in range(len(In_strictU)):
                row = np.reshape(In_strictU.T[n], (-1, len(In_strictU[:][n])))

                lhs = row@P #matrix multiplication
                #PSSDataMod().log_progress("P: ", P.shape)
                #PSSDataMod().log_progress("lhs: ", lhs)
                P[n][0] = lhs[0] + F[n][0]
                #PSSDataMod().log_progress("Pressure: ", P)
        #PSSDataMod().log_progress("Headloss: ", Headloss.shape)
        #PSSDataMod().log_progress("Static_head: ", Static_head.shape)

        Accum_loss = np.amax(P.T*In_U, axis=1).reshape((len(P),1))

        P = P + S

        #Pressure = np.insert(Pressure, 0, 0)    #Add reservior info back into the arrays
        #Accum_loss = np.insert(Accum_loss, 0, 0)

        #PSSDataMod().log_progress("Pressure: \n", Pressure)
        #PSSDataMod().log_progress("Accum Loss: \n", Accum_loss)

        sort_lst_inv = datamod.get_inv_sort_lst(sort_lst)
        node_srt_lst_inv = datamod.get_inv_sort_lst(node_srt_lst)

        #PSSDataMod().log_progress("Pipe sort list:\n", sort_lst)
        #PSSDataMod().log_progress("Inverted Pipe sort list:\n", sort_lst_inv)
        #PSSDataMod().log_progress("Node sort list:\n", node_srt_lst)
        #PSSDataMod().log_progress("Inverted node sort list:\n", node_srt_lst_inv)

        dm.log_progress("/n"+str(Pipe_props))

        Pipe_props = dm.append_col_to_table(Pipe_props, Accum_loss, 'Accumulated Friction Loss [ft]', sort=sort_lst_inv)

        dm.log_progress("\n"+str(Node_props))

        Node_props = dm.append_col_to_table(Node_props, P, 'Pressure [ft]', data_type='float', sort=node_srt_lst_inv)

        #PSSDataMod().log_progress("Pipe Props: \n", Pipe_props)
        #PSSDataMod().log_progress("Node Props: \n", Node_props)

        max_elev = np.maximum(max(Elevation), res_elev)

        return [Pipe_props, Node_props, max_elev, res_elev]

    def get_accum_loss_ind2(self, Pipe_props, Node_props, In, sort_lst, node_srt_lst, res_elev, p_calc, station_depth): #Same as "get_accum_loss" modified to calculate losses based on graph theory with an incidence matrix.  Added calculation of Static head.
        """ {Function}
                2nd formulation for calculation of pressure in each node of the system and evaluation
                the maximum accumulated loss to include in the results table output.
            {Variables}
                Pipe_nodes:
                    (Pandas Dataframe) unsorted list of Pipes and connected junctions
                    based on ordering of QGIS features.
                Pipe_props:
                    (Pandas Dataframe) unsorted list of Pipe attributes based on
                    ordering of QGIS features.
                Node_props:
                    (Pandas Dataframe) unsorted list of node attributes based on
                    ordering of QGIS features.
                In:
                    (2D Numpy array) Incidence matrix.  Rows are an ordered list
                    of all nodes.  Columns are an ordered list of all edges.
                    Matrix entry In_{ij} is 1 if the ith node is connected to the
                    jth edge, and zero otherwise.
                sort_lst:
                    (Numpy array of ints)  "Sort list" array which maps the location
                    of the pipe in the Pipe_props dataframe to the location of the
                    pipe in the sorted Pipes_array dataframe.  generated in the
                    create_conn_matrix() function.
                    Integer value is the index location in the sorted dataframe.
                    Index correspnds to the index in the unsorted "Pipe_props" dataframe.
                node_srt_lst:
                    (Numpy array of ints)   "Sort list" array which maps the location
                    of the junction in the Node_props dataframe to the location
                    of the junction in the sorted Node_props_sort dataframe.
                    Generated in the create_conn_matrix() function.
                    Integer value is the index location in the sorted dataframe.
                    Index corresponds to the index in the unsorted "Node_props" dataframe.
            {Outputs}
                C:
                    (2D Numpy array) Pipe connection matrix.  A square symmetric matrix that defines how pipes are connected within the network.  Each row indicates the current pipe, and each column represents potentially connected pipes.  a value of 1 indicates the pipes are connected.  A value of 0 indicates no connection.  All digonal entries are 0.  Sorted from the reservoir upstream (breadth-first search).
                C_n:
                    (2D Numpy array)  Node connection matrix (adjacency matrix) A square matrix with dimension equal to the number of nodes.  Rows indicate the current node.  Columns indicate the nodes with edges connecting the current node.  Sorted from the reservoir upstream (breadth-first search).  For directed tree graphs, this matrix is strictly upper triangular.
        """
        datamod = PSSDataMod()
        #dm.log_progress(Str(In))
        #get the headloss per pipe, sorted according to the incidence matrix
        F = datamod.sort_dataframe(Pipe_props, sort_lst)['Friction Loss [ft]'].to_numpy()
        F = np.reshape(F, (len(F), -1))
        #get the node elevation sorted according to the incidence matrix
        #PSSDataMod().log_progress("Node_props: ", Node_props)
        #PSSDataMod().log_progress("Pipe_props: ", Pipe_props)
        Elevation = datamod.sort_dataframe(Node_props, node_srt_lst)['Elevation [ft]'].to_numpy()

        #PSSDataMod().log_progress("Elevation: ", Elevation)
        #PSSDataMod().log_progress("node_sort:", node_srt_lst)
        #PSSDataMod().log_progress("Node Sort List: ", node_srt_lst)
        #PSSDataMod().log_progress("Elevation: ", Node_props["Elevation [ft]"].to_numpy().shape)
        #PSSDataMod().log_progress("Elevation: ", Elevation.shape)
        Elevation = np.reshape(Elevation, (len(Elevation), -1))

        #PSSDataMod().log_progress("Elevation: ", Elevation)
        #PSSDataMod().log_progress("Node props: \n", Node_props)

        P = np.zeros((len(In)-1,1), dtype='float')  #node pressure.  assumes 1 reservior
        #Node pressure sorted according to the incidence matrix
        #for l in range(len(In.T)): #cylce thru the columns of the incidence matrix (pipes)
        #    for j in range(len(In)):
        #        if In[j][l] == 1:


        #In_strictu = np.insert( np.identity(len(In)-1), 0, [0 for i in range(len(In)-1)], axis=0 )
        In_U = np.delete(In, 0, axis=0)
        In_strictU = In_U - np.identity(len(In_U))    #Incidence sub-matrix without first row or diagonal. This matrix is strictly upper triangular.

        #PSSDataMod().log_progress("Elevation: ", type(Elevation))
        #PSSDataMod().log_progress("res_elev: ", type(res_elev))

        dm.log_progress(str(In_U))

        End_nodes = np.array([ 0 if (np.sum(row) > 1) else 1 for row in In_U])
        Station_depth = End_nodes*station_depth

        dm.log_progress("Station_depth: "+str(Station_depth))

        #S = -(Elevation - (res_elev+station_depth)) # Static head.  -1* the elevation relative to the outlet
        Elevation= Elevation.reshape((-1,1))
        Station_depth = Station_depth.reshape((-1,1))
        S = -(Elevation - Station_depth)
        S = S + res_elev # Static head.  -1* the elevation relative to the outlet

        dm.log_progress("Static Head:\n"+str(S))

        #PSSDataMod().log_progress("Headloss: ", Headloss)
        #PSSDataMod().log_progress("Static head: ", Static_head)
        #PSSDataMod().log_progress("Pressure: ", Pressure_old)
        #PSSDataMod().log_progress("Headloss: ", Headloss.shape)
        #PSSDataMod().log_progress("Static_head: ", S)
        #PSSDataMod().log_progress("Starting iterative solution of node pressures...")

        # solve the equation for pressure:
        #   In_strictU.T*P.T = P - F - S
        #           F = friction loss
        #           S = Static Head


        #(Option 4) solve the system using forward subsitution
        if p_calc == 'forward-sub':
            PSSDataMod().log_progress("\tSolving pressure using forward substitution...")
            #set the reservoir pressure to equal the elevation:
            P[0][0] = res_elev

            #PSSDataMod().log_progress("Pressure: ",Pressure.shape)
            #PSSDataMod().log_progress("Frictionloss: ",Frictionloss.shape)
            #PSSDataMod().log_progress("Incidence Matrix: ", In_strictU.T[0].shape)

            for n in range(len(In_strictU)):
                row = np.reshape(In_strictU.T[n], (-1, len(In_strictU[:][n])))

                lhs = row@P #matrix multiplication
                #PSSDataMod().log_progress("P: ", P.shape)
                #PSSDataMod().log_progress("lhs: ", lhs)
                P[n] = lhs[0] + F[n][0]
                #PSSDataMod().log_progress("Pressure: ", P)
        #PSSDataMod().log_progress("Headloss: ", Headloss.shape)
        #PSSDataMod().log_progress("Static_head: ", Static_head.shape)
        else:
            datamod.log_error("Only 'forward-sub' option is implemented for pressure calculation")

        P = P.flatten()
        S = S.flatten()

        dm.log_progress("Presssure:\n"+str(P))

        Accum_loss = np.amax(P.T*In_U, axis=1).reshape((len(P),1))

        P = P + S

        #Pressure = np.insert(Pressure, 0, 0)    #Add reservior info back into the arrays
        #Accum_loss = np.insert(Accum_loss, 0, 0)

        #PSSDataMod().log_progress("Pressure: \n", Pressure)
        #PSSDataMod().log_progress("Accum Loss: \n", Accum_loss)

        sort_lst_inv = datamod.get_inv_sort_lst(sort_lst)
        node_srt_lst_inv = datamod.get_inv_sort_lst(node_srt_lst)

        #PSSDataMod().log_progress("Pipe sort list:\n", sort_lst)
        #PSSDataMod().log_progress("Inverted Pipe sort list:\n", sort_lst_inv)
        #PSSDataMod().log_progress("Node sort list:\n", node_srt_lst)
        #PSSDataMod().log_progress("Inverted node sort list:\n", node_srt_lst_inv)

        dm.log_progress("\n"+str(Pipe_props))

        Pipe_props = dm.append_col_to_table(Pipe_props, Accum_loss, 'Accumulated Friction Loss [ft]', sort=sort_lst_inv)

        dm.log_progress("\n"+str(Node_props))

        Node_props = dm.append_col_to_table(Node_props, P, 'Pressure [ft]', data_type='float', sort=node_srt_lst_inv)
        Node_props = dm.append_col_to_table(Node_props, S, 'Static Head [ft]', data_type='float', sort=node_srt_lst_inv)

        #PSSDataMod().log_progress("Pipe Props: \n", Pipe_props)
        #PSSDataMod().log_progress("Node Props: \n", Node_props)

        max_elev = np.maximum(max(Elevation), res_elev)

        return [Pipe_props, Node_props, max_elev, res_elev]


    def append_col_to_table(self, Pipe_props, col, title, data_type=False, sort=False):
        if data_type:
            df = pd.DataFrame(data=col, columns=title, dtype=data_type)
        else:
            df = pd.DataFrame(data=col, columns=title)

        if sort:
            df = df.reindex(index=sort)  #rearrange the pipes within the pandas dataframe to be sorted from the Reservoir upstream


        df.reset_index(drop=True, inplace=True)
        Pipe_props.reset_index(drop=True, inplace=True)

        Pipe_props = pd.concat([Pipe_props, df], axis=1)

        return Pipe_props

    def get_TDH(self, Pipe_props):

        Accumulated_loss = Pipe_props["Accumulated Friction Loss [ft]"].to_numpy()
        Static_head = Pipe_props["Static Head [ft]"].to_numpy()

        TDH = Accumulated_loss + Static_head

        #for i in range(len(Pipe_props.index)):
        #    pipe_TDH = Pipe_props.iloc[i]['Accumulated Friction Loss [ft]'] + Pipe_props.iloc[i]['Static Head [ft]']
        #    TDH.append(pipe_TDH)

        #PSSDataMod().log_progress("Pipe props:\n", Pipe_props)

        #PSSDataMod().log_progress("TDH:\n", TDH)

        Pipe_props = self.append_col_to_table(Pipe_props, TDH, ['Total Dynamic Head [ft]'], data_type='float')

        return Pipe_props

    def get_TDH2(self, Pipe_props, Node_props, sort_lst, node_srt_lst):
        """{Function}
                Retreives the pipe TDH (at downstream node) from the pressure values stored in the
                "Nodes_props" dataframe
            {Variables}
                Pipe_nodes:
                    (Pandas Dataframe) unsorted list of Pipes and connected junctions
                    based on ordering of QGIS features.
                Pipe_props:
                    (Pandas Dataframe) unsorted list of Pipe attributes based on
                    ordering of QGIS features.
                Node_props:
                    (Pandas Dataframe) unsorted list of node attributes based on
                    ordering of QGIS features.
                In:
                    (2D Numpy array) Incidence matrix.  Rows are an ordered list
                    of all nodes.  Columns are an ordered list of all edges.
                    Matrix entry In_{ij} is 1 if the ith node is connected to the
                    jth edge, and zero otherwise.
                sort_lst:
                    (Numpy array of ints)  "Sort list" array which maps the location
                    of the pipe in the Pipe_props dataframe to the location of the
                    pipe in the sorted Pipes_array dataframe.  generated in the
                    create_conn_matrix() function.
                    Integer value is the index location in the sorted dataframe.
                    Index correspnds to the index in the unsorted "Pipe_props" dataframe.
                node_srt_lst:
                    (Numpy array of ints)   "Sort list" array which maps the location
                    of the junction in the Node_props dataframe to the location
                    of the junction in the sorted Node_props_sort dataframe.
                    Generated in the create_conn_matrix() function.
                    Integer value is the index location in the sorted dataframe.
                    Index corresponds to the index in the unsorted "Node_props" dataframe.
        """

        TDH = dm.sort_dataframe(Node_props, node_srt_lst)['Pressure [ft]'].to_numpy()

        Pipe_props = dm.append_col_to_table(Pipe_props, TDH, 'Total Dynamic Head [ft]', data_type='float', sort=dm.get_inv_sort_lst(sort_lst))

        return Pipe_props

    def get_node_pressure(self, Pipe_nodes, Pipe_props, Node_props, res, pipe_srt_lst=False, node_srt_lst=False):  #INCOMPLETE
        """ {Function}
                Calculate the pressure at each node from pipe data.
            {Variables}
                Pipe_props:
                    (Pandas dataframe) Includes pipe info for the pipe network
                Node_props:
                    (Pandas dataframe) Includes junction info for the pipe network
                pipe_srt_lst:
                    (Numpy array of ints)  "Sort list" array which maps the location of the pipe in the Pipe_props dataframe to the location of the pipe in the sorted Pipes_array dataframe.  generated in the create_conn_matrix() function.
                    Integer value is the index location in the sorted dataframe.
                    Index correspnds to the index in the unsorted "Pipe_props" dataframe.
            {Outputs}
                Node_props:
                    (Pandas dataframe) Updated to include pressures from Ppe_props
        """

        datamod = PSSDataMod()

        Pipe_nodes_sort = datamod.sort_dataframe(Pipe_nodes, pipe_srt_lst)

        #set the reservior pressure equal to zero
        pressure = [0 for i in range(len(Pipe_nodes))]

        Pipe_props_sort = datamod.sort_dataframe(Pipe_nodes, pipe_srt_lst)

        headloss = Pipe_props_sort['Headloss [ft]'].to_numpy()

        count = 0

        for pipe in Pipe_nodes_sort:
            upstream_node = datamod.get_upstream_node(pipe[0], Pipe_nodes_sort, Node_props, res, False, node_srt_lst)
            downstream_node = datamod.get_downstream_node(pipe[0], Pipe_nodes_sort)

            pressure[Node_props.iloc[Node_props['Node ID']==upstream_node]] = pressure[Node_props.iloc[Node_props['Node ID']==downstream_node]] + headloss[count]

            count += 1

        if (count != len(Pipe_nodes) - 1):
            raise Exception('ERROR:  Pressures were not updated for all nodes.')

    def populate_edus_from_qepa(self, C, Pipe_props, sort_lst):

        dataMod = PSSDataMod()

        #get "num_edu" field from qepanet
        Pipe_props = dataMod.get_qepanet_edu_data(Pipe_props, sort_lst)

        #modify qepanet field based on connection matrix to zero out EDUs for pipes that are not end nodes

        #get num_edu array
        num_edu = Pipe_props['Number of EDUs'].to_numpy(dtype='int')

        #get connection matrix array
        C_edu = [0 for i in range(len(C))]

        for i in range(len(C)):
            C_edu[i] = C[i][i]

        #replace the "Number of EDUs" column data
        Pipe_props['Number of EDUs'] = Pipe_props['Number of EDUs'].replace(np.multiply(C_edu,num_edu))

        return Pipe_props

    def get_calc_stats(self, Pipe_props, max_elev):

        Vel = Pipe_props['Max Velocity [ft/s]'].tolist()

        min_v = min(Vel)
        max_v = max(Vel)

        TDH = Pipe_props['Total Dynamic Head [ft]'].tolist()
        max_tdh = max(TDH)

        Dia = Pipe_props["Diameter [in]"].tolist()
        max_d = max(Dia)

        Num_edu = Pipe_props["Number Accumulated EDUs"].tolist()
        num_edu = max(Num_edu)

        Max_pres = Pipe_props["Total Dynamic Head [ft]"]
        max_pres = max(Max_pres)

        #Get a list of pipe sizes used in the system
        Dia_list = []

        for d in Dia:
            if d not in Dia_list:
                Dia_list.append(d)

        #Parse through each diameter and sum the lengths
        pipe_sum = [0 for i in range(len(Dia_list))]
        length = Pipe_props['Length [ft]'].to_numpy(dtype=float)
        for j in range(len(pipe_sum)):
            for i, p in enumerate(length):
                if Dia[i] == Dia_list[j]:
                    pipe_sum[j] += p


        stats = {'Min Velocity [ft/s]': [min_v], 'Max Velocity [ft/s]': [max_v], 'Max Total Dynamic Head [ft]': [max_tdh], 'Max Diameter [in]': [max_d], 'Total Number EDUs': [num_edu], 'Max Elevation [ft]': max_elev, 'Max Pressure [ft]': max_pres}

        pipe_len_summary = {'Pipe Diameter [in]': Dia_list, 'Total Length [ft]': pipe_sum}

        index = [0]
        Calc_stats = pd.DataFrame(stats, index=index)

        #PSSDataMod().log_progress("Dia List: ", Dia_list)
        #PSSDataMod().log_progress("pipe_sum: ", pipe_sum)

        Pipe_len = pd.DataFrame(pipe_len_summary)

        return Calc_stats, Pipe_len

    def calc_velocity(self, Pipe_props, l_table, l_material):
        # l_table =  pandas table imported from csv file

        Accum_flow = Pipe_props.iloc[:,Pipe_props.columns.get_loc('Max Flowrate [gpm]')].to_numpy()
        # verify that a valid pipe material was specified
        materials = l_table['Material'].unique().tolist()
        #PSSDataMod().log_progress(str(materials))
        error = True
        for i in range(len(materials)):
            if l_material == materials[i]:
                error = False
        if error:
            raise Exception("ERROR:  Pipe material specified is not one of the available options: "+str(materials))

        Pipe_dia = Pipe_props.iloc[:,Pipe_props.columns.get_loc('Diameter [in]')].to_numpy(float)
        Pipe_v = np.zeros(len(Accum_flow))

        # populate the list of nominal diameters
        l_table_sp = l_table.loc[l_table['Material'] == l_material]  # The pipe table that is specific to the selected material

        nom_dia = pd.to_numeric(l_table_sp["Nominal Diameter [in]"]).tolist()
        in_dia = pd.to_numeric(l_table_sp["Actual ID [in]"]).tolist()

        for i in range(len(Pipe_v)):
            Pipe_v[i] = self.convert_gpm_to_ft3_per_s(Accum_flow[i]) / self.calc_pipe_area(in_dia[nom_dia.index(Pipe_dia[i])])

        df = pd.DataFrame(data=Pipe_v, columns=['Max Velocity [ft/s]'], dtype='float')

        df.reset_index(drop=True, inplace=True)
        Pipe_props.reset_index(drop=True, inplace=True)

        Pipe_props = pd.concat([Pipe_props, df], axis=1)

        return Pipe_props

    def set_op_edu_all_pumps(self, Pipe_props):

        op_edu = Pipe_props['Number Accumulated EDUs'].to_numpy()

        Pipe_props = self.append_col_to_table(Pipe_props, op_edu, ['Accumulated Operating EDUs'], data_type='int')

        #PSSDataMod().log_progress("Accum Op EDUs: ", Pipe_props)

        return Pipe_props
    def broyden_good(x, y, f_equations, J_equations, tol=10e-10, maxIters=50):
        steps_taken = 0

        f = f_equations(x,y)
        J = J_equations(x,y)

        while res > tol and steps_taken < maxIters:

            s = sla.solve(J,-1*f)

            x = x + s[0]
            y = y + s[1]
            newf = f_equations(x,y)
            z = newf - f

            J = J + (np.outer ((z - np.dot(J,s)),s)) / (np.dot(s,s))

            f = newf
            steps_taken += 1
            res = np.linalg.norm(f,2)
            PSSDataMod().log_progress("\titeration: ", steps_taken,";\t residual = ", res )

        return steps_taken, x, y

    def convert_length(self, Pipe_props, native_units):
        """
        Converts the pipe length that are imported in the map CRS units to the native XPSS units.
        Valid options for the CRS units extracted:
            0 Meters
            1 Kilometers
            2 Imperial feet
            3 Nautical miles
            4 Imperial yard
            5 Terrestrial Miles
            6 Degrees
            7 Centimeters
            8 Millimeters
            9 Unknown
        """

        import itertools

        canvas = qgis.utils.iface.mapCanvas()
        map_units = canvas.mapUnits()
        layer_units = QgsDistanceArea().lengthUnits()
        units = qgis.core.QgsUnitTypes

        dm.log_progress("Map units are: "+units.toString(map_units))
        dm.log_progress("Vector layer units are: "+units.toString(layer_units))
        dm.log_progress("XPSS units are set to: "+units.toString(native_units))

        # if map_units is not native_units:
        #
        #     from enum import Enum
        #     class Units(Enum):
        #         Meters = 0
        #         Kilometers = 1
        #         Feet = 2
        #         NauticalMiles = 3
        #         Yards = 4
        #         TerrestrialMiles = 5
        #         Degrees = 6
        #
        #     # TODO: Correct so that the pipe length is not converted multiple times
        #     #pids = Pipe_props.iloc[:, Pipe_props.columns.get_loc('Pipe ID')].tonumpy()
        #     #Length = network_handling.calc_3d_length(params, )
        #     Length = Pipe_props.iloc[:,Pipe_props.columns.get_loc('Length [ft]')].to_numpy()
        #
        #     PSSDataMod().log_progress("Length:\n"+str(Length))
        #
        #     Pipe_props = Pipe_props.drop(columns=['Length [ft]'])
        #
        #     if map_units == 0:  #map units = meters
        #         if native_units == 2:  #native units = feet
        #             PSSDataMod().log_progress("Converting from "+Units(map_units).name+" to "+Units(native_units).name+"...")
        #             Length = Length*3.281
        #
        #     Pipe_props = self.append_col_to_table(Pipe_props, Length, ['Length [ft]'], data_type='float')

        factor = units.fromUnitToUnitFactor(layer_units, native_units)

        Length = Pipe_props['Length [ft]'].to_numpy()
        ID = Pipe_props['Pipe ID'].to_numpy()
        Length_ = []
        for id, length in itertools.zip_longest(ID, Length):
            l_calc = length*factor
            dm.log_progress(str(id)+": "+str(l_calc))
            Length_.append(l_calc)

        Pipe_props = dm.append_col_to_table(Pipe_props, Length, 'Length [ft]', data_type='float', replace=True)

        dm.log_progress(str(Pipe_props))
        dm.log_progress(str(Pipe_props.columns))

        return Pipe_props
