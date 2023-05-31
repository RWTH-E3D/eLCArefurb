import pandas
import re
import pandas as pd
from pathlib import Path
from math import pow
from helpers import reorder_dataframe, create_four_grouped_table, create_grouped_bar_chart, create_facetted_bar_chart, \
    load_component_json, pandas_convert_decimals, create_report_data_dirs
import numpy as np


def analyse_life_cycle_costs():
    '''
    This function reads the output data from the life cycle inventory to calculate the net present value of the energy
    cost savings over 20 years and the costs of the renovation measures. The costs of the renovation measures are
    compared to the energy cost savings.
    Uncertainties in the context of the renovation costs are mapped via a "best", "base" and "worst" case.
    First, the net present value of the energy cost savings over 20 years is calculated. For this purpose, a discount
    rate of 1.5 % and an annual increase in energy costs of 5 % are assumed according to the BNB valuation system
    (BUNDESMINISTERIUM FÜR VERKEHR ; BAU UND STADTENTWICKLUNG: 2.1.1 Gebäudebezogene Kosten im Lebenszyklus.2015).
    In addition, the costs used by the BNB evaluation system for the various energy sources are also used. According to
    this, electricity costs 20 cents/kWh, oil 7 cents/kWh, gas 6 cents/kWh, wood pellet heating 5.7 cents/kWh, district
    heating 7.7 cents/kWh and, according to https://kostencheck.de/hackschnitzelheizung-kosten, woodchip boiler
    heating 3.5 cents/kWh.
    The CSV file "Gebäudebetrieb", which was created by create_lci(), is read in and the values for the final energy
    demand and the net ground space according to the EnEV of the different projects are adopted. Finally, the difference between the
    various refurbishment scenarios and the existing condition is determined.
    To determine the renovation costs, the CSV files AußenwandKosten.csv, DachKosten.csv and FensterKosten.csv are read in.
    Depending on the material, these files contain the costs in the "worst", "base" and "best" case. The costs for roofs and
    exterior walls are given in €/m2 depending on the different insulation materials and for the windows in €/piece depending
    on the frame material.
    Data source for wall and roof refurbishment costs: https://www.co2online.de/modernisieren-und-bauen/daemmung/daemmmassnahmen-uebersicht/
    Data source for window replacement costs: VERBAND FENSTER + FASSADE ; BUNDESVERBAND FLACHGLAS: Mehr Energie sparen mit neuen
    Fenstern: Aktualisierung Mai 2021 der Studie „Im neuen Licht: Energetische Modernisierung von alten Fenstern“. 2, 2021.
    The data contain the costs for both materials and installation. The CSV file for the life cycle
    inventory automatically shows which materials are used for the renovations. The area of the roof and the external wall as
    well as the number of windows are also read from the CSV file for the building components. The costs per m2 are multiplied
    by the mass of the respective building component and thus result in the total renovation costs.
    Both the energy savings and the renovation costs are also scaled up to neighbourhood level by multiplying them by
    the number of buildings of the respective archetype.

    Input:
    1) archetypes.json: List of dictionaries, where each dictionary describes an archetype of the quarter.
    2) Gebäudebetrieb.csv: A table for the operation of the buildings with the final energy demand of
        the different archetypes and scenarios.
    3) NameBaustoffe.csv: For each archetype, a table is created on the masses of the building materials.
    4) AußenwandKosten.csv: Depending on the insulation material, the file contains the costs in the "worst", "base" and "best" case.
    5) DachKosten.csv: Depending on the insulation material, the file contains the costs in the "worst", "base" and "best" case.
    6) FensterKosten.csv: Depending on the frame material, the file contains the costs in the "worst", "base" and "best" case.
    7) EnergieKosten.JSON: Dictionary of energy carriers as keys and costs in cent/kWh as values

    Output:
    1) Bar charts showing the net present value of the energy cost savings over 20 years for the different archetypes and renovation scenarios. (BarChartEnergikostenEinsparungenüber20JahreGebäudeebene)
    2) Bar charts are generated for the refurbishment costs in the "best", "base" and "worst" case. (SanierungskostenXCaseGebäude)
    3) The sum of energy cost savings and refurbishment costs for the "best", "base" and "worst" case is visualised via bar charts. (BarChartVergleichEnergiekosteneinsparungvsSanirungskostenXCaseGebäude)
    4) Tables summarising the life cycle costing are prepared, showing for each variant the net present value of the energy costs,
        the renovation costs in the best, base and worst case and the sum of the two in the best base and worst case. (Kostenanalyse)
    '''
    # Create report data folders if they don't exist already
    create_report_data_dirs()
    # Load archetypes defined by user
    archetypes: list[dict] = load_component_json("archetypes")
    # load data on energy prices calculation
    energy_calc: {dict} = load_component_json("Energy_Calculations", "assessment")
    discount_rate = energy_calc["discount_rate"]
    annual_price_increase = energy_calc["annual_price_increase"]

    def calculate_npv(space: pandas.Series, demand: pandas.Series, price: pandas.Series) -> list[float]:
        npv = []
        # Pandas Dataframe with information on energy demand of different archetypes
        frame = pd.DataFrame({'NGF': space, 'Energiebedarf': demand, 'Preis': price})
        # Calculate energy costs for the whole building and append new column to dataframe
        frame['Basisjahr'] = frame['NGF'] * frame['Energiebedarf'] * frame['Preis']
        # Iterate through pandas Series (column with energy costs of the whole building)
        for _, value in frame['Basisjahr'].items():
            result = 0
            # Assume interest rate of 1.5 % and annual price increase in energy costs 5 % from BNB Bewertungssystem
            # Calculate NPV for a period of 20 years
            for i in range(20):
                result += value * pow(1 + annual_price_increase, i + 1) / pow(1 + discount_rate, i + 1)
            npv.append(result)
        return npv

    # Net Present Value of energy demand
    # Load information on energy demand of archetypes
    df_energy = pd.read_csv('report_data/life_cycle_inventory/Gebäudebetrieb.csv')
    # Change column data types from string to float for further data processing
    float_cols = ['NFA in m²', 'existing building final energy heating in kWh/m²a',
                  'existing building final energy hot water in kWh/m²a', 'Bestand Endenergie in kWh/m²a',
                  'Außenwandsanierung Endenergie in kWh/m²a', 'Dachsanierung Endenergie in kWh/m²a',
                  'Fenstersanierung Endenergie in kWh/m²a', 'Komplettsanierung Endenergie in kWh/m²a']
    # Change comma to point for data type change
    for float_col in float_cols:
        df_energy = pandas_convert_decimals(df_energy, float_col)
    # Dictionary of prices per energy supply system and kWh
    # BNB criteria for the prices assumed for electricity, oil, gas, pellet heating and district heating
    # and https://kostencheck.de/hackschnitzelheizung-kosten for the Woodchip boiler
    energy_prices: {dict} = load_component_json("EnergieKosten", "assessment")
    prices_column = []
    # Pandas Series from energy supply systems
    carriers = df_energy['energy carrier template']
    # Iterate through Pandas series to append prices according to energy supply system
    for index, value in carriers.items():
        supplier = value
        for energy_source, energy_price in energy_prices.items():
            if energy_source in supplier:
                prices_column.append(energy_price)
    # Add price column to energy dataframe
    df_energy['Preis in €/kWh'] = prices_column
    # Define refurbishment scenarios
    refurb_scenarios = ["Außenwandsanierung", "Dachsanierung", "Fenstersanierung", "Komplettsanierung"]
    # Calculate NPV of energy costs fpr the different refurbishment scenarios and the existing scenario
    df_energy[f"Kapitalwert Bestand in €"] = \
        calculate_npv(df_energy['NFA in m²'], df_energy[f"Bestand Endenergie in kWh/m²a"],
                      df_energy['Preis in €/kWh'])
    for refurb_scenario in refurb_scenarios:
        df_energy[f"Kapitalwert {refurb_scenario} in €"] = \
            calculate_npv(df_energy['NFA in m²'], df_energy[f"{refurb_scenario} Endenergie in kWh/m²a"],
                          df_energy['Preis in €/kWh'])
        # Add a column for the difference between the costs in the existing scenario and in the rehabilitation scenario
        df_energy[f'{refurb_scenario} Einsparungen im Vergleich zum Bestandsszenario in €'] = \
            df_energy['Kapitalwert Bestand in €'] - df_energy[f'Kapitalwert {refurb_scenario} in €']
    # Round all values
    df_energy = df_energy.round(decimals=3)
    # Only keep important columns for later visualisation
    savings_names = [f"{refurb_scenario} Einsparungen im Vergleich zum Bestandsszenario in €"
                     for refurb_scenario in refurb_scenarios]
    df_energy = df_energy[['archetype name'] + savings_names]
    # Unpivot the dataframe for later visualisation with plotly
    df_energy = df_energy.melt(id_vars=['archetype name'], value_vars=savings_names,
                               var_name='Sanierungsszenario',
                               value_name='Kapitalwert Energiekosten Einsparungen über 20 Jahre')
    # Dataframe processing for better visualisation
    df_energy['Sanierungsszenario'] = \
        df_energy['Sanierungsszenario'].str.replace(' Einsparungen im Vergleich zum Bestandsszenario in €', '')
    # Sort rows by archetype
    df_energy = df_energy.sort_values(by=['archetype name'], ascending=True)
    # The sorting of the lines by archetype causes a mixing of the indexes,
    # therefore the old indexes should be resetted.
    df_energy.reset_index(drop=True, inplace=True)

    # Refurbishment costs
    # Read in the redevelopment costs
    df_wall_costs = pd.read_csv('assessment/AußenwandKosten.csv')
    df_roof_costs = pd.read_csv('assessment/DachKosten.csv')
    df_window_costs = pd.read_csv('assessment/FensterKosten.csv')
    # Draw up a list of all the refurbishment materials for which costs are available.
    wall_roof_insulation = df_wall_costs['Material'].tolist()
    window_frame_types = df_window_costs['Material'].tolist()
    # Read the files on the masses of refurbishments
    lcia_csv_files = Path("report_data/life_cycle_inventory").glob("*Baustoffe.csv")
    # Create an empty list that can be filled later with data frames of the costs for each archetype
    refurb_costs = []
    # Iterate through archetype files on materials from life cycle inventory phase
    for i, archetype_file in enumerate(lcia_csv_files):
        # Gather the name of teh archetype
        file_name = archetype_file.name
        archetype_name_no_spaces = file_name.replace('Baustoffe.csv', '')
        # If there are several words in one Archetype name (e.g. Atelierhaus Plus),
        # fill in blank spaces between the words, as the file name doesn't have blank spaces
        archetype_name = re.sub(r"(\w)([A-Z])", r"\1 \2", archetype_name_no_spaces)
        # Read in the certain CSV file on materials to create dataframe
        df_materials = pd.read_csv(archetype_file)
        # The insulation material or frame material used for the renovation scenarios should be determined in
        # order to calculate the costs depending on the material. Therefore, the " Baustoffe" dataframe
        # is used to filter out which insulation materials or frame materials have been newly added.
        # To do this, all lines that describe only stock materials are first deleted
        df_materials.drop(df_materials.index[df_materials['Masse in kg Bestand'] != '-'], inplace=True)
        df_materials.drop(df_materials.index[df_materials['Masse in kg Komplettsanierung'] == '-'], inplace=True)
        # The column on the existing state is no longer needed
        df_materials.drop(columns='Masse in kg Bestand', inplace=True)

        # Read the number of windows and the area of roofs and exterior walls from the user input
        square_meter_wall = next(item for item in archetypes if item["archetype name"] == archetype_name)[
            "exterior walls area in m²"]
        square_meter_roof = next(item for item in archetypes if item["archetype name"] == archetype_name)["roof area in m²"]
        window_count = next(item for item in archetypes if item["archetype name"] == archetype_name)["number of windows"]
        # Filter out from the dataframe about the renovation materials only the materials that are used in the
        # exterior wall to obtain the insulation material for exterior wall renovation
        df_wall_insulation = df_materials[df_materials["Kostengruppe"].str.contains("Außenw")]
        # The base value "unbekannt" is used.
        insulation_type_wall = 'unbekannt'
        # Iterate through the materials for exterior wall renovation and check if one of the materials
        # matches an insulation material whose cost is defined in "AußenwandKosten.csv".
        for value in df_wall_insulation['Prozess']:
            for insulation_type in wall_roof_insulation:
                if insulation_type in value:
                    insulation_type_wall = insulation_type
                    break
        # analogous to insulation_type_wall
        df_roof_insulation = df_materials[df_materials["Kostengruppe"].str.contains("Dach")]
        insulation_type_roof = 'unbekannt'
        for value in df_roof_insulation['Prozess']:
            for insulation_type in wall_roof_insulation:
                if insulation_type in value:
                    insulation_type_roof = insulation_type
                    break
        # Get the window frame type of the new window
        window_frame_type = 'unbekannt'
        for value in df_materials['Prozess']:
            # Rahmen or rahmen, sometimes capital or small letter, so avoid errors and search for "ahmen"
            if 'ahmen' in value:
                window_frame_type = value
                break

        # Iterate through the materials for window frames whose costs are defined and check if one of the materials
        # matches teh frame material of the new window.
        frame_material = 'unbekannt'
        for sort in window_frame_types:
            if sort in window_frame_type:
                frame_material = sort
                break

        # Define function to determine renovation costs depending on the material and the area or
        # number for the refurbishment
        # refurb_costs: dataframe on costs in Best, Base or Worst Case for
        # refurbishment (AußenwandKosten.csv, DachKosten.csv, FensterKosten.csv)
        # refurbishment_material_: material for the refurbishment determined above
        # Value_: area or number for the refurbishment (square_meter_wall, square_meter_roof, window_count)
        # refurb_type_: refurbishment scenario
        def calc_refurb_costs(refurb_costs_df: pd.DataFrame, refurbishment_material_: str, value_: float,
                              refurb_type_: str):
            refurb_costs_df = refurb_costs_df.copy()
            # Set new column for the refurbishment Material
            refurb_costs_df = refurb_costs_df[refurb_costs_df["Material"] == refurbishment_material_]
            # Set new column for refurbishment costs for every case and multiply it with area of
            # insulation refurbishment or number of new windows
            refurb_costs_df[[f'Sanierungskosten {case} Case' for case in ["Best", "Base", "Worst"]]] *= value_
            # Add column on refurbishment type for further visualisation
            refurb_costs_df['Sanierungsszenario'] = refurb_type_
            return refurb_costs_df

        # Row for wall refurbishment
        df_arch_wall_costs = calc_refurb_costs(df_wall_costs, insulation_type_wall, square_meter_wall,
                                               'Außenwandsanierung')
        # Row for roof refurbishment
        df_arch_roof_costs = calc_refurb_costs(df_roof_costs, insulation_type_roof, square_meter_roof, 'Dachsanierung')
        # Row for window refurbishment
        df_arch_window_costs = calc_refurb_costs(df_window_costs, frame_material, window_count, 'Fenstersanierung')
        # Concatenate rows on costs for the different refurbishment scenarios
        df_arch_complete_costs = pd.concat([df_arch_wall_costs, df_arch_roof_costs, df_arch_window_costs])
        # Append one row for total refurbishment that summarizes the costs for the individual measures
        # Calculate the total costs first
        total = df_arch_complete_costs.sum()
        total.name = 'Total'
        # Assign sum of all rows of DataFrame as a new Row
        # Therefore a new dataframe with only one row of the total costs has to be created and
        # concatenated to the existing dataframe
        total_frame = pd.DataFrame([total.values], columns=total.index.values)
        df_arch_complete_costs = pd.concat([df_arch_complete_costs, total_frame], ignore_index=True)
        # Append column with archetype name for later visualisation with plotly
        df_arch_complete_costs['archetype name'] = archetype_name
        # The name of the total refurbishment is "AußenwandsanierungDachsanierungFenstersanierung" at the moment
        # and should be changed to "Komplettsanierung".
        df_arch_complete_costs.at[3, 'Sanierungsszenario'] = 'Komplettsanierung'
        # Reset the indexes
        df_arch_complete_costs.reset_index(drop=True, inplace=True)
        # reorder dataframe for later visualisation
        df_arch_complete_costs = reorder_dataframe(df_arch_complete_costs, [5, 4, 0, 1, 2, 3])
        # Append the dataframe in the refurbishment costs for the archetype to the list of dataframes
        # on refurbishment costs on all archetypes
        refurb_costs.append(df_arch_complete_costs)
    # Concatenate all dataframes on refurbishment costs for the different archetypes
    df_refurbishment_costs = pd.concat(refurb_costs)
    # To show that the energy cost savings are an income and the renovation costs are an
    # additional economic expenditure, the renovation costs are multiplied by the factor -1.
    df_refurbishment_costs[[f'Sanierungskosten {case} Case' for case in ["Best", "Base", "Worst"]]] *= -1
    # reset the indexes as they are mixed up due to the concatenation
    df_refurbishment_costs.reset_index(drop=True, inplace=True)
    # Combine the energy cost savings and renovation costs into one dataframe
    result = pd.merge(df_energy, df_refurbishment_costs, on=["archetype name", "Sanierungsszenario"])
    # Sum up the savings and the costs due to the refurbishment and add new columns for each case
    for case in ["Best", "Base", "Worst"]:
        result[f"Vergleich {case} Case"] = \
            result['Kapitalwert Energiekosten Einsparungen über 20 Jahre'] + result[f'Sanierungskosten {case} Case']
    # Reorder the entire dataframe for better visualization of the data for plotly
    result = reorder_dataframe(result, [0, 1, 3, 2, 4, 5, 6, 7, 8, 9])
    # Round values for enhanced visualisation
    result = result.round(decimals=2)
    # Rename columns for enhanced visualisation
    result.rename(columns={"archetype name": "Archetyp", "Sanierungsszenario": "Variante"}, inplace=True)


    # Start creating bar charts and tables for the buidling level
    # Plot table of alle cost information on building level
    create_four_grouped_table(result, 'Kostenanalyse (Werte in €)', 'report_data\life_cycle_costing\Kostenanalyse',
                              1000)
    # Create grouped bar chart for the energy cost savings
    create_grouped_bar_chart(result[["Archetyp", "Variante", "Kapitalwert Energiekosten Einsparungen über 20 Jahre"]],
                             'Kapitalwert Energiekosten Einsparungen über 20 Jahre Gebäudeebene', 'Euro',
                             'report_data\life_cycle_costing')
    # Create grouped bar charts for the refurbishments costs of all cases
    create_grouped_bar_chart(result[["Archetyp", "Variante", "Sanierungskosten Worst Case"]],
                             'Sanierungskosten Worst Case Gebäudeebene', 'Euro', 'report_data\life_cycle_costing')
    create_grouped_bar_chart(result[["Archetyp", "Variante", "Sanierungskosten Base Case"]],
                             'Sanierungskosten Base Case Gebäudeebene', 'Euro', 'report_data\life_cycle_costing')
    create_grouped_bar_chart(result[["Archetyp", "Variante", "Sanierungskosten Best Case"]],
                             'Sanierungskosten Best Case Gebäudeebene', 'Euro', 'report_data\life_cycle_costing')
    # Create grouped bar charts for the sum of energy cost savings and refurbishment costs
    create_grouped_bar_chart(result[["Archetyp", "Variante", "Vergleich Worst Case"]],
                             'Vergleich Energiekosteneinsparung vs Sanierungskosten Worst Case', 'Euro',
                             'report_data\life_cycle_costing')
    create_grouped_bar_chart(result[["Archetyp", "Variante", "Vergleich Base Case"]],
                             'Vergleich Energiekosteneinsparung vs Sanierungskosten Base Case', 'Euro',
                             'report_data\life_cycle_costing')
    create_grouped_bar_chart(result[["Archetyp", "Variante", "Vergleich Best Case"]],
                             'Vergleich Energiekosteneinsparung vs Sanierungskosten Best Case', 'Euro',
                             'report_data\life_cycle_costing')

    # Summary of all costs and sum of costs and savings on building level for all cases in a facetted bar chart
    result_all_cases_costs = result[
        ['Archetyp', 'Variante', 'Sanierungskosten Worst Case', 'Sanierungskosten Base Case',
         'Sanierungskosten Best Case']]
    # Unpivot the dataframe to obtain necessary format for facetted bar chart
    result_all_cases_costs = result_all_cases_costs.melt(id_vars=['Archetyp', 'Variante'],
                                                         value_vars=['Sanierungskosten Worst Case',
                                                                     'Sanierungskosten Base Case',
                                                                     'Sanierungskosten Best Case'],
                                                         var_name='Fälle', value_name='Kosten in €')
    result_all_cases_costs['Fälle'] = result_all_cases_costs['Fälle'].str.replace('Sanierungskosten ', '')
    create_facetted_bar_chart(df=result_all_cases_costs, facet_col='Fälle',
                              list_col=['Worst Case', 'Base Case', 'Best Case'],
                              directory='report_data\\life_cycle_costing\\alleKostenGebäude.pdf', y_var='Kosten in €')

    result_all_cases_sum = result[
        ['Archetyp', 'Variante', 'Vergleich Worst Case', 'Vergleich Base Case', 'Vergleich Best Case']]
    # Unpivot the dataframe to obtain necessary format for facetted bar chart
    result_all_cases_sum = result_all_cases_sum.melt(id_vars=['Archetyp', 'Variante'],
                                                     value_vars=['Vergleich Worst Case',
                                                                 'Vergleich Base Case',
                                                                 'Vergleich Best Case'],
                                                     var_name='Fälle', value_name='Kosten in €')
    result_all_cases_sum['Fälle'] = result_all_cases_sum['Fälle'].str.replace('Vergleich ', '')
    create_facetted_bar_chart(df=result_all_cases_sum, facet_col='Fälle',
                              list_col=['Worst Case', 'Base Case', 'Best Case'],
                              directory='report_data\\life_cycle_costing\\alleSummenGebäude.pdf', y_var='Kosten in €')

    print("Alle Kosten und Einsparungen wurden visualisiert!")

