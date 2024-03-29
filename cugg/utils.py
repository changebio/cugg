# AUTOGENERATED! DO NOT EDIT! File to edit: nbs/06_SNPmatch.ipynb (unless otherwise specified).

__all__ = ['shorten_id', 'check_indels', 'load_yaml', 'parse_input', 'match_ss_with_bim', 'check_ss', 'compare_snps',
           'allele_match', 'check_ss1', 'pair_match', 'strand_flip', 'namebyordA0_A1', 'snps_match', 'snps_match_dup',
           'snps_match_nodup']

# Cell
from xxhash import xxh32 as xxh

# Cell
def shorten_id(x):
    return x if len(x) < 30 else f"{x.split('_')[0]}_{xxh(x).hexdigest()}"

# Cell
import pandas as pd
import numpy as np
from Bio.Seq import Seq
import warnings
import yaml
import glob

# Cell
def check_indels(query):
    #check duplicated indels and remove them.
    indels = query.index.duplicated(keep=False)
    if(indels.any()):
        warnings.warn("There are SNPs {}: REF:ALT = ALT:REF. They will be removed.".format(sum(indels)))
        query = query[~indels]
    return query

def load_yaml(yaml_file):
    with open(yaml_file, "r") as stream:
        try:
            yml = yaml.safe_load(stream)
        except yaml.YAMLError as exc:
            print(exc)
    return yml

def parse_input(yml_input):
    input_dict = {}
    for i in yml_input:
        for name in glob.glob(list(i.keys())[0]):
            input_dict[name] = list(i.values())[0].copy()
    return input_dict

# Cell
def match_ss_with_bim(query,subject):
    '''snp match case in one dataset'''
    query = query.itertuples()
    subject = subject.itertuples()
    qi,si = next(query,None),next(subject,None)
    flip=[]
    while(qi and si):
        if qi.CHR>si.chrom:
            si = next(subject,None)
            continue
        elif qi.CHR<si.chrom:
            raise Exception(qi,'is not in genodata')
        else:
            if qi.POS>si.pos:
                si = next(subject,None)
                continue
            elif qi.POS<si.pos:
                raise Exception(qi,'is not in genodata')
            else:
                #Fix me
                #same pos has multiple snps
                #query compare with each of them in subject
                if qi.ALT == si.a1 and qi.REF == si.a0:
                    flip.append(False)
                elif qi.ALT == si.a0 and qi.REF == si.a1:
                    flip.append(True)
                else:
                    si = next(subject,None)
                    continue
                qi = next(query,None)
                si = next(subject,None)
    return flip

# Cell
def check_ss(ss,bim):
    ss.CHR = ss.CHR.astype(int)
    bim.chrom = bim.chrom.astype(int)
    flip = np.array(match_ss_with_bim(ss,bim))
    print('Total SNPs',len(flip),'. Flip SNPs',sum(flip))
    #shift ref and alt for fliped snps and change snp's name and the sign of beta
    if flip.any():
        fss = ss[flip]
        ref = fss.ALT.copy()
        alt = fss.REF.copy()
        fss.REF = ref
        fss.ALT =alt
        fss.SNP = 'chr'+fss[['CHR','POS','REF','ALT']].astype(str).agg(':'.join, axis=1)
        fss.BETA = -fss.BETA
        ss = pd.concat([ss[~flip],fss]).sort_index()
    return ss

# Cell
def compare_snps(query,subject,only_match=True):
    '''
    input: query and subject, two data frame with the first five column: chr, pos, snp, a0, a1
    output: data frame included six boolean columns (keep,exact,flip,reverse,both, complement) and two columns of the index query and subject.
    '''
    smry = []
    query = query.itertuples()
    subject = subject.itertuples()
    pre_s = None
    qi,si = next(query,None),next(subject,None)
    multi_snps = []
    while(qi and si):
        if qi[1]>si[1]:
            si = next(subject,None)
        elif qi[1]<si[1]:
            smry.append([False]*5+[qi[0],-1])
            qi = next(query,None)
        else:
            if qi[2]>si[2]:
                si = next(subject,None)
            elif qi[2]<si[2]:
                smry.append([False]*5+[qi[0],-1])
                qi = next(query,None)
            else:
                #same pos has multiple snps
                #query compare with each of them in subject
                multi_snps.append(si)
                smry.append(allele_match(qi[3],qi[4],si[3],si[4])+[qi[0],si[0]])
                pre_s = si
                si = next(subject,None)
                if si is None or si[2] != pre_s[2]:
                    qi = next(query,None)
                    while(qi is not None and qi[2]==pre_s[2]):
                        for s in multi_snps:
                            smry.append(allele_match(qi[3],qi[4],s[3],s[4])+[qi[0],s[0]])
                        qi = next(query,None)
                    multi_snps = []

    while(qi):
        smry.append([False]*5+[qi[0],-1])
        qi = next(query,None)
    smry = pd.DataFrame(smry,columns=['keep','exact','flip','reverse','ambiguous','qidx','sidx'])
    #print(smry.iloc[:,:5].groupby(['keep','exact','flip','reverse','ambiguous']))
    if only_match:
        smry = smry[smry.keep==True]
    return smry
def allele_match(a0,a1,ref0,ref1):
    '''
    input: a0 and a1 are the first snp, ref0 and ref1 are the second snp.
    output: keep,exact,flip,reverse,both, complement. boolean values.
    '''
    keep,exact,flip,reverse=False,False,False,False
     # reverse chain for multi base?
    ca0,ca1 = Seq(a0).reverse_complement(),Seq(a1).reverse_complement()
    if a0==ref0 and a1==ref1:
        exact=True
        keep=True
    elif a0==ref1 and a1==ref0:
        flip=True
        keep=True

    if ca0==ref0 and ca1==ref1:
        reverse = True
        keep=True
    elif ca0==ref1 and ca1==ref0:
        flip=True
        reverse = True
        keep=True
    return [keep,exact,flip,reverse,a0==ca1]

# Cell
def check_ss1(ss,bim,keep_ambiguous=True):
    '''index by chr+por+ordered ref and alt'''
    ss.index = namebyordA0_A1(ss[['CHR','POS','REF','ALT']])
    bim.index = namebyordA0_A1(bim[['chrom','pos', 'a0', 'a1']])
    # SNPs in bim should include all SNPs in ss
    if(not ss.index.isin(bim.index).all()):
        raise Exception("some SNPs in sumstat file are not in the bim file")
    #check duplicated index and remove them.
    if(bim.index.duplicated().any() or ss.index.duplicated().any()):
        warnings.warn("There are SNPs: REF:ALT = ALT:REF. They will be removed")
        bim = bim[~bim.index.duplicated(keep=False)]
    bim = bim[bim.index.isin(ss.index)]
    ss = ss.loc[bim.index]
    if(ss.shape[0]!=bim.shape[0]):
        raise Exception("Sumstas and genotype are not match with each other.")
    print("Paired SNPs",ss.shape[0])
    #input paired ss and bim
    pm = pair_match(ss.REF,ss.ALT,bim.a0,bim.a1)
    if keep_ambiguous:
        print('Warning: there are',sum(pm.ambiguous),'ambiguous SNPs')
        pm = pm.iloc[:,1:]
    else:
        pm = pm[~pm.ambiguous].iloc[:,1:]
    keep_idx = pm.any(axis=1)
    keep_idx = keep_idx.index[keep_idx==True]
    print("Overlap SNPs",len(keep_idx))
    #overlap snps by chr+pos+alleles.
    new_subject = bim.loc[keep_idx][['chrom','pos', 'a0', 'a1','snp']]
    new_subject.columns = ['CHR','POS','REF','ALT','SNP']
    #update beta and snp info
    new_query = pd.concat([new_subject.iloc[:,:5],ss.loc[keep_idx].iloc[:,5:]],axis=1)
    new_query.BETA[pm.sign_flip] = -new_query.BETA[pm.sign_flip]
    return new_query

# Cell
def pair_match(a1,a2,ref1,ref2):
    # a1 and a2 are the first data-set
    # ref1 and ref2 are the 2nd data-set
    # Make all the alleles into upper-case, as A,T,C,G:
    a1 = a1.str.upper()
    a2 = a2.str.upper()
    ref1 = ref1.str.upper()
    ref2 = ref2.str.upper()
    # Strand flip, to change the allele representation in the 2nd data-set
    flip1 = ref1.apply(strand_flip)
    flip2 = ref2.apply(strand_flip)
    result = {}
    result["ambiguous"] = ((a1=="A") & (a2=="T")) | ((a1=="T") & (a2=="A")) | ((a1=="C") & (a2=="G")) | ((a1=="G") & (a2=="C"))
    # as long as scenario 1 is involved, sign_flip will return TRUE
    result["sign_flip"] = ((a1==ref2) & (a2==ref1)) | ((a1==flip2) & (a2==flip1))
    # as long as scenario 2 is involved, strand_flip will return TRUE
    result["strand_flip"] = ((a1==flip1) & (a2==flip2)) | ((a1==flip2) & (a2==flip1))
    # remove other cases, eg, tri-allelic, one dataset is A C, the other is A G, for example.
    result["exact_match"] = ((a1 == ref1) & (a2 == ref2))
    return pd.DataFrame(result)
def strand_flip(s):
    return ''.join(Seq(s).reverse_complement())
def namebyordA0_A1(df,cols=['CHR','POS','A0','A1']):
    df.columns = cols
    prefix = df[[x for x in cols if x not in ['CHR','POS','A0','A1']]+['CHR','POS']].astype(str).agg(':'.join, axis=1)
    names = []
    for p,A0,A1 in zip(prefix,df.A0,df.A1):
        tmp = A0+':'+A1 if A0 > A1 else A1 +':'+ A0
        names.append('_'.join([p,tmp]))
    return names

# Cell
def snps_match(query,subject,keep_ambiguous=True):
    print("Total rows of query: ",query.shape[0],"Total rows of subject: ",subject.shape[0])
    if len(query.index[0].split('_')[0].split(':'))>2:
        #gene:chr:pos case
        genes_query = query.index.to_series().apply(lambda x: x.split('_')[0])
        genes_subject = subject.index.to_series().apply(lambda x: x.split('_')[0])
        query = dict(tuple(query.groupby(genes_query)))
        subject = dict(tuple(subject.groupby(genes_subject)))
        new_query, new_subject = [],[]
        for g in genes_query.unique():
            q = query.get(g)
            s = subject.get(g)
            if q is not None and s is not None:
                new_q, new_s=snps_match_dup(q,s,keep_ambiguous)
                new_query.append(new_q)
                new_subject.append(new_s)
        new_query, new_subject=pd.concat(new_query),pd.concat(new_query)
    else:
        #chr:pos case
        new_query, new_subject=snps_match_dup(query,subject,keep_ambiguous)
    return new_query, new_subject

# Cell
def snps_match_dup(query,subject,keep_ambiguous=True):
    pm = compare_snps(query,subject)
    if not keep_ambiguous:
        pm = pm[~pm.ambiguous]
    new_subject = subject.loc[pm.sidx]
    #update beta and snp info
    new_query = pd.concat([new_subject.iloc[:,:5],query.loc[pm.qidx].iloc[:,5:]],axis=1)
    new_query.STAT[list(pm.flip)] = -new_query.STAT[list(pm.flip)]
    return new_query, new_subject

def snps_match_nodup(query,subject,keep_ambiguous=True):
    #overlap snps by chr+pos
    print("Total rows of query: ",query.shape[0],"Total rows of subject: ",subject.shape[0])
    subject = subject[subject.index.isin(query.index)]
    query = query.loc[subject.index]
    print("Overlap chr:pos",query.shape[0])
    if query.index.duplicated().any():
        raise Exception("There are duplicated chr:pos")
    pm = pair_match(query.A1,query.A0,subject.A1,subject.A0)
    if keep_ambiguous:
        print('Warning: there are',sum(pm.ambiguous),'ambiguous SNPs')
        pm = pm.iloc[:,1:]
    else:
        pm = pm[~pm.ambiguous].iloc[:,1:]
    keep_idx = pm.any(axis=1)
    keep_idx = keep_idx.index[keep_idx==True]
    print("Overlap SNPs",len(keep_idx))
    #overlap snps by chr+pos+alleles.
    new_subject = subject.loc[keep_idx]
    #update beta and snp info
    new_query = pd.concat([new_subject.iloc[:,:5],query.loc[keep_idx].iloc[:,5:]],axis=1)
    new_query.STAT[pm.sign_flip] = -new_query.STAT[pm.sign_flip]
    return new_query,new_subject