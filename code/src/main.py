import csv
from http.client import HTTPException
import io
from fastapi import FastAPI, File, UploadFile
from genai_prompt import ask_genai
from models import EntityInput
import os
import json
import requests  # For making HTTP requests
from utils import getCombinedSearchResults
from fastapi.middleware.cors import CORSMiddleware
from transformers import pipeline
from typing import Dict, List, Optional  # Add this import

app = FastAPI()

# Extracts structured transaction details from unstructured text using GenAI.
def extract_from_unstructured(text: str) -> List[Dict[str, str]]:
    prompt = (
        f"Extract transaction details from the given text and return structured CSV format:"
        f"Transaction ID, Sender, Receiver, Amount, Currency, Transaction Details."
        f"Include details such as additional notes, remarks, or any other relevant information in transaction details."
        f"Ensure data integrity and return JSON format."
        f"Do not include any additional text in the output apart from the generated json."
        f"NO explanation, NO markdown formatting, NO additional commentary—ONLY return raw JSON."
    )
    response = ask_genai(f"Text: {text}\n{prompt}", "Entity Extraction")
    try:
        if isinstance(response, str):
            return json.loads(response)
        elif isinstance(response, dict):
            return response
        else:
            raise ValueError("Unexpected response type")
    except (json.JSONDecodeError, ValueError) as e:
        raise HTTPException(
            status_code=500,
            detail=f"Invalid AI response for unstructured data parsing: {str(e)}",
        )


@app.post("/entity/assessment")
async def upload_file(
    file: Optional[UploadFile] = None,  # Make file optional
    text: Optional[str] = None  # Make text optional
):
    if not file and not text:
        raise HTTPException(status_code=400, detail="No file or text provided")

    structured_data = []
    
    if file:
        structured_data = parse_csv(await file.read())
        structured_data = [convert_row_to_entity_input(row) for row in structured_data]
    elif text:
        structured_data = extract_from_unstructured(text)

    if not structured_data:
        raise HTTPException(status_code=500, detail="No structured data found")

    results = []

    # Extract structured transaction details from unstructured text
    for transaction in structured_data:
        print(f"Extracted transaction details: {transaction}")
        results.append(process_input(transaction))  # Process each transaction   

    return results

def process_input(input_data: any):
    entities = [input_data.sender, input_data.receiver]  # Get the list of entities from the user input
    amount = input_data.amount  # Get the transaction amount
    currency = input_data.currency  # Get the transaction currency
    remarks = input_data.transaction_details  # Get the remarks associated with the transaction
    transaction_id = input_data.transaction_id  # Get the transaction ID

    if len(entities) < 2:
        return {"error": "At least two entities are required for the transaction."}

    # Define the transaction details
    transaction_details = {
        "transaction_id": transaction_id,
        "from": entities[0],
        "to": entities[1],
        "amount": amount,
        "currency": currency,
        "remarks": remarks,
    }

    print(f"Transaction details: {transaction_details}")

    # Perform web search for all entities and aggregate results
    combined_search_results = getCombinedSearchResults(entities)

    # Combine all snippets for sentiment analysis
    combined_text = " ".join([result.get("snippet", "") for result in combined_search_results if isinstance(result, dict)])

    # Perform sentiment analysis on the combined text
    sentiment = (analyze_sentiment(combined_text) if combined_text else "No data available")

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
    f"Use the following assessment rules and results dictionary {results} to evaluate the transaction. "
    f"Run the evaluation 5 times independently and calculate the average confidence score and risk scores across all runs. "
    f"Provide a final riskRating, riskRationale, and the average confidence score for the transaction weighing in the entities, amount, currency and remarks in the transaction. "
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
    f"Do not include any additional text in the output apart from the generated json."
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
