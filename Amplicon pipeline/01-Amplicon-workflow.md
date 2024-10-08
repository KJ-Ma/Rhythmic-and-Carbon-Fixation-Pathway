# Amplicon Pipeline

## 1. Notes on file names

The names of the amplicon sequencing files contain sample information: for example, in mud01.2021.01.S1, "mud" indicates that the sampling site is a mudflat, the number represents the sampling date (January 2021), "S" indicates a sample depth of 1-5 cm (where "Z" represents a depth of 5-15 cm and "X" represents 15-25 cm), and "1" denotes the first replicate among three parallel samples. Similarly, in sand01.2021.01.D.S, "sand" indicates that the sampling site is a sandflat, the number denotes the sampling date (January 2021), "D" indicates a low tide sample (where "Z" represents mid tide and "G" represents high tide), "S" again indicates a sample depth of 1-5 cm (with "Z" for 5-15 cm and "X" for 15-25 cm), and "2" denotes the second replicate among three parallel samples.

## 2. Software Versions

- **QIIME2**: v2023.5
- **Parallel**: v1.23.0

## 3. Analysis pipeline of all samples

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
## 4. Analysis pipeline of subgroup samples (Taking the upper layer of mudflats as an example)

### 4.1 Data Filter

Copy original data and metadata
```sh
cp /home/ec2-user/00.third/01.all/01.data/* ./01.original_data
cp /home/ec2-user/00.third/01.all/metadata.txt ./01.original_data
```
Filter mudflat upper layer data
```sh
qiime feature-table filter-samples \
  --i-table 01.original_data/feature-table-finally.qza \
  --m-metadata-file 01.original_data/metadata.txt \
  --p-where "[Sediment_type]='mudflat' AND [Depth]='1_5cm'" \
  --o-filtered-table 02.latest_data/feature-table-finally.qza
```
Visualize filtered feature table
```sh
qiime feature-table summarize \
  --i-table 02.latest_data/feature-table-finally.qza \
  --o-visualization 02.latest_data/feature-table-finally.qzv
```
Update representative sequences
```sh
qiime feature-table filter-seqs \
  --i-table 02.latest_data/feature-table-finally.qza \
  --i-data 01.original_data/repset-seqs.qza \
  --o-filtered-data 02.latest_data/repset-seqs.qza
```
Copy taxonomy data
```sh
cp 01.original_data/taxonomy.qza 02.latest_data/
```
Build phylogenetic tree for 16S analysis
```sh
qiime phylogeny align-to-tree-mafft-fasttree \
  --i-sequences 02.latest_data/repset-seqs.qza \
  --o-alignment 02.latest_data/aligned-repset-seqs.qza \
  --p-n-threads 8 \
  --o-masked-alignment 02.latest_data/masked-aligned-repset-seqs.qza \
  --o-tree 02.latest_data/unrooted-tree.qza \
  --o-rooted-tree 02.latest_data/rooted-tree.qza
```
### 4.2 Preliminary drawing

Taxonomy bar plot
```sh
qiime taxa barplot \
  --i-table ../01.data/02.latest_data/feature-table-finally.qza \
  --i-taxonomy ../01.data/02.latest_data/taxonomy.qza \
  --m-metadata-file ../metadata.txt \
  --o-visualization taxa-bar-plots.qzv
```
### 4.3 Data Processing

Collapse taxonomy at different levels
```sh
qiime taxa collapse \
  --i-table ../01.data/02.latest_data/feature-table-finally.qza \
  --i-taxonomy ../01.data/02.latest_data/taxonomy.qza \
  --p-level 1 \
  --o-collapsed-table taxa_summary/feature-table-final-L1.qza

qiime taxa collapse \
  --i-table ../01.data/02.latest_data/feature-table-finally.qza \
  --i-taxonomy ../01.data/02.latest_data/taxonomy.qza \
  --p-level 2 \
  --o-collapsed-table taxa_summary/feature-table-final-L2.qza

# Repeat for levels 3 to 7
qiime taxa collapse --i-table ../01.data/02.latest_data/feature-table-finally.qza --i-taxonomy ../01.data/02.latest_data/taxonomy.qza --p-level 3 --o-collapsed-table taxa_summary/feature-table-final-L3.qza
qiime taxa collapse --i-table ../01.data/02.latest_data/feature-table-finally.qza --i-taxonomy ../01.data/02.latest_data/taxonomy.qza --p-level 4 --o-collapsed-table taxa_summary/feature-table-final-L4.qza
qiime taxa collapse --i-table ../01.data/02.latest_data/feature-table-finally.qza --i-taxonomy ../01.data/02.latest_data/taxonomy.qza --p-level 5 --o-collapsed-table taxa_summary/feature-table-final-L5.qza
qiime taxa collapse --i-table ../01.data/02.latest_data/feature-table-finally.qza --i-taxonomy ../01.data/02.latest_data/taxonomy.qza --p-level 6 --o-collapsed-table taxa_summary/feature-table-final-L6.qza
qiime taxa collapse --i-table ../01.data/02.latest_data/feature-table-finally.qza --i-taxonomy ../01.data/02.latest_data/taxonomy.qza --p-level 7 --o-collapsed-table taxa_summary/feature-table-final-L7.qza
```
Summarize collapsed tables
```
parallel -j 1 --xapply "qiime feature-table summarize --i-table taxa_summary/{}.qza --o-visualization taxa_summary/{}.qzv" ::: ls taxa_summary/ | sed 's/.qza//'
```
Alpha and Beta diversity analysis
```sh
qiime diversity core-metrics-phylogenetic \
  --i-phylogeny ../01.data/02.latest_data/rooted-tree.qza \
  --i-table ../01.data/02.latest_data/feature-table-finally.qza \
  --p-sampling-depth 40208 \
  --p-n-jobs-or-threads 8 \
  --m-metadata-file ../metadata.txt \
  --output-dir core-metrics-results
```
Alpha diversity significance tests
```
parallel -j 8 --xapply "qiime diversity alpha-group-significance --i-alpha-diversity core-metrics-results/{1}.qza --m-metadata-file ../metadata.txt --o-visualization core-metrics-results/{1}-group-significance.qzv" ::: ls -1 core-metrics-results/*vector.qza | xargs -I {} basename {} .qza
```
Beta diversity significance tests
```sh
parallel -j 8 --xapply "qiime diversity beta-group-significance --i-distance-matrix core-metrics-results/{1}.qza --m-metadata-file ../metadata.txt --m-metadata-column Month --o-visualization core-metrics-results/{1}-group-significance.qzv --p-pairwise" ::: ls -1 core-metrics-results/*matrix.qza | xargs -I {} basename {} .qza
```
### 4.4 Data Export

Export final feature table, taxonomy, representative sequences, and rooted tree
```sh
qiime tools export --input-path ../01.data/02.latest_data/feature-table-finally.qza --output-path ./
qiime tools export --input-path ../01.data/02.latest_data/taxonomy.qza --output-path ./
qiime tools export --input-path ../01.data/02.latest_data/repset-seqs.qza --output-path ./
qiime tools export --input-path ../01.data/02.latest_data/rooted-tree.qza --output-path ./
```
