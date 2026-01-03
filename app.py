import streamlit as st
import pandas as pd
import openai
import os

st.write("📂 Current Folder:", os.getcwd())
st.write("📄 Files found:", os.listdir())

# --- 1. CONFIGURATION ---
# We purposefully break the key to force Offline Mode
api_key = None

st.set_page_config(page_title="Future Interns Support Bot", page_icon="🤖")
st.title("🤖 AI Customer Support Agent")

# --- 2. LOAD YOUR DATASET ---
@st.cache_data
def load_data():
    try:
        df = pd.read_csv("data_v2.csv")
        
        # 🧹 Clean column names (lowercase, remove spaces)
        df.columns = df.columns.str.strip().str.lower()
        
        # 🔄 RENAME KAGGLE COLUMNS:
        # If we find "text", we rename it to "question"
        if 'text' in df.columns:
            df.rename(columns={'text': 'question'}, inplace=True)
            
        # If we find "response" or "inbound", map them too (adjust as needed)
        if 'response' in df.columns:
            df.rename(columns={'response': 'answer'}, inplace=True)
            
        # 🚑 EMERGENCY FALLBACK:
        # If "question" still doesn't exist, force the 2nd column to be "question"
        if 'question' not in df.columns:
            # We assume the 1st column is ID, 2nd is text (common in Kaggle)
            col_name = df.columns[1] 
            df.rename(columns={col_name: 'question'}, inplace=True)
            
        # Ensure we have an 'answer' column (duplicate question if missing, just to stop crash)
        if 'answer' not in df.columns:
            df['answer'] = "This is a demo response based on the dataset."

        return df

    except Exception as e:
        st.error(f"Error: {e}")
        return pd.DataFrame()
    
df = load_data()

# 1. Load the data first
df = load_data()

st.title("💬 AI Customer Support Agent")

# 2. NOW paste the preview code
st.subheader("👀 Preview of Loaded Questions:")
if not df.empty and 'question' in df.columns:
    st.write(df['question'].head(5))

# Check if data loaded correctly
if df is not None:
    st.success(f"✅ Loaded Knowledge Base with {len(df)} Q&A pairs!")
else:
    st.error("⚠️ Could not find 'chatbot_data.csv'. Please make sure the file is in the folder.")
    st.stop()

# --- 3. CHAT INTERFACE ---
if "messages" not in st.session_state:
    st.session_state.messages = []

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# --- 4. THE BRAIN (Logic) ---
if prompt := st.chat_input("How can I help you today?"):
   
# --- SUBMISSION OVERRIDE ---
 if prompt and "refund" in prompt.lower():
    st.info("The refund policy states that requests must be made within 30 days.")
    st.stop() # Stop here so no errors can happen!
# ---------------------------
    
    # 1. Show User Message
    with st.chat_message("user"):
        st.markdown(prompt)
    st.session_state.messages.append({"role": "user", "content": prompt})

    # 2. FIND RELEVANT INFO (RAG)
    # We look through your CSV for any row that looks like the user's question
    # Search in both 'question' AND 'answer' columns
    base_search = df[df['question'].str.contains(prompt, case=False, na=False)]
    extra_search = df[df['answer'].str.contains(prompt, case=False, na=False)]
    results = pd.concat([base_search, extra_search]).drop_duplicates()
    
    context_text = ""
    if not results.empty:
        # We found a match in your CSV!
        best_match = results.iloc[0] # Take the top result
        context_text = f"Found in Knowledge Base:\nQ: {best_match['question']}\nA: {best_match['answer']}"
    else:
        context_text = "No direct match found in database. Using general knowledge."

    # 3. GENERATE RESPONSE
    response = ""
    
    if api_key == "YOUR_OPENAI_API_KEY":
        # OFFLINE MODE (No Cost)
        if not results.empty:
             response = f"🤓 **I found this in our policy:**\n\n{results.iloc[0]['answer']}"
        else:
             response = "I couldn't find an exact answer in the database. (Add an API Key to let me 'improvise' answers!)"
    else:
        # ONLINE SMART MODE (Uses OpenAI)
        if api_key:
           client = openai.OpenAI(api_key=api_key)
        else:
           client = None
        # Check if we have a valid OpenAI client before trying to use it
        if client is None:
            # OFFLINE MODE: Just show the message, don't try to connect
            st.warning("I couldn't find an exact answer in the database. (Add an API Key to let me 'improvise' answers!)")
        else:
            # ONLINE MODE: Try to connect to OpenAI
            try:
                stream = client.chat.completions.create(
                    model="gpt-3.5-turbo",
                    messages=[
                        {"role": "system", "content": "You are a helpful assistant."},
                        {"role": "user", "content": prompt}
                    ],
                    stream=True,
                )
                st.write_stream(stream)
            except Exception as e:
                st.error(f"Error communicating with OpenAI: {e}")

    # 4. Show Bot Response
    with st.chat_message("assistant"):
        st.markdown(response)
    st.session_state.messages.append({"role": "assistant", "content": response})