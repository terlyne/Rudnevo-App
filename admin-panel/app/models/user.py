from flask_login import UserMixin

class User(UserMixin):
    def __init__(self, id: str, email: str, is_admin: bool = False):
        self.id = id
        self.email = email
        self.is_admin = is_admin
    
    @property
    def is_authenticated(self) -> bool:
        return True
    
    @property
    def is_active(self) -> bool:
        return True
    
    @property
    def is_anonymous(self) -> bool:
        return False
    
    def get_id(self) -> str:
        return str(self.id) 