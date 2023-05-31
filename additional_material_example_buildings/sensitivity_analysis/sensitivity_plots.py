import plotly.express as px
import pandas as pd

'''This script was used to visualize the results of the sensitivity 
analyses as well as to calculate the sensitivity parameters.'''

def create_sensi_plot(df, x_axis, y_axis, title, xaxisname, yaxisname, filename,
                      annotation_x = 30, annotation_y = 5, color='Variante', height=400):

        '''
        This function creates sensitivity plots for energy sensitivity
        (energy saving potential and energy carbon tax).
         The annotations are based on the various remediation measures.
         '''


        fig = px.scatter(df, x=x_axis, y=y_axis, color=color, trendline="ols", title=title, template='none')
        # Set titles and font
        fig.update_layout(font_family='Serif', font_color="black", xaxis_title=xaxisname, yaxis_title=yaxisname, uniformtext=dict(minsize=20, mode='show'))
        # The equations of the graphs should be determined to show the sensitivity parameters such as the rate of change
        # Trend line shows the connection of all data dots
        # In this case the trendlines are linear
        model = px.get_trendline_results(fig)
        # A linear equation is composed of the y-axis intercept and the slope. Alpha describes the
        # y-axis intercept and beta the slope. Element "0" of the model
        # is the trend line for exterior wall renovation, element "1" is the trend line for roof
        # renovation and element "2" is the trend line for window renovation - element "3" is the
        # trend line for complete renovation.
        results_wall = model.iloc[0]["px_fit_results"]
        alpha_wall = results_wall.params[0]
        beta_wall = results_wall.params[1]

        results_roof = model.iloc[1]["px_fit_results"]
        alpha_roof = results_roof.params[0]
        beta_roof = results_roof.params[1]

        results_window = model.iloc[2]["px_fit_results"]
        alpha_window = results_window.params[0]
        beta_window = results_window.params[1]

        results_all = model.iloc[3]["px_fit_results"]
        alpha_all = results_all.params[0]
        beta_all = results_all.params[1]

        # Set lines for annotation
        # A line with a linear equation for each rehabilitation measure
        line1 = 'y<sub>Außenwandsanierung</sub> = ' + str(round(alpha_wall, 4)) + ' + ' + str(round(beta_wall, 4))+'x'
        line2 = 'y<sub>Dachsanierung</sub> = ' + str(round(alpha_roof, 4)) + ' + ' + str(round(beta_roof, 4))+'x'
        line3 = 'y<sub>Fenstersanierung</sub> = ' + str(round(alpha_window, 4)) + ' + ' + str(round(beta_window, 4))+'x'
        line4 = 'y<sub>Komplettsanierung</sub> = ' + str(round(alpha_all, 4)) + ' + ' + str(round(beta_all, 4))+'x'
        # Add line breaks between the equations
        summary = line1 + '<br>' + line2 + '<br>' + line3 + '<br>' + line4
        # Add annotation
        fig.add_annotation(
                x=annotation_x,
                y=annotation_y,
                xref="x",
                yref="y",
                text=summary,
                showarrow=False,
                font=dict(
                    family="Times New Roman",
                    size=16,
                    color="black"
                    ),
                align="left",
                arrowhead=2,
                arrowsize=1,
                arrowwidth=2,
                arrowcolor="#636363",
                ax=20,
                ay=-30,
                borderwidth=2,
                borderpad=4,
                bgcolor="rgba(100,100,100, 0.6)",
                opacity=0.8
                )

        fig.write_image(filename, engine='kaleido', height=height)

# Sensitivity analysis of the energy savings potential
# Read data on the different costs and GWP for various energy saving potentials
df_energy = pd.read_csv('data.csv')
# two dataframes: one for the GWP and one for the costs
df_gwp = df_energy.drop('Base Case Vergleich', axis=1)
df_costs = df_energy.drop('Einsparung GWP', axis=1)
# Two plots: one for the GWP and one for the costs
create_sensi_plot(df=df_gwp, x_axis="Einsparung in %", y_axis="Einsparung GWP", title='Auswirkungen des Energieeinsparpotenzials auf die Treibhausgaseinsparungen pro Gebäude', xaxisname='Endenergieeinsparung in %', yaxisname='Veränderungen in kg CO<sub>2</sub>-Äqv./m<sup>2</sup><sub>NGF</sub>a', filename='energy_gwp_sensitivity.pdf')
create_sensi_plot(df=df_costs, x_axis="Einsparung in %", y_axis="Base Case Vergleich", title='Auswirkungen des Energieeinsparpotenzials auf die Einsparungen pro Gebäude', xaxisname='Endenergieeinsparung in %', yaxisname='Summe Energiekosteneinsparung und Sanierungskosten in € (Base Case)', filename='energy_costs_sensitivity.pdf', annotation_x=55, annotation_y=-30000)


