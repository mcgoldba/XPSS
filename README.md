# XPSS

A collection of scripts to solve a pressure sewer system.  Used as a QGIS plugin, largely based on QEPANET.

https://gitlab.com/albertodeluca/qepanet

http://plugins.qgis.org/plugins/qepanet

Forked from QEPANET v2.05

# About
XPSS is a modification to the QEPANET plugin for QGIS which contains scripts that allow for the easy calculation of pressure sewer systems.  

QGIS is a open source GIS software.  Details can be found at https://qgis.org/en/site/.

QEPANET is an implementation of EPANET within QGIS.  EPANET is an open source branched pipe network calculator released by the US Enviornmental Protection Agency (EPA).  It is a common program for the calculation of branched pipe networks.  

The purpose of QEPANET is to recreate the functionality of EPANET within the framework of the QGIS software.  The added benefit here is that QGIS allows for the import and manipulation of map data which a branched pipe netork is built on.  QEPANET allow for the automatic extraction of elevations from a DEM layer, so that user input of elevations is not required.

XPSS scope differs from that of QEPANET in that XPSS aims to add functionality that is specifically suited for pressure sewer system calculations, beyond the original EPANET program.

# Requirements
XPSS is based on v. 2.5 of QEPANET, and requires QGIS v. 3.4.0 or greater.

# Benefits and Limitations

In terms of graph networks, pressure sewer systems are in the form of a branched tree graph.  This is a simpler subset of the general branched pipe network for which EPANET and QEPANET have been designed to use.  The goal of XPSS is to add additional fuctionality that allows for the easy setup and analysis of systems in the form of branched tree graph.

The requirements to uses the XPSS scripts are as follows:
1. The system must contain a single outlet (reservoir).
2. All end junctions are interpreted as pumps.

XPSS makes the additional assumptions about the system:




# Setup

1.  Install QGIS v. 3.4.0 or greater as described here:  https://qgis.org/en/site/forusers/download.html

2.  Do either of the following:
    
    a.  Copy the contents of this repository into C:\{QGIS Install Dir}\profiles\default\python\qepanet
    
    b.  If git is installed on the computer, open a command prompt from within the directory C:\{QGIS Install Dir}\profiles\default\python\qepanet and type:
        `git clone https://github.com/mcgoldba/XPSS.git`
        

# Additional Details

*  Information on the basic use of these scripts can be found in the [user guide](user_guide/user_guide.md)

*  Details on the various user defined options can be found [here](user_guide/user_defined_options.md) (**Work in Progress**)

*  Details on the theory behind these claculations can be founnd in the [theory guide](theory_guide/theory_guide.md)  (**Work in Progress**)

*  Information on the layout and organization of the source code can be found in the [developer's guide](dev_guide/dev_guide.md) (**Work in Progress**)

# No Warrant y or Guarantee

This software is offered as is, without any warranty or guarantee.  Use at your own risk.
