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
api_key = os.getenv("GEMINI_API_KEY")

if not api_key:
    raise ValueError("GEMINI_API_KEY is not set in .env")

client = genai.Client(api_key=api_key)


@app.route("/")
def home():
    return "MediScan AI Backend is Running!"


@app.route("/analyze", methods=["POST"])
def analyze():

    try:

        # -------------------------
        # GET FORM DATA
        # -------------------------

        consultation_type = request.form.get(
            "type",
            "human"
        )

        symptoms = request.form.get(
            "symptoms",
            ""
        )

        image = request.files.get("image")

        # -------------------------
        # CHECK IMAGE
        # -------------------------

        if not image:
            return jsonify({
                "success": False,
                "error": "Please upload an image."
            }), 400

        image_bytes = image.read()

        if not image_bytes:
            return jsonify({
                "success": False,
                "error": "Uploaded image is empty."
            }), 400

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

Give the response in this exact format:

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

Give the response in this exact format:

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

        # -------------------------
        # SEND TO GEMINI
        # -------------------------

        try:

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

        except Exception as gemini_error:

            print("\n==============================")
            print("GEMINI ERROR")
            print("==============================")
            print(gemini_error)
            print("==============================\n")

            return jsonify({
                "success": False,
                "error": "Gemini is temporarily unavailable. Please try again."
            }), 503

        # -------------------------
        # EXTRACT GEMINI TEXT
        # -------------------------

        result_text = ""

        try:

            # First try the normal response.text
            if hasattr(response, "text") and response.text:
                result_text = response.text.strip()

        except Exception as text_error:
            print("Response text extraction warning:", text_error)

        # If response.text was empty, inspect candidates
        if not result_text:

            try:

                if response.candidates:

                    for candidate in response.candidates:

                        if not candidate.content:
                            continue

                        if not candidate.content.parts:
                            continue

                        for part in candidate.content.parts:

                            if hasattr(part, "text") and part.text:
                                result_text += part.text

            except Exception as extraction_error:

                print(
                    "Detailed response extraction error:",
                    extraction_error
                )

        # -------------------------
        # CHECK RESULT
        # -------------------------

        if not result_text.strip():

            print("Gemini returned no readable text.")

            return jsonify({
                "success": False,
                "error": "Gemini returned no readable analysis."
            }), 502

        # -------------------------
        # RETURN RESULT
        # -------------------------

        return jsonify({
            "success": True,
            "result": result_text
        })

    # -------------------------
    # GENERAL ERROR
    # -------------------------

    except Exception as e:

        print("\n==============================")
        print("SERVER ERROR")
        print("==============================")
        print(e)
        print("==============================\n")

        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


# -------------------------
# START SERVER
# -------------------------

if __name__ == "__main__":

    app.run(
        host="0.0.0.0",
        port=5001,
        debug=True
    )