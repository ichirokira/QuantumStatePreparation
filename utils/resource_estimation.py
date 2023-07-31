# Scaling analysis
import time
import os
import cirq
from pyLIQTR.QSP.qsp_helpers import qsp_decompose_once, print_to_openqasm, prettyprint_qsp_to_qasm, count_qubits
from pyLIQTR.gate_decomp.cirq_transforms import clifford_plus_t_direct_transform

toffolis = [
    "CCX",
    "ccx",
    "TOFFOLI",
    "toffoli",
]
def count_Toff_gates(circuit):
    '''
    For counting the number of Toffoli Gates in a circuit
    Parameters:
     - circuit: The circuit to count Toffoli Gates in
    Returns:
     - Toff_gate_counter: the number of Toffoli Gates in the circuit
    '''
    Toff_gate_counter = 0
        
    for moment in circuit:
        for op in moment:
            if (bool([x for x in toffolis if x in str(op)])):
                Toff_gate_counter += 1

    return (Toff_gate_counter)

def count_T_gates(circuit):
    '''
    For counting the number of T-Gates in a circuit
    Parameters:
     - circuit: The circuit to count T-Gates in
    Returns:
     - T_gate_counter: the number of T-Gates in the circuit
    '''
    T_gate_counter = 0
        
    for moment in circuit:
        for op in moment:
            if (str(op).startswith('T')):
                T_gate_counter += 1

    return (T_gate_counter)

def generate_circuit_stats(circuit: cirq.Circuit, n:int, csv_out='scaling_data.csv', save_circuit=False) -> None:
    """
    Produce resources estimation of the circuit based on system size n. The output file ('csv_out') will contain infomation of:
    "Input size -- Toffoli Decomposition Time -- Time writing out Toffoli Circuit -- Total Qubits -- # Toffoli Gates 
    -- Circuit Depth in toffoli decomposition)"

    :param circuit: the circuit wished to validate
    :param n: input size
    :param csv_out: the csv store
    :param save_circuit: whether save circuit or not (in OpenQASM 2.0 format)
    """

    t_start_time = time.time()

    # Decompose circuit:
    decomposed_circuit       = cirq.align_left((qsp_decompose_once(circuit)))
    t_decomp_to_toffoli_time = time.time()


    if save_circuit:
        # Save circuit to file in OpenQASM 2.0 format:
        with open(f'open_qasm_for_toffoli.qasm', 'w') as f:
            print_to_openqasm(f, decomposed_circuit)
        t_write_toffoli_time = time.time()


    # Lets write all this stuff out:
    if os.path.exists(csv_out):
        yes_header = False
    else:
        yes_header = True
    out_file = open(csv_out, 'a')
    if yes_header:
        out_file.write('Input Size,Toff_Decomp_Time,Write_Out_Toff_Time,Ttl_Qubits,Toffoli_Gate_Count ,Circ_Depth_Toff\n')

    # Calculate the times
    t_toff   = (t_decomp_to_toffoli_time  - t_start_time)
    # t_clifft = (t_decomp_to_cliffT_time   - t_decomp_to_toffoli_time)
    if save_circuit:
        t_write_out_toff   = (t_write_toffoli_time - t_decomp_to_toffoli_time)

    else:
        t_write_out_toff   = -1


    
    print_string = f'{n},{t_toff},{t_write_out_toff}'

    ttl_qubits, ctl_qubits, anc_qubits = count_qubits(circuit)
    num_Toff_gates = count_Toff_gates(decomposed_circuit)

    print_string += f',{ttl_qubits}, {num_Toff_gates}'

    depth_toff   = len(cirq.align_left(decomposed_circuit))
    print_string += f',{depth_toff}\n'

    out_file.write(print_string)