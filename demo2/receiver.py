import argparse
import asyncio
import json
import logging
from typing import Optional, Dict, Any, List

from aiortc import RTCPeerConnection, RTCSessionDescription
from aiortc.sdp import candidate_from_sdp, candidate_to_sdp
from aiortc.contrib.media import MediaBlackhole, MediaRecorder
import websockets


logging.basicConfig(level=logging.INFO)


def build_ice_servers(stun_urls: List[str], turn_url: Optional[str], turn_username: Optional[str], turn_password: Optional[str]) -> Dict[str, Any]:
    ice_servers: List[Dict[str, Any]] = []
    if stun_urls:
        ice_servers.append({"urls": stun_urls})
    if turn_url:
        turn_entry: Dict[str, Any] = {"urls": [turn_url]}
        if turn_username:
            turn_entry["username"] = turn_username
        if turn_password:
            turn_entry["credential"] = turn_password
        ice_servers.append(turn_entry)
    return {"iceServers": ice_servers}


async def run(room: str, signaling_url: str, stun_urls: List[str], turn_url: Optional[str], turn_username: Optional[str], turn_password: Optional[str], record_to: Optional[str]):
    pc = RTCPeerConnection(build_ice_servers(stun_urls, turn_url, turn_username, turn_password))

    recorder = MediaRecorder(record_to) if record_to else MediaBlackhole()

    @pc.on("track")
    def on_track(track):
        if track.kind == "audio" or track.kind == "video":
            recorder.addTrack(track)

    await recorder.start()

    async with websockets.connect(signaling_url) as ws:
        await ws.send(json.dumps({"type": "join", "room": room}))

        answer_sent = False

        @pc.on("icecandidate")
        async def on_icecandidate(event):
            if event.candidate:
                await ws.send(json.dumps({
                    "type": "candidate",
                    "candidate": candidate_to_sdp(event.candidate),
                    "sdpMid": event.candidate.sdp_mid,
                    "sdpMLineIndex": event.candidate.sdp_mline_index,
                }))

        async for raw in ws:
            msg = json.loads(raw)

            if msg.get("type") == "offer" and not answer_sent:
                sdp = msg.get("sdp") or msg.get("description", {}).get("sdp")
                await pc.setRemoteDescription(RTCSessionDescription(sdp=sdp, type="offer"))
                answer = await pc.createAnswer()
                await pc.setLocalDescription(answer)
                await ws.send(json.dumps({
                    "type": "answer",
                    "sdp": pc.localDescription.sdp,
                    "sdpType": pc.localDescription.type
                }))
                answer_sent = True

            elif msg.get("type") == "candidate":
                cand = msg.get("candidate")
                sdp_mid = msg.get("sdpMid")
                sdp_mline_index = msg.get("sdpMLineIndex")
                try:
                    if isinstance(cand, str):
                        ice = candidate_from_sdp(cand)
                        ice.sdpMid = sdp_mid
                        ice.sdpMLineIndex = sdp_mline_index
                        await pc.addIceCandidate(ice)
                    else:
                        await pc.addIceCandidate(cand)
                except Exception:
                    pass

    await recorder.stop()


def parse_args():
    p = argparse.ArgumentParser()
    p.add_argument("--room", default="room1")
    p.add_argument("--signaling", default="ws://localhost:8765")
    p.add_argument("--stun", action="append", default=["stun:stun.l.google.com:19302"], help="Repeatable STUN server url")
    p.add_argument("--turn-url", default=None, help="TURN url, e.g. turn:turn.example.com:3478?transport=udp")
    p.add_argument("--turn-username", default=None)
    p.add_argument("--turn-password", default=None)
    p.add_argument("--record", default=None, help="Output file (e.g. output.mp4 or output.webm)")
    return p.parse_args()


if __name__ == "__main__":
    args = parse_args()
    try:
        asyncio.run(run(room=args.room,
                        signaling_url=args.signaling,
                        stun_urls=args.stun,
                        turn_url=args.turn_url,
                        turn_username=args.turn_username,
                        turn_password=args.turn_password,
                        record_to=args.record))
    except KeyboardInterrupt:
        pass


