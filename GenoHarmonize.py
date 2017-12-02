def HarmonizeWith1000G(geno_name):
    # Using 1000 Genomes as a reference(based off Perl script by W.Rayner, 2015, wrayner @ well.ox.ac.uk)
    #   -Removes SNPs with MAF < 5% in study dataset
    #   -Removes SNPs not in 1000 Genomes Phase 3
    #   -Removes all A/T G/C SNPs with MAF > 40% in the reference data set
    #   -Removes all SNPs with an AF difference >0.2, between reference and dataset frequency file, frequency file is
    #         expected to be a plink frequency file with the same number of SNPs as the bim file
    #   -Removes duplicates that may be introduced with the position update
    #   -Removes indels #Need to figure out how to do this. Or even if it is necessary with plink files.
    #   -Removes SNPs with HWE p-value < 0.01
    #   -Updates the reference allele to match 1000G
    #   -Outputs new files per chromosome, in vcf and plink bed/bim/fam format.

    #Needed modules
    import os
    import shutil
    import glob
    import sys
    import pandas as pd
    import numpy as np
    import zipfile
    import urllib.request
    import ftplib

    # Get current working directory.
    orig_wd = os.getcwd()

###Getting require reference files and genotype harmonizer program###
    #Ask the user if they already have the 1000G Phase 3 vcf files.
    vcf_exists = input('\u001b[34;1m Have you already downloaded the 1000G Phase3 VCF files? (y/n): \u001b[0m').lower()

    if vcf_exists in ('y', 'yes'):
        #Getting user's path to VCF files
        vcf_path = input('\u001b[34;1m Please enter the pathname of where your 1000G vcf files are '
                         '(i.e. C:\\Users\\Julie White\\Box Sync\\1000GP\\VCF\\ etc.): \u001b[0m')

        # List of VCF files that we're going to need.
        vcf_file_names = ['ALL.chr%d.phase3_shapeit2_mvncall_integrated_v5a.20130502.genotypes.vcf.gz' % x for x in
                          range(1, 23)]
        vcf_file_names.extend(['ALL.chrX.phase3_shapeit2_mvncall_integrated_v1b.20130502.genotypes.vcf.gz'])

    elif vcf_exists in ('n', 'no'):
        print('Downloading 1000G Phase 3 VCF files now, putting them in "1000G_Phase3_VCF" folder. This might take a while.')

        #Create folder:
        if not os.path.exists('1000G_Phase3_VCF'):
            os.makedirs('1000G_Phase3_VCF')

        #List of VCF files that we're going to need.
        vcf_file_names = ['ALL.chr%d.phase3_shapeit2_mvncall_integrated_v5a.20130502.genotypes.vcf.gz' % x for x in range(1, 23)]
        vcf_file_names.extend(['ALL.chrX.phase3_shapeit2_mvncall_integrated_v1b.20130502.genotypes.vcf.gz'])

        #Open ftp connection
        ftp = ftplib.FTP('ftp.1000genomes.ebi.ac.uk')
        ftp.login()
        ftp.cwd('/vol1/ftp/release/20130502/')

        #Download files and put them in 1000G_Phase3_VCF folder.
        for filename in vcf_file_names:
            local_filename = os.path.join(os.getcwd(), '1000G_Phase3_VCF', filename)
            file = open(local_filename, 'wb')
            ftp.retrbinary('RETR ' + filename, file.write)
            file.close()
        #Once we are done downloading, close the connection to the ftp server.
        ftp.quit()

        #Saving VCF path
        vcf_path = os.path.join(os.getcwd(), '1000G_Phase3_VCF')

    else:
        sys.exit("Please answer yes or no. Quitting now because no VCF files.")

    #Ask the uer if they alraedy have the 1000G Phase 3 Hap/Legend/Sample files.
    legend_exists = input('\u001b[35;1m Have you already downloaded the 1000G Phase 3 Hap/Legend/Sample files? (y/n): \u001b[0m').lower()

    if legend_exists in ('y', 'yes'):
        #Ask the user where the Legend files are.
        legend_path = input('\u001b[35;1m Please enter the pathname of where your 1000G legend files are '
                            '(i.e. C:\\Users\\Julie White\\Box Sync\\1000GP\\ etc.): \u001b[0m')
        #List of legend file names that we're going to need.
        legend_file_names = ['1000GP_Phase3_chr%d.legend.gz' % x for x in range(1, 23)]
        legend_file_names.extend(['1000GP_Phase3_chrX_NONPAR.legend'])

    elif legend_exists in ('n', 'no'):
        print('Downloading 1000G Phase 3 legend files now, putting them in "1000G_Phase3_HapLegendSample" folder. '
              'This might take a while.')

        # Create folder:
        if not os.path.exists('1000G_Phase3_HapLegendSample'):
            os.makedirs('1000G_Phase3_HapLegendSample')

            # List of legend file names that we're going to need.
            legend_file_names = ['1000GP_Phase3_chr%d.legend.gz' % x for x in range(1, 23)]
            legend_file_names.extend(['1000GP_Phase3_chrX_NONPAR.legend'])

            legend_server = "http://mathgen.stats.ox.ac.uk/impute/1000GP_Phase3/"

            # Download files and put them in 1000G_Phase3_VCF folder.
            for filename in legend_file_names:
                urllib.request.urlretrieve(os.path.join(legend_server, filename), os.path.join(os.getcwd(),'1000G_Phase3_HapLegendSample', filename))

        # Saving legend path
        legend_path = os.path.join(os.getcwd(), '1000G_Phase3_HapLegendSample')
    else:
        sys.exit('Please answer yes or no. Quitting now because no legend files.')

    #Ask if they have genotype harmonizer.
    harmonizer_exists = input('\u001b[32;1m Have you already downloaded Genotype Harmonizer? (y/n): \u001b[0m').lower()
    if harmonizer_exists in ('y', 'yes'):
        #Ask the user where genotype harmonizer is.
        harmonizer_path = input('\u001b[34;1m Please enter the pathname of where the Genotype Harmonizer folder is '
                                '(i.e. C:\\Users\\Julie White\\Box Sync\\Software\\GenotypeHarmonizer-1.4.20\\): \u001b[0m')

    elif harmonizer_exists in ('n', 'no'):
        print('\u001b[36;1m Downloading genotype harmonizer now. \u001b[0m')
        #Download genotype harmonizer zip file
        urllib.request.urlretrieve('http://www.molgenis.org/downloads/GenotypeHarmonizer/GenotypeHarmonizer-1.4.20-dist.zip', 'GenotypeHarmonizer-1.4.20.zip')
        #Unzip Genotype Harmonizer
        zip_ref = zipfile.ZipFile('GenotypeHarmonizer-1.4.20.zip', 'r')
        zip_ref.extractall('GenotypeHarmonizer-1.4.20')
        zip_ref.close()
        #Harmonize path now that we've downloaded it.
        harmonizer_path = os.path.join(os.getcwd(),'GenotypeHarmonizer-1.4.20/GenotypeHarmonizer-1.4.20-SNAPSHOT/')

    else:
        sys.exit('\u001b[36;1m Please write yes or no. Quitting now because no Genotype Harmonizer. \u001b[0m')

###Start harmonization###
    #Make new folder where the harmonized files will be located.
    if not os.path.exists('Harmonized_To_1000G'):
        os.makedirs('Harmonized_To_1000G')

    #Copy genotype files to new folder.
    shutil.copy2(geno_name + '.bed', 'Harmonized_To_1000G')
    shutil.copy2(geno_name + '.bim', 'Harmonized_To_1000G')
    shutil.copy2(geno_name + '.fam', 'Harmonized_To_1000G')

    #Copy plink to new folder.
    if not glob.glob(r'plink*'):
        sys.exit("We need plink to run this part of the script. Please run step 1 if you do not have plink, or make sure"
                 " that it is in this directory.")
    else:
        for file in glob.glob(r'plink*'):
            print(file)
            shutil.copy(file, 'Harmonized_To_1000G')

    #Switch to this directory.
    os.chdir('Harmonized_To_1000G')

    #Make the lists that we're going to need, since this is on a per chromosome basis.
    harmonized_geno_names = [geno_name + '_chr%d_Harmonized' % x for x in range(1, 24)]
    freq_file_names = [geno_name + '_chr%d_Harmonized.frq' % x for x in range(1,24)]
    AF_diff_removed_by_chr = ['chr%d_SNPsRemoved_AFDiff' % x for x in range(1,24)]
    final_snp_lists_by_chr = ['chr%d_SNPsKept' % x for x in range(1,24)]
    AF_checked_names = [geno_name + '_chr%d_HarmonizedTo1000G' % x for x in range(1,24)]

    '''
    #Harmonize for each chromosome
    for i in range(0, len(vcf_file_names)):
        #Call genotype harmonizer for autosomes
        if i < 22:
            os.system('java -Xmx1g -jar "' + harmonizer_path + '/GenotypeHarmonizer.jar" $* '
                      '--input ' + geno_name +
                      ' --ref "' + os.path.join(vcf_path,vcf_file_names[i]) +
                      '" --refType VCF '
                      '--chrFilter ' + str(i + 1) +
                      ' --hweFilter 0.01 '
                      '--mafFilter 0.05 '
                      '--update-id '
                      '--debug '
                      '--mafAlign 0 '
                      '--update-reference-allele '
                      '--outputType PLINK_BED '
                      '--output ' + harmonized_geno_names[i])

        elif i == 22:
            # Since chr X is labeled as 23 in the plink files and X in the vcf files, we need to separate it out and convert the 23 to X before harmonizing
            os.system('plink --bfile ' + geno_name + ' --chr X --make-bed --out ' + geno_name + '_chr23')
            #Read chrX file into plink
            bim_file = pd.read_csv(geno_name + '_chr23.bim', sep='\t', header=None)
            #Replace '23' with 'X', which is how genotype harmonizer calls X
            bim_file.iloc[:, 0].replace(23, 'X', inplace=True)
            #Write new genotype
            bim_file.to_csv(geno_name + '_chr23.bim', sep='\t', header=False, index=False, na_rep='NA')
            #Call genotype harmonizer for X chromosome.
            os.system('java -Xmx1g -jar "' + harmonizer_path + '/GenotypeHarmonizer.jar" $* '
                      '--input ' + geno_name + '_chr23'
                      ' --ref "' + os.path.join(vcf_path,vcf_file_names[i]) +
                      '" --refType VCF '
                      '--hweFilter 0.01 '
                      '--mafFilter 0.05 '
                      '--update-id '
                      '--debug '
                      '--mafAlign 0 '
                      '--update-reference-allele '
                      '--outputType PLINK_BED '
                      '--output ' + harmonized_geno_names[i])
        else:
            sys.exit("\u001b[36;1m Something is wrong with the number/name of reference files \u001b[0m")
    '''
    # Now for each that was just harmonized, remove all SNPs with an allele (AF) difference > 0.2 since we are going to use a global reference population
    # between study dataset and all superpopulation allele frequencies. IF within 0.2 of any superpopulation frequency,
    # keep variant. Frequency file is expected to be a Plink frequency file with the same number of variants as the bim file.
    for i in range(0, len(harmonized_geno_names)):
        #Create plink file
        os.system('plink --bfile ' + harmonized_geno_names[i] + ' --freq --out ' + harmonized_geno_names[i])
        #Read freq file into python
        freq_file = pd.read_csv(freq_file_names[i], sep='\s+', header = 0, usecols = [0,1,2,3,4],
                                dtype = {'CHR': int, 'SNP': str, 'A1': str, 'A2': str, 'MAF':float})
        #Rename columns of freq file.
        freq_file.rename(columns={'A1': 'dataset_a1', 'A2': 'dataset_a2', 'MAF': 'dataset_a1_frq'}, inplace=True)
        #Calculate the frequency of the second allele, since it's not given in the freq file.
        freq_file['dataset_a2_frq'] = 1-freq_file['dataset_a1_frq']
        #Read in bim file.
        bim_file = pd.read_csv(harmonized_geno_names[i] + '.bim', sep='\s+', header=None, usecols=[0, 1, 3],
                               names=['CHR', 'SNP', 'position'])
        #Merge frequency file with bim file to get position for each SNP
        freq_file_with_position = pd.merge(left = freq_file, right = bim_file, how = 'inner', on=['CHR','SNP'])
        #Read in legend file.
        legend_file = pd.read_csv(os.path.join(legend_path,legend_file_names[i]), compression="gzip", sep=" ", header = 0,
                                  dtype={'id': str, 'position': int, 'a0': str,'a1': str, 'TYPE': str, 'AFR': float,
                                         'AMR': float, 'EAS': float, 'EUR': float, 'SAS': float, 'ALL': float})
        #Rename columns of legend file
        legend_file.rename(columns={'id': 'reference_id', 'a0': 'reference_a0', 'a1': 'reference_a1'}, inplace=True)

        #To Remove A/T or G/C SNPs in reference file that have an MAF > 40%, first identify which are AT/GC SNPs.
        legend_file['ATGC_SNP'] = np.where(((legend_file['reference_a0'] == 'A') & (legend_file['reference_a1'] == 'T')) |
                                            ((legend_file['reference_a0'] == 'T') & (legend_file['reference_a1'] == 'A')) |
                                            ((legend_file['reference_a0'] == 'C') & (legend_file['reference_a1'] == 'G')) |
                                            ((legend_file['reference_a0'] == 'G') & (legend_file['reference_a1'] == 'C')), 'ATGC', 'Fine')
        #For each superpopulation, create a new column with the MAF. If the AF in that column is less than 0.5, then
        # that is the MAF, if not then 1-AF is MAF
        legend_file['AFR_MAF'] = np.where(legend_file['AFR'] < 0.5, legend_file['AFR'], 1 - legend_file['AFR'])
        legend_file['AMR_MAF'] = np.where(legend_file['AMR'] < 0.5, legend_file['AMR'], 1 - legend_file['AMR'])
        legend_file['EAS_MAF'] = np.where(legend_file['EAS'] < 0.5, legend_file['EAS'], 1 - legend_file['EAS'])
        legend_file['EUR_MAF'] = np.where(legend_file['EUR'] < 0.5, legend_file['EUR'], 1 - legend_file['EUR'])
        legend_file['SAS_MAF'] = np.where(legend_file['SAS'] < 0.5, legend_file['AFR'], 1 - legend_file['SAS'])

        #Create column in legend file with decision about whether to keep or remove SNP, if it is an ATGC SNP where
        # the MAF in all superpopulations is greater than 40%, then remove it.
        legend_file['MAF_Decision'] = np.where((legend_file['ATGC_SNP'] == 'ATGC') & (legend_file['AFR_MAF'] > 0.4) &
                                               (legend_file['AMR_MAF'] > 0.4) & (legend_file['EAS_MAF'] > 0.4) &
                                               (legend_file['EUR_MAF'] > 0.4) & (legend_file['SAS_MAF'] > 0.4), 'Remove', 'Keep')

        #Make new legend file with just the SNPs that pass this threshold.
        legend_file = legend_file[legend_file['MAF_Decision'] == 'Keep']

        legend_file.drop(labels=['ATGC_SNP', 'AFR_MAF', 'AMR_MAF', 'EAS_MAF','EUR_MAF','SAS_MAF','MAF_Decision'], axis=1, inplace=True)

        #Merge freq file with positions with legend file to get overlap. This file contains only SNPs with matches in 1000G
        merged_file = pd.merge(left=freq_file_with_position, right=legend_file, how='inner', on='position')
        merged_file = merged_file[merged_file['TYPE'] == 'Biallelic_SNP']

        #The MAF column in the frq file is the allele frequency of the A1 allele (which is usually minor, but
        # possibly not in my case because I just updated the reference to match 1000G.
        #The AF columns in the legend file are the allele frequencies of the a1 allele in that file.
        #Need to match based on A1 alleles (hopefully this has already been done in the harmonization step, then
        # calculate the allele frequency difference.
        #For each population group, match the alleles where they aren't flipped (i.e. in the same order in house and ref datasets..
        merged_file['AFR_Match_Diff'] = np.where((merged_file['dataset_a1']==merged_file['reference_a1']) &
                                                 (merged_file['dataset_a2'] == merged_file['reference_a0']),
                                                 abs(merged_file['dataset_a1_frq'] - merged_file['AFR']),'')
        merged_file['AMR_Match_Diff'] = np.where((merged_file['dataset_a1']==merged_file['reference_a1']) &
                                                 (merged_file['dataset_a2'] == merged_file['reference_a0']),
                                                 abs(merged_file['dataset_a1_frq'] - merged_file['AMR']), '')
        merged_file['EAS_Match_Diff'] = np.where((merged_file['dataset_a1']==merged_file['reference_a1']) &
                                                 (merged_file['dataset_a2'] == merged_file['reference_a0']),
                                                 abs(merged_file['dataset_a1_frq'] - merged_file['EAS']), '')
        merged_file['EUR_Match_Diff'] = np.where((merged_file['dataset_a1']==merged_file['reference_a1']) &
                                                 (merged_file['dataset_a2'] == merged_file['reference_a0']),
                                                 abs(merged_file['dataset_a1_frq'] - merged_file['EUR']), '')
        merged_file['SAS_Match_Diff'] = np.where((merged_file['dataset_a1']==merged_file['reference_a1']) &
                                                 (merged_file['dataset_a2'] == merged_file['reference_a0']),
                                                 abs(merged_file['dataset_a1_frq'] - merged_file['SAS']), '')
        #For each population group, match the flipped alleles.
        merged_file['AFR_FlipMatch_Diff'] = np.where((merged_file['dataset_a1'] == merged_file['reference_a0']) &
                                                     (merged_file['dataset_a2'] == merged_file['reference_a1']),
                                                     abs(merged_file['dataset_a2_frq'] - merged_file['AFR']), '')
        merged_file['AMR_FlipMatch_Diff'] = np.where((merged_file['dataset_a1'] == merged_file['reference_a0']) &
                                                     (merged_file['dataset_a2'] == merged_file['reference_a1']),
                                                     abs(merged_file['dataset_a2_frq'] - merged_file['AMR']), '')
        merged_file['EAS_FlipMatch_Diff'] = np.where((merged_file['dataset_a1'] == merged_file['reference_a0']) &
                                                     (merged_file['dataset_a2'] == merged_file['reference_a1']),
                                                     abs(merged_file['dataset_a2_frq'] - merged_file['EAS']), '')
        merged_file['EUR_FlipMatch_Diff'] = np.where((merged_file['dataset_a1'] == merged_file['reference_a0']) &
                                                     (merged_file['dataset_a2'] == merged_file['reference_a1']),
                                                     abs(merged_file['dataset_a2_frq'] - merged_file['EUR']), '')
        merged_file['SAS_FlipMatch_Diff'] = np.where((merged_file['dataset_a1'] == merged_file['reference_a0']) &
                                                     (merged_file['dataset_a2'] == merged_file['reference_a1']),
                                                     abs(merged_file['dataset_a2_frq'] - merged_file['SAS']), '')
        #Add the nonflipped and flipped columns together to find out which files have an allele frequency difference > 0.2
        merged_file['AFR_Diff'] = merged_file['AFR_Match_Diff']+merged_file['AFR_FlipMatch_Diff']
        merged_file['AMR_Diff'] = merged_file['AMR_Match_Diff']+merged_file['AMR_FlipMatch_Diff']
        merged_file['EAS_Diff'] = merged_file['EAS_Match_Diff']+merged_file['EAS_FlipMatch_Diff']
        merged_file['EUR_Diff'] = merged_file['EUR_Match_Diff']+merged_file['EUR_FlipMatch_Diff']
        merged_file['SAS_Diff'] = merged_file['SAS_Match_Diff']+merged_file['SAS_FlipMatch_Diff']

        #Delete these columns because we don't need them anymore
        merged_file.drop(labels = ['AFR_Match_Diff', 'AFR_FlipMatch_Diff', 'AMR_Match_Diff', 'AMR_FlipMatch_Diff',
                                   'EAS_Match_Diff', 'EAS_FlipMatch_Diff', 'EUR_Match_Diff', 'EUR_FlipMatch_Diff',
                                   'SAS_Match_Diff', 'SAS_FlipMatch_Diff'],axis=1, inplace = True)

        #Make allele freuqency columns numeric.
        merged_file[['AFR_Diff', 'AMR_Diff', 'EAS_Diff', 'EUR_Diff', 'SAS_Diff']] = \
            merged_file[['AFR_Diff', 'AMR_Diff', 'EAS_Diff', 'EUR_Diff', 'SAS_Diff']].apply(pd.to_numeric, errors = 'coerce')

        #Make new column 'AF_Decision' where you remove alleles that have allele frequency differences > 0.2 from all population groups.
        merged_file['AF_Decision'] = np.where((merged_file['AFR_Diff'] > 0.2) & (merged_file['AMR_Diff'] > 0.2) &
                                              (merged_file['EAS_Diff'] > 0.2) & (merged_file['EUR_Diff'] > 0.2) &
                                              (merged_file['SAS_Diff'] > 0.2), 'Remove', 'Keep')

        #Drop duplicate SNPs
        merged_file.drop_duplicates(subset=['SNP'], keep = False, inplace=True)

        #Write file for each chromosome of the SNPs that we've removed in this step.
        AF_diff_removed_by_chr[i] = merged_file[merged_file['AF_Decision'] == 'Remove']

        # Make a big list of all SNPs removed and all SNPs kept just for reference purposes.
        All_SNPs_Removed = pd.concat([AF_diff_removed_by_chr[0], AF_diff_removed_by_chr[1], AF_diff_removed_by_chr[2],
                                      AF_diff_removed_by_chr[3], AF_diff_removed_by_chr[4], AF_diff_removed_by_chr[5],
                                      AF_diff_removed_by_chr[6], AF_diff_removed_by_chr[7], AF_diff_removed_by_chr[8],
                                      AF_diff_removed_by_chr[9], AF_diff_removed_by_chr[10], AF_diff_removed_by_chr[11],
                                      AF_diff_removed_by_chr[12], AF_diff_removed_by_chr[13],
                                      AF_diff_removed_by_chr[14],
                                      AF_diff_removed_by_chr[15], AF_diff_removed_by_chr[16],
                                      AF_diff_removed_by_chr[17],
                                      AF_diff_removed_by_chr[18], AF_diff_removed_by_chr[19],
                                      AF_diff_removed_by_chr[20],
                                      AF_diff_removed_by_chr[21], AF_diff_removed_by_chr[22]])
        #Write list to text file.
        All_SNPs_Removed.to_csv('SNPs_Removed_AFDiff.txt', sep='\t', header=True, index=False)

        #Write list of final SNPs that we are keeping.
        final_snp_lists_by_chr[i] = merged_file[merged_file['AF_Decision'] == 'Keep']
        #Write list for each chromosome, because we're going to use it to filter the chromosomes to create new files.
        final_snp_lists_by_chr[i]['SNP'].to_csv(final_snp_lists_by_chr[i] + '.txt', sep='\t', header=False, index=False)
        #Make one big list of all SNPs kept
        All_SNPs_Kept = pd.concat([final_snp_lists_by_chr[0], final_snp_lists_by_chr[1], final_snp_lists_by_chr[2],
                                   final_snp_lists_by_chr[3], final_snp_lists_by_chr[4], final_snp_lists_by_chr[5],
                                   final_snp_lists_by_chr[6], final_snp_lists_by_chr[7], final_snp_lists_by_chr[8],
                                   final_snp_lists_by_chr[9], final_snp_lists_by_chr[10], final_snp_lists_by_chr[11],
                                   final_snp_lists_by_chr[12], final_snp_lists_by_chr[13], final_snp_lists_by_chr[14],
                                   final_snp_lists_by_chr[15], final_snp_lists_by_chr[16], final_snp_lists_by_chr[17],
                                   final_snp_lists_by_chr[18], final_snp_lists_by_chr[19], final_snp_lists_by_chr[20],
                                   final_snp_lists_by_chr[21], final_snp_lists_by_chr[22]])
        #Write this list to a text file.
        All_SNPs_Kept.to_csv('SNPs_Kept.txt', sep='\t', header=True, index=False)

        #Make both bed and vcf files for each chromosomes. Need bed file for merging, and need vcf file for phasing
        os.system('plink --bfile ' + harmonized_geno_names[i] + ' --extract ' + final_snp_lists_by_chr[i] +
                  '.txt --recode vcf-iid bgz --make-bed --out ' + AF_checked_names[i])

        # Remove extra files that we don't need anymore. These were files that were harmonized, but not checked for allele frequency differences.
        if os.path.getsize(AF_checked_names[i] + '.bim') > 0:
            os.system('rm ' + final_snp_lists_by_chr[i] + '.txt')
            os.system('rm ' + harmonized_geno_names[i] + '.bed')
            os.system('rm ' + harmonized_geno_names[i] + '.bim')
            os.system('rm ' + harmonized_geno_names[i] + '.fam')
            os.system('rm ' + harmonized_geno_names[i] + '.log')
            os.system('rm ' + harmonized_geno_names[i] + '.frq')
            os.system('rm ' + harmonized_geno_names[i] + '.nosex')
            os.system('rm ' + harmonized_geno_names[i] + '.hh')
        #Done with one chromosome.
        print('\u001b[36;1m Finished with chr' + str(i + 1) + '\u001b[0m')

####Merge harmonized dataset genotypes####
    with open("HouseMergeList.txt", "w") as f:
        wr = csv.writer(f, delimiter="\n")
        wr.writerow(AF_checked_names)
    os.system('plink --merge-list HouseMergeList.txt --geno 0.01 --make-bed --out ' + geno_name + '_HarmonizedTo1000G')

    if os.path.getsize(geno_name + '_HarmonizedTo1000G.bim') > 0:
        for i in range(0, len(AF_checked_names)):
            os.system('rm ' + AF_checked_names[i] + '.bed')
            os.system('rm ' + AF_checked_names[i] + '.bim')
            os.system('rm ' + AF_checked_names[i] + '.fam')
            os.system('rm ' + AF_checked_names[i] + '.log')
            os.system('rm ' + AF_checked_names[i] + '.nosex')
            os.system('rm ' + AF_checked_names[i] + '.hh')
    else:
        sys.exit("\u001b[36;1m For some reason the house gentoypes did not merge. You should try it manually \u001b[0m")
'''
    shutil.copy2(geno_name + '_HarmonizedTo1000G.bed', orig_wd)
    shutil.copy2(geno_name + '_HarmonizedTo1000G.bim', orig_wd)
    shutil.copy2(geno_name + '_HarmonizedTo1000G.fam', orig_wd)
    shutil.copy2(geno_name + '_HarmonizedTo1000G.log', orig_wd)
'''