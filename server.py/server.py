import nest_asyncio
nest_asyncio.apply()

from quart import Quart, request, jsonify, send_from_directory
from quart_cors import cors
from aiortc import RTCPeerConnection, RTCSessionDescription, RTCIceCandidate

app = Quart(__name__, static_folder=".")
app = cors(app, allow_origin="*")

pcs = {}  

@app.route("/")
async def index():
    return await send_from_directory(".", "webrtc_remote_recorder.html")

@app.route("/offer", methods=["POST"])
async def offer():
    params = await request.get_json()
    peer_id = params.get("peer_id")
    if not peer_id:
        return jsonify({"error": "peer_id gerekli"}), 400

    if peer_id not in pcs:
        pc = RTCPeerConnection()
        pc.candidate_buffer = []
        pcs[peer_id] = pc

        @pc.on("track")
        def on_track(track):
            print(f"{peer_id} için yeni track geldi:", track.kind)

    else:
        pc = pcs[peer_id]

   
    if "sdp" in params and "type" in params:
        offer = RTCSessionDescription(sdp=params["sdp"], type=params["type"])
        await pc.setRemoteDescription(offer)

       
        for c in pc.candidate_buffer:
            await pc.addIceCandidate(c)
        pc.candidate_buffer = []

        answer = await pc.createAnswer()
        await pc.setLocalDescription(answer)
        return jsonify({
            "sdp": pc.localDescription.sdp,
            "type": pc.localDescription.type
        })

    
    elif "candidate" in params:
        candidate = params["candidate"]
        ice_candidate = RTCIceCandidate(
            sdpMid=candidate["sdpMid"],
            sdpMLineIndex=candidate["sdpMLineIndex"],
            candidate=candidate["candidate"]
        )
        if not pc.remoteDescription:
            pc.candidate_buffer.append(ice_candidate)
        else:
            await pc.addIceCandidate(ice_candidate)
        return jsonify({"status": "candidate eklendi"})

    return jsonify({"status": "bilinmeyen istek"}), 400

if __name__ == "__main__":
    import uvicorn
    host = "0.0.0.0"
    port = 5000
    print(f"Server çalışıyor: http://{host}:{port}")
    uvicorn.run(app, host=host, port=port)



