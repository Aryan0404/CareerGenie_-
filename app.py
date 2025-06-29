
import streamlit as st
import os
from langchain_openai import ChatOpenAI
from langchain_community.tools.tavily_search import TavilySearchResults
from langchain.agents import create_react_agent, AgentExecutor
from langchain_core.tools import tool
import requests
from langchain import hub
import PyPDF2
from io import BytesIO
import tempfile
import subprocess
import boto3
import hashlib
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
from datetime import datetime, timedelta
import json
import time
import hashlib
import tempfile
import subprocess
from pathlib import Path

from dotenv import load_dotenv
load_dotenv()

if 'chat_history' not in st.session_state:
    st.session_state.chat_history = []
if 'user_profile' not in st.session_state:
    st.session_state.user_profile = {}

os.environ["OPENAI_API_KEY"] = os.getenv("OPENAI_API_KEY")
os.environ["TAVILY_API_KEY"] = os.getenv("TAVILY_API_KEY")

st.markdown("""
<style>
   .main-header {
    background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
    padding: 2rem;
    border-radius: 10px;
    margin-bottom: 2rem;
    text-align: center;
    color: #ffffff;
    box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
    font-size: 1.5rem;
    font-weight: bold;
    }

    

    .feature-card:hover {
        transform: translateY(-2px);
        box-shadow: 0 4px 10px rgba(0, 0, 0, 0.3);
    }

    .metric-card {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 1rem;
        border-radius: 8px;
        color: white;
        text-align: center;
        margin: 0.5rem 0;
        font-weight: 600;
    }

    .success-message {
        background: #2d5f2e;
        border: 1px solid #44c556;
        color: #d4f8d4;
        padding: 1rem;
        border-radius: 5px;
        margin: 1rem 0;
    }

    .warning-message {
        background: #5c3c00;
        border: 1px solid #ffc107;
        color: #ffeaa7;
        padding: 1rem;
        border-radius: 5px;
        margin: 1rem 0;
    }
    .chat-message {
    padding: 1rem;
    margin: 0.5rem 0;
    border-radius: 10px;
    max-width: 80%;
    font-size: 1rem;
    line-height: 1.5;
    }

    .user-message {
        background: #1e88e5;
        color: white;
        margin-left: auto;
        text-align: right;
    }

    .assistant-message {
        background: #2e2e2e;
        color: white;
        margin-right: auto;
    }
    
   
    .progress-bar {
        background: #e0e0e0;
        border-radius: 10px;
        height: 8px;
        overflow: hidden;
        margin: 1rem 0;
    }
    
    .progress-fill {
        background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
        height: 100%;
        border-radius: 10px;
        transition: width 0.3s ease;
    }
</style>
""", unsafe_allow_html=True)

search_tool = TavilySearchResults(k=5)

@tool
def get_company_weather(city: str) -> str:
    """Fetches weather info for the city where the company is located."""
    try:
        api_key = os.getenv("WEATHERSTACK_API_KEY", "your_weatherstack_api_key_here")
        url = f"http://api.weatherstack.com/current?access_key={api_key}&query={city}"
        response = requests.get(url)
        data = response.json()
        if "current" in data:
            weather = data["current"]
            return f"🌤️ Weather in {city}: {weather['temperature']}°C, {weather['weather_descriptions'][0]}"
        else:
            return "🌡️ Weather data not available for this location."
    except Exception as e:
        return f"⚠️ Unable to fetch weather data: {str(e)}"

@tool
def enhanced_resume_feedback(file_text: str) -> str:
    """Provides comprehensive resume feedback with scoring."""
    llm = ChatOpenAI(temperature=0.3)
    prompt = f"""
    You are an expert resume reviewer with 10+ years of experience in talent acquisition.
    Analyze the following resume and provide:
    
    1. Overall Score (1-10)
    2. Strengths (3-5 points)
    3. Areas for Improvement (3-5 points)
    4. Specific Recommendations
    5. ATS Compatibility Assessment
    6. Industry-specific feedback
    
    Resume content:
    {file_text}
    
    Format your response with clear sections and actionable advice.
    """
    response = llm.invoke(prompt)
    return response.content

@tool
def advanced_roadmap_generator(role: str, experience_level: str = "beginner") -> str:
    """Generate a detailed, time-bound career roadmap."""
    llm = ChatOpenAI(temperature=0.2)
    prompt = f"""
    Create a comprehensive career roadmap for a {experience_level} level professional wanting to become a {role}.
    
    Include:
    1. 6-month milestones
    2. Essential skills to develop
    3. Recommended courses/certifications
    4. Portfolio projects
    5. Networking strategies
    6. Salary progression expectations
    7. Common career transitions
    
    Make it specific, actionable, and time-bound.
    """
    response = llm.invoke(prompt)
    return response.content

@tool
def interview_question_generator(role: str, difficulty: str = "medium") -> str:
    """Generate role-specific interview questions with model answers."""
    llm = ChatOpenAI(temperature=0.4)
    prompt = f"""
    Generate 5 {difficulty} level interview questions for a {role} position.
    
    For each question, provide:
    1. The question
    2. Key points to cover in the answer
    3. A sample good response
    4. Common mistakes to avoid
    
    Focus on both technical and behavioral aspects.
    """
    response = llm.invoke(prompt)
    return response.content

import tempfile
import subprocess
import hashlib
from pathlib import Path

@st.cache_data(show_spinner=False)
def generate_audio_response(text: str, voice_id: str = "Joanna", format: str = "mp3") -> bytes:
    """
    Generate audio from text using Amazon Polly with optional format conversion.
    Supports mp3 (default) and wav using ffmpeg. Caches results.
    """
    if not text.strip() or len(text) > 3000:
        return None

    unique_hash = hashlib.md5((text + voice_id + format).encode()).hexdigest()
    cache_path = Path(tempfile.gettempdir()) / f"{unique_hash}.{format}"

    if cache_path.exists():
        return cache_path.read_bytes()

    try:
        polly = boto3.client(
            'polly',
            aws_access_key_id=os.getenv("AWS_ACCESS_KEY_ID"),
            aws_secret_access_key=os.getenv("AWS_SECRET_ACCESS_KEY"),
            region_name='us-east-1'
        )
        response = polly.synthesize_speech(
            Text=text[:3000],
            VoiceId=voice_id,
            OutputFormat="mp3"
        )

        if "AudioStream" not in response:
            return None

        mp3_path = tempfile.NamedTemporaryFile(delete=False, suffix=".mp3").name
        with open(mp3_path, "wb") as f:
            f.write(response["AudioStream"].read())

        if format == "wav":
            wav_path = str(cache_path)
            subprocess.run(["ffmpeg", "-y", "-i", mp3_path, wav_path], check=True)
        else:
            Path(mp3_path).rename(cache_path)

        return cache_path.read_bytes()

    except Exception as e:
        st.error(f"🎧 Polly audio generation failed: {e}")
        return None

@st.cache_resource
def setup_agent():
    llm = ChatOpenAI(temperature=0.3)
    prompt = hub.pull("hwchase17/react")
    agent = create_react_agent(
        llm=llm, 
        tools=[search_tool, get_company_weather, enhanced_resume_feedback, 
               advanced_roadmap_generator, interview_question_generator], 
        prompt=prompt
    )
    return AgentExecutor(
        agent=agent, 
        tools=[search_tool, get_company_weather, enhanced_resume_feedback, 
               advanced_roadmap_generator, interview_question_generator], 
        verbose=True,
        max_iterations=10,
        handle_parsing_errors=True  
    )

agent_executor = setup_agent()

# Enhanced UI
st.set_page_config(
    page_title="CareerGenie - AI Career Assistant", 
    layout="wide",
    initial_sidebar_state="expanded",
    menu_items={
        'Get Help': 'https://www.example.com/help',
        'Report a bug': "https://www.example.com/bug",
        'About': "CareerGenie - Your AI-powered career companion!"
    }
)

st.markdown("""
<div class="main-header">
    <h1>🚀 CareerGenie</h1>
    <p>Your AI-Powered Career Companion - Accelerate Your Professional Journey</p>
</div>
""", unsafe_allow_html=True)

with st.sidebar:
    st.markdown('<div class="sidebar-content">', unsafe_allow_html=True)
    st.header("👤 Your Profile")
    
    name = st.text_input("Name", value=st.session_state.user_profile.get("name", ""))
    current_role = st.text_input("Current Role", value=st.session_state.user_profile.get("current_role", ""))
    experience = st.selectbox("Experience Level", 
                             ["Fresher", "1-2 years", "3-5 years", "5-10 years", "10+ years"],
                             index=0)
    
    if st.button("💾 Save Profile"):
        st.session_state.user_profile = {
            "name": name,
            "current_role": current_role,
            "experience": experience
        }
        st.success("Profile saved!")
    
    st.markdown('</div>', unsafe_allow_html=True)
    
    st.markdown('<div class="sidebar-content">', unsafe_allow_html=True)
    st.header("🎯 Choose Feature")
    option = st.selectbox("Select a feature", [
        "🏢 Company Research Hub",
        "📄 Resume Analyzer Pro",
        "🎤 Mock Interview Studio",
        "🗺️ Career Roadmap Builder",
        "📊 Market Intelligence",
        "💬 Career Chat Assistant"
    ])
    st.markdown('</div>', unsafe_allow_html=True)

import re

# Utility function to extract scores from LLM output
def extract_scores(text: str):
    score_labels = [
        "Overall Score",
        
    ]

    scores = {}
    for label in score_labels:
        # Match formats like: Overall Score: 8, Overall Score - 8.5, etc.
        pattern = rf"{label}[^0-9\-]*?(\d+(?:\.\d+)?)"
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            scores[label] = float(match.group(1))
        else:
            scores[label] = None
    return scores
col1, col2 = st.columns([2, 1])

with col1:
    if option == "🏢 Company Research Hub":
        st.markdown('<div class="feature-card">', unsafe_allow_html=True)
        st.subheader("🔍 Deep Company Research")
        st.write("Get comprehensive insights about companies, their culture, interview processes, and more!")
        
        company = st.text_input("🏢 Company Name", placeholder="e.g., Google, Microsoft, Amazon")
        
        col_a, col_b = st.columns(2)
        with col_a:
            city = st.text_input("🌍 City (Optional)", placeholder="e.g., Bangalore, Mumbai")
        with col_b:
            research_depth = st.selectbox("Research Depth", ["Quick Overview", "Detailed Analysis", "Complete Dossier"])
        
        research_areas = st.multiselect(
            "What would you like to know?",
            ["Company Culture", "Interview Process", "Salary Ranges", "Recent News", "Growth Prospects", "Work-Life Balance"]
        )
        
        if st.button("🚀 Start Research", type="primary"):
            if company:
                with st.spinner("🔍 Researching company data..."):
                    research_query = f"Provide detailed information about {company}"
                    if research_areas:
                        research_query += f" focusing on: {', '.join(research_areas)}"
                    
                    progress_bar = st.progress(0)
                    for i in range(100):
                        time.sleep(0.01)
                        progress_bar.progress(i + 1)
                    
                    response = agent_executor.invoke({"input": research_query})
                    
                    st.markdown('<div class="success-message">', unsafe_allow_html=True)
                    st.write("✅ Research Complete!")
                    st.markdown('</div>', unsafe_allow_html=True)
                    
                    st.markdown("### 📊 Company Analysis")
                    st.write(response["output"])
                    
                    # Add weather info if city provided
                    if city:
                        weather_info = agent_executor.invoke({"input": f"Get weather in {city}"})
                        st.markdown("### 🌤️ Local Weather")
                        st.info(weather_info["output"])
                    
                    # Audio response
                    # audio_bytes = generate_audio_response(response["output"][:1000], format="wav")
                    # if audio_bytes:
                    #     st.audio(BytesIO(audio_bytes), format="audio/wav")
                    # else:
                    #     st.warning("Audio could not be generated.")
                        # Download option
                    st.download_button(
                        "📥 Download Research Report",
                        data=response["output"],
                        file_name=f"{company}_research_report.txt",
                        mime="text/plain"
                    )
            else:
                st.error("Please enter a company name!")
        
        st.markdown('</div>', unsafe_allow_html=True)

    elif option == "📄 Resume Analyzer Pro":
        st.markdown('<div class="feature-card">', unsafe_allow_html=True)
        st.subheader("📋 Professional Resume Analysis")
        st.write("Get expert feedback on your resume with AI-powered insights and scoring!")
        
        uploaded_file = st.file_uploader("📤 Upload Your Resume", type=["pdf"], 
                                       help="Upload your resume in PDF format for analysis")
        
        if uploaded_file:
            col_a, col_b = st.columns(2)
            with col_a:
                target_role = st.text_input("🎯 Target Role", placeholder="e.g., Software Engineer")
            with col_b:
                industry = st.selectbox("🏭 Industry", 
                                      ["Technology", "Finance", "Healthcare", "Marketing", "Consulting", "Other"])
            
            if st.button("🔍 Analyze Resume", type="primary"):
                with st.spinner("🤖 AI is analyzing your resume..."):
                    try:
                        reader = PyPDF2.PdfReader(uploaded_file)
                        full_text = "\n".join([page.extract_text() for page in reader.pages if page.extract_text()])
                        
                        if len(full_text.strip()) < 100:
                            st.error("⚠️ Resume content seems too short. Please ensure the PDF is readable.")
                        else:
                            analysis_query = f"Analyze this resume for {target_role} role in {industry} industry: {full_text}"
                            response = agent_executor.invoke({"input": analysis_query})
                            
                            result_text = response["output"]

                            st.markdown("### 📊 Resume Analysis Results")
                            st.write(result_text)
                            scores = extract_scores(result_text)

                            st.markdown("### 📈 Scoring Breakdown")
                            for metric, score in scores.items():
                                if score is not None:
                                    delta = f"{score - 5:.1f}"
                                    st.metric(metric, f"{score:.1f}/10", delta)
                                else:
                                    st.metric(metric, "N/A", "–")
                            st.markdown("### 📈 Scoring Breakdown")
                            for metric, score in scores.items():
                                st.metric(metric, f"{score}/10", f"{score-5:.1f}")
                            
                            # audio_bytes = generate_audio_response(response["output"][:1000], format="wav")
                            # if audio_bytes:
                            #     st.audio(BytesIO(audio_bytes), format="audio/wav")
                            # else:
                            #     st.warning("Audio could not be generated.")
                            st.download_button(
                                "📥 Download Analysis Report",
                                data=response["output"],
                                file_name="resume_analysis_report.txt",
                                mime="text/plain"
                            )
                    except Exception as e:
                        st.error(f"Error processing resume: {str(e)}")
        
        st.markdown('</div>', unsafe_allow_html=True)

    elif option == "🎤 Mock Interview Studio":
        st.markdown('<div class="feature-card">', unsafe_allow_html=True)
        st.subheader("🎭 Interactive Interview Practice")
        st.write("Practice with AI-generated questions tailored to your role and experience level!")
        
        col_a, col_b, col_c = st.columns(3)
        with col_a:
            interview_role = st.selectbox("🎯 Role", 
                                        ["Software Engineer", "Data Scientist", "Product Manager", 
                                         "DevOps Engineer", "UI/UX Designer", "Marketing Manager"])
        with col_b:
            difficulty = st.selectbox("📊 Difficulty", ["Beginner", "Intermediate", "Advanced"])
        with col_c:
            question_count = st.selectbox("❓ Questions", [3, 5, 10])
        
        interview_type = st.radio("Interview Type", 
                                ["Technical", "Behavioral", "Mixed"], horizontal=True)
        
        if st.button("🎬 Start Mock Interview", type="primary"):
            with st.spinner("🤖 Preparing your interview questions..."):
                query = f"Generate {question_count} {difficulty} {interview_type} interview questions for {interview_role}"
                response = agent_executor.invoke({"input": query})
                
                st.markdown("### 🎯 Your Interview Questions")
                st.write(response["output"])
                
                st.markdown("### ⏱️ Interview Timer")
                if st.button("Start Timer"):
                    placeholder = st.empty()
                    for seconds in range(1800, 0, -1):  # 30 minutes
                        mins, secs = divmod(seconds, 60)
                        placeholder.metric("Time Remaining", f"{mins:02d}:{secs:02d}")
                        time.sleep(1)
                
                # audio_bytes = generate_audio_response(response["output"][:1000], format="wav")
                # if audio_bytes:
                #     st.audio(BytesIO(audio_bytes), format="audio/wav")
                # else:
                #     st.warning("Audio could not be generated.")                
                st.download_button(
                    "📥 Download Interview Questions",
                    data=response["output"],
                    file_name=f"{interview_role}_interview_questions.txt",
                    mime="text/plain"
                )
        
        st.markdown('</div>', unsafe_allow_html=True)

    elif option == "🗺️ Career Roadmap Builder":
        st.markdown('<div class="feature-card">', unsafe_allow_html=True)
        st.subheader("🛤️ Personalized Career Pathway")
        st.write("Get a detailed roadmap tailored to your career goals and current experience!")

        target_role = st.text_input("🎯 Target Role", placeholder="e.g., Senior Data Scientist")
        current_skills = st.text_area("💡 Current Skills", placeholder="List your current skills...")

        col_a, col_b = st.columns(2)
        with col_a:
            timeline = st.selectbox("⏰ Timeline", ["6 months", "1 year", "2 years", "3+ years"])
        with col_b:
            focus_area = st.selectbox("🎯 Focus Area",
                                    ["Technical Skills", "Leadership", "Certifications", "All-Round Development"])

        if st.button("🚀 Generate Roadmap", type="primary"):
            with st.spinner("🗺️ Creating your personalized roadmap..."):
                roadmap_prompt = f"""
                Create a JSON response for a career roadmap for becoming a {target_role} in {timeline}.
                Focus on: {focus_area}
                Current skills: {current_skills}

                Respond in this JSON format only:
                {{
                "milestones": ["Step 1", "Step 2", ...],
                "progress": [10, 30, 60, 80, 100],
                "details": ["What to do in Step 1", "Step 2", ...]
                }}
                """

                try:
                    response = agent_executor.invoke({"input": roadmap_prompt})
                    roadmap = json.loads(response["output"])
                    milestones = roadmap["milestones"]
                    progress = roadmap["progress"]
                    details = roadmap["details"]

                    st.markdown("### 🗺️ Your Career Roadmap")
                    for milestone, step_detail, step_progress in zip(milestones, details, progress):
                        st.subheader(f"🔹 {milestone}")
                        st.write(step_detail)
                        st.progress(step_progress)
                    st.markdown("### 📈 Visual Progress")
                    fig = go.Figure()
                    fig.add_trace(go.Scatter(
                        x=milestones,
                        y=progress,
                        mode='lines+markers',
                        line=dict(color='purple', width=3),
                        marker=dict(size=8)
                    ))
                    fig.update_layout(title="Career Progress", xaxis_title="Milestones", yaxis_title="Progress %")
                    st.plotly_chart(fig, use_container_width=True)

                except Exception as e:
                    st.error(f"❌ Failed to generate roadmap: {e}")
                    st.warning("Try again with clearer inputs.")

        st.markdown('</div>', unsafe_allow_html=True)
    elif option == "📊 Market Intelligence":
        st.markdown('<div class="feature-card">', unsafe_allow_html=True)
        st.subheader("📈 Industry Insights & Trends")
        st.write("Stay ahead with the latest market trends, salary data, and skill demands!")
        
        analysis_type = st.radio("Analysis Type", 
                                ["Job Market Trends", "Salary Analysis", "Skill Demand", "Industry Growth"], 
                                horizontal=True)
        
        col_a, col_b = st.columns(2)
        with col_a:
            role_tech = st.text_input("🔍 Role/Technology", placeholder="e.g., Machine Learning Engineer")
        with col_b:
            location = st.selectbox("📍 Location", ["India", "USA", "UK", "Canada", "Global"])
        
        if st.button("📊 Generate Intelligence Report", type="primary"):
            with st.spinner("📈 Gathering market intelligence..."):
                query = f"Provide latest {analysis_type} for {role_tech} in {location} market with salary ranges and growth prospects"
                response = agent_executor.invoke({"input": query})
                
                st.markdown("### 📊 Market Intelligence Report")
                st.write(response["output"])
                
                # Mock data visualization
                if analysis_type == "Salary Analysis":
                    salary_data = pd.DataFrame({
                        'Experience': ['0-2 years', '2-5 years', '5-8 years', '8+ years'],
                        'Salary_Min': [300000, 600000, 1200000, 2000000],
                        'Salary_Max': [600000, 1200000, 2500000, 4000000]
                    })
                    
                    fig = px.bar(salary_data, x='Experience', y=['Salary_Min', 'Salary_Max'], 
                               title="Salary Ranges by Experience")
                    st.plotly_chart(fig, use_container_width=True)
                
                st.download_button(
                    "📥 Download Market Report",
                    data=response["output"],
                    file_name=f"{role_tech}_market_intelligence.txt",
                    mime="text/plain"
                )
        
        st.markdown('</div>', unsafe_allow_html=True)

    elif option == "💬 Career Chat Assistant":
        st.markdown('<div class="feature-card">', unsafe_allow_html=True)
        st.subheader("🤖 AI Career Counselor")
        st.write("Have a conversation with your AI career counselor about any career-related questions!")
        
        for message in st.session_state.chat_history:
            if message["role"] == "user":
                st.markdown(f'<div class="chat-message user-message">👤 {message["content"]}</div>', 
                          unsafe_allow_html=True)
            else:
                st.markdown(f'<div class="chat-message assistant-message">🤖 {message["content"]}</div>', 
                          unsafe_allow_html=True)
        
        user_question = st.text_input("💭 Ask me anything about your career...", 
                                    placeholder="e.g., How do I transition from marketing to data science?")
        
        col_a, col_b = st.columns([1, 4])
        with col_a:
            if st.button("Send 📤", type="primary"):
                if user_question:
                    st.session_state.chat_history.append({"role": "user", "content": user_question})
                    
                    with st.spinner("🤖 AI is thinking..."):
                        response = agent_executor.invoke({"input": user_question})
                        
                        st.session_state.chat_history.append({"role": "assistant", "content": response["output"]})
                        
                        st.rerun()
        
        with col_b:
            if st.button("🗑️ Clear Chat"):
                st.session_state.chat_history = []
                st.rerun()
        
        st.markdown('</div>', unsafe_allow_html=True)

with col2:
    st.markdown("### 💡 Pro Tips")
    tips = [
        "💼 Keep your resume updated regularly",
        "🌐 Build a strong LinkedIn profile",
        "📚 Continuous learning is key",
        "🤝 Network actively in your industry",
        "🎯 Set clear career goals",
        "📊 Track your progress regularly"
    ]
    
    for tip in tips:
        st.info(tip)
    
    # Usage statistics
    st.markdown("### 📈 Your Usage Stats")
    st.metric("Sessions This Month", "12", "↗️ 3")
    st.metric("Resume Analyses", "3", "↗️ 1")
    st.metric("Mock Interviews", "5", "↗️ 2")
    
    # Quick actions
    st.markdown("### ⚡ Quick Actions")
    if st.button("🔄 Refresh Data"):
        st.success("Data refreshed!")
    
    if st.button("💾 Export Profile"):
        profile_data = json.dumps(st.session_state.user_profile, indent=2)
        st.download_button(
            "Download Profile",
            data=profile_data,
            file_name="career_profile.json",
            mime="application/json"
        )

