import os
from github import Github, Auth
from crewai import Agent, Task, Crew, Process, LLM

# 1. THE BYPASS: Satisfy CrewAI's internal check
os.environ["OPENAI_API_KEY"] = "NA" 

# 2. CONFIGURE GROQ LLM (The New Brain)
# We use Llama 3 70B for high-quality architectural reasoning
groq_llm = LLM(
    model="groq/llama3-70b-8192",
    api_key=os.getenv('GROQ_API_KEY'),
    temperature=0.7
)

# 3. GITHUB AUTHENTICATION
auth = Auth.Token(os.getenv('GH_TOKEN'))
g = Github(auth=auth)
repo = g.get_repo(os.getenv('GITHUB_REPOSITORY'))
pr_number = int(os.environ.get('PR_NUMBER', 1)) 
pr = repo.get_pull(pr_number)

# Fetch the code diff
diff_content = ""
for file in pr.get_files():
    diff_content += f"\nFile: {file.filename}\n{file.patch}\n"

# 4. DEFINE AGENTS (Using Groq LLM)
critic = Agent(
    role='Security Critic',
    goal='Identify vulnerabilities and hardcoded secrets.',
    backstory='Senior AppSec Engineer. Expert at finding leaked keys.',
    llm=groq_llm,
    verbose=True,
    memory=False  
)

architect = Agent(
    role='System Architect',
    goal='Ensure clean code and SOLID principles.',
    backstory='Lead Software Architect. Focuses on scalability.',
    llm=groq_llm,
    verbose=True,
    memory=False
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
    memory=False 
)

result = crew.kickoff()
pr.create_issue_comment(f"## 🤖 AI Aura (Groq-Powered): Analysis\n\n{result}")
