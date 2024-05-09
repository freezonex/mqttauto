import hashlib
import hmac
import json
import os
import requests

# supOS地址
env_supos_url = os.getenv("SDK_ADDRESS")
supos_url = env_supos_url if env_supos_url is not None else "http://47.236.10.165:8080/"
# 从环境变量中获取应用的ak
env_ak = os.getenv("SUPOS_APP_ACCOUNT_ID")
# 从环境变量中获取应用的sk
env_sk = os.getenv("SUPOS_SUPOS_APP_SECRET_KEY")
# 优先从环境变量中获取aksk
app_ak = env_ak if env_ak is not None else "89421a8a5fa871a49c68a849f7afea87"
app_sk = env_sk if env_sk is not None else "cc560e6a276083d453b1f1b42ce9cbed"


class SignRequest:
    __authorize_uri = "/inter-api/auth/v1/oauth2/authorize"
    __token_uri = "/open-api/auth/v2/oauth2/token"

    def authorize(self, redirect_uri, state):
        auth_url = self.__authorize_uri + "?responseType=code&state=" + state + "&redirectUri=" + redirect_uri
        return supos_url + auth_url

    def access_token(self, access_code, logout_url):
        token_dict = {'grantType': 'authorization_code', 'code': access_code, 'logoutUri': logout_url}
        return self.post(self.__token_uri, token_dict)

    def get(self, open_api_uri, query_params):
        return self.__do_request(open_api_uri, "GET", query_params, None)

    def post(self, open_api_uri, request_body):
        return self.__do_request(open_api_uri, "POST", None, request_body)

    def put(self, open_api_uri, request_body):
        return self.__do_request(open_api_uri, "PUT", None, request_body)

    def delete(self, open_api_uri, query_params):
        return self.__do_request(open_api_uri, "DELETE", query_params, None)

    def __do_request(self, api_url, method_name, query_dict, request_dict):
        headers = {"Content-Type": 'application/json;charset=utf-8'}
        whole_url = supos_url + api_url
        self.__sign_header(api_url, method_name, query_dict, headers)
        response = None
        if "GET" == method_name:
            response = requests.get(url=whole_url, params=self.__dict_to_query(query_dict), headers=headers)
        elif "POST" == method_name:
            response = requests.post(url=whole_url, data=json.dumps(request_dict, ensure_ascii=False).encode('utf-8'),
                                     headers=headers)
        elif "PUT" == method_name:
            response = requests.put(url=whole_url, data=json.dumps(request_dict, ensure_ascii=False).encode('utf-8'),
                                    headers=headers)
        elif "DELETE" == method_name:
            response = requests.delete(url=whole_url, headers=headers)
        response.encoding = 'utf-8'
        print("请求返回结果：" + response.text)
        return response

    # 查询参数 将K进行字母小写处理，并按照字母序（ASCLL码序）进行排序。
    @staticmethod
    def __sorted_query(query):
        if query is not None:
            res = ''
            for i in sorted(query):
                if isinstance(query[i], str):
                    res = res + i.lower() + '=' + query[i] + '&'
                else:
                    res = res + i.lower() + '=' + str(query[i]) + '&'
            return res.rstrip('&')
        return ''

    # dict 转成 查询参数串
    @staticmethod
    def __dict_to_query(query):
        if query is not None:
            res = ''
            for i in sorted(query):
                if isinstance(query[i], str):
                    res = res + i + '=' + query[i] + '&'
                else:
                    res = res + i + '=' + str(query[i]) + '&'
            return res.rstrip('&')
        return ''

    # 拼接签名源
    def __build_sign_str(self, uri, method_name, query_params, header_map):
        sign_str = ''
        # HTTP Schema
        sign_str = sign_str + method_name + "\n"
        # HTTP URI
        sign_str = sign_str + uri + "\n"
        # HTTP ContentType
        sign_str = sign_str + header_map['Content-Type'] + "\n"
        # CanonicalQueryString
        sign_str = sign_str + self.__sorted_query(query_params) + "\n" + "\n"
        return sign_str

    # 生成签名并写入请求头
    def __sign_header(self, uri, method_name, query_params, header_map):
        sign_str = self.__build_sign_str(uri, method_name, query_params, header_map)
        print("签名源内容：========开始======>>\n" + sign_str)
        signature = hmac.new(app_sk.encode('utf-8'), sign_str.encode('utf-8'), digestmod=hashlib.sha256).hexdigest()
        final_signature = "Sign " + app_ak + "-" + signature
        print("签名源内容：<<========结束======")
        print('签名结果：' + final_signature)
        header_map['Authorization'] = final_signature


