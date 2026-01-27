from flask import Flask, request, jsonify, render_template
import json, os, hashlib
from datetime import datetime, timedelta

app = Flask(__name__)
KEY_FILE = "keys.json"

# ================= LOAD / SAVE =================
def load_keys():
    if not os.path.exists(KEY_FILE):
        return {}
    with open(KEY_FILE, "r") as f:
        return json.load(f)

def save_keys(data):
    with open(KEY_FILE, "w") as f:
        json.dump(data, f, indent=4)

# ================= TẠO KEY =================
def generate_key(ip):
    today = datetime.now().strftime("%Y%m%d")
    raw = f"XWORLD-{ip}-{today}"
    h = hashlib.md5(raw.encode()).hexdigest()[:12].upper()
    return f"XWORLD-{h}"

# ================= WEB: LẤY KEY =================
@app.route("/")
def web_get_key():
    ip = request.headers.get("X-Forwarded-For", request.remote_addr)
    keys = load_keys()
    now = datetime.now()

    if ip in keys and now.timestamp() < keys[ip]["expire"]:
        key_data = keys[ip]
    else:
        key = generate_key(ip)
        expire = (now + timedelta(hours=24)).timestamp()
        key_data = {
            "key": key,
            "expire": expire,
            "type": "FREE"
        }
        keys[ip] = key_data
        save_keys(keys)

    return render_template(
        "index.html",
        key=key_data["key"],
        ip=ip,
        expire_ts=key_data["expire"]
    )

# ================= WEB: CHECK KEY =================
@app.route("/check")
def web_check():
    ip = request.headers.get("X-Forwarded-For", request.remote_addr)
    key = request.args.get("key")
    keys = load_keys()
    now = datetime.now().timestamp()

    if ip not in keys or keys[ip]["key"] != key:
        return render_template("check.html", status="invalid", message="KEY không hợp lệ")

    if now > keys[ip]["expire"]:
        return render_template("check.html", status="invalid", message="KEY đã hết hạn")

    return render_template("check.html", status="valid", message="KEY hợp lệ (còn hạn)")

# ================= API: LẤY KEY =================
@app.route("/getkey", methods=["POST"])
def api_get_key():
    data = request.json
    ip = data.get("ip")
    if not ip:
        return jsonify({"error": "missing ip"}), 400

    keys = load_keys()
    now = datetime.now()

    if ip in keys and now.timestamp() < keys[ip]["expire"]:
        return jsonify(keys[ip])

    key = generate_key(ip)
    expire = (now + timedelta(hours=24)).timestamp()
    keys[ip] = {"key": key, "expire": expire, "type": "FREE"}
    save_keys(keys)

    return jsonify(keys[ip])

# ================= API: CHECK KEY =================
@app.route("/checkkey", methods=["POST"])
def api_check_key():
    data = request.json
    ip = data.get("ip")
    key = data.get("key")
    keys = load_keys()
    now = datetime.now().timestamp()

    if not ip or not key:
        return jsonify({"status": "FAIL", "msg": "Thiếu IP hoặc KEY"})

    if ip not in keys or keys[ip]["key"] != key:
        return jsonify({"status": "FAIL", "msg": "KEY sai"})

    if now > keys[ip]["expire"]:
        return jsonify({"status": "EXPIRED", "msg": "KEY đã hết hạn"})

    return jsonify({"status": "OK", "msg": "KEY hợp lệ", "type": keys[ip]["type"]})

app = app