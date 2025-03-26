import csv
from http.client import HTTPException
import io
from fastapi import FastAPI, File, UploadFile
from ai_prompt_handler import process_ai_query
from pydantic import BaseModel
import os
import json
import requests  # For making HTTP requests
from fastapi.middleware.cors import CORSMiddleware
from transformers import pipeline
from typing import Dict, List, Optional  # Add this import
from TransactionDTO import TransactionDTO

app = FastAPI()


class EntityInput(BaseModel):
    transaction_id: str  # Transaction ID provided by the user
    sender: str  # Sender name provided by the user
    receiver: str  # Receiver name provided by the user
    amount: float  # Amount associated with the transaction
    currency: str  # Currency associated with the transaction
    transaction_details: str  # Additional notes provided by the user

def is_csv_file(file: UploadFile) -> bool:
    """
    Checks whether the given file is in CSV format.
    :param file: The uploaded file to check.
    :return: True if the file is in CSV format, False otherwise.
    """
    # Check file extension
    if not file.filename.endswith(".csv"):
        return False

    try:
        # Read a small portion of the file to validate its content
        content = file.file.read(1024).decode("utf-8")
        file.file.seek(0)  # Reset file pointer after reading
        csv.Sniffer().sniff(content)  # Validate CSV structure
        return True
    except (csv.Error, UnicodeDecodeError):
        return False

#Parses CSV file content into a structured list.
def parse_csv(file_content: bytes) -> List[Dict[str, str]]:
    decoded_content = file_content.decode("utf-8")
    reader = csv.DictReader(io.StringIO(decoded_content))
    return [row for row in reader]

def convert_row_to_entity_input(row: Dict[str, str]) -> EntityInput:
    """
    Converts a selected row into the EntityInput format using the ask_genai function.
    """
    # Generate a prompt for ask_genai
    prompt = (
        f"Convert the following row into the EntityInput format:\n"
        f"Row: {row}\n"
        f"EntityInput format: {{'transaction_id': <string>, 'sender': <string>, 'receiver': <string>, "
        f"'amount': <float>, 'currency': <string>, 'transaction_details': <string>}}. "
        f"Ensure the output is in JSON format and adheres to the EntityInput structure."
        f"Ensure there are no invalid escape characters in the JSON output"
        f"NO explanation, NO markdown formatting, NO additional commentary—ONLY return raw JSON."
        f"If currency is not found, default to USD"
    )

    print("Souchu: ", row)

    # Call ask_genai to process the row
    response = process_ai_query(prompt, "Row to EntityInput Conversion")

    try:
        # Parse the response into a dictionary
        if isinstance(response, str):
            parsed_response = json.loads(response)
        elif isinstance(response, dict):
            parsed_response = response
        else:
            raise ValueError("Unexpected response type")

        # Convert the parsed response into an EntityInput object
        entity_input = EntityInput(**parsed_response)
        return entity_input

    except (json.JSONDecodeError, ValueError, TypeError) as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to convert row to EntityInput: {str(e)}",
        )

def extract_multi_input_unstructured(text: str) -> List[Dict[str,str]]:
    transactions = text.split(b"---")
    print(transactions)
    data = []
    for t in transactions:
        var = extract_from_unstructured(t)
        print(var, type(var))
        data.append(var)
    print("Multi input data: ", data)
    return data

# Extracts structured transaction details from unstructured text using GenAI.
def extract_from_unstructured(text: str) -> List[Dict[str, str]]:
    prompt = (
        f"Extract transaction details from the given text and return structured CSV format:"
        f"Transaction ID, Sender, Receiver, Amount, Currency, Transaction Details."
        f"Include details such as additional notes, remarks, or any other relevant information in transaction details without any special characters in string format adhering to JSON format."
        f"Ensure data integrity and return JSON format."
        f"Do not include any additional text in the output apart from the generated json."
        f"NO explanation, NO markdown formatting, NO additional commentary—ONLY return raw JSON."
        f"Ensure there are no invalid escape characters in the JSON output"
    )
    response = process_ai_query(f"Text: {text}\n{prompt}", "Entity Extraction")
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
async def upload_file(
    file: Optional[UploadFile] = None,  # Make file optional
    #text: Optional[str] = None  # Make text optional
):
    if not file:
        raise HTTPException(status_code=400, detail="No file or text provided")

    structured_data = []
    
    if is_csv_file(file):
        structured_data = parse_csv(await file.read())
        structured_data = [convert_row_to_entity_input(row) for row in structured_data]
    else:
        text = await file.read()
        structured_data = extract_multi_input_unstructured(text)
        print(f"Extracted structured data before: {structured_data}")
        structured_data_new = []
        for data in structured_data:
            var = convert_row_to_entity_input(data) ##ToDo: removed braces
            structured_data_new.append(var)
        print(f"Extracted structured data after: {structured_data_new}") 
        structured_data = structured_data_new 

    if not structured_data:
        raise HTTPException(status_code=500, detail="No structured data found")

    results = []

    # Extract structured transaction details from unstructured text
    for transaction in structured_data:
        print(f"Extracted transaction details: {transaction}")
        results.append(process_input(transaction))  # Process each transaction   

    transactionDtos = []
    for r in results:
        print("Type of r: ", type(r))
        print(r)
        transactionDetails = r.get("Transaction details")
        transactionId = transactionDetails.get("transaction_id")
        riskRating = r.get("riskRating")
        entityList = [transactionDetails.get("from") , transactionDetails.get("to")]
        entityType = r.get("EntityType")
        confidenceScore = r.get("averageConfidenceScore")
        reason = r.get("riskRationale")
        supportingEvidence = r.get("riskRationaleSources")
        transactionDtos.append(TransactionDTO(transactionId, entityList, entityType, riskRating, supportingEvidence, confidenceScore, reason))
    return transactionDtos

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
    f'{{"Transaction details" , "riskRating": <value>, "riskRationale": <string>, riskRationaleSources: <string>,'
    f'"averageConfidenceScore": <value>, "Sanction Score": <value>, "Adverse Media": <value>, '
    f'"PEP Score": <value>, "High Risk Jurisdiction Score": <value>, '
    f'"Suspicious Transaction Pattern Score": <value>, "Shell Company Link Score": <value>}}. '
    f"Keep the case of key names as given in the prompt. "
    f"Include an extra field EntityType which is an array containing the entity type from a bank's perspective of both the sender and receiver in one or two words without special characters in an array, with a default type Corporation if not found"
    f"Ensure the rationale is in a proper string format adhering to JSON value format without linebreaks. "
    f"Ensure the other scores have a short justification in a separate field in string format adhering to JSON schema"
    f"Do not include any additional text in the output apart from the generated json."
    f"NO explanation, NO markdown formatting, NO additional commentary—ONLY return raw JSON."
)

    # Step 2: Risk Assessment using GenAI
    riskAndComplianceReport = process_ai_query(assessmentPrompt, "Risk Assessment")
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
