# coding=utf-8
import pandas as pd

def merge_multiple_files(file_paths, output_path):
    # ��ʼ��һ���յ�DataFrame��Ϊ�ϲ��Ļ���
    merged_df = pd.DataFrame()

    # ���������ļ�·��
    for file in file_paths:
        # ��ȡÿ���ļ���DataFrame
        df = pd.read_csv(file, sep='\t', index_col='gene_name')

        # ���merged_dfΪ�գ���ֱ�Ӹ�ֵ��������кϲ�
        if merged_df.empty:
            merged_df = df
        else:
            merged_df = merged_df.join(df, how='outer')

    # ����ϲ����DataFrame��ָ��������ļ�
    merged_df.to_csv(output_path, sep='\t')

# �ļ�·���б�
file_paths = ['RPKM1.txt', 'RPKM2.txt', 'RPKM3.txt', 'RPKM4.txt'] # ��Ӹ����ļ�·��
output_path = 'RPKM.txt' # �ϲ��������ļ�·��

# ���ú������кϲ�
merge_multiple_files(file_paths, output_path)
