import os
from github import Github, Auth
from crewai import Agent, Task, Crew, Process, LLM

# 1. THE BYPASS: Satisfy the hidden check immediately
# This MUST be set before any agents are created
os.environ["OPENAI_API_KEY"] = "NA" 

# 2. CHOOSE YOUR BRAIN (Gemini or Groq)
# For Gemini:
my_llm = LLM(
    model="gemini/gemini-1.5-flash",
    api_key=os.getenv('GEMINI_API_KEY')
)

# 3. SECURE GITHUB AUTH
auth = Auth.Token(os.getenv('GH_TOKEN'))
g = Github(auth=auth)
repo = g.get_repo(os.getenv('GITHUB_REPOSITORY'))
pr_number = int(os.environ.get('PR_NUMBER', 1)) 
pr = repo.get_pull(pr_number)

# Fetch code diff
diff_content = ""
for file in pr.get_files():
    diff_content += f"\nFile: {file.filename}\n{file.patch}\n"

# 4. DEFINE AGENTS (Set memory=False)
critic = Agent(
    role='Security Critic',
    goal='Identify vulnerabilities and hardcoded secrets.',
    backstory='Senior AppSec Engineer. Expert at finding leaked keys.',
    llm=my_llm,
    verbose=True,
    memory=False  # MUST BE FALSE
)

architect = Agent(
    role='System Architect',
    goal='Ensure clean code and SOLID principles.',
    backstory='Lead Software Architect. Focuses on scalability.',
    llm=my_llm,
    verbose=True,
    memory=False  # MUST BE FALSE
)

# 5. DEFINE TASK & KICKOFF
review_task = Task(
    description=f"Analyze these changes:\n{diff_content}",
    expected_output="A Markdown report with Security and Architecture sections.",
    agent=critic
)

crew = Crew(
    agents=[critic, architect],
    tasks=[review_task],
    process=Process.sequential,
    memory=False  # MUST BE FALSE
)

result = crew.kickoff()
pr.create_issue_comment(f"## 🤖 AI Aura: Analysis\n\n{result}")
