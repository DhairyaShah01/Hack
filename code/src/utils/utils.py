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
        f"NO explanation, NO markdown formatting, NO additional commentary—ONLY return raw JSON."
    )

    print("Souchu: ", row)

    # Call ask_genai to process the row
    response = ask_genai(prompt, "Row to EntityInput Conversion")

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

def getCombinedSearchResults(entities):
    combined_search_results = []
    for entity_name in entities:
        print(f"Performing web search for entity: {entity_name}")
        search_results = web_search(entity_name)  # Perform web search

        if not search_results:
            search_results = [{"snippet": "No data available"}]

        combined_search_results.extend(search_results)
    return combined_search_results
