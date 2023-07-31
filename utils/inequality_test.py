""" Implement quantum circuit for comparing two number A and B which represented in 2^n qubits. 
The implementation is based on https://arxiv.org/pdf/1711.10460.pdf"""

import math
import cirq
class Comparator:
  def __init__(self, A, B):
    """
        :param A: The quantum register holding the first number
        :param B: The quantum register second number
    """
    self.A = A
    self.B = B
    self.length = len(A)


  def compare2(self, a0: cirq.NamedQubit, b0: cirq.NamedQubit, a1:cirq.NamedQubit, b1:cirq.NamedQubit, name: str) -> [cirq.Circuit, cirq.NamedQubit, cirq.NamedQubit]:
    # Compare a pair of two bits
    p = cirq.NamedQubit("ancilla_comp2_{}".format(name))
    compare2 = cirq.Circuit()
    compare2.append(cirq.X(p))
    compare2.append(cirq.CNOT(b1,a1), strategy=cirq.InsertStrategy.EARLIEST)
    compare2.append(cirq.CNOT(b0,a0), strategy=cirq.InsertStrategy.EARLIEST)
    # compare2.append(cirq.CSWAP(a1, a0, p), strategy=cirq.InsertStrategy.NEW_THEN_INLINE)
    compare2.append(cirq.CCNOT(a1, a0, p), strategy=cirq.InsertStrategy.NEW_THEN_INLINE)
    compare2.append(cirq.CCNOT(a1, p, a0), strategy=cirq.InsertStrategy.NEW_THEN_INLINE)
    compare2.append(cirq.CCNOT(a1, a0, p), strategy=cirq.InsertStrategy.NEW_THEN_INLINE)

    # compare2.append(cirq.CSWAP(a1, b1, b0), strategy=cirq.InsertStrategy.NEW_THEN_INLINE)
    compare2.append(cirq.TOFFOLI(a1, b1, b0), strategy=cirq.InsertStrategy.NEW_THEN_INLINE)
    compare2.append(cirq.TOFFOLI(a1, b0, b1), strategy=cirq.InsertStrategy.NEW_THEN_INLINE)
    compare2.append(cirq.TOFFOLI(a1, b1, b0), strategy=cirq.InsertStrategy.NEW_THEN_INLINE)

    compare2.append(cirq.CNOT(b0,a0), strategy=cirq.InsertStrategy.NEW_THEN_INLINE)

    return compare2, a0, b0


  def finalizer(self, a: cirq.NamedQubit, b: cirq.NamedQubit) -> cirq.Circuit:
    # verify b>a

    self.anc1 = cirq.NamedQubit("ancilla_fin")

    final_cir = cirq.Circuit()
    final_cir.append(cirq.X(a), strategy=cirq.InsertStrategy.NEW_THEN_INLINE)
    final_cir.append(cirq.TOFFOLI(a,b, self.anc1), strategy=cirq.InsertStrategy.NEW_THEN_INLINE)
    final_cir.append(cirq.X(a), strategy=cirq.InsertStrategy.NEW_THEN_INLINE)

    return final_cir

  def construct_circuit(self,) -> cirq.Circuit:
    self.circuit = cirq.Circuit()
    two_bitwise_compare = {}
    qubits_out_acc_layer = {}
    for j in range(0, int(math.log2(self.length))):
      two_bitwise_compare[j] = []
      qubits_out_acc_layer[j] = []
    # first layer
    for i in range(0, self.length//2):
      cir, a_out, b_out = self.compare2(self.A[2*i], self.B[2*i], self.A[2*i+1], self.B[2*i+1], name="0_"+str(i))
      two_bitwise_compare[0].append(cir)
      qubits_out_acc_layer[0].append([a_out, b_out])
    # later layer
    for j in range(1, int(math.log2(self.length))):
      for i in range(len(qubits_out_acc_layer[j-1])//2):
        cir, a_out, b_out = self.compare2(*qubits_out_acc_layer[j-1][2*i], *qubits_out_acc_layer[j-1][2*i+1], name=str(j)+"_"+str(i))
        two_bitwise_compare[j].append(cir)
        qubits_out_acc_layer[j].append([a_out, b_out])


    final_compare = self.finalizer(*qubits_out_acc_layer[int(math.log2(self.length))-1][0])
    for j in range(0, int(math.log2(self.length))):
      self.circuit.append((two_bitwise_compare[j]), strategy=cirq.InsertStrategy.NEW_THEN_INLINE)
    self.circuit.append(final_compare, strategy=cirq.InsertStrategy.NEW_THEN_INLINE)
    return self.circuit

# if __name__ == "__main__":
#     # Test: verify B>A or not
#     A = "0110"
#     B = "0010"
#     n = len(A)
#     A_qubits = [cirq.NamedQubit('a' + str(i)) for i in range(n)]
#     B_qubits = [cirq.NamedQubit('b' + str(i)) for i in range(n)]

#     circuit = Comparator(A_qubits, B_qubits).construct_circuit()

#     simulator = cirq.Simulator()
#     qubits = sorted(list(circuit.all_qubits()))
#     intial_state = int(A+"0"*(4)+B, 2)
#     result = simulator.simulate(circuit, qubit_order=qubits, initial_state=intial_state)
#     output = result.dirac_notation()
#     output = output[n+4]
#     print("Is {}>{}? {}".format(B, A, output))