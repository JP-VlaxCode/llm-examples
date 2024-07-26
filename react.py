# Script Information
## This script is based on the following repository: [vertex-ai-samples](https://github.com/jchavezar/vertex-ai-samples/blob/main/gen_ai/streamlit_website/culture_react.py).
## Purpose
#The purpose of this script is to run a prompt using the ReAct framework for simple querying with Wikipedia.


from langchain_openai import AzureChatOpenAI
import os, httpx, re
from dotenv import load_dotenv

load_dotenv()

llm = AzureChatOpenAI(
    azure_endpoint=os.environ["AZURE_OPENAI_ENDPOINT"],
    azure_deployment=os.environ["AZURE_OPENAI_DEPLOYMENT"],
    openai_api_version=os.environ["AZURE_OPENAI_VERSION"],
)

prompt = """
You run in a loop of Thought, Action, PAUSE, Observation.
At the end of the loop you output an Answer
Use Thought to describe your thoughts about the question you have been asked.
Use Action to run one of the actions available to you - then return PAUSE.
Observation will be the result of running those actions.

Your only available actions are:

wikipedia:
e.g. wikipedia: Python
Returns a summary from searching Wikipedia.

Additional Instructions:
-If you do not find the answer through the actions just say you do not know it.

Example session:

Question: What is the capital of France?
Thought: I should look up France on Wikipedia
Action: wikipedia: France
PAUSE

You will be called again with this:

Observation: France is a country. The capital is Paris.

You then output:

Answer: The capital of France is Paris    
"""

def wikipedia(q):
    return httpx.get("https://en.wikipedia.org/w/api.php", params={
        "action": "query",
        "list": "search",
        "srsearch": q,
        "format": "json"
    }).json()["query"]["search"][0]["snippet"]

known_actions = {
    "wikipedia": wikipedia
}

class Chatbot:
    def __init__(self, system=""):
        self.system = system
        self.messages = []
        
        if self.system:
            self.messages.append("Context: {}".format(system))
    
    def __call__(self, message):
        self.messages.append(message)
        result = self.execute()
        self.messages.append(result)
        return result
    
    def execute(self):
        response = llm.invoke("\n".join(self.messages))
        print("execute-resp::", response.content)
        return response.content

def separator(repit=100):
    print("-"*repit)

action_re = re.compile('^Action: (\w+): (.*)$')
answer_re = re.compile('^Answer: (.*)$')

def query(question, max_turns=5):
        i = 0
        bot = Chatbot(prompt)
        next_prompt = question
        print("next_prompt::", next_prompt)

        while i < max_turns:
            i += 1
            if i == 1:
                result = bot(f"Question: \n{next_prompt}")
            if i > 1:
                result = bot(f"\n{next_prompt}")
            separator()
            print(result)
            separator()
            actions = []
            for a in result.split("\n"):
                if action_re.match(a):
                    actions.append(action_re.match(a))
                elif answer_re.match(a):
                    print("Answer found::", result)
                    return

            if actions:
                action, action_input = actions[0].groups()
                if action not in known_actions:
                    print(":Unknow Action {}: {}".format(action, action_input))
                    raise Exception("Unknown action: {}: {}".format(action, action_input))
                print(" -- Running {} {}".format(action, action_input))
                observation = known_actions[action](action_input)
                next_prompt = "Observation: {}".format(observation)
            else:
                print(result)
                return

query("Como jugar League of Legend?")
