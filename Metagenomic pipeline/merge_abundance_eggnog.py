# 打开protein.emapper.annotations文件
with open("protein.emapper.annotations", "r") as f1:
    protein_lines = f1.readlines()

# 打开RPKM.txt文件
with open("RPKM.txt", "r") as f2:
    rpkm_lines = f2.readlines()

# 创建一个字典，用于存储protein.emapper.annotations文件的数据
protein_data = {}
for line in protein_lines:
    columns = line.strip().split('\t')
    if len(columns) >= 12:
        key = columns[0]
        values = columns[6:9] + [columns[11]]
        protein_data[key] = values

# 创建一个新的合并后的文件
output_lines = []
for line in rpkm_lines:
    columns = line.strip().split('\t')
    key = columns[0]
    if key in protein_data:
        merged_columns = columns + protein_data[key]
    else:
        # 如果没有匹配结果，则填充空值
        merged_columns = columns + [""] * 4

    output_lines.append('\t'.join(merged_columns) + '\n')

# 将合并后的数据写入新文件
with open("merged_RPKM.txt", "w") as output_file:
    output_file.writelines(output_lines)

print("合并完成，结果保存在 merged_RPKM.txt 文件中。")
