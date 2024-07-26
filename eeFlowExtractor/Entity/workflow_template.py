from Utils.uuid_util import UUIDUtil

## type类型用来指明当前模板用作什么类型
#  model: 当前模板表示主模板，或者是function decleration，dag为空，因为由code_snippet组合而成
#  code_snippet: 模板下的子句，通常是parent_id属于当前模板，且拥有dag
#                如果不存在dag，则说明当前snippet是[]，下面有子code snippet构成，需要遍历
#  arguments: 用作临时表示的模板，表示参数，该设置是为了避免参数中存在复杂嵌套，模板parent_id是一个Service Node

class WorkflowTemplate:
    def __init__(self, level, raw_script, ast_body, parent_id=None, init_params=[],code_snippet=None,workflow_type='model'):
        self.uuid = UUIDUtil.generate_uuid4()
        self.level = level
        self.raw_script = raw_script ## 全局的js代码
        self.ast_body = ast_body
        self.parent_id = parent_id  ## parent_id可能是一个template的id，也可能是一个节点的id，因此使用时需要判断是与谁联系
        self.init_params = init_params
        self.code_snippet=code_snippet  ## 局部供调试的js代码，表示当前片段实质解析的内容
        self.dag=[]
        self.workflow_type=workflow_type
        self.connect_id=None    ## 为function自定义函数服务，关联service和workflow_template

    def set_connect_id(self,connect_id):
        self.connect_id=connect_id

    def append_dag(self,dag):
        self.dag.append(dag)

    def set_uuid(self,new_uuid):
        self.uuid=new_uuid

    def set_parent_id(self, parent_id):
        self.parent_id=parent_id

# Code Snippet 也有可能表示一个template
# raw_scripts是整个代码的script，确保与AST中的位置一致

class CodeSnippet:
    def __init__(self, level, snippet_type, raw_script, ast_body, parent_id):
        self.uuid = UUIDUtil.generate_uuid4()
        self.level = level
        self.snippet_type = snippet_type  # complex/simple
        self.raw_script = raw_script
        self.ast_body = ast_body
        self.parent_id = parent_id