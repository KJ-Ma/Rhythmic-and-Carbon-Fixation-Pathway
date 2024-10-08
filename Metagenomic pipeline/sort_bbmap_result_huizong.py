# coding=utf-8
import pandas as pd

def merge_multiple_files(file_paths, output_path):
    # Initialize an empty DataFrame as the basis for merging
    merged_df = pd.DataFrame()

    # Iterate through all file paths
    for file in file_paths:
        # Read each file into a DataFrame
        df = pd.read_csv(file, sep='\t', index_col='gene_name')

        # If merged_df is empty, directly assign, otherwise merge
        if merged_df.empty:
            merged_df = df
        else:
            merged_df = merged_df.join(df, how='outer')

    # Save the merged DataFrame to the specified output file
    merged_df.to_csv(output_path, sep='\t')

# List of file paths
file_paths = ['RPKM1.txt', 'RPKM2.txt', 'RPKM3.txt', 'RPKM4.txt']  # Add more file paths as needed
output_path = 'RPKM.txt'  # Path for the merged output file

# Call the function to perform the merge
merge_multiple_files(file_paths, output_path)
