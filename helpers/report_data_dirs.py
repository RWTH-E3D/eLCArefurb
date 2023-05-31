import os

def create_report_data_dirs():
    '''
    Since empty folders are not captured in GitLab, the folder structure for sorting the result files
    should be created automatically, if the folders do not exist yet.
    '''
    # Create report data folders if they don't exist already
    root = 'report_data'
    midFolders = ['life_cycle_inventory', 'life_cycle_impact', 'life_cycle_interpretation', 'life_cycle_costing', 'final_rating']
    endFolders = ['material_pie_charts', 'variants']
    for midFolder in midFolders:
        # exist_ok = True: if directories already exist leave them unaltered
        os.makedirs(os.path.join(root, midFolder), exist_ok=True)
    for endFolder in endFolders:
        os.makedirs(os.path.join(root, 'life_cycle_interpretation', endFolder), exist_ok=True)