## 测试方法

from Utils.ast_parser import JavaScriptASTParser
from Utils.service_dag_generator import ServiceDAGGenerator
from Utils.gee_utils import GEEUtils
from Entity.service_dag import ServiceDAG
from Entity.workflow_template import WorkflowTemplate
from graphviz import Digraph
from collections import defaultdict


def find_sub_templates_by_id(all_templates,given_id):
    target_templates=[]
    for template in all_templates:
        if template.parent_id == given_id:
            target_templates.append(template)
    return target_templates  # 如果没有找到匹配的 template，返回 None

def find_template_by_service(all_templates,service):
    for template in all_templates:
        for dag_index,dag in enumerate(template.dag):
            for node in dag.nodes:
                if node.id==service.id:
                    return template,dag_index
    return None,None

def find_template_by_id(templates, given_id):
    for template in templates:
        if template.uuid == given_id:
            return template
    return None  # 如果没有找到匹配的 template，返回 None

def find_service_by_id(service_node_list, given_id):
    for service_node in service_node_list:
        if service_node.id == given_id:
            return service_node
    return None  # 如果没有找到匹配的 template，返回 None

def extract_from_script_parth(file_path):
    ast_parser = JavaScriptASTParser()
    ast = ast_parser.get_js_ast(file_path)
    if not ast['body']:
        print(ast['error'])
        return
    # 当前脚本的完整AST表示以及源码
    original_ast_node_list = ast['body']
    pure_js_file = ast_parser.get_script_without_comments(
        ast['raw'], ast['comments'])  # raw scripts to slice

    ##记录所有template，用来总结一个脚本
    all_templates=[]

    # 初始化当前代码
    main_template = WorkflowTemplate(0, pure_js_file, original_ast_node_list,None,[],pure_js_file)
    all_templates.append(main_template)
    # 待处理的模块
    template_stack = [main_template]

    ## 挖掘所有的连接关系
    while template_stack:
        cur_template = template_stack.pop()
        cur_id, cur_level, cur_raw_script = cur_template.uuid, cur_template.level,pure_js_file
        cur_ast_body = cur_template.ast_body
        
        # 遍历当前模板中的每一句表达式，返回的dag属于当前模板的dag
        for index, ast_node in enumerate(cur_ast_body):
            ## 用workflow template表示一个code snippet(当前模板中的每一句代码)
            cur_code_snippet = WorkflowTemplate(cur_level,  cur_raw_script, ast_node, cur_id,[],cur_raw_script[ast_node['start']:ast_node['end']],'code_snippet')
            all_templates.append(cur_code_snippet)
            ## 解析当前的code snippet构造DAG
            ## 会出现两种情况：（1）正常解析语句（赋值、初始化、变量声明等）；（2）包含了map()的语句，意味着arguments中存在嵌套
            ## 返回：（1）DAG类；（2）包含的Workflow Template([wt1,wt2,...])，可能为空
            generator= ServiceDAGGenerator(cur_code_snippet)
            cur_dag,cur_new_templates = generator.generate_from_expression()
            if cur_new_templates:
                template_stack.extend(cur_new_templates)
                all_templates.extend(cur_new_templates)
            if cur_dag:
                cur_code_snippet.append_dag(cur_dag)


    ## 收集当前脚本中所有实例化的服务节点
    all_service_nodes=[]
    for workflow_template in all_templates:
        if workflow_template.dag:
            for cur_dag in workflow_template.dag:
                all_service_nodes.extend(cur_dag.nodes)

    ## 为子model寻找父model
    def search_for_model_template(workflow_template,all_templates,all_service_nodes):
        cur_node=workflow_template
        ## 一个子模版不可能属于两个父模板，该关系是单一的
        ## 同理如果子模版来源于服务节点（parent_id）是服务节点，那么肯定来自于包含该服务节点的模板
        #? 情况二的服务节点的模板是不是单一的？当前find_template_by_service认为一个服务只属于一个模板下的dag
        while cur_node:
            parent_id=cur_node.parent_id
            ## cur_node 可以是template也可能是service node
            parent_node=find_template_by_id(all_templates,parent_id)
            if parent_node: ## 模板中存在该parent，说明当前模板的父节点也是模板
                if (parent_node.workflow_type=='model'):  ##这个模板就是查找的父模板
                    return parent_node
                else:
                    cur_node=parent_node  ##这个模板是code_snippet或者arguments，继续往下搜索
            else:
                ## 当前parent_node不存在于workflow template中，说明parent可能是servoce_node
                parent_service = find_service_by_id(all_service_nodes,parent_id)
                parent_node,_ = find_template_by_service(all_templates,parent_service)
                if parent_node: ## 模板中存在该parent，说明当前模板的父节点也是模板
                    if (parent_node.workflow_type=='model'):  ##这个模板就是查找的父模板
                        return parent_node
                    else:
                        cur_node=parent_node  ##这个模板是code_snippet或者arguments，继续往下搜索
                else:## 否则表明parent_id找不到，这是有问题的，返回None，跳出循环
                    cur_node=None
        return None

    def simplify_templates(all_templates):
        # 剪枝template
        removed_templates=[]
        for cur_workflow_template in all_templates:
            if cur_workflow_template.workflow_type=='arguments': # arguments类型模板之上必有code_snippet类型模板
                code_snippets=find_sub_templates_by_id(all_templates,cur_workflow_template.uuid)
                parent_service_node=find_service_by_id(all_service_nodes,cur_workflow_template.parent_id)
                removed_templates.append(cur_workflow_template)
                removed_templates.extend(code_snippets)
                if parent_service_node:
                    parent_template,dag_index=find_template_by_service(all_templates,parent_service_node)
                    if parent_template:
                        cur_parent_template_dag=parent_template.dag[dag_index]
                        for code_snippet in code_snippets:
                            if code_snippet.dag:
                                for cur_dag in code_snippet.dag:
                                    if (cur_dag.nodes):
                                        cur_parent_template_dag.nodes.extend(cur_dag.nodes)
                                        cur_parent_template_dag.add_edge(cur_dag.nodes[0],parent_service_node)
                                    if (cur_dag.edges):
                                        cur_parent_template_dag.edges.extend(cur_dag.edges)
            elif cur_workflow_template.workflow_type=='model':
                #如果不是根（level=0)脚本，需要寻找最近的model作为当前脚本的父节点
                if (cur_workflow_template.level!=0):
                    parent_model_template=search_for_model_template(cur_workflow_template,all_templates,all_service_nodes)
                    if parent_model_template:
                        cur_workflow_template.set_parent_id(parent_model_template.uuid)           
                code_snippets=find_sub_templates_by_id(all_templates,cur_workflow_template.uuid)
                removed_templates.extend(code_snippets)
                for code_snippet in code_snippets:
                    cur_workflow_template.dag.extend(code_snippet.dag)

        remaining_templates = [t for t in all_templates if t not in removed_templates]
        return remaining_templates

    def simplify_dags(all_templates):
        for cur_workflow_template in all_templates:
            if not cur_workflow_template.dag:
                continue
            for dag in cur_workflow_template.dag:
                temp_nodes=[]
                for node in dag.nodes:
                    if node.node_type=='temp_identifier':
                        temp_nodes.append(node)
                if temp_nodes: ## 待移除的节点集
                    for node in temp_nodes:
                        front_edges=dag.get_edges_by_second_node(node)
                        end_edge=dag.get_edge_by_first_node(node)
                        if front_edges and end_edge:
                            for edge in front_edges:
                                new_edge = (edge[0], end_edge[1])
                                dag.replace_edge(edge, new_edge)
                            dag.remove_edge(end_edge[0],end_edge[1])
                        elif front_edges and not end_edge:  ## 说明这个temp_identifier是根节点，一般会在function的return出现
                            dag.remove_edges(front_edges)
                    dag.remove_nodes(temp_nodes)
        return all_templates                

    def set_edges_in_order(all_templates):
        for cur_workflow_template in all_templates:
            if not cur_workflow_template.dag:
                continue
            for dag in cur_workflow_template.dag:
                # 使用字典存储每个节点的当前入边数量
                in_edge_count = defaultdict(int)
                
                # 创建新的edges列表存储带有order的三元组
                new_edges = []
                
                for edge in dag.edges:
                    source, target = edge 
                    in_edge_count[target] += 1
                    order = in_edge_count[target]
                    new_edges.append((source, target, order))
            
                # 用新的edges替换旧的edges
                dag.edges = new_edges

        return all_templates  # 根据需要可以返回处理后的模板

    def merge_dags(all_templates):
        def merge_cur_dags(dag_list):
            ## 根据名称检查当前节点是不是在给定list中
            ## 用在检查variable是否在之前已经出现
            def get_node_by_name(node_name,service_list):
                for index,cur_node in enumerate(service_list):
                    if cur_node.node_name==node_name:
                        return cur_node,index
                return None,None

            merged_dag = ServiceDAG()
            remove_nodes = []
            variable_list= []
            for i, dag in enumerate(dag_list):
                merged_dag.nodes.extend(dag.nodes)
                merged_dag.edges.extend(dag.edges)
                
                ## 查找需要替换的节点和边，例如标识符node1,node2和边(node0,node1)与(node2,node3)
                ## （1）新增连接边（node0,node3)（2）删除node1,node2这两个identifier类型的节点，3：删掉边(node0,node1)和(node2,node3)；
                ## node_type类型是variable 的节点是需要记录和最终删除的节点
                ## identifier需要根据variable记录的顺序决定绑定的node
                #?  遇到variable一般意味着是根节点，但实际上需要先解决叶子节点的赋值，否则会出错，例如a=a.func()会先修改了=左边的值
                #? 当前解决方案是用两层循环，分别操作
                for node in dag.nodes:
                    if node.node_type == 'identifier':  ## identifier的节点从variable_list找
                        # 找到与当前节点具有相同 node_name 的已存在的节点
                        node_front,_=get_node_by_name(node.node_name,variable_list)  ## 当前与identifier相连的variable节点
                        if node_front:
                            remove_nodes.append(node)
                            edge_front=merged_dag.get_edge_by_second_node(node_front) ## variable在前一条连边中是尾节点
                            edges_after=merged_dag.get_edges_by_first_node(node) ## identifier可能有多个连接关系，但作为头节点
                            if edge_front and edges_after:
                                node1=edge_front[0]
                                for edge_after in edges_after:
                                    node2=edge_after[1]
                                    merged_dag.add_edge(node1,node2,edge_after[2])
                                    merged_dag.remove_edge(edge_after[0],edge_after[1])
                                    # merged_dag.remove_node(node_after)

                for node in dag.nodes:
                    if node.node_type== 'variable':
                        variable_node, index=get_node_by_name(node.node_name,variable_list)
                        if not variable_node:   # 当前变量节点不在列表中
                            variable_list.append(node)
                        else:  ##当前节点存在，但现在又出现了，表示当前节点有更新,用当前的节点替换供后续使用；例如var a=funcA(); a=a.funcB()
                            variable_list[index]=node
                        remove_nodes.append(node)

                #? 这里强行把node_type==complex部分连接的节点上下文关系强行关联在一起，没有删除边
                ## 不记得为什么需要这一步了
                # for node in dag.nodes:
                #     if node.node_type== 'complex':
                #         edges_front=merged_dag.get_edges_by_second_node(node)
                #         edge_after=merged_dag.get_edge_by_first_node(node)
                #         if edges_front and edge_after:
                #             for edge_front in edges_front:
                #                 merged_dag.add_edge(edge_front[0],edge_after[1],edge_front[2])
                        

            for node in remove_nodes:
                remove_edges=merged_dag.get_edge_by_node(node)
                merged_dag.remove_edges(remove_edges)
                merged_dag.remove_node(node)

            ## 若此时还存在identifier，或存在eeFunction（比如function func(),后文语句调用var a=func()）可能意味着：
            #? 特殊情况：identifier表示对函数的调用，将其与代表该函数的userDefinedFunction节点相连 (暂时这么处理，没有删除掉该identifier)
            function_nodes=[]
            for node in merged_dag.nodes:
                if node.node_type=='userDefinedFunction':
                    function_nodes.append(node)
            for node in merged_dag.nodes:
                if node.node_type=='identifier' or  node.node_type=='eeFunction':
                    for function_node in function_nodes:
                        if function_node.node_name==node.node_name:
                            merged_dag.add_edge(function_node,node)
                            if node.node_type=='eeFunction':  ##当前节点实际上是自定义的函数
                                node.set_node_type('userDefinedFunction')

            return merged_dag
        
        ## 合并每一个model template中的identifier （按顺序） 
        # #? 当前没有考虑level不同的模板之间的参数传递
        for cur_workflow_template in all_templates:
        ## 当前所有workflow template应该都是model
            if  cur_workflow_template.workflow_type != 'model': ## 表示这是主template
                print('find other workflow template in current templates')
                continue
            new_model_dag=None
            dag_list = [dag for dag in cur_workflow_template.dag]
            if dag_list:
                new_model_dag=merge_cur_dags(dag_list)
            if new_model_dag:
                cur_workflow_template.dag=[new_model_dag]
        return all_templates

    ## 修剪当前的templates，把无用的剔除
    all_templates=simplify_templates(all_templates)

    ## 修剪每一个dag，修剪完成后才是合并同一个模板中的所有dag
    all_templates=simplify_dags(all_templates)

    ## 为每一个节点确定好连边传入的顺序（为当前的边增加一个属性）
    all_templates=set_edges_in_order(all_templates)

    ## 合并同一model的dag，对同一model的dag_list的identifier的处理
    all_templates=merge_dags(all_templates)

    return all_templates

def visualize(all_templates):
    ## 展示所有workflow template以及之间的关系
    dot = Digraph()
    # 所有service节点之间，即dag
    all_service_nodes=[]
    for wt in all_templates:
        if wt.dag:
            for cur_dag in wt.dag:
                for index,node in enumerate(cur_dag.nodes):
                    if node.node_type!='eeFunction':
                        continue
                    dot.node(node.id, 'node: '+str(node.node_name)+' '+node.node_type,style='filled', fillcolor='green', shape='box')
                # 添加所有的边到图中
                for edge in cur_dag.edges:
                    if edge[0].node_type!='eeFunction' or edge[1].node_type!='eeFunction':
                        continue
                    if len(edge)==3:
                        # dot.edge(str(edge[0].id), str(edge[1].id),label=str(edge[2]))
                        dot.edge(str(edge[0].id), str(edge[1].id))
                    else:
                        dot.edge(str(edge[0].id), str(edge[1].id))
                all_service_nodes.extend(cur_dag.nodes)

    ## 模板之间的关系
    ## 节点与模板之间的关系   
    # for index,wt in enumerate(all_templates):
    #     dot.node(wt.uuid, f"{wt.workflow_type}): {wt.code_snippet}",style='filled', fillcolor='brown', shape='box')

    #     if (wt.parent_id):
    #         parent_wt=find_template_by_id(all_templates,wt.parent_id)
    #         if parent_wt:
    #             dot.edge( wt.uuid,parent_wt.uuid,color='brown',label='sub template') 
    #     if (wt.connect_id):
    #         cur_service_node=find_service_by_id(all_service_nodes,wt.connect_id)
    #         dot.edge( wt.uuid,cur_service_node.id,color='red',label='refers to') 

    
    # for wt in all_templates:
    #     if wt.dag:
    #         for cur_dag in wt.dag:
    #             if cur_dag.nodes:
    #                 end_node=cur_dag.nodes[0]
    #                 dot.edge(end_node.id,wt.uuid,color='orange',label='belongs to') 

    dot.view()

all_templates=extract_from_script_parth(file_path = r"eeFlowExtractor_v_0_2\TestSet\test.txt")
# visualize(all_templates)
# 使用GEE_Utils类
gee_utils = GEEUtils()
gee_utils.load_gee_apis("eeFlowExtractor_v_0_2\EE_API\GEE_APIs.csv")
gee_utils.load_gee_params("eeFlowExtractor_v_0_2\EE_API\GEE_Params.csv")

#? 记录service_node之间关系、workflow_template之间关系，workflow_template与service_node之间关系
def record_all_relationships(all_templates):
    node_relationships = []
    ee_relationships=[]
    template_relationships=[]
    for cur_template in all_templates:
        if cur_template.parent_id:
            template_relationships.append({"id":cur_template.uuid,"parent_id":cur_template.parent_id})
        if cur_template.dag:
            cur_template_id=cur_template.uuid
            for dag in cur_template.dag:
                if dag.edges:
                    sorted_edges_order=dag.topological_sort()
                    for edge in sorted_edges_order: 
                        node1,node2=edge[0],edge[1]
                        if len(edge)==3:
                            order=edge[2]
                        else:
                            order=1
                        node_relationships.append({"node1":node1.node_name,"node1_type":node1.node_type,"node1_id":node1.id,
                                                   "node2":node2.node_name,"node2_type":node2.node_type,"node2_id":node2.id,
                                                   "order":order,
                                                   "template_id":cur_template_id})
                        if node1.node_type=='eeFunction' and node2.node_type=='eeFunction':
                            ## 算法，获取eeFunction的全称
                            ee_relationships.append({"node1":node1.node_name,"node2":node2.node_name,"order":order})

    return template_relationships,node_relationships,ee_relationships


_,node_relationships,ee_relationships= record_all_relationships(all_templates)

from Utils.MKProcess_generator import simplify_ids,convert_nodes_to_escaped_xml_string,convert_edges_to_relationship_xml_string

simplified_json_list = simplify_ids(node_relationships)

xml_nodes_string = convert_nodes_to_escaped_xml_string(simplified_json_list)
xml_relationships_string = convert_edges_to_relationship_xml_string(simplified_json_list)

with open('Node.txt', 'w') as file:
    file.write(xml_nodes_string)

with open('Relationship.txt', 'w') as file:
    file.write(xml_relationships_string)

with open('result.txt', 'w') as file:
    for line in simplified_json_list:
        file.write(str(line) + '\n')

