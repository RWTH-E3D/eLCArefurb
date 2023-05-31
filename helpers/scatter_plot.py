import pandas
import plotly.express as px

def create_scatter(df: pandas.DataFrame, x_axis: str, y_axis: str, title: str, directory: str, height: int = 700) -> None:

    '''

    Create a scatter plot to compare the ecological and economic effects of the renovations.
    Thereby, all archetypes and snaation scenarios shall be presented at the same time
    :param df: pandas data frame as data source
    :param x_axis: Name of dataframe column that represents the x-axis entries
    :param y_axis: Name of dataframe column that represents the y-axis entries
    :param title: title of the table
    :param directory: directory to save the table
    :param image_height: height of pdf file to save table
    '''
    # Create plotly express scatter plot

    fig = px.scatter(df, x=x_axis, y=y_axis, color="Variante", symbol="Archetyp", title=title, template='none')
    # Set font
    fig.update_traces(marker=dict(size=12,
                              line=dict(width=0.5,
                                        color='black')))
    fig.update_layout(font_family='Serif', font_color="black", font_size=16)
    #fig.data = fig.data[::-1]
    # Save PDf file
    fig.write_image(directory, engine='kaleido', height=height)



def create_facetted_scatter(df: pandas.DataFrame, x_axis: str, y_axis: str, facet_col: str, title: str, directory: str, height: int = 1600, width: int = 1200) -> None:

    '''

    Create multiple dot plots side by side to compare the environmental and economic impacts of the retrofits.
    All archetypes and scenarios should be shown at the same time. This function is used to display the dot
    diagrams for Worst Base and Best Case next to each other.

    :param df: pandas data frame as data source
    :param x_axis: Name of dataframe column that represents the x-axis entries
    :param y_axis: Name of dataframe column that represents the y-axis entries
    :param facet_col: Column that determines the layout of the diagrams. Per value of this column a new diagram is created.
    :param title: title of the table
    :param directory: directory to save the table
    :param image_height: height of pdf file to save table


    '''
    # Create plotly express scatter plot
    fig = px.scatter(df, x=x_axis, y=y_axis, color="Variante", symbol="Archetyp", facet_col=facet_col, title=title, template='none')
    # Set font
    fig.update_layout(font_family='Serif', font_color="black", uniformtext=dict(minsize=20, mode='show'))
    fig.update_traces(marker=dict(line=dict(width=0.5, color='black')))
    #fig.data = fig.data[::-1]
    # Save PDf file
    fig.write_image(directory, engine='kaleido',  width=width, height=height)