# Amplicon Pipeline

## 1. Notes on file names

The names of the amplicon sequencing files contain sample information: for example, in mud01.2021.01.S1, "mud" indicates that the sampling site is a mudflat, the number represents the sampling date (January 2021), "S" indicates a sample depth of 1-5 cm (where "Z" represents a depth of 5-15 cm and "X" represents 15-25 cm), and "1" denotes the first replicate among three parallel samples. Similarly, in sand01.2021.01.D.S, "sand" indicates that the sampling site is a sandflat, the number denotes the sampling date (January 2021), "D" indicates a low tide sample (where "Z" represents mid tide and "G" represents high tide), "S" again indicates a sample depth of 1-5 cm (with "Z" for 5-15 cm and "X" for 15-25 cm), and "2" denotes the second replicate among three parallel samples.

## 2. Software Versions

- **QIIME2**: v2023.5
- **Parallel**: v1.23.0

## 3. Analysis pipeline

### 3.1 Data Import and Primer Removal

Activate env
```sh
conda activate qiime2-2023.5
```
Import raw data into QIIME2
```
qiime tools import \
  --type SampleData[PairedEndSequencesWithQuality] \
  --input-path manifest.txt \
  --output-path paired-end-demux.qza \
  --input-format PairedEndFastqManifestPhred33V2
```
Summarize and visualize the data, can be viewed on https://view.qiime2.org/
```sh
qiime demux summarize \
  --i-data result/paired-end-demux.qza \
  --o-visualization result/paired-end-demux-summary.qzv
```
Remove primers (modified V4 primers)
```sh
qiime cutadapt trim-paired \
  --i-demultiplexed-sequences result/paired-end-demux.qza \
  --p-cores 90 \
  --p-no-indels \
  --p-front-f GTGYCAGCMGCCGCGGTAA \
  --p-front-r GGACTACNVGGGTWTCTAAT \
  --o-trimmed-sequences result/primer-trimmed-demux.qza
```
Visualize the primer-trimmed data
```sh
qiime demux summarize \
  --i-data result/primer-trimmed-demux.qza \
  --o-visualization result/primer-trimmed-demux-summary.qzv
```
### 3.2 Generate ASVs

Use DADA2 for merging, denoising, chimera removal, and generating the feature table and representative sequences
```sh
nohup qiime dada2 denoise-paired \
  --i-demultiplexed-seqs result/primer-trimmed-demux.qza \
  --p-trunc-len-f 220 \
  --p-trunc-len-r 210 \
  --p-n-threads 0 \
  --o-table result/table.qza \
  --o-representative-sequences result/rep-seqs.qza \
  --o-denoising-stats result/denoising-stats.qza > result/dada_log.txt 2>&1 &
```
Visualize the denoising stats, feature table, and representative sequences
```sh
qiime metadata tabulate --m-input-file result/denoising-stats.qza --o-visualization result/denoising-stats.qzv
qiime feature-table summarize --i-table result/table.qza --o-visualization result/table.qzv
qiime feature-table tabulate-seqs --i-data result/rep-seqs.qza --o-visualization result/rep-seqs.qzv
```
### 3.3 Taxonomic Classification

Classification with V4 classifier
```sh
nohup qiime feature-classifier classify-sklearn \
  --i-classifier qiime2_classifier/silva-138-99-515-806-nb-classifier.qza \
  --i-reads ../01.rawdata/result/rep-seqs.qza \
  --o-classification qiime2_result/taxonomy.qza \
  --p-n-jobs 48 > qiime2_result/classify_log.txt 2>&1 &
```
Visualize taxonomy classification results
```sh
qiime metadata tabulate --m-input-file taxonomy.qza --o-visualization taxonomy.qzv
```
### 3.4 Data Filtering

Filter out contaminants, mitochondria, chloroplasts, and eukaryotes
```sh
nohup qiime taxa filter-table \
  --i-table ../01.rawdata/result/table.qza \
  --i-taxonomy ../02.otu_analysis/qiime2_result/taxonomy.qza \
  --p-exclude mitochondria,chloroplast,eukaryota \
  --p-include p__ \
  --o-filtered-table feature-table-filt-contam.qza > filter_contam_log.txt 2>&1 &

qiime feature-table summarize --i-table feature-table-filt-contam.qza --o-visualization feature-table-filt-contam.qzv
```
Filter rare ASVs
```sh
qiime feature-table filter-features --i-table feature-table-filt-contam.qza --p-min-frequency 5 --p-min-samples 3 --o-filtered-table feature-table-finally.qza

qiime feature-table summarize --i-table feature-table-finally.qza --o-visualization feature-table-finally.qzv
```
Update the representative sequences
```sh
qiime feature-table filter-seqs --i-table feature-table-finally.qza --i-data ../01.rawdata/result/rep-seqs.qza --o-filtered-data repset-seqs.qza
```
Construct a phylogenetic tree for 16S analysis
```sh
nohup qiime phylogeny align-to-tree-mafft-fasttree \
  --i-sequences repset-seqs.qza \
  --o-alignment aligned-repset-seqs.qza \
  --p-n-threads 62 \
  --o-masked-alignment masked-aligned-repset-seqs.qza \
  --o-tree unrooted-tree.qza \
  --o-rooted-tree rooted-tree.qza > fasttree_log.txt 2>&1 &
```
Alpha rarefaction curve
```sh
qiime diversity alpha-rarefaction \
  --i-table feature-table-finally.qza \
  --i-phylogeny rooted-tree.qza \
  --p-max-depth 168807 \
  --m-metadata-file ../04.taxonomy/metadata.txt \
  --o-visualization alpha-rarefaction.qzv
```
### 3.5 Export Data

Export data for downstream analysis
```sh
qiime tools export --input-path ../01.data/feature-table-finally.qza --output-path ./
qiime tools export --input-path ../01.data/taxonomy.qza --output-path ./
qiime tools export --input-path ../01.data/repset-seqs.qza --output-path ./
qiime tools export --input-path ../01.data/rooted-tree.qza --output-path ./
```



