

class BLSException(Exception):
    """
    本项目的基类异常。
    """
    code: int

    def __init__(self, code:int =-1, msg: str = "出现了错误，但是未说明具体原因。"):
        super().__init__(msg)
        self.code = code
        self.msg = msg

    def __str__(self):
        return f"<code={self.code},message={self.msg}>"