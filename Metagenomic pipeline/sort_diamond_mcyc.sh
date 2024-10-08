#!/bin/bash

# Specify the names of the input file and map file
input_file="diamond_mcyc.tsv"
map_file="/home/adm/database/Mcyc/id2gene.map"

# Check if the input file and map file exist
if [ ! -f "$input_file" ]; then
    echo "Input file $input_file does not exist."
    exit 1
fi

if [ ! -f "$map_file" ]; then
    echo "Map file $map_file does not exist."
    exit 1
fi

# Create the name for the new output file
output_file="diamond_mcyc_sorted.tsv"

# Extract the first two columns from the input file, adding the third column from the map file to the new file
awk -F'\t' 'NR==FNR {map[$1]=$2; next} map[$2]!="" {print $1 "\t" map[$2]}' "$map_file" "$input_file" > "$output_file"

# Add header to the output file
sed -i '1i gene_name\tmcyc_result' "$output_file"

echo "Operation completed. Results saved in $output_file."
