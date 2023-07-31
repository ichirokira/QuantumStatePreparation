# QuantumStatePreparation
Inequality test-based techniques for Quantum State Preparation

## Set up

We recommend to follow the installation guides from [pyLIQTR](https://github.com/isi-usc-edu/pyLIQTR/tree/v0.3.0)

## Folder Organization

QuantumStatePreparation/  
│  
├── experimental/  
│   ├── __init__.py  
│   ├── fx_equals_x.py  
│   ├── fx_equals_x2.py  
│   └── ...  
│
├── modelling/  
│   ├── __init__.py  
│   ├── black_box_without_arithmetic.py  
│   ├── gaussian1D.py  
│   └── ...  
│
├── results/  
│   ├── output.png  
│   ├── outptu.csv  
│   └── ...
│  
├── utils/  
│   ├── __init__.py  
│   ├── arithmetics.py  
│   ├── helpers.py  
|   ├── inequality_test.py  
|   ├── resource_estimation.py  
│   └── ...  
│  
├── __init__.py  
├── README.md  
└── ...  

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
2. [Nearly optimal quantum algorithm for generating the ground state of a free quantum field theory](https://arxiv.org/abs/2110.05708)
