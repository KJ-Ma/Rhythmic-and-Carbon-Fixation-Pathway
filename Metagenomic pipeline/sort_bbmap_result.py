# encoding = utf-8
# @Time :2023/3/16 15:34
# Author : Pinocchio


import os
import sys
from collections import defaultdict
# os.chdir("/data/guest2022/Peiyou/Project/virus_gene_quantify/bwa/pileup/HuB")
stat_type = sys.argv[1]
# stat_type = "RPKM"
stat_index = 0
if stat_type == "Bases":
    stat_index = 2
elif stat_type == "Coverage":
    stat_index = 3
elif stat_type == "RPKM":
    stat_index = 5
elif stat_type == "FPKM":
    stat_index = 7
else:
    print("no such type")
    exit()
samples = []
rpkms = os.popen("ls *rpkm.out").read().split("\n")[:-1]
header = ["gene_name"]
for rpkm in rpkms:
    header.append(rpkm.split(".rpkm")[0])
    samples.append(rpkm.split(".rpkm")[0])
F = open(f"{stat_type}.txt","w")
print("\t".join(header),file=F)

gene2sample2rpkm = {}
genes = set()

for rpkm in rpkms:
    sample = rpkm.split(".rpkm")[0]
    
    with open(rpkm, "r") as f:
        for line in f:
            if line[0] == "#":
                continue
            else:
                ls = line.split("\t")
                gene_name = ls[0]
                if "#" in gene_name:
                    continue
                if gene_name not in gene2sample2rpkm.keys():
                    genes.add(gene_name)
                    gene2sample2rpkm[gene_name] = defaultdict(float)
                RPKM_value = ls[stat_index]
                gene2sample2rpkm[gene_name][sample] = RPKM_value

genes = list(genes)

for g in genes:
    p = [g]
    for s in samples:
        p.append(gene2sample2rpkm[g][s])
    try:
        print("\t".join(p),file=F)
    except:
        print(str(p))
        exit()
F.close()