import nest_asyncio
nest_asyncio.apply()

from quart import Quart, request, jsonify, send_from_directory
from quart_cors import cors

app = Quart(__name__, static_folder=".")  
app = cors(app, allow_origin="*")

room_data = {
    "offer": None,
    "answer": None,
    "candidates": []
}

@app.route("/")
async def index():
    return await send_from_directory(".", "webrtc_remote_recorder.html")

@app.route("/data", methods=["GET", "POST"])
async def data():
    global room_data

    if request.method == "POST":
        payload = await request.get_json()
        if payload.get("type") == "offer":
            room_data = {"offer": payload, "answer": None, "candidates": []}
            print("Offer alındı ve saklandı.")
        elif payload.get("type") == "answer":
            room_data["answer"] = payload
            print("Answer alındı ve saklandı.")
        elif payload.get("candidate"):
            room_data["candidates"].append(payload)
            print("Candidate alındı ve saklandı.")
        return jsonify({"status": "ok"})

    elif request.method == "GET":
        return jsonify(room_data)

if __name__ == "__main__":  
    import uvicorn

    host = "0.0.0.0"
    port = 5000

    ssl_keyfile = "key.pem"
    ssl_certfile = "cert.pem"

    print(f"Server HTTPS olarak çalışıyor: https://{host}:{port}")
    uvicorn.run(
        app,
        host=host,
        port=port,
        ssl_keyfile=ssl_keyfile,
        ssl_certfile=ssl_certfile
    )
