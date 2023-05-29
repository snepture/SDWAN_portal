import tornado.web
import tornado.httpclient
import yaml
import asyncio
from module.Login_control import LoginControl
import json

edge_list = []


class UserBaseHandler(tornado.web.RequestHandler):
    def get_current_user(self):
        return self.get_secure_cookie("username")

class ICGWApi(UserBaseHandler):
    async def get(self):
        # Check user's validation
        if not self.current_user:
            print("Invalid login, please login again.")
            self.finish("Invalid login, please login again.")

        config = yaml.safe_load(open('config.yaml', 'r'))

        ICGW_headers = {"Content-Type":"application/json", 
                       "cookie": config['cookie'],
                       "X-XSRF-Token": config['token']}
        
        client = client = tornado.httpclient.AsyncHTTPClient()

        ICGW_url = "https://{}".format(config["vManage_ip"]) + "/dataservice/multicloud/dashboard/edge"
        ICGW_request = tornado.httpclient.HTTPRequest(ICGW_url, method="GET", headers=ICGW_headers, validate_cert=False)
        try:
            ICGW_response = await client.fetch(ICGW_request)
            if ICGW_response.code == 200:
                response = ICGW_response.body.decode("utf-8")
        except tornado.httpclient.HTTPError as e:
            print("Error:" + str(e))

        
        for i in json.loads(response)["data"]:
            print(json.dumps(i))
            self.write(json.dumps(i))
            edge_list.append(i["edgeGatewayName"])
        # self.write(response) 