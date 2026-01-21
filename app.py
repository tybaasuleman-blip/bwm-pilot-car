import streamlit as st
import os
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_community.tools.ddg_search import DuckDuckGoSearchRun
from langgraph.prebuilt import create_react_agent
from fpdf import FPDF
from datetime import datetime
import io

# 1. PRIMARY PAGE CONFIG (Must be the first Streamlit command!)
LOGO_URL = "https://raw.githubusercontent.com/tybaasuleman-blip/bwm-pilot-car/main/PILOT_CAR_BWM_LOGO.png"

st.set_page_config(
    page_title="BWM Pilot Car | Intelligence",
    page_icon=LOGO_URL,
    layout="wide"
)

# Sidebar Logo Branding
st.logo(LOGO_URL, link="https://bwm-pilot-car.streamlit.app")

# Initialize Session States
if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False
if 'driver_name' not in st.session_state:
    st.session_state.driver_name = ""

# Professional BWM UI Styling
st.markdown("""
    <style>
    .stApp { background-color: #f0f2f6; }
    .main-header { color: #003366; font-size: 32px; font-weight: bold; border-bottom: 3px solid #003366; padding-bottom: 10px; margin-bottom: 25px; }
    .report-card { background: #ffffff; padding: 30px; border-radius: 15px; border-left: 12px solid #003366; box-shadow: 0 10px 25px rgba(0,0,0,0.1); color: #1a1a1a; margin-top: 20px; }
    .stButton>button { background-color: #003366 !important; color: white !important; font-size: 18px !important; font-weight: bold !important; border-radius: 8px; height: 3.5em; width: 100%; border: none; }
    </style>
    """, unsafe_allow_html=True)

# 2. PDF GENERATOR LOGIC
def create_bwm_pdf(route, content, driver):
    pdf = FPDF()
    pdf.add_page()
    
    # Blue Header Bar
    pdf.set_fill_color(0, 51, 102)
    pdf.rect(0, 0, 210, 40, 'F')
    
    pdf.set_font("Arial", 'B', 22)
    pdf.set_text_color(255, 255, 255)
    pdf.cell(0, 15, "BWM PILOT CAR SERVICE, LLC", ln=True, align='C')
    pdf.set_font("Arial", 'I', 12)
    pdf.cell(0, 10, "Official Safety & Route Intelligence Report", ln=True, align='C')
    
    pdf.ln(20)
    pdf.set_text_color(0, 0, 0)
    
    # Metadata Table
    pdf.set_fill_color(230, 235, 245)
    pdf.set_font("Arial", 'B', 11)
    pdf.cell(45, 10, " ROUTE:", 1, 0, 'L', True)
    pdf.set_font("Arial", '', 11)
    pdf.cell(145, 10, f" {route}", 1, 1, 'L')
    
    pdf.set_font("Arial", 'B', 11)
    pdf.cell(45, 10, " DATE/TIME:", 1, 0, 'L', True)
    pdf.set_font("Arial", '', 11)
    pdf.cell(145, 10, f" {datetime.now().strftime('%Y-%m-%d %I:%M %p')}", 1, 1, 'L')
    
    pdf.set_font("Arial", 'B', 11)
    pdf.cell(45, 10, " PILOT DRIVER:", 1, 0, 'L', True)
    pdf.set_font("Arial", '', 11)
    pdf.cell(145, 10, f" {driver}", 1, 1, 'L')
    
    pdf.ln(10)
    
    # Content Body
    pdf.set_font("Arial", 'B', 14)
    pdf.set_text_color(0, 51, 102)
    pdf.cell(0, 10, "SAFETY ANALYSIS & LOGISTICS", ln=True)
    pdf.set_line_width(0.5)
    pdf.line(10, pdf.get_y(), 200, pdf.get_y())
    pdf.ln(5)
    
    pdf.set_font("Arial", size=11)
    pdf.set_text_color(0, 0, 0)
    
    # Clean text for Latin-1 encoding
    clean_text = content.replace('\u2022', '-').replace('\u2013', '-').replace('\u2019', "'").replace('\u201d', '"').replace('\u201c', '"')
    pdf.multi_cell(0, 8, txt=clean_text.encode('latin-1', 'ignore').decode('latin-1'))
    
    return bytes(pdf.output(dest='S'))

# 3. SIDEBAR AUTH & API KEY
with st.sidebar:
    st.markdown("### 🛠️ BWM TERMINAL")
    if not st.session_state.logged_in:
        u_id = st.text_input("Unit ID / Driver Name")
        u_pw = st.text_input("Security PIN", type="password")
        if st.button("Authorize Access"):
            if u_id and u_pw == "PILOT":
                st.session_state.logged_in = True
                st.session_state.driver_name = u_id.upper()
                st.rerun()
    else:
        st.success(f"ONLINE: {st.session_state.driver_name}")
        
        # KEY LOGIC: Check Secrets first
        if "GOOGLE_API_KEY" in st.secrets:
            api_key = st.secrets["GOOGLE_API_KEY"]
            st.info("✅ Enterprise AI Active")
        else:
            api_key = st.text_input("Gemini API Key", type="password")
            
        if st.button("End Session"):
            st.session_state.logged_in = False
            st.rerun()
    st.divider()
    st.markdown("**BWM Logistics HQ**\nFort Lauderdale, FL")

# 4. MAIN INTERFACE
if not st.session_state.logged_in:
    st.markdown("<div class='main-header'>BWM Pilot Car Service | Enterprise Portal</div>", unsafe_allow_html=True)
    st.warning("Please log in via the sidebar to access route intelligence.")
else:
    st.markdown(f"<div class='main-header'>BWM Intelligence Dashboard</div>", unsafe_allow_html=True)
    
    route_q = st.text_input("Enter Route (e.g. Houston, TX to New Orleans, LA)", placeholder="Houston, TX to New Orleans, LA")
    
    col1, col2 = st.columns(2)
    with col1:
        search_trigger = st.button("🚀 EXECUTE ALL-IN-ONE SEARCH")
    with col2:
        if st.button("✨ Load Video Demo Route"):
            route_q = "Houston, TX to New Orleans, LA via I-10"

    if (search_trigger) and route_q:
        if not api_key:
            st.error("Please provide your API Key in the sidebar or Secrets.")
        else:
            with st.spinner("BWM AI is calculating distance, weather, fuel, and bridges..."):
                try:
                    # FIX: Using the most current Flash model ID for 2026
                    llm = ChatGoogleGenerativeAI(model="gemini-1.5-flash", google_api_key=api_key)
                    search = DuckDuckGoSearchRun()
                    agent = create_react_agent(llm, [search])

                    prompt = f"""
                    Research a professional safety audit for BWM Pilot Car route: {route_q}.
                    Provide the following in one concise report:
                    1. DISTANCE: Total miles and estimated travel time.
                    2. WEATHER: Current conditions and wind gust alerts for today.
                    3. BRIDGES: List low clearances or height restrictions on major highways.
                    4. FUEL & REST: 3 truck-friendly stops (Loves/Pilot) and safe rest areas for oversized loads.
                    
                    Format with bold headers and clear bullet points.
                    """
                    
                    response = agent.invoke({"messages": [("user", prompt)]})
                    report_text = response["messages"][-1].content
                    
                    if isinstance(report_text, list):
                        report_text = "\n".join([str(item.get('text', item)) for item in report_text])

                    st.markdown(f"<div class='report-card'><h3>Route Intel: {route_q}</h3><hr>{report_text}</div>", unsafe_allow_html=True)
                    
                    pdf_data = create_bwm_pdf(route_q, report_text, st.session_state.driver_name)
                    
                    st.divider()
                    st.success("✅ Analysis Complete. Official BWM PDF Report is ready.")
                    st.download_button(
                        label="📥 DOWNLOAD OFFICIAL BWM PDF REPORT",
                        data=pdf_data,
                        file_name=f"BWM_Report_{datetime.now().strftime('%Y%m%d_%H%M')}.pdf",
                        mime="application/pdf"
                    )
                except Exception as e:
                    st.error(f"System Error: {e}")
