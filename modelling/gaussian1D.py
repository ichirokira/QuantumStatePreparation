import sympy
import cirq
import numpy as np
from utils.arithmetics import Multiplier
from utils.helpers import *
from utils.inequality_test import Comparator

class Gaussian1DineqBased:
  """
  Implement inequality test based method for 1D Gaussian State in https://arxiv.org/abs/2110.05708
  Attributes:
    -----------
    p : float
        working precision

    m : int
        fixed-point number of representation
    
    sigma: float
        std value of the target gaussian (mean value is set to be 0)
    
    delta : float
        lattice spacing value

  Methods:
    --------
    simulate() -> cirq.StateVectorTrialResult
        Generates output state vector 
    
    post_process_cricuit() -> cirq.Circuit
        Generates for post measurement process.
    
  """
  def __init__(self, p: int, m: int, sigma: float, delta: float) -> None:
    """
    Initialize the class with some preparation parameters

    Args:
        p: working precision
        m: fixed-point number of representation
        sigma: std value of the target gaussian (mean value is set to be 0)
        delta: lattice spacing value
    """
    self.p = p # p > 2m + 1
    self.m = m
    self.sigma = sigma
    self.delta = delta

    # intialize working registers
    self.full_out_register = [cirq.NamedQubit('out' + str(p-1-i)) for i in range(p)]
    self.active_out_register = self.full_out_register[0:m]
    # The order of qubits in out_register will follows order in the paper (the least significant qubit is 0th)
    # The other will be kept in normal order.
    self.ref_register = [cirq.NamedQubit('ref' + str(i)) for i in range(m)]
    self.tmp_register = [cirq.NamedQubit('tmp' + str(i)) for i in range(m)]
    self.ang_register = [cirq.NamedQubit('ang' + str(i)) for i in range(p)]
    self.spc_register = [cirq.NamedQubit('spc' + str(i)) for i in range(m)]
    self.prod_out_register = [cirq.NamedQubit('prod_out' + str(i)) for i in range(p)]
    self.ineq_qubit = cirq.NamedQubit("inequality_test_qubit")
    self.flag_qubit = cirq.NamedQubit("flip_flag")
    self.preparation_circuit = cirq.Circuit()

  def simulate(self)-> cirq.StateVectorTrialResult:
    """
    Return the circuit described in Algorithm.7
    """
    self.circuit = cirq.Circuit()

    # Prepare Eq. 78

    thetas = rot_angles(self.m, self.sigma)
    ## store theta_(m-2) to ang_register
    angle_circuit = angle_to_register(self.ang_register, thetas[self.m-2])
    self.circuit.append(angle_circuit,
                        strategy=cirq.InsertStrategy.NEW_THEN_INLINE)
    ## Apply ROT on out_(m-2)
    self.circuit.append(rot_circuit(self.active_out_register[1],
                                    self.ang_register,
                                    controlled_qubit=None),
                                    strategy=cirq.InsertStrategy.NEW_THEN_INLINE)
    ## Uncompute ang_register
    self.circuit.append(cirq.inverse(angle_circuit),
                        strategy=cirq.InsertStrategy.NEW_THEN_INLINE)

    ## Implement Line 6-10 in Alg.7
    for l in np.arange(self.m-3, -1, -1):
      self.circuit.append(cirq.CNOT(self.active_out_register[self.m-l-2], self.active_out_register[self.m-l-1]))
      angle_circuit = angle_to_register(self.ang_register, thetas[l])
      self.circuit.append(angle_circuit,
                        strategy=cirq.InsertStrategy.NEW_THEN_INLINE)

      self.circuit.append(rot_circuit(self.active_out_register[self.m-l-1],
                                    self.ang_register,
                                    controlled_qubit=self.active_out_register[self.m-l-2]),
                                    strategy=cirq.InsertStrategy.NEW_THEN_INLINE)
      self.circuit.append(cirq.inverse(angle_circuit),
                        strategy=cirq.InsertStrategy.NEW_THEN_INLINE)

    ## Implement Line 12-13 in Alg.7
    for l in range(1, self.m):
      self.circuit.append(cirq.CNOT(self.active_out_register[self.m-l-1], self.active_out_register[self.m-l]))
      self.circuit.append(cirq.H(self.active_out_register[self.m-l]).controlled_by(self.active_out_register[self.m-l-1]))



    # Prepare Ratio Eq.80
    b = 1
    while b == 1:
      ##  prepares t-qubit ref register in uniform superposition state
      for i in range(self.m):
        self.circuit.append(cirq.H(self.ref_register[i]))
      ## implement Ratio circuit
      for j in range(0, 2**self.m - 1):
        ratio_circuit = ratio_to_register(j, self.sigma, self.tmp_register)
        ratio_circuit_op = cirq.CircuitOperation(ratio_circuit.freeze())
        self.circuit.append(ratio_circuit_op.controlled_by(*self.active_out_register,
                                                           control_values=[int(k) for k in format(j, "b").zfill(self.m)]))

      # Compare ref and tmp
      comparator = Comparator( self.tmp_register, self.ref_register)
      compare_circ = comparator.construct_circuit()

      self.circuit.append(compare_circ, strategy=cirq.InsertStrategy.NEW_THEN_INLINE)
      self.circuit.append(cirq.X(comparator.anc1))
      self.circuit.append(cirq.CNOT(comparator.anc1, self.ineq_qubit))
      self.circuit.append(cirq.X(comparator.anc1))

      # unprepare ref
      for i in range(self.m):
        self.circuit.append(cirq.H(self.ref_register[i]))

      self.preparation_circuit.append(self.circuit)

      # the circuit outputs Eq.77 if ineq qubit return 0
      # flip the Eq.77 to Eq. 76 if ineq return 0
      a = sympy.symbols('ineq')
      sympy_cond = sympy.Eq(a, 0)
      self.circuit.append(cirq.measure(self.ineq_qubit, key="ineq"))

      # post process if measure ineq returns 1
      post_process_circuit = self.post_process_cricuit()
      post_process_op = cirq.CircuitOperation(post_process_circuit.freeze())
      self.circuit.append(post_process_op.with_classical_controls(sympy_cond))

      # Run simulation
      #print(comparator.circuit.get_independent_qubit_sets()[0])
      simulator = cirq.Simulator()
      result = simulator.simulate(self.circuit)
      b = result.measurements['ineq'][0]

      return result

  def post_process_cricuit(self) -> cirq.Circuit:
    circuit = cirq.Circuit()
    # COMP(out, ref, flag)
    comparator = Comparator(self.ref_register, self.active_out_register)
    compare_circ = comparator.construct_circuit()
    circuit.append(compare_circ, strategy=cirq.InsertStrategy.NEW_THEN_INLINE)
    circuit.append(cirq.CNOT(comparator.anc1, self.flag_qubit))

    # CHAD(flag, out[m-1])
    circuit.append(cirq.H(self.active_out_register[0]).controlled_by(self.flag_qubit))
    # erase flag
    inv_compare = cirq.inverse(compare_circ)
    circuit.append(inv_compare, strategy=cirq.InsertStrategy.NEW_THEN_INLINE)

    self.preparation_circuit.append(circuit)
    # delta to register
    binarized_delta = format(int(self.delta), "b").zfill(self.m) # convert to binary string
    for qubit, value in zip(self.spc_register, binarized_delta):
      if value == "1":
        circuit.append(cirq.X(qubit))

    # MUL(out, spc, anc)
    multiplier = Multiplier(self.active_out_register, self.spc_register, self.prod_out_register).multiply()
    circuit.append(multiplier)

    # erases spc_register
    for qubit, value in zip(self.spc_register, binarized_delta):
      if value == "1":
        circuit.append(cirq.X(qubit))

    # erases out
    circuit.append(cirq.inverse(self.preparation_circuit))

    for l in range(0, self.p):
      circuit.append(cirq.SWAP(self.full_out_register[l], self.prod_out_register[l]))

    return circuit

