# Metagenome Non-redundant gene Pipeline

## 1. Notes on file names

The names of the metagenomic sequencing files contain sample information: for example, in mud01.2021.01.S, "mud" indicates that the sampling site is a mudflat, the number represents the sampling date (January 2021), and "S" indicates a sample depth of 1-5 cm (where "Z" represents a depth of 5-15 cm and "X" represents 15-25 cm). Similarly, in sand01.2021.01.D.S, "sand" indicates that the sampling site is a sandflat, the number denotes the sampling date (January 2021), "D" indicates a low tide sample (where "Z" represents mid tide and "G" represents high tide), and "S" again indicates a sample depth of 1-5 cm (with "Z" for 5-15 cm and "X" for 15-25 cm).

## 2. Software Versions

- **FastQC**: v0.12.1
- **MultiQC**: v1.14
- **Trimmomatic**: v0.39
- **Parallel**: v1.23.0
- **metaWRAP**: v1.3.2 (MEGAHIT v1.1.3, metabat2 v2.12.1, MaxBin v2.2.6, concoct v1.0.0)
- **quast**: v5.0.2
- **coverM**: v0.6.1
- **GTDB-Tk**: v2.3.2
- **SeqKit**: v2.5.1
- **Prodigal**: v2.6.3
- **cdhit**: v4.8.1
- **DIAMOND**: v2.1.8
- **CheckM**: v1.2.2
- **IQ-TREE**: v1.6.12
- **trimAl**: v1.4.rev15
- **MEGAN**: v6.24.20
- **BWA**: v0.7.17 (r1188)
- **BBMap**: v39.06
- **emapper**: v2.1.12
- **dRep**: v3.4.5
- **Prokka**: v1.14.6
- **METABOLIC**: v.4.0

## 3. Create gene set

### 3.1 Gene prediction and deduplication

Download contigs from S3 and rename
```sh
for i in `tail -n+1 list.txt`; do 
  aws s3 cp s3://makuojian/metagenome/results/mix3_assembly/${i}/megahit/final.contigs.fa 01contigs/
  mv 01contigs/final.contigs.fa 01contigs/mix3_${i}.fa
done
```
Filter contigs less than 500bp
```sh
parallel -j 16 --xapply "seqkit seq -j 2 -m 500 01contigs/mix3_{}.fa > 02contigs_500/mix3_500_{}.fa" ::: `tail -n+1 list.txt`
```
Rename contigs using a custom script (rename_contigs.sh)
```sh
screen -S rename_contigs
bash rename_contigs.sh
```
Gene prediction with Prodigal
```sh
parallel -j 1 --xapply "mkdir -p 04prodigal/{}" ::: `tail -n+1 list.txt`
parallel -j 24 --xapply "prodigal -i 03renamed_contigs/mix3_500_{}_modified.fa -a 04prodigal/{}/{}_protein.fasta \
  -d 04prodigal/{}/{}_nucleotide.fasta -f gff -o 04prodigal/{}/{}.gff -s 04prodigal/{}/{}_potential.stat \
  -p meta -m" ::: `tail -n+1 list.txt`
parallel -j 32 --xapply "seqkit stat 04prodigal/{}/{}_nucleotide.fasta" ::: `tail -n+1 list.txt` > prodigal_gene_stat.txt
```
Remove sequences less than 100bp
```sh
parallel -j 8 --xapply "seqkit seq -m 100 04prodigal/{}/{}_nucleotide.fasta > 04prodigal_min_100/{}_nucleotide_min_100.fasta" ::: `tail -n+1 list.txt`
```
Merge nucleotide sequences from different samples, and deduplicate nucleotide sequences using cd-hit
```sh
for i in `tail -n+1 list.txt`; do cat 04prodigal_min_100/${i}_nucleotide_min_100.fasta >> 05partial_merged/all_nucleotide.fasta; done
nohup cd-hit-est -i all_nucleotide.fasta -o all_cdhit_nucleotide.fasta -aS 0.9 -c 0.95 -G 0 -g 1 -d 0 -M 0 -T 64 > all_cdhit.log 2>&1 &
seqkit stat all_cdhit_nucleotide.fasta -j 24 > all_cdhit_nucleotide_stat.txt
```
Extract non-redundant protein sequences
```sh
grep '>' all_cdhit_nucleotide.fasta > non_redundancy_gene_list.txt
sed -i 's/>//' non_redundancy_gene_list.txt
for i in `tail -n+1 ../list.txt`; do 
  s3_key="s3://makuojian/metagenome/results/07rm_redundancy/04prodigal/${i}/${i}_protein.fasta"
  aws s3 cp ${s3_key} protein_temp/
done
parallel -j 1 --xapply "cat protein_temp/{}_protein.fasta >> 07partial_cdhit2/all_protein.fasta" ::: `tail -n+1 ../list.txt`
seqkit grep -n -f non_redundancy_gene_list.txt all_protein.fasta > non_redundancy_protein.fasta
```
### 3.2 Species annotation and quantification

DIAMOND NR database annotation
```sh
nohup diamond blastp -d /home/adm/database/NCBI/NCBI_NR/nr_20230728.dmnd -q ../07rm_redundancy/07partial_cdhit2/non_redundancy_protein.fasta \
  --outfmt 6 --max-target-seqs 5 -e 1e-10 --query-cover 80 --id 50 --threads 100 -c 1 -b 12 -o diamond_annotation_nr.tsv > diamond_log.txt 2>&1 &
```
Use blast2lca with MEGAN to extract species information
```sh
split -n l/500 diamond_annotation_nr.tsv diamond_annotation_nr
parallel -j 20 --xapply "blast2lca -i {}.tsv -o megan_output/{}.LCA -f BlastTab -ms 50 -me 0.001 --mapDB /home/ec2-user/software/db/megan/megan-map-Feb2022.db" ::: `tail -n+1 list.txt`
```
Index sequences with bwa for read mapping
```sh
bwa index -p non_redundancy_nucleotide ../all_cdhit_nucleotide.fasta
parallel -j 2 --xapply "bwa mem -t 124 bwa_index/non_redundancy_nucleotide ../cleandata/{}.paired.R_1.fastq ../cleandata/{}.paired.R_2.fastq | gzip -3 > bwa_out/{}.sam.gz" ::: `tail -n+1 list.txt`
```
BBMap for RPKM calculation
```sh
sed 's/ .*//' all_cdhit_nucleotide.fasta > all_cdhit_nucleotide_renamed.fasta
nohup parallel -j 5 --xapply "pileup.sh in=bwa_out/{}.sam.gz ref=all_cdhit_nucleotide_renamed.fasta out=bbmap_out/{}.coverage.txt -Xmx200g rpkm=bbmap_out/{}.rpkm.out && pigz -9 bbmap_out/{}.coverage.txt" ::: `tail -n+1 list.txt` > pileup_log.txt 2>&1 &
```
Summarize RPKM across samples
```sh
python /home/ec2-user/scripts/sort_bbmap_result.py RPKM
python sort_bbmap_result_huizong.py
```
