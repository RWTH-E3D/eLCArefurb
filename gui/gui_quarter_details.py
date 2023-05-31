from __future__ import annotations
import PyQt5.QtWidgets as qtw
import PyQt5.QtGui as qtg
from helpers import load_component_json, save_component_json


def create_quarter_gui():
    """

    This function creates a graphical user interface where a user can enter information
    on stock building archetypes of a quarter. For this purpose, the JSON files stock_components
    and energy_sources created in the script components_collection are read in, as only
    these pre-read templates can be selected and eco-balanced. These are the basis for the
    selection boxes. Moreover, the files refurb_templates.json and refurb_alternatives.json are read in
    to show the U-Values of the stock component and the refurbished component.
    Up to 8 archetypes can be defined. A JSON file "archetypes" is created
    from the user's entries. This consists of a list of dictionaries. Each dictionary
    describes an archetype of the quarter.

    Input:
    1) energy_sources.json: Dictionary with names of energy sources as keys and corresponding IDs as values
    2) stock_templates.json: List of dictionaries where every list item describes a stock component
                            and every item consists of a dictionary with information on the component
    3) refurb_templates: list of dictionaries where every list item describes a refurbishment component
                        and every item consists of a dictionary with information on the component
    4) refurb_alternatives: dictionary with IDs of stock templates as keys and IDs of corresponding refurbishment components as values
    5) GUI user entry: Information on archetypes

    Output:
    1) archetypes.json: List of dictionaries, where each dictionary describes an archetype of the quarter.

    """
    # The stock_templates.json can be selected through the dropdown box
    stock_templates: list[dict] = load_component_json("stock_templates")
    # refurb_templates and refurb_alternatives will be used to display the U-Value
    # of the stock components and the refurbished components
    refurb_templates: list[dict] = load_component_json("refurb_templates")
    refurb_alternatives: list[dict] = load_component_json("refurb_alternatives")

    # The energy_sources.json can be selected through the dropdown box
    energy_sources: dict[str, str] = load_component_json("energy_sources")
    # These construction age classes are defined by TABULA building typology and will help to define the
    # energy_savings_potential
    construction_age_classes: list = ['bis 1859', '1860-1918', '1919-1948', '1949-1957', '1958-1968', '1969-1978',
                                      '1979-1983', '1984-1994', '1995-2001', '2002-2009', '2010-2015', 'ab 2016']
    # create a list where each list entry describes one archetype
    archetypes = []

    # Create graphic user interface (GUI) using PyQt5
    class MainWindow(qtw.QWidget):
        def __init__(self):
            super().__init__()
            # Title of the GUI
            # Title of the GUI is name of the tool
            self.setWindowTitle("eLCArefurb")
            # Build Form
            form_layout = qtw.QFormLayout()
            self.setLayout(form_layout)
            # Add Widgets
            # Add description
            label_1 = qtw.QLabel("Informationen zum Gebäude-Archetyp")
            # Define description font
            label_1.setFont(qtg.QFont("Helvetica", 12))

            # Variables are defined, which are assigned to the user inputs in the next step
            # Name of the Archetype
            archetype_name = qtw.QLineEdit(self)
            # Number of buildings of the archetype in the neighborhood
            no_quarter = qtw.QLineEdit(self)
            # Gross ground space (BGF) according to DIN 276
            bgf = qtw.QLineEdit(self)
            # Net ground space (NGF) according to DIN 276
            ngf = qtw.QLineEdit(self)
            # NGF according to the EnEV becomes important for the input of the final energy balance.
            ngf_enev = qtw.QLineEdit(self)
            # Indication of final energy for heating
            final_energy_heat = qtw.QLineEdit(self)
            # Specification of final energy for hot water
            final_energy_water = qtw.QLineEdit(self)
            # Specification of the masses for the outer walls
            quantity_outer_walls = qtw.QLineEdit(self)
            # Specification of the masses for the roof
            quantity_roof = qtw.QLineEdit(self)
            # Specification of the masses for the windows
            quantity_windows = qtw.QLineEdit(self)

            # Rows are added to the layout. In each row there is a new query on variables defined above
            # Line contains the label "Informationen zum Gebäude-Archetyp"
            form_layout.addRow(label_1)
            # Line: Name of the Archetype
            # The name of the archetype cannot contain spaces and numbers at the same time,
            # because in the life cycle costing phase (calculate_lcc) the CSV files created in
            # the life cycle inventory phase are read in and these have the name of the archetype
            # without spaces. If there is a space between words, this will be processed,
            # but numbers are only processed without spaces so far.
            # Also, for this reason, names that use capital letters in the middle of a word or
            # special characters cannot be used.
            form_layout.addRow("Name des Archetyps:", archetype_name)
            # Add description on name convention
            label_name = qtw.QLabel("Namenskonvention: keine Leerzeichen und Nummern gleichzeitig, Großbuchstaben nur bei Beginn eines neuen Wortes am Anfang oder nach Leerzeichen, keine Sonderzeichen")
            # Define description font
            label_name.setFont(qtg.QFont("Helvetica", 8))
            form_layout.addRow(label_name)
            # Line: Number of buildings of the archetype in the neighborhood
            form_layout.addRow("Anzahl der Gebäude des Archetyps im Quartier:", no_quarter)
            # Line: Gross ground space (BGF) according to DIN 276
            form_layout.addRow("BGF nach DIN 276:", bgf)
            # Line: Net ground space (NGF) according to DIN 276
            form_layout.addRow("NGF nach DIN 276:", ngf)
            # Line: NGF according to the EnEV
            form_layout.addRow("NGF nach der EnEV:", ngf_enev)
            # Line: Indication of final energy for heating
            form_layout.addRow("Endenergie für Heizung in kWh/(m²a):", final_energy_heat)
            # Line: Specification of final energy for hot water
            form_layout.addRow("Endenergie für Warmwasser in kWh/(m²a):", final_energy_water)
            # Line: Specification of the masses for the outer walls
            form_layout.addRow("Fläche der Außenwände in m²:", quantity_outer_walls)
            # Line: Specification of the masses for the windows
            form_layout.addRow("Fläche des Dachs in m²:", quantity_roof)
            # Line: Specification of the masses for the roof
            form_layout.addRow("Anzahl der Fenster:", quantity_windows)

            # Create a Combo box (selection box) for outer wall components
            wall_combo_box = qtw.QComboBox(self)
            # Add items to the Combo Box
            for template in stock_templates:
                # wall combo box only contains walls
                # walls have the cost group 330
                if template['KGR_DIN_276'] == "330":
                    # Add the name as currentText parameter of combo box and ID as currentData parameter
                    wall_combo_box.addItem(template['Vorlage'], template['UUID'])
            # Create a widget from the combo box
            self.layout().addWidget(wall_combo_box)
            # Line: Set wall combo box and give information on what to choose in this selection box
            form_layout.addRow("Auswahl Außenwand KGR 330", wall_combo_box)
            # Show description  and U-Value of the currently selected component
            # Show the U-Value of the corresponding refurbished component

            # Iterate through all stock templates to find the fitting name (currentText parameter of combo box)
            for template in stock_templates:
                if template['Vorlage'] == wall_combo_box.currentText():
                    # Choose the right U-Value from dictionary of stock components
                    wall_u_value = template['U-Wert']
                    # Choose the right description from dictionary of stock components
                    wall_description = template['Beschreibung']
                    # Choose the right U-Value of the corresponding refurbished component
                    # Get the ID of the stock component
                    wall_id = template['UUID']
                    # search for ID of corresponding refurbished component
                    for key, value in refurb_alternatives.items():
                        if key == wall_id:
                            for refurb_template in refurb_templates:
                                # Get the U-Value of the refurbished component with the ID of the refurbished component
                                if value == refurb_template['UUID']:
                                    wall_u_value_refurb = refurb_template['U-Wert']
                                    # If the corresponding U-Value of the refurbished component was found,
                                    # break the loop
                                    break
            # Add label for U-Value of stock component
            u_value_label_wall = qtw.QLabel(wall_u_value)
            # Add label fo U-Value of refurbished component
            u_value_label_wall_refurb = qtw.QLabel(wall_u_value_refurb)
            # Add label for the description of the stock component
            description_label_wall = qtw.QLabel(wall_description)
            # Lines: Add rows for U-Values
            form_layout.addRow("Bestand U-Wert in W/(m²K) Außenwand", u_value_label_wall)
            form_layout.addRow("Sanierung U-Wert in W/(m²K) Außenwand", u_value_label_wall_refurb)

            # Line: Show description
            form_layout.addRow("Beschreibung Außenwand", description_label_wall)

            #  Change the description and U-Values if the selection of the combo box is changed
            # Define function to change the description and U-Values according to the currently selected wall component
            def change_description_uvalue(ComboBox, description_label, u_value_label, u_value_label_refurb):
                for template in stock_templates:
                    # Choose the right description from dictionary of stock components
                    # Iterate through all stock templates to find the fitting name (currentText parameter of combo box)
                    if template['Vorlage'] == ComboBox.currentText():
                        # Show U-Value of template
                        u_value = template['U-Wert']
                        # Show the new description unterneath the wall combo box
                        description = template['Beschreibung']
                        # Get the U-Value of the refurbished component (see comments above)
                        template_id = template['UUID']
                        for key, value in refurb_alternatives.items():
                            if key == template_id:
                                for refurb_template in refurb_templates:
                                    if value == refurb_template['UUID']:
                                        u_value_refurb = refurb_template['U-Wert']
                                        break
                # Change the labels according to current selection of the combo box
                u_value_label.setText(u_value)
                u_value_label_refurb.setText(u_value_refurb)
                description_label.setText(description)

            # Execute function to change the description and U-Values
            wall_combo_box.currentIndexChanged.connect(
                lambda: change_description_uvalue(wall_combo_box, description_label_wall, u_value_label_wall,
                                                  u_value_label_wall_refurb))

            # Create a Combo box for windows
            window_combo_box = qtw.QComboBox(self)
            # Add items to the Combo Box
            for template in stock_templates:
                # window combo box only contains windows
                # windows have the cost group 334
                if template['KGR_DIN_276'] == "334":
                    # Add the name as currentText parameter of combo box and ID as currentData parameter
                    window_combo_box.addItem(template['Vorlage'], template['UUID'])
            # Create a widget from the combo box
            self.layout().addWidget(window_combo_box)
            # Line: Set window combo box and give information on what to choose in this selection box
            form_layout.addRow("Auswahl Fenster KGR 334", window_combo_box)
            # See wall templates for comments on the code
            # Procedure is analogous to the wall components
            for template in stock_templates:
                if template['Vorlage'] == window_combo_box.currentText():
                    window_u_value = template['U-Wert']
                    window_description = template['Beschreibung']
                    window_id = template['UUID']
                    for key, value in refurb_alternatives.items():
                        if key == window_id:
                            for refurb_template in refurb_templates:
                                if value == refurb_template['UUID']:
                                    window_u_value_refurb = refurb_template['U-Wert']
                                    break
            u_value_label_window = qtw.QLabel(window_u_value)
            u_value_label_window_refurb = qtw.QLabel(window_u_value_refurb)
            description_label_window = qtw.QLabel(window_description)
            form_layout.addRow("Bestand U-Wert in W/(m²K) Fenster", u_value_label_window)
            form_layout.addRow("Sanierung U-Wert in W/(m²K) Fenster", u_value_label_window_refurb)
            form_layout.addRow("Beschreibung Fenster", description_label_window)
            window_combo_box.currentIndexChanged.connect(
                lambda: change_description_uvalue(window_combo_box, description_label_window, u_value_label_window,
                                                  u_value_label_window_refurb))

            # Create a combo box for roofs
            roof_combo_box = qtw.QComboBox(self)
            # Add items to the Combo Box
            for template in stock_templates:
                # roof combo box only contains roofs
                # roods have the cost group 360
                if template['KGR_DIN_276'] == "360":
                    # Add the name as currentText parameter of combo box and ID as currentData parameter
                    roof_combo_box.addItem(template['Vorlage'], template['UUID'])
            # Create a widget from the combo box
            self.layout().addWidget(roof_combo_box)
            # Line: Set roof combo box and give information on what to choose in this selection box
            form_layout.addRow("Auswahl Dach KGR 360", roof_combo_box)
            # Procedure is analogous to the wall components
            for template in stock_templates:
                if template['Vorlage'] == roof_combo_box.currentText():
                    roof_u_value = template['U-Wert']
                    roof_description = template['Beschreibung']
                    roof_id = template['UUID']
                    for key, value in refurb_alternatives.items():
                        if key == roof_id:
                            for refurb_template in refurb_templates:
                                if value == refurb_template['UUID']:
                                    roof_u_value_refurb = refurb_template['U-Wert']
                                    break
            u_value_label_roof = qtw.QLabel(roof_u_value)
            u_value_label_roof_refurb = qtw.QLabel(roof_u_value_refurb)
            description_label_roof = qtw.QLabel(roof_description)
            form_layout.addRow("Bestand U-Wert in W/(m²K) Dach", u_value_label_roof)
            form_layout.addRow("Sanierung U-Wert in W/(m²K) Dch", u_value_label_roof_refurb)
            form_layout.addRow("Beschreibung Dach", description_label_roof)
            roof_combo_box.currentIndexChanged.connect(
                lambda: change_description_uvalue(roof_combo_box, description_label_roof, u_value_label_roof,
                                                  u_value_label_roof_refurb))

            # Create a Combo box for energy sources
            energy_carrier_combo_box = qtw.QComboBox(self)
            for key, value in energy_sources.items():
                # Add the name (key) as currentText parameter of combo box and ID (value) as currentData parameter
                energy_carrier_combo_box.addItem(key, value)
                # Create a widget from the combo box
            self.layout().addWidget(energy_carrier_combo_box)
            # Line: Set energy carrier combo box and give information on what to choose in this selection box
            form_layout.addRow("Auswahl Wärmeversorgungsanlage", energy_carrier_combo_box)

            # Create a Combo box for building age class
            building_age_combo_box = qtw.QComboBox(self)
            # Add the list of building age classes to the combo box
            building_age_combo_box.addItems(construction_age_classes)
            # Create a widget from the combo box
            self.layout().addWidget(building_age_combo_box)
            # Line: Set buidling age class combo box and give information on what to choose in this selection box
            form_layout.addRow("Auswahl Baualtersklasse", building_age_combo_box)

            # Buttons to either define another archetype or to complete the archetype specification process
            # Line: Next archetype
            form_layout.addRow(qtw.QPushButton(
                "Einen weiteren Archetypen hinzufügen! Es können maximal 8 Archetypen klassifiziert werden.",
                clicked=lambda: press_it_next()))
            # Line: Done
            form_layout.addRow(qtw.QPushButton("Keine weiteren Archetypen hinzufügen! Quartierdaten anzeigen!",
                                               clicked=lambda: press_it_done()))

            # Show the app
            self.show()

            # When button 1 is pressed, the data format of the input should be checked first (test_data_format).
            # If the data format is correct, the input for the archetype should be stored in a dictionary (read_values)
            # and then the GUI should be cleared so that a new input for another archetype can be made.
            def press_it_next():
                test_data_format()
                if test_data_format() == 'Data formats correct':
                    read_values()
                    clear_values()
                else:
                    clear_values()

            # If button 2 is pressed, then first the data format of the input should be checked (test_data_format).
            # If the data format is correct, then the input for the archetypes should be stored in a dictionary
            # (read_values) and then the input for the different archetypes should be displayed again before
            # eLCArefurb goes on.
            def press_it_done():
                test_data_format()
                if test_data_format() == 'Data formats correct':
                    read_values()
                    alert = qtw.QMessageBox()
                    alert.setWindowTitle("eLCArefurb")
                    alert.setText(f'Sie haben folgende Gebäude-Archetypen definiert: {archetypes}')
                    alert.exec_()
                    self.close()
                else:
                    clear_values()

            # All numbers in the entry boxes should be saved in a float or int format and not as strings to facilitate
            # further data processing
            def parse_number(input_str: str,
                             input_type: str,
                             default_value: float | int = None) -> float:
                assert input_type in ["int", "float"]
                try:
                    if input_type == "float":
                        # for the conversion from string to float the german comma must be replaced by a dot
                        return float(input_str.replace(",", "."))
                    elif input_type == "int":
                        return int(input_str)
                except ValueError:
                    if default_value:
                        return default_value
                    else:
                        # If the string of the number cannot be converted to an integer or a float, then there is
                        # an error and the data input must be changed, then a warning box should pop up.
                        alert = qtw.QMessageBox()
                        alert.setWindowTitle(f"Falscher Input!")
                        alert.setText(
                            f"Eingabe {input_str} konnte nicht als {input_type} identifiziert werden. Bitte geben Sie die Daten zum letzten Archetyp erneut ein")
                        alert.exec_()
                        alert.close()
                        return 'Error'

            # Function to test the data format
            # If all entries have a correct dataformat the function returns the message 'Data format correct'
            # If the one entry has a wrong data format the function returns the message 'Data format incorrect'
            # Current Text describes the text that is shown in the combo box or the form entry
            # Current data is used for the combo boxes to save the IDs connected to the selected names of
            # the components or energy carriers
            def test_data_format():
                if parse_number(no_quarter.text(), "int") == 'Error':
                    return 'Data formats incorrect'
                elif parse_number(bgf.text(), "float") == 'Error':
                    return 'Data formats incorrect'
                elif parse_number(ngf.text(), "float") == 'Error':
                    return 'Data formats incorrect'
                elif parse_number(ngf_enev.text(), "float") == 'Error':
                    return 'Data formats incorrect'
                elif parse_number(final_energy_heat.text(), "float") == 'Error':
                    return 'Data formats incorrect'
                elif parse_number(final_energy_water.text(), "float") == 'Error':
                    return 'Data formats incorrect'
                elif parse_number(quantity_outer_walls.text(), "float") == 'Error':
                    return 'Data formats incorrect'
                elif parse_number(quantity_roof.text(), "float") == 'Error':
                    return 'Data formats incorrect'
                elif parse_number(quantity_windows.text(), "int") == 'Error':
                    return 'Data formats incorrect'
                elif parse_number(wall_combo_box.currentData(), "int") == 'Error':
                    return 'Data formats incorrect'
                elif parse_number(window_combo_box.currentData(), "int") == 'Error':
                    return 'Data formats incorrect'
                elif parse_number(roof_combo_box.currentData(), "int") == 'Error':
                    return 'Data formats incorrect'
                elif parse_number(energy_carrier_combo_box.currentData(), "int") == 'Error':
                    return 'Data formats incorrect'
                else:
                    return 'Data formats correct'

            # This function stores all inputs in a list of dictionaries where every list item defines one archetype.
            def read_values():
                archetypes.append({
                    # Delete white space at the end of the quarter name if it exists
                    # White spaces at the end of quarter names are typos and lead to an error
                    'Archetyp Name': (archetype_name.text()).rstrip(),
                    'Anzahl im Quartier': parse_number(no_quarter.text(), "int"),
                    'BGF DIN 276': parse_number(bgf.text(), "float"),
                    'NGF DIN 276': parse_number(ngf.text(), "float"),
                    'NGF nach EnEV': parse_number(ngf_enev.text(), "float"),
                    'Energie Heizung': parse_number(final_energy_heat.text(), "float"),
                    'Energie WW': parse_number(final_energy_water.text(), "float"),
                    'Masse Außenwände': parse_number(quantity_outer_walls.text(), "float"),
                    'Masse Dächer': parse_number(quantity_roof.text(), "float"),
                    'Anzahl Fenster': parse_number(quantity_windows.text(), "int"),
                    'Außenwand Vorlage': wall_combo_box.currentText(),
                    'Fenster Vorlage': window_combo_box.currentText(),
                    'Dach Vorlage': roof_combo_box.currentText(),
                    'WVA/Energieträger Vorlage': energy_carrier_combo_box.currentText(),
                    'Außenwand ID': parse_number(wall_combo_box.currentData(), "int"),
                    'Fenster ID': parse_number(window_combo_box.currentData(), "int"),
                    'Dach ID': parse_number(roof_combo_box.currentData(), "int"),
                    'WVA/Energieträger ID': parse_number(energy_carrier_combo_box.currentData(), "int"),
                    'Baualtersklasse': building_age_combo_box.currentText()
                })

            # This function clears all entry boxes to allow new entries for new archetypes
            # or an improvement of the input in case of input of wrong data types
            def clear_values():
                archetype_name.clear()
                no_quarter.clear()
                bgf.clear()
                ngf.clear()
                ngf_enev.clear()
                final_energy_heat.clear()
                final_energy_water.clear()
                quantity_outer_walls.clear()
                quantity_roof.clear()
                quantity_windows.clear()

    app = qtw.QApplication([])
    mw = MainWindow()
    # Run the App
    app.exec_()

    # Save the list of dictionaries on the archetypes as a JSON file for further usage
    save_component_json(archetypes, "archetypes")
    print('Die angegebenen Informationen zu den Archetypen des Quartiers wurden gespeichert!')
