# 打开 merged_RPKM.txt 文件
with open("merged_RPKM.txt", "r") as input_file:
    lines = input_file.readlines()

# 创建一个新的处理后的文件
output_lines = []
for line in lines:
    columns = line.strip().split('\t')
    
    # 1. 将表格数据中的“-”替换为空值
    for i in range(len(columns)):
        if columns[i] == "-":
            columns[i] = ""
    
    # 2. 将第290列的表格数据中，如果包括两个及以上的字母，则只保留第一个字母
    if len(columns) >= 290:
        column_289 = columns[289]
        if len(column_289) >= 2:
            columns[289] = column_289[0]
    
    # 3. 将第290列的表格数据中的ko:删去
    if len(columns) >= 293:
        column_292 = columns[292]
        if column_292.startswith("ko:"):
            columns[292] = column_292[3:]
    
    output_lines.append('\t'.join(columns) + '\n')


# 获取表头并添加到最后四列后面
header = output_lines[0].strip().split('\t')
header.extend(["COG_category", "Description", "Preferred_name", "KEGG_ko"])
output_lines[0] = '\t'.join(header) + '\n'

# 将处理后的数据写入新文件
with open("merged_RPKM_eggnog.txt", "w") as output_file:
    output_file.writelines(output_lines)

print("文件处理完成，结果保存在 merged_RPKM_eggnog.txt 文件中。")
