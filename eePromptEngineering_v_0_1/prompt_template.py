from langchain.chat_models import ErnieBotChat
from langchain.prompts import PromptTemplate
from langchain.prompts import ChatPromptTemplate
from langchain.chains import LLMChain
from langchain.chains import LLMMathChain
from langchain.agents import Tool
from langchain.agents import initialize_agent

def read_content_from_txt(filename):  
    with open(filename, 'r',encoding='utf-8') as file:  
        code = file.read()  
    return code

code=read_content_from_txt(r'eePromptEngineering_v_0_1\test_ee_script.txt')
GCMDtheme=read_content_from_txt(r'eePromptEngineering_v_0_1\thematic_task_l1.txt')

llm = ErnieBotChat(model_name="ERNIE-Bot-4",ernie_client_id="qU735xgmPWEikqBqI8zXKEve",ernie_client_secret="PomzS3b7r8hSmTqnVpvko9iDs6djaeU1")
# llm_math = LLMMathChain(llm=llm)
prompt_template = """
You are designed to be a professional GEE developer and GIS expert. Your goal is to extract 
the required information from the given GEE workflow script according to the requirements. 
The script to be processed is as follows:
"""+str(code)+"""
The specific requirements are as follows:

1. You are required to select a keyword from the list I provided that matches the theme of the script. 
The list is as follows:
"""+str(GCMDtheme)+"""
Only one keyword should be output, in the format {"task":"Agriculture"}. 
If it's not possible to determine, the value should be Others, and the output should be 
{"task":"Others"} instead of {"task": "None"}

2. Output the time range involved in the script, in the format {"start":"YYYY-MM-DD","end":"YYYY-MM-DD"}. 
If it's not possible to determine, the value should be None, i.e., {"start": "None", "end": "None"};

3. Output the geographic location involved in the script, either as a list of place names or geographic ranges. 
If it's place names, the list should contain the names as strings, for example, {"geo-location":["Wuhan","Beijing"]}. 
If it's coordinates, the list should contain the bounding rectangle, for example, {"geo-location":[[xmin,ymin,xmax,ymax]]}.
If it's not possible to determine, the value should be None, i.e., {"geo-location": ["None"]};

4. Output the data sources involved in the script, for example, {"datasource":["LANDSAT/LC08/C01/T1_TOA","users/zzy2019110165/songhuajiangliuyu"]}. 
If it's not possible to determine, the value should be None, i.e., {"datasource": ["None"]};

5. Your response should be concise and clear, only containing the combination of required content in a list in JSON format, 
like the following example:
[{"task":"Agriculture"},{"start":"YYYY-MM-DD","end":"YYYY-MM-DD"},{"geo-location":"Wuhan;Beijing"},
{"datasource":["LANDSAT/LC08/C01/T1_TOA","users/zzy2019110165/songhuajiangliuyu"]}]
        
6. Remember! Do not include any content other than the required response in your reply. Keep the format consistent with the example.
"""

# print(final_prompt)
ret=llm.predict(prompt_template)
print(ret)
