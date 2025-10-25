import os
from flask import Flask, request, jsonify, session, send_file, redirect

app = Flask(__name__)
app.secret_key = "temporary_dev_secret_key"
app.config["SESSION_TYPE"] = "filesystem"
app.config["SESSION_PERMANENT"] = False

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_FOLDER = os.path.join(BASE_DIR, "data")

# ===== ROUTES =====

@app.route("/")
def home():
    if "username" in session:
        return redirect("/index.html")
    return redirect("/login.html")

@app.route("/login.html")
def login_page():
    if "username" in session:
        return redirect("/index.html")
    return send_file(os.path.join(BASE_DIR, "login.html"))

@app.route("/index.html")
def index_page():
    if "username" not in session:
        return redirect("/login.html")
    return send_file(os.path.join(BASE_DIR, "index.html"))

@app.route("/about.html")
def about_page():
    if "username" not in session:
        return redirect("/login.html")
    return send_file(os.path.join(BASE_DIR, "about.html"))

@app.route("/files.html")
def files_page():
    if "username" not in session:
        return redirect("/login.html")
    return send_file(os.path.join(BASE_DIR, "files.html"))

@app.route("/logout")
def logout():
    session.clear()
    return redirect("/login.html")

# ===== API LOGIN =====

@app.route("/api/login", methods=["POST"])
def api_login():
    data = request.json or {}
    username = data.get("username", "").strip()
    password = data.get("password", "").strip()

    if username and password:
        session["username"] = username
        return jsonify({"success": True})
    return jsonify({"success": False, "error": "Missing username or password"}), 400

# ===== SEARCH =====

@app.route("/search", methods=["POST"])
def search():
    if "username" not in session:
        return jsonify({"results": [], "error": "Not logged in"}), 401

    body = request.json or {}
    query = (body.get("email") or "").strip().lower()
    if not query:
        return jsonify({"results": []})

    results = {}
    if not os.path.exists(DATA_FOLDER):
        return jsonify({"results": []})

    MAX_MATCHES_PER_FILE = 100

    for root, _, files in os.walk(DATA_FOLDER):
        for filename in files:
            if filename.lower().endswith((".txt", ".csv", ".log", ".json")):
                path = os.path.join(root, filename)
                try:
                    matches = []
                    with open(path, "r", encoding="utf-8", errors="ignore") as f:
                        for line in f:
                            if query in line.lower():
                                matches.append(line.strip())
                                if len(matches) >= MAX_MATCHES_PER_FILE:
                                    break
                    if matches:
                        results[filename] = matches
                except Exception as e:
                    print(f"Error reading {filename}: {e}")

    formatted = [{"file": fn, "matches": lines} for fn, lines in results.items()]
    return jsonify({"results": formatted})

# ===== FILES API =====

@app.route("/api/files")
def list_files():
    if "username" not in session:
        return jsonify({"error": "Not logged in"}), 401
    files = []
    for f in os.listdir(DATA_FOLDER):
        path = os.path.join(DATA_FOLDER, f)
        if os.path.isfile(path):
            size = os.path.getsize(path)
            files.append({"name": f, "size": size})
    return jsonify(files)

if __name__ == "__main__":
    app.run(debug=True)
