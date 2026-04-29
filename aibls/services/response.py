

class ResponseResult:
    code:int
    message:str

    def __init__(self,code:int,message:str):
        self.code = code
        self.message = message

    def __repr__(self):
        return f"<result(code={self.code}, message='{self.message}')>"

    def to_dict(self):
        return {
            "code":self.code,
            "message":self.message
        }
