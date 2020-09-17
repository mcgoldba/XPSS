# User Defined Options

This document discussed the various variables that can be defined at the beginning of the `calc_pss_simple_v2.py` script.

## Boolean Switches 

* `debug`
    * **Description:**  If `True`, prints additional information to assist in debugging

* `zones`
    * **Description:**  Defines the amount of information that is exported to the `.csv` file from a calculation. 
        *  `True`:  After calculating system characteristics simply the results by grouping into zones
        *  `False`:  Display results for each pipe.

* `run_checks`
    * **Description:**  If `True` performs a check for a suitable pipe network geometry before running the calculation.
    * A valid pipe network is one in which:
        *  There is one reservoir.
        *  All pipes are connected such that all components form a single pipe network.
        *  The pipe network forms a "directed tree graph" structure such that each node has only one downstream pipe connection, and any number of upstream pipe connections.
    *  The following options can be set if `run_checks` is `True`:
        * `check_pipe_conns`
            * **Description:**  If `True`, checks if every pipe is connected to two nodes.
        * `check_node_conns`
            * **Description:**  If `True`, checks if every node is connected to at least 1 pipe.
