# AUTOGENERATED! DO NOT EDIT! File to edit: nbs/01_Sumstat.ipynb (unless otherwise specified).

__all__ = ['p2z', 'Sumstat', 'read_sumstat']

# Cell
import yaml
import numpy as np
import pandas as pd
from scipy.stats import norm
from .utils import *

# Cell
def p2z(pval,beta,twoside=True):
    if twoside:
        pval = pval/2
    z=np.abs(norm.ppf(pval))
    ind=beta<0
    z[ind]=-z[ind]
    return z

class Sumstat:
    def __init__(self,sumstat_path,config_file=None,rename=True):
        self.ss = self.read_sumstat(sumstat_path,config_file,rename)

    def __repr__(self):
        return "sumstat:% s" % (self.ss)

        #functions to read sumstats
    def read_sumstat(self,file, config_file,rename):
        if config_file is not None:
            config_file = yaml.safe_load(open(config_file, 'r'))
        return read_sumstat(file,config_file,rename)

    def extractbyregion(self,region):
        sumstats = self.ss
        idx = (sumstats.CHR == region[0]) & (sumstats.POS >= region[1]) & (sumstats.POS <= region[2])
        print('this region',region,'has',sum(idx),'SNPs in Sumstat')
        self.ss = sumstats[idx]

    def extractbyvariants(self,variants,notin=False):
        idx = self.ss.SNP.isin(variants)
        if notin:
            idx = idx == False
        #update sumstats
        self.ss = self.ss[idx]

    def calculateZ(self):
        self.ss['Z'] = list(p2z(self.ss.P,self.ss.BETA))

    def match_ss(self,bim):
        self.ss = check_ss1(self.ss,bim)



# Cell
def read_sumstat(file, config,rename=True):
    try:
        sumstats = pd.read_csv(file, compression='gzip', header=0, sep='\t', quotechar='"')
    except:
        sumstats = pd.read_csv(file, header=0, sep='\t', quotechar='"')
    if config is not None:
        try:
            ID = config.pop('ID').split(',')
            sumstats = sumstats.loc[:,list(config.values())]
            sumstats.columns = list(config.keys())
            sumstats.index = namebyordA0_A1(sumstats[ID],cols=ID)
        except:
            raise ValueError(f'According to config_file, input summary statistics should have the following columns: %s' % list(config.values()))
        sumstats.columns = list(config.keys())
    if rename:
        sumstats.SNP = 'chr'+sumstats.CHR.astype(str) + ':' + sumstats.POS.astype(str) + ':' + sumstats.A0.astype(str) + ':' + sumstats.A1.astype(str)
    sumstats.CHR = sumstats.CHR.astype(int)
    sumstats.POS = sumstats.POS.astype(int)
    return sumstats