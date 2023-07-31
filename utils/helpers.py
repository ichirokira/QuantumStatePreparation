import numpy as np
import cirq

"""
Define some helper functions especially for Gaussian 1D state preparation in https://arxiv.org/abs/2110.05708
"""

def rot_angles(m: int, sigma: float) -> list:
  """
  Compute a vector of angles based on Eq.87
  """

  angles = []
  for l in range(0, m-1):
    norm_factor = 1 + sum([(2**i) * np.exp((-2**(2*(i-1)))/(2*sigma**2)) for i in range(1, l+1)])

    angle = 2**(l/2)*np.sqrt(2/norm_factor)*np.exp((-2**(2*l))/(4*sigma**2))

    angles.append(angle)
  return angles

def angle_to_register(ang_register: list, theta: float) -> cirq.Circuit:
  """
  Compute p-bit approximation for theta/(2*np.pi) and store the result in the ang_register.
  Note that the least significant bit will be stored at the right most qubit.
  """

  # Compute p-bit approximation
  angle = theta/(2*np.pi)
  p = len(ang_register)
  angle_apprx = format(int(np.floor(2**p * angle)), "b").zfill(p) # convert to binary string

  # Store angle_apprx to ang_register
  circuit = cirq.Circuit()
  for qubit, value in zip(ang_register, angle_apprx):
    if value == "1":
      circuit.append(cirq.X(qubit))

  return circuit


def ratio_to_register(out: int, sigma: float,
                      tmp_register: list) -> cirq.Circuit:
  """
  Compute ratio based on the index `out` from out_register and store the result
  in the tmp_register.

  This function implements Eq.81 in the paper.

  Args:
      - out: an index value in out_register
      - sigma: std value of the target gaussian function
      - tmp_register: qubit register that stores the value of ratio
  Return:
      A cirq.Circuit() store value of r_out to tmp_register
  """

  # Calculate t-bit approximation of ratio
  t = len(tmp_register)

  if out == 0:
    r_out =  1
  else:
    r_out = np.exp((2**(2*np.floor(np.log2(out)))-out**2)/(4*sigma**2))

  if r_out < 1:
    r_out = (np.floor(2**t * r_out))

  r_out = format(int(r_out), "b").zfill(t) # convert to binary string

  assert len(r_out) == t

  # Store the value in tmp_register
  circuit = cirq.Circuit()
  for qubit, value in zip(tmp_register, r_out):
    if value == "1":
      circuit.append(cirq.X(qubit))
  return circuit

def rot_circuit(out:  cirq.NamedQubit, ang_register: list,
                controlled_qubit: cirq.NamedQubit) -> cirq.Circuit:
    """
    Implement the following operations Eq.73 and Eq.88:
      if controled_qubit is not None:
        ROT|ang>|out> -> |ang>(cos(2*pi*ang)|0>_out+sin(2*pi*ang)|1>_out)
      else:
        CROT|controlled_qubit>|ang>|out> -> |controlled_qubit>ROT^(1-controlled_bit)|ang>|out>
    """
    circuit = cirq.Circuit()
    for i, qubit in enumerate(ang_register):
      circuit.append(cirq.Ry(rads = 2**(-(i+1))).on(out).controlled_by(qubit))

    if controlled_qubit:
      controlled_circuit = cirq.Circuit()
      circuit_op = cirq.CircuitOperation(circuit.freeze())
      controlled_circuit.append(circuit_op.controlled_by(controlled_qubit, control_values=[0]))
      return controlled_circuit
      # for op in circuit.all_operations():
      #   print(op)
      #   circuit.append(op.controlled_by(controlled_qubit, control_values=[0]))
      # return circuit
    else:
      return circuit
