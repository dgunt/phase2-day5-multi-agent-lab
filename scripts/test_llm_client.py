from dotenv import load_dotenv

from multi_agent_research_lab.services.llm_client import LLMClient

load_dotenv()

client = LLMClient()
response = client.complete(
    system_prompt="You are a concise assistant.",
    user_prompt="Say hello in one short sentence.",
)

print(response.content)
print("input_tokens:", response.input_tokens)
print("output_tokens:", response.output_tokens)