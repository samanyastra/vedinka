class EmailBackend:

    def __init__(self) -> None:
        pass

    def get_auth_token(self):
        raise NotImplementedError
    
    def prepare_email(self):
        raise NotImplementedError
    
    def send(self):
        raise NotImplementedError