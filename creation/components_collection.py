from __future__ import annotations
import json
import re
from bs4 import BeautifulSoup
from helpers import login, create_post_soup, load_component_json, save_component_json, save_elca_csv


def collect_templates():
    """
    This function reads the energy sources, outer walls, windows and roofs from eLCA,
    which can be chosen by the user in the GUI dropdown-box from the next eLCArefurb function.
    Existing building components are assigned to the appropriate refurbishment alternative.
    The templates are read in the user account.
    If further components are needed outside the templates already created,
    they can be created in the indicated account via the eLCA Bauteileditor and in the
    "Vorlagen Erstellung" project.
    The components must then be saved as component templates.
    For each newly created existing component, a renovation component must be created,
    otherwise the components will not be read by eLCArefurb.
    The naming of the two matching components must comply with the following naming convention:
    Existing component: Name
    Refurbishment component: Name Sanierung
    For each material within the component, it must be indicated whether it is an existing material
    or a new material (tick the existing material box). For stock components all materials are classified as "stock"
    and for refurbishment components some are not. Window refurbishment components are completely new, as they are
    replaced as a whole.

    Input:
    1) Components in eLCA account
    2) Energy carriers from elCA account

    Output:
    1) energy_sources: dictionary with names of energy sources as keys and corresponding IDs as values
    2) refurb_alternatives: dictionary with IDs of stock templates as keys and IDs of corresponding refurbishment
                            components as values
    3) stock_templates: list of dictionaries where every list item describes a stock component
                        and every item consists of a dictionary with information on the component
    4) refurb_templates: list of dictionaries where every list item describes a refurbishment component
                        and every item consists of a dictionary with information on the component
    5) templates.csv:  This CSV file contains all component templates (existing and refurbishment) and can be imported
                        into eLCA; this allows the component templates to be used in other accounts as well
    6) templates.json: List of dictionaries, where each list element defines a component as a dictionary with
                        information on the component such as name, ID and cost group. This file contains both as-built
                        components and refurbishment components

    """
    # Note that the program has started
    print("Das Programm eLCArefurb wurde gestartet. Die Bauteilvorlagen aus eLCA werden eingelesen. In wenigen Sekunden wird die grafische Benutzeroberfläche angezeigt.")
    session = login()
    # Selection of final energy source Category 8.06 Use (the broadest selection)

    # List of all templates for testing reasons
    templates: list[dict] = []
    # List for the components to be available for selection in the gui
    stock_templates: list[dict] = []
    # List of components that are available as refurbishment alternatives have the same name as the
    # Existing building components with "Sanierung" appendix
    refurb_templates: list[dict] = []
    # Dictionary in which the refurbishment alternative is assigned to each existing building component
    refurb_alternatives: dict = {}
    # These elements are excluded in eLCArefurb, as they do not allow independent modelling of window and wall
    wrong_elements = [
        "2016_AW_mit_Fenster_Beispiel",
        "m²_Fenster / Isoglas 2-Scheiben / Alurahmen",
        "Stück_Fenster_1,6m² / Isoglas 2-Scheiben / Alurahmen",
        "Außenwand / einschaliges Mauerwerk / WDVS mit Fenster"
    ]

    component_groups: list[tuple[str, str]] = [("outer_walls", "246"), ("roofs", "269"), ("windows", "250")]
    for component, component_no in component_groups:
        # Create a function to read the names and IDs of the components in the eLCA templates
        def find_all_element_ids(response_text: str,
                                 filter_names: list[str] = None) -> list[int]:
            elements_view = json.loads(response_text)["Elca\\View\\ElcaElementsView"]
            elements_soup = BeautifulSoup(elements_view, "lxml")
            id_expr = re.compile(r"elca-sheet-(\d+)")
            name_expr = re.compile(r"(.+) \[\d+]")
            ids = []
            for element in list(elements_soup.find_all(name="div", attrs={"class": "elca-element-sheet"})):
                element_name_import = name_expr.search(element.find(name="h2", attrs={"class": "headline"}).text).group(1)
                element_name = element_name_import.replace(" (Importiert)", "")
                # if the element name matches with any of the names of the defined wrong_elements, stop and don't append
                # this element id
                if filter_names and any(wrong_element == element_name for wrong_element in wrong_elements):
                    continue

                ids.append(re.search(id_expr, element.attrs["id"]).group(1))
            return ids

        first_page_response = session.post('https://www.bauteileditor.de/elements/list/', data={
            #  Each component category has an ID, see line 93 "component groups".
            't': component_no,
            'search': '',
            'constrCatalogId': '',
            'constrDesignId': '',
            # "53" is Ökobaudat 2021 II ID, but there are errors in this database,
            # that's why Ökobaudat 2016 is chosen with the ID "45".
            'processDbId': '45',
            # Only private components should be read in, since only these
            # can ensure that they meet the requirements for modeling in
            # eLCArefurb. Public component templates are subject to change
            # over time that could generate an error output in eLCArefurb
            'scope': 'private'
        })
        # The components defined above, which can not be eco-balanced via eLCArefurb, are not
        # read in, this is ensured by the parameter filter_names
        element_ids = find_all_element_ids(first_page_response.text, filter_names=wrong_elements)
        # The display of the part templates can take up several pages in eLCA.
        # Therefore, all pages are read starting from page 1.
        # As soon as the "next_page_response" is no longer given (FALSE) the reading of parts is also interrupted.
        i = 1
        while True:
            next_page_response = session.get(
                f'https://www.bauteileditor.de/elements/list/?t={component_no}&page={i}',
                data={'t': component_no, 'page': i}
            )
            new_element_ids = find_all_element_ids(next_page_response.text, filter_names=wrong_elements)

            if not new_element_ids:
                break
            # Append to the List of element IDS
            element_ids.extend(new_element_ids)
            # Go to next page
            i += 1
        # Get more information about the component templates
        # Iterate through all components using their IDs
        for element_id in element_ids:
            # Enter the template page in eLCA
            element_response = session.get(f'https://www.bauteileditor.de/elements/{element_id}/')
            # Windows have a different website structure in eLCA than exterior walls and roofs,
            # therefore the information on Windows is retrieved differently than the information
            # about the other components, which is expressed here by "if" and "else".
            if component == "windows":
                # The JSON response has several sections, including: ElcaOsitView and ElcaElementView
                # For windows: the ElcaOsitView section contains the information on the cost group and the template name
                # ElcaElementView contains information on the description
                first_section_element_html = json.loads(element_response.text)["Elca\\View\\ElcaOsitView"]
                component_soup = BeautifulSoup(first_section_element_html, 'lxml')
                # Retrieve cost group of the template component
                cost_group = re.search(r"(\d{3})", component_soup.find(name='a', attrs={'class': 'page'}).text).group(1)
                # Retrieve template name
                template_name_import = re.search(r"(.*) \[", component_soup.find(name='li', attrs={'class': 'library active'}).span.text).group(1)
                template_name = template_name_import.replace(" (Importiert)", "")
                try:
                    # Windows created via the window wizard in eLCA are represented by two different tabs.
                    # Through the second_window_tab_response the second tab is accessed
                    # The description of the window can only be accessed through this second tab
                    second_window_tab_response = session.get(f'https://www.bauteileditor.de/elements/general/?e={element_id}&tab=general')
                    second_window_tab_html = json.loads(second_window_tab_response.text)["Elca\\View\\ElcaElementView"]
                    soup_second_window_tab = BeautifulSoup(second_window_tab_html, 'lxml')
                    # Description of the template
                    description = soup_second_window_tab.textarea.text
                    template_u_value = soup_second_window_tab.find(name='input', attrs={'name': 'attr[elca.uValue]'}).attrs['value']
                # Windows that are not created using the window wizard
                # (some windows of the public component templates, for example) have only one tab.
                # So if there is no second tab, an attribute or key error occurs and the description
                # of the window can be read in the original first tab
                except AttributeError or KeyError:
                    # JSON section ElcaElementView contains information on the description
                    second_section_element_html = json.loads(element_response.text)["Elca\\View\\ElcaElementView"]
                    description_soup = BeautifulSoup(second_section_element_html, 'lxml')
                    description = description_soup.textarea.text
                    template_u_value = \
                    soup_second_window_tab.find(name='input', attrs={'name': 'attr[elca.uValue]'}).attrs['value']
                # At the beginning of the development of eLCArefurb, public templates were still included,
                # therefore the information about the publicity of the templates is
                # recorded in the dictionary for each component. In the further course of the software development,
                # the decision was made to include only private components.
                # All elements are private (see above)
                public = False
            else:
                # This section is for roofs and outer walls
                # Roofs and walls all have only one tab
                first_section_element_html = json.loads(element_response.text)["Elca\\View\\ElcaElementView"]
                soup_element_information = BeautifulSoup(first_section_element_html, 'lxml')
                template_name_item = soup_element_information.find(name='input', attrs={'name': 'name'})
                # Full name of the component template
                template_name_import = template_name_item.attrs['value']
                template_name = template_name_import.replace(" (Importiert)", "")
                # The public templates cannot be overwritten.
                # This can be used to determine whether the templates are public or private (see comment above)
                public = "readonly" in template_name_item.attrs
                # Retrieve description
                description = soup_element_information.textarea.text  # Beschreibung der Bauteilvorlage
                template_u_value = soup_element_information.find(name='input', attrs={'name': 'attr[elca.uValue]'}).attrs['value']
                # Second section of the JSON response contains the cost group
                second_element_html = json.loads(element_response.text)['Elca\\View\\ElcaOsitView']
                soup_element_cost_group_information = BeautifulSoup(second_element_html, 'lxml')
                cost_group = re.search(r"(\d{3})", soup_element_cost_group_information.find(name='a', attrs={'class': 'page'}).text).group(1)
            # Append all information to dictionary
            # This information is necessary to create projects in eLCA through CSV-Import
            # only the information on publicity is not necessary
            if template_u_value == "":
                template_u_value = "no information in eLCA"
            if description == "":
                description = "no information in eLCA"
            element_dict = {"template_name": template_name, "CG_DIN_276": cost_group, "UUID": element_id,
                            "description": description, "public": public, "U-Value": template_u_value}
            # Create a csv file to use component templates in other accounts if needed
            # To create projects through csv import the reference unit must be specified
            # Windows are specified in pieces and roofs and walls in m²
            if 'Fenster' in template_name:
                reference_unit = 'Stück'
            else:
                reference_unit = 'm²'
            # Append information to dictionary. The dictionary has the form that would be necessary for the csv import.
            elca_csv_dict = {'Name': template_name, 'KG DIN 276': cost_group, 'Fläche': 1, 'Bezugsgröße': reference_unit, 'eLCA BT ID': element_id}
            # "Templates" is a list of all dictionries with information on the components
            templates.append(elca_csv_dict)
            # Divide the component templates into existing and refurbishment components using the naming convention
            if 'Sanierung' in template_name:
                refurb_templates.append(element_dict)
            else:
                stock_templates.append(element_dict)

    # Allocation of the existing components to the matching refurbishment alternatives using the naming convention.
    # Sort the IDs to each other
    for i in stock_templates:
        for x in refurb_templates:
            if x["template_name"] == i["template_name"] + ' Sanierung':
                refurb_alternatives[i["UUID"]] = x["UUID"]
            else:
                continue

    stock_templates[:] = [d for d in stock_templates if d.get('UUID') in refurb_alternatives.keys()]

    # Saving the data as JSON files for further use in the tool
    save_component_json(refurb_alternatives, "refurb_alternatives")
    save_component_json(refurb_templates, "refurb_templates")
    save_component_json(stock_templates, "stock_templates")
    save_component_json(templates, "templates")
    templates_file: list[dict] = load_component_json("templates")
    # Save csv file
    save_elca_csv(templates, 'templates')

    print('Alle in dem Account eLCArefurb hinterlegten Bauteilvorlagen wurden ausgelesen! Bestandsbauteile wurden Sanierungsalternativen zugeteilt!')