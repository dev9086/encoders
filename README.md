# encoders
HackMate - CYHI Quick Teams ⚡
A powerful Streamlit application designed to help hackers form optimal teams quickly for hackathons using AI-powered matching algorithms.

Live Demo
🚀 Try it now: HackMate Live on Hugging Face Spaces

Features
⚡ Instant Team Matching: Form teams in under 2 minutes with AI-powered matching

🎯 Smart Skill Analysis: ML algorithms analyze skill compatibility and domain expertise

👥 Browse Hackers: Find teammates based on skills, availability, and experience

📊 Team Analytics: View team compatibility scores and formation statistics

🏢 Group Management: Create and manage skill categories and domains

📨 Team Requests: Send and manage team join requests

How It Works
Create Your Profile: Add your skills, experience level, availability, and preferences

Find Matches: Use ML-powered matching to find compatible teammates

Form Teams: Create teams instantly or send join requests

Analyze Performance: View team compatibility scores and analytics

Installation
Clone the repository:

bash
git clone https://github.com/yourusername/hackmate-quick-teams.git
cd hackmate-quick-teams
Install required dependencies:

bash
pip install -r requirements.txt
Run the application:

bash
streamlit run app2.py
Requirements
Python 3.7+

Streamlit

scikit-learn

pandas

numpy

plotly

Pillow

File Structure
text
hackmate-quick-teams/
├── app2.py              # Main application file
├── categories.json      # Skill categories and domains (auto-generated)
├── users.json          # User profiles (auto-generated)
├── teams.json          # Team data (auto-generated)
├── quick_teams.json    # Quick team formations (auto-generated)
├── team_requests.json  # Team join requests (auto-generated)
├── achievement_uploads/ # Directory for achievement uploads
└── README.md           # This file
Usage
Create a Profile: Navigate to the "Create Profile" section and fill in your details

Find Teams: Browse existing teams or use the instant matching feature

Form Teams: Create new teams or join existing ones

Manage Groups: Create skill categories and domains for better matching

Technologies Used
Frontend: Streamlit with custom CSS styling

Backend: Python with scikit-learn for ML matching

Data Storage: JSON files for persistence

Visualization: Plotly for analytics charts

Contributing
Fork the repository

Create a feature branch

Make your changes

Submit a pull request

License
This project is licensed under the MIT License.

Support
For support or questions, please open an issue in the GitHub repository.

📊 Example Use Cases

🏢 Hackathon Organizers – Provide participants a tool to find teammates quickly.

👨‍💻 Developers & Designers – Find complementary skills for better collaboration.

🎓 Students – Build strong, diverse teams for projects or competitions.

🔮 Future Improvements

🌍 Multi-language support

📨 Real-time team chat integration

🧠 Advanced ML-based role recommendation

☁️ Cloud database (instead of local JSON)

🤝 Contributing

Contributions are welcome! 🎉
Feel free to fork the repo, open issues, or submit PRs to improve HackMate - CYHI Quick Teams.

📜 License

This project is licensed under the MIT License – free to use, modify, and distribute.
