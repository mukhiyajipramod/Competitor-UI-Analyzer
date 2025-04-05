# Competitor UI Analyzer - Dark/Light Mode Compatible

import streamlit as st

# Set page configuration (must be the first Streamlit command)
st.set_page_config(
    page_title="Competitor UI Analyzer",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="auto"
)

import requests
from bs4 import BeautifulSoup
import re
import json
import pandas as pd
from urllib.parse import urlparse

# Apply CSS for dark/light mode compatibility
st.markdown("""
<style>
/* Adaptive coloring based on theme */
.dark-light-text {
    color: var(--text-color);
}
.dark-light-bg {
    background-color: var(--background-color);
}
.dark-light-card {
    background-color: var(--secondary-background-color);
    padding: 1rem;
    border-radius: 0.5rem;
    margin-bottom: 1rem;
}
/* Common styles for both themes */
.text-center {
    text-align: center;
}
/* Rating styles that work in both modes */
.rating-legend {
    display: flex;
    margin-bottom: 15px;
}
.rating-category {
    padding: 5px 10px;
    margin-right: 10px;
    border-radius: 4px;
    color: var(--text-color);
}
.bad {
    background-color: rgba(203, 52, 56, 0.5);
    border: 1px solid #CB3438;
}
.good {
    background-color: rgba(217, 143, 5, 0.5);
    border: 1px solid #D98F05;
}
.excellent {
    background-color: rgba(95, 169, 90, 0.5);
    border: 1px solid #5FA95A;
}
/* Section header style */
.section-header {
    background-color: var(--secondary-background-color);
    border: 1px solid var(--primary-color);
    padding: 10px;
    border-radius: 5px;
    margin-bottom: 10px;
    font-weight: bold;
}
</style>
"""
, unsafe_allow_html=True)

def extract_site_name(url):
    try:
        netloc = urlparse(url).netloc
        name = netloc.replace("www.", "").split(".")[0].capitalize()
        return name
    except:
        return "Site"

st.markdown("## 🔍 Competitor UI Analyzer")
st.markdown("Analyze and compare websites using **Gemini 1.5 Pro** AI.")

API_KEY = st.secrets["gemini"]["api_key"]
API_URL = f"https://generativelanguage.googleapis.com/v1/models/gemini-1.5-pro:generateContent?key={API_KEY}"

def extract_ui_summary_from_html(url):
    try:
        response = requests.get(url, timeout=20, headers={"User-Agent": "Mozilla/5.0"})
        soup = BeautifulSoup(response.text, "html.parser")
        summary = {
            "Navbars": len(soup.find_all("nav")),
            "Forms": len(soup.find_all("form")),
            "Buttons/Links": len(soup.find_all("button")) + len(soup.find_all("a", href=True)),
            "Inputs": len(soup.find_all("input")),
            "Headers (H1–H6)": len(soup.find_all(re.compile("^h[1-6]$"))),
            "Sections": len(soup.find_all("section")),
        }
        return summary
    except Exception as e:
        return {"error": str(e)}

def call_gemini(prompt):
    headers = {"Content-Type": "application/json"}
    data = {"contents": [{"parts": [{"text": prompt}]}]}
    response = requests.post(API_URL, headers=headers, data=json.dumps(data))
    if response.status_code == 200:
        result = response.json()
        return result["candidates"][0]["content"]["parts"][0]["text"]
    else:
        # Check for rate limit errors (status code 429)
        if response.status_code == 429:
            error_text = "⚠️ API rate limit reached. Please try again later."
            st.error(error_text)
            return error_text
        else:
            return f"❌ Error from Gemini: {response.status_code} - {response.text}"

def compare_with_gemini(name1, name2, desc1, desc2):
    prompt = f"""
Compare these two website UIs and their design approaches in detail:

{name1}: {desc1}

{name2}: {desc2}

Provide a comprehensive analysis with the following sections:
1. KEY SIMILARITIES: Identify all shared UI patterns, design elements, and approaches.
2. KEY DIFFERENCES: Compare layout structure, visual hierarchy, navigation approaches, and content presentation styles.
3. UX IMPROVEMENT SUGGESTIONS: Provide specific recommendations for each site to enhance usability, focusing on:
   - Navigation improvements
   - Visual design enhancements
   - Content organization
   - Accessibility considerations
   - Interactive elements

For each category, include specific examples from each website to illustrate your points.
"""
    return call_gemini(prompt)

def score_with_gemini(name1, name2, desc1, desc2):
    prompt = f"""
Based on the following UI summaries, assign a score from 1 to 10 (10 being best) for each of these UX categories:
- Visual Design
- Navigation Clarity
- Content Hierarchy
- Call-To-Action Visibility
- Accessibility
- Overall UX

{name1}: {desc1}

{name2}: {desc2}

Format the output as JSON:
{{
  "{name1}": {{"Visual Design": X, ...}},
  "{name2}": {{"Visual Design": Y, ...}}
}}
"""
    response = call_gemini(prompt)
    try:
        match = re.search(r'\{[\s\S]+\}', response)
        if match:
            return json.loads(match.group()), response
        else:
            return {"error": "❌ JSON block not found."}, response
    except Exception as e:
        return {"error": f"❌ Could not parse scores: {str(e)}"}, response

def split_comparison_sections(response_text):
    sections = {"Similarities": "", "Differences": "", "Suggestions": ""}
    current = None
    for line in response_text.split("\n"):
        lower = line.strip().lower()
        if "similarities" in lower:
            current = "Similarities"
        elif "differences" in lower:
            current = "Differences"
        elif "suggestions" in lower or "recommendations" in lower:
            current = "Suggestions"
        elif current:
            sections[current] += line.strip() + "\n"
    return sections

tab1, tab4, tab2, tab3 = st.tabs(["🔗 Input URLs", "📈 UX Scorecard", "📊 Layout Summary", "🤖 Gemini Comparison"])

with tab1:
    st.markdown("### 🔗 Enter Competitor URLs")
    col1, col2 = st.columns(2)
    with col1:
        url1 = st.text_input("URL for Site A", placeholder="https://example.com")
    with col2:
        url2 = st.text_input("URL for Site B", placeholder="https://example.com")

    # Space for better layout
    st.markdown("&nbsp;")
    
    analyze = st.button("🚀 Run Analysis")

    if analyze:
        if not url1 or not url2:
            st.error("Please enter both URLs to compare.")
        else:
            try:
                name1, name2 = extract_site_name(url1), extract_site_name(url2)
                with st.spinner("Fetching layout summaries..."):
                    s1 = extract_ui_summary_from_html(url1)
                    s2 = extract_ui_summary_from_html(url2)
                
                # Check if there was an error with either URL
                if "error" in s1:
                    st.error(f"Error fetching site A: {s1['error']}")
                    continue_analysis = False
                elif "error" in s2:
                    st.error(f"Error fetching site B: {s2['error']}")
                    continue_analysis = False
                else:
                    continue_analysis = True
                    
                if continue_analysis:
                    with st.spinner("Getting Gemini Comparison..."):
                        comparison = compare_with_gemini(name1, name2, s1, s2)
                    with st.spinner("Scoring UX..."):
                        scores, raw = score_with_gemini(name1, name2, s1, s2)
                    
                    # Check if a rate limit error was returned
                    if "API rate limit reached" in comparison or "API rate limit reached" in raw:
                        st.error("⚠️ API request failed. Please try again.")
                    else:
                        st.session_state.update({
                            "s1": s1,
                            "s2": s2,
                            "name1": name1,
                            "name2": name2,
                            "comparison": comparison,
                            "scores": scores,
                            "raw_score_response": raw
                        })
                        st.success("✅ Analysis complete. View all tabs.")
            except Exception as e:
                st.error(f"An error occurred: {str(e)}")

with tab4:
    st.markdown("### 📈 UX Scorecard (1–10 Ratings)")
    
    # Display rating legend
    st.markdown("""
    <div class="rating-legend">
        <span class="rating-category bad">1–4: Bad</span>
        <span class="rating-category good">5–7: Good</span>
        <span class="rating-category excellent">8–10: Excellent</span>
    </div>
    """, unsafe_allow_html=True)
    
    if "scores" in st.session_state:
        score_data = st.session_state["scores"]
        if "error" in score_data:
            st.error(score_data["error"])
            with st.expander("🔍 Raw Gemini Response"):
                st.code(st.session_state["raw_score_response"])
        else:
            df = pd.DataFrame(score_data).T
            
            # Function to color cells based on value - using specified color codes
            def color_rating(val):
                if val <= 4:
                    return 'background-color: rgba(203, 52, 56, 0.5); border: 1px solid #CB3438;'  # Red for bad
                elif val <= 7:
                    return 'background-color: rgba(217, 143, 5, 0.5); border: 1px solid #D98F05;'  # Orange for good
                else:
                    return 'background-color: rgba(95, 169, 90, 0.5); border: 1px solid #5FA95A;'  # Green for excellent
            
            # Apply styling (using .map instead of deprecated .applymap)
            styled_df = df.style.map(color_rating)
            # Still highlight max values with a border
            styled_df = styled_df.highlight_max(axis=0, props='border: 2px solid black')
            
            st.dataframe(styled_df)
            with st.expander("🔍 Raw Gemini Response"):
                st.code(st.session_state["raw_score_response"])
    else:
        st.info("Run the analysis to view UX scoring.")
    
    # Tooltips for UX parameters
    tooltips = {
        "Visual Design": "Evaluates aesthetics, color scheme, typography, and overall visual appeal of the UI.",
        "Navigation Clarity": "Measures how easily users can find their way around the site and locate key information.",
        "Content Hierarchy": "Assesses how well content is organized and prioritized to guide the user's attention.",
        "Call-To-Action Visibility": "Evaluates how clearly action buttons stand out and prompt user engagement.",
        "Accessibility": "Measures how well the site serves users with disabilities or limitations.",
        "Overall UX": "Comprehensive rating of the entire user experience combining all factors."
    }
    
    # Display parameter tooltips
    st.markdown("#### Parameter Definitions:")
    for param, tooltip in tooltips.items():
        with st.expander(f"ℹ️ {param}"):
            st.markdown(tooltip)

with tab2:
    st.markdown("### 📊 Layout Summary")
    if "s1" in st.session_state and "s2" in st.session_state:
        # Create a combined DataFrame for easy comparison
        s1 = st.session_state["s1"]
        s2 = st.session_state["s2"]
        name1 = st.session_state['name1']
        name2 = st.session_state['name2']
        
        # Create a list of all possible layout elements
        all_elements = sorted(set(list(s1.keys()) + list(s2.keys())))
        
        # Create data for the comparison table
        comparison_data = []
        for element in all_elements:
            site1_value = s1.get(element, 0)
            site2_value = s2.get(element, 0)
            comparison_data.append({
                "Element": element,
                f"🅰️ {name1}": site1_value,
                f"🅱️ {name2}": site2_value,
                "Difference": site2_value - site1_value
            })
        
        # Convert to DataFrame
        df = pd.DataFrame(comparison_data)
        
        # Function to highlight differences - using specified color codes
        def highlight_diff(val):
            if isinstance(val, int) and val > 0:
                return 'background-color: rgba(95, 169, 90, 0.5); border: 1px solid #5FA95A;'  # Green for positive
            elif isinstance(val, int) and val < 0:
                return 'background-color: rgba(203, 52, 56, 0.5); border: 1px solid #CB3438;'  # Red for negative
            return ''
        
        # Apply styling
        styled_df = df.style.map(highlight_diff, subset=['Difference'])
        
        # Display the comparison table
        st.dataframe(styled_df)
        
        # Show raw JSON data in expandable sections
        with st.expander(f"🔍 View Raw JSON Data"):
            col1, col2 = st.columns(2)
            with col1:
                st.markdown(f"#### 🅰️ {name1}")
                st.json(s1)
            with col2:
                st.markdown(f"#### 🅱️ {name2}")
                st.json(s2)
            
        # Layout element definitions
        layout_tooltips = {
            "Navbars": "Navigation bars containing site links and menus",
            "Forms": "Input forms for user data submission",
            "Buttons/Links": "Interactive elements for user actions and navigation",
            "Inputs": "Form fields, search boxes, and other input elements",
            "Headers (H1–H6)": "Heading elements used for content hierarchy",
            "Sections": "Distinct content blocks or page segments"
        }
        
        st.markdown("#### Element Definitions:")
        for element, definition in layout_tooltips.items():
            with st.expander(f"ℹ️ {element}"):
                st.markdown(definition)
    else:
        st.info("Run the analysis first from the **Input URLs** tab.")

with tab3:
    st.markdown("### 🤖 Gemini-Powered Comparison")
    if "comparison" in st.session_state:
        structured = split_comparison_sections(st.session_state["comparison"])
        
        # Create tabs for similarities, differences and suggestions
        comparison_tabs = st.tabs(["🔹 KEY SIMILARITIES", "🔸 KEY DIFFERENCES", "💡 UX IMPROVEMENT SUGGESTIONS"])
        
        # Display similarities tab with enhanced formatting
        with comparison_tabs[0]:
            if structured["Similarities"]:
                # Process and display each bullet point
                similarities = structured["Similarities"].split("\n")
                for point in similarities:
                    if point.strip():
                        if not point.strip().startswith("•") and not point.strip().startswith("-"):
                            point = "• " + point
                        st.markdown(point)
            else:
                st.markdown("_No similarities detected._")
            
        # Display differences tab with enhanced formatting
        with comparison_tabs[1]:
            if structured["Differences"]:
                # Process and display each bullet point
                differences = structured["Differences"].split("\n")
                for point in differences:
                    if point.strip():
                        if not point.strip().startswith("•") and not point.strip().startswith("-"):
                            point = "• " + point
                        st.markdown(point)
            else:
                st.markdown("_No differences detected._")
            
        # Display suggestions in the third tab
        with comparison_tabs[2]:
            if structured["Suggestions"]:
                # Add tabs for site-specific suggestions if available
                if "{" in structured["Suggestions"] or "}" in structured["Suggestions"] or ":" in structured["Suggestions"]:
                    # Try to separate site-specific suggestions
                    name1 = st.session_state.get('name1', 'Site A')
                    name2 = st.session_state.get('name2', 'Site B')
                    site_tabs = st.tabs([f"🅰️ {name1}", f"🅱️ {name2}", "🔄 General"])
                    
                    with site_tabs[0]:
                        found = False
                        for line in structured["Suggestions"].split("\n"):
                            if name1 in line or "Site A" in line or "site a" in line or "First site" in line.lower():
                                found = True
                                st.markdown(line)
                        if not found:
                            st.markdown("_No specific suggestions for this site._")
                    
                    with site_tabs[1]:
                        found = False
                        for line in structured["Suggestions"].split("\n"):
                            if name2 in line or "Site B" in line or "site b" in line or "Second site" in line.lower():
                                found = True
                                st.markdown(line)
                        if not found:
                            st.markdown("_No specific suggestions for this site._")
                    
                    with site_tabs[2]:
                        found = False
                        for line in structured["Suggestions"].split("\n"):
                            if not (name1 in line or name2 in line or "Site A" in line or "Site B" in line or "site a" in line or "site b" in line):
                                if line.strip():
                                    found = True
                                    st.markdown(line)
                        if not found:
                            st.markdown("_No general suggestions provided._")
                else:
                    # Process and display each bullet point
                    suggestions = structured["Suggestions"].split("\n")
                    for point in suggestions:
                        if point.strip():
                            if not point.strip().startswith("•") and not point.strip().startswith("-"):
                                point = "• " + point
                            st.markdown(point)
            else:
                st.markdown("_No suggestions provided._")
        
        # Show the raw response in an expander
        with st.expander("🔍 View Raw Gemini Response"):
            st.code(st.session_state["comparison"])
    else:
        st.info("Run the analysis first to view comparison.")
