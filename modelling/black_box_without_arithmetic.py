import cirq
import numpy as np
from utils.inequality_test import Comparator

__all__ = ["BlackBoxRegularAA", "BlackBoxObliviousAA", "BlackBoxSquareRoot"]

class BlackBoxRegularAA:
  """
  Implement inequality test based method in https://arxiv.org/abs/1807.03206 with regular ampltitude amplification technqiues
  """
  def __init__(self, num_out_qubits: int, num_data_qubits: int, input_data: list =None, black_box: cirq.Circuit = None)-> None:
    """
    :param num_out_qubits: number of qubits for output register
    :param num_data_qubits: number of qubits to estimate the output data from the oracle
    :param input_data: if 'black_box' is None, user can direct input the list of amplitudes as 'input_data'
    :param black_box: the oracle to generate the output data.
    """
    self.num_out_qubits = num_out_qubits
    self.num_data_qubits = num_data_qubits
    self.input_data = input_data
    
    self.out = [cirq.NamedQubit('out' + str(i)) for i in range(num_out_qubits)]
    self.data = [cirq.NamedQubit('data' + str(i)) for i in range(num_data_qubits)]
    self.ref = [cirq.NamedQubit('ref' + str(i)) for i in range(num_data_qubits)]
    self.flag = cirq.NamedQubit('flag')
    if black_box:
        # if there is input blackbox, directly apply the oracle on out and data registers
        self.blackbox = black_box(self.out, self.data)

  def good_state_preparation(self,) -> cirq.Circuit:
    """
    Generate the good state at |0>_ref|0>-flag.
    Implement Eq.(7) in the paper 
    """
    circuit = cirq.Circuit()

    # intializer
    for i in range(self.num_out_qubits):
      circuit.append(cirq.H(self.out[i]))
    if self.blackbox is None:
      # if there is no input blackbox, apply simple basis encoding for input_data
      def ai_to_gate(ai):
        circ = cirq.Circuit()
        for i, val in enumerate(ai):
          if val == '1':
            circ.append(cirq.X(self.data[self.num_data_qubits-1-i]))
        return circ

      def oracle(A, d, n):
          """ Loads the data array onto the circuit, controlled by register out as index. """
          oracle = cirq.Circuit()
          for i in range(2**d):
              circ_ai = ai_to_gate(A[i])
              circ_ai_to_op = cirq.CircuitOperation(circ_ai.freeze())
              ai_encode_gate = circ_ai_to_op.controlled_by(*self.out, control_values=[int(k) for k in format(i, "b").zfill(self.num_out_qubits)])
              oracle.append(ai_encode_gate)
          return oracle 
      # Apply blackbox
      self.blackbox = oracle(self.input_data, self.num_out_qubits, self.num_data_qubits)
      circuit.append(self.blackbox, strategy=cirq.InsertStrategy.NEW_THEN_INLINE)
    else:
      circuit.append(self.blackbox, strategy=cirq.InsertStrategy.NEW_THEN_INLINE)

    # initialize ref
    for i in range(self.num_data_qubits):
      circuit.append(cirq.H(self.ref[i]))
    
    # compare ref to data
    comparator = Comparator(self.ref, self.data)
    compare_circ = comparator.construct_circuit()

    circuit.append(compare_circ, strategy=cirq.InsertStrategy.NEW_THEN_INLINE)
    circuit.append(cirq.X(comparator.anc1))
    circuit.append(cirq.CNOT(comparator.anc1, self.flag))
    circuit.append(cirq.X(comparator.anc1))

    # uncompute comparator
    inv_compare = cirq.inverse(compare_circ)
    circuit.append(inv_compare, strategy=cirq.InsertStrategy.NEW_THEN_INLINE)

    # unprepare superposition from ref
    for i in range(self.num_data_qubits):
      circuit.append(cirq.H(self.ref[i]))

    return circuit

  def amplitude_amplification(self, num_iteration: int) -> cirq.Circuit:

    #define components
    def phase_oracle() -> cirq.Circuit:
      """
      Negate the amplitude with |0>_ref |0>_flag
      """
      circ = cirq.Circuit()
      circ.append(cirq.X(self.flag))
      circ.append(cirq.H(self.flag)) # on flag
      circ.append(cirq.XPowGate().controlled(self.num_data_qubits, control_values=[0]*self.num_data_qubits).on(*self.ref, self.flag))
      circ.append(cirq.H(self.flag)) # on flag
      circ.append(cirq.X(self.flag))
      return circ

    def zero_reflection(qubits: list) -> cirq.Circuit:
      """
      Reflect zero state. 
      Implement I - 2|0><0| over all qubits
      """
      circ = cirq.Circuit()
      for i in range(len(qubits)):
        circ.append(cirq.X(qubits[i]))

      circ.append(cirq.H(qubits[-1])) # on flag
      circ.append(cirq.XPowGate().controlled(self.num_out_qubits+2*self.num_data_qubits).on(*qubits))
      circ.append(cirq.H(qubits[-1])) # on flag

      for i in range(len(qubits)):
        circ.append(cirq.X(qubits[i]))
      
      return circ

    circ = cirq.Circuit()
    oracle = phase_oracle()
    good_state_preparation = self.good_state_preparation()
    reflection = zero_reflection(self.out+self.data+self.ref+[self.flag])
    
    
    circ.append(good_state_preparation, strategy=cirq.InsertStrategy.NEW_THEN_INLINE)
    for i in range(num_iteration):
      circ.append(oracle, strategy=cirq.InsertStrategy.NEW_THEN_INLINE)
      circ.append(cirq.inverse(good_state_preparation), strategy=cirq.InsertStrategy.NEW_THEN_INLINE)
      circ.append(reflection, strategy=cirq.InsertStrategy.NEW_THEN_INLINE)
      circ.append(good_state_preparation, strategy=cirq.InsertStrategy.NEW_THEN_INLINE)
    
    return circ
  
  def run(self,num_iteration: int) -> None:
    self.output_circuit = self.amplitude_amplification(num_iteration=num_iteration) # math.floor(np.sqrt(2**self.num_data_qubits))
    # uncompute data
    self.output_circuit.append(self.blackbox, strategy=cirq.InsertStrategy.NEW_THEN_INLINE)

  def check_output(self) -> list:
    # measurement
    self.output_circuit.append(cirq.measure(*(self.out+self.ref+[self.flag]), key="result"))
    s = cirq.Simulator()
    samples = s.run(self.output_circuit, repetitions=5000)
    results = samples.histogram(key="result")
    care_results = []
    for i in range(2**self.num_out_qubits):
      binarized_i = format(i, "b").zfill(self.num_out_qubits)
      binarized_i = binarized_i[::-1]
      care_position = int(binarized_i+"0"*self.num_data_qubits+"0", 2)
      care_results.append(results[care_position])
    
    amplitude = np.sqrt(np.array(care_results)/(sum(care_results)))
    
    return amplitude
  



class BlackBoxObliviousAA:
  """
  Implement inequality test based method in https://arxiv.org/abs/1807.03206 with oblivious ampltitude amplification technqiues
  """
  def __init__(self, num_out_qubits: int, num_data_qubits: int, input_data: list =None, black_box: cirq.Circuit = None)-> None:
    """
    :param num_out_qubits: number of qubits for output register
    :param num_data_qubits: number of qubits to estimate the output data from the oracle
    :param input_data: if 'black_box' is None, user can direct input the list of amplitudes as 'input_data'
    :param black_box: the oracle to generate the output data.
    """

    self.num_out_qubits = num_out_qubits
    self.num_data_qubits = num_data_qubits
    self.input_data = input_data
    
    self.out = [cirq.NamedQubit('out' + str(i)) for i in range(num_out_qubits)]
    self.data = [cirq.NamedQubit('data' + str(i)) for i in range(num_data_qubits)]
    self.ref = [cirq.NamedQubit('ref' + str(i)) for i in range(num_data_qubits)]
    self.flag = cirq.NamedQubit('flag')
    if black_box:
        # if there is input blackbox, directly apply the oracle on out and data registers
        self.blackbox = black_box(self.out, self.data)

  def good_state_preparation(self,)-> cirq.Circuit:
    """
    Generate the good state at |0>_ref|0>_flag.
    Implement Eq.(7) in the paper 
    """
    circuit = cirq.Circuit()

    # intializer
    for i in range(self.num_out_qubits):
      circuit.append(cirq.H(self.out[i]))
    if self.blackbox is None:
      # if there is no input blackbox, apply simple basis encoding for input_data
      def ai_to_gate(ai):
        circ = cirq.Circuit()
        for i, val in enumerate(ai):
          if val == '1':
            circ.append(cirq.X(self.data[self.num_data_qubits-1-i]))
        return circ

      def oracle(A, d, n):
          """ Loads the data array onto the circuit, controlled by register out as index. """
          oracle = cirq.Circuit()
          for i in range(2**d):
              circ_ai = ai_to_gate(A[i])
              circ_ai_to_op = cirq.CircuitOperation(circ_ai.freeze())
              ai_encode_gate = circ_ai_to_op.controlled_by(*self.out, control_values=[int(k) for k in format(i, "b").zfill(self.num_out_qubits)])
              oracle.append(ai_encode_gate)
          return oracle 
      # Apply blackbox
      self.blackbox = oracle(self.input_data, self.num_out_qubits, self.num_data_qubits)
      circuit.append(self.blackbox, strategy=cirq.InsertStrategy.NEW_THEN_INLINE)
    else:

      circuit.append(self.blackbox, strategy=cirq.InsertStrategy.NEW_THEN_INLINE)

    # initialize ref
    for i in range(self.num_data_qubits):
      circuit.append(cirq.H(self.ref[i]))
    # compare ref to data
    comparator = Comparator(self.ref, self.data)
    compare_circ = comparator.construct_circuit()

    circuit.append(compare_circ, strategy=cirq.InsertStrategy.NEW_THEN_INLINE)
    circuit.append(cirq.X(comparator.anc1))
    circuit.append(cirq.CNOT(comparator.anc1, self.flag))
    circuit.append(cirq.X(comparator.anc1))

    # uncompute comparator
    inv_compare = cirq.inverse(compare_circ)
    circuit.append(inv_compare, strategy=cirq.InsertStrategy.NEW_THEN_INLINE)

    # unprepare superposition from ref
    for i in range(self.num_data_qubits):
      circuit.append(cirq.H(self.ref[i]))

    return circuit

  def amplitude_amplification(self, num_iteration):


    def zero_reflection():
      '''
      This oracle phase flip the state of |0>_ref|0>_flag
      '''
      circ = cirq.Circuit()
      anc = cirq.NamedQubit('phase_oracle_ancilla')
      circ.append(cirq.X(anc))
      circ.append(cirq.H(anc))
      circ.append(cirq.XPowGate().controlled(self.num_data_qubits+1, 
                                             control_values=[0]*(self.num_data_qubits+1)).on(*self.ref, self.flag, anc))
      circ.append(cirq.H(anc))
      circ.append(cirq.X(anc))
      return circ

    
    circ = cirq.Circuit()
    good_state_preparation = self.good_state_preparation()
    reflection = zero_reflection()

    
    circ.append(good_state_preparation, strategy=cirq.InsertStrategy.NEW_THEN_INLINE)
    for i in range(num_iteration):
      
      circ.append(cirq.inverse(good_state_preparation), strategy=cirq.InsertStrategy.NEW_THEN_INLINE)
      circ.append(reflection, strategy=cirq.InsertStrategy.NEW_THEN_INLINE)
      circ.append(good_state_preparation, strategy=cirq.InsertStrategy.NEW_THEN_INLINE)
      circ.append(reflection, strategy=cirq.InsertStrategy.NEW_THEN_INLINE)
    return circ
  
  def run(self,num_iteration:int) -> None:
    self.output_circuit = self.amplitude_amplification(num_iteration=num_iteration) # math.floor(np.sqrt(2**self.num_data_qubits))
    # uncompute data
    self.output_circuit.append(self.blackbox, strategy=cirq.InsertStrategy.NEW_THEN_INLINE)

  def check_output(self) -> list:
    # measurement
    self.output_circuit.append(cirq.measure(*(self.out+self.ref+[self.flag]), key="result"))
    s = cirq.Simulator()
    samples = s.run(self.output_circuit, repetitions=5000)
    results = samples.histogram(key="result")
    care_results = []
    for i in range(2**self.num_out_qubits):
      binarized_i = format(i, "b").zfill(self.num_out_qubits)
      binarized_i = binarized_i[::-1]
      care_position = int(binarized_i+"0"*self.num_data_qubits+"0", 2)
      care_results.append(results[care_position])
    
    amplitude = np.sqrt(np.array(care_results)/(sum(care_results)))
    
    return amplitude



class BlackBoxSquareRoot:
  """
  Implement inequality test based method in https://arxiv.org/abs/1807.03206 with square root amplitudes
  """
  def __init__(self, num_out_qubits: int, num_data_qubits: int, input_data: list =None, black_box: cirq.Circuit = None)-> None:
    """
    :param num_out_qubits: number of qubits for output register
    :param num_data_qubits: number of qubits to estimate the output data from the oracle
    :param input_data: if 'black_box' is None, user can direct input the list of amplitudes as 'input_data'
    :param black_box: the oracle to generate the output data.
    """

    self.num_out_qubits = num_out_qubits
    self.num_data_qubits = num_data_qubits
    self.input_data = input_data
    
    self.out = [cirq.NamedQubit('out' + str(i)) for i in range(num_out_qubits)]
    self.data = [cirq.NamedQubit('data' + str(i)) for i in range(num_data_qubits)]
    self.ref = [cirq.NamedQubit('ref' + str(i)) for i in range(num_data_qubits)]
    self.flag = cirq.NamedQubit('flag')
    if black_box:
        # if there is input blackbox, directly apply the oracle on out and data registers
        self.blackbox = black_box(self.out, self.data)

  def good_state_preparation(self,)-> cirq.Circuit:

    circuit = cirq.Circuit()

    # intializer
    for i in range(self.num_out_qubits):
      circuit.append(cirq.H(self.out[i]))
    if self.blackbox is None:
      # if there is no input blackbox, apply simple basis encoding for input_data
      def ai_to_gate(ai):
        circ = cirq.Circuit()
        for i, val in enumerate(ai):
          if val == '1':
            circ.append(cirq.X(self.data[self.num_data_qubits-1-i]))
        return circ

      def oracle(A, d, n):
          """ Loads the data array onto the circuit, controlled by register out as index. """
          oracle = cirq.Circuit()
          for i in range(2**d):
              circ_ai = ai_to_gate(A[i])
              circ_ai_to_op = cirq.CircuitOperation(circ_ai.freeze())
              ai_encode_gate = circ_ai_to_op.controlled_by(*self.out, control_values=[int(k) for k in format(i, "b").zfill(self.num_out_qubits)])
              oracle.append(ai_encode_gate)
          return oracle 
      # Apply blackbox
      self.blackbox = oracle(self.input_data, self.num_out_qubits, self.num_data_qubits)
      circuit.append(self.blackbox, strategy=cirq.InsertStrategy.NEW_THEN_INLINE)
    else:

      circuit.append(self.blackbox, strategy=cirq.InsertStrategy.NEW_THEN_INLINE)

    # initialize ref
    for i in range(self.num_data_qubits):
      circuit.append(cirq.H(self.ref[i]))
    # compare ref to data
    comparator = Comparator(self.ref, self.data)
    compare_circ = comparator.construct_circuit()

    circuit.append(compare_circ, strategy=cirq.InsertStrategy.NEW_THEN_INLINE)
    circuit.append(cirq.X(comparator.anc1))
    circuit.append(cirq.CNOT(comparator.anc1, self.flag))
    circuit.append(cirq.X(comparator.anc1))

    # uncompute comparator
    inv_compare = cirq.inverse(compare_circ)
    circuit.append(inv_compare, strategy=cirq.InsertStrategy.NEW_THEN_INLINE)

    return circuit

  def unif(self) -> cirq.Circuit:
    """
    Approximate unif operation (Eq.8 in the paper) by unif' (Eq. 9):
    U: |lambda>_data |0>_ref --> 1/sqrt(lambda) |lambda>_data sum_{x=0}^{lambda-1}|0>_ref
    The circuit can be implemented by  n-controlled Hadamard gates followed by an application of Comparator. 
    It is finalized by ampltitude amplification to get close to Eq.8
    """
    unif_ancilla = cirq.NamedQubit('unif_anc')
    def state_unif():
      circ = cirq.Circuit()
      
      # apply controlled Hadamard gates
      for i in range(self.num_data_qubits):
        circ.append(cirq.HPowGate().controlled(1).on(self.data[i], self.ref[i]))
      # apply comparator
      comparator = Comparator(self.ref, self.data)
      compare_circ = comparator.construct_circuit()

      circ.append(compare_circ, strategy=cirq.InsertStrategy.NEW_THEN_INLINE)
      circ.append(cirq.X(comparator.anc1))
      circ.append(cirq.CNOT(comparator.anc1, unif_ancilla))
      circ.append(cirq.X(comparator.anc1))

      # uncompute comparator
      inv_compare = cirq.inverse(compare_circ)
      circ.append(inv_compare, strategy=cirq.InsertStrategy.NEW_THEN_INLINE)

      return circ
    def unif_zero_reflection():
      circ = cirq.Circuit()
      circ.append(cirq.X(unif_ancilla))
      circ.append(cirq.H(unif_ancilla)) # on flag
      circ.append(cirq.X(unif_ancilla))
      circ.append(cirq.H(unif_ancilla)) # on flag
      circ.append(cirq.X(unif_ancilla))
      return circ
    
    circ = cirq.Circuit()

    state_preparation = state_unif()
    oracle = unif_zero_reflection()

    
    
    circ.append(state_preparation, strategy=cirq.InsertStrategy.NEW_THEN_INLINE)
    # for simple case number of iteration in AA of 2 is enough, can be changed for better understanding
    for i in range(2): 
      
      circ.append(cirq.inverse(state_preparation), strategy=cirq.InsertStrategy.NEW_THEN_INLINE)
      circ.append(oracle, strategy=cirq.InsertStrategy.NEW_THEN_INLINE)
      circ.append(state_preparation, strategy=cirq.InsertStrategy.NEW_THEN_INLINE)

      circ.append(oracle, strategy=cirq.InsertStrategy.NEW_THEN_INLINE)
    
    return circ
    

  def amplitude_amplification(self, num_iteration:int ) -> cirq.Circuit:
    """
    Use oblivious Amplitude Amplification
    """

    def zero_reflection():
      circ = cirq.Circuit()
      circ.append(cirq.X(self.flag))
      circ.append(cirq.H(self.flag)) # on flag
      circ.append(cirq.X(self.flag))
      circ.append(cirq.H(self.flag)) # on flag
      circ.append(cirq.X(self.flag))
      return circ
    
    circ = cirq.Circuit()
    state_preparation = self.good_state_preparation()
    oracle = zero_reflection()

    
    
    circ.append(state_preparation, strategy=cirq.InsertStrategy.NEW_THEN_INLINE)
    for i in range(num_iteration):
      
      circ.append(cirq.inverse(state_preparation), strategy=cirq.InsertStrategy.NEW_THEN_INLINE)
      circ.append(oracle, strategy=cirq.InsertStrategy.NEW_THEN_INLINE)
      circ.append(state_preparation, strategy=cirq.InsertStrategy.NEW_THEN_INLINE)
      circ.append(oracle, strategy=cirq.InsertStrategy.NEW_THEN_INLINE)
    
    return circ
  
  def run(self,num_iteration:int) -> None:
    self.output_circuit = self.amplitude_amplification(num_iteration=num_iteration) # math.floor(np.sqrt(2**self.num_data_qubits))
    #apply inverse unif
    unif_circuit = self.unif()
    self.output_circuit.append(cirq.inverse(unif_circuit), strategy=cirq.InsertStrategy.NEW_THEN_INLINE)
    # uncompute data
    self.output_circuit.append(self.blackbox, strategy=cirq.InsertStrategy.NEW_THEN_INLINE)

  def check_output(self) -> list:
    # measurement
    self.output_circuit.append(cirq.measure(*(self.out+[self.flag]), key="result"))
    s = cirq.Simulator()
    samples = s.run(self.output_circuit, repetitions=5000)
    results = samples.histogram(key="result")
    care_results = []
    for i in range(2**self.num_out_qubits):
      binarized_i = format(i, "b").zfill(self.num_out_qubits)
      binarized_i = binarized_i[::-1]
      care_position = int(binarized_i+"0", 2)
      care_results.append(results[care_position])
    
    amplitude = np.sqrt(np.array(care_results)/(sum(care_results)))
    
    return amplitude

