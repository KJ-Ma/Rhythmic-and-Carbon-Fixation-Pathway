#!/bin/bash

# 指定输入文件和map文件的名称
input_file="diamond_mcyc.tsv"
map_file="/home/adm/database/Mcyc/id2gene.map"

# 检查输入文件和map文件是否存在
if [ ! -f "$input_file" ]; then
    echo "输入文件 $input_file 不存在."
    exit 1
fi

if [ ! -f "$map_file" ]; then
    echo "Map文件 $map_file 不存在."
    exit 1
fi

# 创建新文件的名称
output_file="diamond_mcyc_sorted.tsv"

# 提取文件的前两列，并将第三列从map文件中添加到新文件，两列之间只有一个制表符分隔
awk -F'\t' 'NR==FNR {map[$1]=$2; next} map[$2]!="" {print $1 "\t" map[$2]}' "$map_file" "$input_file" > "$output_file"

# 添加表头
sed -i '1i gene_name\tmcyc_result' "$output_file"

echo "操作完成，结果保存在 $output_file 中."
