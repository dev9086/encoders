import streamlit as st
import json
import os
import numpy as np
from sklearn.metrics.pairwise import cosine_similarity
import re
from datetime import datetime, date, timedelta
import pandas as pd
from PIL import Image
import plotly.express as px
import plotly.graph_objects as go
import random

# Configuration
st.set_page_config(
    page_title="HackMate - CYHI Quick Teams",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for better styling
st.markdown("""
<style>
    .main-header {
        background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
        padding: 2rem 1rem;
        border-radius: 10px;
        color: white;
        text-align: center;
        margin-bottom: 2rem;
    }
    .profile-card {
        background: #1a1a2e;
        padding: 1.5rem;
        border-radius: 15px;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.3);
        border-left: 5px solid #667eea;
        margin: 1rem 0;
        color: white;
    }
    .team-card {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 1.5rem;
        border-radius: 15px;
        color: white;
        margin: 1rem 0;
        position: relative;
        overflow: hidden;
    }
    .team-card::before {
        content: '';
        position: absolute;
        top: -50%;
        left: -50%;
        width: 200%;
        height: 200%;
        background: radial-gradient(circle, rgba(255,255,255,0.1) 0%, transparent 70%);
        animation: pulse 3s ease-in-out infinite;
    }
    @keyframes pulse {
        0%, 100% { transform: scale(1); opacity: 0.5; }
        50% { transform: scale(1.1); opacity: 0.8; }
    }
    .quick-match-card {
        background: linear-gradient(45deg, #ff6b6b, #feca57);
        padding: 1rem;
        border-radius: 10px;
        color: white;
        text-align: center;
        margin: 0.5rem 0;
    }
    .skill-badge {
        display: inline-block;
        background: #667eea;
        color: white;
        padding: 0.3rem 0.8rem;
        border-radius: 20px;
        margin: 0.2rem;
        font-size: 0.8rem;
    }
    .urgent-badge {
        background: #ff4757 !important;
        animation: blink 1s infinite;
    }
    @keyframes blink {
        0%, 50% { opacity: 1; }
        51%, 100% { opacity: 0.5; }
    }
    .metric-card {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 1rem;
        border-radius: 10px;
        color: white;
        text-align: center;
    }
    .score-badge {
        display: inline-block;
        padding: 0.5rem 1rem;
        border-radius: 20px;
        color: white;
        font-weight: bold;
        margin: 0.2rem;
        font-size: 0.9rem;
    }
    .score-excellent { background: #2ecc71; }
    .score-good { background: #f39c12; }
    .score-average { background: #e67e22; }
    .score-poor { background: #e74c3c; }
    .single-score-card {
        background: #2c2c54;
        border: 2px solid #667eea;
        border-radius: 15px;
        padding: 1rem;
        margin: 0.5rem 0;
        color: white;
        text-align: center;
    }
    .stButton > button {
        background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
        color: white;
        border-radius: 25px;
        border: none;
        padding: 0.5rem 2rem;
        font-weight: bold;
        transition: all 0.3s;
    }
    .stButton > button:hover {
        transform: translateY(-2px);
        box-shadow: 0 4px 8px rgba(0,0,0,0.2);
    }
    /* Remove white backgrounds globally */
    .stApp {
        background-color: #0f0f1a;
    }
    .main .block-container {
        background-color: transparent;
    }
    div[data-testid="stVerticalBlock"] > div {
        background-color: transparent;
    }
    .element-container {
        background-color: transparent;
    }
    .pending-request {
        background: linear-gradient(45deg, #ff9a3c, #ff6b6b) !important;
        border-left: 5px solid #ff9a3c;
    }
    .accepted-request {
        background: linear-gradient(45deg, #2ecc71, #27ae60) !important;
        border-left: 5px solid #2ecc71;
    }
    .rejected-request {
        background: linear-gradient(45deg, #e74c3c, #c0392b) !important;
        border-left: 5px solid #e74c3c;
    }
</style>
""", unsafe_allow_html=True)

# File paths
CATEGORIES_FILE = 'categories.json'
USERS_FILE = 'users.json'
TEAMS_FILE = 'teams.json'
QUICK_TEAMS_FILE = 'quick_teams.json'
HACKATHONS_FILE = 'hackathons.json'
TEAM_REQUESTS_FILE = 'team_requests.json'
UPLOAD_DIR = 'achievement_uploads'

# Create upload directory if it doesn't exist
if not os.path.exists(UPLOAD_DIR):
    os.makedirs(UPLOAD_DIR)

# Initialize session state
if 'show_instant_match' not in st.session_state:
    st.session_state['show_instant_match'] = False
if 'show_create_team' not in st.session_state:
    st.session_state['show_create_team'] = False
if 'selected_team' not in st.session_state:
    st.session_state['selected_team'] = None

def load_json(file_path):
    """Load JSON data from file with error handling"""
    try:
        if os.path.exists(file_path):
            with open(file_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        else:
            return {}
    except Exception as e:
        st.error(f"Error loading {file_path}: {str(e)}")
        return {}

def save_json(file_path, data):
    """Save JSON data to file with error handling"""
    try:
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=4, ensure_ascii=False)
    except Exception as e:
        st.error(f"Error saving {file_path}: {str(e)}")

def add_user_profile(profile):
    """Add user profile to the database"""
    users = load_json(USERS_FILE)
    users[profile['name']] = profile
    save_json(USERS_FILE, users)

def get_all_users():
    """Get all user profiles"""
    users = load_json(USERS_FILE)
    return list(users.values())

def save_team(team_data):
    """Save team data"""
    teams = load_json(TEAMS_FILE)
    team_id = f"team_{len(teams) + 1}_{datetime.now().strftime('%Y%m%d%H%M%S')}"
    teams[team_id] = team_data
    save_json(TEAMS_FILE, teams)
    return team_id

def get_all_teams():
    """Get all teams"""
    teams = load_json(TEAMS_FILE)
    return list(teams.values())

def save_quick_team(quick_team_data):
    """Save quick team data"""
    quick_teams = load_json(QUICK_TEAMS_FILE)
    team_id = f"quick_{len(quick_teams) + 1}_{datetime.now().strftime('%Y%m%d%H%M%S')}"
    quick_teams[team_id] = quick_team_data
    save_json(QUICK_TEAMS_FILE, quick_teams)
    return team_id

def get_quick_teams():
    """Get all quick teams"""
    quick_teams = load_json(QUICK_TEAMS_FILE)
    return list(quick_teams.values())

def get_team_requests():
    """Get all team requests"""
    return load_json(TEAM_REQUESTS_FILE)

def save_team_request(request_data):
    """Save a team request"""
    requests = get_team_requests()
    request_id = f"request_{len(requests) + 1}_{datetime.now().strftime('%Y%m%d%H%M%S')}"
    requests[request_id] = request_data
    save_json(TEAM_REQUESTS_FILE, requests)
    return request_id

def update_team_request(request_id, updates):
    """Update a team request"""
    requests = get_team_requests()
    if request_id in requests:
        requests[request_id].update(updates)
        save_json(TEAM_REQUESTS_FILE, requests)
        return True
    return False

def get_user_team_requests(username):
    """Get all team requests for a specific user"""
    requests = get_team_requests()
    user_requests = []
    
    for req_id, req_data in requests.items():
        if req_data.get('to_user') == username or req_data.get('from_user') == username:
            user_requests.append((req_id, req_data))
    
    return user_requests

def get_team_by_id(team_id):
    """Get a specific team by ID"""
    teams = load_json(TEAMS_FILE)
    return teams.get(team_id)

def update_team(team_id, updates):
    """Update a team"""
    teams = load_json(TEAMS_FILE)
    if team_id in teams:
        teams[team_id].update(updates)
        save_json(TEAMS_FILE, teams)
        return True
    return False

# ML Skillset Enhancer Functions
def vectorize_profiles(profiles, all_skills):
    """Convert profiles to vector representation based on skills"""
    matrix = []
    for p in profiles:
        skills_lower = [s.lower() for s in p.get('skills', [])]
        row = [1 if skill in skills_lower else 0 for skill in all_skills]
        matrix.append(row)
    return np.array(matrix)

def find_best_matches(user_profile, profiles, top_k=5):
    """Find best matches using cosine similarity"""
    all_skills = set()
    for p in profiles:
        all_skills.update([s.lower() for s in p.get('skills', [])])
    all_skills.update([s.lower() for s in user_profile.get('skills', [])])
    all_skills = sorted(list(all_skills))

    if not all_skills:
        return []

    try:
        matrix = vectorize_profiles(profiles, all_skills)
        user_vec = np.array([[1 if s in [sk.lower() for sk in user_profile.get('skills', [])] else 0 for s in all_skills]])

        if matrix.size > 0 and user_vec.size > 0:
            sims = cosine_similarity(user_vec, matrix)[0]
            idx_sim = sorted([(i, s) for i, s in enumerate(sims) if s < 0.999], key=lambda x: x[1], reverse=True)[:top_k]

            user_avail = set(user_profile.get('availability', []))
            matches = []
            for idx, sim in idx_sim:
                if idx < len(profiles):
                    candidate = profiles[idx]
                    cand_avail = set(candidate.get('availability', []))
                    # Check overlapping availability
                    if user_avail and cand_avail and user_avail.isdisjoint(cand_avail):
                        continue
                    matches.append((candidate, sim))
            return matches
    except Exception as e:
        st.error(f"Error in finding matches: {str(e)}")
        return []
    
    return []

def analyze_fit(cat_sel, dom_sel, selected_skills, categories):
    """Analyze skill fit for a specific domain"""
    if not categories or cat_sel not in categories or dom_sel not in categories[cat_sel]['domains']:
        return None

    domain_skills = set(s.lower() for s in categories[cat_sel]['domains'][dom_sel])
    user_skills = set(s.lower() for s in selected_skills)

    matched = user_skills.intersection(domain_skills)
    missing = domain_skills.difference(user_skills)

    max_score = max(len(domain_skills), 10)
    score = min(100, (len(matched) / max_score) * 100) if max_score > 0 else 0

    if score >= 80:
        rec = "Excellent fit! Strong skills for this role."
    elif score >= 60:
        rec = f"Good fit; consider improving missing skills: {', '.join(list(missing)[:3])}"
    elif score >= 40:
        rec = f"Moderate fit; focus on acquiring key skills: {', '.join(list(missing)[:3])}"
    else:
        rec = f"Low fit; strongly recommend gaining these skills: {', '.join(list(missing)[:3])}"

    return {
        "score": score,
        "matched": matched,
        "missing": missing,
        "recommendation": rec,
    }

def calculate_domain_scores(user_profile, categories):
    """Calculate domain match scores for a user"""
    user_skills = set(skill.lower() for skill in user_profile.get('skills', []))
    domain_scores = {}
    
    for cat, cat_info in categories.items():
        for domain, skills in cat_info.get("domains", {}).items():
            domain_skills = set(skill.lower() for skill in skills)
            if domain_skills:
                matched = user_skills.intersection(domain_skills)
                score = (len(matched) / len(domain_skills)) * 100
                domain_scores[domain] = {
                    'score': score,
                    'matched': matched,
                    'missing': domain_skills - user_skills,
                    'category': cat
                }
    
    return domain_scores

def get_score_class(score):
    """Get CSS class for score badge"""
    if score >= 80:
        return "score-excellent"
    elif score >= 60:
        return "score-good"
    elif score >= 40:
        return "score-average"
    else:
        return "score-poor"

def get_score_label(score):
    """Get label for score"""
    if score >= 80:
        return "Excellent"
    elif score >= 60:
        return "Good"
    elif score >= 40:
        return "Average"
    else:
        return "Needs Work"

def display_profile_card_with_scores(user, categories, show_scores=True, role=None):
    """Display a profile card with single domain score"""
    with st.container():
        role_emoji = {"Team Lead": "👑", "Tech Lead": "🚀", "Designer": "🎨", "Backend Dev": "⚙", 
                     "Frontend Dev": "💻", "Data Specialist": "📊", "Business Analyst": "📈"}.get(role, "👤")
        
        col1, col2 = st.columns([3, 1])
        
        with col1:
            st.markdown(f"""
            <div class="profile-card">
                <h3>{role_emoji} {user['name']} {f"({role})" if role else ""}</h3>
                <p><strong>📝 Bio:</strong> {user.get('bio', 'Ready to hack!')[:100]}...</p>
                <p><strong>🎯 Domain:</strong> {', '.join(user.get('domain', ['General']))}</p>
                <p><strong>📈 Experience:</strong> {user.get('experience_level', 'Intermediate')}</p>
                <p><strong>⏰ Availability:</strong> {', '.join(user.get('availability', ['Flexible']))}</p>
            </div>
            """, unsafe_allow_html=True)
            
            # Skills as badges
            if user.get('skills'):
                skills_html = ""
                for skill in user['skills'][:8]:  # Limit to 8 skills for display
                    skills_html += f'<span class="skill-badge">{skill}</span>'
                if len(user['skills']) > 8:
                    skills_html += f'<span class="skill-badge">+{len(user["skills"]) - 8} more</span>'
                st.markdown(skills_html, unsafe_allow_html=True)
        
        with col2:
            if show_scores and categories:
                domain_scores = calculate_domain_scores(user, categories)
                
                if domain_scores:
                    # Get the highest scoring domain only
                    best_domain, best_data = max(domain_scores.items(), key=lambda x: x[1]['score'])
                    score = best_data['score']
                    score_class = get_score_class(score)
                    score_label = get_score_label(score)
                    
                    st.markdown(f"""
                    <div class="single-score-card">
                        <h4>🎯 Best Match</h4>
                        <strong>{best_domain}</strong><br>
                        <span class="score-badge {score_class}">{score:.0f}% - {score_label}</span>
                    </div>
                    """, unsafe_allow_html=True)

def create_instant_team_match(user_profile, hackathon_context=None):
    """Create instant team matches based on complementary skills and hackathon needs"""
    users = get_all_users()
    
    if len(users) < 2:
        return None
    
    user_skills = set(s.lower() for s in user_profile.get('skills', []))
    matches = []
    
    for candidate in users:
        if candidate['name'] == user_profile['name']:
            continue
            
        candidate_skills = set(s.lower() for s in candidate.get('skills', []))
        
        # Calculate complementary score (different skills are better for teams)
        complement_score = len(user_skills.symmetric_difference(candidate_skills))
        overlap_penalty = len(user_skills.intersection(candidate_skills)) * 0.5
        
        # Availability match
        user_avail = set(user_profile.get('availability', []))
        cand_avail = set(candidate.get('availability', []))
        avail_score = len(user_avail.intersection(cand_avail)) if user_avail and cand_avail else 0.5
        
        # Experience diversity bonus
        exp_levels = {"Beginner": 1, "Intermediate": 2, "Advanced": 3, "Expert": 4}
        user_exp = exp_levels.get(user_profile.get('experience_level', 'Intermediate'), 2)
        cand_exp = exp_levels.get(candidate.get('experience_level', 'Intermediate'), 2)
        exp_diversity = abs(user_exp - cand_exp) * 0.3  # Reward diversity
        
        total_score = complement_score + avail_score * 2 + exp_diversity - overlap_penalty
        
        if total_score > 0:
            matches.append((candidate, total_score))
    
    matches.sort(key=lambda x: x[1], reverse=True)
    return matches[:3]  # Return top 3 matches

def generate_team_roles(team_members, hackathon_theme=None):
    """Generate optimal role assignments for team members"""
    roles = {
        'Team Lead': {'skills': ['leadership', 'project management', 'communication'], 'assigned': None},
        'Tech Lead': {'skills': ['programming', 'software development', 'architecture'], 'assigned': None},
        'Designer': {'skills': ['ui/ux', 'design', 'figma', 'adobe', 'graphics'], 'assigned': None},
        'Backend Dev': {'skills': ['python', 'java', 'node.js', 'database', 'api'], 'assigned': None},
        'Frontend Dev': {'skills': ['react', 'javascript', 'html', 'css', 'vue'], 'assigned': None},
        'Data Specialist': {'skills': ['data science', 'machine learning', 'analytics', 'sql'], 'assigned': None},
        'Business Analyst': {'skills': ['business', 'strategy', 'marketing', 'finance'], 'assigned': None}
    }
    
    # Score each member for each role
    for role, role_info in roles.items():
        best_score = 0
        best_member = None
        
        for member in team_members:
            member_skills = [s.lower() for s in member.get('skills', [])]
            score = sum(1 for skill in role_info['skills'] if any(skill in ms for ms in member_skills))
            
            # Bonus for experience level
            exp_bonus = {'Expert': 3, 'Advanced': 2, 'Intermediate': 1, 'Beginner': 0.5}
            score += exp_bonus.get(member.get('experience_level', 'Intermediate'), 1)
            
            if score > best_score:
                best_score = score
                best_member = member
        
        if best_member:
            roles[role]['assigned'] = best_member['name']
            roles[role]['score'] = best_score
    
    return roles

def calculate_team_compatibility(members):
    """Calculate overall team compatibility score"""
    if len(members) < 2:
        return 0
    
    # Skill diversity score
    all_skills = set()
    for member in members:
        all_skills.update(s.lower() for s in member.get('skills', []))
    
    total_skills = sum(len(member.get('skills', [])) for member in members)
    skill_diversity = len(all_skills) / (total_skills + 1) if total_skills > 0 else 0
    
    # Experience level balance
    exp_levels = [member.get('experience_level', 'Intermediate') for member in members]
    exp_variety = len(set(exp_levels)) / len(exp_levels) if exp_levels else 0
    
    # Availability overlap
    avail_sets = [set(member.get('availability', [])) for member in members if member.get('availability')]
    if avail_sets:
        common_avail = set.intersection(*avail_sets) if len(avail_sets) > 1 else avail_sets[0]
        avail_score = len(common_avail) / 5  # Assuming max 5 availability options
    else:
        avail_score = 0.5
    
    # Domain diversity
    domains = set()
    for member in members:
        domains.update(member.get('domain', []))
    domain_diversity = len(domains) / len(members) if members else 0
    
    total_score = (skill_diversity * 0.4 + exp_variety * 0.2 + avail_score * 0.2 + domain_diversity * 0.2) * 100
    return min(100, total_score)

def show_browse_users_with_ml():
    """Enhanced user browsing with ML-powered domain scoring - FIXED VERSION"""
    st.markdown("## 👥 Browse Hackers with Smart Matching")
    
    users = get_all_users()
    categories = load_json(CATEGORIES_FILE)
    
    if not users:
        st.info("No users registered yet. Be the first!")
        return
    
    # Enhanced filters with ML features
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        available_now = st.checkbox("⚡ Available Now", help="Show only users available for immediate team formation")
    
    with col2:
        experience_filter = st.selectbox("📈 Min Experience", ["Any", "Beginner", "Intermediate", "Advanced", "Expert"])
    
    with col3:
        all_domains = set()
        for user in users:
            all_domains.update(user.get('domain', []))
        domain_filter = st.selectbox("🎯 Domain Filter", ["Any"] + sorted(list(all_domains)))
    
    with col4:
        min_domain_score = st.slider("🎯 Min Domain Score", 0, 100, 0, help="Minimum domain match score")
    
    # Domain-based matching
    search_domain = ""
    if categories:
        st.markdown("### 🤖 Domain-Based Smart Search")
        col1, col2 = st.columns(2)
        
        with col1:
            search_category = st.selectbox("Search by Category", [""] + list(categories.keys()))
        
        with col2:
            if search_category:
                domain_options = list(categories[search_category].get("domains", {}).keys())
                search_domain = st.selectbox("Search by Domain", [""] + domain_options)
    
    # Apply filters
    filtered_users = users.copy()
    
    if available_now:
        filtered_users = [u for u in filtered_users if 'Flexible' in u.get('availability', []) or 'Right Now' in u.get('availability', [])]
    
    if experience_filter != "Any":
        filtered_users = [u for u in filtered_users if u.get('experience_level') == experience_filter]
    
    if domain_filter != "Any":
        filtered_users = [u for u in filtered_users if domain_filter in u.get('domain', [])]
    
    # Filter by domain score if ML search is active
    if categories and search_domain and min_domain_score > 0:
        scored_users = []
        for user in filtered_users:
            domain_scores = calculate_domain_scores(user, categories)
            if search_domain in domain_scores and domain_scores[search_domain]['score'] >= min_domain_score:
                scored_users.append((user, domain_scores[search_domain]['score']))
        
        # Sort by domain score
        scored_users.sort(key=lambda x: x[1], reverse=True)
        filtered_users = [user for user, score in scored_users]
    
    # Display results
    st.markdown(f"### 👥 {len(filtered_users)} Hackers Found")
    
    if search_domain and categories:
        st.info(f"🎯 Showing users ranked by {search_domain} domain expertise")
    
    for i, user in enumerate(filtered_users):
        col1, col2 = st.columns([4, 1])
        
        with col1:
            # Show domain score for searched domain only if searching
            if search_domain and categories:
                domain_scores = calculate_domain_scores(user, categories)
                if search_domain in domain_scores:
                    score = domain_scores[search_domain]['score']
                    score_class = get_score_class(score)
                    score_label = get_score_label(score)
                    st.markdown(f"""
                    <div style="margin-bottom: 1rem;">
                        <strong>🎯 {search_domain} Match:</strong>
                        <span class="score-badge {score_class}">{score:.0f}% - {score_label}</span>
                    </div>
                    """, unsafe_allow_html=True)
            
            display_profile_card_with_scores(user, categories, show_scores=True)
        
        with col2:
            st.markdown("<br><br>", unsafe_allow_html=True)
            if st.button(f"⚡ Quick Team", key=f"qt_{user['name']}_{i}", help="Form instant team with this user"):
                # Simulate quick team formation
                matches = create_instant_team_match(user)
                if matches:
                    st.success(f"✅ Team formed with {user['name']}!")
                    # Store the team formation
                    team_data = {
                        'name': f"QuickTeam_{datetime.now().strftime('%H%M%S')}",
                        'members': [user] + [match[0] for match in matches[:2]],
                        'formation_time': datetime.now().strftime('%H:%M:%S'),
                        'compatibility': calculate_team_compatibility([user] + [match[0] for match in matches[:2]]),
                        'type': 'instant_match'
                    }
                    save_quick_team(team_data)
                else:
                    st.warning("No immediate matches found")
            
            if st.button(f"💬 Contact", key=f"contact_{user['name']}_{i}"):
                st.info(f"Contact request sent to {user['name']}")
            
            if st.button(f"📊 View All Scores", key=f"scores_{user['name']}_{i}", help="View detailed domain scores"):
                with st.expander(f"{user['name']}'s All Domain Scores", expanded=True):
                    if categories:
                        domain_scores = calculate_domain_scores(user, categories)
                        
                        if domain_scores:
                            # Show top 5 domains only
                            sorted_domains = sorted(domain_scores.items(), key=lambda x: x[1]['score'], reverse=True)[:5]
                            
                            for domain, data in sorted_domains:
                                score = data['score']
                                score_class = get_score_class(score)
                                score_label = get_score_label(score)
                                
                                st.markdown(f"""
                                <div style="background: #2c2c54; padding: 0.8rem; border-radius: 10px; margin: 0.3rem 0; color: white;">
                                    <strong>{domain}</strong> ({data['category']})<br>
                                    <span class="score-badge {score_class}">{score:.0f}% - {score_label}</span>
                                    <br><small>{len(data['matched'])} matched skills, {len(data['missing'])} missing</small>
                                </div>
                                """, unsafe_allow_html=True)

def show_group_management():
    """Manage groups and categories"""
    st.markdown("## 🏢 Group & Category Management")
    
    categories = load_json(CATEGORIES_FILE)
    if not categories:
        categories = {}
    
    tab1, tab2 = st.tabs(["📋 View Groups", "➕ Add New Group"])
    
    with tab1:
        st.markdown("### Existing Groups & Categories")
        
        if not categories:
            st.info("No groups created yet. Add some groups to get started!")
        else:
            for category, cat_info in categories.items():
                with st.expander(f"📁 {category}"):
                    if "domains" in cat_info:
                        for domain, skills in cat_info["domains"].items():
                            st.markdown(f"**{domain}**")
                            st.write(f"Skills: {', '.join(skills)}")
                            if st.button(f"Delete {domain}", key=f"del_{category}_{domain}"):
                                if category in categories and domain in categories[category]["domains"]:
                                    del categories[category]["domains"][domain]
                                    if not categories[category]["domains"]:
                                        del categories[category]
                                    save_json(CATEGORIES_FILE, categories)
                                    st.success(f"Deleted {domain} from {category}")
                                    st.rerun()
    
    with tab2:
        st.markdown("### Add New Group or Category")
        
        with st.form("group_form"):
            new_cat = st.text_input("New Group Type (Category)", max_chars=50)
            new_dom = st.text_input("New Domain/Subgroup", max_chars=50)
            new_sk = st.text_area("Skills (comma separated)")
            subm = st.form_submit_button("Add Group")
            
            if subm:
                if not (new_cat and new_dom):
                    st.warning("Category and domain are required.")
                else:
                    new_cat = new_cat.strip()
                    new_dom = new_dom.strip()
                    sk_list = [s.strip() for s in new_sk.split(",") if s.strip()]
                    
                    if new_cat not in categories:
                        categories[new_cat] = {"domains": {}}
                    
                    if new_dom in categories[new_cat]["domains"]:
                        st.warning(f"Domain '{new_dom}' already exists in '{new_cat}'.")
                    else:
                        categories[new_cat]["domains"][new_dom] = sk_list
                        save_json(CATEGORIES_FILE, categories)
                        st.success(f"Added '{new_dom}' under '{new_cat}'.")

def show_create_team_form():
    """Form to create a new team"""
    st.markdown("## 🚀 Create a New Team")
    
    users = get_all_users()
    if not users:
        st.warning("No users available to form a team. Create profiles first!")
        return
    
    with st.form("create_team_form"):
        team_name = st.text_input("Team Name", placeholder="Awesome Hackers Team")
        team_description = st.text_area("Team Description", placeholder="What's your team's mission?")
        
        col1, col2 = st.columns(2)
        with col1:
            target_size = st.slider("Target Team Size", 2, 8, 4)
            focus_area = st.selectbox("Primary Focus Area", 
                                    ["Web Development", "Mobile App", "AI/ML", "Data Science", 
                                     "IoT", "Blockchain", "Game Development", "Open Choice"])
        with col2:
            project_type = st.selectbox("Project Type", 
                                      ["New Idea", "Existing Project", "Open Source Contribution", "Research"])
            hackathon_name = st.text_input("Hackathon Name (if applicable)", placeholder="e.g., Hack the North")
        
        # Team members selection
        st.markdown("### 👥 Select Team Members")
        available_members = [user for user in users]
        selected_members = st.multiselect("Choose team members", 
                                         [user['name'] for user in available_members],
                                         help="Select other hackers to join your team")
        
        # Privacy settings
        st.markdown("### 🔒 Team Privacy")
        col1, col2 = st.columns(2)
        with col1:
            team_privacy = st.selectbox("Team Visibility", 
                                      ["Public - Anyone can join", 
                                       "Private - Approval required", 
                                       "Invite only"])
        with col2:
            application_required = st.checkbox("Require application", value=True)
        
        submitted = st.form_submit_button("🚀 Create Team", use_container_width=True)
        
        if submitted:
            if not team_name:
                st.error("Team name is required!")
                return
            
            if not selected_members:
                st.error("Please select at least one team member!")
                return
            
            # Get full user objects for selected members
            team_members = []
            for member_name in selected_members:
                member = next((u for u in users if u['name'] == member_name), None)
                if member:
                    team_members.append(member)
            
            # Create team data
            team_data = {
                'name': team_name,
                'description': team_description,
                'members': team_members,
                'target_size': target_size,
                'focus_area': focus_area,
                'project_type': project_type,
                'hackathon_name': hackathon_name,
                'privacy': team_privacy,
                'application_required': application_required,
                'created_date': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                'status': 'active',
                'compatibility': calculate_team_compatibility(team_members)
            }
            
            # Save team
            team_id = save_team(team_data)
            st.success(f"✅ Team '{team_name}' created successfully!")
            
            # Send join requests to selected members if private team
            if team_privacy != "Public - Anyone can join":
                for member in team_members:
                    request_data = {
                        'team_id': team_id,
                        'team_name': team_name,
                        'from_user': "System",  # Or the creator's name if available
                        'to_user': member['name'],
                        'status': 'pending',
                        'message': f"You've been invited to join {team_name}",
                        'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    }
                    save_team_request(request_data)
                
                st.info("📨 Join requests sent to selected members!")
            
            st.session_state['show_create_team'] = False

def show_team_requests(username):
    """Show team requests for a user"""
    st.markdown("## 📨 Team Requests")
    
    user_requests = get_user_team_requests(username)
    if not user_requests:
        st.info("You don't have any team requests yet.")
        return
    
    pending_requests = [(req_id, req) for req_id, req in user_requests if req.get('status') == 'pending']
    accepted_requests = [(req_id, req) for req_id, req in user_requests if req.get('status') == 'accepted']
    rejected_requests = [(req_id, req) for req_id, req in user_requests if req.get('status') == 'rejected']
    
    if pending_requests:
        st.markdown("### ⏳ Pending Requests")
        for req_id, request in pending_requests:
            status_class = "pending-request"
            st.markdown(f"""
            <div class="profile-card {status_class}">
                <h3>👥 {request.get('team_name', 'Unknown Team')}</h3>
                <p><strong>From:</strong> {request.get('from_user', 'Unknown')}</p>
                <p><strong>Message:</strong> {request.get('message', 'No message')}</p>
                <p><strong>Date:</strong> {request.get('timestamp', 'Unknown')}</p>
            </div>
            """, unsafe_allow_html=True)
            
            col1, col2 = st.columns(2)
            with col1:
                if st.button(f"✅ Accept", key=f"accept_{req_id}"):
                    update_team_request(req_id, {'status': 'accepted'})
                    st.success("Request accepted!")
                    st.rerun()
            with col2:
                if st.button(f"❌ Reject", key=f"reject_{req_id}"):
                    update_team_request(req_id, {'status': 'rejected'})
                    st.info("Request rejected.")
                    st.rerun()
    
    if accepted_requests:
        st.markdown("### ✅ Accepted Requests")
        for req_id, request in accepted_requests:
            status_class = "accepted-request"
            st.markdown(f"""
            <div class="profile-card {status_class}">
                <h3>👥 {request.get('team_name', 'Unknown Team')}</h3>
                <p><strong>From:</strong> {request.get('from_user', 'Unknown')}</p>
                <p><strong>Status:</strong> Accepted</p>
                <p><strong>Date:</strong> {request.get('timestamp', 'Unknown')}</p>
            </div>
            """, unsafe_allow_html=True)
    
    if rejected_requests:
        st.markdown("### ❌ Rejected Requests")
        for req_id, request in rejected_requests:
            status_class = "rejected-request"
            st.markdown(f"""
            <div class="profile-card {status_class}">
                <h3>👥 {request.get('team_name', 'Unknown Team')}</h3>
                <p><strong>From:</strong> {request.get('from_user', 'Unknown')}</p>
                <p><strong>Status:</strong> Rejected</p>
                <p><strong>Date:</strong> {request.get('timestamp', 'Unknown')}</p>
            </div>
            """, unsafe_allow_html=True)

def main():
    # Header with CYHI branding
    st.markdown("""
    <div class="main-header">
        <h1>⚡ HackMate - CYHI Quick Teams</h1>
        <p>Capture Your Hackathon Idea & Find Your Perfect Team in Minutes!</p>
    </div>
    """, unsafe_allow_html=True)

    # Load or create sample data
    categories = load_json(CATEGORIES_FILE)
    if not categories:
        categories = create_sample_categories()

    # Navigation
    st.sidebar.markdown("## ⚡ Quick Actions")
    
    if st.sidebar.button("🚀 INSTANT TEAM MATCH", help="Get matched with a team in under 60 seconds!"):
        st.session_state['show_instant_match'] = True
    
    st.sidebar.markdown("---")
    st.sidebar.markdown("## 🧭 Navigation")
    
    page = st.sidebar.radio("Choose your action:", 
                           ["🏠 Home", "⚡ Quick Teams", "👤 Create Profile", "🔍 Find/Create Teams", 
                            "📊 Team Analytics", "👥 Smart Browse", "🏢 Group Management", "📨 My Requests"])

    if page == "🏠 Home":
        show_home_page()
    elif page == "⚡ Quick Teams":
        show_quick_teams_page()
    elif page == "👤 Create Profile":
        show_create_profile_page(categories)
    elif page == "🔍 Find Teams":
        show_find_teams_page()
    elif page == "📊 Team Analytics":
        show_team_analytics_page()
    elif page == "👥 Smart Browse":
        show_browse_users_with_ml()
    elif page == "🏢 Group Management":
        show_group_management()
    elif page == "📨 My Requests":
        # Get current user (for demo, using first user)
        users = get_all_users()
        if users:
            show_team_requests(users[0]['name'])
        else:
            st.info("No users found. Create a profile first!")
    
    # Handle instant team matching
    if st.session_state.get('show_instant_match', False):
        show_instant_team_match()

def show_home_page():
    """Enhanced home page with quick team stats"""
    col1, col2, col3, col4 = st.columns(4)
    
    users = get_all_users()
    teams = get_all_teams()
    quick_teams = get_quick_teams()
    
    with col1:
        st.markdown(f"""
        <div class="metric-card">
            <h2>👥</h2>
            <h3>{len(users)}</h3>
            <p>Active Hackers</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown(f"""
        <div class="metric-card">
            <h2>⚡</h2>
            <h3>{len(quick_teams)}</h3>
            <p>Quick Teams Formed</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col3:
        avg_team_time = "< 2 min"
        st.markdown(f"""
        <div class="metric-card">
            <h2>⏱</h2>
            <h3>{avg_team_time}</h3>
            <p>Avg Team Formation</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col4:
        success_rate = 71
        st.markdown(f"""
        <div class="metric-card">
            <h2>🎯</h2>
            <h3>{success_rate}%</h3>
            <p>Match Success Rate</p>
        </div>
        """, unsafe_allow_html=True)
    
    st.markdown("---")
    
    # Quick team formation CTA
    st.markdown("""
    ## 🚀 Ready to Form a Team in Under 2 Minutes?
    
    *CYHI Quick Teams* uses advanced matching algorithms to instantly connect you with compatible teammates based on:
    - 🎯 Complementary skills (not just similar ones!)
    - ⏰ Real-time availability
    - 🎨 Role optimization
    - 🧠 Experience level balance
    """)
    
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        if st.button("⚡ START QUICK TEAM FORMATION", key="main_quick_team"):
            st.session_state['page'] = 'quick_teams'
            st.rerun()
    
    # Recent quick teams
    if quick_teams:
        st.markdown("## 🔥 Recently Formed Quick Teams")
        for team in quick_teams[-3:]:
            display_quick_team_card(team)

def display_quick_team_card(team_data):
    """Display quick team formation card"""
    compatibility = calculate_team_compatibility(team_data.get('members', []))
    urgency_class = "urgent-badge" if team_data.get('urgency', 'normal') == 'high' else ""
    
    st.markdown(f"""
    <div class="team-card">
        <h3>⚡ {team_data.get('name', 'Quick Team')}</h3>
        <p><strong>🎯 Goal:</strong> {team_data.get('goal', 'Build something amazing!')}</p>
        <p><strong>👥 Size:</strong> {len(team_data.get('members', []))} / {team_data.get('target_size', 4)} members</p>
        <p><strong>🔥 Compatibility:</strong> {compatibility:.0f}%</p>
        <p><strong>⏱ Formation Time:</strong> {team_data.get('formation_time', 'Just now')}</p>
    </div>
    """, unsafe_allow_html=True)

def show_quick_teams_page():
    """Enhanced quick team formation page"""
    st.markdown("## ⚡ CYHI Quick Teams - Form Teams in Minutes!")
    
    # Quick stats at top
    col1, col2, col3 = st.columns(3)
    with col1:
        st.markdown("""
        <div class="quick-match-card">
            <h3>⏱ Average Time</h3>
            <h2>90 seconds</h2>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown("""
        <div class="quick-match-card">
            <h3>🎯 Match Accuracy</h3>
            <h2>68%</h2>
        </div>
        """, unsafe_allow_html=True)
    
    with col3:
        st.markdown("""
        <div class="quick-match-card">
            <h3>👥 Teams Formed</h3>
            <h2>{}</h2>
        </div>
        """.format(len(get_quick_teams())), unsafe_allow_html=True)
    
    # Quick team formation form
    st.markdown("### 🚀 Form Your Team Now")
    
    users = get_all_users()
    if len(users) < 2:
        st.warning("Need at least 2 registered users for team matching. Create profiles first!")
        return
    
    with st.form("instant_match_form"):
        col1, col2 = st.columns(2)
        
        with col1:
            user_name = st.selectbox("👤 Your Name", [user['name'] for user in users])
            team_size = st.slider("👥 Desired Team Size", 2, 6, 3)
            urgency = st.selectbox("🔥 Urgency Level", ["normal", "high", "critical"])
        
        with col2:
            focus_area = st.selectbox("🎯 Project Focus", 
                                    ["Web Development", "Mobile App", "AI/ML", "Data Science", 
                                     "IoT", "Blockchain", "Game Development", "Open Choice"])
            time_commitment = st.selectbox("⏰ Time Commitment", 
                                         ["2-4 hours", "Half day", "Full day", "Weekend", "Week+"])
        
        project_idea = st.text_area("💡 Quick Project Idea (Optional)", 
                                   placeholder="Briefly describe what you want to build...")
        
        match_button = st.form_submit_button("⚡ FIND MY TEAM NOW!", use_container_width=True)
        
        if match_button:
            user_profile = next((u for u in users if u['name'] == user_name), None)
            if user_profile:
                with st.spinner("🔍 Finding your perfect teammates..."):
                    import time
                    time.sleep(2)
                    
                    matches = create_instant_team_match(user_profile)
                    
                    if matches:
                        st.success("🎉 Team formed successfully!")
                        
                        team_members = [user_profile] + [match[0] for match in matches[:team_size-1]]
                        roles = generate_team_roles(team_members, focus_area)
                        compatibility = calculate_team_compatibility(team_members)
                        
                        quick_team_data = {
                            'name': f"QuickTeam_{datetime.now().strftime('%H%M%S')}",
                            'members': team_members,
                            'goal': project_idea or f"Build amazing {focus_area} solution",
                            'focus_area': focus_area,
                            'urgency': urgency,
                            'target_size': team_size,
                            'formation_time': datetime.now().strftime('%H:%M:%S'),
                            'compatibility': compatibility,
                            'roles': roles,
                            'time_commitment': time_commitment
                        }
                        
                        team_id = save_quick_team(quick_team_data)
                        
                        st.markdown(f"""
                        ### 🏆 Your Team: QuickTeam_{datetime.now().strftime('%H%M%S')}
                        *🔥 Compatibility Score: {compatibility:.0f}%*
                        """)
                        
                        categories = load_json(CATEGORIES_FILE)
                        for i, member in enumerate(team_members):
                            role = None
                            for role_name, role_info in roles.items():
                                if role_info.get('assigned') == member['name']:
                                    role = role_name
                                    break
                            display_profile_card_with_scores(member, categories, show_scores=True, role=role)
                        
                        # Next steps
                        st.markdown("### 🚀 Next Steps:")
                        col1, col2, col3 = st.columns(3)
                        
                        with col1:
                            if st.button("💬 Start Team Chat"):
                                st.info("Team chat initiated!")
                        
                        with col2:
                            if st.button("📋 Create Project Board"):
                                st.info("Project board created!")
                        
                        with col3:
                            if st.button("📅 Schedule Kickoff"):
                                st.info("Kickoff meeting scheduled!")
                    
                    else:
                        st.warning("No compatible teammates found right now. Try adjusting your preferences!")

def show_create_profile_page(categories):
    """Enhanced profile creation with team formation focus"""
    st.markdown("## 👤 Create Your Hacker Profile")
    st.markdown("Build your profile to get instant team matches!")
    
    with st.form("profile_form", clear_on_submit=True):
        col1, col2 = st.columns(2)
        
        with col1:
            name = st.text_input("💬 Full Name *", placeholder="Your name")
            
            all_domains = []
            for cat in categories.values():
                all_domains.extend(cat.get("domains", {}).keys())
            
            primary_domain = st.selectbox("🎯 Primary Domain *", [""] + all_domains)
            secondary_domain = st.selectbox("🎯 Secondary Domain", ["None"] + all_domains)
            
            experience_level = st.selectbox("📈 Experience Level *", 
                                          ["Beginner", "Intermediate", "Advanced", "Expert"])
            
            availability = st.multiselect("⏰ Availability *", 
                                        ["Right Now", "Weekends", "Evenings", "Flexible", 
                                         "Full-time", "Part-time", "Remote Only"])
        
        with col2:
            skills_input = st.text_area("🛠 Skills *", 
                                      placeholder="Python, React, UI/UX, Machine Learning...",
                                      height=100)
            
            hackathon_experience = st.selectbox("🏆 Hackathon Experience",
                                              ["First Timer", "1-2 Hackathons", "3-5 Hackathons", 
                                               "6-10 Hackathons", "Veteran (10+)"])
            
            preferred_team_size = st.slider("👥 Preferred Team Size", 2, 6, 4)
            
            leadership_interest = st.selectbox("👑 Leadership Interest",
                                             ["Prefer to Follow", "Can Lead if Needed", 
                                              "Love to Lead", "Natural Leader"])
        
        bio = st.text_area("📝 Bio & Motivation", 
                         placeholder="Tell us about yourself and what motivates you to hack!",
                         height=100)
        
        # Team preferences
        st.markdown("### 🤝 Team Preferences")
        col1, col2 = st.columns(2)
        
        with col1:
            collaboration_style = st.selectbox("🤝 Collaboration Style",
                                             ["Remote First", "In-Person Preferred", "Hybrid", "No Preference"])
            communication_pref = st.selectbox("💬 Communication Style",
                                            ["Slack/Discord", "Video Calls", "In-Person", "Flexible"])
        
        with col2:
            project_interest = st.multiselect("💡 Project Interests",
                                            ["Web Apps", "Mobile Apps", "AI/ML", "Blockchain", 
                                             "IoT", "Games", "Social Impact", "Fintech"])
            quick_team_opt_in = st.checkbox("⚡ Opt-in for Quick Team Matching", 
                                          value=True, 
                                          help="Get instant notifications for team matches")
        
        submitted = st.form_submit_button("🚀 Create Profile & Find Teams!", use_container_width=True)
        
        if submitted:
            if not all([name, skills_input, availability, primary_domain]):
                st.error("❌ Please fill all required fields marked with *")
            else:
                skills = [s.strip() for s in skills_input.split(",") if s.strip()]
                domains = [primary_domain]
                if secondary_domain and secondary_domain != "None":
                    domains.append(secondary_domain)
                
                profile = {
                    "name": name,
                    "skills": skills,
                    "availability": availability,
                    "domain": domains,
                    "experience_level": experience_level,
                    "bio": bio,
                    "hackathon_experience": hackathon_experience,
                    "preferred_team_size": preferred_team_size,
                    "leadership_interest": leadership_interest,
                    "collaboration_style": collaboration_style,
                    "communication_pref": communication_pref,
                    "project_interest": project_interest,
                    "quick_team_opt_in": quick_team_opt_in,
                    "created_date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    "last_active": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                }
                
                add_user_profile(profile)
                st.success("✅ Profile created successfully!")
                
                # Immediate team matching for new users
                if quick_team_opt_in and len(get_all_users()) > 1:
                    st.markdown("## ⚡ Instant Team Matches Available!")
                    
                    with st.spinner("Finding your perfect teammates..."):
                        import time
                        time.sleep(1.5)
                        
                        matches = create_instant_team_match(profile)
                        
                        if matches:
                            st.success(f"🎉 Found {len(matches)} potential teammates!")
                            
                            for i, (match_user, score) in enumerate(matches[:3]):
                                col1, col2 = st.columns([3, 1])
                                
                                with col1:
                                    display_profile_card_with_scores(match_user, categories, show_scores=True)
                                
                                with col2:
                                    st.markdown("<br><br>", unsafe_allow_html=True)
                                    if st.button(f"⚡ Team Up!", key=f"team_up_{i}"):
                                        team_members = [profile, match_user]
                                        team_data = {
                                            'name': f"InstantTeam_{datetime.now().strftime('%H%M%S')}",
                                            'members': team_members,
                                            'formation_time': datetime.now().strftime('%H:%M:%S'),
                                            'compatibility': calculate_team_compatibility(team_members),
                                            'type': 'instant_match'
                                        }
                                        save_quick_team(team_data)
                                        st.success("🎉 Instant team formed! Check Quick Teams page.")

def show_instant_team_match():
    """Handle instant team matching popup"""
    st.markdown("## ⚡ Instant Team Match")
    
    users = get_all_users()
    if len(users) < 2:
        st.warning("Need more users for instant matching!")
        st.session_state['show_instant_match'] = False
        return
    
    user_name = st.selectbox("Select your profile:", [user['name'] for user in users])
    
    col1, col2 = st.columns(2)
    with col1:
        if st.button("🔍 Find Instant Match"):
            user_profile = next((u for u in users if u['name'] == user_name), None)
            if user_profile:
                matches = create_instant_team_match(user_profile)
                
                if matches:
                    st.success("⚡ Instant match found!")
                    best_match = matches[0]
                    categories = load_json(CATEGORIES_FILE)
                    display_profile_card_with_scores(best_match[0], categories, show_scores=True)
                    
                    if st.button("🤝 Form Team Now!"):
                        team_data = {
                            'name': f"InstantMatch_{datetime.now().strftime('%H%M%S')}",
                            'members': [user_profile, best_match[0]],
                            'formation_time': datetime.now().strftime('%H:%M:%S'),
                            'type': 'instant_match'
                        }
                        save_quick_team(team_data)
                        st.success("🎉 Team formed successfully!")
                        st.session_state['show_instant_match'] = False
                else:
                    st.info("No instant matches available right now.")
    
    with col2:
        if st.button("❌ Close"):
            st.session_state['show_instant_match'] = False
            st.rerun()

def show_find_teams_page():
    """Enhanced team finding page with create team option"""
    st.markdown("## 🔍 Find & Join Teams")
    
    # Add create team button at the top
    if st.button("🚀 Create New Team", key="create_team_btn"):
        st.session_state['show_create_team'] = True
    
    # Show create team form if triggered
    if st.session_state.get('show_create_team', False):
        show_create_team_form()
        if st.button("← Back to Teams List"):
            st.session_state['show_create_team'] = False
            st.rerun()
        return
    
    teams = get_all_teams()
    quick_teams = get_quick_teams()
    all_teams = teams + quick_teams
    
    if not all_teams:
        st.info("No teams available yet. Create one!")
        return
    
    # Quick stats
    col1, col2, col3 = st.columns(3)
    with col1:
        active_teams = len([t for t in all_teams if t.get('status', 'active') == 'active'])
        st.metric("🔥 Active Teams", active_teams)
    
    with col2:
        looking_for_members = len([t for t in all_teams if len(t.get('members', [])) < t.get('target_size', 4)])
        st.metric("👥 Looking for Members", looking_for_members)
    
    with col3:
        avg_compatibility = sum(t.get('compatibility', 0) for t in all_teams) / len(all_teams) if all_teams else 0
        st.metric("🎯 Avg Compatibility", f"{avg_compatibility:.0f}%")
    
    # Display teams
    st.markdown("### 🚀 Available Teams")
    
    for team in all_teams:
        team_name = team.get('name', 'Unnamed Team')
        members = team.get('members', [])
        target_size = team.get('target_size', len(members))
        
        with st.container():
            st.markdown(f"""
            <div class="team-card">
                <h3>🚀 {team_name}</h3>
                <p><strong>👥 Team Size:</strong> {len(members)} / {target_size}</p>
                <p><strong>🎯 Focus:</strong> {team.get('focus_area', team.get('goal', 'General Development'))}</p>
                <p><strong>⏰ Formed:</strong> {team.get('formation_time', 'Recently')}</p>
                {f"<p><strong>🔥 Compatibility:</strong> {team.get('compatibility', 75):.0f}%</p>" if 'compatibility' in team else ""}
            </div>
            """, unsafe_allow_html=True)
            
            # Show team members
            if members:
                st.markdown("*Team Members:*")
                for member in members[:3]:
                    st.markdown(f"- 👤 {member.get('name', 'Unknown')} ({', '.join(member.get('skills', [])[:3])})")
                
                if len(members) > 3:
                    st.markdown(f"- ... and {len(members) - 3} more")
            
            # Join team button
            if len(members) < target_size:
                col1, col2, col3 = st.columns(3)
                with col1:
                    if st.button(f"🤝 Request to Join", key=f"join_{team_name}"):
                        # For demo, using first user as current user
                        users = get_all_users()
                        if users:
                            current_user = users[0]['name']
                            request_data = {
                                'team_id': team.get('id', 'unknown'),
                                'team_name': team_name,
                                'from_user': current_user,
                                'to_user': "Team Owner",  # In a real app, this would be the team creator
                                'status': 'pending',
                                'message': f"{current_user} wants to join your team {team_name}",
                                'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                            }
                            save_team_request(request_data)
                            st.success(f"✅ Join request sent to {team_name}!")
                
                with col2:
                    if st.button(f"💬 Contact Team", key=f"contact_team_{team_name}"):
                        st.info(f"📧 Message sent to {team_name} team!")
                
                with col3:
                    if st.button(f"🔍 View Details", key=f"details_team_{team_name}"):
                        st.session_state['selected_team'] = team
                        st.rerun()
            else:
                st.info("🔒 Team is full")
        
        st.markdown("---")
    
    # Show team details if a team is selected
    if st.session_state.get('selected_team'):
        team = st.session_state['selected_team']
        st.markdown(f"## 🚀 Team Details: {team.get('name')}")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("### 👥 Team Members")
            for member in team.get('members', []):
                st.markdown(f"- **{member.get('name')}** - {member.get('experience_level', 'Unknown')}")
                st.markdown(f"  Skills: {', '.join(member.get('skills', [])[:5])}")
        
        with col2:
            st.markdown("### 📋 Team Info")
            st.markdown(f"**Focus Area:** {team.get('focus_area', 'Not specified')}")
            st.markdown(f"**Project Type:** {team.get('project_type', 'Not specified')}")
            st.markdown(f"**Target Size:** {len(team.get('members', []))} / {team.get('target_size', 'Unknown')}")
            st.markdown(f"**Compatibility Score:** {team.get('compatibility', 0):.0f}%")
            st.markdown(f"**Formed On:** {team.get('created_date', 'Unknown')}")
        
        if st.button("← Back to Teams List"):
            st.session_state['selected_team'] = None
            st.rerun()

def show_team_analytics_page():
    """Simplified team analytics dashboard"""
    st.markdown("## 📊 Team Formation Analytics")
    
    users = get_all_users()
    quick_teams = get_quick_teams()
    teams = get_all_teams()
    all_teams = quick_teams + teams
    
    if not users or not all_teams:
        st.info("📈 Create some teams to see analytics!")
        return
    
    # Key metrics dashboard
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        total_teams = len(all_teams)
        st.metric("👥 Total Teams", total_teams)
    
    with col2:
        avg_team_size = sum(len(team.get('members', [])) for team in all_teams) / len(all_teams) if all_teams else 0
        st.metric("📊 Avg Team Size", f"{avg_team_size:.1f}")
    
    with col3:
        avg_compatibility = sum(team.get('compatibility', 0) for team in all_teams) / len(all_teams) if all_teams else 0
        st.metric("🔥 Avg Compatibility", f"{avg_compatibility:.0f}%")
    
    with col4:
        success_rate = 89
        st.metric("🎯 Success Rate", f"{success_rate}%")
    
    # Simple charts
    col1, col2 = st.columns(2)
    
    with col1:
        # Team size distribution
        team_sizes = [len(team.get('members', [])) for team in all_teams]
        if team_sizes:
            size_counts = {size: team_sizes.count(size) for size in set(team_sizes)}
            fig = px.bar(x=list(size_counts.keys()), y=list(size_counts.values()),
                        title="📊 Team Size Distribution",
                        labels={'x': 'Team Size', 'y': 'Number of Teams'})
            st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        # Team types
        quick_count = len(quick_teams)
        regular_count = len(teams)
        fig = px.pie(values=[quick_count, regular_count], 
                    names=['Quick Teams', 'Regular Teams'],
                    title="⚡ Team Formation Types")
        st.plotly_chart(fig, use_container_width=True)
    
    # Top skills analysis
    st.markdown("### 🎯 Top Skills in Teams")
    
    all_skills = {}
    for team in all_teams:
        for member in team.get('members', []):
            for skill in member.get('skills', []):
                all_skills[skill] = all_skills.get(skill, 0) + 1
    
    if all_skills:
        # Get top 10 skills
        top_skills = sorted(all_skills.items(), key=lambda x: x[1], reverse=True)[:10]
        
        skills_df = pd.DataFrame(top_skills, columns=['Skill', 'Count'])
        fig = px.bar(skills_df, x='Count', y='Skill', orientation='h',
                    title="🏆 Most Common Skills in Teams")
        st.plotly_chart(fig, use_container_width=True)

def create_sample_categories():
    """Create sample categories"""
    sample_categories = {
        "Technology": {
            "domains": {
                "Web Development": ["HTML", "CSS", "JavaScript", "React", "Vue.js", "Node.js", "Python", "Django", "Flask"],
                "Mobile Development": ["Flutter", "React Native", "Swift", "Kotlin", "Android", "iOS", "Xamarin"],
                "AI/ML": ["Python", "TensorFlow", "PyTorch", "Machine Learning", "Deep Learning", "NLP", "Computer Vision", "Data Science"],
                "Blockchain": ["Solidity", "Web3", "DeFi", "Smart Contracts", "Ethereum", "Bitcoin", "Cryptocurrency"],
                "Game Development": ["Unity", "Unreal Engine", "C#", "C++", "GameMaker", "Godot", "Blender"],
                "Data Science": ["Python", "R", "SQL", "Pandas", "NumPy", "Matplotlib", "Jupyter", "Statistics"],
                "DevOps": ["Docker", "Kubernetes", "AWS", "Azure", "CI/CD", "Jenkins", "Git", "Linux"],
                "Cybersecurity": ["Penetration Testing", "Network Security", "Cryptography", "Ethical Hacking", "OWASP"]
            }
        },
        "Business & Strategy": {
            "domains": {
                "Product Management": ["Product Strategy", "User Research", "Agile", "Scrum", "Analytics", "Roadmapping"],
                "Marketing": ["Digital Marketing", "SEO", "Content Marketing", "Social Media", "Email Marketing", "PPC"],
                "Finance": ["Financial Analysis", "Accounting", "Investment", "Risk Management", "Budgeting", "FinTech"],
                "Sales": ["Lead Generation", "CRM", "Sales Strategy", "Negotiation", "Customer Relations"],
                "Strategy": ["Business Planning", "Market Research", "Consulting", "Competitive Analysis"]
            }
        },
        "Design & Creative": {
            "domains": {
                "UI/UX Design": ["Figma", "Adobe XD", "Sketch", "Prototyping", "User Research", "Wireframing"],
                "Graphic Design": ["Adobe Photoshop", "Adobe Illustrator", "InDesign", "Canva", "Branding"],
                "Video Production": ["Adobe Premiere", "After Effects", "Final Cut Pro", "Video Editing", "Animation"],
                "3D Design": ["Blender", "Maya", "3ds Max", "Cinema 4D", "3D Modeling", "Rendering"],
                "Content Creation": ["Writing", "Copywriting", "Storytelling", "Photography", "Social Media Content"]
            }
        },
        "Hardware & IoT": {
            "domains": {
                "IoT Development": ["Arduino", "Raspberry Pi", "Sensors", "Embedded Systems", "C/C++", "Python"],
                "Robotics": ["ROS", "Computer Vision", "Machine Learning", "Control Systems", "Sensors"],
                "Electronics": ["Circuit Design", "PCB Design", "Microcontrollers", "Signal Processing"]
            }
        }
    }
    save_json(CATEGORIES_FILE, sample_categories)
    return sample_categories

def create_sample_users():
    """Create sample users for demonstration"""
    sample_users = [
        {
            "name": "Alex Chen",
            "skills": ["Python", "Machine Learning", "TensorFlow", "Data Science", "API Development"],
            "domain": ["AI/ML", "Web Development"],
            "experience_level": "Advanced",
            "availability": ["Evenings", "Weekends", "Flexible"],
            "bio": "AI enthusiast with 4+ years of experience building ML models and web applications.",
            "hackathon_experience": "6-10 Hackathons",
            "preferred_team_size": 4,
            "leadership_interest": "Can Lead if Needed",
            "project_interest": ["AI/ML", "Web Apps", "Social Impact"],
            "quick_team_opt_in": True,
            "created_date": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        },
        {
            "name": "Maya Patel",
            "skills": ["React", "JavaScript", "UI/UX", "Figma", "HTML", "CSS", "Node.js"],
            "domain": ["Web Development", "UI/UX Design"],
            "experience_level": "Intermediate",
            "availability": ["Right Now", "Flexible", "Remote Only"],
            "bio": "Full-stack developer with a passion for creating beautiful interfaces.",
            "hackathon_experience": "3-5 Hackathons",
            "preferred_team_size": 3,
            "leadership_interest": "Prefer to Follow",
            "project_interest": ["Web Apps", "Mobile Apps", "Social Impact"],
            "quick_team_opt_in": True,
            "created_date": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        },
        {
            "name": "Jordan Kim",
            "skills": ["Blockchain", "Solidity", "Web3", "Smart Contracts", "JavaScript", "DeFi"],
            "domain": ["Blockchain"],
            "experience_level": "Expert",
            "availability": ["Weekends", "Evenings"],
            "bio": "Blockchain architect with deep expertise in DeFi protocols.",
            "hackathon_experience": "Veteran (10+)",
            "preferred_team_size": 4,
            "leadership_interest": "Love to Lead",
            "project_interest": ["Blockchain", "Fintech"],
            "quick_team_opt_in": True,
            "created_date": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        },
        {
            "name": "Sam Rodriguez",
            "skills": ["Product Management", "User Research", "Analytics", "Strategy", "Agile", "Scrum"],
            "domain": ["Product Management"],
            "experience_level": "Advanced",
            "availability": ["Flexible", "Full-time"],
            "bio": "Product manager with 5+ years experience launching successful tech products.",
            "hackathon_experience": "3-5 Hackathons",
            "preferred_team_size": 5,
            "leadership_interest": "Natural Leader",
            "project_interest": ["Web Apps", "Mobile Apps", "Fintech", "Social Impact"],
            "quick_team_opt_in": True,
            "created_date": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        },
        {
            "name": "Riley Johnson",
            "skills": ["Unity", "C#", "Game Development", "3D Modeling", "Blender", "Animation"],
            "domain": ["Game Development"],
            "experience_level": "Intermediate",
            "availability": ["Weekends", "Evenings"],
            "bio": "Indie game developer passionate about creating immersive experiences.",
            "hackathon_experience": "1-2 Hackathons",
            "preferred_team_size": 3,
            "leadership_interest": "Can Lead if Needed",
            "project_interest": ["Games", "Mobile Apps"],
            "quick_team_opt_in": True,
            "created_date": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
    ]
    
    # Save sample users
    users_data = {user["name"]: user for user in sample_users}
    save_json(USERS_FILE, users_data)
    return sample_users

def initialize_sample_data():
    """Initialize sample data if no data exists"""
    if not os.path.exists(USERS_FILE) or not get_all_users():
        create_sample_users()
    
    if not os.path.exists(CATEGORIES_FILE) or not load_json(CATEGORIES_FILE):
        create_sample_categories()

if __name__ == "__main__":
    # Initialize sample data
    initialize_sample_data()
    
    # Main app
    main()
