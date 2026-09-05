import streamlit as st
from google import genai
import os

st.set_page_config(page_title="AI Study Hub", page_icon="🎓", layout="centered")

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

user_text = st.text_area("Paste your topic, syllabus, or lecture notes here:", height=150)

if st.button("Generate Study Material"):
    if not client:
        st.error("API Key is not configured!")
    elif not user_text.strip():
        st.warning("Please enter some text or topic first.")
    else:
        # Custom prompt engineering based on mode
        if mode == "⚡ Quick Summary & Key Takeaways":
            prompt = f"Provide a concise summary, bullet points, and key takeaways for this content:\n\n{user_text}"
        elif mode == "📝 Exam Cheat Sheet (Definitions, Formulas & Key Points)":
            prompt = (
                "Format this into a high-yield Exam Cheat Sheet with: "
                "1. Core Definitions (1-2 lines each), 2. Essential Formulas/Rules, "
                "3. Crucial High-Yield Points to remember for exams:\n\n"
                f"{user_text}"
            )
        elif mode == "💡 Explain Like I'm 10 (Simple Real-life Analogies)":
            prompt = (
                "Explain the following concept in extremely simple terms using vivid real-life analogies, "
                "easy language, and zero complex jargon:\n\n"
                f"{user_text}"
            )
        else:
            prompt = (
                "Generate 4 to 5 high-yield revision flashcards from the text below. "
                "Format strictly as pairs like:\n"
                "Q: [Question here]\n"
                "A: [Clear concise answer here]\n\n"
                f"{user_text}"
            )

        with st.spinner("Generating your study material..."):
            try:
                response = client.models.generate_content(
                    model="gemini-3.6-flash",
                    contents=prompt
                )
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

            except Exception as e:
                st.error(f"Error details: {e}")
                
