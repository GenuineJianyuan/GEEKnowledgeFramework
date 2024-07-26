import pandas as pd

class GEEUtils:
    def __init__(self):
        self.gee_apis_df = pd.DataFrame()
        self.gee_params_df = pd.DataFrame()

    def load_gee_apis(self, filepath="GEE_APIs.csv"):
        """读取GEE_APIs.csv，并存储到self.gee_apis_df中"""
        self.gee_apis_df = pd.read_csv(filepath)

    def load_gee_params(self, filepath="GEE_Params.csv"):
        """读取GEE_Params.csv，并存储到self.gee_params_df中"""
        self.gee_params_df = pd.read_csv(filepath)

    def get_full_name_from_node_name(self, node_name):
        # 检查full_name中是否有匹配项
        full_name_match = self.gee_apis_df[self.gee_apis_df['full_name'] == node_name]
        if len(full_name_match) == 1:
            return full_name_match['full_name'].iloc[0]
        
        # 检查short_name中是否有匹配项
        short_name_match = self.gee_apis_df[self.gee_apis_df['short_name'] == node_name]
        if len(short_name_match) == 1:
            return short_name_match['full_name'].iloc[0]
        
        # 处理多个short_name匹配的情况
        if len(short_name_match) > 1:
            # 等待你提供的算法
            pass
        return None
    