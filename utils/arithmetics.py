import cirq
""" Several Common Arithmetics for State Prepartion: Add, Multiplication"""
class Adder:
    def __init__(self, A: list, B: list, ancillae: list = None, type: bool =True) -> None:
        """
        :param A: The quantum register holding the first integer
        :param B: The quantum register second the first integer (the last N qubits of the addition result will be
                 registered in B)
        :param ancillae: The two needed ancillae
        :param type: Boolean parameter : if True the result will be in N+1 precision otherwise, otherwise it will
        """
        self.A = A
        self.B = B
        self.size = len(A)
        self.type = type
        if ancillae != None:
            self.ancillae = ancillae
        else:
            self.ancillae = [cirq.NamedQubit("ancilla1") ,cirq.NamedQubit("ancilla2")]

    def construct_circuit(self) -> cirq.Circuit:
        circuit = cirq.Circuit()
        # The set of CNOTs between Ai and Bi
        firs_set_of_CNOTs=[cirq.Moment([cirq.CNOT(self.A[i], self.B[i]) for i in range(1, self.size)])]

        # The set of CNOTs between Ai and Ai+1
        second_set_of_CNOTs=[]

        # The set of CNOTs between Ai, Bi and Ai+1
        firs_set_of_toff=[cirq.Moment([cirq.TOFFOLI(self.B[0], self.A[0], self.A[1])])]

        last_set_of_toff=[cirq.Moment([cirq.CNOT(self.A[0], self.B[0])])]

        single=[]
        for i in range(1, self.size-1):
            # Constructing the first part of the circuit
            second_set_of_CNOTs.append(cirq.Moment([cirq.CNOT(self.A[i], self.A[i+1])]))
            firs_set_of_toff.append(cirq.Moment([cirq.TOFFOLI(self.B[i], self.A[i], self.A[i+1])]))

            # Constructing the last part of the circuit
            last_set_of_toff.append(cirq.Moment([cirq.CNOT(self.A[i], self.B[i])]))
        last_set_of_toff.append(cirq.Moment([cirq.CNOT(self.A[-1], self.B[-1])]))

        # Adding or removing the N+1st qubit depending on choice
        if self.type:
            firs_set_of_toff.append(cirq.Moment([cirq.TOFFOLI(self.B[-1], self.A[-1], self.ancillae[0])])) # here
            single = [cirq.Moment([cirq.CNOT(self.A[-1], self.ancillae[0])])]

        # Constrcting the fist half of the circuit
        circuit.append(firs_set_of_CNOTs, strategy=cirq.InsertStrategy.NEW_THEN_INLINE)
        circuit.append(single, strategy=cirq.InsertStrategy.NEW_THEN_INLINE) # here
        circuit.append(second_set_of_CNOTs[::-1], strategy=cirq.InsertStrategy.NEW_THEN_INLINE)
        circuit.append(firs_set_of_toff, strategy=cirq.InsertStrategy.NEW_THEN_INLINE)

        # Balancing the circuit
        if self.type:
            firs_set_of_toff = firs_set_of_toff[::-1][1:]
        else:
            firs_set_of_toff = firs_set_of_toff[::-1]

        # Constructing the last part of the circuit
        last_set_of_toff = last_set_of_toff[::-1]
        for i in range(len(firs_set_of_toff)):
            circuit.append(last_set_of_toff[i], strategy=cirq.InsertStrategy.NEW_THEN_INLINE)
            circuit.append(firs_set_of_toff[i], strategy=cirq.InsertStrategy.NEW_THEN_INLINE)
        circuit.append(last_set_of_toff[-1], strategy=cirq.InsertStrategy.NEW_THEN_INLINE)
        circuit.append(second_set_of_CNOTs, strategy=cirq.InsertStrategy.NEW_THEN_INLINE)
        circuit.append(firs_set_of_CNOTs, strategy=cirq.InsertStrategy.NEW_THEN_INLINE)

        return circuit

# Controlled Adder
class ControlAdder:
    def __init__(self, A: list, B: list, ctrl: cirq.NamedQubit, ancillae: list = None, type: bool =True) -> None:
        """
        :param A: The quantum register holding the first integer
        :param B: The quantum register second the first integer (the last N qubits of the addition result will be
                 registered in B)
        :param ctrl: The qubit controlling the operation
        :param ancillae: The two needed ancillae
        :param type: Boolean parameter : if True the result will be in N+1 precision otherwise, otherwise it will
                 be in N qubit precision
        """
        self.A = A
        self.B = B
        self.ctrl = ctrl
        self.size = len(A)
        self.type = type
        if ancillae != None:
            self.ancillae = ancillae
        else:
            self.ancillae = [cirq.NamedQubit("ancilla1"), cirq.NamedQubit("ancilla2")]

    def construct_circuit(self) -> cirq.Circuit:
        self.circuit = cirq.Circuit()
        # The first set of CNOTs
        firs_set_of_CNOTs = [cirq.Moment([cirq.CNOT(self.A[i], self.B[i]) for i in range(1, self.size)])]
        # The set of CNOTs between the Ais
        second_set_of_CNOTs = []
        # The set of Toffolis between Ai Bi and Ai+1
        firs_set_of_toff = [cirq.Moment([cirq.TOFFOLI(self.B[0], self.A[0], self.A[1])])]
        # The set of Toffolis in the second part of the circuit
        second_set_of_toff = [cirq.TOFFOLI(self.ctrl, self.A[0], self.B[0])]
        single = []
        for i in range(1, self.size - 1):
            # Constructing the first part of the circuit
            second_set_of_CNOTs.append(cirq.Moment([cirq.CNOT(self.A[i], self.A[i + 1])]))
            firs_set_of_toff.append(cirq.Moment([cirq.TOFFOLI(self.B[i], self.A[i], self.A[i + 1])]))

            # Constructing the last part of the circuit
            second_set_of_toff.append(cirq.Moment([cirq.TOFFOLI(self.ctrl, self.A[i], self.B[i])]))

        # Appending the last Toffoli of the first set
        second_set_of_toff.append(cirq.Moment([cirq.TOFFOLI(self.ctrl, self.A[-1], self.B[-1])]))

        # Adding or removing the N+1st qubit depending on the choice
        if self.type:
            firs_set_of_toff.append(cirq.Moment([cirq.TOFFOLI(self.B[-1], self.A[-1], self.ancillae[1])]))  # here
            second_set_of_toff.append(cirq.Moment([cirq.TOFFOLI(self.ctrl, self.ancillae[1], self.ancillae[0])]))  # here
            single = [cirq.Moment([cirq.TOFFOLI(self.ctrl, self.A[-1], self.ancillae[0])])]

        # Constructing the circuit
        self.circuit.append(firs_set_of_CNOTs, strategy=cirq.InsertStrategy.NEW_THEN_INLINE)
        self.circuit.append(single, strategy=cirq.InsertStrategy.NEW_THEN_INLINE)  # here
        self.circuit.append(second_set_of_CNOTs[::-1], strategy=cirq.InsertStrategy.NEW_THEN_INLINE)
        self.circuit.append(firs_set_of_toff, strategy=cirq.InsertStrategy.NEW_THEN_INLINE)
        firs_set_of_toff = firs_set_of_toff[::-1]
        second_set_of_toff = second_set_of_toff[::-1]
        for i in range(len(firs_set_of_toff)):
            self.circuit.append(second_set_of_toff[i], strategy=cirq.InsertStrategy.NEW_THEN_INLINE)
            self.circuit.append(firs_set_of_toff[i], strategy=cirq.InsertStrategy.NEW_THEN_INLINE)
        self.circuit.append(second_set_of_toff[-1], strategy=cirq.InsertStrategy.NEW_THEN_INLINE)
        self.circuit.append(second_set_of_CNOTs, strategy=cirq.InsertStrategy.NEW_THEN_INLINE)
        self.circuit.append(firs_set_of_CNOTs, strategy=cirq.InsertStrategy.NEW_THEN_INLINE)

        return self.circuit

# Controlled Toffoli
class ControlToffoli:
    def __init__(self, ctrl, B, A):
        self.ctrl = ctrl
        self.B = B
        self.A = A

    def construct_moments(self):
        moments = [cirq.TOFFOLI(self.ctrl, self.B[i], self.A[i]) for i in range(len(self.A))]
        return moments

class Multiplier:
    def __init__(self, A: list, B: list, P: list = None)-> None:
        """
        :param A: First operand
        :param B: Second operand
        """
        self.A = A
        self.B = B
        self.size = len(A)
        # The qubits holding the product
        if P is None:
          self.P = [cirq.NamedQubit('P'+str(i)) for i in range(2*self.size+1)]
        else:
          self.P = P

    def multiply(self)-> cirq.Circuit:
        circuit = cirq.Circuit()
        circuit.append(ControlToffoli(self.B[0], self.A, self.P[0:self.size]).construct_moments())
        for i in range(1, self.size):
            # Add and shift
            circuit += ControlAdder(self.A, self.P[i:i + self.size], self.B[i], ancillae=[self.P[i + self.size], self.P[i + 1 + self.size]]).construct_circuit()
        return circuit


# # test
# if __name__ == "__main__":
#     print("-----------Test Adder------------")
#     # Test
#     A = "0010"
#     B = "0110"
#     n = len(A)
#     A_qubits = [cirq.NamedQubit('a' + str(i)) for i in range(n)]
#     B_qubits = [cirq.NamedQubit('b' + str(i)) for i in range(n)]

#     circuit = Adder(A_qubits, B_qubits, type=True).construct_circuit()
#     qubits = sorted(list(circuit.all_qubits()))[::-1]
#     print(qubits)
#     simulator = cirq.Simulator()
#     intial_state = int(B+"0"+A, 2)
#     result = simulator.simulate(circuit, qubit_order=qubits, initial_state=intial_state)
#     output = result.dirac_notation()
#     output = output[n+1]+ output[1:n+1]
#     print("Result of {}+{} = {}".format(A,B,output))

#     print("-----------Test Multiplication------------")

#     # Test
#     A_qubits = [cirq.NamedQubit('a' + str(i)) for i in range(n)]
#     B_qubits = [cirq.NamedQubit('b' + str(i)) for i in range(n)]

#     circuit = Multiplier(A_qubits, B_qubits).multiply()

#     simulator = cirq.Simulator()
#     qubits = sorted(list(circuit.all_qubits()))[::-1]
#     intial_state = int(B+A+"0"*(2*n+1), 2)
#     result = simulator.simulate(circuit, qubit_order=qubits, initial_state=intial_state)
#     output = result.dirac_notation()
#     output = output[2*n:-1]
#     print("Result of {}x{} = {}".format(A,B,output))


