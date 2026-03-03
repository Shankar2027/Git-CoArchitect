import os
from github import Github, Auth
from crewai import Agent, Task, Crew, Process, LLM

# 1. THE BYPASS: Satisfy CrewAI's internal OpenAI check
# This stops the "OPENAI_API_KEY is required" error immediately.
os.environ["OPENAI_API_KEY"] = "sk-dummy-key-for-bypass"

# 2. CONFIGURE GEMINI (The actual brain)
# We use Gemini 1.5 Flash for its high speed and free tier limits.
gemini_llm = LLM(
    model="gemini/gemini-1.5-flash",
    api_key=os.getenv('GEMINI_API_KEY'),
    temperature=0.7
)

# 3. UPDATED GITHUB AUTHENTICATION
# Fixing the 'login_or_token' deprecation warning.
auth = Auth.Token(os.getenv('GH_TOKEN'))
g = Github(auth=auth)

repo = g.get_repo(os.getenv('GITHUB_REPOSITORY'))
pr_number = int(os.environ.get('PR_NUMBER', 1)) 
pr = repo.get_pull(pr_number)

# Fetch the code changes (the "diff")
diff_content = ""
for file in pr.get_files():
    diff_content += f"\nFile: {file.filename}\n{file.patch}\n"

# 4. DEFINE AGENTS (Crucial: set memory=False)
# Memory in CrewAI uses OpenAI embeddings by default, so we disable it.
critic = Agent(
    role='Security Critic',
    goal='Identify vulnerabilities and hardcoded secrets in code changes.',
    backstory='You are a Senior AppSec Engineer. You find leaked keys and risky logic.',
    llm=gemini_llm,
    verbose=True,
    memory=False  
)

architect = Agent(
    role='System Architect',
    goal='Ensure code follows clean architecture and naming conventions.',
    backstory='You are a Lead Software Architect who loves SOLID principles.',
    llm=gemini_llm,
    verbose=True,
    memory=False
)

# 5. DEFINE THE TASK
review_task = Task(
    description=f"Analyze these changes for security and logic errors:\n{diff_content}",
    expected_output="A Markdown report with sections: Security Risks and Architecture Improvements.",
    agent=critic
)

# 6. KICKOFF THE CREW
crew = Crew(
    agents=[critic, architect],
    tasks=[review_task],
    process=Process.sequential,
    memory=False # Ensuring global memory is also disabled
)

result = crew.kickoff()

# 7. POST FEEDBACK BACK TO GITHUB
pr.create_issue_comment(f"## 🤖 AI Aura: Git-CoArchitect Analysis\n\n{result}")
