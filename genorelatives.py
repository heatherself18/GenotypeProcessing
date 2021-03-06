import platform
import os
from os.path import expanduser
home = expanduser("~")
bindir = os.path.join(home, 'software', 'bin')

# Since we use plink a lot, I'm going to go ahead and set a plink variable with the system-specific plink name.
system_check = platform.system()
if system_check in ("Linux", "Darwin"):
    plink = "plink"
    rm = "rm "
elif system_check == "Windows":
    plink = 'plink.exe'
    rm = "del "

# Determine if they have plink, if not download it.
if os.path.exists(os.path.join(bindir, plink)):
    pass
else:
    import genodownload
    genodownload.plink()


def ibd(geno_name):
    # Identity-by-descent in Plink
    # This part of the script will prune for LD, calculate IBD, and exclude individuals who have IBD < 0.2
    # The IBD results will have .genome appended to your file name. I have also included a line to convert the IBD
    # results from whitespace to tab delimited. This will have .tab.genome appended to your filename.

    # Important values of Pi-hat
    #   -First-degree relative = 0.5 (full sibs, parent-offspring)
    #   -Second-degree relative = 0.25 (half-sibs, uncle/aunt-nephew/niece, grandparent-grandchild)
    #   -Third-degree relative = 0.125 (cousins, etc.)
    #   -Fourth-degree relative = 0.0625
    #   -Fifth-degree relative = 0.03125

    # A good cutoff to use for Pi_Hat is 0.1875. This represents the halfway point between 2nd and 3rd degree relatives.
    import os
    import subprocess

    # Make a folder to put IBD calculations in
    if not os.path.exists('IBD_Calculations'):
        os.makedirs('IBD_Calculations')

    # Use plink to prune for LD
    subprocess.check_output([plink, '--bfile', geno_name, '--indep', '50', '5', '2', '--out',
                             'IBD_Calculations/' + geno_name])
    # Perform IBD calculation, filtering for a minimum of 0.1875. This is the halfway point between 2nd and 3rd degree
    # relatives.
    subprocess.check_output([plink, '--bfile', geno_name, '--exclude', 'IBD_Calculations/' + geno_name + '.prune.out',
                             '--genome', '--min', '0.1875', '--out', 'IBD_Calculations/' + geno_name])

    # Finished
    print("Analysis finished. Your IBD results will have the name " + geno_name
          + ".genome and be in the folder 'IBD_Calculations'. You should use this file to investigate your "
            "relatives and possibly update the FID and IIDs in your file.\n"
            "If you are planning on using these data for an admixture analysis you should make set lists of people who "
            "are unrelated in each set. These lists should have Family ID / Individual ID pairs, one person per line "
            "(tab or space delimited).")


def update_id(geno_name, update_id_filename):
    # File for updating FID should have four fields
    #  1) Old FID
    #  2) Old IID
    #  3) New FID
    #  4) New IID
    import subprocess

    subprocess.check_output([plink, '--bfile', geno_name, '--update-ids', update_id_filename, '--make-bed', '--out',
                             geno_name + '_IDUpdated'])
    print("Finished. Your genotype files with the ID updated will have the name " + geno_name + "_IDUpdated")


def update_parental(geno_name, update_parents_filename):
    # File for updating parents should have four fields:
    #   1) FID
    #   2) IID
    #   3) New paternal IID
    #   4) New maternal IID
    import subprocess

    subprocess.check_output([plink, '--bfile', geno_name, '--update-parents', update_parents_filename, '--make-bed',
                             '--out', geno_name + '_ParentsUpdated'])
    print("Finished. Your genotype files with parents updated will have the name " + geno_name + "_ParentsUpdated")
