class ModelScript:
    def __init__(self, id, level, raw_script, model_type='general',init_params=[]):
        self.id = id  # 唯一标识符
        self.level = level  # 等级
        self.raw_script = raw_script  # 原始脚本
        self.group = []
        self.model_type=model_type
        self.init_params=init_params

    def set_group(self,group):
        self.group=group
