# Quantum Tunneling Simulator

An interactive, real-time simulation of a quantum wave packet hitting a potential barrier, visualized in the browser and powered by a Python physics engine.

## What is this?

This project simulates the time evolution of a quantum particle's wave function ψ(x, t) as it travels toward a potential barrier inside a box with hard walls. Depending on the barrier's height, its width, and the particle's momentum, part of the wave packet **reflects** off the barrier and part **tunnels** through. The walls and the barrier together form two quantum wells.

The simulation displays the probability density |ψ(x, t)|² as a live animated curve, along with the percentage of probability on each side of the barrier (reflected vs. tunneled).

## The Physics

The simulation solves the 1D time-dependent Schrödinger equation:

```
iħ ∂ψ/∂t = -ħ²/(2m) ∂²ψ/∂x² + V(x)ψ
```

in natural units (ħ = m = 1), so the wave packet's kinetic energy is about k0²/2.

It uses the **Crank-Nicolson method**, which averages the forward Euler (explicit) and backward Euler (implicit) updates. This gives a tridiagonal linear system at each step, solved with `scipy.linalg.solve_banded`. That function only works with the three non-zero diagonals rather than the full 1000×1000 matrix, which is much more efficient. Crank-Nicolson is second-order accurate in time and unconditionally stable. It is also the Cayley form of the time-evolution operator, so it is unitary and conserves total probability, which plain Euler methods do not.

The initial state is a Gaussian wave packet with an initial momentum:

```
ψ(x, 0) = exp(-(x - x0)² / 4σ²) · exp(i k0 x)
```

V(x) is zero everywhere except inside the barrier. Try comparing the barrier height to the particle's kinetic energy (~k0²/2) and see how the reflected and tunneled fractions change.

## How It's Built

**Backend (Python)**
- `physics_engine.py` sets up the spatial grid, the initial wave packet, and the Crank-Nicolson matrices. Each call to `step()` advances ψ by one time step.
- `main.py` runs a Flask server (serves the page) and a WebSocket server (streams simulation data) in separate threads.

**Frontend (HTML/JS)**
- A `<canvas>` draws |ψ|² as an animated line, with the barrier shown as a shaded region.
- A WebSocket connection receives binary-packed data every frame.
- Sliders control barrier height, barrier width, and wave packet momentum.
- Live readouts show the reflected and tunneled probabilities.

**Why WebSockets and binary data?** An earlier version used HTTP polling with JSON. It worked but lagged, since every frame needed a full request/response cycle and about 1000 floats had to be parsed as text. Switching to a persistent WebSocket, with data packed using Python's `struct` module and read into a `Float32Array` in JavaScript, made the animation much smoother.

## Controls

| Control | Effect |
|---|---|
| **Reset** | Restores the initial Gaussian wave packet |
| **Play / Pause** | Starts or stops the time evolution |
| **Barrier Height** | Sets the potential energy of the barrier |
| **Barrier Width** | Sets the barrier's half-width in grid points (the barrier spans twice this value) |
| **Momentum** | Sets the wave packet's initial momentum k0 |

Changing a slider resets the wave packet and pauses the simulation, so press play to run it again.

## Running It Locally

```bash
pip install flask websockets numpy scipy
python main.py
```

Then open `http://localhost:5001` in your browser.

## Limitations

- 1D only, in natural units, with hard-wall boundaries. Waves reflect off the box edges, so long runs include wall effects.
- A discretized model with finite grid resolution, so it approximates the continuous physics rather than reproducing it exactly.

## What I Learned

I started this project from an interest in quantum physics and computational modeling. My first version used a 100-point grid with a discretized Hamiltonian stepped forward each frame, animated with Dash. It was rough, but it gave me enough understanding to build something better.

The next version tracked the probability density while evolving ψ on a 1000-point grid with the Crank-Nicolson method. I multiplied the Gaussian envelope by a complex exponential, exp(i k0 x), to give the packet momentum. An explicit time step is not unitary, so the wave function's norm drifts. Crank-Nicolson avoids this because it is a Cayley transform of the Hamiltonian.

As I added more to the JavaScript side, including the live probabilities, the animation started to lag. I tuned the number of steps per frame, then replaced HTTP polling with a WebSocket connection, so Python could push data continuously instead of waiting for a request each frame.
