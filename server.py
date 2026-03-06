import os
import pymysql
from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
from werkzeug.utils import secure_filename
from flaskext.mysql import MySQL

app = Flask(__name__)
CORS(app)

UPLOAD_FOLDER = 'uploads'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

mysql = MySQL()

# ================= DATABASE =================
app.config['MYSQL_DATABASE_USER'] = 'root'
app.config['MYSQL_DATABASE_PASSWORD'] = ''
app.config['MYSQL_DATABASE_DB'] = 'asset_management'
app.config['MYSQL_DATABASE_HOST'] = 'localhost'

mysql.init_app(app)

# ================= LOGIN =================
@app.route("/login", methods=["POST"])
def login():
    data = request.json

    conn = mysql.connect()
    cursor = conn.cursor(pymysql.cursors.DictCursor)

    cursor.execute("""
        SELECT user_id,first_name,last_name,email,username,role
        FROM users
        WHERE username=%s AND password=%s
    """,(data["username"], data["password"]))

    user = cursor.fetchone()

    cursor.close()
    conn.close()

    if user:
        return jsonify({"status":"success","user":user})
    else:
        return jsonify({"status":"error"}),401
# ================= REGISTER =================
@app.route("/register", methods=["POST"])
def register():
    data = request.json

    conn = mysql.connect()
    cursor = conn.cursor()

    cursor.execute("""
        INSERT INTO users
        (first_name,last_name,email,username,password,role)
        VALUES (%s,%s,%s,%s,%s,'user')
    """,(
        data["first_name"],
        data["last_name"],
        data["email"],
        data["username"],
        data["password"]
    ))

    conn.commit()
    cursor.close()
    conn.close()

    return jsonify({"message":"success"})


# ================= GET ASSETS =================
@app.route("/assets", methods=["GET"])
def get_assets():

    search = request.args.get("search")

    conn = mysql.connect()
    cursor = conn.cursor(pymysql.cursors.DictCursor)

    if search:
        cursor.execute("""
        SELECT a.*, t.type_name
        FROM assets a
        LEFT JOIN asset_types t ON a.type_id = t.type_id
        WHERE a.asset_name LIKE %s
        OR a.asset_code LIKE %s
        """,('%'+search+'%','%'+search+'%'))

    else:
        cursor.execute("""
        SELECT a.*, t.type_name
        FROM assets a
        LEFT JOIN asset_types t ON a.type_id = t.type_id
        """)

    data = cursor.fetchall()

    cursor.close()
    conn.close()

    return jsonify(data)


# ================= GET ASSET BY CODE =================
@app.route("/assets/code/<string:code>", methods=["GET"])
def get_asset_by_code(code):

    conn = mysql.connect()
    cursor = conn.cursor(pymysql.cursors.DictCursor)

    cursor.execute("""
    SELECT a.*, t.type_name
    FROM assets a
    LEFT JOIN asset_types t ON a.type_id = t.type_id
    WHERE a.asset_code=%s
    """,(code,))

    asset = cursor.fetchone()

    cursor.close()
    conn.close()

    if asset:
        return jsonify(asset)
    else:
        return jsonify({"message":"not found"}),404


# ================= GET TYPES =================
@app.route("/types", methods=["GET"])
def get_types():

    conn = mysql.connect()
    cursor = conn.cursor(pymysql.cursors.DictCursor)

    cursor.execute("SELECT * FROM asset_types")

    data = cursor.fetchall()

    cursor.close()
    conn.close()

    return jsonify(data)


# ================= ADD ASSET =================
@app.route("/assets", methods=["POST"])
def add_asset():

    data = request.json

    conn = mysql.connect()
    cursor = conn.cursor()

    cursor.execute("""
    INSERT INTO assets
    (asset_code,asset_name,type_id,brand,location,description,status,image)
    VALUES (%s,%s,%s,%s,%s,%s,%s,%s)
    """,(
        data["asset_code"],
        data["asset_name"],
        data["type_id"],
        data["brand"],
        data["location"],
        data["description"],
        data["status"],
        data["image"]
    ))

    conn.commit()

    cursor.close()
    conn.close()

    return jsonify({"message":"added"})


# ================= UPDATE ASSET =================
@app.route("/assets/<int:id>", methods=["PUT"])
def update_asset(id):

    data = request.json

    conn = mysql.connect()
    cursor = conn.cursor()

    cursor.execute("""
    UPDATE assets SET
        asset_code=%s,
        asset_name=%s,
        brand=%s,
        location=%s,
        description=%s,
        status=%s
    WHERE asset_id=%s
    """,(
        data["asset_code"],
        data["asset_name"],
        data["brand"],
        data["location"],
        data["description"],
        data["status"],
        id
    ))

    conn.commit()

    cursor.close()
    conn.close()

    return jsonify({"message":"updated"})

# ================= DELETE =================
@app.route("/assets/<int:id>", methods=["DELETE"])
def delete_asset(id):

    conn = mysql.connect()
    cursor = conn.cursor()

    cursor.execute("DELETE FROM assets WHERE asset_id=%s",(id,))
    conn.commit()

    cursor.close()
    conn.close()

    return jsonify({"message":"deleted"})


# ================= DASHBOARD =================
@app.route("/dashboard", methods=["GET"])
def dashboard():

    conn = mysql.connect()
    cursor = conn.cursor(pymysql.cursors.DictCursor)

    cursor.execute("SELECT COUNT(*) total FROM assets")
    total = cursor.fetchone()["total"]

    cursor.execute("SELECT COUNT(*) normal FROM assets WHERE status='ปกติ'")
    normal = cursor.fetchone()["normal"]

    cursor.execute("SELECT COUNT(*) repair FROM assets WHERE status='แจ้งซ่อม'")
    repair = cursor.fetchone()["repair"]

    cursor.execute("SELECT COUNT(*) disposed FROM assets WHERE status='จำหน่ายออก'")
    disposed = cursor.fetchone()["disposed"]

    cursor.close()
    conn.close()

    return jsonify({
        "total":total,
        "normal":normal,
        "repair":repair,
        "disposed":disposed
    })


# ================= UPLOAD IMAGE =================
@app.route("/upload", methods=["POST"])
def upload():

    file = request.files['file']
    filename = secure_filename(file.filename)

    file.save(os.path.join(UPLOAD_FOLDER, filename))

    return jsonify({"filename":filename})


@app.route("/uploads/<filename>")
def uploaded_file(filename):
    return send_from_directory(UPLOAD_FOLDER, filename)


# ================= START SERVER =================
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)