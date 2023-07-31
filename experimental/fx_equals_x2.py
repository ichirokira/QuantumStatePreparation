import numpy as np
import matplotlib.pyplot as plt
import math
import cirq
import os
import sys


from modelling.black_box_without_arithmetic import *
from utils.resource_estimation import generate_circuit_stats
from utils.arithmetics import Multiplier
import argparse


def get_argparse():
    parser = argparse.ArgumentParser()
    parser.add_argument('-m', '--model', default='regular_aa',
                        choices=['regular_aa', 'oblivious_aa', 'square_root'])
    parser.add_argument('-f', '--figure', default='fx_equals_x2.png',
                        help='Output file for the visualization')
    parser.add_argument('-o', '--rs_dir', default='results/fx_equals_x2.csv', help='Output file for resouce estimation')
    return parser.parse_args()

# blackbox for f(x) = x^2
def blackbox(out_register, data_register):
  anncilla = [cirq.NamedQubit('bb2_anc' + str(i)) for i in range(len(out_register))]
  circuit = cirq.Circuit()

  for out, anc in zip(out_register, anncilla):
    circuit.append(cirq.CNOT(out, anc), strategy=cirq.InsertStrategy.NEW_THEN_INLINE)
  
  multiplier = Multiplier(out_register, anncilla, data_register).multiply()
  circuit.append(multiplier, strategy=cirq.InsertStrategy.NEW_THEN_INLINE)

  return circuit


def visualize_results(config, input_size, model, output_file="fx_equals_x2.png"):
  circuit = model(num_out_qubits=input_size, num_data_qubits=2*input_size+1, black_box=blackbox)
  num_iteration = math.ceil((np.pi/4)*np.sqrt(2**input_size)/np.linalg.norm([x for x in range(0,2**input_size)]))
  print("[INFO] Running the experiment with {} Amplitude Amplification Rounds".format(num_iteration))
  circuit.construct_circuit(num_iteration=num_iteration)
  output = circuit.get_output()
  if config.model == "square_root":
      expected_output = np.arange(0, 2**input_size)/np.linalg.norm(np.arange(0, 2**input_size))
  else:
      expected_output = (np.arange(0, 2**input_size)**2)/np.linalg.norm((np.arange(0, 2**input_size)**2))

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

   # visualize results on system size of 2
   visualize_results(config=config, input_size=2, model=model, output_file=config.figure)

   # resouce estimated on different input size
   input_size = [2,4,8,16]
   for n in input_size:
        print("[INFO] Prepare result with:", n)
        state_prep = model(num_out_qubits=n, num_data_qubits=2*n+1, black_box=blackbox)
        state_prep.construct_circuit(num_iteration = math.ceil((np.pi/4)*np.sqrt(2**n)/np.linalg.norm([x for x in range(0,2**n)])))

        generate_circuit_stats(state_prep.output_circuit, n, csv_out = config.rs_dir)
   print("[INFO] DONE!!!")

if __name__ == '__main__':
    main()