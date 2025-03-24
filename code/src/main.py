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

# Function to perform a web search using Bing Search API
def web_search(entity_name):
    endpoint = "https://api.duckduckgo.com/"
    params = {
        "q": entity_name,
        "format": "json",
        "no_html": 1,
        "skip_disambig": 1
    }
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
    # print("Starting the analysis...")
    # content = await file.read()
    # transactionDetails = content.decode("utf-8")

    # # Prompt for extracting entities
    # prompt = f"Identify people and company in '{transactionDetails}'. Return a JSON with objects identifiedRisks, entityBasicRiskRating, entityName and entityType. entityType can be People or Company. IdentifiedRisks field should have risks identified with people or company based on transaction input given. entityBasicRisk rating will be very low, low, medium, high, very high based on notes and other details in transaction. Keep the original transaction detail fields associated with each entity for verification."
    # # Step 1: Extract entities using GenAI
    # entities = ask_genai(prompt, "Entity Extraction")
    # print("Entities identified:")
    # print(entities)
    entities = input_data.entities  # Get the list of entities from the user input

    results = []
    # Fetch data from OpenCorporates or other sources
    for entity_name in entities:
        print(f"Performing web search for entity: {entity_name}")
        search_results = web_search(entity_name)  # Perform web search

        if not search_results:
            search_results = [{"snippet": "No data available"}]

        # Perform sentiment analysis on the search results
        combined_text = " ".join([result["snippet"] for result in search_results])  # Combine snippets
        sentiment = analyze_sentiment(combined_text) if combined_text else "No data available"

        entity_result = {
            "entityName": entity_name,
            "searchResults": search_results,
            "sentiment": sentiment
        }

        results.append(entity_result)

    # Get current script directory
    BASE_DIR = os.path.dirname(__file__)

    # Use relative path based on script's location
    assessement_file_path = os.path.join(BASE_DIR, "assessment_rules.txt")
    with open(assessement_file_path, "r", encoding="utf-8") as file:
        assessmentRules = file.read()
    # Prompt for coming up with risk assessment
    assessmentPrompt = f"Use the following assessment rules and results dictionary and come up with riskRating, riskRationale, complianceRating and complianceRationle  for each entity in '{entities}', AssessmentRules:'{assessmentRules}'. Look for internet for more recent data and news. Example check in Google for any negative news or results. Check in OpenCorporate, Wikipedia, Sanctions lists around the world. Keep the original transaction detail fields associated with each entity for verification. In Rationale mention which source of data was the reason like Transaction detail, Google, Wikipedia, Sanctions List, OpenCorporate etc.  Provide output in JSON format. Dont add any other text in output apart from this report."
    # Step 2: Risk Assessement using GenAI
    riskAndComplianceReport = ask_genai(assessmentPrompt, "Risk Assessment")
    print("Final Risk and Compliance Report:")
    print(riskAndComplianceReport)
    print("Analysis is complete. Returning the result.")
    # Clean the string by removing "```json" and "```"
    if riskAndComplianceReport.startswith("```json"):
        riskAndComplianceReport = riskAndComplianceReport.lstrip("```json")
    if riskAndComplianceReport.endswith("```"):
        riskAndComplianceReport = riskAndComplianceReport.rstrip("```")
    cleaned_str = riskAndComplianceReport.strip()


    try:
        parsed_json = json.loads(cleaned_str)
    except json.JSONDecodeError as e:
        print(f"JSON parsing error: {e}")
        raise ValueError("The response is not valid JSON.")
    
    return parsed_json

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)