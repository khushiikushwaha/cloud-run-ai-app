import streamlit as st
from google import genai
import os
from pypdf import PdfReader
import time

st.set_page_config(page_title="Smart AI Study Hub", page_icon="🎓", layout="centered")

st.title("🎓 Smart AI Study Hub")
st.caption("Custom study tools designed for fast exam preparation & active recall.")

api_key = st.secrets.get("GEMINI_API_KEY") or os.environ.get("GEMINI_API_KEY")
client = genai.Client(api_key=api_key) if api_key else None

# Mode Selection
mode = st.selectbox(
    "Choose Study Output:",
    [
        "⚡ Quick Summary & Key Takeaways",
        "📝 Exam Cheat Sheet (Definitions, Formulas & Key Points)",
        "💡 Explain Like I'm 10 (Simple Real-life Analogies)",
        "🗂️ Interactive Flashcards (Click to Reveal Answers)"
    ]
)

# Input method tabs
tab_text, tab_file = st.tabs(["✍️ Paste Text", "📄 Upload PDF Notes"])

with tab_text:
    pasted_text = st.text_area("Paste your topic, syllabus, or lecture notes:", height=150)

with tab_file:
    uploaded_file = st.file_uploader("Upload your lecture slide or notes (PDF):", type=["pdf"])

# Extract content
final_text = ""
if uploaded_file is not None:
    try:
        reader = PdfReader(uploaded_file)
        pdf_content = ""
        for page in reader.pages:
            text = page.extract_text()
            if text:
                pdf_content += text + "\n"
        final_text = pdf_content
        st.success(f"PDF loaded successfully! ({len(reader.pages)} pages)")
    except Exception as err:
        st.error(f"Error reading PDF: {err}")
else:
    final_text = pasted_text

if st.button("Generate Study Material"):
    if not client:
        st.error("API Key is not configured in Secrets!")
    elif not final_text.strip():
        st.warning("Please paste some text or upload a PDF first.")
    else:
        # Prompt tuning
        if mode == "⚡ Quick Summary & Key Takeaways":
            prompt = f"Provide a concise summary, bullet points, and key takeaways for this content:\n\n{final_text}"
        elif mode == "📝 Exam Cheat Sheet (Definitions, Formulas & Key Points)":
            prompt = (
                "Format this into a high-yield Exam Cheat Sheet with: "
                "1. Core Definitions (1-2 lines each), 2. Essential Formulas/Rules, "
                "3. Crucial High-Yield Points to remember for exams:\n\n"
                f"{final_text}"
            )
        elif mode == "💡 Explain Like I'm 10 (Simple Real-life Analogies)":
            prompt = (
                "Explain the following concept in extremely simple terms using vivid real-life analogies, "
                "easy language, and zero complex jargon:\n\n"
                f"{final_text}"
            )
        else:
            prompt = (
                "Generate 4 to 5 high-yield revision flashcards from the text below. "
                "Format strictly as pairs like:\n"
                "Q: [Question here]\n"
                "A: [Clear concise answer here]\n\n"
                f"{final_text}"
            )

        with st.spinner("Generating your study material..."):
            response = None
            # Retry loop for 503 high-demand spikes
            for attempt in range(2):
                try:
                    response = client.models.generate_content(
                        model="gemini-3.6-flash",
                        contents=prompt
                    )
                    break
                except Exception as e:
                    if "503" in str(e) and attempt == 0:
                        time.sleep(2)
                        continue
                    else:
                        st.error(f"Error details: {e}")
                        break

            if response and hasattr(response, "text"):
                output_text = response.text

                # Display Logic
                if mode == "🗂️ Interactive Flashcards (Click to Reveal Answers)":
                    st.subheader("🗂️ Flashcards (Tap to reveal):")
                    cards = output_text.split("Q:")
                    found_cards = False
                    for card in cards:
                        if "A:" in card:
                            parts = card.split("A:")
                            question = parts[0].strip()
                            answer = parts[1].strip()
                            with st.expander(f"❓ {question}"):
                                st.write(answer)
                            found_cards = True
                    if not found_cards:
                        st.write(output_text)
                else:
                    st.subheader("Output:")
                    st.markdown(output_text)

                # Download Button
                st.download_button(
                    label="📥 Download Notes as TXT",
                    data=output_text,
                    file_name="study_notes.txt",
                    mime="text/plain"
                )
                
