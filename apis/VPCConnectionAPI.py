import tornado.web
import tornado.httpclient
import yaml
import asyncio
from module.Login_control import LoginControl
import json

account_list = []
mapping_list = []
name_id_dict = {}
id_name_dict = {}

name_mapping_dict = {"VPN10": "studio1-vpn10",
                     "VPN20": "studio1-vpn20",
                     "Tag-TenantA-USwest-1": "Tag-TenantA-USwest-1",
                     "Tag-TenantB-USwest-1": "Tag-TenantB-USwest-1"}

class UserBaseHandler(tornado.web.RequestHandler):
    def get_current_user(self):
        return self.get_secure_cookie("username")

class VPCAccountApi(UserBaseHandler):
    async def get(self):
        # Check user's validation
        if not self.current_user:
            print("Invalid login, please login again.")
            self.finish("Invalid login, please login again.")

        config = yaml.safe_load(open('config.yaml', 'r'))

        VPCC_headers = {"Content-Type":"application/json", 
                       "cookie": config['cookie'],
                       "X-XSRF-Token": config['token']}
        
        client = tornado.httpclient.AsyncHTTPClient()

        VPCC_TC_url = "https://{}".format(config["vManage_ip"]) + "/dataservice/multicloud/map/vpns?cloudType=AWS"
        VPCC_TC_request = tornado.httpclient.HTTPRequest(VPCC_TC_url, method="GET", headers=VPCC_headers, validate_cert=False)
        try:
            VPCC_TC_response = await client.fetch(VPCC_TC_request)
            if VPCC_TC_response.code == 200:
                TC_response = VPCC_TC_response.body.decode("utf-8")
        except tornado.httpclient.HTTPError as e:
            print("Error:" + str(e))
        
        for i in json.loads(TC_response)['data']:
            account = {"name": name_mapping_dict[i['segmentName']],
                       "id": i['id'],
                       "provider": 'TencentCloud'}
            account_list.append(account)
            name_id_dict[i['segmentName']] = i['id']
            id_name_dict[i['id']] = i['segmentName']
        
        VPCC_AWS_url = "https://{}".format(config["vManage_ip"]) + "/dataservice/multicloud/map/tags?cloudType=AWS"
        VPCC_AWS_request = tornado.httpclient.HTTPRequest(VPCC_AWS_url, method="GET", headers=VPCC_headers, validate_cert=False)
        try:
            VPCC_AWS_response = await client.fetch(VPCC_AWS_request)
            if VPCC_AWS_response.code == 200:
                AWS_response = VPCC_AWS_response.body.decode("utf-8")
        except tornado.httpclient.HTTPError as e:
            print("Error:" + str(e))
        
        for j in json.loads(AWS_response)['data']:
            account = {"name": name_mapping_dict[j['tag']],
                       "id": '{}'.format(bytes(j['tag'],'UTF-8').hex()),
                       "provider": 'AWS'}
            
            account_list.append(account)
            name_id_dict[j['tag']] = '{}'.format(bytes(j['tag'],'UTF-8').hex())
            id_name_dict['{}'.format(bytes(j['tag'],'UTF-8').hex())] = j['tag']

        if account_list:
            # print(account_list)
            self.write(json.dumps(account_list))
            account_list.clear()


class VPCConnectionApi(UserBaseHandler):
    async def get(self):
        # Check user's validation
        if not self.current_user:
            print("Invalid login, please login again.")
            self.finish("Invalid login, please login again.")

        config = yaml.safe_load(open('config.yaml', 'r'))

        mapping_headers = {"Content-Type":"application/json", 
                       "cookie": config['cookie'],
                       "X-XSRF-Token": config['token']}
        
        client = tornado.httpclient.AsyncHTTPClient()

        mapping_url = "https://{}".format(config["vManage_ip"]) + "/dataservice/multicloud/map?cloudType=AWS"
        mapping_request = tornado.httpclient.HTTPRequest(mapping_url, method="GET", headers=mapping_headers, validate_cert=False)
        try:
            mapping_response = await client.fetch(mapping_request)
            if mapping_response.code == 200:
                mapping_response = mapping_response.body.decode("utf-8")
        except tornado.httpclient.HTTPError as e:
            print("Error:" + str(e))

        try:
            if not json.loads(mapping_response)['data']:
                self.write(json.dumps([]))
                return
            
            status_response = await get_status()

            for i in json.loads(mapping_response)['data']:
                flag = 0
                if i['conn'] == 'enabled':
                    if 'tag' in i['srcType']:

                        for exist in mapping_list:              #exclude the double-direction link, Asrc=Bdest and Adest=Bsrc
                            if exist['source'] == name_id_dict[str.upper(i['destType'])+i['destId']] and exist['dest'] == name_id_dict[i['srcId']]:
                                flag = 1
                        if not flag:
                            status = await self.check_status(status_response, i['srcId'],i['destType']+i['destId'])
                            mapping_list.append({'id': '{}-{}-{}'.format(bytes(i['srcId'],'UTF-8').hex(),
                                                                        bytes(i['destType'],'UTF-8').hex(),
                                                                        bytes(i['destId'],'UTF-8').hex()),
                                                'source': name_id_dict[i['srcId']],
                                                'dest': name_id_dict[str.upper(i['destType'])+i['destId']],
                                                'status': status})
                            print('4')
                    else:
                        for exist in mapping_list:
                            if exist['source'] == name_id_dict[i['destId']] and exist['dest'] == name_id_dict[(str.upper(i['srcType']) + i['srcId'])]:
                                flag = 1
                        if not flag:
                            status = await self.check_status(status_response, i['srcType']+i['srcId'],i['destId'])
                            mapping_list.append({'id': '{}-{}-{}'.format(bytes(i['srcType'],'UTF-8').hex(),
                                                                        bytes(i['srcId'],'UTF-8').hex(),
                                                                        bytes(i['destId'],'UTF-8').hex()),
                                                'source': name_id_dict[(str.upper(i['srcType']) + i['srcId'])],
                                                'dest': name_id_dict[i['destId']],
                                                'status': status})
        except Exception as e:
            print(e)

        self.write(json.dumps(mapping_list))
        mapping_list.clear()

    async def check_status(self, status_response, src, dest):

        try:
            if not json.loads(status_response)['data']:
                self.write('No mappings')
            for i in json.loads(status_response)['data']:
                if 'tag' in i['srcType'] and i['srcId'] == src and (i['destType']+i['destId']) == dest:
                    if i['mapped']:
                        return "active"
                    elif i['unmapped']:
                        return "error"
                    else:
                        return "pending"
                elif 'vpn' in i['srcType'] and (i['srcType']+i['srcId']) == src and i['destId'] == dest:
                    if i['mapped']:
                        return "active"
                    elif i['unmapped']:
                        return "error"
                    else:
                        return "pending"
        except Exception as e:
            print(e)




class VPCCHandlerApi(UserBaseHandler):
    async def post(self):
        # Check user's validation
        if not self.current_user:
            print("Invalid login, please login again.")
            self.finish("Invalid login, please login again.")

        config = yaml.safe_load(open('config.yaml', 'r'))

        data = json.loads(self.request.body)
        src_id = data['source']
        dst_id = data['dest']
        request = data['request']

        if request == "vpc_connect":
            query = "enabled"
        elif request == "vpc_disconnect":
            query = "disabled"
        else:
            self.write(json.dumps({"message":"Unknown order type"}))
        establish_body = await self.build_body(id_name_dict[src_id], id_name_dict[dst_id], query)
        print(establish_body)

        establish_body = establish_body.encode("utf-8")
        # Request headers for login post
        establish_headers={"Content-Type":"application/json", 
                       "cookie": config['cookie'],
                       "X-XSRF-Token": config['token']}
        
        client = client = tornado.httpclient.AsyncHTTPClient()

        establish_url = "https://{}".format(config["vManage_ip"]) + "/dataservice/multicloud/map?cloudType=AWS"
        establish_request = tornado.httpclient.HTTPRequest(establish_url, method="POST", body = establish_body, headers=establish_headers, validate_cert=False)
        establish_response = None
        try:
            establish_response = await client.fetch(establish_request)
            if establish_response.code == 200:
                establish_response = establish_response.body.decode("utf-8")
        except tornado.httpclient.HTTPError as e:
            print("Error:" + str(e))
        except Exception as e:
            print("Error:" + str(e))
        

        try:
            print(establish_response)
            processId = json.loads(establish_response)["id"]
            print(processId)
            self.update_processId(processId)
            self.write(json.dumps({"result":"success", "order_id": processId}))
        except Exception as e:
            print("Error:" + str(e))
            self.write(json.dumps({"result":"fail","message":"Can not process request further"}))


    async def build_body(self, src, dst, status):
        post_body = {}
        post_body["cloudType"] = "AWS"
        post_body["connMatrix"] = []
        map_status_list = {}
        if status == 'disabled':
            status_response = await get_status()
            try:
                if not json.loads(status_response)['data']:
                    self.write('No mappings')
                for i in json.loads(status_response)['data']:
                    if i['srcType']+i['srcId'] == src.replace("VPN","vpn") and i['destId'] == dst:
                        map_status_list = i
            except Exception as e:
                print(e)
        if "VPN" in src:
            if status == 'enabled':
                post_body["connMatrix"].append({"srcType": "vpn",
                                                "srcId": src.replace("VPN",""),
                                                "destType": "tag",
                                                "destId": dst,
                                                "conn": status})
                post_body["connMatrix"].append({"srcType": "tag",
                                                "srcId": dst,
                                                "destType": "vpn",
                                                "destId": src.replace("VPN",""),
                                                "conn": status})
            else:
                post_body["connMatrix"].append({"srcType": "vpn",
                                                "srcId": src.replace("VPN",""),
                                                "destType": "tag",
                                                "destId": dst,
                                                "conn": status,
                                                "mapped": map_status_list['mapped'],
                                                "unmapped": map_status_list['unmapped'],
                                                "outstandingMapping": map_status_list['outstandingMapping']})
                post_body["connMatrix"].append({"srcType": "tag",
                                                "srcId": dst,
                                                "destType": "vpn",
                                                "destId": src.replace("VPN",""),
                                                "conn": status})
            
        else:
            if status == 'enabled':
                post_body["connMatrix"].append({"srcType": "tag",
                                                "srcId": src,
                                                "destType": "vpn",
                                                "destId": dst.replace("VPN",""),
                                                "conn": status})
                post_body["connMatrix"].append({"srcType": "vpn",
                                                "srcId": dst.replace("VPN",""),
                                                "destType": "vpn",
                                                "destId": src,
                                                "conn": status})
            else:
                post_body["connMatrix"].append({"srcType": "tag",
                                                "srcId": src,
                                                "destType": "tag",
                                                "destId": dst.replace("VPN",""),
                                                "conn": status})
                post_body["connMatrix"].append({"srcType": "vpn",
                                                "srcId": dst.replace("VPN",""),
                                                "destType": "tag",
                                                "destId": src,
                                                "conn": status,
                                                "mapped": map_status_list['mapped'],
                                                "unmapped": map_status_list['unmapped'],
                                                "outstandingMapping": map_status_list['outstandingMapping']})

        return json.dumps(post_body)
    
    def update_processId(self, processId):
        try:
            with open('config.yaml', 'r') as f1:
                config = yaml.safe_load(f1)
                f1.close()
            with open('config.yaml', 'w') as f2:
                config['processId'] = processId
                yaml.dump(config,f2)
                f2.close()
        except Exception as e:
            print(e)
    
    

class VPCCStateApi(UserBaseHandler):
    async def get(self):
        # Check user's validation
        if not self.current_user:
            print("Invalid login, please login again.")
            self.finish("Invalid login, please login again.")

        config = yaml.safe_load(open('config.yaml', 'r'))

        # Request headers for login post
        state_headers={"Content-Type":"application/json", 
                       "cookie": config['cookie'],
                       "X-XSRF-Token": config['token']}
        
        client = tornado.httpclient.AsyncHTTPClient()

        processId = config['processId']
        state_url = "https://{}".format(config["vManage_ip"]) + "/dataservice/device/action/status/" + processId
        state_request = tornado.httpclient.HTTPRequest(state_url, method="GET", headers=state_headers, validate_cert=False)
        try:
            state_response = await client.fetch(state_request)
            if state_response.code == 200:
                state_response = state_response.body.decode("utf-8")
        except tornado.httpclient.HTTPError as e:
            print("Error:" + str(e))

        state = {"status": json.loads(state_response)["data"][0]["status"],
                 "activity": json.loads(state_response)["data"][0]["activity"]}

        self.write(state)


async def get_status():

    config = yaml.safe_load(open('config.yaml', 'r'))

    status_headers = {"Content-Type":"application/json", 
                       "cookie": config['cookie'],
                       "X-XSRF-Token": config['token']}
        
    client = tornado.httpclient.AsyncHTTPClient()

    status_url = "https://{}".format(config["vManage_ip"]) + "/dataservice/multicloud/map/status?cloudType=AWS"
    status_request = tornado.httpclient.HTTPRequest(status_url, method="GET", headers=status_headers, validate_cert=False)
    try:
        status_response = await client.fetch(status_request)
        if status_response.code == 200:
            status_response = status_response.body.decode("utf-8")
    except tornado.httpclient.HTTPError as e:
        print("Error:" + str(e))

    return status_response