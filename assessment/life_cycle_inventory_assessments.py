import re
import pandas as pd
import numpy as np
from difflib import SequenceMatcher
from helpers import load_component_json, login, create_get_soup, create_post_soup, projects_dict, create_table, \
    reorder_dataframe, diff_two_dataframes, create_report_data_dirs


def compile_lci():
    """
    This function is used for phase 2 of the LCA, the life cycle inventory.
    The life cycle inventory data of the created projects are
    retrieved from eLCA. From the information compiled by eLCA on the input and
    output flows of the building over the product life cycle, various tables are
    created.

    Input:
    1) archetypes.json: List of dictionaries, where each dictionary describes an archetype of the quarter.
    2) eLCA Projects

    Output:
    1)  For each archetype, a table is created on the masses of the building materials.
        (ArchetypnameBaustoffe)
    2)  A table to show the neighbourhood composition, which means the names of the
        archetypes, the number of buildings of the archetype in the neighbourhood
        and floor areas. (Quartierszusammensetzung)
    3)  A table for the operation of the buildings with the final energy demand of
        the different archetypes and scenarios. (Gebäudebetrieb)
    Each table is saved as PDF and as CSV file in the folder
    report_data > life_cycle-inventory.

    """

    # Create report data folders if they don't exist already
    create_report_data_dirs()
    # Load information from user input
    archetypes: list[dict] = load_component_json("archetypes")
    # Create dictionary of all final energy demands and fill it later
    oper_dict = {}
    session = login()
    projects = projects_dict(session)
    project_names = list(projects.values())
    archetypes: list[dict] = load_component_json("archetypes")
    for archetype in archetypes:
        archetype_name = archetype['archetype name']
        # No spaces name is needed for file saving
        no_spaces_name = archetype_name.replace(' ', '')
        # Dictionary of final energy demands for each project of the archetype
        oper_one_arch = {}
        # Dictionary for material masses for each project of the archetype
        masses_frames_dict = {}
        archetype_projects = {k:v for (k,v) in projects.items() if archetype_name in v.split(" ")[0]}
        for project_id, project_name in archetype_projects.items():
            # Identify the refurbishment scenario
            refurb_variant = project_name.replace(f'{archetype_name} ', '')
            # Update session header
            response_project_overview = session.get("https://www.bauteileditor.de/projects/{}/".format(project_id))

            # Read final energy demand for each project
            operation_soup = create_get_soup(session, 'https://www.bauteileditor.de/project-report-effects/operation/', 'Elca\\View\\Report\\ElcaReportEffectsView')
            # Some energy sources cause errors and are not recognised in the balance sheet
            # Print error message if the energy sources are not balanced
            # Problem in the eLCA database
            try:
                final_energy = re.search(r"(.*) kWh", operation_soup.find('ul', attrs={'class': 'category final-energy'}).find('dd').text).group(1)
            except AttributeError:
                final_energy = None
                print(f'ERROR: The final energy balance for the project {project_name} must be checked! '
                  f'There is an error in the eLCA data set for the selected energy sources. '
                  f'Please delete all data created so far by executing the function "delete_projects()". '
                  f'Then start DisteLCA again and select another energy carrier or electricity source.')
            oper_one_arch.update({f'{refurb_variant} Endenergie in kWh/m²a': final_energy})

            # life_cycle_inventory for materials
            # Read table ranking mass from eLCA and create dataframe
            soup_LCI = create_post_soup(session, 'https://www.bauteileditor.de/project-report-assets/topAssets/', 'Elca\\View\\Report\\ElcaReportAssetsView', data={
                # Allow to show up to 200 materials at the same time to read all
                'limit': '200',
                # Present the materials in descending order with respect to mass
                'order': 'DESC',
                'inTotal': '1'
                })
            # Retrieve table input
            table_masses = soup_LCI.find('table', attrs={'class': 'report report-top-elements'})
            # Retrieve table headers and append them to a list of headers used for the new pandas dataframe
            titles = []
            for i in table_masses.find('thead').find('tr').find_all('th'):
                title = i.text
                titles.append(title)
            # Create pandas dataframe with table headers as columns
            masses_df = pd.DataFrame(columns=titles)
            # Create a for loop to fill mydata
            for j in table_masses.find('tbody').find_all('tr'):
                # fill dataframe row by row
                row_data = j.find_all('td')
                row = [i.text for i in row_data]
                length = len(masses_df)
                masses_df.loc[length] = row
            # Ranking row is not needed
            masses_df = masses_df.drop(columns=['#'])
            # Change type to float for further processing
            masses_df["Masse in kg"] = masses_df["Masse in kg"].str.replace(",", ".")
            masses_df = masses_df.astype({'Masse in kg': float})
            # Customise names of materials to indicate same materials throughout archetypes
            masses_df["Bauteil"] = masses_df["Bauteil"].str.extract(r"(.*) \[")
            masses_df["Bauteil"] = masses_df["Bauteil"].str.replace(" Sanierung", "")
            # Append dataframe to dictionary with project names as key and dataframe as value
            masses_frames_dict[project_name] = masses_df
        # Fill dictionary of all energy demands with archetype name as key and dictionary of energy
        # demand for all refurbishment alternatives as value
        # In total: dictionary of dictionaries
        oper_dict.update({archetype_name: oper_one_arch})

        # Customise masses_frames_dict to efficiently display all variants simultaneously
        masses_frames_list = list(masses_frames_dict.values())
        # Stock masses are defined by 1st item of frames
        # Order follows the projects order in eLCA
        # projects are sorted according to the alphabet in eLCA
        # Alphabetic order: 0 Außenwandsanierung, 1 Bestand, 2 Dachsanierung, 3 Fenstersanierung, 4 Komplettsanierung
        # Dataframes only including the new materials in comparison to existing buidling
        existing_df = masses_frames_list[1]
        df_diff_wall = diff_two_dataframes(existing_df, masses_frames_list[0])
        df_diff_roof = diff_two_dataframes(existing_df, masses_frames_list[2])
        # Stock windows are missing in refurbishment variant window refurbishment
        df_delete_windows = existing_df.drop(
            existing_df.loc[existing_df['Kostengruppe'] == '334 Außentüren und -fenster'].index)
        df_diff_window = diff_two_dataframes(df_delete_windows, masses_frames_list[3])
        # Change column name according to refurbishment variant
        existing_df.rename(columns={'Masse in kg': 'Masse in kg Bestand'}, inplace=True)
        df_diff_wall.rename(columns={'Masse in kg': 'Masse in kg Außenwandsanierung'}, inplace=True)
        df_diff_roof.rename(columns={'Masse in kg': 'Masse in kg Dachsanierung'}, inplace=True)
        df_diff_window.rename(columns={'Masse in kg': 'Masse in kg Fenstersanierung'}, inplace=True)
        # Merge frames of all variants
        merging_frames = [existing_df, df_diff_wall, df_diff_roof, df_diff_window]
        result_df = pd.concat(merging_frames)
        # Refurbishment of outer_walls and roof has all stock materials plus added materials
        # Fill NaN values with stock materials' information
        result_df["Masse in kg Außenwandsanierung"] = result_df["Masse in kg Außenwandsanierung"].fillna(result_df["Masse in kg Bestand"])
        result_df["Masse in kg Dachsanierung"] = result_df["Masse in kg Dachsanierung"].fillna(result_df["Masse in kg Bestand"])
        # Drop column on module
        result_df = result_df.drop(columns=['Modul'])
        # Fill Fenstersanierung with all stock values except the existing building windows
        result_df['Masse in kg Fenstersanierung'] = np.where((result_df['Kostengruppe'] !='334 Außentüren und -fenster'), result_df["Masse in kg Bestand"], result_df['Masse in kg Fenstersanierung'])
        # Create column on overall refurbishment as sum of all refurbishment variants
        group_roof = ['363 Dachbeläge', '361 Dachkonstruktionen', '364 Dachbekleidungen', '362 Dachfenster, Dachöffnungen', '369 Dächer, sonstiges']
        group_wall = ['331 Tragende Außenwände', '332 Nichttragende Außenwände', '333 Außenstützen', '335 Außenwandbekleidungen, außen', '335 Außenwandbekleidungen, innen', '337 Elementierte Außenwände', '339 Außenwände, sonstiges']
        # Fill overall refurbishment with new window parts
        result_df['Masse in kg Komplettsanierung'] = result_df['Masse in kg Fenstersanierung']
        # fill overall refurbishment with new roof parts
        for r in group_roof:
            result_df['Masse in kg Komplettsanierung'] = np.where((result_df['Kostengruppe'] == r ), result_df["Masse in kg Dachsanierung"], result_df['Masse in kg Komplettsanierung'])
        # fill overall refurbishment with new wall parts
        for w in group_wall:
            result_df['Masse in kg Komplettsanierung'] = np.where((result_df['Kostengruppe'] == w), result_df["Masse in kg Außenwandsanierung"], result_df['Masse in kg Komplettsanierung'])
        # Fill all NaN values with - for better readability
        result_df = result_df.fillna('-')
        # Change the decimal places from dot to comma for german notation and visualization
        # To change the notation all number data types have to be changed to strings
        result_df = result_df.astype({'Masse in kg Bestand': str,'Masse in kg Außenwandsanierung': str, 'Masse in kg Dachsanierung': str, 'Masse in kg Fenstersanierung': str, 'Masse in kg Komplettsanierung': str})
        float_cols = ['Masse in kg Bestand','Masse in kg Außenwandsanierung', 'Masse in kg Dachsanierung', 'Masse in kg Komplettsanierung']
        for col in float_cols:
            result_df[col] = result_df[col].str.replace('.', ',', regex=True)
        # Create plotly table
        create_table(result_df, f'{archetype_name} Baustoffe', f'report_data\life_cycle_inventory\{no_spaces_name}Baustoffe', 2000)
        result_df = result_df[0:0]
    print('Sachbilanz: Tabellen zu Massen der Baustoffe erstellt!')

    # Final energy demand life cycle inventory
    df_op = pd.DataFrame.from_dict(archetypes)
    df_op.reset_index(drop=True, inplace=True)
    df_op = df_op[["archetype name", "NFA in m²", "energy carrier template", "final energy heating in kWh/m²a", "final energy hot water in kWh/m²a"]]
    # Add unit to columns for better understanding
    df_op.rename(columns={"final energy heating in kWh/m²a": "existing building final energy heating in kWh/m²a","final energy hot water in kWh/m²a": "existing building final energy hot water in kWh/m²a"}, inplace=True)
    df_op.index = df_op['archetype name']
    # Add information on energy demand of refurbishment variants
    # Use dictionary from above
    refurb_oper_df = pd.DataFrame.from_dict(oper_dict, orient='index')
    # Reorder for better readability
    refurb_oper_df = reorder_dataframe(refurb_oper_df, [1,0,2,3,4])
    # Merge stock and refurbishment information
    df_op_all = pd.merge(df_op, refurb_oper_df, left_index=True, right_index=True)
    # Change the decimal places from dot to comma for german notation and visualization
    # To change the notation all number data types have to be changed to strings
    # Create plotly table
    create_table(df_op_all, 'Gebäudebetrieb', 'report_data\life_cycle_inventory\Gebäudebetrieb', 800)
    print('Sachbilanz: Tabelle zum Betrieb der Gebäude erstellt (Endenergiebedarf)!')

    # Create table of quarter composition from user input
    # Show details on archetypes
    df_quarter = pd.DataFrame.from_dict(archetypes)
    df_quarter.reset_index(drop=True, inplace=True)
    # Create plotly table
    create_table(df_quarter, 'Quartierszusammensetzung', 'report_data\life_cycle_inventory\Quartierszusammensetzung', 500)
    print('Sachbilanz: Tabelle zur Quartierzusammensetzung erstellt!')

    # # Show details on building components
    # df_comp = pd.DataFrame.from_dict(archetypes)
    # # Drop all columns that are not important for wall, roof and window components
    # df_comp.reset_index(drop=True, inplace=True)
    # unused_for_components = ['Anzahl im Quartier', 'BGF DIN 276', 'NGF DIN 276', 'NGF nach EnEV', 'Energie Heizung', 'Energie WW', 'WVA/Energieträger Vorlage', 'Außenwand ID', 'Fenster ID', 'Dach ID', 'WVA/Energieträger ID']
    # df_comp.drop(unused_for_components, axis=1, inplace=True)
    # # Add unit to columns for better understanding
    # df_comp.rename(columns={'Masse Außenwände': 'Fläche Außenwände in m²', 'Masse Dächer': 'Fläche Dächer in m²'}, inplace=True)
    # # Reorder dataframe
    # df_comp = reorder_dataframe(df_comp, [0,4,1,6,2,5,3])
    # # Change the decimal places from dot to comma for german notation and visualization
    # # To change the notation all number data types have to be changed to strings
    # df_comp = df_comp.astype({'Fläche Außenwände in m²': str, 'Fläche Dächer in m²': str})
    # df_comp['Fläche Außenwände in m²'] = df_comp['Fläche Außenwände in m²'].str.replace(".", ",", regex=True)
    # df_comp['Fläche Dächer in m²'] = df_comp['Fläche Dächer in m²'].str.replace(".", ",", regex=True)
    # # Create plotly table
    # create_table(df_comp, 'Bauteile', 'report_data\life_cycle_inventory\Bauteile', 500)
    # print('Sachbilanz: Tabelle zu Bauteilen der verschiedenen Archetypen erstellt')

