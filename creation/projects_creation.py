import os
import json
import re
from collections import defaultdict
from glob import glob
from helpers import login, create_get_soup


def create_elca_projects():
    """

    This function creates the projects in eLCA through the CSV import feature.
    The existing building components selected by the user are modelled for the
    existing scenario and the corresponding renovation components are modelled
    for the renovation scenarios. In addition, the floor areas
    and the energy source used with the corresponding final energy demand
    for heating and hot water are specified. The CSV files and json files created in projects_data
    are read for each project. Each archetype is mapped into a separate eLCA account.

    Input:
    1) JSON file for each archetype - refurbishment scenario combination
    2) CSV file with building components for each archetype - refurbishment scenario combination
    3) eLCA data

    Output:
    1) 5 eLCA projects per archetype

    """

    # Create list of archetype folders in temp data directory
    all_archetype_folders = glob("temp_data/*/")
    # Create dictionary with archetype names as keys and list of projects data as values
    all_projects = defaultdict(list)
    # Iterate through all archetypes
    for archetype_folder in all_archetype_folders:
        # Last part of the all_archetypes_folders entry is the archetype name
        # e.g. temp_data \\ ARCHETYP_NAME \\
        archetype_name = archetype_folder.split("\\")[1]
        # Each Archetype has 5 projects: Existing building, External Wall Refurbishment, Roof Refurbishment,
        # Window Refurbishment and Complete Refurbishment
        # Every project is defined by information from a JSON file
        # Make a list of projects JSON data in the specific archetype folder
        archetype_projects = glob(f"temp_data/{archetype_name}/*.json")
        # Iterate through the projects of the archetype to fill all: projects dictionary
        for archetype_project in archetype_projects:
            # Open the JSON data and append it to a dictionary with archetype
            # names as keys and list of projects data as values
            with open(archetype_project, encoding="utf-8") as file:
                all_projects[archetype_name].append(json.load(file))

    session = login()
    # Iterate through dictionary with archetype names as keys and list of projects data
    # as values to create all projects of one archetype in a certain eLCA account
    for i, (key, value) in enumerate(all_projects.items()):
        # LOGIN to eLCA user account of the Archetype number (up to 8 archetypes) to create the projects in eLCA

        # Iterate through refurbishment variants (in total 5 projects) in the values of the dictionary
        # The values consist of lists with all projects of the archetype
        for variant in value:
            # open CSV of the project to create project
            filename = f"temp_data/{key}/{variant['projectname']}.csv"
            # Set parameter to import CSV file in eLCA
            files = {
                'importFile': (os.path.basename(filename), open(filename, 'rb'), "text/csv"),
            }
            # Data for CSV import project creation
            # Post data to eLCA server through post response with requests
            response_validate = session.post('https://www.bauteileditor.de/project-csv/validate/',
                                             files=files,
                                             data={
                                                 'name': variant['projectname'],
                                                 # private construction measure
                                                 'constrMeasure': "1",
                                                 # generic postcode
                                                 'postcode': "12345",
                                                 # single family homes
                                                 'constrClassId': "210",
                                                 # At this point a BNB Benchmark System has to be set
                                                 # to create the project
                                                 # Later, the benchmark system is deselected,
                                                 # so that no benchmark system
                                                 # is selected, since no evaluation according to BNB is to take place
                                                 # See further below
                                                 # Benchmark system BNB-BN_2015 has the Version ID "6"
                                                 'benchmarkVersionId': "6",
                                                 # net floor space
                                                 'netFloorSpace': variant['net_floor_area'],
                                                 # gross floor space
                                                 'grossFloorSpace': variant['gross_floor_area'],
                                                 'upload': "Absenden"
                                             })

            # Create dictionary for POST data to confirm component collection from CSV
            element_data = {}
            # Load preview of the components to create the project to retrieve data from the source code
            preview_soup = create_get_soup(session, 'https://www.bauteileditor.de/project-csv/preview/',
                                           'Elca\\View\\Import\\Csv\\ProjectImportPreviewView')
            for item in preview_soup.find_all('li', {"class": "element"}):
                item_name = item.find('span').text
                # Reading the KGR 2. level of the cost group (e.g. 330)
                item_cg_two = re.search(r"option selected=\"\" value=\"(\d{3})\">",
                                        str(item('select')[0].contents)).group(1)
                # Reading the KGR 3. level of the cost group, if available (e.g. 334)
                try:
                    examine_third_level = re.search(r"option selected=\"\" value=\"(\d{3})\">",
                                                    str(item('select')[1].contents)).group(1)
                    item_cg_three = examine_third_level
                    # if Attribute Error occurs there is no third level
                except AttributeError:
                    item_cg_three = ""
                # Reading element quantity and unit (m2/ Stück)
                item_quantity = item.input.attrs["value"]
                item_unit = re.search(r"option selected=\"\" value=\"(.*?)\">", str(item('select')[2].contents)).group(
                    1)
                # Reading the rel_id of the elements (long element ID)
                rel_id = re.search(r"relId=(.{8}-.{4}-.{4}-.{4}-.{12})", item.a.attrs["href"]).group(1)
                # Reading the short element ID of each element
                tpl_element_id = item('input')[1].attrs["value"]
                # Reading the description of each element
                designation = item.a.attrs["title"]
                # Fill POST data dictionary with the information read about elements
                element_data.update({
                    'dinCode2[{}]'.format(rel_id): item_cg_two,
                    'dinCode3[{}]'.format(rel_id): item_cg_three,
                    'quantity[{}]'.format(rel_id): item_quantity,
                    'unit[{}]'.format(rel_id): item_unit,
                    # short ID
                    'tplElementId[{}]'.format(rel_id): tpl_element_id
                })
            # Post data dictionary to confirm project creation requires this at the end
            element_data.update({'createProject': 'Projekt erstellen'})
            # Create projects by confirming the components with the element_data
            # Project creation through POST request
            generation_response = session.post('https://www.bauteileditor.de/project-csv/preview/', data=element_data)
            # Project is now created!
            # Editing created project
            project_id_text = json.loads(generation_response.text)["Elca\\View\\ElcaModalProcessingView"]
            # Read the project ID
            project_id = re.search(r"data-action=\"/project-data/lcaProcessing/\?id=(\d{1,7})&amp",
                                   project_id_text).group(
                1)
            # Get request to update session headers and enter the project just created
            document = session.get(f'https://www.bauteileditor.de/projects/{project_id}/')

            # At each section of the project, the "Save" button must also be selected automatically
            # after creation so that the information is included in the life cycle assessment.
            # Read variant ID to make POST request on saving master data - general
            general_soup = create_get_soup(session, 'https://www.bauteileditor.de/project-data/general/',
                                           'Elca\\View\\ElcaProjectDataGeneralView')
            # Variant ID indicates planning phase - eLCArefurb only uses variant "preliminary planning"
            current_variant_id = \
            general_soup.find('div', {'class': 'form-section HtmlSelectbox-section currentVariantId'}).find('option',
                                                                                                            text="-- Bitte wählen --").find_next_sibling(
                name='option').attrs["value"]
            # Save and specify "existing building" project master data - general
            # and specify it as "existing building" to be able to tick the "Bestand" boxes
            general_save_data = {
                'name': variant['projectname'],
                'projectNr': '',
                # private constrcution measure
                'constrMeasure': '1',
                # Evaluation period 50 years
                'lifeTime': '50',
                # Building classification: single-family houses for residential purposes only
                'constrClassId': '210',
                # specify "existing building"
                'isExtantBuilding': 'true',
                'description': '',
                'street': '',
                # generic postcode
                'postcode': '12345',
                'city': '',
                'editor': '',
                'bnbNr': '',
                'eGisNr': '',
                # Deselect the BNB system evaluation (see above)
                'benchmarkVersionId': '',
                # 53 is Ökobaudat 2021 II but there are errors in this database,
                # that's why Ökobaudat 2016 is chosen with the ID 45
                'processDbId': '45',
                'currentVariantId': current_variant_id,
                'constrCatalogId': '',
                'constrDesignId': '',
                'livingSpace': '',
                'netFloorSpace': variant['net_floor_area'],
                'grossFloorSpace': variant['gross_floor_area'],
                'floorSpace': '',
                'propertySize': '',
                'pw': '',
                'pwRepeat': '',
                'save': 'Speichern'
            }
            # Save master dta - general through post request
            response_save = session.post('https://www.bauteileditor.de/project-data/save/', data=general_save_data)

            # Create function to save all components
            # from eLCArefurb templates
            # Outer walls have the code 246
            # Windows have the code 250
            # Roofs have the code 269
            def save_components(eLCA_component_category_id: int):
                # enter list of components of the project just created in this URL through get request
                components_soup = create_get_soup(session,
                                                  f'https://www.bauteileditor.de/project-elements/list/?t={eLCA_component_category_id}',
                                                  'Elca\\View\\ElcaProjectElementsView')
                # Make list of all components of the certain category (walls, roofs or windows)
                components = []
                for item in components_soup.find_all(name='h2', attrs={'class': 'headline'}):
                    # Read the ID of the component
                    component_id = re.search(r"(\d{7})", item.text).group(1)
                    # Append the ID to the list
                    components.append(component_id)
                # Iterate through list of components to save all components
                for component in components:
                    # POST request for saving requires name, quantity, description and U-Value
                    # The eLCArefurb window templates created through the window wizard have a
                    # different saving data structure than the other components (see under except)
                    # All windows created without the window wizard and all roofs and outer
                    # walls have the code structure to be saved with the code in "try section"
                    try:
                        # This is the code for  windows created without the
                        # window wizard and all roofs and outer walls
                        # Enter the component
                        component_soup = create_get_soup(session,
                                                         f'https://www.bauteileditor.de/project-elements/{component}/',
                                                         'Elca\\View\\ElcaElementView')
                        # Retrieve component name
                        component_name = component_soup.find(name='input', attrs={'name': 'name'}).attrs['value']
                        # Retrieve component quantity
                        component_quantity = component_soup.find(name='input', attrs={'name': 'quantity'})[
                            'value']
                        # Retrieve component description
                        component_description = component_soup.textarea.text
                        # Retrieve component U-Value
                        component_uvalue = component_soup.find(name='input', attrs={'name': 'attr[elca.uValue]'}).attrs[
                            'value']
                        # Windows (ID=250) have the unit "Stück" while other components have the unit "m2"
                        if eLCA_component_category_id == 250:
                            component_unit = 'Stück'
                        else:
                            component_unit = 'm2'
                        # Create dictionary for the data that has to be send to the eLCA server to
                        # save the components through post request
                        component_save_data = {
                            # Variant ID indicates planning phase - eLCArefurb only uses variant "preliminary planning"
                            'projectVariantId': current_variant_id,
                            'elementId': component,
                            'name': component_name,
                            'attr[elca.oz]': '',
                            'description': component_description,
                            'quantity': component_quantity,
                            'refUnit': component_unit,
                            'attr[elca.uValue]': component_uvalue,
                            # R-Value could be specified, but it's not necessary
                            'attr[elca.rW]': '',
                            # Dismantling (Rückbau), separation (Trennung) and recycling
                            # (Verwertung) factors can be specified
                            # to evaluate the Dismantling, separation and recycling criterion of the BNB System.
                            # This is not used in eLCArefurb
                            'attr[elca.bnb.eol]': '',
                            'attr[elca.bnb.separation]': '',
                            'attr[elca.bnb.recycling]': '',
                            'saveElement': 'Speichern'
                        }
                        # Save component of the project
                        save_component_response = session.post('https://www.bauteileditor.de/project-elements/save/',

                                                               data=component_save_data)
                    except KeyError:
                        # Windows created with the window wizard
                        # Retrieve information through Beautiful Soup
                        # Windows created through the window wizard can contain a lot of information about
                        # frames, gaskets, fittings, etc., all of which must be retrieved and saved in the next step.
                        window_soup = create_get_soup(session,
                                                      f'https://www.bauteileditor.de/project-elements/{component}/',
                                                      'Elca\\View\\Assistant\\WindowAssistantView')
                        # Information on the window name
                        window_name = window_soup.find(name='input', attrs={'name': 'name'}).attrs['value']
                        # Window width
                        window_width = window_soup.find(name='input', attrs={'name': 'width'}).attrs['value']
                        # Window height
                        window_height = window_soup.find(name='input', attrs={'name': 'height'}).attrs['value']
                        # Sealing (Abdichtung)
                        window_sealing_width = window_soup.find(name='input', attrs={'name': 'sealingWidth'}).attrs[
                            'value']
                        # More data on the specific window
                        # Blind frame width
                        fixedFrameWidth = window_soup.find(name='input', attrs={'name': 'fixedFrameWidth'}).attrs[
                            'value']
                        # Sash width
                        sashFrameWidth = window_soup.find(name='input', attrs={'name': 'sashFrameWidth'}).attrs['value']
                        # Mullions and transoms
                        numberOfMullions = window_soup.find(name='input', attrs={'name': 'numberOfMullions'}).attrs[
                            'value']
                        numberOfTransoms = window_soup.find(name='input', attrs={'name': 'numberOfTransoms'}).attrs[
                            'value']
                        # ID of blind frame material
                        processConfigId_fixedFrame = \
                            window_soup.find(name='input', attrs={'name': 'processConfigId[fixedFrame]'}).attrs['value']
                        # ID of sash frame material
                        processConfigId_sashFrame = \
                            window_soup.find(name='input', attrs={'name': 'processConfigId[sashFrame]'}).attrs['value']
                        # ID of glass type
                        processConfigId_glass = \
                            window_soup.find(name='input', attrs={'name': 'processConfigId[glass]'}).attrs[
                                'value']
                        # ID of sealing material
                        processConfigId_sealing = \
                            window_soup.find(name='input', attrs={'name': 'processConfigId[sealing]'}).attrs[
                                'value']
                        # ID of fittings
                        processConfigId_fittings = \
                            window_soup.find(name='input', attrs={'name': 'processConfigId[fittings]'}).attrs[
                                'value']
                        # Name of fittings
                        fittings = window_soup.find(name='input', attrs={'name': 'fittings'}).attrs['value']
                        # ID of handles
                        processConfigId_handles = \
                            window_soup.find(name='input', attrs={'name': 'processConfigId[handles]'}).attrs[
                                'value']
                        # Name of handles
                        handles = window_soup.find(name='input', attrs={'name': 'handles'}).attrs['value']
                        # ID of sun shade
                        processConfigId_sunscreenOutdoor = \
                            window_soup.find(name='input', attrs={'name': 'processConfigId[sunscreenOutdoor]'}).attrs[
                                'value']
                        # ID of glare shield
                        processConfigId_sunscreenIndoor = \
                            window_soup.find(name='input', attrs={'name': 'processConfigId[sunscreenIndoor]'}).attrs[
                                'value']
                        # ID of interior windowsill
                        processConfigId_sillIndoor = \
                            window_soup.find(name='input', attrs={'name': 'processConfigId[sillIndoor]'}).attrs['value']
                        # Size of interior windowsill
                        sillIndoorSize = window_soup.find(name='input', attrs={'name': 'sillIndoorSize'}).attrs['value']
                        # Depth of interior windowsill
                        sillIndoorDepth = window_soup.find(name='input', attrs={'name': 'sillIndoorDepth'}).attrs[
                            'value']
                        # ID of interior window soffit
                        processConfigId_soffitIndoor = \
                            window_soup.find(name='input', attrs={'name': 'processConfigId[soffitIndoor]'}).attrs[
                                'value']
                        # Size of interior window soffit
                        soffitIndoorSize = window_soup.find(name='input', attrs={'name': 'soffitIndoorSize'}).attrs[
                            'value']
                        # Depth of interior window soffit
                        soffitIndoorDepth = window_soup.find(name='input', attrs={'name': 'soffitIndoorDepth'}).attrs[
                            'value']
                        # ID of exterior windowsill
                        processConfigId_sillOutdoor = \
                            window_soup.find(name='input', attrs={'name': 'processConfigId[sillOutdoor]'}).attrs[
                                'value']
                        # Size of exterior windowsill
                        sillOutdoorSize = window_soup.find(name='input', attrs={'name': 'sillOutdoorSize'}).attrs[
                            'value']
                        # Depth of exterior windowsill
                        sillOutdoorDepth = window_soup.find(name='input', attrs={'name': 'sillOutdoorDepth'}).attrs[
                            'value']
                        # ID of exterior window soffit
                        processConfigId_soffitOutdoor = \
                            window_soup.find(name='input', attrs={'name': 'processConfigId[soffitOutdoor]'}).attrs[
                                'value']
                        # Size of exterior window soffit
                        soffitOutdoorSize = window_soup.find(name='input', attrs={'name': 'soffitOutdoorSize'}).attrs[
                            'value']
                        # Depth of exterior window soffit
                        soffitOutdoorDepth = window_soup.find(name='input', attrs={'name': 'soffitOutdoorDepth'}).attrs[
                            'value']

                        # create dictionary with all the window data
                        window_save_data = {
                            'context': 'project-elements',
                            'projectVariantId': current_variant_id,
                            'e': component,
                            'name': window_name,
                            'width': window_width,
                            'height': window_height,
                            'sealingWidth': window_sealing_width,
                            'fixedFrameWidth': fixedFrameWidth,
                            'sashFrameWidth': sashFrameWidth,
                            'numberOfMullions': numberOfMullions,
                            'numberOfTransoms': numberOfTransoms,
                            'processConfigId[fixedFrame]': processConfigId_fixedFrame,
                            'processConfigId[sashFrame]': processConfigId_sashFrame,
                            'processConfigId[glass]': processConfigId_glass,
                            'processConfigId[sealing]': processConfigId_sealing,
                            'processConfigId[fittings]': processConfigId_fittings,
                            'fittings': fittings,
                            'processConfigId[handles]': processConfigId_handles,
                            'handles': handles,
                            'processConfigId[sunscreenOutdoor]': processConfigId_sunscreenOutdoor,
                            'processConfigId[sunscreenIndoor]': processConfigId_sunscreenIndoor,
                            'processConfigId[sillIndoor]': processConfigId_sillIndoor,
                            'sillIndoorSize': sillIndoorSize,
                            'sillIndoorDepth': sillIndoorDepth,
                            'processConfigId[soffitIndoor]': processConfigId_soffitIndoor,
                            'soffitIndoorSize': soffitIndoorSize,
                            'soffitIndoorDepth': soffitIndoorDepth,
                            'processConfigId[sillOutdoor]': processConfigId_sillOutdoor,
                            'sillOutdoorSize': sillOutdoorSize,
                            'sillOutdoorDepth': sillOutdoorDepth,
                            'processConfigId[soffitOutdoor]': processConfigId_soffitOutdoor,
                            'soffitOutdoorSize': soffitOutdoorSize,
                            'soffitOutdoorDepth': soffitOutdoorDepth,
                            'saveElement': 'Speichern'
                        }
                        # save the windows with the data from the dictionary
                        response_save_window = session.post('https://www.bauteileditor.de/assistant/window/save/',
                                                            data=window_save_data)

            # Save components
            # Outer walls have the code 246 in eLCA
            save_components(246)
            # Windows have the code 250 in eLCA
            save_components(250)
            # Roofs have the code 269 in eLCA
            save_components(269)

            # Add final energy audit
            # Update headers to enter final energy input page
            enev_response = session.get('https://www.bauteileditor.de/project-data/enEv/')
            # Save the energy demand and specify net floor area according to EnEV
            ngf_enev_response = session.post('https://www.bauteileditor.de/project-data/saveEnEv/', data={
                'projectVariantId': current_variant_id,
                'addDemand': '',
                'addEnergyDemand': 'Bedarf hinzufügen',
                # Specify net floor area according to EnEV
                'ngf': variant['net_floor_area_enev'],
                'enEvVersion': ''
            })
            # Specify energy source and save
            energy_source_response = session.post('https://www.bauteileditor.de/project-data/selectProcessConfig/',
                                                  data={
                                                      'relId': 'newDemand',
                                                      'projectVariantId': current_variant_id,
                                                      'ngf': variant['net_floor_area_enev'],
                                                      'enEvVersion': '',
                                                      'headline': 'Baustoff suchen und wählen',
                                                      'p': '',
                                                      'sp': '',
                                                      # 53 is Ökobaudat 2021 II but there are errors in this database,
                                                      # that's why Ökobaudat 2016 is chosen with the ID 45
                                                      'db': '45',
                                                      'filterByProjectVariantId': '',
                                                      'tpl': '',
                                                      'b': 'operation',
                                                      'u': 'kWh',
                                                      'search': '',
                                                      # Category 8.06 Usage: Selections from this only.
                                                      'processCategoryNodeId': '679',
                                                      # retrive energy carrier ID chosen by user in GUI
                                                      'id': variant['energy_source'],
                                                      'select': 'Übernehmen'
                                                  })
            # Specify end energy for heating and warm water
            end_energy_response = session.post('https://www.bauteileditor.de/project-data/saveEnEv/', data={
                'projectVariantId': current_variant_id,
                # only one energy carrier in eLCArefurb
                'addDemand': '1',
                # energy carrier from JSON data
                'processConfigId[newDemand]': variant['energy_source'],
                # energy need for heating from JSON data
                'heating[newDemand]': variant['energy_heating'],
                # energy need for hot water from JSON data
                'water[newDemand]': variant['energy_water'],
                'lighting[newDemand]': '',
                'ventilation[newDemand]': '',
                'cooling[newDemand]': '',
                'isKwk[newDemand]': '',
                'saveEnergyDemand': 'Speichern',
                # Net floor area
                'ngf': variant['net_floor_area_enev'],
                'enEvVersion': ''
            })

            print(f"Projekt {variant['projectname']} erstellt!")

        print("Alle Projekte des Archetyps wurden erstellt")

    print("Alle Projekte wurden erstellt")
