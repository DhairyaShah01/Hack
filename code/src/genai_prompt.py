import openai

def ask_genai(prompt, prompt_type):
    print(f"Asking GenAI: '{prompt}'")
    print(f"Processing {prompt_type}... Retrieving and evaluating multiple data sources. This may take a few minutes. Thank you for your patience. Comprehensive insights are on the way.")
    client = openai.OpenAI(
        api_key="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",
        base_url="https://openrouter.ai/api/v1",
        )

    completion = client.chat.completions.create(
    extra_body={},
    # model="deepseek/deepseek-r1-zero:free",
    # model="meta-llama/llama-3.1-8b-instruct:free",
    model="nvidia/llama-3.1-nemotron-70b-instruct:free",
    messages=[
        {
        "role": "user",
        "content": prompt
        }
    ]
    )
    return completion.choices[0].message.content;