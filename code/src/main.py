from fastapi import FastAPI, File, UploadFile
from genai_prompt import ask_genai
from pydantic import BaseModel
import os
import json
import requests  # For making HTTP requests
from fastapi.middleware.cors import CORSMiddleware
from transformers import pipeline
from typing import List  # Add this import

app = FastAPI()


class EntityInput(BaseModel):
    entities: List[str]  # List of entity names provided by the user
    amount: float  # Amount associated with the transaction
    currency: str  # Currency associated with the transaction


# Function to perform a web search using Bing Search API
def web_search(entity_name):
    endpoint = "https://api.duckduckgo.com/"
    params = {"q": entity_name, "format": "json", "no_html": 1, "skip_disambig": 1}
    response = requests.get(endpoint, params=params)
    print(f"Raw response for {entity_name}: {response.text}")  # Debug print

    try:
        if response.status_code == 200:
            return response.json().get("RelatedTopics", [])
        else:
            print(f"Search failed for {entity_name}: {response.status_code}")
            return []
    except json.JSONDecodeError as e:
        print(f"Error decoding JSON for {entity_name}: {e}")
        return []


def analyze_sentiment(text):
    sentiment_pipeline = pipeline("sentiment-analysis")
    result = sentiment_pipeline(text)
    return result  # Returns a list of dictionaries with 'label' (e.g., 'POSITIVE') and 'score'


@app.post("/entity/assessment")
async def upload_file(input_data: EntityInput):
    entities = input_data.entities  # Get the list of entities from the user input
    amount = input_data.amount  # Get the transaction amount
    currency = input_data.currency  # Get the transaction currency

    if len(entities) < 2:
        return {"error": "At least two entities are required for the transaction."}

    # Define the transaction details
    transaction_details = {
        "from": entities[0],
        "to": entities[1],
        "amount": amount,
        "currency": currency,
    }

    print(f"Transaction details: {transaction_details}")

    # Perform web search for all entities and aggregate results
    combined_search_results = []
    for entity_name in entities:
        print(f"Performing web search for entity: {entity_name}")
        search_results = web_search(entity_name)  # Perform web search

        if not search_results:
            search_results = [{"snippet": "No data available"}]

        combined_search_results.extend(search_results)

    # Combine all snippets for sentiment analysis
    combined_text = " ".join(
        [
            result.get("snippet", "")
            for result in combined_search_results
            if isinstance(result, dict)
        ]
    )

    # Perform sentiment analysis on the combined text
    sentiment = (
        analyze_sentiment(combined_text) if combined_text else "No data available"
    )

    # Prepare the results for all entities
    results = [
        {
            "entityName": entity_name,
            "searchResults": combined_search_results,
            "sentiment": sentiment,
        }
        for entity_name in entities
    ]

    # Get current script directory
    BASE_DIR = os.path.dirname(__file__)

    # Use relative path based on script's location
    assessement_file_path = os.path.join(BASE_DIR, "assessment_rules.txt")
    with open(assessement_file_path, "r", encoding="utf-8") as file:
        assessmentRules = file.read()

    # Prompt for coming up with risk assessment
    assessmentPrompt = (
    f"Use the following assessment rules and results dictionary to evaluate the transaction. "
    f"Run the evaluation 20 times independently and calculate the average confidence score across all runs. "
    f"Provide a final riskRating, riskRationale, and the average confidence score for the transaction. "
    f"Transaction details: {transaction_details}, AssessmentRules: '{assessmentRules}'. "
    f"Check in OpenCorporate, Wikipedia, Sanctions lists around the world. "
    f"Keep the original transaction detail fields associated, for verification and make sure the format is adhering to JSON format"
    f"In the rationale, mention which source of data was the reason for the evaluation. "
    f"Extract the following fields from the assessment rules: Sanction Score, Adverse Media, PEP Score, "
    f"High Risk Jurisdiction Score, Suspicious Transaction Pattern Score, Shell Company Link Score. "
    f"Provide the output in JSON format with the following structure: "
    f'{{"Transaction details" , "riskRating": <value>, "riskRationale": <string>, '
    f'"averageConfidenceScore": <value>, "Sanction Score": <value>, "Adverse Media": <value>, '
    f'"PEP Score": <value>, "High Risk Jurisdiction Score": <value>, '
    f'"Suspicious Transaction Pattern Score": <value>, "Shell Company Link Score": <value>}}. '
    f"Ensure the rationale is in a proper string format adhering to JSON value format without linebreaks. "
    f"Do not include any additional text in the output apart from this report."
)

    # Step 2: Risk Assessment using GenAI
    riskAndComplianceReport = ask_genai(assessmentPrompt, "Risk Assessment")
    print("Final Risk and Compliance Report:")
    print(riskAndComplianceReport)

    # ✅ If it's a string, convert it to a dictionary
    if isinstance(riskAndComplianceReport, str):
        try:
            parsed_json = json.loads(riskAndComplianceReport)  # Convert string to dict
        except json.JSONDecodeError:
            print("Error: AI response is not valid JSON")
            return {"error": "Invalid AI response"}
    else:
        parsed_json = riskAndComplianceReport  # Already a dict, no need to parse

    # ✅ Return valid JSON response
    return parsed_json


app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
