from pydantic import BaseModel


class Request(BaseModel):
    pass


class NoRequest(Request):
    pass
