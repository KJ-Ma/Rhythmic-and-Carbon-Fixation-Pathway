# Open the merged_RPKM.txt file
with open("merged_RPKM.txt", "r") as input_file:
    lines = input_file.readlines()

# Create a new processed output
output_lines = []
for line in lines:
    columns = line.strip().split('\t')
    
    # 1. Replace "-" in table data with empty values
    for i in range(len(columns)):
        if columns[i] == "-":
            columns[i] = ""
    
    # 2. In column 290, if there are two or more letters, keep only the first letter
    if len(columns) >= 290:
        column_289 = columns[289]
        if len(column_289) >= 2:
            columns[289] = column_289[0]
    
    # 3. In column 290, remove "ko:" prefix if present
    if len(columns) >= 293:
        column_292 = columns[292]
        if column_292.startswith("ko:"):
            columns[292] = column_292[3:]
    
    output_lines.append('\t'.join(columns) + '\n')

# Retrieve header and add to the last four columns
header = output_lines[0].strip().split('\t')
header.extend(["COG_category", "Description", "Preferred_name", "KEGG_ko"])
output_lines[0] = '\t'.join(header) + '\n'

# Write the processed data to a new file
with open("merged_RPKM_eggnog.txt", "w") as output_file:
    output_file.writelines(output_lines)

print("File processing complete. Results saved in merged_RPKM_eggnog.txt.")
