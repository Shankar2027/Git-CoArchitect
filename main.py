import os
from github import Github
from crewai import Agent, Task, Crew, Process, LLM

# 1. SETUP THE LLM (THE BRAIN)
# This tells CrewAI to use Gemini instead of searching for OpenAI
gemini_llm = LLM(
    model="gemini/gemini-1.5-flash",
    api_key=os.getenv('GEMINI_API_KEY')
)

# 2. AUTHENTICATION
# Using the updated GitHub authentication method
g = Github(os.getenv('GH_TOKEN'))
repo = g.get_repo(os.getenv('GITHUB_REPOSITORY'))
pr_number = int(os.environ.get('PR_NUMBER', 1)) 
pr = repo.get_pull(pr_number)

# Get the code changes
diff_content = ""
for file in pr.get_files():
    diff_content += f"\nFile: {file.filename}\n{file.patch}\n"

# 3. DEFINE THE AGENTS (Linking the Gemini LLM)
critic = Agent(
    role='Security & Quality Critic',
    goal='Identify vulnerabilities and logic bugs in code changes.',
    backstory='You are a Senior Security Engineer at SVCET. You never miss a leaked key.',
    llm=gemini_llm,  # <--- THIS IS THE FIX
    verbose=True
)

architect = Agent(
    role='System Architect',
    goal='Ensure code follows clean architecture and SOLID principles.',
    backstory='You are a Lead Software Architect specializing in AI & ML systems.',
    llm=gemini_llm,  # <--- THIS IS THE FIX
    verbose=True
)

# 4. DEFINE THE TASKS
review_task = Task(
    description=f"Review the following code changes and provide feedback:\n{diff_content}",
    expected_output="A structured report in Markdown with Security and Logic feedback.",
    agent=critic
)

# 5. KICKOFF
crew = Crew(
    agents=[critic, architect],
    tasks=[review_task],
    process=Process.sequential
)

result = crew.kickoff()

# 6. POST TO GITHUB
pr.create_issue_comment(f"## 🤖 AI Aura: Git-CoArchitect Analysis\n\n{result}")
