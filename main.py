import os
from github import Github, Auth
from crewai import Agent, Task, Crew, Process, LLM

# 1. BYPASS OPENAI CHECK (MANDATORY)
# CrewAI requires this env variable to exist, even if not used.
os.environ["OPENAI_API_KEY"] = "sk-dummy-key-for-internal-validation"

# 2. CONFIGURE GEMINI LLM
# Using Gemini 3 Flash for speed and free-tier compatibility
gemini_llm = LLM(
    model="gemini/gemini-1.5-flash",
    api_key=os.getenv('GEMINI_API_KEY'),
    temperature=0.7
)

# 3. UPDATED GITHUB AUTHENTICATION
# Fixing the 'login_or_token' deprecation warning
auth = Auth.Token(os.getenv('GH_TOKEN'))
g = Github(auth=auth)

repo = g.get_repo(os.getenv('GITHUB_REPOSITORY'))
pr_number = int(os.environ.get('PR_NUMBER', 1)) 
pr = repo.get_pull(pr_number)

# Fetching the code changes
diff_content = ""
for file in pr.get_files():
    diff_content += f"\nFile: {file.filename}\n{file.patch}\n"

# 4. DEFINE AGENTS (Explicitly passing Gemini LLM)
critic = Agent(
    role='Security & Quality Critic',
    goal='Identify vulnerabilities, hardcoded secrets, and logic bugs.',
    backstory='You are a Senior AppSec Engineer at SVCET. You never miss a leaked key.',
    llm=gemini_llm,
    verbose=True,
    memory=False  # Disable memory to avoid OpenAI embedding dependencies
)

architect = Agent(
    role='System Architect',
    goal='Ensure code follows clean architecture and SOLID principles.',
    backstory='You are a Lead Software Architect specializing in scalable AI systems.',
    llm=gemini_llm,
    verbose=True,
    memory=False
)

# 5. DEFINE TASKS
review_task = Task(
    description=f"Analyze these code changes:\n{diff_content}",
    expected_output="A structured report in Markdown including: 1. Security Risks 2. Architectural Improvements.",
    agent=critic
)

# 6. KICKOFF THE CREW
crew = Crew(
    agents=[critic, architect],
    tasks=[review_task],
    process=Process.sequential,
    memory=False  # Ensure global memory is also disabled
)

result = crew.kickoff()

# 7. POST FEEDBACK
pr.create_issue_comment(f"## 🤖 AI Aura: Git-CoArchitect Analysis\n\n{result}")
