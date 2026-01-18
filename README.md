# 📊 Marketing Insights Analyzer

A Python-based tool to compare **Generative AI (Azure OpenAI)** against a **Rule-Based Baseline** for analyzing customer feedback.

## ✨ Features
*   **Dual Analysis**: Runs AI (GPT) and deterministic rules side-by-side.
*   **Streamlit UI**: interactive dashboard to upload files and view results.
*   **Cost Tracking**: Monitors token usage and estimated USD cost per request.
*   **Structured Output**: Exports insights to JSON.

## 🚀 Setup

1.  **Install Dependencies**
    ```bash
    pip install streamlit openai python-dotenv
    ```

2.  **Configure Environment**
    Create a `.env` file in the project root:
    ```ini
    AZURE_OPENAI_API_KEY="your_key_here"
    AZURE_OPENAI_ENDPOINT="https://your-resource.openai.azure.com/"
    AZURE_OPENAI_DEPLOYMENT_NAME="gpt-4o"
    AZURE_OPENAI_API_VERSION="2024-02-15-preview"
    ```

3.  **Run the App**
    ```bash
    streamlit run app.py
    ```

## 📂 Input Formats
Supports `.csv`, `.json`, or `.txt`.
*   **CSV**: Must have a column named `feedback`, `text`, `review`, or `body`.
