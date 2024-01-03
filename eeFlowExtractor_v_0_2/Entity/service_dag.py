from Utils.uuid_util import UUIDUtil


## node 分四种类型：
# literal（数值型）：1,'a',0.1,-1
# complex (JS对象型) array,object,labeled({k,v},for,if)
# eeFunction（GEE对象方法型）
# userDefinedFunction（用户自定义方法型）
# identifier （标识符型）a.funcb().funcc()中的a
# variable (变量类型) 作为一种特殊的标识符，可能会在脚本上下文中重复使用或者更新，例如var a=1；或a=1
# temp_identifier (临时标识符) 表示一串尚未解析完成的表达式，例如"a.func()"
# 默认是eeFunction型
## name用来存放当前的源码
##
class ServiceNode:
    def __init__(self,node_name, node_type='eeFunction'):
        self.id=UUIDUtil.generate_uuid4()
        self.node_name=node_name
        self.node_type=node_type
        self.ee_type=None  ## 设置ee的类型，用于推测full_name

    def set_node_id(self,new_id):
        self.id=new_id
    
    def set_node_type(self, new_node_type):
        self.node_type=new_node_type

    def set_ee_type(self,ee_type):
        self.ee_type=ee_type

class ServiceDAG:
    def __init__(self):
        self.id=UUIDUtil.generate_uuid4()
        self.edges = list()  # 用于存储所有的边，每个边表示为一个元组
        self.nodes = list()  # 用于存储所有的节点

    def add_node(self,node):
        self.nodes.append(node)
    
    def add_edge(self,node1,node2,order=None):
        if (order):
            self.edges.append((node1,node2,order))
        else:
            self.edges.append((node1,node2))

    ### 单个的edge获取一般用在identifier相关的节点上
    def get_edge_by_second_node(self,second_node):
        for edge in self.edges:
            if edge[1]==second_node:
                return edge
        return None
    
    def get_edge_by_first_node(self,first_node):
        for edge in self.edges:
            if edge[0]==first_node:
                return edge
        return None
    
    
    
    ### 多个edges的获取
    def get_edges_by_second_node(self,second_node):
        target_edges=[]
        for edge in self.edges:
            if edge[1]==second_node:
               target_edges.append(edge)
        return target_edges
    
    def get_edges_by_first_node(self,first_node):
        target_edges=[]
        for edge in self.edges:
            if edge[0]==first_node:
                target_edges.append(edge)
        return target_edges
    
    def get_edge_by_node(self,node):
        target_edges=[]
        for edge in self.edges:
            if edge[0]==node or edge[1]==node:
                target_edges.append(edge)
        return target_edges
    
    def remove_edge(self,node1,node2):
        try:
             self.edges.remove((node1, node2))
        except ValueError:
            # print("The edge was not found in the list.")
            return

    def remove_node(self,node):
        try:
             self.nodes.remove(node)
        except ValueError:
            # print("The node node2 was not found in the list.")
            return

    def remove_edges(self,edges):
        try:
            for edge in edges:
                self.edges.remove(edge)
        except ValueError:
            print("The edge was not found in the list.")

    def replace_edge(self, old_edge, new_edge):
        try:
            index = self.edges.index(old_edge)
            self.edges[index] = new_edge
        except ValueError:
            print("The replacing edge was not found in the list.")
    
    def remove_nodes(self,nodes):
        try:
            for node in nodes:
                self.nodes.remove(node)
        except ValueError:
            print("The node was not found in the list.")

    def check_if_start_node(self,node):
        is_start=True
        for edge in self.edges:
            if edge[1]==node and edge[0].node_type=='eeFunction':
                is_start=False
        return is_start

    def get_ee_func_node_by_edges(self,node):
        nodes=[]
        for edge in self.edges:
            if edge[1]==node and edge[0].node_type=='eeFunction':
                nodes.append(edge[0])
        return nodes

    def topological_sort(self):
        in_degree = {node: 0 for node in self.nodes}
        for edge in self.edges:
            in_degree[edge[1]] += 1

        stack = [node for node in self.nodes if in_degree[node] == 0]
        sorted_order = []

        while stack:
            v = stack.pop()
            sorted_order.append(v)
            for edge in self.edges:
                if edge[0] == v:
                    in_degree[edge[1]] -= 1
                    if in_degree[edge[1]] == 0:
                        stack.append(edge[1])

        # 确保DAG中的所有节点都被包含在排序中
        if len(sorted_order) != len(self.nodes):
            return []

        # 从拓扑排序中生成边的顺序
        edge_order = []
        visited = set()
        for node in sorted_order:
            visited.add(node)
            for edge in self.edges:
                if edge[1] == node and edge[0] in visited:
                    # if edge[0].node_type == "eeFunction" and edge[1].node_type == "eeFunction":
                    edge_order.append(edge)

        return edge_order

        