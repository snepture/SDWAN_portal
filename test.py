import tornado.ioloop
from tornado.web import RequestHandler, Application
from tornado.httpserver import HTTPServer
from tornado.options import options, define
import tornado.web
import tornado.httpclient
import os



define('port', default=8000, help='监听端口')


vManage_ip = "173.39.145.71"

class UserBaseHandler(tornado.web.RequestHandler):
    def get_current_user(self):
        return self.get_secure_cookie("username")

class LoginHandler(UserBaseHandler):

    auth_status = 0
    token = None

    def get(self):
         self.render("login.html")

    async def post(self):
        user_name = self.get_argument("username")
        user_passwd = self.get_argument("password")
        # self.render("****SDWAN_login.index", username=user_name, password=user_passwd)
        self.auth_status = await self.user_auth(user_name, user_passwd)

        if self.auth_status:
            self.set_secure_cookie("username", user_name)
            print("Success")
        else:
            print("Not auth")
            self.render("login.html")


    async def user_auth(self, user_name, user_passwd):
        sdwan_url = "https://{}".format(vManage_ip)
        auth_action = "/j_security_check"
        req_body = "j_username={}&j_password={}".format(user_name,user_passwd)
        req_headers={"Content-Type":"application/x-www-form-urlencoded"}
        auth_url = sdwan_url+auth_action

        client = tornado.httpclient.AsyncHTTPClient()
        auth_request = tornado.httpclient.HTTPRequest(auth_url, method="POST", headers=req_headers, body=req_body, validate_cert=False)
        print(auth_url)
        auth_response = await client.fetch(auth_request)
        print(auth_response.headers.get_list("Set-Cookie"))
        auth_cookie = auth_response.headers.get_list("Set-Cookie")
        # print(response.code)
        # print(response.buffer)
        # print(response.body)

        if auth_response.code == 200:
            if "Invalid" in str(auth_response.body):
                print("Invalid User or Password")
            else:
                print("Login success")
                token_action = "/dataservice/client/token"
                token_url = sdwan_url + token_action
                token_headers = {"Cookie": auth_cookie[0]}
                token_request = tornado.httpclient.HTTPRequest(token_url, method="GET", headers=token_headers, validate_cert=False)
                token_response = await client.fetch(token_request)
                if token_response.code == 200:
                    self.token = token_response.body.decode("utf-8")
                    print(self.token)

            return 1
        return 0


class LoginSuccessHandler(UserBaseHandler):
    @tornado.web.authenticated
    def get(self):
        name = tornado.escape.xhtml_escape(self.current_user)
        print("welcome, {}".format(name))
        return self.get_secure_cookie("")
    
class LogoutHandler(UserBaseHandler):
    def get(self):
        self.clear_cookie("username")
        self.redirect("/")


if __name__ == '__main__':
    options.parse_command_line()
    handlers_routes = [
        (r'/', LoginHandler)
    ]
    settings = {
        # "template_path": os.path.join(os.path.dirname(__file__), "templates"),
        "cookie_secret": "secret must be hard to guess",
        "login_url": "/"
    }
    app = Application(handlers=handlers_routes, **settings)
    http_server = HTTPServer(app)
    http_server.listen(options.port)
    tornado.ioloop.IOLoop.current().start()