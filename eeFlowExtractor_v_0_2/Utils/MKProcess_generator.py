def simplify_ids(json_list):
    # 用于存储原始ID到简化ID的映射
    id_map = {}
    current_id = 1

    # 更新的JSON列表
    updated_json_list = []

    for item in json_list:
        # 对于每个项目，检查并更新node1_id和node2_id
        for node in ['node1_id', 'node2_id']:
            original_id = item[node]
            if original_id not in id_map:
                id_map[original_id] = current_id
                current_id += 1
            item[node] = id_map[original_id]
        updated_json_list.append(item)
    return updated_json_list

def escape_xml_chars(value):
    """Escapes special XML characters in a string."""
    return str(value).replace("<", "&lt;").replace(">", "&gt;")

def convert_nodes_to_escaped_xml_string(json_list):
    # 开始XML字符串
    xml_str = "<ServiceNode>\n"

    # 记录已经添加过的节点ID
    processed_ids = set()

    for item in json_list:
        for node_key in ['node1', 'node2']:
            node_id = item[node_key + '_id']
            node_type = item[node_key + '_type']
            node_value = escape_xml_chars(item[node_key])  # 转义XML特殊字符

            # 检查节点ID是否已经添加过
            if node_id not in processed_ids:
                xml_str += f'   <Node id="{node_id}" type="{node_type}">{node_value}</Node>\n'
                processed_ids.add(node_id)

    # 结束XML字符串
    xml_str += "</ServiceNode>"
    return xml_str

def convert_edges_to_relationship_xml_string(json_list):
    # 开始XML字符串
    xml_str = "<Relationship>\n"

    # 用于Relationship的ID自增
    relationship_id = 1

    for item in json_list:
        # 获取source和target节点的ID
        source_node_id = item['node1_id']
        target_node_id = item['node2_id']

        # 创建Relationship元素
        xml_str += f'   <Relation id="{relationship_id}" sourceNodeId="{source_node_id}" targetNodeId="{target_node_id}"></Relation>\n'
        relationship_id += 1

    # 结束XML字符串
    xml_str += "</Relationship>"
    return xml_str