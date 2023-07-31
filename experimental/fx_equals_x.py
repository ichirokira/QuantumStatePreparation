import numpy as np
import matplotlib.pyplot as plt
import math
import cirq
import os
import sys


from modelling.black_box_without_arithmetic import *
from utils.resource_estimation import generate_circuit_stats
import argparse


def get_argparse():
    parser = argparse.ArgumentParser()
    parser.add_argument('-m', '--model', default='regular_aa',
                        choices=['regular_aa', 'oblivious_aa', 'square_root'])
    parser.add_argument('-f', '--figure', default='fx_equals_x.png',
                        help='Output file for the visualization')
    parser.add_argument('-o', '--rs_dir', default='results/fx_equals_x.csv', help='Output file for resouce estimation')
    return parser.parse_args()

def blackbox(out_register: list, data_register: list) -> cirq.Circuit:
  # blackbox for f(x) = x
  circuit = cirq.Circuit()

  for out, data in zip(out_register, data_register):
    circuit.append(cirq.CNOT(out, data), strategy=cirq.InsertStrategy.NEW_THEN_INLINE)

  return circuit

def visualize_results(config, input_size, model, output_file="f(x)_equals_x.png"):
  circuit = model(num_out_qubits=input_size, num_data_qubits=input_size, black_box=blackbox)
  num_iteration = math.ceil((np.pi/4)*np.sqrt(2**input_size)/np.linalg.norm([x for x in range(0,2**input_size)]))
  print("[INFO] Running the experiment with {} Amplitude Amplification Rounds".format(num_iteration))
  circuit.construct_circuit(num_iteration=num_iteration)
  output = circuit.get_output()
  if config.model == "square_root":
      expected_output = np.sqrt(np.arange(0, 2**input_size)/np.sum(np.arange(0, 2**input_size)))
  else:
      expected_output = np.arange(0, 2**input_size)/np.linalg.norm(np.arange(0, 2**input_size))
  plt.plot(output, color="red", label="Output")
  plt.plot(expected_output, color="blue", label="Expected Output")
  plt.xlabel("x")
  plt.ylabel("Normalized f(x)")
  plt.title("No. Grover Iteration: {}".format(num_iteration))
  plt.legend()
  save_path = os.path.join("results", output_file)
  plt.savefig(save_path)

def main():
   config = get_argparse()
   # define model 
   if config.model == "regular_aa":
      model = BlackBoxRegularAA
   elif config.model == "oblivious_aa":
      model = BlackBoxObliviousAA
   elif config.model == "square_root":
      model = BlackBoxSquareRoot
   else:
      raise Exception('Unknown model') 

   # visualize results on system size of 4
   visualize_results(config=config, input_size=4, model=model, output_file=config.figure)

   # resouce estimated on different input size
   input_size = [2,4,8,16]
   for n in input_size:
        print("[INFO] Prepare result with:", n)
        state_prep = model(num_out_qubits=n, num_data_qubits=n, black_box=blackbox)
        state_prep.construct_circuit(num_iteration = math.ceil((np.pi/4)*np.sqrt(2**n)/np.linalg.norm([x for x in range(0,2**n)])))

        generate_circuit_stats(state_prep.output_circuit, n, csv_out = config.rs_dir)
   print("[INFO] DONE!!!")

if __name__ == '__main__':
    main()