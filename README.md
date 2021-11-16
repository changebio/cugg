# Scalable pipeline for computing LD matrix in big sample phenotype



### 4 modules
- Genodata
- Sumstats
- Liftover
- LDmatrix

## Install

`pip install LDtools`

## How to use

```python
lf = Liftover('hg38','hg19')
```

```python
vcf ='/home/yh3455/Github/SEQLinkage/MWE/small_sample_ii_coding.vcf.gz'
```

```python
lf.vcf_liftover(vcf)
```