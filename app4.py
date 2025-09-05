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
        background: white;
        padding: 1.5rem;
        border-radius: 15px;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
        border-left: 5px solid #667eea;
        margin: 1rem 0;
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
    .quick-team-button {
        background: linear-gradient(45deg, #ff6b6b, #feca57) !important;
        font-size: 1.2rem !important;
        padding: 1rem 3rem !important;
        animation: glow 2s ease-in-out infinite alternate;
    }
    @keyframes glow {
        from { box-shadow: 0 0 10px #ff6b6b; }
        to { box-shadow: 0 0 20px #feca57, 0 0 30px #ff6b6b; }
    }
</style>
""", unsafe_allow_html=True)

# File paths
CATEGORIES_FILE = 'categories.json'
USERS_FILE = 'users.json'
TEAMS_FILE = 'teams.json'
QUICK_TEAMS_FILE = 'quick_teams.json'
HACKATHONS_FILE = 'hackathons.json'

def load_json(file_path):
    if os.path.exists(file_path):
        with open(file_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    else:
        return {}

def save_json(file_path, data):
    with open(file_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=4)

def add_user_profile(profile):
    users = load_json(USERS_FILE)
    users[profile['name']] = profile
    save_json(USERS_FILE, users)

def get_all_users():
    users = load_json(USERS_FILE)
    return list(users.values())

def save_team(team_data):
    teams = load_json(TEAMS_FILE)
    team_id = f"team_{len(teams) + 1}_{datetime.now().strftime('%Y%m%d%H%M%S')}"
    teams[team_id] = team_data
    save_json(TEAMS_FILE, teams)
    return team_id

def get_all_teams():
    teams = load_json(TEAMS_FILE)
    return list(teams.values())

def save_quick_team(quick_team_data):
    quick_teams = load_json(QUICK_TEAMS_FILE)
    team_id = f"quick_{len(quick_teams) + 1}_{datetime.now().strftime('%Y%m%d%H%M%S')}"
    quick_teams[team_id] = quick_team_data
    save_json(QUICK_TEAMS_FILE, quick_teams)
    return team_id

def get_quick_teams():
    quick_teams = load_json(QUICK_TEAMS_FILE)
    return list(quick_teams.values())

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
    
    skill_diversity = len(all_skills) / (sum(len(member.get('skills', [])) for member in members) + 1)
    
    # Experience level balance
    exp_levels = [member.get('experience_level', 'Intermediate') for member in members]
    exp_variety = len(set(exp_levels)) / len(exp_levels)
    
    # Availability overlap
    avail_sets = [set(member.get('availability', [])) for member in members if member.get('availability')]
    if avail_sets:
        common_avail = set.intersection(*avail_sets)
        avail_score = len(common_avail) / 5  # Assuming max 5 availability options
    else:
        avail_score = 0.5
    
    # Domain diversity
    domains = set()
    for member in members:
        domains.update(member.get('domain', []))
    domain_diversity = len(domains) / len(members)
    
    total_score = (skill_diversity * 0.4 + exp_variety * 0.2 + avail_score * 0.2 + domain_diversity * 0.2) * 100
    return min(100, total_score)

def display_profile_card(user, score=None, role=None):
    """Display a beautiful profile card"""
    with st.container():
        role_emoji = {"Team Lead": "👑", "Tech Lead": "🚀", "Designer": "🎨", "Backend Dev": "⚙", 
                     "Frontend Dev": "💻", "Data Specialist": "📊", "Business Analyst": "📈"}.get(role, "👤")
        
        st.markdown(f"""
        <div class="profile-card">
            <h3>{role_emoji} {user['name']} {f"({role})" if role else ""}</h3>
            {f"<p><strong>🎯 Match Score:</strong> {score:.0%}</p>" if score else ""}
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

    # Navigation with enhanced quick team options
    st.sidebar.markdown("## ⚡ Quick Actions")
    
    # Quick team formation button
    if st.sidebar.button("🚀 INSTANT TEAM MATCH", key="instant_team", help="Get matched with a team in under 60 seconds!"):
        st.session_state['show_instant_match'] = True
    
    st.sidebar.markdown("---")
    st.sidebar.markdown("## 🧭 Navigation")
    
    page = st.sidebar.radio("Choose your action:", 
                           ["🏠 Home", "⚡ Quick Teams", "👤 Create Profile", "🔍 Find Teams", 
                            "🏆 Active Hackathons", "📊 Team Analytics", "👥 Browse Users"])

    if page == "🏠 Home":
        show_home_page()
    elif page == "⚡ Quick Teams":
        show_quick_teams_page()
    elif page == "👤 Create Profile":
        show_create_profile_page(categories)
    elif page == "🔍 Find Teams":
        show_find_teams_page()
    elif page == "🏆 Active Hackathons":
        show_hackathons_page()
    elif page == "📊 Team Analytics":
        show_team_analytics_page()
    elif page == "👥 Browse Users":
        show_browse_users_page()
    
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
        avg_team_time = "< 2 min"  # Mock average team formation time
        st.markdown(f"""
        <div class="metric-card">
            <h2>⏱</h2>
            <h3>{avg_team_time}</h3>
            <p>Avg Team Formation</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col4:
        success_rate = 92  # Mock success rate
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
        for i, team in enumerate(quick_teams[-3:]):
            display_quick_team_card(team)

def show_quick_teams_page():
    """Enhanced quick team formation page - the core CYHI feature"""
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
            <h2>92%</h2>
        </div>
        """, unsafe_allow_html=True)
    
    with col3:
        st.markdown("""
        <div class="quick-match-card">
            <h3>👥 Teams Formed</h3>
            <h2>{}</h2>
        </div>
        """.format(len(get_quick_teams())), unsafe_allow_html=True)
    
    # Quick team formation options
    st.markdown("### Choose Your Quick Team Formation Method:")
    
    tab1, tab2, tab3 = st.tabs(["🚀 Instant Match", "🎯 Smart Assembly", "🏆 Hackathon Ready"])
    
    with tab1:
        show_instant_match_form()
    
    with tab2:
        show_smart_assembly_form()
    
    with tab3:
        show_hackathon_ready_form()

def show_instant_match_form():
    """Instant team matching form"""
    st.markdown("#### ⚡ Get matched instantly with available teammates!")
    
    users = get_all_users()
    if len(users) < 2:
        st.warning("⚠ Need at least 2 registered users for team matching. Create profiles first!")
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
            # Find the user profile
            user_profile = next((u for u in users if u['name'] == user_name), None)
            if user_profile:
                with st.spinner("🔍 Finding your perfect teammates..."):
                    import time
                    time.sleep(2)  # Simulate processing time
                    
                    matches = create_instant_team_match(user_profile)
                    
                    if matches:
                        st.success("🎉 Team formed successfully!")
                        
                        # Create team members list
                        team_members = [user_profile] + [match[0] for match in matches[:team_size-1]]
                        
                        # Generate roles
                        roles = generate_team_roles(team_members, focus_area)
                        compatibility = calculate_team_compatibility(team_members)
                        
                        # Save quick team
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
                        
                        # Display team
                        st.markdown(f"""
                        ### 🏆 Your Team: QuickTeam_{datetime.now().strftime('%H%M%S')}
                        *🔥 Compatibility Score: {compatibility:.0f}%*
                        """)
                        
                        for i, member in enumerate(team_members):
                            role = None
                            for role_name, role_info in roles.items():
                                if role_info.get('assigned') == member['name']:
                                    role = role_name
                                    break
                            display_profile_card(member, 
                                               score=matches[i-1][1]/10 if i > 0 else 1.0,
                                               role=role)
                        
                        # Next steps
                        st.markdown("### 🚀 Next Steps:")
                        col1, col2, col3 = st.columns(3)
                        
                        with col1:
                            if st.button("💬 Start Team Chat"):
                                st.info("Team chat initiated! Check your notifications.")
                        
                        with col2:
                            if st.button("📋 Create Project Board"):
                                st.info("Project board created! Link shared with team.")
                        
                        with col3:
                            if st.button("📅 Schedule Kickoff"):
                                st.info("Kickoff meeting scheduled! Calendar invites sent.")
                    
                    else:
                        st.warning("😅 No compatible teammates found right now. Try adjusting your preferences or create more profiles!")

def show_smart_assembly_form():
    """Smart team assembly with more control"""
    st.markdown("#### 🎯 Smart team assembly with role-based matching")
    
    users = get_all_users()
    if len(users) < 3:
        st.warning("⚠ Need at least 3 users for smart assembly!")
        return
    
    with st.form("smart_assembly_form"):
        st.markdown("*Step 1: Define your ideal team structure*")
        
        required_roles = st.multiselect("🎭 Required Roles", 
                                      ["Team Lead", "Tech Lead", "Designer", "Backend Dev", 
                                       "Frontend Dev", "Data Specialist", "Business Analyst"],
                                      default=["Tech Lead", "Designer"])
        
        col1, col2 = st.columns(2)
        with col1:
            min_experience = st.selectbox("📈 Minimum Experience Level", 
                                        ["Beginner", "Intermediate", "Advanced", "Expert"])
            project_type = st.selectbox("🚀 Project Type",
                                      ["Startup MVP", "Hackathon Project", "Open Source", "Research"])
        
        with col2:
            collaboration_style = st.selectbox("🤝 Collaboration Style",
                                             ["Remote", "In-person", "Hybrid", "Flexible"])
            timeline = st.selectbox("⏰ Project Timeline",
                                   ["24 hours", "48 hours", "1 week", "2-4 weeks", "1+ month"])
        
        project_description = st.text_area("📝 Project Description",
                                         placeholder="Describe your project vision and goals...")
        
        assemble_button = st.form_submit_button("🎯 ASSEMBLE SMART TEAM!", use_container_width=True)
        
        if assemble_button and project_description and required_roles:
            with st.spinner("🧠 Using AI to find the perfect team combination..."):
                import time
                time.sleep(3)  # Simulate AI processing
                
                # Smart matching algorithm
                available_users = [u for u in users if u.get('experience_level', 'Intermediate') != 'Beginner' or min_experience == 'Beginner']
                
                # Create optimal team based on roles
                selected_team = []
                used_users = set()
                
                for role in required_roles:
                    best_candidate = None
                    best_score = 0
                    
                    role_skills = {
                        'Team Lead': ['leadership', 'management', 'communication'],
                        'Tech Lead': ['programming', 'architecture', 'technical'],
                        'Designer': ['design', 'ui', 'ux', 'figma'],
                        'Backend Dev': ['python', 'java', 'database', 'api'],
                        'Frontend Dev': ['react', 'javascript', 'html', 'css'],
                        'Data Specialist': ['data', 'analytics', 'machine learning'],
                        'Business Analyst': ['business', 'strategy', 'analysis']
                    }.get(role, [])
                    
                    for user in available_users:
                        if user['name'] in used_users:
                            continue
                        
                        user_skills = [s.lower() for s in user.get('skills', [])]
                        score = sum(1 for skill in role_skills if any(skill in us for us in user_skills))
                        
                        if score > best_score:
                            best_score = score
                            best_candidate = user
                    
                    if best_candidate:
                        selected_team.append((best_candidate, role))
                        used_users.add(best_candidate['name'])
                
                if selected_team:
                    st.success("🎉 Smart team assembled successfully!")
                    
                    team_data = {
                        'name': f"SmartTeam_{datetime.now().strftime('%H%M%S')}",
                        'members': [member[0] for member in selected_team],
                        'roles': {member[1]: member[0]['name'] for member in selected_team},
                        'project_type': project_type,
                        'description': project_description,
                        'timeline': timeline,
                        'collaboration_style': collaboration_style,
                        'formation_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                    }
                    
                    save_quick_team(team_data)
                    
                    st.markdown("### 🏆 Your Smart Team:")
                    
                    for member, role in selected_team:
                        display_profile_card(member, role=role)
                    
                    # Team compatibility analysis
                    compatibility = calculate_team_compatibility([member[0] for member in selected_team])
                    st.markdown(f"🔥 Team Compatibility: {compatibility:.0f}%")
                    
                    # Project roadmap suggestion
                    st.markdown("### 🗺 Suggested Project Roadmap:")
                    roadmap_phases = {
                        "24 hours": ["Planning (2h)", "MVP Development (16h)", "Testing & Demo (6h)"],
                        "48 hours": ["Planning & Design (6h)", "Core Development (30h)", "Integration & Testing (8h)", "Demo Prep (4h)"],
                        "1 week": ["Week 1: Planning & Architecture", "Week 2-5: Development Sprints", "Week 6-7: Testing & Refinement"],
                        "2-4 weeks": ["Phase 1: Research & Design", "Phase 2: Core Development", "Phase 3: Feature Enhancement", "Phase 4: Launch Prep"],
                        "1+ month": ["Month 1: Foundation", "Month 2-3: Core Features", "Month 4+: Scale & Optimize"]
                    }
                    
                    phases = roadmap_phases.get(timeline, ["Phase 1: Start", "Phase 2: Build", "Phase 3: Launch"])
                    for i, phase in enumerate(phases, 1):
                        st.markdown(f"{i}. **{phase}")

def show_hackathon_ready_form():
    """Hackathon-specific team formation"""
    st.markdown("#### 🏆 Form teams optimized for hackathon success")
    
    # Mock hackathon data
    active_hackathons = [
        {"name": "AI Innovation Challenge", "deadline": "2 days", "theme": "AI/ML", "prizes": "$50K"},
        {"name": "Web3 Builder Fest", "deadline": "5 days", "theme": "Blockchain", "prizes": "$25K"},
        {"name": "Climate Tech Hack", "deadline": "1 week", "theme": "Sustainability", "prizes": "$30K"},
        {"name": "FinTech Revolution", "deadline": "3 days", "theme": "Finance", "prizes": "$40K"}
    ]
    
    with st.form("hackathon_ready_form"):
        hackathon = st.selectbox("🏆 Target Hackathon", 
                                [f"{h['name']} - {h['deadline']} left (Prize: {h['prizes']})" for h in active_hackathons])
        
        if hackathon:
            selected_hackathon = active_hackathons[0]  # Default to first hackathon
            
            col1, col2 = st.columns(2)
            with col1:
                your_strength = st.selectbox("💪 Your Primary Strength",
                                           ["Technical Development", "UI/UX Design", "Business Strategy", 
                                            "Data Science", "Product Management", "Marketing"])
                competition_level = st.selectbox("🎯 Competition Level",
                                               ["Beginner Friendly", "Intermediate", "Advanced", "Expert Level"])
            
            with col2:
                team_strategy = st.selectbox("📈 Team Strategy",
                                           ["Speed & MVP", "Polish & Presentation", "Innovation Focus", 
                                            "Technical Excellence", "Market Viability"])
                preferred_role = st.selectbox("🎭 Preferred Role in Team",
                                            ["Leader", "Core Developer", "Specialist", "Support", "Flexible"])
        
        hackathon_experience = st.text_area("🏆 Previous Hackathon Experience",
                                          placeholder="Describe your hackathon experience and notable achievements...")
        
        form_team_button = st.form_submit_button("🏆 FORM HACKATHON TEAM!", use_container_width=True)
        
        if form_team_button and hackathon_experience:
            with st.spinner("🏆 Assembling your winning hackathon team..."):
                import time
                time.sleep(2.5)
                
                users = get_all_users()
                if len(users) >= 3:
                    # Hackathon-optimized matching
                    hackathon_team = random.sample(users, min(4, len(users)))
                    
                    # Create hackathon team data
                    team_data = {
                        'name': f"HackTeam_{selected_hackathon['name'].split()[0]}",
                        'hackathon': selected_hackathon,
                        'members': hackathon_team,
                        'strategy': team_strategy,
                        'competition_level': competition_level,
                        'formation_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                        'deadline': selected_hackathon['deadline']
                    }
                    
                    save_quick_team(team_data)
                    
                    st.success(f"🎉 Hackathon team formed for {selected_hackathon['name']}!")
                    
                    # Display team with hackathon focus
                    st.markdown(f"""
                    ### 🏆 Team: {team_data['name']}
                    *🎯 Target:* {selected_hackathon['name']}  
                    *⏰ Deadline:* {selected_hackathon['deadline']}  
                    *💰 Prize Pool:* {selected_hackathon['prizes']}  
                    *📈 Strategy:* {team_strategy}
                    """)
                    
                    # Assign hackathon-specific roles
                    hackathon_roles = ["Ideator & Presenter", "Lead Developer", "Designer & UX", "Integration & Demo"]
                    for i, member in enumerate(hackathon_team):
                        role = hackathon_roles[i % len(hackathon_roles)]
                        display_profile_card(member, role=role)
                    
                    # Hackathon success tips
                    st.markdown("""
                    ### 🎯 Hackathon Success Tips:
                    
                    **⏰ Time Management:**
                    - First 2 hours: Team bonding & detailed planning
                    - 60% of time: Core development
                    - 25% of time: Integration & testing
                    - 15% of time: Demo preparation & presentation
                    
                    **🏆 Winning Strategy:**
                    - Focus on solving a real problem
                    - Keep MVP simple but polished
                    - Prepare a compelling 3-minute demo
                    - Practice your pitch multiple times
                    """)
                    
                    # Quick actions for hackathon team
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        if st.button("📋 Create Sprint Board"):
                            st.info("Sprint board created with hackathon timeline!")
                    with col2:
                        if st.button("💬 Team Discord"):
                            st.info("Discord channel created for team communication!")
                    with col3:
                        if st.button("📊 Track Progress"):
                            st.info("Progress tracker initialized!")

def show_hackathons_page():
    """Display active and upcoming hackathons"""
    st.markdown("## 🏆 Active Hackathons & Competitions")
    
    # Mock hackathon data
    hackathons = [
        {
            "name": "AI Innovation Challenge 2025",
            "organizer": "TechCorp",
            "theme": "Artificial Intelligence",
            "deadline": datetime.now() + timedelta(days=2),
            "prize_pool": "$50,000",
            "participants": 1247,
            "teams_needed": 8,
            "difficulty": "Advanced",
            "description": "Build innovative AI solutions that solve real-world problems"
        },
        {
            "name": "Web3 Builder Fest",
            "organizer": "Blockchain Foundation",
            "theme": "Blockchain & DeFi",
            "deadline": datetime.now() + timedelta(days=5),
            "prize_pool": "$25,000",
            "participants": 892,
            "teams_needed": 12,
            "difficulty": "Intermediate",
            "description": "Create decentralized applications that reshape finance"
        },
        {
            "name": "Climate Tech Hackathon",
            "organizer": "Green Future",
            "theme": "Sustainability",
            "deadline": datetime.now() + timedelta(days=7),
            "prize_pool": "$30,000",
            "participants": 654,
            "teams_needed": 15,
            "difficulty": "Beginner Friendly",
            "description": "Develop technology solutions for climate change"
        }
    ]
    
    # Display hackathon cards
    for hackathon in hackathons:
        days_left = (hackathon["deadline"] - datetime.now()).days
        urgency_color = "🔴" if days_left <= 2 else "🟡" if days_left <= 5 else "🟢"
        
        with st.container():
            st.markdown(f"""
            <div class="team-card">
                <h3>🏆 {hackathon['name']}</h3>
                <p><strong>🏢 Organizer:</strong> {hackathon['organizer']}</p>
                <p><strong>🎯 Theme:</strong> {hackathon['theme']}</p>
                <p><strong>💰 Prize Pool:</strong> {hackathon['prize_pool']}</p>
                <p><strong>{urgency_color} Deadline:</strong> {days_left} days left</p>
                <p><strong>👥 Participants:</strong> {hackathon['participants']} | <strong>🔍 Teams Needed:</strong> {hackathon['teams_needed']}</p>
                <p><strong>📈 Difficulty:</strong> {hackathon['difficulty']}</p>
                <p><strong>📝 Description:</strong> {hackathon['description']}</p>
            </div>
            """, unsafe_allow_html=True)
            
            col1, col2, col3 = st.columns(3)
            with col1:
                if st.button(f"⚡ Quick Team for {hackathon['name'][:10]}...", key=f"quick_{hackathon['name']}"):
                    st.session_state['selected_hackathon'] = hackathon
                    st.session_state['show_hackathon_team'] = True
            
            with col2:
                if st.button(f"📋 View Details", key=f"details_{hackathon['name']}"):
                    st.info(f"Opening {hackathon['name']} details...")
            
            with col3:
                if st.button(f"👥 Join Existing Team", key=f"join_{hackathon['name']}"):
                    st.info("Showing available teams for this hackathon...")
        
        st.markdown("---")

def show_team_analytics_page():
    """Advanced team analytics and insights"""
    st.markdown("## 📊 Team Formation Analytics")
    
    users = get_all_users()
    quick_teams = get_quick_teams()
    
    if not users or not quick_teams:
        st.info("📈 Create some teams to see analytics!")
        return
    
    # Key metrics dashboard
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        avg_team_size = sum(len(team.get('members', [])) for team in quick_teams) / len(quick_teams) if quick_teams else 0
        st.metric("👥 Avg Team Size", f"{avg_team_size:.1f}")
    
    with col2:
        avg_compatibility = sum(team.get('compatibility', 0) for team in quick_teams) / len(quick_teams) if quick_teams else 0
        st.metric("🔥 Avg Compatibility", f"{avg_compatibility:.0f}%")
    
    with col3:
        success_rate = 89  # Mock success rate
        st.metric("🎯 Success Rate", f"{success_rate}%")
    
    with col4:
        total_formations = len(quick_teams)
        st.metric("⚡ Total Formations", total_formations)
    
    # Charts
    col1, col2 = st.columns(2)
    
    with col1:
        # Team size distribution
        team_sizes = [len(team.get('members', [])) for team in quick_teams]
        if team_sizes:
            size_counts = {size: team_sizes.count(size) for size in set(team_sizes)}
            fig = px.bar(x=list(size_counts.keys()), y=list(size_counts.values()),
                        title="📊 Team Size Distribution",
                        labels={'x': 'Team Size', 'y': 'Number of Teams'})
            st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        # Formation time analysis (mock data)
        formation_times = ["< 1 min", "1-2 min", "2-5 min", "5+ min"]
        time_counts = [15, 25, 8, 2]  # Mock data
        
        fig = px.pie(values=time_counts, names=formation_times,
                    title="⏱ Team Formation Speed")
        st.plotly_chart(fig, use_container_width=True)
    
    # Skills gap analysis
    st.markdown("### 🎯 Skills Gap Analysis")
    
    all_skills = {}
    for user in users:
        for skill in user.get('skills', []):
            all_skills[skill] = all_skills.get(skill, 0) + 1
    
    if all_skills:
        # Find underrepresented skills
        total_users = len(users)
        skill_percentages = {skill: (count/total_users)*100 for skill, count in all_skills.items()}
        
        underrepresented = {skill: pct for skill, pct in skill_percentages.items() if pct < 20}
        
        if underrepresented:
            st.markdown("#### 🔍 Skills in High Demand (< 20% coverage):")
            for skill, percentage in sorted(underrepresented.items(), key=lambda x: x[1]):
                st.markdown(f"- *{skill}*: {percentage:.1f}% of users")
        
        # Most common skills
        common_skills = sorted(skill_percentages.items(), key=lambda x: x[1], reverse=True)[:10]
        
        col1, col2 = st.columns(2)
        with col1:
            st.markdown("#### 🏆 Most Common Skills:")
            for skill, pct in common_skills[:5]:
                st.markdown(f"- {skill}: {pct:.1f}%")
        
        with col2:
            st.markdown("#### 📈 Trending Combinations:")
            # Mock trending skill combinations
            trending = ["Python + AI", "React + Node.js", "Figma + UI/UX", "Data Science + ML", "Blockchain + DeFi"]
            for trend in trending:
                st.markdown(f"- {trend}")

def show_browse_users_page():
    """Enhanced user browsing with team formation context"""
    st.markdown("## 👥 Browse Hackers & Form Teams")
    
    users = get_all_users()
    if not users:
        st.info("📭 No users registered yet. Be the first!")
        return
    
    # Enhanced filters
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        available_now = st.checkbox("⚡ Available Now", help="Show only users available for immediate team formation")
    
    with col2:
        experience_filter = st.selectbox("📈 Min Experience", ["Any", "Beginner", "Intermediate", "Advanced", "Expert"])
    
    with col3:
        all_domains = set()
        for user in users:
            all_domains.update(user.get('domain', []))
        domain_filter = st.selectbox("🎯 Domain", ["Any"] + sorted(list(all_domains)))
    
    with col4:
        team_role_filter = st.selectbox("🎭 Looking for Role", 
                                      ["Any", "Team Lead", "Developer", "Designer", "Business", "Data Specialist"])
    
    # Apply filters
    filtered_users = users.copy()
    
    if available_now:
        filtered_users = [u for u in filtered_users if 'Flexible' in u.get('availability', [])]
    
    if experience_filter != "Any":
        filtered_users = [u for u in filtered_users if u.get('experience_level') == experience_filter]
    
    if domain_filter != "Any":
        filtered_users = [u for u in filtered_users if domain_filter in u.get('domain', [])]
    
    # User cards with team formation actions
    st.markdown(f"### 👥 {len(filtered_users)} Hackers Found")
    
    for user in filtered_users:
        col1, col2 = st.columns([3, 1])
        
        with col1:
            display_profile_card(user)
        
        with col2:
            st.markdown("<br>", unsafe_allow_html=True)
            if st.button(f"⚡ Quick Team", key=f"qt_{user['name']}", help="Form instant team with this user"):
                # Simulate quick team formation
                matches = create_instant_team_match(user)
                if matches:
                    st.success(f"✅ Team formed with {user['name']}!")
                    # You could store this team or show more details
                else:
                    st.warning("😅 No immediate matches found")
            
            if st.button(f"💬 Contact", key=f"contact_{user['name']}"):
                st.info(f"📧 Contact request sent to {user['name']}")
            
            if st.button(f"🔍 Find Similar", key=f"similar_{user['name']}", help="Find users with similar skills"):
                similar_users = []
                user_skills = set(s.lower() for s in user.get('skills', []))
                
                for other_user in users:
                    if other_user['name'] == user['name']:
                        continue
                    other_skills = set(s.lower() for s in other_user.get('skills', []))
                    overlap = len(user_skills.intersection(other_skills))
                    if overlap >= 2:  # At least 2 common skills
                        similar_users.append((other_user, overlap))
                
                if similar_users:
                    st.success(f"Found {len(similar_users)} similar users!")
                else:
                    st.info("No similar users found")

def show_create_profile_page(categories):
    """Enhanced profile creation with team formation focus"""
    st.markdown("## 👤 Create Your Hacker Profile")
    st.markdown("Build your profile to get instant team matches!")
    
    with st.form("profile_form", clear_on_submit=True):
        col1, col2 = st.columns(2)
        
        with col1:
            name = st.text_input("💬 Full Name *", placeholder="Your name")
            
            all_domains = []
            for cat in categories:
                all_domains.extend(categories[cat]["domains"].keys())
            
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
                                    display_profile_card(match_user, score=score/10)
                                
                                with col2:
                                    st.markdown("<br><br>", unsafe_allow_html=True)
                                    if st.button(f"⚡ Team Up!", key=f"team_up_{i}"):
                                        # Create instant team
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
        return
    
    user_name = st.selectbox("Select your profile:", [user['name'] for user in users])
    
    if st.button("🔍 Find Instant Match"):
        user_profile = next((u for u in users if u['name'] == user_name), None)
        if user_profile:
            matches = create_instant_team_match(user_profile)
            
            if matches:
                st.success("⚡ Instant match found!")
                best_match = matches[0]
                display_profile_card(best_match[0], score=best_match[1]/10)
                
                if st.button("🤝 Form Team Now!"):
                    team_data = {
                        'name': f"InstantMatch_{datetime.now().strftime('%H%M%S')}",
                        'members': [user_profile, best_match[0]],
                        'formation_time': datetime.now().strftime('%H:%M:%S'),
                        'type': 'instant_match'
                    }
                    save_quick_team(team_data)
                    st.success("🎉 Team formed successfully!")
            else:
                st.info("No instant matches available right now.")

def show_find_teams_page():
    """Enhanced team finding with CYHI quick team focus"""
    st.markdown("## 🔍 Find & Join Teams")
    
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
        
        # Team card
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
                for member in members[:3]:  # Show first 3 members
                    st.markdown(f"- 👤 {member.get('name', 'Unknown')} ({', '.join(member.get('skills', [])[:3])})")
                
                if len(members) > 3:
                    st.markdown(f"- ... and {len(members) - 3} more")
            
            # Join team button
            if len(members) < target_size:
                col1, col2, col3 = st.columns(3)
                with col1:
                    if st.button(f"🤝 Request to Join", key=f"join_{team_name}"):
                        st.success(f"✅ Join request sent to {team_name}!")
                
                with col2:
                    if st.button(f"💬 Contact Team", key=f"contact_team_{team_name}"):
                        st.info(f"📧 Message sent to {team_name} team!")
                
                with col3:
                    if st.button(f"🔍 View Details", key=f"details_team_{team_name}"):
                        st.info("Opening team details...")
            else:
                st.info("🔒 Team is full")
        
        st.markdown("---")

# Sample data creation functions
def create_sample_categories():
    """Create sample categories for CYHI"""
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
            "bio": "AI enthusiast with 4+ years of experience building ML models and web applications. Love hackathons and collaborative coding!",
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
            "bio": "Full-stack developer with a passion for creating beautiful, user-friendly interfaces. Always excited about new challenges!",
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
            "bio": "Blockchain architect with deep expertise in DeFi protocols. Founded 2 crypto startups and love building the future of finance.",
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
            "bio": "Product manager with 5+ years experience launching successful tech products. Great at turning ideas into actionable plans.",
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
            "bio": "Indie game developer passionate about creating immersive experiences. Published 3 mobile games and love collaborative projects.",
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
        st.info("Sample users created for demonstration!")
    
    if not os.path.exists(CATEGORIES_FILE) or not load_json(CATEGORIES_FILE):
        create_sample_categories()

# Enhanced sidebar with CYHI features
def enhanced_sidebar():
    """Enhanced sidebar with CYHI quick team features"""
    st.sidebar.markdown("---")
    
    # Quick team status
    st.sidebar.markdown("### Quick Team Status")
    users = get_all_users()
    quick_teams = get_quick_teams()
    
    available_users = len([u for u in users if "Right Now" in u.get('availability', []) or "Flexible" in u.get('availability', [])])
    st.sidebar.metric("Available Now", available_users)
    st.sidebar.metric("Quick Teams Today", len(quick_teams))
    
    # Formation speed indicator
    if quick_teams:
        avg_time = "< 2 min"  # Mock calculation
        st.sidebar.metric("Avg Formation Time", avg_time)
    
    st.sidebar.markdown("---")
    
    # Quick actions
    st.sidebar.markdown("### Quick Actions")
    
    if st.sidebar.button("Smart Match Me", help="Find best teammates using AI"):
        st.session_state['show_smart_match'] = True
    
    if st.sidebar.button("Join Urgent Team", help="Join teams that need members ASAP"):
        st.session_state['show_urgent_teams'] = True
    
    if st.sidebar.button("My Team Stats", help="View your team formation history"):
        st.session_state['show_my_stats']= True

    st.sidebar.markdown("---")
    
    # Current hackathons sidebar
    st.sidebar.markdown("### Live Hackathons")
    hackathons = [
        {"name": "AI Challenge", "deadline": "2 days"},
        {"name": "Web3 Fest", "deadline": "5 days"},
        {"name": "Climate Tech", "deadline": "1 week"}
    ]
    
    for hackathon in hackathons:
        st.sidebar.markdown(f"*{hackathon['name']}*")
        st.sidebar.markdown(f"{hackathon['deadline']} left")
        if st.sidebar.button(f"Quick Team", key=f"sidebar_{hackathon['name']}"):
            st.session_state['selected_hackathon'] = hackathon
    
    st.sidebar.markdown("---")
    
    # Tips section
    with st.sidebar.expander("Quick Team Tips"):
        st.markdown("""
        **Fast Formation Tips:**
        - Keep availability updated
        - List complementary skills
        - Be open to new ideas
        - Communicate quickly
        
        **Better Matches:**
        - Complete your bio
        - Specify experience level
        - Set realistic team size
        - Join multiple domains
        """)

def show_notification_center():
    """Show notifications for team invites, matches, etc."""
    if st.session_state.get('show_notifications'):
        st.sidebar.markdown("### Notifications")
        
        # Mock notifications
        notifications = [
            {"type": "team_invite", "message": "Alex Chen invited you to AI Dream Team", "time": "2 min ago"},
            {"type": "match_found", "message": "New perfect match found!", "time": "5 min ago"},
            {"type": "hackathon", "message": "AI Challenge deadline in 2 days", "time": "1 hour ago"}
        ]
        
        for notif in notifications:
            icon = {"team_invite": "handshake", "match_found": "target", "hackathon": "trophy"}.get(notif["type"], "bell")
            st.sidebar.markdown(f"{icon} {notif['message']}")
            st.sidebar.caption(notif["time"])

# Performance tracking
def track_team_formation_metrics():
    """Track metrics for team formation success"""
    quick_teams = get_quick_teams()
    
    metrics = {
        "total_formations": len(quick_teams),
        "avg_formation_time": 95,  # seconds - mock data
        "success_rate": 92,  # percentage - mock data
        "user_satisfaction": 4.6,  # out of 5 - mock data
        "most_common_team_size": 3,
        "peak_formation_hours": ["19:00-21:00", "10:00-12:00"]  # mock data
    }
    
    return metrics

# Real-time team matching simulation
def simulate_real_time_matching():
    """Simulate real-time matching notifications"""
    if st.session_state.get('real_time_matching', False):
        # This would integrate with real WebSocket connections in production
        import time
        import random
        
        placeholder = st.empty()
        
        for i in range(3):
            time.sleep(2)
            placeholder.info(f"Searching for teammates... {i+1}/3")
        
        time.sleep(1)
        placeholder.success("Perfect match found! Creating team...")

if __name__ == "__main__":
    # Initialize sample data
    initialize_sample_data()
    
    # Enhanced sidebar
    enhanced_sidebar()
    
    # Show notifications
    show_notification_center()
    
    # Main app
    main()
    
    # Handle session state for various popups/modals
    if st.session_state.get('show_smart_match'):
        st.session_state['show_smart_match'] = False
        st.rerun()
    
    if st.session_state.get('show_urgent_teams'):
        st.session_state['show_urgent_teams'] = False
        st.rerun()
    
    # Real-time matching simulation (for demo purposes)
    if st.session_state.get('start_real_time_matching'):
        simulate_real_time_matching()
        st.session_state['start_real_time_matching'] = False
                        