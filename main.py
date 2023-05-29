import tornado.ioloop
from tornado.web import Application
from tornado.httpserver import HTTPServer
from tornado.options import options, define


from apis.LoginApi import LoginHandler
from apis.UserAuth import UserInfoHandler
# from apis.VPCWidgetApi import VPCWidgetApi
from apis.CloudAccountApi import CloudAccountApi
# from apis.ICGWAPI import ICGWApi
from apis.VPCConnectionAPI import VPCConnectionApi
from apis.VPCConnectionAPI import VPCAccountApi
from apis.VPCConnectionAPI import VPCCHandlerApi
from apis.VPCConnectionAPI import VPCCStateApi


define('port', default=8000, help='port listen')


if __name__ == '__main__':
    options.parse_command_line()
    handlers_routes = [
        (r'/api/v1/login', LoginHandler),
        (r'/api/v1/userinfo', UserInfoHandler),
        # (r'/api/v1/vpcwidget', VPCWidgetApi),
        (r'/api/v1/cloudaccount', CloudAccountApi),
        (r'/api/v1/vpc', VPCAccountApi),
        # (r'/api/v1/ICGWedge', ICGWApi),
        (r'/api/v1/vpc_connection', VPCConnectionApi),
        (r'/api/v1/order', VPCCHandlerApi),
        (r'/api/v1/vpcstate', VPCCStateApi)
    ]

    settings = {
        # "template_path": os.path.join(os.path.dirname(__file__), "templates"),
        "cookie_secret": "secret must be hard to guess",
        # "login_url": "/"
    }
    app = Application(handlers=handlers_routes, **settings)
    http_server = HTTPServer(app)
    http_server.listen(options.port)
    tornado.ioloop.IOLoop.current().start()
