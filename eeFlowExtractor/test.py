from Utils.workflow_generator import generate_process_info, generate_source_code_info, generate_mapping_info
    
## 全部使用绝对路径
GEE_API_Path = r"EE_API\GEE_APIs.csv"
GEE_Parameter_path = r'EE_API\GEE_Params.csv'
source_script_path = r'TestSet\landslide_susceptility_evaluation.txt'
origin_result_save_path = r'ResultSet\origin.txt'
node_xml_save_path = r'ResultSet\Node.txt'
edge_xml_save_path = r'ResultSet\Relationship.txt'
source_code_xml_save_path = r'ResultSet\SourceCode.txt'
mapping_xml_save_path = r'ResultSet\Mapping.txt'

isSucceed = generate_process_info(GEE_API_Path, GEE_Parameter_path, source_script_path, origin_result_save_path, node_xml_save_path, edge_xml_save_path,source_code_xml_save_path,mapping_xml_save_path)
if isSucceed:
    print(f'Succeed to save XML info')
else:
    print(f'Fail to save nodes and edges, check path settings and try again!')

