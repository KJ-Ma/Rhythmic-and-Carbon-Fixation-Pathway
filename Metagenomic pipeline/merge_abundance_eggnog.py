# Open the protein.emapper.annotations file
with open("protein.emapper.annotations", "r") as f1:
    protein_lines = f1.readlines()

# Open the RPKM.txt file
with open("RPKM.txt", "r") as f2:
    rpkm_lines = f2.readlines()

# Create a dictionary to store data from protein.emapper.annotations file
protein_data = {}
for line in protein_lines:
    columns = line.strip().split('\t')
    if len(columns) >= 12:
        key = columns[0]
        values = columns[6:9] + [columns[11]]
        protein_data[key] = values

# Create a new merged output
output_lines = []
for line in rpkm_lines:
    columns = line.strip().split('\t')
    key = columns[0]
    if key in protein_data:
        merged_columns = columns + protein_data[key]
    else:
        # If there is no match, fill with empty values
        merged_columns = columns + [""] * 4

    output_lines.append('\t'.join(merged_columns) + '\n')

# Write the merged data to a new file
with open("merged_RPKM.txt", "w") as output_file:
    output_file.writelines(output_lines)

print("Merge complete, results saved in merged_RPKM.txt.")

