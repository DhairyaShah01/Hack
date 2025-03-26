import openai
import json
import re


def ask_genai(prompt, prompt_type):
    print(f"Asking GenAI: '{prompt}'")
    print(
        f"Processing {prompt_type}... Retrieving and evaluating multiple data sources. This may take a few minutes. Thank you for your patience. Comprehensive insights are on the way."
    )
    client = openai.OpenAI(
        api_key="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",
        base_url="https://openrouter.ai/api/v1",
    )

    completion = client.chat.completions.create(
        extra_body={},
        # model="deepseek/deepseek-r1-zero:free",
        # model="meta-llama/llama-3.1-8b-instruct:free",
        model="nvidia/llama-3.1-nemotron-70b-instruct:free",
        messages=[{"role": "user", "content": prompt}],
    )
    raw_response = completion.choices[0].message.content.strip()

    # 🔍 Debug: Print the raw response
    print(f"🔍 Raw AI Response:\n{raw_response}")

    # 🛠 Remove markdown-style triple backticks (` ``` `)
    clean_response = re.sub(r"^```(?:json)?\n|\n```$", "", raw_response)

    # 🛠 Extract only the JSON part
    json_match = re.search(r"\{.*\}", clean_response, re.DOTALL)
    if json_match:
        clean_response = json_match.group(0)

    try:
        parsed_json = json.loads(clean_response)  # Convert to dictionary
        return parsed_json
    except json.JSONDecodeError:
        print(
            f"❌ Error: AI response is not valid JSON.\n🔍 Cleaned Response:\n{clean_response}"
        )
        raise ValueError("The response is not valid JSON.")
