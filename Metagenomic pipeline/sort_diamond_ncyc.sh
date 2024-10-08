#!/bin/bash


# 指定输入文件和map文件的名称
input_file="diamond_ncyc.tsv"
map_file="/home/adm/database/Ncyc/data/id2gene.map"

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
output_file="diamond_ncyc_sorted.tsv"

# 提取文件的前两列，并将第三列从map文件中添加到新文件
awk -F'\t' 'NR==FNR {map[$1]=$2; next} map[$2]!="" {print $1 "\t" $3 "\t" map[$2]}' "$map_file" "$input_file" > "$output_file"

# 删除第二列
awk -F'\t' '{$2=""; gsub(/\t\t/, "\t"); print}' "$output_file" > "$output_file.tmp"
mv "$output_file.tmp" "$output_file"

echo "操作完成，结果保存在 $output_file 中."











