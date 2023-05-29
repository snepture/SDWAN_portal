import tornado.httpclient
from module.SDWAN_Login import SDWANLogin
import yaml
config=yaml.safe_load(open('config.yaml', 'r'))


class LoginControl(object):

    login_state = 0
    login = None
    vManage_ip = None
    user_name = None
    user_passwd = None
    token = None
    cookie = None
    client = None

    def __init__(self, vManage_ip, user_name, user_passwd):

        if self.login_state == 0:
            self.login = SDWANLogin(user_name=user_name, user_passwd=user_passwd, vManage_ip=config['vManage_ip'])
            if self.login.status == 1:
                self.login_state == 1
                self.token = self.login.token
                self.cookie = self.login.cookie
                self.client = self.login.client
                self.vManage_ip = vManage_ip
                self.user_name = user_name
                self.user_passwd = user_passwd

        
    def get_token(self):
        if self.login_state:
            return self.token
        else:
            print("login error")

    def get_cookie(self):
        if self.login_state:
            return self.cookie
        else:
            print("login error")
    
    def get_client(self):
        if self.login_state:
            return self.client
        else:
            print("login error")
    