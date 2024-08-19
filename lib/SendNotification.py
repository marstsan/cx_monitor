import requests, yaml
from .loginEncrypt import passwordEncryption



class SendNotification:
    def __init__(self, config_name):
        config = yaml.load(open('config.yaml'), Loader=yaml.FullLoader)[config_name]
        self.edge_server = config['edge_server']
        self.service_id = config['service_id']
        self.account = config['account']
        self.password = config['password']
        self.room_id_list = config['room_id']
        self.room_name = config['room_name']

        self.encrypt_password, self.rnd = passwordEncryption(self.password)

        self.s = requests.Session()

    def get_eid_token(self):
        url = f'{self.edge_server}/auth/v1/service/{self.service_id}/users/token'
        headers = {'accept': 'application/json', 'content-type': 'application/json;charset=UTF-8'}
        body = {'username': self.account, 'password': self.encrypt_password, 'grant_type': 'password', 'challenge': {'type': 'mcpwv3', 'rand': self.rnd}}
        response = self.s.post(url, headers=headers, json=body)
        eid = response.json()['result']['eid']
        token = response.json()['result']['access_token']

        return eid, token

    def send_notification(self, text):
        eid, token = self.get_eid_token()

        results = {}
        for room_id in self.room_id_list:
            url = f'{self.edge_server}/im/v1/im/events/rooms/{room_id}/message'
            headers = {'x-m800-eid': eid, 'authorization': f'bearer {token}',
                       'x-m800-dp-sendername': 'Monitor',
                       'x-m800-dp-styledtext': 'Monitor',
                       'x-m800-dp-roomname': self.room_name
                       }
            body = {'type': 1, 'text': f'{text}'}

            response = self.s.post(url, headers=headers, json=body)

            results[room_id] = response.json()

        return results

