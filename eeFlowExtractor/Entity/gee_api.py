import pandas as pd

class GEE_API:
    def __init__(self, api_id, full_name, short_name, output_type):
        self.api_id = api_id
        self.full_name = full_name
        self.short_name = short_name
        self.output_type = output_type
        self.params = []  # 列表用于存储此API关联的参数

    def add_param(self, name, param_type, necessary):
        param = {
            "name": name,
            "type": param_type,
            "necessary": necessary
        }
        self.params.append(param)

    @classmethod
    def from_csv(cls, apis_path, params_path):
        # 从csv文件中读取数据
        apis_df = pd.read_csv(apis_path)
        params_df = pd.read_csv(params_path)

        # 创建一个空的GEE_APIs字典，键为API的ID
        api_dict = {}

        # 遍历GEE_APIs.csv，为每个API创建一个GEE_API对象
        for index, row in apis_df.iterrows():
            api_obj = cls(row['index'], row['full_name'], row['short_name'], row['output_type'])
            api_dict[row['index']] = api_obj

        # 遍历GEE_Params.csv，并将参数添加到相关的GEE_API对象中
        for index, row in params_df.iterrows():
            parent_id = row['parent_id']
            if parent_id in api_dict:
                api_dict[parent_id].add_param(row['name'], row['r_type'], row['necessary'])

        return api_dict
    
