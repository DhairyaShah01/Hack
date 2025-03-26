# 🚀 Hackathon Project

## 📌 Table of Contents
- [Introduction](#introduction)
- [Demo](#demo)
- [Inspiration](#inspiration)
- [What It Does](#what-it-does)
- [How We Built It](#how-we-built-it)
- [Challenges We Faced](#challenges-we-faced)
- [How to Run](#how-to-run)
- [Tech Stack](#tech-stack)
- [Team](#team)

---

## 🎯 Introduction
The Transaction Risk Assessment API is a FastAPI-based solution designed to assess transaction risks using AI-powered entity extraction, sentiment analysis, and compliance checks. It processes both structured and unstructured transaction data to generate risk assessments and compliance reports.

## 🎥 Demo
🔗 [Live Demo](#)  
📹 [Video Demo](#)  
🖼️ Project Overview:

![Project Overview](artifacts/images/projectOverview.png)

## 💡 Inspiration
The need for robust financial compliance and risk assessment tools inspired this project. It aims to simplify and automate the process of identifying high-risk transactions, ensuring regulatory compliance, and mitigating fraud.

## ⚙️ What It Does
- Parses CSV files and unstructured text for transaction data.
- Extracts structured transaction details using AI.
- Performs web searches for additional context about entities.
- Analyzes sentiment for entities involved in transactions.
- Evaluates transaction risks based on predefined rules.
- Generates detailed risk and compliance reports.

## 🛠️ How We Built It
- **Backend**: FastAPI for building the API endpoints.
- **AI Integration**: OpenAI API and Hugging Face Transformers for entity extraction and sentiment analysis.
- **Web Search**: DuckDuckGo API for fetching additional entity information.
- **Risk Assessment**: Custom rules defined in `assessment_rules.txt` for evaluating transaction risks.

## 🚧 Challenges We Faced
- Ensuring the accuracy of AI-generated structured data from unstructured text.
- Handling edge cases in transaction data, such as missing fields or invalid formats.
- Integrating multiple APIs (OpenAI, DuckDuckGo) seamlessly.
- Designing a robust risk assessment framework.


## 🏃 How to Run
1. Clone the repository  
   ```sh
   git clone https://github.com/your-repo.git
   ```
2. Install dependencies  
   ```sh
   pip install -r code/src/requirements.txt
   ```
3. Run the project  
   ```sh
   uvicorn code.src.main:app --reload
   ```

## 🏗️ Tech Stack
- 🔹 Backend: FastAPI
- 🔹 AI Integration:  OpenAI API, Hugging Face Transformers
- 🔹 Web Search: DuckDuckGo API
- 🔹 Language: Python
- 🔹 Middleware: CORS

## 👥 Team
- **[Your Name]** - [GitHub](#) | [LinkedIn](#)
- **[Teammate 2]** - [GitHub](#) | [LinkedIn](#)