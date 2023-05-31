import pandas as pd
import numpy as np
from helpers import load_component_json, create_grouped_bar_chart, create_vertical_bar_chart, create_four_grouped_table, create_scatter, \
    create_facetted_scatter, create_report_data_dirs


def create_rating_diagram():
    '''

    This section is for a comparison of the environmental and economic aspects of remediation. The function "create_rating_diagram() reads
    the file "Veränderungen.CSV" from the interpretation phase and the file "Kostenanalyse.CSV" from the life cycle costing.
    Scatter plots are created showing the incremental cost or savings from retrofit on the x-axis and the increase or decrease in
    CO2 emissions compared to the existing building on the y-axis for each archetype and retrofit option. The costs on the x-axis
    are given in Euros. An evaluation diagram is created for each of the best, base, and worst cases. For each case, a diagram is
    created at the building level with the changes in greenhouse gas emissions on the y-axis in kg CO2-eqv./m2a and a diagram
    for the results at the neighborhood level with the change in kg CO2-eqv./a (CaseXBewertungsdiagramm.pdf:).
    Furthermore, the representation of the percentage change in greenhouse gas emissions compared to the existing scenario
    is provided (CaseXBewetungsdiagrammProzent.pdf:).
    The retrofit measures whose costs are not amortized within 20 years according to calculations by eLCArefurb, but result in a
    reduction of greenhouse gas emissions, should be carried out in second priority if sufficient economic resources are available.
    These variants appear in the lower left quadrant of the scatter diagrams.
    To visualize preferences between the different measures in first and second priority, potential GHG savings per Euro
    are calculated and output in tabular form in both PDF and CSV formats (CO2proEuro). A chart grading the measures taken
    in the first priority (CO2EinsparungenproEuro1Priorität.pdf) shows how many kg CO2-eqv./a are saved for each Euro
    gained through the renovation. The corresponding chart for 2nd priority measures indicates how much greenhouse
    gases are saved per euro spent as a result of the remediation measures(CO2EinsparungenproEuro2Priorität.pdf).
     The greenhouse gas savings per euro always refer only to the base case scenario of the sum of energy cost savings and
     renovation costs. Furthermore, only individual measures are evaluated here. To determine the GHG savings per Euro,
     the change in GWP per building in kg CO2-eqv./m2a from the file "Changes.CSV" is multiplied by the net floor area of
     the respective archetype, which is taken from the JSON file "archetypes" created in the 2nd step of the program.
     The result is then divided by the building-level costs taken from the Kostenanalyse.CSV" file.

    Input:
    1) Kostenanalyse.csv: Tables summarising the life cycle costing are prepared, showing for each variant the net present value of the energy costs,
        the renovation costs in the best, base and worst case and the sum of the two in the best base and worst case
        on building level.
    2) KostenanalyseQuartier.csv: ables summarising the life cycle costing are prepared, showing for each variant the net present value of the energy costs,
        the renovation costs in the best, base and worst case and the sum of the two in the best base and worst case
        on quarter level.
    3) Veränderungen.csv: Bar chart showing the changes in total GWP compared to the existing stock for the different refurbishment scenarios on building level.
    4) Veränderungen Quartier.csv: Bar chart showing the changes in total GWP compared to the existing stock for the different refurbishment scenarios on quarter level.

    Output:
    1) CaseXBewertungsdiagramm.pdf
    2) CaseXBewetungsdiagrammProzent.pdf
    3) CO2proEuro (PDF und CSV)
    4) CO2EinsparungenproEuro2Priorität.pdf
    5) CO2EinsparungenproEuro1Priorität.pdf
    6) BarChartPrisorisierungsabfolge

    '''

    # Create report data folders if they don't exist already
    create_report_data_dirs()
    # Read data on building level for costs and GWP and create dataframe
    costs = pd.read_csv('report_data/life_cycle_costing/Kostenanalyse.csv', encoding="utf-8")
    greenhouse_gases = pd.read_csv('report_data/life_cycle_interpretation/variants/Veränderungen.csv', encoding="utf-8")
    result = pd.merge(costs, greenhouse_gases, on=["Archetyp", "Variante"])


    # Rating diagrams for Base Case scenario on building level in percent and kg CO2-Äqv.
    create_scatter(result[["Archetyp", "Variante", "Vergleich Base Case", "Veränderungen zu Bestand in %"]],
                   x_axis="Vergleich Base Case", y_axis="Veränderungen zu Bestand in %",
                   title="Bewertungsdiagramm Gebäudeebene Base Case",
                   directory="report_data/final_rating/BaseBewertungsdiagrammProzent.pdf")
    create_scatter(result[["Archetyp", "Variante", "Vergleich Base Case",
                           "Veränderungen zu Bestand in kg CO<sub>2</sub>-Äqv./m<sup>2</sup><sub>NGF</sub>a"]],
                   x_axis="Vergleich Base Case",
                   y_axis="Veränderungen zu Bestand in kg CO<sub>2</sub>-Äqv./m<sup>2</sup><sub>NGF</sub>a",
                   title="Bewertungsdiagramm Gebäudeebene Base Case",
                   directory='report_data/final_rating/BaseBewertungsdiagramm.pdf')

    # Rating diagrams for Best Case scenario on building level in percent and kg CO2-Äqv.
    create_scatter(result[["Archetyp", "Variante", "Vergleich Best Case", "Veränderungen zu Bestand in %"]],
                   x_axis="Vergleich Best Case", y_axis="Veränderungen zu Bestand in %",
                   title="Bewertungsdiagramm Gebäudeebene Best Case",
                   directory="report_data/final_rating/BestBewertungsdiagrammProzent.pdf")
    create_scatter(result[["Archetyp", "Variante", "Vergleich Best Case",
                           "Veränderungen zu Bestand in kg CO<sub>2</sub>-Äqv./m<sup>2</sup><sub>NGF</sub>a"]],
                   x_axis="Vergleich Best Case",
                   y_axis="Veränderungen zu Bestand in kg CO<sub>2</sub>-Äqv./m<sup>2</sup><sub>NGF</sub>a",
                   title="Bewertungsdiagramm Gebäudeebene Best Case",
                   directory='report_data/final_rating/BestBewertungsdiagramm.pdf')

    # Rating diagrams for Worst Case scenario on building level in percent and kg CO2-Äqv.
    create_scatter(result[["Archetyp", "Variante", "Vergleich Worst Case", "Veränderungen zu Bestand in %"]],
                   x_axis="Vergleich Worst Case", y_axis="Veränderungen zu Bestand in %",
                   title="Bewertungsdiagramm Gebäudeebene Worst Case",
                   directory="report_data/final_rating/WorstBewertungsdiagrammProzent.pdf")
    create_scatter(result[["Archetyp", "Variante", "Vergleich Worst Case",
                           "Veränderungen zu Bestand in kg CO<sub>2</sub>-Äqv./m<sup>2</sup><sub>NGF</sub>a"]],
                   x_axis="Vergleich Worst Case",
                   y_axis="Veränderungen zu Bestand in kg CO<sub>2</sub>-Äqv./m<sup>2</sup><sub>NGF</sub>a",
                   title="Bewertungsdiagramm Gebäudeebene Worst Case",
                   directory='report_data/final_rating/WorstBewertungsdiagramm.pdf')


    # Faceted diagrams on quarter level
    # All Cost Cases compared to the GWP in kg CO2-Äqv.

    # Faceted diagrams on building level
    # All Cost Cases compared to the GWP in kg CO2-Äqv.
    facet_result_kg = result[['Archetyp', 'Variante', 'Vergleich Worst Case',
                              'Vergleich Base Case', 'Vergleich Best Case',
                              'Veränderungen zu Bestand in kg CO<sub>2</sub>-Äqv./m<sup>2</sup><sub>NGF</sub>a']]
    facet_result_kg = facet_result_kg.melt(id_vars=['Archetyp', 'Variante',
                                                    'Veränderungen zu Bestand in kg CO<sub>2</sub>-Äqv./m<sup>2</sup><sub>NGF</sub>a'],
                                           value_vars=['Vergleich Worst Case', 'Vergleich Base Case',
                                                       'Vergleich Best Case'],
                                           var_name='Fälle', value_name='Kosten in €')
    facet_result_kg['Fälle'] = facet_result_kg['Fälle'].str.replace('Vergleich ', '')
    create_facetted_scatter(df=facet_result_kg, x_axis='Kosten in €',
                            y_axis='Veränderungen zu Bestand in kg CO<sub>2</sub>-Äqv./m<sup>2</sup><sub>NGF</sub>a',
                            facet_col='Fälle', title='Alle Fälle auf Gebäudeebene GWP in kg CO<sub>2</sub>-Äqv./a',
                            directory='report_data\\final_rating\\alleFällekgCO2Gebäude.pdf')

    # All Cost Cases compared to the GWP in %
    facet_result_percentage = result[['Archetyp', 'Variante', 'Vergleich Worst Case',
                                      'Vergleich Base Case', 'Vergleich Best Case', 'Veränderungen zu Bestand in %']]
    facet_result_percentage = facet_result_percentage.melt(
        id_vars=['Archetyp', 'Variante', 'Veränderungen zu Bestand in %'],
        value_vars=['Vergleich Worst Case', 'Vergleich Base Case', 'Vergleich Best Case'],
        var_name='Fälle', value_name='Kosten in €')
    facet_result_percentage['Fälle'] = facet_result_percentage['Fälle'].str.replace('Vergleich ', '')
    create_facetted_scatter(df=facet_result_percentage, x_axis='Kosten in €',
                            y_axis='Veränderungen zu Bestand in %', facet_col='Fälle',
                            title='Alle Fälle auf Gebäudeebene GWP in %',
                            directory='report_data\\final_rating\\alleFälleProzentGebäude.pdf')

    print(
        "Punktdiagramme zum Vergleich der ökonomischen Auswirkungen im Base, Best und Worst Case mit den GWP-Veränderungen in Prozent und in kg CO2-Äqv. wurden erstrellt!")

    # CO2 per Euro
    archetypes: list[dict] = load_component_json("archetypes")
    # To determine the GWP savings per Euro only the following 3 columns are needed
    df_co2_per_euro_all = result.copy()
    df_co2_per_euro_all = df_co2_per_euro_all[["Archetyp", "Variante", "Vergleich Base Case",
                                               "Veränderungen zu Bestand in kg CO<sub>2</sub>-Äqv./m<sup>2</sup><sub>NGF</sub>a"]]
    # The GWP change is multiplied by the net floor area and then divided by the
    # building-level refurbishment costs in the Base Case
    df_co2_per_euro_all['NGF'] = None
    # First fill teh column for the net ground space with the matching sizes
    for archetype in archetypes:
        df_co2_per_euro_all['NGF'] = np.where((df_co2_per_euro_all['Archetyp'] == archetype['archetype name']),
                                              archetype['NFA in m²'], df_co2_per_euro_all['NGF'])
    # Now add a new row and calculate the CO2 change per Euro
    df_co2_per_euro_all['kg CO<sub>2</sub>-Äqv./a pro Euro'] = (df_co2_per_euro_all[
                                                                    'Veränderungen zu Bestand in kg CO<sub>2</sub>-Äqv./m<sup>2</sup><sub>NGF</sub>a'] *
                                                                df_co2_per_euro_all['NGF']) / df_co2_per_euro_all[
                                                                   'Vergleich Base Case']
    # Create table to show data
    create_four_grouped_table(df=df_co2_per_euro_all[['Archetyp', 'Variante', 'kg CO<sub>2</sub>-Äqv./a pro Euro']],
                              title='Tabelle kg CO<sub>2</sub>-Äqv./a pro Euro',
                              directory="report_data\\final_rating\\CO2proEuro")

    # Visualise the preferences of the first priority
    # (GWP savings and economic savings)
    df_co2_per_euro_first_prio = df_co2_per_euro_all.copy()
    # Define which scenarios do not belong to the 1st priority and remove them from the dataframe
    # Not included in the 1st priority:
    # all scenarios in which the refurbishment costs cannot be amortized by the energy cost savings,
    # all scenarios that cause additional GWP,
    # the complete refurbishment is excluded because only individual measures are to be investigated here
    indexNames_first = df_co2_per_euro_first_prio[(df_co2_per_euro_first_prio[
                                                       'Veränderungen zu Bestand in kg CO<sub>2</sub>-Äqv./m<sup>2</sup><sub>NGF</sub>a'] >= 0) | (
                                                          df_co2_per_euro_first_prio['Vergleich Base Case'] <= 0) | (
                                                          df_co2_per_euro_first_prio[
                                                              'Variante'] == 'Komplettsanierung')].index
    df_co2_per_euro_first_prio.drop(indexNames_first, inplace=True)
    # Since the GWP change has a negative sign and the money change has a positive sign (revenue),
    # the result is a negative value, which is converted into a positive value for better understanding.
    df_co2_per_euro_first_prio['kg CO<sub>2</sub>-Äqv./a pro Euro'] = df_co2_per_euro_first_prio[
                                                                          'kg CO<sub>2</sub>-Äqv./a pro Euro'] * (-1)
    # Create Plotly bar chart
    create_grouped_bar_chart(input_frame=df_co2_per_euro_first_prio[
        ['Archetyp', 'Variante', 'kg CO<sub>2</sub>-Äqv./a pro Euro']],
                             title='kg CO<sub>2</sub>-Äqv./a-Einsparung pro eingenommenem Euro (1. Priorität)',
                             y_axis_name='kg CO<sub>2</sub>-Äqv./a pro Euro', directory="report_data\\final_rating")

    # Visualise the preferences of the second priority (gwp savings, but costs)
    df_co2_per_euro_second_prio = df_co2_per_euro_all.copy()
    # Define which scenarios do not belong to the 2nd priority and remove them from the dataframe
    # Not included in the 2nd priority:
    # all scenarios in which the refurbishment costs can be amortized by the energy cost savings,
    # all scenarios that cause additional GWP,
    # the complete refurbishment is excluded because only individual measures are to be investigated here
    indexNames_second = df_co2_per_euro_second_prio[(df_co2_per_euro_second_prio[
                                                         'Veränderungen zu Bestand in kg CO<sub>2</sub>-Äqv./m<sup>2</sup><sub>NGF</sub>a'] >= 0) | (
                                                                df_co2_per_euro_second_prio[
                                                                    'Vergleich Base Case'] >= 0) | (
                                                                df_co2_per_euro_second_prio[
                                                                    'Variante'] == 'Komplettsanierung')].index
    df_co2_per_euro_second_prio.drop(indexNames_second, inplace=True)
    # Create Plotly bar chart
    create_grouped_bar_chart(
        input_frame=df_co2_per_euro_second_prio[['Archetyp', 'Variante', 'kg CO<sub>2</sub>-Äqv./a pro Euro']],
        title='kg CO<sub>2</sub>-Äqv./a-Einsparung pro ausgegebenem Euro (2. Priorität)',
        y_axis_name='kg CO<sub>2</sub>-Äqv./a pro Euro', directory="report_data\\final_rating")


    df_prio_order =  df_co2_per_euro_all.copy()

    df_prio_order["Maßnahme"] = df_prio_order[['Archetyp', 'Variante']].agg(', '.join, axis=1)
    df_prio_order = df_prio_order.drop(df_prio_order[df_prio_order.Variante=="Komplettsanierung"].index)
    create_vertical_bar_chart(input_frame=df_prio_order, title="Priorisierungsabfolge", y_axis_name="Maßnahme", x_axis_name='kg CO<sub>2</sub>-Äqv./a pro Euro', directory="report_data\\final_rating")


    print("Darstellungen der GWP-Veränderungen pro ausgegebenem oder eingenommenem Euro wurden erstellt!")
