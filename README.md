# eLCArefurb - An extension to eLCA for the upscaled ecological assessment of refurbishment scenarios


To run the program, main must be started. Before that, some conditions must be fulfilled:
- download the packages listed in requirements (pip install -r requirements.txt)
- create an eLCA components editor account (https://www.bauteileditor.de/)
- A normal eLCA account can contain up to 15 projects. Since with this automation 5 projects are created per building, only 3 buildings can be examined at the same time with a normal eLCA account. An unlimited account can be requested from the BBSR.
- In the account used, the existing and renovation components for exterior walls, roof and windows of the buildings to be examined must be stored in component templates. These must follow the following naming convention:
    Existing component name: Name
    Renovation component name: Name Sanierung
- If the tool has been executed before, all result files and eLCA projects as well as the temporary files must be deleted before the tool is executed again.


## Description
eLCArefurb creates a life cycle assessment of possible renovation scenarios on multiple buildings by entering only a few pieces of information. For each archetype, the renovation scenarios exterior wall renovation, window renovation, roof renovation and complete renovation are automatically modelled and compared with each other. Only the external wall, roof and window components as well as the operation of the building are balanced. This enables a comparison of the total global warming potential (GWP) for the different scenarios. Furthermore, the refurbishment costs and the energy costs savings are calculated. Finally, the ecological aspects of GWP changes are compared with the economic aspects in order to allow a comprehensive evaluation of the refurbishment scenarios.

## Version
eLCArefurb is currently being developed and is based on eLCA v0.9.7. The current release enables the scenario assessment of a range of refurbishment measures (exterior walls, windows, roofs). In addition, the operational energy use is considered.

## Dependencies
eLCArefurb is currently being developed using Python 3.9 and a range of libraries. The user may install said dependencies by using the provided requirements.txt file. In addition, an account on www.bauteileditor.de was provided to the e3D for research purposes, which allows the creation of an unlimited number of projects. In order to use eLCArefurb with this account, a connection to the internet must exist and the corresponding login credentials have to be entered in the eLCArefurb login GUI. The login credentials can be requested from the Institute of Energy Efficiency and Sustainable Building (e3D), RWTH Aachen University. Using eLCArefurb with other eLCA Accounts limits the number of assessable archetypes to 15. To run the program, main must be started. Before that, some conditions must be fulfilled:
- download the packages listed in requirements (pip install -r requirements.txt)
- create an eLCA components editor account (https://www.bauteileditor.de/)
- In the account used, the existing and renovation components for exterior walls, roof and windows of the buildings to be examined must be stored in component templates. These must follow the following naming convention: Existing component name: Name, Renovation component name: Name Sanierung
- If the tool has been executed before, all result files and eLCA projects as well as the temporary files must be deleted before the tool is executed again.


## Installation
eLCArefurb can be used by cloning or downloading the whole eLCArefurb package from the GIT Repository.

## How to contribute to the development of eLCArefurb
You are invited to contribute to the development of eLCArefurb. You may report any issues by sending us an email to herzogenrath@e3d.rwth-aachen.de.

## How to cite eLCArefurb
Citation of BS2023 Paper

## How to cite original eLCA bauteileditor
- Life cycle assessment of buildings - Assessing the global ecological quality of a building with eLCA, Federal Institute for Research on Building, Urban Affairs and Spatial Development, Research News No 1/2015 - Building and Architecture. 

## Acknowledgments
The developers extend their sincere thanks to the German Federal Office for Building and Regional Planning for the support during the development of the eLCArefurb tool.