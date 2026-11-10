import asyncio
from email import message
import threading
import websockets
import struct
import numpy as np
from flask import Flask, send_from_directory
import physics_engine as pe

app = Flask(__name__)
psi = pe.envelope * pe.phase
paused = True

@app.route("/")
def index():
    return send_from_directory(".", "index.html")

def get_prob():
    prob = np.abs(psi)**2
    total = np.sum(prob)
    left = np.sum(prob[:500]) / total
    right = np.sum(prob[500:]) / total
    return prob, left, right

async def simulate(websocket):
    global psi, paused

    await asyncio.sleep(0.1)
    prob, left, right = get_prob()
    data_bytes = struct.pack(f'{len(prob)}f', *prob) + struct.pack('2f', left, right)
    await websocket.send(data_bytes)

    async def receive():
        global psi, paused
        async for message in websocket:
            if message == "reset":
                psi = pe.envelope * pe.phase
                paused = True
                prob, left, right = get_prob()
                data_bytes = struct.pack(f'{len(prob)}f', *prob) + struct.pack('2f', left, right)
                await websocket.send(data_bytes)
            elif message == "pause":
                paused = True
            elif message == "resume":
                paused = False
            elif message.startswith("barrier:"):
                parts = message.split(":")
                barrier_height = float(parts[1])
                barrier_width = int(parts[2])
                momentum = float(parts[3])
                pe.V[:] = 0 
                pe.V[500 - barrier_width : 500 + barrier_width] = barrier_height
                pe.A_center[:] = 1.0 + 0.5j * pe.dt * (2*pe.K + pe.V)
                pe.B_center[:] = 1.0 - 0.5j * pe.dt * (2*pe.K + pe.V)
                pe.A_band[1,:] = pe.A_center
                pe.B_band[1,:] = pe.B_center
                pe.k0 = momentum
                pe.phase = np.exp(1j * pe.k0 * pe.x)
                psi = pe.envelope * pe.phase
                paused = True
                await websocket.send(data_bytes)

    async def send():
        global psi, paused
        while True:
            if not paused:
                for _ in range(10):
                    psi = pe.step(psi)
                prob, left, right = get_prob()
                data_bytes = struct.pack(f'{len(prob)}f', *prob) + struct.pack('2f', left, right)
                await websocket.send(data_bytes)
            await asyncio.sleep(0)

    await asyncio.gather(receive(), send())

async def main():
    async with websockets.serve(simulate, "localhost", 8765):
        await asyncio.Future()

def run_flask():
    app.run(port=5001, debug=False, use_reloader=False)

if __name__ == "__main__":
    threading.Thread(target=run_flask).start()
    asyncio.run(main())