import asyncio
import websockets
import json

rooms = {}

async def handler(websocket):
    room = None
    try:
        message = await websocket.recv()
        data = json.loads(message)

        if data.get('type') == 'join':
            room = data['room']
            if room not in rooms:
                rooms[room] = set()
            rooms[room].add(websocket)
            print(f"Client joined room '{room}'. Total clients in room: {len(rooms[room])}")

            async for message in websocket:
                for client in rooms[room]:
                    if client != websocket:
                        await client.send(message)
    except websockets.exceptions.ConnectionClosedError:
        print(f"Client disconnected from room '{room}'")
    finally:
        if room and websocket in rooms[room]:
            rooms[room].remove(websocket)
            if not rooms[room]:
                del rooms[room]
                print(f"Room '{room}' is now empty and closed.")


async def main():
    async with websockets.serve(handler, "0.0.0.0", 8765):
        print("Signaling server 0.0.0.0:8765 is running...")
        await asyncio.Future()  # Sonsuza kadar çalış


if __name__ == "__main__":
    asyncio.run(main())