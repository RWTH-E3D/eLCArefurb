from creation.components_collection import collect_templates
from creation.projects_data import prepare_projects_data
from creation.projects_creation import create_elca_projects
from gui.gui_buildings_input import create_buildings_gui
from gui.gui_projects_delete import delete_projects
from assessment.life_cycle_inventory_assessments import compile_lci
from assessment.life_cycle_impact_assessments import calculate_lcia
from assessment.life_cycle_interpretation_assessments import interpret_lca
from assessment.final_rating_diagram import create_rating_diagram
from assessment.life_cycle_costing_assessments import analyse_life_cycle_costs
from gui.login_credentials import create_login_gui
import warnings
warnings.simplefilter(action='ignore', category=FutureWarning)



def main():
    """

    eLCArefurb creates a life cycle assessment of possible renovation scenarios on multiple buildings by
    entering only a few pieces of information. For each
    archetype, the renovation scenarios exterior wall renovation, window renovation, roof
    renovation and complete renovation are automatically modelled and compared with each other.
    Only the external wall, roof and window components as well as the operation of the building
    are balanced. This enables a comparison of the total global warming potential (GWP) for the
    different scenarios. Furthermore, the refurbishment costs and the energy costs savings are calculated.
    Finally, the ecological aspects of GWP changes are compared with the economic aspects in order
    to allow a comprehensive evaluation of the refurbishment scenarios.

    """

    create_login_gui()
    # collect_templates reads the energy sources, outer walls, windows and roofs from eLCA,
    # which can be chosen by the user in the gui dropdown-box.
    # Existing building components are assigned to the appropriate refurbishment alternative.
    collect_templates()
    # Create a graphical user interface where a user can enter information
    # on stock building archetypes of a quarter.
    create_buildings_gui()
    # Transform the data from the user input on the archetypes and the read
    # renovation components into the data formats necessary to create a project through a
    # CSV import in eLCA. For each archetype defined by the user, 5 projects are to be created:
    # Existing building, exterior wall renovation, roof renovation, window renovation and
    # complete renovation.
    prepare_projects_data()
    # Create the projects in eLCA through the CSV import feature.
    # The existing building components selected by the user are modelled for the
    # existing scenario and the corresponding renovation components are modelled
    # for the renovation scenarios.
    # The energy source and the corresponding final energy demand
    # for heating and hot water are specified.
    create_elca_projects()
    # compile_lci is used for phase 2 of the LCA, the life cycle inventory.
    # The life cycle inventory data of the created projects are
    # retrieved from eLCA. From the information compiled by eLCA on the input and
    # output flows of the building over the product life cycle, various tables are
    # created.
    compile_lci()
    # calculate_lcia is used for phase 3 of the LCA, the impact assessment.
    # The evaluations for the impact assessments on the total GWP from eLCA are read and
    # tables for the different archetypes and remediation scenarios are created.
    calculate_lcia()
    # interpret_lca is used for phase 4 of the LCA, the interpretation. The data from the
    # impact assessment phase is read in and processed to create visualisations on the
    # identification of pollution hotspots, the comparison of refurbishment scenarios
    # and the temporal distribution.
    interpret_lca()
    # analysis_life_cycle_costs is used to calculate the costs for the refurbishment measures
    # according to the best base and worst case. In addition, the net present value of the
    # energy cost savings is calculated and compared to the costs for the refurbishment.
    analyse_life_cycle_costs()
    # create_rating_diagram compares the changes in GWP with the economic impacts.
    # In addition, the changes in GWP per euro spent are determined to allow prioritization of the different scenarios.
    create_rating_diagram()
    # delete_projects creates a graphical user interface that asks the user whether the projects
    # in the eLCA accounts, the temporary files for creating the eLCA projects and the report data should be deleted.
    # Deleting the files and projects allows the programme to be run again.
    delete_projects()
    # end programme
    return 0


if __name__ == '__main__':
    main()



