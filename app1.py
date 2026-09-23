import os
import uuid
import base64
import sys

from flask import Flask, render_template, request
from PIL import Image

from facemodule1 import process_uploaded_image

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
ROOT_DIR = os.path.abspath(os.path.join(BASE_DIR, "..", ".."))

if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

from backend.search_module import search_module
from blockchain_module import register_hash, verify_hash


UPLOAD_DIR = os.path.join(BASE_DIR, "uploads")
os.makedirs(UPLOAD_DIR, exist_ok=True)

FACE_MODEL = "hog"
MULTIPLE_FACES_MODE = "largest"

app = Flask(__name__)
app.config["MAX_CONTENT_LENGTH"] = 10 * 1024 * 1024


def classify_result(result):
    if result["reason"] == "success":
        return "success"
    if result["reason"] == "no_face":
        return "no_face"
    if result["reason"] == "multiple_faces":
        return "multiple_faces"
    return "invalid"


def get_image_metadata(image_path):
    try:
        with Image.open(image_path) as img:
            return img.width, img.height, img.format
    except Exception:
        return None, None, None


def build_display_context(result, filename, width, height, image_format):

    encoding_preview = None

    if result["encoding"] is not None:
        encoding_preview = [
            round(float(v), 4)
            for v in result["encoding"][:5]
        ]

    return {
        "success": result["success"],
        "face_detected": result["face_detected"],
        "num_faces": result["num_faces"],
        "face_location": result["face_location"],
        "has_encoding": result["encoding"] is not None,
        "encoding_dimensions": (
            128 if result["encoding"] is not None else None
        ),
        "encoding_preview": encoding_preview,
        "image_hash": result["image_hash"],
        "input_type": result["input_type"],
        "message": result["message"],
        "filename": filename,
        "width": width,
        "height": height,
        "image_format": image_format,
    }


def process_and_render(temp_path, input_type, original_filename):

    # ==========================================
    # 1. FACE DETECTION
    # ==========================================

    result = process_uploaded_image(
        temp_path,
        model=FACE_MODEL,
        multiple_faces=MULTIPLE_FACES_MODE
    )

    result["input_type"] = input_type

    width, height, image_format = get_image_metadata(temp_path)

    display = build_display_context(
        result,
        original_filename,
        width,
        height,
        image_format
    )

    status = classify_result(result)


    search_result = None

    try:
        print("\n🔍 Running reverse image search...")
        search_result = search_module(temp_path)

        if search_result:
            print("✅ Reverse image search result found.")
        else:
            print("⚠️ No reverse image search result.")

    except Exception as e:
        print("❌ Reverse image search failed:", e)


    blockchain_result = None

    try:

        image_hash = result["image_hash"]

        if image_hash:

            print("\n🔎 Checking blockchain...")

            blockchain_result = verify_hash(image_hash)

            if blockchain_result["verified"]:

                print("⚠️ Image already registered on blockchain.")

            else:

                print("⛓️ Image not registered.")
                print("Registering image on blockchain...")

                tx_hash = register_hash(image_hash)

                blockchain_result = verify_hash(image_hash)

                if blockchain_result:
                    blockchain_result["tx_hash"] = tx_hash

                print("✅ Image registered on blockchain.")

    except Exception as e:

        print("❌ Blockchain verification failed:", e)

  

    display["search_result"] = search_result
    display["blockchain_result"] = blockchain_result



    if status == "success":
        final_status = "success"
        final_error = None

    elif status == "no_face":
        final_status = "no_face"
        final_error = result["message"]

    elif status == "multiple_faces":
        final_status = "multiple_faces"
        final_error = result["message"]

    else:
        final_status = None
        final_error = result["message"]

    return render_template(
        "index.html",
        status=final_status,
        error=final_error,
        result=display
    )




@app.route("/")
def index():

    return render_template(
        "index.html",
        status=None,
        error=None,
        result=None
    )




@app.route("/upload", methods=["POST"])
def upload():

    uploaded_file = request.files.get("photo")

    if uploaded_file is None or uploaded_file.filename == "":

        return render_template(
            "index.html",
            status=None,
            error="No file selected. Please choose an image.",
            result=None
        )

    ext = os.path.splitext(
        uploaded_file.filename
    )[1].lower() or ".img"

    temp_path = os.path.join(
        UPLOAD_DIR,
        f"{uuid.uuid4().hex}{ext}"
    )

    uploaded_file.save(temp_path)

    return process_and_render(
        temp_path,
        "upload",
        uploaded_file.filename
    )




@app.route("/capture", methods=["POST"])
def capture():

    data_url = request.form.get("image_data")

    if not data_url or "," not in data_url:

        return render_template(
            "index.html",
            status=None,
            error="No photo was captured. Please try again.",
            result=None
        )

    try:

        header, encoded = data_url.split(",", 1)

        image_bytes = base64.b64decode(encoded)

    except Exception:

        return render_template(
            "index.html",
            status=None,
            error="Captured photo could not be read. Please try again.",
            result=None
        )

    temp_path = os.path.join(
        UPLOAD_DIR,
        f"{uuid.uuid4().hex}.jpg"
    )

    with open(temp_path, "wb") as f:
        f.write(image_bytes)

    return process_and_render(
        temp_path,
        "camera",
        "captured_photo.jpg"
    )



if __name__ == "__main__":

    app.run(
        debug=True,
        host="127.0.0.1",
        port=5000
    )
