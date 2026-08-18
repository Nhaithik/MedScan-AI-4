from flask import Flask, request, jsonify
from flask_cors import CORS
from google import genai
from dotenv import load_dotenv
import os

# Load .env
load_dotenv()

# Create Flask app
app = Flask(__name__)
CORS(app)

# Gemini client
client = genai.Client(
    api_key=os.getenv("GEMINI_API_KEY")
)


@app.route("/")
def home():
    return "MediScan AI Backend is Running!"


@app.route("/analyze", methods=["POST"])
def analyze():

    try:

        # Get consultation type
        consultation_type = request.form.get(
            "type",
            "human"
        )

        # Get symptoms
        symptoms = request.form.get(
            "symptoms",
            ""
        )

        # Get uploaded image
        image = request.files.get("image")

        # Make sure image exists
        if not image:
            return jsonify({
                "success": False,
                "error": "Please upload an image."
            }), 400

        # Read image
        image_bytes = image.read()

        # -------------------------
        # HUMAN CONSULTATION
        # -------------------------

        if consultation_type == "human":

            prompt = f"""
You are MediScan AI, an AI healthcare
information assistant for a student project.

The user has provided an image and the following
symptoms:

{symptoms}

Analyze the image and the symptoms together.

Give the response in this format:

POSSIBLE CONDITION:
Give possible conditions, not a confirmed diagnosis.

IMAGE FINDINGS:
Describe visible features in the image.

POSSIBLE CAUSES:
List possible general causes.

FIRST AID:
Give general first-aid guidance where appropriate.

DOCTOR RECOMMENDATION:
Explain whether professional medical evaluation
may be appropriate.

URGENCY LEVEL:
Low / Moderate / High

IMPORTANT:
This is preliminary AI-generated information.
It is NOT a confirmed medical diagnosis.
Do not claim certainty.
Encourage the user to consult a qualified
healthcare professional when appropriate.
"""

        # -------------------------
        # ANIMAL CONSULTATION
        # -------------------------

        else:

            animal_type = request.form.get(
                "animal_type",
                "Unknown"
            )

            breed = request.form.get(
                "breed",
                "Unknown"
            )

            age = request.form.get(
                "age",
                "Unknown"
            )

            behaviour = request.form.get(
                "behaviour",
                ""
            )

            prompt = f"""
You are MediScan AI, an AI veterinary
information assistant for a student project.

Animal type:
{animal_type}

Breed:
{breed}

Age:
{age}

Symptoms:
{symptoms}

Behaviour changes:
{behaviour}

Analyze the uploaded image together with
the information above.

Give the response in this format:

POSSIBLE CONDITION:
Give possible conditions, not a confirmed diagnosis.

IMAGE FINDINGS:
Describe visible features in the image.

HOME CARE:
Give general supportive care information.

VETERINARY RECOMMENDATION:
Explain whether veterinary evaluation may be appropriate.

URGENCY LEVEL:
Low / Moderate / High

IMPORTANT:
This is preliminary AI-generated information.
It is NOT a confirmed veterinary diagnosis.
Do not claim certainty.
Encourage consultation with a qualified
veterinarian when appropriate.
"""

        # Send image + prompt to Gemini
        response = client.models.generate_content(
            model="gemini-3.6-flash",
            contents=[
                prompt,
                {
                    "inline_data": {
                        "mime_type": image.mimetype,
                        "data": image_bytes
                    }
                }
            ]
        )

        # Send result back to website
        return jsonify({
            "success": True,
            "result": response.text
        })

    except Exception as e:

        print("ERROR:", e)

        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


if __name__ == "__main__":

    app.run(
        host="0.0.0.0",
        port=5001,
        debug=True
    )