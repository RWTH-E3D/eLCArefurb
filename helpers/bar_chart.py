import pandas
import plotly.express as px
import string


# Function to create grouped bar charts
# Used to represent all variants of all archetypes at the same time
def create_grouped_bar_chart(input_frame: pandas.DataFrame, title: str, y_axis_name: str, directory: str = "report_data\\life_cycle_interpretation\\variants") -> None:
    """

    This function creates a grouped bar chart with plotly express to represent all refurbishment scenarios of
    all archetypes at the same time in one bar chart.
    :param input_frame: pandas data frame as data source
    :param title: title of the table
    :param y_axis_name: Sometimes there should be more explanation on the y-axis, e.g. about units, than just
            the column name describing the y-axis, so this parameter can be used to adjust the label of the y-axis
    :param directory: directory to save the table
    """
    # Identify name without punctuation, subscript or superscript nor spaces for the PDF name
    new_string = title.translate(str.maketrans('', '', string.punctuation))
    no_spaces_title = new_string.replace(" ", "")
    no_subscript_title = no_spaces_title.replace("suba", "")
    no_subscript_title = no_spaces_title.replace("sub", "")
    # Columns of the DataFrame indicate the entries of the bar chart
    col = input_frame.columns.values.tolist()
    # plotly express create grouped bar chart
    # x-axis shows archetype and colour of bar represents refurbishment scenario
    fig = px.bar(input_frame,
                 x="Archetyp",
                 color="Variante",
                 # 3rd column of dataframe is shows the y-axis
                 y=col[2],
                 # Bars should display their height with a label above the bar
                 text=col[2],
                 # PDf should have a title
                 title=title,
                 # Grouped bar chart
                 barmode='group',
                 height=400,
                 # rename y-axis if needed
                 labels={col[2]: y_axis_name},
                 # Blue colour scheme
                 #color_discrete_sequence = px.colors.sequential.Rainbow,
                 # White background
                 template='none'
                 )
    # Text on the bars should be outside and in an 90° angle
    fig.update_traces(textfont_size=12, textposition='outside', cliponaxis=False, textangle=-90)
    # Set font
    fig.update_layout(font=dict(family="Times New Roman", size=16, color="black"), uniformtext=dict(minsize=16, mode='show'), title_x=0.5)
    # Save image as PDF
    fig.write_image(f'{directory}\BarChart{no_subscript_title}.pdf',
                    engine='kaleido', height=400)



def create_stacked_bar_chart(input_frame: pandas.DataFrame, title: str, y_axis_name: str, directory: str = "report_data\\life_cycle_interpretation\\variants") -> None:

    """

    This function creates a stacked bar chart with plotly express to represent all refurbishment scenarios of
    all archetypes at the same time in one bar chart and show teh influence of the life cycle modules on the total GWP.
    :param input_frame: pandas data frame as data source
    :param title: title of the table
    :param y_axis_name: Sometimes there should be more explanation on the y-axis, e.g. about units, than just
            the column name describing the y-axis, so this parameter can be used to adjust the label of the y-axis
    :param directory: directory to save the table
    """

    # Identify name without punctuation, subscript or superscript nor spaces for the PDF name
    new_string = title.translate(str.maketrans('', '', string.punctuation))
    no_spaces_title = new_string.replace(" ", "")
    no_subscript_title = no_spaces_title.replace("subtotalsub", "")
    # List of all archetype names
    archetypes_list = list(dict.fromkeys(input_frame["Archetyp"].tolist()))
    # Create List of all column names
    col = input_frame.columns.values.tolist()
    # plotly express create stacked bar chart
    fig = px.bar(input_frame,
                 x="Variante",
                 color="Modul",
                 # 4th column of the dataframe shows gwp (y-axis value)
                 y=col[3],
                 # Stacked bars should display their gwp with a label above the bar
                 text=col[3],
                 title=title,
                 height=1100,
                 labels={col[3]: y_axis_name},
                 facet_col="Archetyp",
                 category_orders={"Archetyp": archetypes_list},
                 #color_discrete_sequence = px.colors.sequential.Rainbow,
                 template='none'
                )
    fig.update_traces(textangle=0, textposition='outside', textfont_size=8, cliponaxis=False)
    # Set font and order of refurbishment scenarios
    fig.update_layout(uniformtext=dict(minsize=6, mode='show'), font_family="Times New Roman", font_color="black", title_x=0.5,
                      xaxis={'categoryorder': 'array', 'categoryarray': ['Bestand', 'Außenwandsanierung', 'Dachsanierung', 'Fenstersanierung', 'Komplettsanierung']})
    fig.write_image(f'{directory}\\BarChart{no_subscript_title}.pdf',
                    engine='kaleido', width=1000, height=1100)

# Show two grouped bar charts next to each other
def create_facetted_bar_chart(df: pandas.DataFrame, facet_col: str, list_col: list, directory: str, y_var: str):
    """

    This function creates two grouped bar charts next to each other with plotly express to represent all refurbishment scenarios of
    all archetypes at the same time and to compare different GWP sources.
    :param df: pandas data frame as data source
    :param facet_col: Column that determines the layout of the diagrams. Per value of this column a new diagram is created.
    :param list_col: All entries of the facet column
    :param directory: directory to save the table
    :param y_var: y-axis labeling

    """


    fig = px.bar(df, x='Archetyp',
                 y=y_var,
                 color='Variante',
                 barmode="group",
                 facet_col=facet_col,
                 category_orders={facet_col: list_col},
                 text=y_var,
                 height=2000,
                 #color_discrete_sequence = px.colors.sequential.Rainbow,
                 template='none',
                 labels={y_var:  y_var}
                 )
    fig.update_traces(textposition='outside', textfont_size=24, cliponaxis=False, textangle=-90)
    fig.update_layout(font=dict(family="Times New Roman", size=24, color="black"), uniformtext=dict(minsize=24, mode='show'),
                     title_x=0.5)
    #fig.update_layout(font_family="Serif", uniformtext=dict(minsize=24, mode='show'), font_color="black", title_x=0.5)
    # Save image as PDF for further data processing
    fig.write_image(directory, engine='kaleido', height=2000,  width=800)


def create_vertical_bar_chart(input_frame: pandas.DataFrame, title: str, x_axis_name : str, y_axis_name: str, directory: str) -> None:
    """

    This function creates a grouped bar chart with plotly express to represent all refurbishment scenarios of
    all archetypes at the same time in one bar chart.
    :param input_frame: pandas data frame as data source
    :param title: title of the table
    :param y_axis_name: Sometimes there should be more explanation on the y-axis, e.g. about units, than just
            the column name describing the y-axis, so this parameter can be used to adjust the label of the y-axis
    :param directory: directory to save the table
    """
    # Identify name without punctuation, subscript or superscript nor spaces for the PDF name
    new_string = title.translate(str.maketrans('', '', string.punctuation))
    no_spaces_title = new_string.replace(" ", "")
    no_subscript_title = no_spaces_title.replace("suba", "")
    no_subscript_title = no_spaces_title.replace("sub", "")
    # Columns of the DataFrame indicate the entries of the bar chart
    col = input_frame.columns.values.tolist()
    # plotly express create grouped bar chart
    # x-axis shows archetype and colour of bar represents refurbishment scenario
    fig = px.bar(input_frame,
                 x=x_axis_name,
                 # 3rd column of dataframe is shows the y-axis
                 y=y_axis_name,
                 # PDf should have a title
                 title=title,
                 orientation ="h",
                 height=400,
                 #color_discrete_sequence = px.colors.sequential.Rainbow,
                 # White background
                 template='none'
                 )
    # Text on the bars should be outside and in an 90° angle
    fig.update_traces(textfont_size=12, textposition='outside', cliponaxis=False)
    # Set font
    fig.update_layout(font=dict(family="Times New Roman", size=16, color="black"), uniformtext=dict(minsize=16, mode='show'), title_x=0.5, yaxis={'categoryorder':'total ascending'})
    # Save image as PDF
    fig.write_image(f'{directory}\BarChart{no_subscript_title}.pdf',
                    engine='kaleido', height=400, width= 1000)



