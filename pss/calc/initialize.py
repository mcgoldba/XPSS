
def initialize(self):
    """
    Populate class variables
    """

    run_checks=False

    if run_checks is True:
        [has_error, num_entity_err, num_pipes, num_nodes] = dataMod.check(check_pipe_conns, check_node_conns)
    else:
        [has_error, num_entity_err, num_pipes, num_nodes] = [False, False, 0, 0]

    [Pipe_props, Node_props, Pipe_nodes, res, res_elev] = dm.initialize_from_qepanet()

    [C, C_n, In, Pipe_props, sort_lst, node_srt_lst] = dataMod.create_conn_matrix(Pipe_nodes, Pipe_props, Node_props, res, num_entity_err, num_pipes, num_nodes)

    self.A = csr_matrix(numpy.delete(In, (0), axis=0))

    self.S = Node_props['Elevation [ft]']
