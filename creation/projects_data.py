# instead of "from typing import Union": Union[str, int] == str | int
from __future__ import annotations
import os
from pathlib import Path
from helpers import load_component_json, save_component_json, save_elca_csv, create_report_data_dirs
import pandas as pd

def prepare_projects_data():
    """

    This function transforms the data from the user input from the function "create_buildings_gui" on the archetypes and the read
    renovation components into the data formats necessary to create a project through a
    CSV import in eLCA. For each archetype defined by the user, 5 projects are to be created:
    Existing building, exterior wall renovation, roof renovation, window renovation and
    complete renovation.  For each project, a CSV file with the corresponding information
    about the building components exterior wall, roof and windows and a json file are
    created.The json file contains further information important for the project, such
    as name, floor space and energy balance. The final energy demand for heating for the
    renovation scenarios is estimated according to the TABULA building typology.
    The savings potentials are read in from the savings.csv file. This gives an estimate
    for the savings of the final energy demand depending on the building age class,
    energy source and renovation measure. To examine the calculations see
    additional_material_example_buildings > energy_savings_calculations > EndenergiebedarfTABULA.xlsx and
    website https://webtool.building-typology.eu/#bm.
    The final energy demand for the provision of hot water remains unchanged by the
    renovations. This corresponds to the modelling of renovation scenarios by the
    TABULA building typology.

    Input:
    1) refurb_alternatives.json: dictionary with IDs of stock templates as keys and IDs of corresponding refurbishment
        components as values
    2) archetypes.json: List of dictionaries, where each dictionary describes an archetype of the quarter.
    3) savings.csv: The final energy demand reduction potential for the renovation scenarios

    Output:
    1) JSON file for each archetype-refurbishment scenario combination
    2) CSV file with building components for each archetype-refurbishment scenario combination

    """
    # Create report data folders if they don't exist already
    create_report_data_dirs()
    # Read the energy saving potentials from the csv data
    df_savings = pd.read_csv('creation\savings.csv', encoding="utf-8")
    # Create a nested dictionary to access the data for the enregy savings
    # according to energy supply system and construction year class
    savings_dict = df_savings.groupby('Baualtersklasse')[['Energieträger', 'Wand', 'Dach', 'Fenster', 'Alles']].apply(
        lambda x: x.set_index('Energieträger').to_dict(orient='index')).to_dict()
    # load the information on the user-defined archetypes from archetypes.json
    archetypes: list[dict] = load_component_json("archetypes")
    # Load the dictionary, which assigns a rehabilitation alternative to each existing component.
    refurb_alternatives: dict[str, str] = load_component_json("refurb_alternatives")
    # Iterate through all archetypes to create CSV and JSON file for all archetypes
    # Create 5 projects per archetype: Existing building, exterior wall renovation,
    # roof renovation, window renovation and complete renovation.
    for archetype in archetypes:
        # Create sub folder with name of the archetype for each archetype in temp_data
        folder_name = Path('temp_data') / archetype['archetype name']
        os.makedirs(folder_name, exist_ok=True)

        # Create dictionaries with project data for the JSON file
        # This data is required to create a project in eLCA via CSV-Import
        # Data for the existing building
        # The data for the existing project are the same data from the user input
        stock_project_data: dict[str, str | int | float] = {
            # project names are always "archetype name + redevelopment scenario"
            'projectname': archetype['archetype name'] + " Bestand",
            # Gross ground space
            'gross_floor_area': archetype['GFA in m²'],
            # net ground space
            'net_floor_area': archetype['NFA in m²'],
            # net ground space according to EnEV
            'net_floor_area_enev': archetype['NFA in m²'],
            # energy need for heating
            'energy_heating': archetype['final energy heating in kWh/m²a'],
            # energy need for hot water
            'energy_water': archetype['final energy hot water in kWh/m²a'],
            # energy carrier Id
            'energy_source': archetype['energy carrier ID']
        }

        def csv_components(component_name: str, cost_group: int, mass_name: str, unit: str, id_name: str) -> dict[
            str, str | int | float]:
            if archetype[component_name] == "Outside the scope of the study":
                csv_dict = None
            else:
                csv_dict = {'Name': archetype[component_name],
                            'KG DIN 276': cost_group,
                            'Fläche': archetype[mass_name],
                            'Bezugsgröße': unit,
                            'eLCA BT ID': archetype[id_name]
                            }
            return csv_dict

        stock_outer_wall = csv_components('exterior walls template', 330, 'exterior walls area in m²', 'm²',
                                          'exterior walls ID')
        stock_window = csv_components('window template', 334, 'number of windows', 'Stück', 'window ID')
        stock_roof = csv_components('roof template', 360, 'roof area in m²', 'm²', 'roof ID')


        # create csv file with header and three rows (wall-row, window-row, roof-row)
        # This CSV file describes the existing building, therefore the name is "Archetypname + Bestand"
        save_elca_csv([stock_outer_wall, stock_window, stock_roof],
                      archetype['archetype name'] + " Bestand",
                      folder=folder_name)
        # Save JSON file on existing building with the same name convention
        save_component_json(stock_project_data,
                            archetype['archetype name'] + " Bestand",
                            folder=folder_name)

        # from here, information on remediation alternatives are compiled
        # Variante 1: Außenwand sanieren (outer wall refurbishment)
        # Variante 2: Fenster sanieren (window refurbishment)
        # Variante 3: Dach sanieren (roof refurbishment)
        # Variante 4: Dach, Fenster und Außenwand (outer wall, window and roof refurbishment)
        # Information that has to be changed for the refurbishment alternatives:
        # 1) Name of the project (+ Außenwandsanierung, Fenstersanierung etc.)
        # 2) Energy need for heating (according to savings.csv)
        # 3) Name of the refurbished component(s) in the CSV file (+ Sanierung)
        # 4) ID of the refurbished component(s) in the CSV file (according to refurb_alternatives.json)

        # Selection of energy saving potential from TABULA
        # retrieve construction year class and energy carrier from archetype.JSON
        construction_class = archetype["building age class"]
        energy_carrier = archetype["energy carrier template"]
        # Names of suppliers from csv data
        # Create list of energy suppliers defined in savings.csv
        heat_supply_systems = []
        for energy_supplier in savings_dict[construction_class].keys():
            heat_supply_systems.append(energy_supplier)
        # If none of the above-mentioned suppliers is used for the
        # archetype choose energy saving potentials for the gas supplier
        # Reason: Gas is the most used energy source in Germany
        energy_search = 'Gas'
        # Try to find energy carriers of the archetype in list of energy carriers output in savings.csv.
        # If one of the energy sources listed there matches the one of the archetype, energy_search will be updated.
        for heat_supply_system in heat_supply_systems:
            if heat_supply_system in energy_carrier:
                energy_search = heat_supply_system

        # VARIANTE 1: wall refurbishment
        # Create JSON file for wall refurbishment
        # Use data of existing building as base data
        project_data_var_1 = stock_project_data.copy()
        # update project name
        project_name_var_1 = archetype['archetype name'] + " Außenwandsanierung"
        project_data_var_1.update({'projectname': project_name_var_1})
        # update energy demand for heating with the savings potential from savings.csv according
        # to construction year class and energy carrier and round it to two decimals
        project_data_var_1["energy_heating"] = round(project_data_var_1["energy_heating"] * savings_dict[construction_class][energy_search]['Wand'],2)

        # Create CSV file for wall refurbishment
        #  csv file has the same windows and roof as the existing building,
        # but the outer wall has to be updated to the refurbishment version
        # Update wall row of csv file to refurbishment alternative
        outer_wall_var_1 = stock_outer_wall.copy()
        # Add the appendix " Sanierung" to the mane of the component as it is the refurbishment alternative
        # Alternative way to retrieve the name would be to access the name of the ID in the refurb_templates.json,
        # but it is easier to just
        # reassign the name here as the names always have to follow this same name convention
        outer_wall_var_1["Name"] += " Sanierung"
        # To create the corresponding refurbishment component access the dictionary refurb_alternatives
        # that assigns the refurbishment components to the existing components
        # As the csv file has to contain strings the data type of the ID has to be changd to string
        outer_wall_var_1["eLCA BT ID"] = refurb_alternatives[str(archetype["exterior walls ID"])]
        # save CSV file for outer wall refurbishment in directory of archetype
        # Only change the outer wall row in the csv file as the roof and window components wont be changed
        save_elca_csv([outer_wall_var_1, stock_window, stock_roof],
                      project_name_var_1,
                      folder=folder_name)
        # save JSON file for outer wall refurbishment in directory of archetype
        save_component_json(project_data_var_1,
                            project_name_var_1,
                            folder=folder_name)

        # VARIANTE 2: window refurbishment
        # see comments for wall refurbishment
        # the procedure here is analogous to the procedure for exterior wall refurbishment
        project_data_var_2 = stock_project_data.copy()
        # update project name
        project_name_var_2 = archetype['archetype name'] + " Fenstersanierung"
        project_data_var_2.update({'projectname': project_name_var_2})
        # update energy demand for heating with the savings potential from savings.csv according
        # to construction year class and energy carrier and round it to two decimals
        project_data_var_2["energy_heating"] = round(project_data_var_2["energy_heating"] * savings_dict[construction_class][energy_search]['Fenster'],2)
        window_var_2 = stock_window.copy()
        window_var_2["Name"] += " Sanierung"
        window_var_2["eLCA BT ID"] = refurb_alternatives[str(archetype["window ID"])]

        save_elca_csv([stock_outer_wall, window_var_2, stock_roof],
                      project_name_var_2,
                      folder=folder_name)
        save_component_json(project_data_var_2,
                            project_name_var_2,
                            folder=folder_name)

        # VARIANTE 3: roof refurbishment
        # see comments for wall refurbishment
        # the procedure here is analogous to the procedure for exterior wall refurbishment
        project_data_var_3 = stock_project_data.copy()
        project_name_var_3 = archetype['archetype name'] + " Dachsanierung"
        project_data_var_3.update({'projectname': project_name_var_3})
        project_data_var_3["energy_heating"] = round(project_data_var_3["energy_heating"] * savings_dict[construction_class][energy_search]['Dach'], 2)

        roof_var_3 = stock_roof.copy()
        roof_var_3["Name"] += " Sanierung"
        roof_var_3["eLCA BT ID"] = refurb_alternatives[str(archetype["roof ID"])]

        save_elca_csv([stock_outer_wall, stock_window, roof_var_3],
                      project_name_var_3,
                      folder=folder_name)
        save_component_json(project_data_var_3,
                            project_name_var_3,
                            folder=folder_name)

        # VARIANTE 4
        project_data_var_4 = stock_project_data.copy()
        project_name_var_4 = archetype['archetype name'] + " Komplettsanierung"
        project_data_var_4.update({'projectname': project_name_var_4})
        project_data_var_4["energy_heating"] = round(project_data_var_4["energy_heating"] * savings_dict[construction_class][energy_search]['Alles'], 3)
        # Change all components as here a complete refurbishment will be carried out
        save_elca_csv([outer_wall_var_1, window_var_2, roof_var_3],
                      project_name_var_4,
                      folder=folder_name)
        save_component_json(project_data_var_4,
                            project_name_var_4,
                            folder=folder_name)


