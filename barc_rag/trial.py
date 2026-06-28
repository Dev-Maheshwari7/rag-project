from langchain_groq import ChatGroq
from langchain_core.messages import HumanMessage
from dotenv import load_dotenv
load_dotenv()
llm = ChatGroq(
    model="qwen/qwen3-32b",
    temperature=0,
    reasoning_format="hidden",
    reasoning_effort="none",
)

response = llm.invoke([
    HumanMessage(content="Return only: hello")
])

print(response.content)
print(response.additional_kwargs)
print(response.response_metadata)