from Entity.service_dag import ServiceDAG,ServiceNode
from Entity.workflow_template import WorkflowTemplate
from Utils.uuid_util import UUIDUtil

class ServiceDAGGenerator:
    def __init__(self, code_snippet):
        self.code_snippet=code_snippet
        self.js_script = self.code_snippet.raw_script
        self.ast_body = self.code_snippet.ast_body
        self.level=self.code_snippet.level
        self.dag=ServiceDAG()
        self.templates=[]

    def generate_from_expression(self):
        cur_node=self.ast_body
        cur_raw_snippet=self.js_script[cur_node['start']:cur_node['end']]
        ## 不解析包含UI模块的语句
        # if ('ui.' in cur_raw_snippet):
        #     print(f"find UI modules from positions {cur_node['start']}:{cur_node['end']}")
        #     return self.dag,self.templates  
        if cur_node['type'] == 'VariableDeclaration':
            for declaration in cur_node['declarations']:
                # 获取变量名
                variable_name = declaration['id']['name']
                # 获取等号右边的表达式
                init = declaration['init']
                if init is None:  # 只是声明了变量，没有赋值操作，e.g. var a相当于初始化了一个node节点，但没有边
                    # print(f"Variable {variable_name} is declared without an initialization.")
                    self.dag.add_node(ServiceNode(variable_name,node_type='variable'))
                    break
                elif init['type']=='FunctionExpression':
                    ## 例如var a= function(){}的情形
                    ## 提出来特殊处理，因为该情况下，function的名字是变量名
                    ## 对于函数， 将其中的init_params和Code Snippets提取出来,把其视为一个子Workflow Template；
                    ## 产生一个类型为userDefinedFunction的节点，但没有边
                    init_params=[]
                    for identifier in init['params']:
                        init_params.append(identifier['name'])
                    cur_service_node=ServiceNode(variable_name,node_type='userDefinedFunction')
                    self.dag.add_node(cur_service_node)
                    function_template=WorkflowTemplate(self.level+1,self.js_script,init['body']['body'],cur_service_node.id,init_params=init_params,code_snippet=self.js_script[init['body']['start']:init['body']['end']])
                    ## 将自定义方法的函数模板id设置为与代表该函数的node一致，以此作为依据
                    function_template.set_connect_id(cur_service_node.id)
                    self.templates.append(function_template)
                else:
                    ## 表明当前表达式至少是var a=1; var a=b(identifier);var a=b.func(); 等常规的形式，遍历其节点
                    ## 此时，相当于等号左边的identifer是一个最终的节点，因此需要与表达式右边最终输出相连
                    last_dag_node=ServiceNode(variable_name,node_type='variable')
                    self.dag.add_node(last_dag_node)
                    self.generate_from_complex_expression(init,last_dag_node)
        elif cur_node['type'] == 'ExpressionStatement':  # 常见的为Map\Export\print这几个
            expression = cur_node['expression']
            if (expression['type']=='AssignmentExpression'):
                ## 表示重新赋值 e.g. x=a.funb()
                if (expression['left']['type']=='Identifier'):
                    variable_name=expression['left']['name']
                else:
                    #? 这是什么情形？a[1]=a[1]+1?
                    variable_name=self.js_script[expression['left']['start']:expression['left']['end']]
                last_dag_node=ServiceNode(variable_name,node_type='variable')
                self.dag.add_node(last_dag_node)
                self.generate_from_complex_expression(expression['right'],last_dag_node)
            else:    ##处理a.funb()的形式
                variable_name=self.js_script[cur_node['start']:cur_node['end']]
                last_dag_node=ServiceNode(variable_name,node_type='temp_identifier')
                self.dag.add_node(last_dag_node)
                self.generate_from_complex_expression(expression,last_dag_node)
        elif cur_node['type'] == 'FunctionDeclaration':  
            ## 对于函数，把其视为一个子Workflow Template，声明包含了function的名称
            function_name=cur_node['id']['name']
            function_dag_node=ServiceNode(function_name,node_type='userDefinedFunction')
            self.dag.add_node(function_dag_node)
            init_params=[]
            for identifier in cur_node['params']:
                init_params.append(identifier['name'])
            function_template=WorkflowTemplate(self.level+1, self.js_script, cur_node['body']['body'],function_dag_node.id,init_params=init_params,code_snippet=self.js_script[cur_node['body']['start']:cur_node['body']['end']])
            function_template.set_connect_id(function_dag_node.id)
            self.templates.append(function_template)
        elif cur_node['type'] == 'Identifier':
            self.generate_from_complex_expression(cur_node)
        elif cur_node['type'] == 'CallExpression':      # 通常在拆分后作为argument出现，否则应该是ExpressionStatement
            self.generate_from_complex_expression(cur_node)
        elif cur_node['type']=='ArrayExpression':
            ## 每一个表达式可能是一个template
            last_dag_node=ServiceNode(self.code_snippet.code_snippet,'temp_identifier')
            self.dag.add_node(last_dag_node)
            self.generate_from_array_expression(cur_node,last_dag_node)
        elif cur_node['type']=='ObjectExpression':
            self.generate_from_complex_expression(cur_node)
        elif cur_node['type']=='Literal':
            self.generate_from_complex_expression(cur_node)
        elif cur_node['type']=='FunctionExpression':
            self.split_function_expression(cur_node)
        elif cur_node['type']=='Property': ## 出现在对对象类型的解析，Property表示的是key:value对
            last_dag_node=ServiceNode(self.code_snippet.code_snippet,'temp_identifier')
            self.dag.add_node(last_dag_node)
            self.generate_from_complex_expression(cur_node['value'],last_dag_node)
        elif cur_node['type'] == 'ReturnStatement':
            self.generate_from_complex_expression(cur_node['argument'])
        elif cur_node['type']=='ForStatement':
            # print('find for statement')
            ## 对于for循环，把其视为一个子Workflow Template
            #? 目前只做最粗浅的解析,for模块名字用uuid代替
            loop_name='for '+UUIDUtil.generate_uuid4()
            loop_dag_node=ServiceNode(loop_name,node_type='complex')
            self.dag.add_node(loop_dag_node)
            #? 声明包含了for 的主体（暂未有效解决）
            init_params=[]
            if 'body' in cur_node['body']:
                self.templates.append(WorkflowTemplate(self.level , self.js_script, cur_node['body']['body'],loop_dag_node.id,init_params=init_params,code_snippet=self.js_script[cur_node['body']['start']:cur_node['body']['end']]))
            else:
                try:
                    self.templates.append(WorkflowTemplate(self.level , self.js_script, [cur_node['body']['expression']],loop_dag_node.id,init_params=init_params,code_snippet=self.js_script[cur_node['body']['start']:cur_node['body']['end']]))
                except Exception as e:
                    print ('find unsolved loop')
        #? If的当前解析逻辑很差
        elif cur_node['type']=='IfStatement':
            # print('find if statement')
            #? 目前只做最粗浅的解析,if模块名字用uuid代替
            condition_name='if '+UUIDUtil.generate_uuid4()
            init_params=[]
            for_dag_node=ServiceNode(condition_name,node_type='complex')
            self.dag.add_node(for_dag_node)
            if 'body' not in cur_node['consequent']: ##只有一个单句的if
                try:
                    self.templates.append(WorkflowTemplate(self.level , self.js_script, [cur_node['consequent']['expression']],for_dag_node.id,init_params=init_params,code_snippet=self.js_script[cur_node['consequent']['start']:cur_node['consequent']['end']],workflow_type='arguments'))                
                except Exception as e:
                    #? 例如：  
                    # if (params && !(params.image instanceof ee.Image))
                    #   throw Error('panSharpen(params): You must provide an params object with an image key.')
                    print('find unsoloved condition')
            else:
                self.templates.append(WorkflowTemplate(self.level , self.js_script, cur_node['consequent']['body'],for_dag_node.id,init_params=init_params,code_snippet=self.js_script[cur_node['consequent']['start']:cur_node['consequent']['end']],workflow_type='arguments'))

                has_alternate=True
                if not cur_node['alternate']:
                    has_alternate=False
                next_template_in_condition=cur_node
                while has_alternate:
                    next_template_in_condition=next_template_in_condition['alternate']
                    if (next_template_in_condition['type']=='IfStatement'):
                        self.templates.append(WorkflowTemplate(self.level , self.js_script, next_template_in_condition['consequent']['body']
                                ,for_dag_node.id,init_params=init_params,code_snippet=self.js_script[next_template_in_condition['consequent']['start']:next_template_in_condition['consequent']['end']],workflow_type='arguments'))
                        if not next_template_in_condition['alternate']:
                            has_alternate=False
                    elif (next_template_in_condition['type']=='BlockStatement'):
                        self.templates.append(WorkflowTemplate(self.level , self.js_script, next_template_in_condition['body']
                                ,for_dag_node.id,init_params=init_params,code_snippet=self.js_script[next_template_in_condition['start']:next_template_in_condition['end']],workflow_type='arguments'))
                        has_alternate=False
        return self.dag,self.templates         

    def generate_from_array_expression(self,ast_body,last_dag_node=None):
        cur_dag_node=ServiceNode('ee.List','eeFunction')
        self.dag.add_node(cur_dag_node)
        if (last_dag_node):
            self.dag.add_edge(cur_dag_node,last_dag_node)
        if not ast_body['elements']:
            return
        else:
            for element in ast_body['elements']:
                self.generate_from_complex_expression(element,cur_dag_node)            

    ## complex_expression意味着包含当前传入的表达式是多样化的，可能包含不同类型
    ## 如果有last_dag_node意味着存在赋值，需要将表达式输出与之相连
    def generate_from_complex_expression(self,ast_body,last_dag_node=None):
        ## function a(){return}中的ReturnStatement会出现的情况
        if not ast_body:
            return
        if ast_body['type'] == 'Literal':   
            ## e.g., var a=1
            cur_dag_node=ServiceNode(ast_body['value'],'literal')
            self.dag.add_node(cur_dag_node)
            if (last_dag_node):
                self.dag.add_edge(cur_dag_node,last_dag_node)
        elif ast_body['type'] == 'Identifier':   
            cur_dag_node=ServiceNode(ast_body['name'],'identifier')
            self.dag.add_node(cur_dag_node)
            if (last_dag_node):
                self.dag.add_edge(cur_dag_node,last_dag_node)
        elif (ast_body['type']=='ObjectExpression'):
            ## e.g., var a={"min":0,"max":1,"palette":["eee","4c009e"],"format":"png"},
            # print("parsing object expression")
            self.split_object_expression(ast_body,last_dag_node)
        elif (ast_body['type']=='ArrayExpression'):
            ## e.g., [1,2,3...]
            self.split_array_expression(ast_body,last_dag_node)
        elif (ast_body['type']=='BinaryExpression'):
             ## 加减等 c=a+b
            self.split_binary_expression(ast_body,last_dag_node)
        elif (ast_body['type']=='FunctionExpression'):  
            ## 对于variable declaration这一步已经执行，不会经过这里的处理
            self.split_function_expression(ast_body,last_dag_node)
        elif (ast_body['type']=='UnaryExpression'):  
            ## 复数，var a=-1
            self.split_unaray_expression(ast_body,last_dag_node)
        elif (ast_body['type']=='LabeledStatement'):  
            ## {key:value}的形式，和obj有点区别(暂时没发现出现过)
            self.split_labeled_statement(ast_body,last_dag_node)
        else:
            ## 最常出现的情况funcA().funcB().funcC()...
            self.split_general_expression(ast_body,last_dag_node)
        return

    def split_general_expression(self,ast_body,last_dag_node=None):
        cur_raw_snippet=self.js_script[ast_body['start']:ast_body['end']]
        ## 把表达式视为根节点
        root_node=ServiceNode(cur_raw_snippet,'temp_identifier')
        self.dag.add_node(root_node)
        if last_dag_node:
            self.dag.add_edge(root_node,last_dag_node)

        ## 解析这个表达式的具体内容（来自原本代码）
        ## (1)解析单层的表达式；（2）可能会返回参数中嵌套的其它表达式
        ## 因此返回元组：（按顺序的node序列，node对应的arguments（如果存在））
        ## 返回的service_list包含当前表达式“宽度”，最后一个节点代表表达式的输出，将其与root_node相连
        cur_service_list=self.split_one_level_expression(ast_body)
        cur_width=len(cur_service_list)
        if (cur_width==0):
            return
        elif cur_width==1:
            ## 当前表达式只有一个节点
            cur_dag_node=cur_service_list[0][0]
            self.dag.add_node(cur_dag_node)  
            self.dag.add_edge(cur_dag_node,root_node)
            ## 拆解其arguments，如果存在，把其作为一个新的workflow template拆解，level相同
            if cur_service_list[0][1]:  ##即当前节点有arguments
                ## start是第一个argument的start，end是最后一个argument的end
                start,end=cur_service_list[0][1][0]['start'],cur_service_list[0][1][-1]['end']
                self.templates.append(WorkflowTemplate(self.level,self.js_script,cur_service_list[0][1],cur_dag_node.id,[],self.js_script[start:end],'arguments'))
        else:
            ##当前表达式有若干个节点，依次连接
            cur_dag_node=root_node
            for service_node_tuple in cur_service_list:
                self.dag.add_node(service_node_tuple[0])
                self.dag.add_edge(service_node_tuple[0],cur_dag_node)
                cur_dag_node=service_node_tuple[0]
                  ## 拆解其arguments，如果存在，把其作为一个新的workflow template拆解，level相同
                if  service_node_tuple[1]:
                    start,end=service_node_tuple[1][0]['start'],service_node_tuple[1][-1]['end']
                    self.templates.append(WorkflowTemplate(self.level,self.js_script,service_node_tuple[1],cur_dag_node.id,[],self.js_script[start:end],'arguments'))


    ## 当前表达式为一个连续的sequence，横向拆分该表达式（处理一层的表达式，来自于源代码）
    ## 获取的是倒序的服务序列
    def split_one_level_expression(self,ast_body): 
        ## 代码来自于之前的版本
        expression=ast_body
        objects = []
        cur_arguments_AST=None
        while expression['type'] == 'CallExpression' or expression['type'] == 'MemberExpression' or expression['type'] == 'Identifier':
            if expression['type'] == 'MemberExpression':
                # 如果属性类型是Identifier，那么我们将其视为一个单独的对象
                if expression['property']['type'] == 'Identifier' :  #? 这里会错分eeFunction为identifier，在最终dag表示将其修正，因为不可能identifier后会再连接一个identifier
                    objects.append([expression['type'],expression['object']['type'],expression['property']['name'],cur_arguments_AST,expression['start'],expression['end']])
                    cur_arguments_AST=None  ##清空当前变量
                elif  expression['property']['type'] == 'Literal':  #? 碰到[]的这种情况（列举不清楚，待观察）
                    objects.append([expression['type'],expression['object']['type'],expression['property']['value'],None,expression['start'],expression['end']])
                expression = expression['object']
            elif expression['type'] == 'Identifier':  ## 不可能出现一个句子中出现两个a.a.func()的情况，只可能存在1个object是Identifier位于开头
                objects.append(['','Identifier',expression['name'],None,expression['start'],expression['end']])
                break
            elif expression['type'] == 'CallExpression':
                cur_arguments_AST=expression['arguments']
                expression=expression['callee']
                # 对于CallExpression，我们只关注callee
                if expression['type'] == 'Identifier': 
                    objects.append(['','Identifier',expression['name'],cur_arguments_AST,expression['start'],expression['end']])  
                    cur_arguments_AST=None  ##清空当前变量
                    break 
                
        ## object[前序AST类型(0)，当前AST类型(1)，当前变量名称(2)，arguments的AST，当且仅当object是CallExpression时(3)，否则为None，start,end（4,5）]
        service_list=[]
        ## 处理ee、Map、存在的情况（存在合并）  
        if len(objects)  ==0:
            return service_list
        if (objects[-1][2] not in  ['ee', 'Map', 'Export']):  ## 不存在使用ee.Image这样的初始化，即每一个当前的object都是“可以直接表示的eeFunction”
            for index,object in enumerate(objects):
                #? 临时方法，当前可能把表达式中的节点错误识别为identifier，例如image.clip()会把clip识别为identifier
                cur_node_type=self.get_node_type_by_AST(object[1])
                if (cur_node_type=='identifier') and (self.js_script[object[5]:object[5]+1]=='('):
                    cur_node_type='eeFunction'
                service_list.append((ServiceNode(object[2],cur_node_type),object[3]))
            return service_list    
        else:
            start=-1
            ##处理ee.Algorithm.Landsat(...)的情况，ee.Algorithm.Landsat视为一个method
            for index,object in enumerate(objects):  
                if ((object[0]=='MemberExpression' and object[1]=='Identifier') 
                        or (object[0]=='MemberExpression' and object[1]=='MemberExpression')):
                    start=index
                    break
                else:
                    cur_node_type=self.get_node_type_by_AST(object[1])
                    if (cur_node_type=='identifier') and (self.js_script[object[5]:object[5]+1]=='('):
                        cur_node_type='eeFunction'
                    service_list.append((ServiceNode(object[2],cur_node_type),object[3]))
            new_service=ServiceNode('')
            new_service_arguments=None  ##后文仅会出现一次arguments
            for i in range(start ,len(objects)):
                new_service.node_name=objects[i][2]+'.'+new_service.node_name
                if objects[i][3]:
                    new_service_arguments=objects[i][3]
            new_service.node_name=new_service.node_name[:-1]
            service_list.append((new_service,new_service_arguments))

            return service_list


    def split_object_expression(self,ast_body,last_dag_node=None):
        cur_raw_snippet=self.js_script[ast_body['start']:ast_body['end']]
        obj_node=ServiceNode(cur_raw_snippet,'complex')
        ####### 还需要解析这个obj的具体内容
        start,end=ast_body['start'],ast_body['end']
        self.templates.append(WorkflowTemplate(self.level,self.js_script,ast_body['properties'],obj_node.id,[],self.js_script[start:end],'arguments'))
        self.dag.add_node(obj_node)
        if last_dag_node:
            self.dag.add_edge(obj_node,last_dag_node)

    def split_array_expression(self,ast_body,last_dag_node=None):
        cur_raw_snippet=self.js_script[ast_body['start']:ast_body['end']]
        array_node=ServiceNode(cur_raw_snippet,'complex')
        ####### 还需要解析这个array的具体内容
        self.dag.add_node(array_node)
        if last_dag_node:
            self.dag.add_edge(array_node,last_dag_node)

    def split_binary_expression(self,ast_body,last_dag_node=None):
        cur_raw_snippet=self.js_script[ast_body['start']:ast_body['end']]
        binary_node=ServiceNode(cur_raw_snippet,'complex')
        ####### 还需要解析这个表达式的具体内容
        self.dag.add_node(binary_node)
        if last_dag_node:
            self.dag.add_edge(binary_node,last_dag_node)
    
    def split_function_expression(self,ast_body,last_dag_node=None):
        ## 这里处理的应该是map(func(){}})的情况，但这里是不存在方法名，用uuid4生成临时方法名
        init_params=[]
        ## 对于函数， 将其中的init_params和Code Snippets提取出来,把其视为一个子Workflow Template；
        for identifier in ast_body['params']:
            init_params.append(identifier['name'])
        cur_template=WorkflowTemplate(self.level+1,self.js_script,ast_body['body']['body'],self.code_snippet.uuid,init_params=init_params,code_snippet=self.js_script[ast_body['body']['start']:ast_body['body']['end']])
        
        self.templates.append(cur_template)
        ## 产生一个类型为userDefinedFunction的节点
        function_dag_node = ServiceNode(cur_template.code_snippet,node_type='userDefinedFunction')
        ## 用id与model关联，function_dag_node的id与WorkflowTemplate相同，使用时以此为依据
        function_dag_node.set_node_id(cur_template.uuid)

        cur_template.set_connect_id(cur_template.uuid)

        self.dag.add_node(function_dag_node)
        if last_dag_node:
            self.dag.add_edge(function_dag_node,last_dag_node)

    def split_unaray_expression(self,ast_body,last_dag_node=None):
        if 'raw' in ast_body['argument']: ## '-1'的形式
            unary_value='-'+ast_body['argument']['raw']
        elif 'name' in ast_body['argument']: ## '-identifier'的形式
            unary_value='-'+ast_body['argument']['name']
        else:
            unary_value=self.js_script[ast_body['start']:ast_body['end']]
        unary_node=ServiceNode(unary_value,'literal')
        ####### 还需要解析这个表达式的具体内容
        self.dag.add_node(unary_node)
        if last_dag_node:
            self.dag.add_edge(unary_node,last_dag_node)
    
    def split_labeled_statement(self,ast_body,last_dag_node=None):
        cur_raw_snippet=self.js_script[ast_body['start']:ast_body['end']]
        labeled_node=ServiceNode(cur_raw_snippet,'complex')
        ####### 还需要解析这个表达式的具体内容
        self.dag.add_node(labeled_node)
        if last_dag_node:
            self.dag.add_edge(labeled_node,last_dag_node)

    ## 判断当前子单元是不是identifier，例如a.funcb().funcc()中的a
    def get_node_type_by_AST(self,AST_type):
        if (AST_type=='Identifier'):
            return 'identifier'
        elif (AST_type=='Literal'):
            return 'literal'
        else:
            return 'eeFunction'
