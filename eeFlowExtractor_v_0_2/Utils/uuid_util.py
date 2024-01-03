import uuid

class UUIDUtil:
    @staticmethod
    def generate_uuid1(node=None, clock_seq=None):
        """生成一个基于主机和当前时间的UUID（UUID1）"""
        return str(uuid.uuid1(node, clock_seq))

    @staticmethod
    def generate_uuid4():
        """生成一个随机的UUID（UUID4）"""
        return str(uuid.uuid4())