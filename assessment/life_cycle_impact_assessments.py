import re
from typing import Union, Any
import pandas as pd
from helpers import load_component_json, login, create_get_soup, projects_dict, create_table, create_five_grouped_table, reorder_dataframe, create_report_data_dirs
from difflib import SequenceMatcher


def calculate_lcia():
    """
    This function is used for phase 3 of the life cycle assessment, the impact assessment.
    The evaluations for the impact assessments on the total GWP from eLCA are read and
    tables for the different archetypes and remediation scenarios are created.

    Input:
    1) archetypes.json: List of dictionaries, where each dictionary describes an archetype of the quarter.
    2) eLCA Projects

    Output:
    1)  For each archetype, a table is compiled on different GWP estimates. There is
        one column for each renovation scenario. The global warming potential on a
        neighbourhood scale (scaled to the corresponding number of buildings), for
        a single building, module B6, construction, individual components and
        building materials is given. In addition, the potential savings compared
        to a completely new building are provided. (ArchetypnameWirkungsanalyse)
    2)  A table showing the allocation of the total GWP to the individual life cycle
        modules (A1-A3, B4, B6, C3, C4, Total, D) depending on the project is created. (Lebenszyklusmodule)
    Each table is saved as a PDF and a CSV file in the folder
    report_data > life_cycle-impact.

    """
    # Create report data folders if they don't exist already
    create_report_data_dirs()
    # Load information from user input
    archetypes: list[dict] = load_component_json("archetypes")
    # Create dictionary for life cycle impact assessment
    lcia_frames_dict = {}

    # Create dataframe to evaluate the gwp of the life cycle modules with specified columns
    df_lca_modules = pd.DataFrame(columns=['Projektname', 'A1-A3: Herstellung', 'B4: Ersatz', 'B6: Betrieblicher Energieeinsatz', 'C3: Abfallbehandlung', 'C4: Deponierung', 'Gesamt', 'D: Recyclingpotenzial'])
    list_lca_modules = []
    session = login()
    projects = projects_dict(session)
    project_names = list(projects.values())
    for archetype in archetypes:
        archetype_name = archetype['archetype name']
        # Get net floor space for the archetype from user input
        net_ground_space = (next((item for item in archetypes if item['archetype name'] == archetype_name), None))['NFA in m²']
        # Create dictionary for every archetype
        projects_evaluation_data = {}
        archetype_projects = {k: v for (k, v) in projects.items() if archetype_name in v.split(" ")[0]}
        for project_id, project_name in archetype_projects.items():
            # Create empty dictionary for gwp information on each component of the project and fill it later
            elements_catalog = {}
            # Enter project to update header
            project_overview_response = session.get("https://www.bauteileditor.de/projects/{}/".format(project_id))
            # Enter overall balance in eLCA
            summary_soup = create_get_soup(session, 'https://www.bauteileditor.de/project-reports/summary/', 'Elca\\View\\Report\\ElcaReportSummaryView')
            # Retrieve data from overall balance table in eLCA
            gwp_tabelle = summary_soup.find('table', {'class': 'GPWtabelle'})  # Achtung typo!
            # Retrieve total GWP
            gwptotal = gwp_tabelle.find('td', text="GWP").find_next_sibling(name='td', attrs={'class': 'lastColumn'}).text
            # Retrieve GWP of module B6
            gwpb6 = gwp_tabelle.find('td', text="B6").find_next_sibling(name='td', attrs={'class': 'lastColumn'}).text
            # Retrieve GWP of constrcution (walls, windows and roof)
            gwpkg300 = gwp_tabelle.find('td', text="KG 300").find_next_sibling(name='td',
                                                                               attrs={'class': 'lastColumn'}).text
            # Round values
            # To round values the decimal seperator comma has to be exchanged
            # through a dot and the datatype has to be float
            gwp_float = float(gwptotal.replace(',', '.'))
            # Create dictionary from information of overall balance
            overall = {'GWP pro Gebäude': gwptotal,
                       'Modul B6': gwpb6, 'Konstruktion (KGR 300)': gwpkg300}

            # Fill Data Frame of LCA modules
            # GWP A1-A3: Herstellung
            product_stage = summary_soup.find_all(name='li', attrs={'class':'section clearfix'})[0].find(name='tbody').find(name='tr', attrs={'class': 'firstRow'}).contents[2].text
            # GWP B4: Ersatz
            replacement = summary_soup.find_all(name='li', attrs={'class':'section clearfix last'})[1].find(name='tbody').find(name='tr', attrs={'class': 'firstRow'}).contents[2].text
            # GWP B6: Betrieblicher Energieeinsatz
            operational_energy_use = summary_soup.find_all(name='li', attrs={'class':'section clearfix'})[1].find(name='tbody').find(name='tr', attrs={'class': 'firstRow'}).contents[2].text
            # GWP C3: Abfallbehandlung
            waste_processing = summary_soup.find_all(name='li', attrs={'class':'section clearfix'})[2].find(name='tbody').find(name='tr', attrs={'class': 'firstRow'}).contents[2].text
            # GWP C4: Deponierung
            disposal = summary_soup.find_all(name='li', attrs={'class':'section clearfix'})[3].find(name='tbody').find(name='tr', attrs={'class': 'firstRow'}).contents[2].text
            # GWP D: Recyclingpotenzial
            rec_potential = summary_soup.find_all(name='li', attrs={'class':'section clearfix'})[4].find(name='tbody').find(name='tr', attrs={'class': 'firstRow'}).contents[2].text
            # Add information on GWP of lca modules in list of dictionaries
            list_lca_modules.append({
                'Projektname': project_name,
                'A1-A3: Herstellung': product_stage,
                'B4: Ersatz': replacement,
                'B6: Betrieblicher Energieeinsatz': operational_energy_use,
                'C3: Abfallbehandlung': waste_processing,
                'C4: Deponierung': disposal,
                'Gesamt': gwptotal,
                'D: Recyclingpotenzial': rec_potential})

            # Enter overall building element catalog in eLCA
            elements_soup = create_get_soup(session, 'https://www.bauteileditor.de/project-reports/elements/', 'Elca\\View\\Report\\ElcaReportEffectsView')
            # Read information on all building components
            # for each component of the components of the project:
            for element in list(elements_soup.find('ul', attrs={'class': 'category'}).contents):
                # Find the name
                element_name = element.find(name='a', attrs={'class': 'page'}).text
                # Find the ID
                element_id = re.search(r"\/project-elements\/(\d+)", element.find('a').attrs['href']).group(1)
                # Find the GWP
                element_gwp = element.find(name='td', attrs={'class': 'total'}).text
                data_url = str(element.find('h3').attrs['data-url'])
                picture_size = (re.search(r'm2a=(\d*\.*\d+)', data_url).group()).replace("m2a=","")

                # Refurbishment components have the same name as the stock alternative plus " Sanierung" appendix
                # To allow faster comparison drop " Sanierung" appendix
                if "Sanierung" in element_name:
                    element_name = element_name.replace(" Sanierung", "")
                # Fill the dictionary with element names as keys and element GWP as values
                elements_catalog[element_name] = element_gwp

                # Read the results for the different building materials per component
                params: tuple[tuple[str, Union[str, Any]], tuple[str, str], tuple[str, str], tuple[str, str]] = (
                    # ID of the element
                    ('e', element_id),
                    # picture size
                    ('m2a', picture_size),
                    ('a', '0'),
                    ('rec', '0'),
                )
                element_details_soup = create_get_soup(session, 'https://www.bauteileditor.de/project-report-effects/elementDetails/', 'Elca\\View\\Report\\ElcaReportEffectDetailsView', params=params)
                # Customise the material names for unity between archetype variants - easier data processing
                # Delete specific ID in name, if there is one
                # (names of the materials have the strcuture "[ID numbers] no. materialname")
                pattern1 = re.compile(r"\[\d+] \d{1,2}\.(.*)")
                pattern2 = re.compile(r"\d{1,2}\.(.*)")
                for detail in element_details_soup.find_all('li', attrs={'class': 'section clearfix'}):
                    # Materialname with all numbers and the ID
                    detail_name_all = detail.find(name='h4').text
                    # GWP of the material
                    detail_gwp = detail.find(name='tbody').find(name='td', attrs={'class': 'total'}).text
                    # filter the materialname using regular expression
                    try:
                        detail_name = re.search(pattern1, detail_name_all).group(1)
                    except AttributeError:
                        try:
                            detail_name = re.search(pattern2, detail_name_all).group(1)
                        except AttributeError:
                            detail_name = detail_name_all
                    # Adding the material to the part catalog under the designation to which part the material belongs.
                    elements_catalog[f'{element_name}: Baustoff {detail_name}'] = detail_gwp

            # Enter "Eingesparte Umwelteinwirkungen" and retrieve saved GWP through existent building components
            extant_savings_soup = create_get_soup(session, 'https://www.bauteileditor.de/report/extant-savings/savings/', 'Elca\\View\\Report\\ExtantSavingsView')
            existing_vs_new = extant_savings_soup.find('table', {'class': 'report report-effects'}).find('td',
                                                                                                         text="GWP").find_next_sibling(
                name='td', attrs={'class': 'lastColumn'}).text
            extant = {'Ersparnis Bestand vs. Neubau': existing_vs_new}
            # Merge all the evaluation data into one dictionary for the archetype with projectname
            # as key and dictionaries of LCIA data as values
            projects_evaluation_data[project_name] = {**overall, **extant, **elements_catalog}

        # Now all LCIA data is retrieved from eLCA
        # Create dataframe from dictionary of dictionaries on LCIA data for all projects
        lcia_frame = pd.DataFrame.from_dict(projects_evaluation_data)
        # Fill NaN values with '_' for better readability
        lcia_frame = lcia_frame.fillna('-')
        # Set index as new column
        lcia_frame['Wirkungsanalyse'] = lcia_frame.index
        # Drop index
        lcia_frame.reset_index(drop=True, inplace=True)
        # Reorder the frame for better readability
        lcia_frame = reorder_dataframe(lcia_frame, [5,1,0,2,3,4])
        # Add the frame to dictionary of all archetype frames
        # Archetype names as keys and dataframe of the archetype that summarizes
        # all data for all refurbishment scenarios as value
        lcia_frames_dict[archetype_name] = lcia_frame

    # Iterate through dictionary to create plotly tables
    for key, value in lcia_frames_dict.items():
        # No spaces name for filename
        no_spaces_name = key.replace(' ', '')
        # Create plotly table
        create_table(value, f'{key} Wirkungsanalyse (GWP<sub>total</sub> in kg CO<sub>2</sub>-Äqv./m<sup>2</sup><sub>NGF</sub>a)', f'report_data\life_cycle_impact\{no_spaces_name}Wirkungsanalyse', 2500)
    print('Wirkungsabschätzung: Tabellen zu GWP der Projekte wurden erstellt!')

    # Use dataframe of life cycle modules to create plotly table
    # Create Pandas dataframe from list of dictionaries on LCA modules for each project
    df_lca_modules = pd.DataFrame.from_records(list_lca_modules)
    # Create a plotly table, that groupes all projects of the same archetype through colour scheme
    create_five_grouped_table(df_lca_modules, 'Wirkungsanalyse Lebenszyklusmodule (GWP<sub>total</sub> in kg CO<sub>2</sub>-Äqv./m<sup>2</sup><sub>NGF</sub>a)', 'report_data\life_cycle_impact\Lebenszyklusmodule', 1000)
    print('Wirkungsabschätzung: Tabelle zu GWP der Lebenszyklusmodule wurde erstellt!')


