import tornado.web
import tornado.httpclient
import tornado.escape

class UserBaseHandler(tornado.web.RequestHandler):
    def get_current_user(self):
        return self.get_secure_cookie("username")

class UserInfoHandler(UserBaseHandler):
    def get(self):
        if not self.current_user:
            self.set_status(401)
            self.finish({"name": "", "status": "invalid"})
        name = tornado.escape.xhtml_escape(self.current_user)
        print("welcome, {}".format(name))
        self.write({"name": name, "status": "valid"}) 


# class LoginSuccessHandler(UserBaseHandler):
#     @tornado.web.authenticated
#     def get(self):
#         name = tornado.escape.xhtml_escape(self.current_user)
#         print("welcome, {}".format(name))
# #         return {"name": name, "status": "validate"}
    
# class LogoutHandler(UserBaseHandler):
#     def get(self):
#         self.clear_cookie("username")
#         self.redirect("/")

        