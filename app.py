import streamlit as st
from google import genai
import os

st.set_page_config(page_title="AI Study Helper", page_icon="📚")
st.title("📚 Quick AI Study Assistant")

api_key = st.secrets.get("GEMINI_API_KEY") or os.environ.get("GEMINI_API_KEY")
client = genai.Client(api_key=api_key) if api_key else None

user_text = st.text_area("Paste your topic or study notes here:", height=150)

if st.button("Generate Summary & Key Points"):
    if not client:
        st.error("API Key is not configured!")
    elif not user_text.strip():
        st.warning("Please enter some text first.")
    else:
        prompt = f"Explain this clearly in simple bullet points and key takeaways:\n\n{user_text}"
        response = client.models.generate_content(
            model="gemini-2.0-flash",
            contents=prompt
        )
        st.subheader("Your AI Summary:")
        st.write(response.text)
      
