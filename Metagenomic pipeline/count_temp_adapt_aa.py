import os
import csv
from Bio import SeqIO

def count_aa_in_fasta(file_path, aa_list):
    """
    Count the occurrences of specified amino acids in a FASTA file.

    Args:
        file_path (str): Path to the FASTA file.
        aa_list (list): List of amino acids to count.

    Returns:
        tuple: A dictionary of amino acid counts and the total number of amino acids.
    """
    aa_count = {aa: 0 for aa in aa_list}  # Initialize amino acid counts
    total_aa = 0  # Total amino acid count
    for record in SeqIO.parse(file_path, "fasta"):  # Parse the FASTA file
        for aa in record.seq:  # Iterate through each amino acid in the sequence
            if aa in aa_count:
                aa_count[aa] += 1
            total_aa += 1
    return aa_count, total_aa

def process_folder(folder_path, aa_list, output_file):
    """
    Process all FASTA files in a folder, count temperature-related amino acids, and save results to a CSV file.

    Args:
        folder_path (str): Path to the folder containing FASTA files.
        aa_list (list): List of amino acids to analyze.
        output_file (str): Path to save the output CSV file.
    """
    results = []  # List to store results
    for file_name in os.listdir(folder_path):  # Iterate through files in the folder
        if file_name.endswith(".fasta"):  # Check if the file is a FASTA file
            file_path = os.path.join(folder_path, file_name)
            aa_count, total_aa = count_aa_in_fasta(file_path, aa_list)  # Count amino acids
            # Calculate amino acid frequencies
            aa_frequency = {aa: aa_count[aa] / total_aa for aa in aa_list}
            # Append results for the current file
            results.append({
                "MAG": file_name,
                "Total_AA": total_aa,
                **{f"{aa}_Count": aa_count[aa] for aa in aa_list},
                **{f"{aa}_Frequency": aa_frequency[aa] for aa in aa_list}
            })
    
    # Save results to a CSV file
    with open(output_file, mode="w", newline="") as csvfile:
        fieldnames = ["MAG", "Total_AA"] + [f"{aa}_Count" for aa in aa_list] + [f"{aa}_Frequency" for aa in aa_list]
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()  # Write the header
        writer.writerows(results)  # Write the data
    print(f"Results have been saved to {output_file}")

if __name__ == "__main__":
    # Configuration parameters
    folder_path = "/path/to/amino/acids/folder"  # Path to the folder containing FASTA files
    output_file = "temp_adapt_aa_counts.csv"  # Name of the output file
    aa_list = ['I', 'Y', 'E', 'K', 'A', 'G']  # Temperature-related amino acids

    # Run the script
    process_folder(folder_path, aa_list, output_file)
