# Rhythmic-and-Carbon-Fixation-Pathway
This repository contains the scripts and data associated with the article: "A Comprehensive Analysis of Rhythmic Patterns and Carbon Fixation in Microbial Communities of Unvegetated Tidal Flats". The project aims to explore rhythmic patterns and carbon fixation pathways in microbial communities found in various tidal flat environments.

# Key Components
## 1. Amplicon Pipeline
Contains scripts and metadata necessary for the analysis of amplicon sequencing data. Key workflows and input metadata files can be found under this directory. The raw amplicon data used in the analysis have been uploaded to NCBI. The NCBI Sequence Read Archive (SRA) accession can be found in the Data Availability section of the article.

## 2.Metagenomic Pipeline
This directory contains pipelines for analyzing non-redundant genes and metagenome-assembled genomes (MAGs). Key scripts and input metadata files can be found under this directory. The raw metagenomic data used in the analysis have been uploaded to NCBI. The NCBI Sequence Read Archive (SRA) accession can be found in the Data Availability section of the article.

## 3.R Scripts and Data
Includes various datasets and intermediate results used in the analysis. This section includes all R code and example data, which are stored in the Data directory and provided for illustrative purposes only.

# Repository Structure
```
Rhythmic-and-Carbon-Fixation-Pathway-main
├─ Amplicon pipeline
│    ├─ 01-Amplicon-workflow.md
│    └─ Metadata
│           ├─ manifest.txt
│           ├─ metadata.txt
│           └─ metadata_mudS.txt
├─ Data
│    ├─ JTKresult_feature_table_tax_rare_inter_mudX.txt
│    ├─ README.md
│    ├─ env_mud.txt
│    ├─ env_mudX.txt
│    ├─ feature_table_tax_rare.txt
│    ├─ feature_table_tax_rare_all.txt
│    ├─ feature_table_tax_rare_mud.txt
│    ├─ final_rhythmic_ASV_mudX.txt
│    ├─ lomb_results_noreplicate_asv_mudX.xlsx
│    ├─ metadata_all.txt
│    └─ metadata_mudX.txt
├─ LICENSE
├─ Lomb.Rmd
├─ Mantel_test_heatmap.Rmd
├─ Metacycle.Rmd
├─ Metagenomic pipeline
│    ├─ 01-Non-redundant-gene-pipeline.md
│    ├─ 02-MAGs-workflow.md
│    ├─ Data
│    │    ├─ list.txt
│    │    └─ list_all_sample.txt
│    ├─ Metadata
│    │    └─ list.txt
│    ├─ count_temp_adapt_aa.py
│    ├─ merge_abundance_eggnog.py
│    ├─ modify_abundance_eggnog.py
│    ├─ rename_contigs.sh
│    ├─ sort_bbmap_result.py
│    ├─ sort_bbmap_result_huizong.py
│    ├─ sort_diamond_mcyc.sh
│    ├─ sort_diamond_ncyc.sh
│    └─ sort_diamond_scyc.sh
├─ NMDS_12groups.Rmd
├─ README.md
├─ Randomforest.Rmd
└─ Rhythmic_ASV_plots.Rmd
```

# License
This project is licensed under the MIT License - see the LICENSE file for details.

# Citation
If you use this code in your research, please cite the following article:
A Comprehensive Analysis of Rhythmic Patterns and Carbon Fixation in Microbial Communities of Unvegetated Tidal Flats (to be added)
