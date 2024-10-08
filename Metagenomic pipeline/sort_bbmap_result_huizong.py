# coding=utf-8
import pandas as pd

def merge_multiple_files(file_paths, output_path):
    # 初始化一个空的DataFrame作为合并的基础
    merged_df = pd.DataFrame()

    # 遍历所有文件路径
    for file in file_paths:
        # 读取每个文件到DataFrame
        df = pd.read_csv(file, sep='\t', index_col='gene_name')

        # 如果merged_df为空，则直接赋值，否则进行合并
        if merged_df.empty:
            merged_df = df
        else:
            merged_df = merged_df.join(df, how='outer')

    # 保存合并后的DataFrame到指定的输出文件
    merged_df.to_csv(output_path, sep='\t')

# 文件路径列表
file_paths = ['RPKM1.txt', 'RPKM2.txt', 'RPKM3.txt', 'RPKM4.txt'] # 添加更多文件路径
output_path = 'RPKM.txt' # 合并后的输出文件路径

# 调用函数进行合并
merge_multiple_files(file_paths, output_path)
