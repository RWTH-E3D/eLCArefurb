import pandas
import plotly.graph_objects as go
import numpy as np
np.random.seed(1)
import plotly.io as pio
pio.kaleido.scope.mathjax = None

def create_table(df: pandas.DataFrame, title: str, directory: str, image_height: int, layout_width: int = 2000, layout_height: int = 10000) -> None:
    """
    Create a plotly table with alternating row colours.
    :param df: pandas data frame that should be displayed as a table
    :param cell_values: column titles of the table
    :param title: title of the table
    :param directory: directory to save the table and table name without ".pdf" at the end
    :param image_height: height of pdf file to save table

    """
    headerColor = 'grey'
    rowEvenColor = 'lightgrey'
    rowOddColor = 'white'
    # Create plotly table
    fig = go.Figure(data=[go.Table(
        # Set headers
        header=dict(values=list(df.columns),
                    line_color='darkslategray',
                    fill_color=headerColor,
                    align=['left', 'center'],
                    font=dict(color='white', size=12)
                    ),
        # Set cell values
        cells=dict(
            # Set cell values as list of columns in the dataframe
            values=[df[f'{column}'] for column in df.columns.tolist()],
            line_color='darkslategray',
            # List of colors for alternating rows
            fill_color=[[rowOddColor, rowEvenColor] * 200],
            align=['left', 'center'],
            font=dict(color='darkslategray', size=11)
        ))
    ])
    fig.update_layout(width=layout_width, height=layout_height)
    # Set font
    fig.update_layout(title_text=title,  font_family="Serif", font_color="black")
    # Save PDF
    fig.write_image(directory + '.pdf', engine='kaleido', height=image_height)
    # Save CSV file for further data processing
    df.to_csv(directory + '.csv', index=False)

def create_five_grouped_table(df: pandas.DataFrame, title: str, directory: str, image_height: int) -> None:
    """
    Create a plotly table with grouped row colours for a better differentiation of the different archetypes.
    Five rows have the same colour.
    :param df: pandas data frame that should be displayed as a table
    :param cell_values: column titles of the table
    :param title: title of the table
    :param directory: directory to save the table and table name without ".pdf" at the end
    :param image_height: height of pdf file to save table

    """
    headerColor = 'grey'
    rowEvenColor = 'lightgrey'
    rowOddColor = 'white'
    # Create plotly table
    fig = go.Figure(data=[go.Table(
        header=dict(values=list(df.columns),
                    # Set headers
                    line_color='darkslategray',
                    fill_color=headerColor,
                    align=['left', 'center'],
                    font=dict(color='white', size=12)
                    ),
        cells=dict(
            # Set cell values as list of columns in the dataframe
            values=[df[f'{column}'] for column in df.columns.tolist()],
            line_color='darkslategray',
            # List of colors for alternating rows
            fill_color=[[rowOddColor, rowOddColor, rowOddColor, rowOddColor, rowOddColor, rowEvenColor, rowEvenColor, rowEvenColor, rowEvenColor, rowEvenColor] * 200],
            align=['left', 'center'],
            font=dict(color='darkslategray', size=11)
        ))
    ])
    fig.update_layout(width=2000, height=10000)
    # Set font
    fig.update_layout(title_text=title,  font_family="Serif", font_color="black")
    # Save PDF
    fig.write_image(directory + '.pdf', engine='kaleido', height=image_height)
    # Save CSV file for further data processing
    df.to_csv(directory + '.csv', index=False)





def create_four_grouped_table(df: pandas.DataFrame, title: str, directory: str, image_height: int = 1000) -> None:
    """
    Create a plotly table with grouped row colours for a better differentiation of the different archetypes.
    Four rows have the same colour.
    :param df: pandas data frame that should be displayed as a table
    :param cell_values: column titles of the table
    :param title: title of the table
    :param directory: directory to save the table and table name without ".pdf" at the end
    :param image_height: height of pdf file to save table
    """
    headerColor = 'grey'
    rowEvenColor = 'lightgrey'
    rowOddColor = 'white'
    # Create plotly table
    fig = go.Figure(data=[go.Table(
        header=dict(values=list(df.columns),
                    # Set headers
                    line_color='darkslategray',
                    fill_color=headerColor,
                    align=['left', 'center'],
                    font=dict(color='white', size=12)
                    ),
        cells=dict(
            # Set cell values as list of columns in the dataframe
            values=[df[f'{column}'] for column in df.columns.tolist()],
            line_color='darkslategray',
            # List of colors for alternating rows
            fill_color=[[rowOddColor, rowOddColor, rowOddColor, rowOddColor, rowEvenColor, rowEvenColor, rowEvenColor, rowEvenColor] * 200],
            align=['left', 'center'],
            font=dict(color='darkslategray', size=11)
        ))
    ])
    fig.update_layout(width=2000, height=10000)
    # Set font
    fig.update_layout(title_text=title,  font_family="Serif", font_color="black")
    # Save PDf
    fig.write_image(directory + '.pdf', engine='kaleido', height=image_height)
    # Save CSV file for further data processing
    df.to_csv(directory + '.csv', index=False)

