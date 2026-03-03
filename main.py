import os
from github import Github, Auth
from crewai import Agent, Task, Crew, Process, LLM

# 1. THE CRITICAL BYPASS: This stops the OpenAI error immediately
# CrewAI checks for this variable at startup. Using "NA" prevents the crash.
os.environ["OPENAI_API_KEY"] = "NA" 

# 2. CONFIGURE GROQ LLM (The New Brain)
# We use Llama 3 70B for its high-quality reasoning and fast speed.
groq_llm = LLM(
    model="groq/llama3-70b-8192",
    api_key=os.getenv('GROQ_API_KEY'),
    temperature=0.7
)

# 3. SECURE GITHUB AUTHENTICATION
# This fixes the 'login_or_token' DeprecationWarning you saw in your logs.
auth = Auth.Token(os.getenv('GH_TOKEN'))
g = Github(auth=auth)

repo = g.get_repo(os.getenv('GITHUB_REPOSITORY'))
pr_number = int(os.environ.get('PR_NUMBER', 1)) 
pr = repo.get_pull(pr_number)

# Fetch the code changes (the "diff")
diff_content = ""
for file in pr.get_files():
    diff_content += f"\nFile: {file.filename}\n{file.patch}\n"

# 4. DEFINE AGENTS (Set memory=False to stay 100% free)
# CrewAI memory uses OpenAI by default; turning it off removes that dependency.
critic = Agent(
    role='Security Critic',
    goal='Identify vulnerabilities and hardcoded secrets in code changes.',
    backstory='Senior AppSec Engineer. Expert at finding leaked keys and risky logic.',
    llm=groq_llm,
    verbose=True,
    memory=False  
)

architect = Agent(
    role='System Architect',
    goal='Ensure code follows clean architecture and naming conventions.',
    backstory='Lead Software Architect. Expert in SOLID principles and scalability.',
    llm=groq_llm,
    verbose=True,
    memory=False
)

# 5. DEFINE THE REVIEW TASK
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
    memory=False # Disables internal OpenAI embedding calls
)

result = crew.kickoff()

# 7. POST FEEDBACK BACK TO GITHUB
pr.create_issue_comment(f"## 🤖 AI Aura (Groq-Powered): Analysis\n\n{result}")
