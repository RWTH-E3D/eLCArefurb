import pandas
import re
import pandas as pd
import plotly.express as px
from pathlib import Path
from os import path
from glob import glob
import numpy as np
from helpers import reorder_dataframe, create_four_grouped_table, create_grouped_bar_chart, create_stacked_bar_chart, \
    create_report_data_dirs


def interpret_lca():
    """

    This function is used for phase 4 of the LCA, the interpretation. The data from the
    impact assessment phase is read in (ArchetypnameWirkungsanalyse.csv and Lebenszyklusmodule.csv)
    and processed to create visualisations on the identification of pollution hotspots, the
    comparison of refurbishment scenarios, and the temporal distribution.
    The tables read in are processed further as Pandas data frames. The processing of the data
    frames is then based on the necessary format for the creation of graphical representations
    with the Python library plotly.
    Input:
    1)  In "calculate_lcia", for each archetype, a table is compiled on different GWP estimates. There is
        one column for each renovation scenario. The global warming potential on a
        neighbourhood scale (scaled to the corresponding number of buildings), for
        a single building, module B6, construction, individual components and
        building materials is given. In addition, the potential savings compared
        to a completely new building are provided. (ArchetypnameWirkungsanalyse)
    2)  In "calculate_lcia", a table showing the allocation of the total GWP to the individual life cycle
        modules (A1-A3, B4, B6, C3, C4, Total, D) depending on the project is created. (Lebenszyklusmodule)

    Output:
    The following visualisations are created and saved as
    PDF files under report_data > life_cycle-interpretation:
    Group A: Identification of pollution hotspots:
        1)  Staggered pie charts for each project (each scenario for each archetype) on the
            percentage distribution of the total global warming potential among the different
            components and the materials they contain. (ArchetypnameSzenarioGWPKonstruktion.pdf)
    Group B: Comparison of refurbishment scenarios
        2)  Bar charts showing the changes in total
            GWP compared to the existing stock for the different refurbishment scenarios.
            The graphs are produced and are also available
            with changes in kg CO2-Äqv. and percentages.
            (BarChartVeränderungendesGWPBestandvsSanierung.pdf)
        3)  Grouped bar chart for the comparison of the total GWP caused by the building
            operation (module B6). (BarChartGWPModulB6.pdf)
        4)  Grouped bar chart for the comparison of the total GWP caused by the construction.
            Only the roof, the windows and the exterior walls are taken into account.
            (BarChartGWPKonstruktion.pdf)
        5)  Grouped bar chart for the comparison of the total GWP caused by the external wall.
            (BarChartGWPAußenwand.pdf)
        6)  Grouped bar chart for the comparison of the total GWP caused by the windows.
            (BarChartGWPFenster.pdf)
        7)  Grouped bar chart for the comparison of the total GWP caused by the roof.
            (BarChartGWPDach.pdf)
        8)  Grouped bar chart for the comparison of the total GWP caused by a building.
            External wall, windows, roof and module B6 are taken into account.
            (BarChartGesamtesGWPproGebäudeB6AußenwandFensterDach.pdf)
        9) Grouped bar chart for the comparison of the possible savings in total GWP
            compared to a completely new building.
            (BarChartErsparnisgegenübereinemkomplettenNeubau.pdf)
        10) Tables are prepared with the information on the changes in GWP. (Veränderungen)
    Group C: Temporal distribution of the pollution
        11) Temporal distribution: Grouped and stacked bar chart showing the distribution of
            total GWP across the different life cycle modules for each project.
            (BarChartGWPVerteilungLebenszyklusModule.pdf)

"""
    # Create report data folders if they don't exist already
    create_report_data_dirs()

    # List of all csv files from life cycle impact assessment
    def find_ext(dr, ext):
        return glob(path.join(dr, "*.{}".format(ext)))

    lcia_csv = find_ext(Path("report_data/life_cycle_impact"), "csv")
    # Drop the "modules" files
    approved = ['Wirkungsanalyse']
    lcia_csv[:] = [arch for arch in lcia_csv if any(sub in arch for sub in approved)]
    # Iterate through all "Wirkungsanalyse" files
    # There is one "Wirkungsanalyse" file for each archetype
    for arch in lcia_csv:
        # every csv file represents an archetype
        df = pd.read_csv(arch)
        # Columns have names of different refurbishment scenarios or the projects of the archetype
        # Make list of al projects from certain archetype
        arch_projects = df.columns.values.tolist()
        # Retrieve list of all archetypes by dropping substring "Wirkungsanalyse"
        arch_projects.remove('Wirkungsanalyse')
        # Iterate through projects of the archetype
        for project in arch_projects:
            project_name = project
            # Name without spaces is needed for the file that will be saved in the end
            no_spaces_name = project.replace(' ', '')
            # Create multilevel pie chart (sunburst chart) for the identification
            # of GWP hotspots of materials in each project
            # One sunburst chart per project
            # Prepare dataframe for sunburst chart
            # filter the dataframe for the whole archetype by the name of the specific project
            df_project = df[['Wirkungsanalyse', project_name]]
            # Drop all rows not describing a material (Baustoff), as only the
            # materials are interesting for this sunburst chart
            df_project = df_project[df_project.Wirkungsanalyse.str.contains("Baustoff", na=False)]
            # Indicate NaN values
            df_project[project_name].replace('-', np.nan, inplace=True)
            # Drop rows of NaN as project does not contain those materials
            # (e.g. materials of other refurbishment scenarios)
            df_project.dropna(subset=[project_name], inplace=True)
            # Create two columns from "Wirkungsanalyse" column
            # Indicate the associated component to the building material in another column
            df_project[['Bauteil', 'Baustoff']] = df_project['Wirkungsanalyse'].str.split(':', 1, expand=True)
            # Drop column "Wirkungsanalyse" as its now a duplicate of the two new columns
            df_project.drop('Wirkungsanalyse', axis=1, inplace=True)
            # Drop the name "Baustoff"
            df_project['Baustoff'] = df_project['Baustoff'].str.replace('Baustoff ', '', regex=True)
            # Drop the reference to the old substance (Altsubstanz) to embellish the visualisation in the sunburst chart
            df_project['Baustoff'] = df_project['Baustoff'].str.replace(' \[Altsubstanz\]', '', regex=True)
            # The column with the project name now indicates the GWP, therefore the column name is changed to "GWP"
            df_project.rename(columns={project_name: 'GWP'}, inplace=True)
            # To change the string to a float change the punctuation and then round the value
            df_project['GWP'] = df_project['GWP'].str.replace(',', '.')
            df_project = df_project.astype({'GWP': float})
            # Drop materials with GWP = zero
            df_project = df_project[df_project['GWP'] != 0.00000]
            # Reorder the pandas dataframe according to the required order fo the plotly multilevel pie chart
            df_project = reorder_dataframe(df_project, [1, 2, 0])

            # Insert line breaks in the names of the components or materials to enhance the visualisation
            # Line break after 2 words
            def split_string_in_series(input_series: pandas.Series,
                                       after_n_words: int = 2) -> pandas.Series:
                # Iterate through the cell values
                for i_, input_str in enumerate(input_series.values):
                    # Split the cell values into single words
                    string_splittet = input_str.split()
                    # Count the words in the cell value
                    words = len(string_splittet)
                    # Set result parameter that is to be updated
                    result = ""
                    # Set k parameter
                    k = 0
                    # Insert a line break after k words
                    while k < words:
                        result = result + string_splittet[k] + " "
                        if k % after_n_words == 0:
                            result = result + "<br>"
                        k += 1
                    input_series.values[i_] = result
                return input_series

            # Create sunburst chart with plotly and use the function split_string_in_series for cleaner presentation
            fig = px.sunburst(
                data_frame=df_project,
                # inner level of the multilevel pie chart represents the component (wall, window or roof)
                # and the outer level represents the materials
                path=['Bauteil', 'Baustoff'],
                # Use function above here to obtain a cleaner visualisation of the materials in the chart
                labels=split_string_in_series(df_project['Baustoff']),
                # Section of the pie chart is determined by the amount of GWP
                values='GWP',
                # Sunburst chart section should have the name of the material
                names='Baustoff',
                # PDF file should hava a title
                title=f'{project_name} Gebäudekonstruktion GWP<sub>total</sub>',
                # Determine height of the picture
                height=1000,
                # ggplot2 is the plotly template for a white background with scale lines
                template='ggplot2',
                # Colours should follow a blue colour scheme
                #color_discrete_sequence=px.colors.sequential.Blues_r
            )
            # Horizontal alignment of the text for better readability
            # Show material name and percentage of GWP in the pie chart section
            fig.update_traces(insidetextorientation='horizontal', textinfo='label+percent entry')
            # Set font
            fig.update_layout(uniformtext=dict(minsize=10, mode='show'), font_family="Serif", font_color="black")
            # Save image as PDF for further data processing
            fig.write_image(
                f'report_data\\life_cycle_interpretation\\material_pie_charts\\{no_spaces_name}GWPKonstruktion.pdf',
                engine='kaleido', height=500)
    print('Interpretation: Mehrstufige Kreisdiagramme zu GWP der Baustoffe und Bauteile wurden erstellt!')

    # Processing of the data frame for the comparison of the GWP for other
    # rows of "Wirkungsanalyse.csv" in grouped bar charts
    arch_names = []
    # List of frames - every archetype has a frame consisting of "Wirkungsanalyse.csv"
    compare_frames = []
    for arch in lcia_csv:
        # Read the CSV data
        df_compare = pd.read_csv(arch)
        # Drop material columns as they were already assessed above (sunburst charts)
        df_compare = df_compare[~df_compare.Wirkungsanalyse.str.contains("Baustoff", na=False)]
        # As sun protectors are considered as own component and not as part of the windows they will be dropped
        # Only components window, roof and outer walls should be compared
        df_compare = df_compare[~df_compare.Wirkungsanalyse.str.contains("Sonnenschutz", na=False)]
        # Indicate the archetype names
        data_name = arch.replace('report_data\\life_cycle_impact\\', '')
        arch_name = data_name.replace('Wirkungsanalyse.csv', '')
        # Insert spaces before capital letters (redo no spaces name)
        arch_name = re.sub(r"(\w)([A-Z])", r"\1 \2", arch_name)
        # Append to list of archetype names
        arch_names.append(arch_name)
        # Transpose the dataframe
        df_compare = df_compare.transpose()
        # Create new column as the archetype names are now the index
        df_compare['Projekt'] = df_compare.index
        # Drop index of names
        df_compare.reset_index(drop=True, inplace=True)
        # Set the first row as header
        new_header = df_compare.iloc[0]
        # Take the data less the header row
        df_compare = df_compare[1:]
        df_compare.columns = new_header
        # Split "Projekt" column in two columns indicating the archetype name and the refurbishment scenario
        df_compare[['Archetyp', 'Variante']] = df_compare['Wirkungsanalyse'].str.rsplit(' ', 1, expand=True)
        # Drop the "Wirkungsanalyse" column as it is now a duplicate
        df_compare.drop('Wirkungsanalyse', axis=1, inplace=True)
        # Reorder the dataframe - archetype as first and variant as second column
        first_column = df_compare.pop('Archetyp')
        df_compare.insert(0, 'Archetyp', first_column)
        second_column = df_compare.pop('Variante')
        df_compare.insert(1, 'Variante', second_column)
        # Change the names of the columns for unity between archetypes
        # 8th column always describes outer walls etc.
        mapping = {df_compare.columns[6]: 'Außenwand',
                   df_compare.columns[7]: 'Fenster', df_compare.columns[8]: 'Dach'}
        df_compare.rename(columns=mapping, inplace=True)
        # add to list of frames - every archetype has a frame
        compare_frames.append(df_compare)
    # Concat dataframes from archetypes
    compare_all_df = pd.concat(compare_frames)
    # Indices were taken over from the individual dataframes, so they should be dropped
    compare_all_df.reset_index(drop=True, inplace=True)
    # Change datatype of the GWP columns to float for further processing
    float_cols = ['GWP pro Gebäude', 'Modul B6', 'Konstruktion (KGR 300)',
                  'Ersparnis Bestand vs. Neubau', 'Außenwand', 'Fenster', 'Dach']
    compare_all_df[float_cols] = compare_all_df[float_cols].replace(',', '.', regex=True)
    compare_all_df = compare_all_df.astype(
        {'GWP pro Gebäude': float, 'Modul B6': float,
         'Konstruktion (KGR 300)': float, 'Ersparnis Bestand vs. Neubau': float, 'Außenwand': float, 'Fenster': float,
         'Dach': float})
    # Round GWP to 3 decimals
    compare_all_df = compare_all_df.round(decimals=3)

    # Create several bar charts with dataframe
    # Drop all irrelevant columns of the dataframe

    # Gesamtes GWP pro Gebäude
    create_grouped_bar_chart(compare_all_df[["Archetyp", "Variante", "GWP pro Gebäude"]],
                             'Gesamtes GWP<sub>total</sub> pro Gebäude (B6, Außenwand, Fenster, Dach)',
                             'GWP<sub>total</sub> in kg CO<sub>2</sub>-Äqv./m<sup>2</sup><sub>NGF</sub>a')

    # GWP Modul B6
    create_grouped_bar_chart(compare_all_df[["Archetyp", "Variante", "Modul B6"]], 'GWP<sub>total</sub> Modul B6',
                             'GWP<sub>total</sub> in kg CO<sub>2</sub>-Äqv./m<sup>2</sup><sub>NGF</sub>a')
    # GWP Konstruktion
    df_gwp_constr = compare_all_df.drop(
        columns=['GWP pro Gebäude', 'Modul B6', 'Ersparnis Bestand vs. Neubau',
                 'Außenwand', 'Fenster', 'Dach'])
    create_grouped_bar_chart(compare_all_df[["Archetyp", "Variante", "Konstruktion (KGR 300)"]],
                             'GWP<sub>total</sub> Konstruktion',
                             'GWP<sub>total</sub> in kg CO<sub>2</sub>-Äqv./m<sup>2</sup><sub>NGF</sub>a')
    # GWP Bestand vs. Neubau
    create_grouped_bar_chart(compare_all_df[["Archetyp", "Variante", "Ersparnis Bestand vs. Neubau"]],
                             'GWP<sub>total</sub> Ersparnis gegenüber einem kompletten Neubau',
                             'GWP<sub>total</sub> in kg CO<sub>2</sub>-Äqv./m<sup>2</sup><sub>NGF</sub>a (positive Werte entsprechen GWP-Einsparung durch Bestandsnutzung)')  # "$V_O^{**}$"
    # GWP Außenwand
    create_grouped_bar_chart(compare_all_df[["Archetyp", "Variante", "Außenwand"]], 'GWP<sub>total</sub> Außenwand',
                             'GWP<sub>total</sub> in kg CO<sub>2</sub>-Äqv./m<sup>2</sup><sub>NGF</sub>a')
    # GWP Fenster
    create_grouped_bar_chart(compare_all_df[["Archetyp", "Variante", "Fenster"]], 'GWP<sub>total</sub> Fenster',
                             'GWP<sub>total</sub> in kg CO<sub>2</sub>-Äqv./m<sup>2</sup><sub>NGF</sub>a')
    # GWP Dach
    create_grouped_bar_chart(compare_all_df[["Archetyp", "Variante", "Dach"]], 'GWP<sub>total</sub> Dach',
                             'GWP<sub>total</sub> in kg CO<sub>2</sub>-Äqv./m<sup>2</sup><sub>NGF</sub>a')
    # Compare between several columns of original dataframe

    # Changes im GWP through refurbishment on building level
    df_gwp_changes = compare_all_df[["Archetyp", "Variante", "GWP pro Gebäude"]]
    # Process dataframe to indicate stock GWP for every column
    # Create new dataframe containing information on stock GWP to merge with original frame
    df_stock_gwp = compare_all_df[["Archetyp", "Variante", "GWP pro Gebäude"]]
    df_stock_gwp = df_stock_gwp[df_stock_gwp.Variante == 'Bestand']
    df_stock_gwp.rename(columns={'GWP pro Gebäude': 'Bestand GWP'}, inplace=True)
    df_stock_gwp.drop(columns={'Variante'}, inplace=True)
    # Merge the two dataframes
    df_gwp_changes = df_gwp_changes.merge(df_stock_gwp, on='Archetyp', how='left')
    # Drop all rows of stock
    df_gwp_changes = df_gwp_changes[df_gwp_changes.Variante != 'Bestand']
    # Add new rows with changes to stock in %
    df_gwp_changes['Veränderungen zu Bestand in %'] = ((df_gwp_changes['GWP pro Gebäude'] / df_gwp_changes[
        'Bestand GWP']) - 1.0) * 100.0
    # Add new rows with changes to stock in kg CO2-Äq.
    df_gwp_changes['Veränderungen zu Bestand in kg CO<sub>2</sub>-Äqv./m<sup>2</sup><sub>NGF</sub>a'] = df_gwp_changes[
                                                                                                            'GWP pro Gebäude'] - \
                                                                                                        df_gwp_changes[
                                                                                                            'Bestand GWP']
    # Round values for enhanced visualisation
    df_gwp_changes = df_gwp_changes.round(decimals=3)
    # Save table as csv for futher usage
    # Create table
    create_four_grouped_table(df_gwp_changes, 'GWP<sub>total</sub> Veränderungen zu Bestand',
                              'report_data\\life_cycle_interpretation\\variants\\Veränderungen', 600)
    # Drop columns for bar chart processing of percentages
    df_gwp_changes_percentage = df_gwp_changes.drop(columns={'GWP pro Gebäude', 'Bestand GWP',
                                                             'Veränderungen zu Bestand in kg CO<sub>2</sub>-Äqv./m<sup>2</sup><sub>NGF</sub>a'})
    # Create bar chart
    create_grouped_bar_chart(df_gwp_changes_percentage,
                             'Prozentuale Veränderungen des GWP<sub>total</sub> Bestand vs. Sanierung',
                             'Veränderungen in % (negative Werte entsprechen GWP-Einsparung)')
    # Drop columns for bar chart processing of kg CO2-Äq.
    df_gwp_changes_co2 = df_gwp_changes.drop(
        columns={'GWP pro Gebäude', 'Bestand GWP', 'Veränderungen zu Bestand in %'})
    # Create bar chart
    create_grouped_bar_chart(df_gwp_changes_co2, 'Veränderungen des GWP<sub>total</sub> Bestand vs. Sanierung',
                             'Veränderungen in kg CO<sub>2</sub>-Äqv./m<sup>2</sup><sub>NGF</sub>a (negative Werte entsprechen GWP-Einsparung)')

    # Changes im GWP through refurbishment on quarter level

    print('Interpretation: Balkendiagramme zum Vergleich der Archetypen und Sanierungsvarianten wurden erstellt!')

    # Visualise the modules in a stacked bar chart
    # Read the modules csv
    # Aufteilung des GWP auf verschiedene Module
    df_compare_modules = pd.read_csv('report_data/life_cycle_impact/Lebenszyklusmodule.csv')
    # Process the dataframe from the csv for stacked bar chart creation
    df_compare_modules = df_compare_modules.transpose()
    # Grab the first row for the header
    new_header = df_compare_modules.iloc[0]
    # Take the data less the header row
    df_compare_modules = df_compare_modules[1:]
    df_compare_modules.columns = new_header
    # Set index as column module
    df_compare_modules['Modul'] = df_compare_modules.index
    # Drop index
    df_compare_modules.reset_index(drop=True, inplace=True)
    # Change order of columns
    first_column_modules = df_compare_modules.pop('Modul')
    df_compare_modules.insert(0, 'Modul', first_column_modules)
    # "Unpivot" the dataframe
    # One or more columns are identifier variables (id_vars), while all other columns,
    # considered measured variables (value_vars)
    df_compare_modules = df_compare_modules.melt(id_vars=['Modul'], var_name='Projektname', value_name='GWP')
    # Drop module "D" as it is not part of the LCA (according to DIN EN 15804 + A1)
    df_compare_modules = df_compare_modules[df_compare_modules.Modul != 'D: Recyclingpotenzial']
    # Drop teh rows with overall GWP
    df_compare_modules = df_compare_modules[df_compare_modules.Modul != 'Gesamt']
    # Change datatypes to float and round
    df_compare_modules["GWP"] = df_compare_modules["GWP"].str.replace(",", ".")
    df_compare_modules = df_compare_modules.astype({'GWP': float})
    df_compare_modules = df_compare_modules.round(decimals=1)
    # Create columns for archetype and refurbishment variant
    df_compare_modules[['Archetyp', 'Variante']] = df_compare_modules['Projektname'].str.rsplit(' ', 1, expand=True)
    df_compare_modules.drop('Projektname', axis=1, inplace=True)
    # Change order of columns
    df_compare_modules = reorder_dataframe(df_compare_modules, [2, 3, 0, 1])
    # Create bar chart
    create_stacked_bar_chart(df_compare_modules, 'GWP<sub>total</sub> Verteilung Lebenszyklus Module',
                             'GWP<sub>total</sub> in kg CO<sub>2</sub>-Äqv./m<sup>2</sup><sub>NGF</sub>a')
    print('Interpretation: Gestapeltes Balkendiagramm zur Aufteilung des GWP auf verschiedene Module wurde erstellt!')
