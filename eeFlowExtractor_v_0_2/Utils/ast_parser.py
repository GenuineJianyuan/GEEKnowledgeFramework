import subprocess
import json
import os

class JavaScriptASTParser:
    def __init__(self, js_parser_script=None,error_log=None):
        if js_parser_script is None:
            current_script_path = os.path.realpath(__file__)
            # 获取当前脚本所在的目录
            current_directory = os.path.dirname(current_script_path)
            # 构造parse.js的绝对路径
            js_parser_script = os.path.join(current_directory, 'parse.js')
        self.js_parser_script = js_parser_script


    def get_js_ast(self, js_file_path):
        try:
            result = subprocess.run(['node', self.js_parser_script, js_file_path,'0'], capture_output=True, text=False,encoding='utf-8')
            if not result.stdout:
                return {'body':[]}
            return json.loads(result.stdout)
        except:
            # print('script {0} has syntax error'.format(js_file_path))
            # self.error_log.log_error(js_file_path+' unknowledge error')
            return {'body':[],'error':'script {0} has syntax error'.format(js_file_path)}
        

    # def get_js_ast_from_string(self, js_string):
    #     try:
    #         result = subprocess.run(['node', self.js_parser_script, js_string,'1'], capture_output=True, text=True, encoding='utf-8')
    #         return json.loads(result.stdout)
    #     except:
    #         return None

    # def get_js(self,js_file_path):
    #     with open(js_file_path, 'r') as file:
    #         data = file.read()
    #     return data

    def get_script_without_comments(self,origin_script,comments):
        cur_script=origin_script
        for comment in comments:
            cur_start=comment['start']
            cur_end=comment['end']
            before = cur_script[:cur_start]
            after = cur_script[cur_end :]
            spaces = ' ' * (cur_end - cur_start )

            cur_script=before + spaces + after
        return cur_script
