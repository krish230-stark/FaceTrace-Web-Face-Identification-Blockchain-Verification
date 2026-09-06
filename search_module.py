import os
import requests
from dotenv import load_dotenv

load_dotenv()

SERPAPI_KEY = os.getenv("SERPAPI_KEY")


def search_module(image_path):
    # Step 1: Local image upload to SerpApi
    upload_url = "https://serpapi.com/image"

    with open(image_path, "rb") as image_file:
        response = requests.post(
            upload_url,
            files={
                "image": (
                    os.path.basename(image_path),
                    image_file,
                    "image/jpeg"
                )
            },
            data={
                "api_key": SERPAPI_KEY
            },
            timeout=60
        )

    upload_result = response.json()

    if "error" in upload_result:
        print("SerpApi Upload Error:", upload_result["error"])
        return None

    image_id = upload_result.get("image_id")

    if not image_id:
        print("Image upload failed.")
        return None

    print("Image uploaded to SerpApi successfully.")

    # Step 2: Search uploaded image using Google Lens
    search_url = "https://serpapi.com/search"

    params = {
        "engine": "google_lens",
        "image_id": image_id,
        "type": "all",
        "api_key": SERPAPI_KEY
    }

    search_response = requests.get(
        search_url,
        params=params,
        timeout=60
    )

    results = search_response.json()

    # Temporary debugging
    # print("RAW GOOGLE LENS RESPONSE:")
    # print(results)

    if "error" in results:
        print("Google Lens Error:", results["error"])
        return None

    # Prefer exact matches
    matches = results.get("exact_matches", [])

    # If no exact matches, use visual matches
    if not matches:
        matches = results.get("visual_matches", [])

    if matches:
        first_match = matches[0]

        return {
            "title": first_match.get("title", "N/A"),
            "url": first_match.get("link", "N/A"),
            "source": first_match.get("source", "N/A"),
            "snippet": first_match.get("snippet", "N/A")
        }

    return None