import os
from langchain.chat_models import ErnieBotChat
from langchain.chat_models import ChatOpenAI
from main_generator import execute


#############################################################################################################################################
# Main Function for Generating GEE Templates
# This function generates and saves the XML document in the directory: demo_data/gee_template_result
#############################################################################################################################################

os.environ["http_proxy"] = "http://127.0.0.1:7890"
os.environ["https_proxy"] = "http://127.0.0.1:7890"
os.environ['OPENAI_API_KEY'] = 'Your key'

## Generate xml string for <Fact>
llm = ChatOpenAI(model_name="gpt-3.5-turbo",temperature=0.2)  ## use ChatGPT
# llm = ErnieBotChat(model_name="ERNIE-Bot-4",ernie_client_id="",ernie_client_secret="")  ## use other LLMs

theme_path = r'eePromptEngineering\thematic_task_l1.txt'
temp_save_dir = r'data\temp'
orginal_script_dir = r'data\raw_code'
template_save_dir = r'data\gee_template_result'

input_dir = set(os.listdir(orginal_script_dir))

for file_name in input_dir:
    source_script_path = os.path.join(orginal_script_dir,file_name)
    isSucceed = execute(source_script_path,theme_path,temp_save_dir,template_save_dir, llm=llm)
    if (isSucceed):
        print(f"Succeed to generate template for {source_script_path}")
    else:
        print(f"Fail to generate template for {source_script_path}")



