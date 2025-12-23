import streamlit as st
import google.generativeai as genai
import time
from google.api_core.exceptions import ResourceExhausted

# --- CONFIGURATION ---
st.set_page_config(page_title="Pavel PhD AI (Unstoppable)", page_icon="⚛️", layout="wide")

# Custom Styles for the Debate Arena
st.markdown("""
<style>
    .stChatMessage { font-family: 'Times New Roman', serif; }
    .theorist { background-color: #e3f2fd; padding: 10px; border-radius: 10px; border-left: 5px solid #2196f3; }
    .applied { background-color: #e8f5e9; padding: 10px; border-radius: 10px; border-left: 5px solid #4caf50; }
    .verdict { background-color: #fffde7; padding: 10px; border-radius: 10px; border-left: 5px solid #fbc02d; }
</style>
""", unsafe_allow_html=True)

# --- KEY ROTATOR (The Vault) ---
def get_working_model(system_instruction):
    # 1. Try Loading Keys from Secrets (The Vault)
    if "gemini" in st.secrets and "keys" in st.secrets["gemini"]:
        keys = st.secrets["gemini"]["keys"]
    else:
        # Fallback: Return None so we can ask for manual key
        return None

    # 2. Try keys one by one until one works
    for i, key in enumerate(keys):
        try:
            genai.configure(api_key=key)
            # Test connection with a dummy model config (no request sent yet)
            model = genai.GenerativeModel(
                model_name="gemini-1.5-flash",
                system_instruction=system_instruction
            )
            return model # If we get here without error, return this model setup
        except Exception:
            continue # Try next key
            
    st.error("💀 ALL KEYS EXHAUSTED. Add more accounts to Secrets.")
    return None

# --- SIDEBAR ---
with st.sidebar:
    st.header("🧠 Control Panel")
    
    # Check if Vault is Active
    if "gemini" in st.secrets:
        st.success(f"🔐 Vault Active: {len(st.secrets['gemini']['keys'])} Keys Loaded")
        st.caption("Auto-Rotation Enabled")
    else:
        st.warning("⚠️ No Vault Found. Add keys in App Settings -> Secrets.")
        manual_key = st.text_input("Or enter Manual Key", type="password")

    mode = st.radio("Select Mode:", ["📚 Document Research", "⚔️ AI Debate Arena"])

    if mode == "📚 Document Research":
        st.info("Upload books and solve equations.")
        uploaded_files = st.file_uploader("Library", accept_multiple_files=True, type=['pdf', 'png', 'jpg'])
    else:
        st.info("Two AI Personas will fight over your question.")
        uploaded_files = [] 

# --- MAIN APP ---
st.title("🎓 Pavel AI: PhD Research Station")

# --- MODE 1: RESEARCH ---
if mode == "📚 Document Research":
    if "doc_messages" not in st.session_state: st.session_state.doc_messages = []
    
    for msg in st.session_state.doc_messages:
        with st.chat_message(msg["role"]): st.markdown(msg["content"])

    if prompt := st.chat_input("Ask about your uploaded PDFs..."):
        st.session_state.doc_messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"): st.markdown(prompt)

        with st.chat_message("assistant"):
            with st.spinner("Analyzing documents..."):
                # Get a working model from the vault
                model = get_working_model("You are a PhD Researcher. Use LaTeX for math.")
                
                # Manual Key Fallback
                if not model and 'manual_key' in locals() and manual_key:
                    genai.configure(api_key=manual_key)
                    model = genai.GenerativeModel("gemini-1.5-flash")

                if model:
                    try:
                        # Prepare Content (Text + Files)
                        content = [prompt]
                        if uploaded_files:
                            for file in uploaded_files:
                                # Send PDF data directly to Gemini
                                content.append({"mime_type": file.type, "data": file.getvalue()})
                        
                        response = model.generate_content(content)
                        st.markdown(response.text)
                        st.session_state.doc_messages.append({"role": "assistant", "content": response.text})
                    except Exception as e:
                        st.error(f"Error: {e}")

# --- MODE 2: DEBATE ARENA ---
else:
    st.subheader("⚔️ The Debate Arena: Theory vs. Application")
    if "debate_history" not in st.session_state: st.session_state.debate_history = []

    for item in st.session_state.debate_history:
        st.markdown(item, unsafe_allow_html=True)

    if topic := st.chat_input("Enter a controversial physics topic..."):
        st.markdown(f"**You:** {topic}")
        st.session_state.debate_history.append(f"**You:** {topic}")

        # 1. THEORIST
        with st.spinner("Theorist is deriving axioms..."):
            model = get_working_model("You are a Formal Theorist. Use LaTeX. Be stubborn.")
            if model:
                try:
                    resp_1 = model.generate_content(f"Theoretical view: {topic}").text
                    html_1 = f"<div class='theorist'><b>🔵 Theorist:</b><br>{resp_1}</div>"
                    st.markdown(html_1, unsafe_allow_html=True)
                    st.session_state.debate_history.append(html_1)
                except Exception as e: st.error(str(e))

        # 2. APPLIED
        with st.spinner("Applied Scientist is simulating..."):
            # We call get_working_model AGAIN to rotate keys if needed
            model = get_working_model("You are an Applied Scientist. Critique the Theorist.")
            if model:
                try:
                    resp_2 = model.generate_content(f"Practical view: {topic}. Critique: {resp_1}").text
                    html_2 = f"<div class='applied'><b>🟢 Applied:</b><br>{resp_2}</div>"
                    st.markdown(html_2, unsafe_allow_html=True)
                    st.session_state.debate_history.append(html_2)
                except Exception as e: st.error(str(e))

        # 3. VERDICT
        with st.spinner("Pavel is rendering verdict..."):
            model = get_working_model("You are Pavel, Head Researcher. Synthesize.")
            if model:
                try:
                    resp_3 = model.generate_content(f"Theorist: {resp_1}. Applied: {resp_2}. Verdict?").text
                    html_3 = f"<div class='verdict'><b>⚖️ FINAL VERDICT:</b><br>{resp_3}</div>"
                    st.markdown(html_3, unsafe_allow_html=True)
                    st.session_state.debate_history.append(html_3)
                except Exception as e: st.error(str(e))
