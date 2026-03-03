import os
from github import Github, Auth
from crewai import Agent, Task, Crew, Process, LLM

# 1. THE CRITICAL BYPASS: Satisfy CrewAI's internal check immediately
# This stops the "OPENAI_API_KEY is required" error from crashing the script
os.environ["OPENAI_API_KEY"] = "NA" 

# 2. CONFIGURE GEMINI 3 FLASH
gemini_llm = LLM(
    model="gemini/gemini-1.5-flash",
    api_key=os.getenv('GEMINI_API_KEY'),
    temperature=0.7
)

# 3. SECURE GITHUB AUTH
auth = Auth.Token(os.getenv('GH_TOKEN'))
g = Github(auth=auth)
repo = g.get_repo(os.getenv('GITHUB_REPOSITORY'))
pr_number = int(os.environ.get('PR_NUMBER', 1)) 
pr = repo.get_pull(pr_number)

# Fetch the code diff
diff_content = ""
for file in pr.get_files():
    diff_content += f"\nFile: {file.filename}\n{file.patch}\n"

# 4. DEFINE AGENTS (MUST set memory=False)
critic = Agent(
    role='Security Critic',
    goal='Identify vulnerabilities and hardcoded secrets.',
    backstory='Senior AppSec Engineer at SVCET. Expert at finding leaked keys.',
    llm=gemini_llm,
    verbose=True,
    memory=False  # Required to bypass OpenAI embedding dependency
)

architect = Agent(
    role='System Architect',
    goal='Ensure clean code and SOLID principles.',
    backstory='Lead Software Architect. Focuses on scalability and logic.',
    llm=gemini_llm,
    verbose=True,
    memory=False  # Required to bypass OpenAI embedding dependency
)

# 5. DEFINE TASK
review_task = Task(
    description=f"Analyze these changes for security and logic errors:\n{diff_content}",
    expected_output="A Markdown report with Security Risks and Architecture sections.",
    agent=critic
)

# 6. KICKOFF THE CREW
crew = Crew(
    agents=[critic, architect],
    tasks=[review_task],
    process=Process.sequential,
    memory=False # Ensures global memory is disabled
)

result = crew.kickoff()

# 7. POST FEEDBACK
pr.create_issue_comment(f"## 🤖 AI Aura: Git-CoArchitect Analysis\n\n{result}")
