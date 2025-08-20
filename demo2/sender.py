import argparse
import asyncio
import json
import logging
from typing import Optional, Dict, Any, List

from aiortc import RTCPeerConnection, RTCSessionDescription
from aiortc.contrib.media import MediaPlayer
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


async def run(room: str, signaling_url: str, stun_urls: List[str], turn_url: Optional[str], turn_username: Optional[str], turn_password: Optional[str], video: Optional[str], audio: Optional[str]):
    pc = RTCPeerConnection(build_ice_servers(stun_urls, turn_url, turn_username, turn_password))

    # Create capture from default devices or explicit sources
    # For Windows camera via ffmpeg/dshow, you may pass: video="video=Integrated Camera" and audio="audio=Microphone (Realtek...)"
    player = MediaPlayer(video, format=None) if video else MediaPlayer(None)
    if audio and audio != "default":
        # If explicit audio device provided, create a second player for audio-only and use its audio track
        audio_player = MediaPlayer(audio, format=None)
        if audio_player.audio:
            pc.addTrack(audio_player.audio)
    else:
        if player.audio:
            pc.addTrack(player.audio)

    if player.video:
        pc.addTrack(player.video)

    async with websockets.connect(signaling_url) as ws:
        await ws.send(json.dumps({"type": "join", "room": room}))

        offer = await pc.createOffer()
        await pc.setLocalDescription(offer)

        await ws.send(json.dumps({
            "type": "offer",
            "sdp": pc.localDescription.sdp,
            "sdpType": pc.localDescription.type
        }))

        @pc.on("icecandidate")
        async def on_icecandidate(event):
            if event.candidate:
                await ws.send(json.dumps({
                    "type": "candidate",
                    "candidate": event.candidate.to_sdp(),
                    "sdpMid": event.candidate.sdp_mid,
                    "sdpMLineIndex": event.candidate.sdp_mline_index,
                }))

        async for raw in ws:
            msg = json.loads(raw)

            if msg.get("type") == "answer":
                sdp = msg.get("sdp") or msg.get("description", {}).get("sdp")
                await pc.setRemoteDescription(RTCSessionDescription(sdp=sdp, type="answer"))

            elif msg.get("type") == "candidate":
                candidate = msg.get("candidate")
                sdp_mid = msg.get("sdpMid")
                sdp_mline_index = msg.get("sdpMLineIndex")
                payload = candidate if isinstance(candidate, dict) else {
                    "candidate": candidate,
                    "sdpMid": sdp_mid,
                    "sdpMLineIndex": sdp_mline_index,
                }
                try:
                    await pc.addIceCandidate(payload)
                except Exception:
                    pass


def parse_args():
    p = argparse.ArgumentParser()
    p.add_argument("--room", default="room1")
    p.add_argument("--signaling", default="ws://localhost:8765")
    p.add_argument("--stun", action="append", default=["stun:stun.l.google.com:19302"], help="Repeatable STUN server url")
    p.add_argument("--turn-url", default=None, help="TURN url, e.g. turn:turn.example.com:3478?transport=udp")
    p.add_argument("--turn-username", default=None)
    p.add_argument("--turn-password", default=None)
    p.add_argument("--video", default=None, help="Video source. For Windows dshow: video=Integrated Camera. If omitted, default device.")
    p.add_argument("--audio", default=None, help="Audio source. For Windows dshow: audio=Microphone (Realtek...). If omitted, default device.")
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
                        video=args.video,
                        audio=args.audio))
    except KeyboardInterrupt:
        pass


