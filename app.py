import streamlit as st
from google import genai
import os
from pypdf import PdfReader
import time
from gtts import gTTS
import io
import re
from fpdf import FPDF

st.set_page_config(page_title="Smart AI Study Hub", page_icon="🎓", layout="centered")

st.title("🎓 Smart AI Study Hub")
st.caption("Custom study tools designed for fast exam preparation & active recall.")

api_key = st.secrets.get("GEMINI_API_KEY") or os.environ.get("GEMINI_API_KEY")
client = genai.Client(api_key=api_key) if api_key else None

def create_pdf(text_content):
    # PDF generation helper
    pdf = FPDF()
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.add_page()
    
    # Header styling
    pdf.set_font("Helvetica", "B", 18)
    pdf.set_text_color(30, 41, 59)
    pdf.cell(0, 10, "Smart AI Study Notes", new_x="LMARGIN", new_y="NEXT", align="C")
    pdf.ln(5)
    
    # Body font
    pdf.set_font("Helvetica", size=10)
    pdf.set_text_color(51, 65, 85)
    
    # Clean text from markdown syntax for clean PDF rendering
    clean_lines = text_content.split("\n")
    for line in clean_lines:
        line_clean = line.replace("**", "").replace("###", "").replace("##", "").replace("#", "").strip()
        # Clean basic latex wraps if any
        line_clean = re.sub(r'\\text\{([^}]+)\}', r'\1', line_clean)
        line_clean = line_clean.replace("$$", "").replace("$", "").replace(r"\rightarrow", "->")
        
        # Encode safely to latin-1 to avoid fpdf character encoding crashes
        safe_line = line_clean.encode('latin-1', 'replace').decode('latin-1')
        
        if line.startswith("#"):
            pdf.ln(3)
            pdf.set_font("Helvetica", "B", 12)
            pdf.multi_cell(0, 7, safe_line)
            pdf.set_font("Helvetica", size=10)
        else:
            pdf.multi_cell(0, 6, safe_line)
            
    return pdf.output()

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
        if mode == "⚡ Quick Summary & Key Takeaways":
            prompt = f"Provide a concise summary, bullet points, and key takeaways for this content. Use plain text and simple equation symbols, avoid complex raw LaTeX:\n\n{final_text}"
        elif mode == "📝 Exam Cheat Sheet (Definitions, Formulas & Key Points)":
            prompt = (
                "Format this into a high-yield Exam Cheat Sheet with: "
                "1. Core Definitions (1-2 lines each), 2. Essential Formulas/Rules, "
                "3. Crucial High-Yield Points to remember for exams. Avoid raw LaTeX syntax:\n\n"
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

                # Display Output
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

                # Audio Revision Player
                try:
                    clean_audio_text = output_text.replace("#", "").replace("*", "").strip()
                    tts = gTTS(text=clean_audio_text[:1000], lang='en')
                    audio_bytes = io.BytesIO()
                    tts.write_to_fp(audio_bytes)
                    audio_bytes.seek(0)
                    st.write("---")
                    st.subheader("🎧 Listen to Revision Audio:")
                    st.audio(audio_bytes, format="audio/mp3")
                except Exception:
                    pass

                # Download Buttons
                st.write("---")
                col1, col2 = st.columns(2)
                with col1:
                    # PDF Generator
                    try:
                        pdf_data = create_pdf(output_text)
                        st.download_button(
                            label="📄 Download as PDF",
                            data=bytes(pdf_data),
                            file_name="study_notes.pdf",
                            mime="application/pdf",
                            use_container_width=True
                        )
                    except Exception as pdf_err:
                        st.download_button(
                            label="📥 Download as TXT",
                            data=output_text,
                            file_name="study_notes.txt",
                            mime="text/plain",
                            use_container_width=True
                        )
                with col2:
                    st.download_button(
                        label="📑 Download as Markdown",
                        data=output_text,
                        file_name="study_notes.md",
                        mime="text/markdown",
                        use_container_width=True
            )
                    
