import os
from github import Github, Auth
from crewai import Agent, Task, Crew, Process, LLM

# 1. THE BYPASS: Satisfy the check before it starts
os.environ["OPENAI_API_KEY"] = "NA" 

# 2. SELECT YOUR BRAIN (Using Groq as the fast alternative)
# Make sure your secret name is GROQ_API_KEY in GitHub Settings
my_llm = LLM(
    model="groq/llama3-70b-8192",
    api_key=os.getenv('GROQ_API_KEY')
)

# 3. GITHUB AUTH
auth = Auth.Token(os.getenv('GH_TOKEN'))
g = Github(auth=auth)
repo = g.get_repo(os.getenv('GITHUB_REPOSITORY'))
pr_number = int(os.environ.get('PR_NUMBER', 1)) 
pr = repo.get_pull(pr_number)

diff_content = ""
for file in pr.get_files():
    diff_content += f"\nFile: {file.filename}\n{file.patch}\n"

# 4. DEFINE AGENTS (Set memory=False)
# If memory is True, it will FORCE a search for OpenAI keys!
critic = Agent(
    role='Security Critic',
    goal='Find leaked keys and bugs.',
    backstory='Senior Engineer at SVCET.',
    llm=my_llm,
    verbose=True,
    memory=False  # CRITICAL: MUST BE FALSE
)

architect = Agent(
    role='System Architect',
    goal='Ensure clean code.',
    backstory='Lead Architect.',
    llm=my_llm,
    verbose=True,
    memory=False  # CRITICAL: MUST BE FALSE
)

# 5. KICKOFF
crew = Crew(
    agents=[critic, architect],
    tasks=[Task(description=f"Review:\n{diff_content}", expected_output="Report", agent=critic)],
    process=Process.sequential,
    memory=False  # CRITICAL: MUST BE FALSE
)

result = crew.kickoff()
pr.create_issue_comment(f"## 🤖 AI Aura Analysis\n\n{result}")
