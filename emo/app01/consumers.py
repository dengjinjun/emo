from channels.generic.websocket import WebsocketConsumer
from channels.exceptions import StopConsumer

class ChatConsumer(WebsocketConsumer):
    def websocket_connect(self, message):
        # 有客户端来向后端发送websocket连接的请求时，自动触发。
        # 服务端允许和客户端创建连接。
        print('有人来连接')
        self.accept()
    def websocket_receive(self, message):
        # 浏览器基于websocket向后端发送数据，自动触发接收消息。
        print(message['text'])
        # self.send("不要回复不要回复")
        # self.close()
    def websocket_disconnect(self, message):
        #客户端与服务端断开连接时，自动触发。
        raise StopConsumer()