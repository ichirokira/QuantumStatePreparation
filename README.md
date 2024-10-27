# QuantumStatePreparation
Inequality test-based techniques for Quantum State Preparation

## Set up

We recommend to follow the installation guides from [pyLIQTR](https://github.com/isi-usc-edu/pyLIQTR/tree/v0.3.0)
```
# Environment create
conda create -n name_env python=3.8
conda activate name_env

pip install git+https://github.com/isi-usc-edu/pyLIQTR
```

## Folder Organization

### experimental

* [fx_equals_x.py](.\experimental\fx_equals_x.py)
* [fx_equals_x2.py](.\experimental\fx_equals_x2.py)
* [__init__.py](.\experimental\__init__.py)

### modelling

* [black_box_without_arithmetic.py](.\modelling\black_box_without_arithmetic.py)
* [gaussian1D.py](.\modelling\gaussian1D.py)
* [__init__.py](.\modelling\__init__.py)

### notebooks

* [EnvelopStateforNonIncrease(Decrease)function.ipynb](.\notebooks\EnvelopStateforNonIncrease(Decrease)function.ipynb)

### results

* [fx_equals_x.csv](.\results\fx_equals_x.csv)
* [fx_equals_x.png](.\results\fx_equals_x.png)
* [fx_equals_x2.csv](.\results\fx_equals_x2.csv)
* [fx_equals_x2.png](.\results\fx_equals_x2.png)
* [fx_equal_x.csv](.\results\fx_equal_x.csv)
* [output.csv](.\results\output.csv)
* [output.png](.\results\output.png)

### utils

* [arithmetics.py](.\utils\arithmetics.py)
* [helpers.py](.\utils\helpers.py)
* [inequality_test.py](.\utils\inequality_test.py)
* [resource_estimation.py](.\utils\resource_estimation.py)
* [__init__.py](.\utils\__init__.py)


## Testing

```
python -m experimental.name_test --model regular_aa --figure output.png --rs_dir results/output.csv
```


**Example: f(x) = x**

```
# BlackBox model with regular amplitude amplification
python -m experimental.fx_equals_x --model regular_aa --figure output.png --rs_dir results/output.csv

# BlackBox model with oblivious amplitude amplification
python -m experimental.fx_equals_x --model oblivious_aa --figure output.png --rs_dir results/output.csv

# BlackBox model with square root coefficients
python -m experimental.fx_equals_x --model square_root --figure output.png --rs_dir results/output.csv
```

## Current Support
The code is based on two main papers using inequality test for state preparation:
1. [Black-box quantum state preparation without arithmetic](https://arxiv.org/abs/1807.03206)
2. (Ongoing) Our Paper

## Notes
For verification of the experiments in our paper: 
1. Check [EnvelopStateforNonIncrease(Decrease)function.ipynb](.\notebooks\EnvelopStateforNonIncrease(Decrease)function.ipynb) for counting number of $T$ gates in preparing envelop state of non-increasing and non-decreasing functions 
2. Check [qmpa](https://github.com/Alan-Robertson/qmpa) for counting number of Toffoli gates in multiplication operation.



## Citation
```
@misc{ichirokira_quantumstatepreparation,
  author       = {Ichirokira},
  title        = {{Quantum State Preparation}},
  year         = {n.d.},
  note         = {GitHub repository},
  howpublished = {\url{https://github.com/ichirokira/QuantumStatePreparation}},
  urldate      = {2024-10-28}
}
```