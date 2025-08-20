import asyncio
import json
import logging
from typing import Dict, Set

import websockets


logging.basicConfig(level=logging.INFO)

# Room name -> set of websocket connections
rooms: Dict[str, Set[object]] = {}


async def handler(websocket):
    room_name = None
    try:
        # Expect first message to be a room join
        raw = await websocket.recv()
        msg = json.loads(raw)
        if msg.get("type") != "join" or "room" not in msg:
            await websocket.close(code=1002, reason="First message must be a room join")
            return

        room_name = str(msg["room"]) or "default"
        if room_name not in rooms:
            rooms[room_name] = set()
        rooms[room_name].add(websocket)
        logging.info("Client joined room '%s' (size=%d)", room_name, len(rooms[room_name]))

        # Fan-out all subsequent messages to other peers in the same room
        async for raw in websocket:
            try:
                # Validate JSON but do not enforce schema; this is a relay
                _ = json.loads(raw)
            except Exception:
                # Ignore non-JSON messages
                continue

            targets = [ws for ws in rooms.get(room_name, set()) if ws is not websocket]
            if not targets:
                continue

            await asyncio.gather(*[t.send(raw) for t in targets], return_exceptions=True)

    except websockets.exceptions.ConnectionClosed:
        pass
    finally:
        if room_name and websocket in rooms.get(room_name, set()):
            rooms[room_name].remove(websocket)
            if not rooms[room_name]:
                del rooms[room_name]
                logging.info("Room '%s' is now empty and closed", room_name)


async def main(host: str = "0.0.0.0", port: int = 8765):
    async with websockets.serve(handler, host, port, ping_interval=20, ping_timeout=20):
        logging.info("Signaling server listening on ws://%s:%d", host, port)
        await asyncio.Future()  # run forever


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        pass


