# Metagenome Analysis Pipeline

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

### 2.1 Quality Control

Batch processing through Amazon Web Services (AWS)
All raw metagenomic sequencing data are stored in the "metagenome/01rawdata" folder on the AWS cloud platform for analysis.
```sh
echo 'qc sample: '$1', threads: '$2, 'bucket: '$3, 'dbtable: '$4
sample=$1
threads=$2
bucket=$3
dbtable=$4

src_path=s3://$bucket/metagenome/01rawdata
results_path=s3://$bucket/metagenome/results/qc
storage_class=INTELLIGENT_TIERING

aws dynamodb execute-statement --statement "UPDATE $dbtable SET status=1, threads=$threads WHERE sample='$sample'"
time1=`date +%s`
#unzip
mkdir -p rawdata
aws s3 sync ${src_path}/${sample}/ rawdata/
echo 'unzip...'
gunzip rawdata/*.gz
mv rawdata/${sample}.R1.fq rawdata/${sample}.R_1.fastq
mv rawdata/${sample}.R2.fq rawdata/${sample}.R_2.fastq
aws dynamodb execute-statement --statement "UPDATE $dbtable SET status=2 WHERE sample='$sample'"

echo 'quality control...'
mkdir -p fastqc_before_trimmomatic
mkdir -p multiqc_before_trimmomatic
#raw data quality check
fastqc rawdata/*.fastq -t $threads -o fastqc_before_trimmomatic/
multiqc -d fastqc_before_trimmomatic/ -o multiqc_before_trimmomatic/
echo 'upload raw data quality check results'
aws s3 sync fastqc_before_trimmomatic ${results_path}/${sample}/fastqc_before_trimmomatic/ --storage-class ${storage_class} 
aws s3 sync multiqc_before_trimmomatic ${results_path}/${sample}/multiqc_before_trimmomatic/ --storage-class ${storage_class}
aws dynamodb execute-statement --statement "UPDATE $dbtable SET status=3 WHERE sample='$sample'"

#trimmomatic
mkdir -p cleandata
java -jar /opt/tools/Trimmomatic-0.39/trimmomatic-0.39.jar PE -threads $threads -phred33 \
rawdata/${sample}.R_1.fastq rawdata/${sample}.R_2.fastq \
cleandata/${sample}.paired.R_1.fastq cleandata/${sample}.unpaired.R_1.fastq \
cleandata/${sample}.paired.R_2.fastq cleandata/${sample}.unpaired.R_2.fastq \
ILLUMINACLIP:/opt/tools/Trimmomatic-0.39/adapters/TruSeq3-PE.fa:2:30:10 LEADING:3 TRAILING:3 SLIDINGWINDOW:5:20 MINLEN:50
rm cleandata/*.unpaired.*
echo 'upload trimmomatic results'
aws s3 sync cleandata ${results_path}/${sample}/cleandata/ --storage-class ${storage_class}
aws dynamodb execute-statement --statement "UPDATE $dbtable SET status=4 WHERE sample='$sample'"

#pure data quality check
mkdir -p fastqc_after_trimmomatic
mkdir -p multiqc_after_trimmomatic
fastqc cleandata/*.fastq -t $threads -o fastqc_after_trimmomatic/
multiqc -d fastqc_after_trimmomatic/ -o multiqc_after_trimmomatic/
echo 'upload pure data quality check results'
aws s3 sync fastqc_after_trimmomatic ${results_path}/${sample}/fastqc_after_trimmomatic/ --storage-class ${storage_class}
aws s3 sync multiqc_after_trimmomatic ${results_path}/${sample}/multiqc_after_trimmomatic/ --storage-class ${storage_class}
time2=`date +%s`
interval=`expr $time2 - $time1`
aws dynamodb execute-statement --statement "UPDATE $dbtable SET status=5, qc_time=$interval WHERE sample='$sample'"

echo 'delete local results'
rm rawdata -rf
rm fastqc_before_trimmomatic -rf
rm multiqc_before_trimmomatic -rf
rm cleandata -rf
rm fastqc_after_trimmomatic -rf
rm multiqc_after_trimmomatic -rf
echo 'done'
```
### 2.2 Mix-assembly

Batch processing through Amazon Web Services (AWS)
All clean metagenomic data are stored in the "metagenome/results/qc" folder on the AWS cloud platform for analysis.
```sh
echo 'assembly sample: '$1', threads: '$2, 'memory: '$3, 'type: '$4, 'bucket: '$5, 'dbtable: '$6
. /opt/miniconda/etc/profile.d/conda.sh
conda activate metawrap-env

sample=$1
threads=$2
memory=$3
type=$4
bucket=$5
dbtable=$6

storage_class=INTELLIGENT_TIERING
s3_mount_point=/s3

echo 'mount s3 bucket'
mkdir -p $s3_mount_point
goofys --region cn-northwest-1 $bucket $s3_mount_point
base_dir=$s3_mount_point/metagenome
qc_results=$base_dir/results/qc
ls -lh $qc_results

aws dynamodb execute-statement --statement "UPDATE $dbtable SET status=1 WHERE sample='$sample'"
time1=`date +%s`
case "$type" in
    # 1)
    #     echo "Single sample assembly"
    #     #sample=mud01.2020.11.S
    #     sample_prefix=${qc_results}/$sample/cleandata/$sample.paired
    #     sample_r1=${sample_prefix}.R_1.fastq
    #     sample_r2=${sample_prefix}.R_2.fastq
    #     assembly_dir=sig_assembly
    #     ;;
    3)
        echo "Mixed assembly of 3 samples"
        #sample=mud01.2020.11 or sample=sand01.2020.11.D
        sample1_prefix=${qc_results}/${sample}.S/cleandata/$sample.S.paired
        sample2_prefix=${qc_results}/${sample}.Z/cleandata/$sample.Z.paired
        sample3_prefix=${qc_results}/${sample}.X/cleandata/$sample.X.paired
        sample_r1="${sample1_prefix}.R_1.fastq,${sample2_prefix}.R_1.fastq,${sample3_prefix}.R_1.fastq"
        sample_r2="${sample1_prefix}.R_2.fastq,${sample2_prefix}.R_2.fastq,${sample3_prefix}.R_2.fastq"
        assembly_dir=mix3_assembly
        ;;
    # 9)
    #     echo "Mixed assembly of 9 samples"
    #     #sample=sand01.2020.11
    #     sample1_prefix=${qc_results}/${sample}.G.S/cleandata/$sample.G.S.paired
    #     sample2_prefix=${qc_results}/${sample}.G.Z/cleandata/$sample.G.Z.paired
    #     sample3_prefix=${qc_results}/${sample}.G.X/cleandata/$sample.G.X.paired
    #     sample4_prefix=${qc_results}/${sample}.Z.S/cleandata/$sample.Z.S.paired
    #     sample5_prefix=${qc_results}/${sample}.Z.Z/cleandata/$sample.Z.Z.paired
    #     sample6_prefix=${qc_results}/${sample}.Z.X/cleandata/$sample.Z.X.paired
    #     sample7_prefix=${qc_results}/${sample}.D.S/cleandata/$sample.D.S.paired
    #     sample8_prefix=${qc_results}/${sample}.D.Z/cleandata/$sample.D.Z.paired
    #     sample9_prefix=${qc_results}/${sample}.D.X/cleandata/$sample.D.X.paired
    #     sample_r1="${sample1_prefix}.R_1.fastq,${sample2_prefix}.R_1.fastq,${sample3_prefix}.R_1.fastq,${sample4_prefix}.R_1.fastq,${sample5_prefix}.R_1.fastq,${sample6_prefix}.R_1.fastq,${sample7_prefix}.R_1.fastq,${sample8_prefix}.R_1.fastq,${sample9_prefix}.R_1.fastq"
    #     sample_r2="${sample1_prefix}.R_2.fastq,${sample2_prefix}.R_2.fastq,${sample3_prefix}.R_2.fastq,${sample4_prefix}.R_2.fastq,${sample5_prefix}.R_2.fastq,${sample6_prefix}.R_2.fastq,${sample7_prefix}.R_2.fastq,${sample8_prefix}.R_2.fastq,${sample9_prefix}.R_2.fastq"
    #     assembly_dir=mix9_assembly
    #     ;;
    *)
        echo "type incorrect"
        exit 1
        ;;
esac

echo 'metawrap assembly '
mkdir -p ${assembly_dir}
metawrap assembly -t $threads -m $memory --megahit -o ${assembly_dir}/$sample -1 ${sample_r1} -2 ${sample_r2}

echo ${assembly_dir}
aws s3 sync ${assembly_dir}/$sample/ s3://$bucket/metagenome/results/${assembly_dir}/$sample/ --storage-class ${storage_class}

time2=`date +%s`
interval=`expr $time2 - $time1`
aws dynamodb execute-statement --statement "UPDATE $dbtable SET status=2, assembly_time=$interval WHERE sample='$sample'"

echo "delete local files"
rm ${assembly_dir} -rf

# echo "submit metawrap binning job"
# script=/scripts/metawrap-binning.sh
# threads=32
# memory=58
# jobqueue='q-metawrap-binning'
# jobdef='jd-metawrap-binning:3'
# jobname=$dbtable-${sample//./_}-$threads
# aws batch submit-job --job-name $jobname --job-queue $jobqueue --job-definition $jobdef --parameters script=$script,sample=$sample,threads=$threads,memory=$memory,type=$type,bucket=$bucket,dbtable=$dbtable

echo 'done'
```
### 2.3 Binning and Bin refinement

Batch processing through Amazon Web Services (AWS)
All assembly contigs are stored in the "$base_dir/results/mix3_assembly" folder on the AWS cloud platform for analysis.
```sh
echo 'binning sample: '$1', threads: '$2, 'memory: '$3, 'type: '$4, 'bucket: '$5, 'dbtable: '$6
. /opt/miniconda/etc/profile.d/conda.sh
conda activate metawrap-env

sample=$1
threads=$2
memory=$3
type=$4
bucket=$5
dbtable=$6

storage_class=INTELLIGENT_TIERING
s3_mount_point=/s3

echo 'mount s3 bucket'
mkdir -p $s3_mount_point
goofys --region cn-northwest-1 $bucket $s3_mount_point
base_dir=$s3_mount_point/metagenome
ls -lh $base_dir
qc_results=$base_dir/results/qc

echo 'copy ref data'
s3_refdata_bucket=sio
s3_refdata_mount_point=/sio
mkdir -p $s3_refdata_mount_point
goofys --region cn-northwest-1 $s3_refdata_bucket $s3_refdata_mount_point
mkdir -p /opt/metaWRAP_db/MY_CHECKM
cp ${s3_refdata_mount_point}/ref_data/checkm_data/* /opt/metaWRAP_db/MY_CHECKM/ -rf

aws dynamodb execute-statement --statement "UPDATE $dbtable SET status=3 WHERE sample='$sample'"
time1=`date +%s`

case "$type" in
    # 1)
    #     sample_prefix=${qc_results}/$sample/cleandata/$sample
    #     samples="${sample_prefix}.*.fastq"
    #     assembly_dir=$base_dir/results/sig_assembly
    #     binning_dir=sig_binning
    #     refine_dir=sig_refinement
    #     ;;
    3)
        sample1_prefix=${qc_results}/${sample}.S/cleandata/$sample
        sample2_prefix=${qc_results}/${sample}.Z/cleandata/$sample
        sample3_prefix=${qc_results}/${sample}.X/cleandata/$sample
        samples="${sample1_prefix}.*.fastq ${sample2_prefix}.*.fastq ${sample3_prefix}.*.fastq"
        assembly_dir=$base_dir/results/mix3_assembly
        binning_dir=mix3_binning
        refine_dir=mix3_refinement
        ;;
    # 9)
    #     sample1_prefix=${qc_results}/${sample}.G.S/cleandata/$sample
    #     sample2_prefix=${qc_results}/${sample}.G.Z/cleandata/$sample
    #     sample3_prefix=${qc_results}/${sample}.G.X/cleandata/$sample
    #     sample4_prefix=${qc_results}/${sample}.Z.S/cleandata/$sample
    #     sample5_prefix=${qc_results}/${sample}.Z.Z/cleandata/$sample
    #     sample6_prefix=${qc_results}/${sample}.Z.X/cleandata/$sample
    #     sample7_prefix=${qc_results}/${sample}.D.S/cleandata/$sample
    #     sample8_prefix=${qc_results}/${sample}.D.Z/cleandata/$sample
    #     sample9_prefix=${qc_results}/${sample}.D.X/cleandata/$sample
    #     samples="${sample1_prefix}.*.fastq ${sample2_prefix}.*.fastq ${sample3_prefix}.*.fastq ${sample4_prefix}.*.fastq ${sample5_prefix}.*.fastq ${sample6_prefix}.*.fastq ${sample7_prefix}.*.fastq ${sample8_prefix}.*.fastq ${sample9_prefix}.*.fastq"
    #     assembly_dir=$base_dir/results/mix9_assembly
    #     binning_dir=mix9_binning
    #     refine_dir=mix9_refinement
    #     ;;
    *)
        echo "type incorrect"
        exit 1
        ;;
esac
echo ${assembly_dir}
ls -lh $assembly_dir

echo "metawrap binning..."
mkdir -p ${binning_dir}
metawrap binning --metabat2 --maxbin2 --concoct -t $threads -m $memory -a ${assembly_dir}/$sample/final_assembly.fasta -o ${binning_dir}/$sample $samples
aws s3 sync ${binning_dir}/$sample/ s3://$bucket/metagenome/results/${binning_dir}/$sample/ --storage-class ${storage_class}
time2=`date +%s`
interval=`expr $time2 - $time1`
aws dynamodb execute-statement --statement "UPDATE $dbtable SET status=4, binning_time=$interval WHERE sample='$sample'"

echo "metawrap refinement..."
mkdir -p ${refine_dir}
metawrap bin_refinement -t $threads -m $memory -o ${refine_dir}/$sample -A ${binning_dir}/$sample/concoct_bins/ -B ${binning_dir}/$sample/maxbin2_bins/ -C ${binning_dir}/$sample/metabat2_bins/ -c 50 -x 10
aws s3 sync ${refine_dir}/$sample/ s3://$bucket/metagenome/results/${refine_dir}/$sample/ --storage-class ${storage_class}
time3=`date +%s`
interval=`expr $time3 - $time2`
aws dynamodb execute-statement --statement "UPDATE $dbtable SET status=5, refinement_time=$interval WHERE sample='$sample'"

echo "delete local files"
rm ${binning_dir} -rf
rm ${refine_dir} -rf

echo 'done'
```
### 2.4 Dereplication of MAGs

Link bins from three samples into the same folder and rename (all MAGs)
```sh
for i in `aws s3 ls s3://makuojian/metagenome/results/mix3_refinement/`;do 
  aws s3 cp s3://makuojian/metagenome/results/mix3_refinement/${i}/metawrap_50_10_bins/ ${i}/ --recursive
done

for i in `ls ../01.raw_MAG`; do 
  ln -s ../01.raw_MAG/${i}/bin.* ./ 
  rename "bin" "Mix_${i}" ./bin.*
done
```
Check the number of bins from different groups
```sh
ls ./Mix_mud* | cut -f2 -d '_' | cut -f1-3 -d '.' | uniq -c | sort -n
ls ./Mix_sand* | cut -f2 -d '_' | cut -f1-4 -d '.' | uniq -c | sort -n
```
Execute dRep, 99% ANI similarity, 50% completeness, 10% contamination.
```sh
nohup dRep dereplicate 03.dreped_MAG/ -g 02.renamed_MAG/*.fa -sa 0.99 -comp 50 -con 10 -nc 0.30 -p 32 -d > drep.log 2>&1 &
```
### 2.5 Quantification of MAGs using coverm for relative abundance

cd /home/ec2-user/zhoushan/metagenome/04quantify_MAG












