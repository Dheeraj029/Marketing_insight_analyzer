import streamlit as st
import os
import json
import time
import csv
import io
import uuid
from dotenv import load_dotenv
from openai import AzureOpenAI
from prompts import ANALYSIS_PROMPT

# Load environment variables
load_dotenv()

# Pricing estimates (USD per 1K tokens)
INPUT_PRICE = 0.005
OUTPUT_PRICE = 0.015


# -------------------------------
# Utility: Read Uploaded File
# -------------------------------
def read_feedback_file(file):
    ext = file.name.split('.')[-1].lower()
    content = file.getvalue().decode("utf-8")
    records = []

    if ext == "csv":
        reader = csv.DictReader(io.StringIO(content))
        for row in reader:
            records.append(row.get("feedback") or row.get("text"))

    elif ext == "txt":
        records = [line.strip() for line in content.splitlines() if line.strip()]

    elif ext == "json":
        raw = json.loads(content)
        records = raw if isinstance(raw, list) else []

    return records


# -------------------------------
# Baseline Analyzer
# -------------------------------
def baseline_analysis(text):
    start = time.time()
    text_l = text.lower()

    negative_terms = ["confusing", "crash", "slow", "error", "expensive"]
    positive_terms = ["good", "great", "excellent", "love"]

    score = sum(w in text_l for w in positive_terms) - sum(w in text_l for w in negative_terms)
    sentiment = "Positive" if score > 0 else "Negative" if score < 0 else "Neutral"

    themes = []
    if "price" in text_l:
        themes.append("Pricing")
    if "login" in text_l or "password" in text_l:
        themes.append("Authentication")
    if "crash" in text_l:
        themes.append("Stability")

    return {
        "sentiment": sentiment,
        "themes": themes,
        "summary": "Derived using rule-based logic",
        "recommendations": ["Manual review suggested"] if sentiment == "Negative" else [],
        "meta": {
            "method": "Baseline",
            "latency": round(time.time() - start, 4),
            "cost_usd": 0.0
        }
    }


# -------------------------------
# Azure OpenAI Analyzer
# -------------------------------
def ai_analysis(text, client, deployment):
    start = time.time()

    response = client.chat.completions.create(
        model=deployment,
        messages=[
            {"role": "system", "content": ANALYSIS_PROMPT},
            {"role": "user", "content": text}
        ],
        temperature=0,
        response_format={"type": "json_object"}
    )

    usage = response.usage
    prompt_tokens = usage.prompt_tokens
    completion_tokens = usage.completion_tokens

    cost = (prompt_tokens / 1000 * INPUT_PRICE) + (completion_tokens / 1000 * OUTPUT_PRICE)

    result = json.loads(response.choices[0].message.content)
    result["meta"] = {
        "method": "Azure OpenAI",
        "latency": round(time.time() - start, 4),
        "tokens": usage.total_tokens,
        "cost_usd": round(cost, 6)
    }

    return result


# -------------------------------
# Conclusion Generator
# -------------------------------
def generate_conclusion(results):
    baseline_score = 0
    ai_score = 0

    for item in results:
        base = item["baseline"]
        ai = item["azure_ai"]

        if len(ai.keys()) > len(base.keys()):
            ai_score += 1
        else:
            baseline_score += 1

        if ai.get("recommendations"):
            ai_score += 1
        if base.get("recommendations"):
            baseline_score += 1

        if len(ai.get("themes", [])) > len(base.get("themes", [])):
            ai_score += 1

    if ai_score > baseline_score:
        winner = "Azure OpenAI Analyzer"
        reason = (
            "Azure OpenAI provides deeper insights, contextual reasoning, "
            "and more structured analysis compared to the rule-based baseline."
        )
    elif baseline_score > ai_score:
        winner = "Baseline Analyzer"
        reason = (
            "The baseline analyzer performs well for simple sentiment detection "
            "with zero cost and minimal latency."
        )
    else:
        winner = "Both Perform Similarly"
        reason = "Both analyzers show comparable effectiveness on this dataset."

    return {
        "baseline_score": baseline_score,
        "azure_ai_score": ai_score,
        "winner": winner,
        "reason": reason
    }


# -------------------------------
# Streamlit UI
# -------------------------------
def main():
    st.set_page_config(page_title="Marketing Insights Analyzer", layout="wide", page_icon="📊")

    st.title("📊 Marketing Insights Analyzer")
    st.caption("Comparison of Rule-Based Analysis vs Azure OpenAI")

    with st.sidebar:
        st.header("⚙️ Configuration")
        uploaded_file = st.file_uploader("Upload Feedback File", ["csv", "txt", "json"])
        max_rows = st.slider("Max feedback items", 1, 20, 5)
        run_btn = st.button("🚀 Run Analysis", type="primary")

    if uploaded_file and run_btn:
        batch_id = uuid.uuid4().hex[:6].upper()
        st.success(f"Batch ID: {batch_id}")

        feedback_list = read_feedback_file(uploaded_file)[:max_rows]

        client = AzureOpenAI(
            api_key=os.getenv("AZURE_OPENAI_API_KEY"),
            api_version=os.getenv("AZURE_OPENAI_API_VERSION"),
            azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT")
        )
        deployment = os.getenv("AZURE_OPENAI_DEPLOYMENT_NAME")

        results = []
        progress = st.progress(0)

        for i, feedback in enumerate(feedback_list, start=1):
            progress.progress(i / len(feedback_list))

            baseline = baseline_analysis(feedback)
            ai_result = ai_analysis(feedback, client, deployment)

            results.append({
                "id": i,
                "feedback": feedback,
                "baseline": baseline,
                "azure_ai": ai_result
            })

            with st.expander(f"📝 Feedback {i}"):
                st.info(feedback)

                col1, col2 = st.columns(2)
                with col1:
                    st.subheader("🤖 Baseline Analysis")
                    st.json(baseline)
                with col2:
                    st.subheader("✨ Azure AI Analysis")
                    st.json(ai_result)

        st.success("✅ Analysis completed")

        # Download JSON
        json_output = json.dumps(results, indent=2)
        st.download_button(
            label="📥 Download Results as JSON",
            data=json_output,
            file_name=f"analysis_results_{batch_id}.json",
            mime="application/json"
        )

        # Conclusion
        st.divider()
        st.subheader("🏁 Final Conclusion")

        conclusion = generate_conclusion(results)

        c1, c2, c3 = st.columns(3)
        c1.metric("Baseline Score", conclusion["baseline_score"])
        c2.metric("Azure AI Score", conclusion["azure_ai_score"])
        c3.metric("Winner", conclusion["winner"])

        st.success(f"🏆 Best Performer: {conclusion['winner']}")
        st.write(conclusion["reason"])

    else:
        st.info("👈 Upload a file and click **Run Analysis** to begin")


if __name__ == "__main__":
    main()
