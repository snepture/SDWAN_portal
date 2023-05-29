import tornado.web
import tornado.httpclient
import asyncio
from module.SDWAN_Login import SDWANLogin
import yaml
import json


class UserBaseHandler(tornado.web.RequestHandler):
    def get_current_user(self):
        return self.get_secure_cookie("username")

class LoginHandler(UserBaseHandler):

    def get(self):
        self.render("login.html")

    async def post(self):
        data = json.loads(self.request.body)
        # user_name = self.get_argument("username")
        # user_passwd = self.get_argument("password")
        user_name = data["username"]
        user_passwd = data["password"]
        try:
            assert type(user_name) == str
            assert type(user_passwd) in (str, int, float)
        except Exception as e:
            self.write(json.dumps({"error": "params are not valid"}))
            return

        try:
            config = yaml.safe_load(open('config.yaml', 'r'))
        except Exception as e:
            return e
        
        SDWANLogin_obj = SDWANLogin(user_name=user_name, user_passwd=user_passwd, vManage_ip=config['vManage_ip'])
        await SDWANLogin_obj.login()
        auth_status = SDWANLogin_obj.status
        print(auth_status)
        if auth_status:
            self.set_secure_cookie("username", user_name)
            self.write({"result":"success"})
        else:
            self.write({"result":"fail","error": "Invalid Credentials"})

# class UserInfoHandler(UserBaseHandler):
#     def get(self):
#         if not self.current_user:
#             return {"name": "", "status": "invalidate"}
#         name = tornado.escape.xhtml_escape(self.current_user)
#         print("welcome, {}".format(name))
#         return {"name": name, "status": "validate"}


# class LoginSuccessHandler(UserBaseHandler):
#     @tornado.web.authenticated
#     def get(self):
#         name = tornado.escape.xhtml_escape(self.current_user)
#         print("welcome, {}".format(name))
#         return {"name": name, "status": "validate"}
    
# class LogoutHandler(UserBaseHandler):
#     def get(self):
#         self.clear_cookie("username")
#         self.redirect("/")



