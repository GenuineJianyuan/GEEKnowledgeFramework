import sys
# Set directionary path to import package
directories = [r'eeFlowExtractor', r'eePromptEngineering']
for directory in directories:
    # 将目录添加到sys.path中
    if directory not in sys.path:
        sys.path.append(directory)


from eePromptEngineering.prompt_template import generate_fact_info
from eeFlowExtractor.Utils.workflow_generator import generate_process_info
import os
from langchain.chat_models import ErnieBotChat
from langchain.chat_models import ChatOpenAI

def execute(source_script_path, theme_path, temp_save_dir, template_save_dir, llm = None):
    try:
        filename_without_extension = os.path.splitext(os.path.basename(source_script_path))[0]

        GEE_API_Path = r"eeFlowExtractor\EE_API\GEE_APIs.csv"
        GEE_Parameter_path = r'eeFlowExtractor\EE_API\GEE_Params.csv'
        datasource_path = r'eePromptEngineering\GEE_dataset.csv'

        origin_result_save_path = os.path.join(temp_save_dir,filename_without_extension,'origin.txt')
        node_xml_save_path = os.path.join(temp_save_dir,filename_without_extension,'Node.txt')
        edge_xml_save_path = os.path.join(temp_save_dir,filename_without_extension,'Relationship.txt')
        source_code_xml_save_path = os.path.join(temp_save_dir,filename_without_extension,'SourceCode.txt')
        mapping_xml_save_path = os.path.join(temp_save_dir,filename_without_extension,'Mapping.txt')
        fact_xml_save_path = os.path.join(temp_save_dir,filename_without_extension,'Fact.txt')
        template_save_path = os.path.join(template_save_dir,filename_without_extension+'.xml')

        os.makedirs(os.path.join(temp_save_dir,filename_without_extension), exist_ok=True)

        isSucceed1 = generate_fact_info(source_script_path, theme_path, fact_xml_save_path, datasource_path, llm=llm)
        if not isSucceed1:
            print(f'Fail to save info, check path settings and try again!')

        ## Generate xml string for <ServiceNode>, <Relationship>, <SourceCode>, <Mapping>
        isSucceed2 = generate_process_info(GEE_API_Path, GEE_Parameter_path, source_script_path, origin_result_save_path, node_xml_save_path, edge_xml_save_path,source_code_xml_save_path,mapping_xml_save_path)
        if isSucceed2:
            print(f'Succeed to save XML info')
        else:
            print(f'Fail to save info, check path settings and try again!')

        if isSucceed1 and isSucceed2:
            filename_without_extension = os.path.splitext(os.path.basename(source_script_path))[0]
            template_xml = f'<GEEModelingKnowledgeTemplate name="{filename_without_extension}" description="">\n'
            template_xml += ' <!-- Modeling Knowledge Expression Module -->\n'
            template_xml += '<ModelingKnowledge>\n'
            template_xml += '<!-- Descriptive Modeling Knowledge -->\n'
            with open(fact_xml_save_path, 'r') as f:
                fact_xml = f.read()
            template_xml += f'{fact_xml}\n'
            template_xml += ' <!-- Procedural Modeling Knowledge -->\n'
            template_xml += '<Process>\n'
            with open(node_xml_save_path, 'r') as f:
                node_xml = f.read()
            template_xml += f'{node_xml}\n'
            with open(edge_xml_save_path, 'r') as f:
                edge_xml = f.read()
            template_xml += f'{edge_xml}\n'
            template_xml += '</Process>\n'
            template_xml += '</ModelingKnowledge>\n'
            template_xml += '<!-- GEE Workflow Script Copy Module -->\n'
            with open(source_code_xml_save_path, 'r') as f:
                source_code_xml = f.read()
            template_xml += f'{source_code_xml}\n'
            template_xml += '<!-- Mapping Module -->\n'
            with open(mapping_xml_save_path, 'r') as f:
                mapping_xml = f.read()
            template_xml += f'{mapping_xml}\n'
            template_xml += '</GEEModelingKnowledgeTemplate>\n'

            with open(template_save_path,'w',encoding='utf-8') as f:
                f.write(template_xml)

            return True
        else:
            return False
    except Exception as e:
        print(e)
        return False