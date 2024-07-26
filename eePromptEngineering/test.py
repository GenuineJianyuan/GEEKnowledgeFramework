from langchain.chat_models import ErnieBotChat
from langchain.chat_models import ChatOpenAI
from prompt_template import generate_fact_info

import os


script_path = r'test_ee_script.txt'
theme_path = r'thematic_task_l1.txt'

os.environ['OPENAI_API_KEY'] = 'your key'

## use other LLMs
# llm = ErnieBotChat(model_name="ERNIE-Bot-4",ernie_client_id="",ernie_client_secret="")
## use ChatGPT
llm = ChatOpenAI(model_name="gpt-3.5-turbo",temperature=0.2)
fact_xml_save_path = r'fact.txt'
datasource_path = r'GEE_dataset.csv'

generate_fact_info(script_path, theme_path, fact_xml_save_path, datasource_path, llm = llm)