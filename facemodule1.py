import os
import io
import hashlib
import cv2
import numpy as np
from PIL import Image
import face_recognition


VALID_MULTIPLE_FACES_MODES = {"first", "largest", "reject"}
VALID_MODELS = {"hog", "cnn"}
MAX_DIMENSION = 1600

MSG_CANNOT_OPEN = "Could not open or process the image."
MSG_NO_FACE = "No face detected. Please upload another photo or capture a new photo."
MSG_MULTIPLE_FACES = "Multiple faces detected. Please provide an image containing one face."
MSG_SUCCESS = "Face detected and encoded successfully."


def _empty_result(input_type="upload"):
    return {
        "success": False,
        "face_detected": False,
        "encoding": None,
        "image_bytes": None,
        "image_hash": None,
        "num_faces": 0,
        "face_location": None,
        "input_type": input_type,
        "message": "",
        "reason": None,
    }


def calculate_image_hash(image_path):
    if not os.path.isfile(image_path):
        return None
    with open(image_path, "rb") as f:
        data = f.read()
    return hashlib.sha256(data).hexdigest()


def _hash_bytes(image_bytes):
    return hashlib.sha256(image_bytes).hexdigest()


def _validate_and_load_image(image_path):
    if not os.path.isfile(image_path):
        raise ValueError(f"File not found: {image_path}")

    with open(image_path, "rb") as f:
        image_bytes = f.read()

    if len(image_bytes) == 0:
        raise ValueError("Image file is empty.")

    try:
        verify_img = Image.open(io.BytesIO(image_bytes))
        verify_img.verify()
        pil_image = Image.open(io.BytesIO(image_bytes))
        pil_image.load()
    except Exception as e:
        raise ValueError(f"Could not open or decode image: {e}")

    return pil_image, image_bytes


def normalize_image_to_rgb_array(pil_image):
    if pil_image.mode != "RGB":
        pil_image = pil_image.convert("RGB")

    rgb_array = np.asarray(pil_image, dtype=np.uint8)

    if rgb_array.ndim != 3 or rgb_array.shape[2] != 3:
        raise ValueError(f"Unexpected image shape after normalization: {rgb_array.shape}")

    return rgb_array


def _resize_for_detection(rgb_array, max_dimension=MAX_DIMENSION):
    h, w = rgb_array.shape[:2]
    largest_side = max(h, w)

    if largest_side <= max_dimension:
        return rgb_array, 1.0

    scale = max_dimension / float(largest_side)
    new_w = max(1, int(w * scale))
    new_h = max(1, int(h * scale))
    resized = cv2.resize(rgb_array, (new_w, new_h), interpolation=cv2.INTER_AREA)
    return resized, scale


def _scale_location(location, scale):
    top, right, bottom, left = location
    inv = 1.0 / scale
    return (
        int(top * inv),
        int(right * inv),
        int(bottom * inv),
        int(left * inv),
    )


def _largest_face(face_locations):
    def area(loc):
        top, right, bottom, left = loc
        return (bottom - top) * (right - left)
    return max(face_locations, key=area)


def _select_face(face_locations, multiple_faces):
    if len(face_locations) == 1:
        return face_locations[0]
    if multiple_faces == "reject":
        return None
    if multiple_faces == "first":
        return face_locations[0]
    return _largest_face(face_locations)


def process_uploaded_image(image_path, model="hog", multiple_faces="reject"):
    result = _empty_result("upload")

    try:
        pil_image, image_bytes = _validate_and_load_image(image_path)
    except Exception:
        result["message"] = MSG_CANNOT_OPEN
        result["reason"] = "invalid_image"
        return result

    result["image_bytes"] = image_bytes
    result["image_hash"] = _hash_bytes(image_bytes)

    if model not in VALID_MODELS or multiple_faces not in VALID_MULTIPLE_FACES_MODES:
        result["message"] = "Invalid processing parameters."
        result["reason"] = "invalid_params"
        return result

    try:
        rgb_array = normalize_image_to_rgb_array(pil_image)
    except Exception:
        result["message"] = MSG_CANNOT_OPEN
        result["reason"] = "invalid_image"
        return result

    try:
        detection_array, scale = _resize_for_detection(rgb_array)
        raw_locations = face_recognition.face_locations(detection_array, model=model)
        face_locations = [_scale_location(loc, scale) for loc in raw_locations]
    except Exception as e:
        result["message"] = f"Face detection failed: {e}"
        result["reason"] = "detection_failed"
        return result

    result["num_faces"] = len(face_locations)

    if len(face_locations) == 0:
        result["message"] = MSG_NO_FACE
        result["reason"] = "no_face"
        return result

    result["face_detected"] = True

    chosen_location = _select_face(face_locations, multiple_faces)

    if chosen_location is None:
        result["message"] = MSG_MULTIPLE_FACES
        result["reason"] = "multiple_faces"
        return result

    result["face_location"] = chosen_location

    try:
        encodings = face_recognition.face_encodings(rgb_array, known_face_locations=[chosen_location])
        if len(encodings) == 0:
            result["message"] = "Face detected but encoding could not be generated."
            result["reason"] = "encoding_failed"
            return result
        result["encoding"] = encodings[0]
    except Exception as e:
        result["message"] = f"Encoding failed: {e}"
        result["reason"] = "encoding_failed"
        return result

    result["success"] = True
    result["message"] = MSG_SUCCESS
    result["reason"] = "success"
    return result


def draw_debug_preview(image_path, output_path="debug_preview.jpg", model="hog"):
    if os.path.abspath(image_path) == os.path.abspath(output_path):
        raise ValueError("output_path must be different from image_path.")

    pil_image, _ = _validate_and_load_image(image_path)
    rgb_array = normalize_image_to_rgb_array(pil_image)

    detection_array, scale = _resize_for_detection(rgb_array)
    raw_locations = face_recognition.face_locations(detection_array, model=model)
    face_locations = [_scale_location(loc, scale) for loc in raw_locations]

    bgr_array = cv2.cvtColor(rgb_array, cv2.COLOR_RGB2BGR)

    for (top, right, bottom, left) in face_locations:
        cv2.rectangle(bgr_array, (left, top), (right, bottom), (0, 255, 0), 2)

    cv2.imwrite(output_path, bgr_array)
    return output_path