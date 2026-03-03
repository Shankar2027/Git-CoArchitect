import os
from github import Github
from crewai import Agent, Task, Crew, Process

# 1. AUTHENTICATION & DATA FETCHING
# This connects your script to the secrets you just saved
g = Github(os.getenv('GH_TOKEN'))
repo = g.get_repo(os.getenv('GITHUB_REPOSITORY'))
# In a real PR, GitHub Actions provides the PR number automatically
pr_number = int(os.environ.get('PR_NUMBER', 1)) 
pr = repo.get_pull(pr_number)

# Get the code changes (the "diff")
diff_content = ""
for file in pr.get_files():
    diff_content += f"\nFile: {file.filename}\n{file.patch}\n"

# 2. DEFINE THE AI AURA AGENTS
critic = Agent(
    role='Security & Quality Critic',
    goal='Identify vulnerabilities, hardcoded secrets, and logic bugs in the code changes.',
    backstory='You are a Senior Security Engineer. You are meticulous and never miss a leaked API key or a risky database query.',
    verbose=True,
    memory=True
)

architect = Agent(
    role='System Architect',
    goal='Ensure the code follows clean architecture, proper naming conventions, and SOLID principles.',
    backstory='You are a Lead Software Architect. You ensure that every piece of code is scalable, readable, and consistent with the project structure.',
    verbose=True
)

# 3. DEFINE THE TASKS
review_task = Task(
    description=f"Review the following code changes and provide actionable feedback:\n{diff_content}",
    expected_output="A structured report in Markdown including: 1. Security Risks 2. Architectural Improvements 3. Logic Bugs.",
    agent=critic # The Critic starts, then the Architect follows
)

# 4. KICKOFF THE CREW
crew = Crew(
    agents=[critic, architect],
    tasks=[review_task],
    process=Process.sequential # One agent works, then passes it to the next
)

result = crew.kickoff()

# 5. POST THE FEEDBACK BACK TO GITHUB
pr.create_issue_comment(f"## 🤖 AI Aura: Git-CoArchitect Analysis\n\n{result}")

print("Review submitted successfully!")
