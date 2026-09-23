import hashlib
import json
import os

from backend.search_module import search_module
from blockchain_module import register_hash, verify_hash


def create_image_fingerprint(image_path):
    sha256 = hashlib.sha256()

    with open(image_path, "rb") as image_file:
        while True:
            chunk = image_file.read(8192)

            if not chunk:
                break

            sha256.update(chunk)

    return sha256.hexdigest()


if __name__ == "__main__":

    # Actual local image
    image_path = os.path.join(
        "backend",
        "test_image.jpg"
    )

    print("\n🔍 Searching uploaded image...")

    # Reverse image search
    result = search_module(image_path)

    if result is None:
        print("\n❌ No matching image found.")
    else:
        print("\n✅ Reverse Image Search Result:")
        print(json.dumps(result, indent=2))

    # Create fingerprint from ACTUAL image
    fingerprint = create_image_fingerprint(image_path)

    print("\n🔐 SHA-256 Image Fingerprint:")
    print(fingerprint)

    # Check whether image is already registered
    print("\n🔎 Checking blockchain...")

    existing = verify_hash(fingerprint)

    if existing["verified"]:
        print("\n⚠️ Image already registered on blockchain.")
        print(json.dumps(existing, indent=2))

    else:
        # Register image fingerprint
        print("\n⛓️ Registering image fingerprint on Sepolia...")

        tx_hash = register_hash(fingerprint)

        print("\n✅ Blockchain Registration Successful!")
        print("TX Hash:", tx_hash)

        # Verify again
        print("\n🔎 Verifying fingerprint...")

        verification = verify_hash(fingerprint)

        print("\n✅ Final Verification Result:")
        print(json.dumps(verification, indent=2))