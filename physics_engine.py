import numpy as np
from scipy.linalg import solve_banded

# Spatial Resolution
N = 1000
 
# Displacement
dx = 0.05
dt = (dx**2) / 4

# Kinetic Energy Coefficient
K = 1/(2*dx**2)

# Potential Energy Array Base
V = np.zeros(N)
barrier_width = 10
barrier_height = 50
V[500 - barrier_width : 500 + barrier_width] = barrier_height

# Crank-Nicolson
A_neighbour = -0.5j * dt * K
B_neighbour = 0.5j * dt * K

A_center = 1.0 + 0.5j * dt * (2*K + V)
B_center = 1.0 - 0.5j * dt * (2*K + V)

A_band = np.zeros((3, N), dtype=complex)
B_band = np.zeros((3, N), dtype=complex)

A_band[0,1:], A_band[1,:], A_band[2,:-1] = A_neighbour, A_center , A_neighbour
B_band[0,1:], B_band[1,:], B_band[2,:-1] = B_neighbour, B_center, B_neighbour

# Spatial Grid from 0 to N*dx
x = np.linspace(0, N*dx, N)

# Shape
x0 = 15.0
sigma = 1.0
envelope = np.exp(-((x - x0) ** 2) / (4 * sigma ** 2))

# Momentum
k0 = 10.0
phase = np.exp(1j * k0 * x)

#
psi = envelope * phase

def step(psi):
    b = np.zeros(N, dtype=complex)
    b[0]    = B_center[0]*psi[0]   + B_neighbour*psi[1]
    b[1:-1] = B_neighbour*psi[:-2] + B_center[1:-1]*psi[1:-1] + B_neighbour*psi[2:]
    b[-1]   = B_neighbour*psi[-2]  + B_center[-1]*psi[-1]
    psi = solve_banded((1, 1), A_band, b)
    psi[0] = 0
    psi[-1] = 0
    return psi