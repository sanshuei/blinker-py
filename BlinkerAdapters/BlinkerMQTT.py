# -*- coding: utf-8 -*-

import requests
import paho.mqtt.client as mqtt
from Blinker.BlinkerConfig import *
from Blinker.BlinkerDebug import *
from BlinkerUtility import *


class MQTTProtocol(object):
    host = ''
    port = ''
    subtopic = ''
    pubtopic = ''
    deviceName = ''
    clientID = ''
    userName = ''
    password = ''
    uuid = ''
    msgBuf = ''
    isRead = False
    state = CONNECTING
    isAlive = False
    printTime = 0
    kaTime = 0
    debug = BLINKER_DEBUG
    sendTime = 0


class BlinkerMQTT(MQTTProtocol):
    """ """

    def isDebugAll(self):
        if self.debug == BLINKER_DEBUG_ALL:
            return True
        else:
            return False

    def checkKA(self):
        if self.isAlive is False:
            return False
        if (millis() - self.kaTime) < BLINKER_MQTT_KEEPALIVE:
            return True
        else:
            self.isAlive = False
            return False

    def checkCanPrint(self):
        if self.checkKA() is False:
            BLINKER_ERR_LOG("MQTT NOT ALIVE OR MSG LIMIT")
            return False
        if (millis() - self.printTime) >= BLINKER_MQTT_MSG_LIMIT or self.printTime == 0:
            return True
        BLINKER_ERR_LOG("MQTT NOT ALIVE OR MSG LIMIT")
        return False

    def checkCanSend(self):
        if (millis() - self.sendTime) >= BLINKER_SMS_MSG_LIMIT or self.sendTime == 0:
            return True
        BLINKER_ERR_LOG("MQTT NOT ALIVE OR MSG LIMIT")
        return False

    def delay10s(self):
        start = millis()
        time_run = 0
        while time_run < 10000:
            time_run = millis() - start

    def checkAuthData(self, data):
        if data['detail'] == BLINKER_CMD_NOTFOUND:
            while True:
                BLINKER_ERR_LOG("Please make sure you have put in the right AuthKey!")
                self.delay10s()

    @classmethod
    def getInfo(cls, auth):
        host = 'https://iotdev.clz.me'
        url = '/api/v1/user/device/diy/auth?authKey=' + auth

        r = requests.get(url=host + url)
        data = ''

        if r.status_code != 200:
            BLINKER_ERR_LOG('Device Auth Error!')
            return
        else:
            data = r.json()
            cls().checkAuthData(data)
            if cls().isDebugAll() is True:
                BLINKER_LOG('Device Auth Data: ', data)

        deviceName = data['detail']['deviceName']
        iotId = data['detail']['iotId']
        iotToken = data['detail']['iotToken']
        productKey = data['detail']['productKey']
        uuid = data['detail']['uuid']
        broker = data['detail']['broker']

        bmt = cls()

        if bmt.isDebugAll() is True:
            BLINKER_LOG('deviceName: ', deviceName)
            BLINKER_LOG('iotId: ', iotId)
            BLINKER_LOG('iotToken: ', iotToken)
            BLINKER_LOG('productKey: ', productKey)
            BLINKER_LOG('uuid: ', uuid)
            BLINKER_LOG('broker: ', broker)

        if broker == 'aliyun':
            bmt.host = BLINKER_MQTT_ALIYUN_HOST
            bmt.port = BLINKER_MQTT_ALIYUN_PORT
            bmt.subtopic = '/' + productKey + '/' + deviceName + '/r'
            bmt.pubtopic = '/' + productKey + '/' + deviceName + '/s'
            bmt.clientID = deviceName
            bmt.userName = iotId
        elif broker == 'qcloud':
            bmt.host = BLINKER_MQTT_QCLOUD_HOST
            bmt.port = BLINKER_MQTT_QCLOUD_PORT
            bmt.subtopic = productKey + '/' + deviceName + '/r'
            bmt.pubtopic = productKey + '/' + deviceName + '/s'
            bmt.clientID = productKey + deviceName
            bmt.userName = bmt.clientID + ';' + iotId

        bmt.deviceName = deviceName
        bmt.password = iotToken
        bmt.uuid = uuid

        if bmt.isDebugAll() is True:
            BLINKER_LOG('clientID: ', bmt.clientID)
            BLINKER_LOG('userName: ', bmt.userName)
            BLINKER_LOG('password: ', bmt.password)
            BLINKER_LOG('subtopic: ', bmt.subtopic)
            BLINKER_LOG('pubtopic: ', bmt.pubtopic)

        return bmt


class MQTTClient():
    def __init__(self):
        self.auth = ''
        self._isClosed = False
        self.client = None
        self.bmqtt = None

    def on_connect(self, client, userdata, flags, rc):
        if self.bmqtt.isDebugAll() is True:
            BLINKER_LOG('Connected with result code ' + str(rc))
        if rc == 0:
            self.bmqtt.state = CONNECTED
            BLINKER_LOG("MQTT connected")
        else:
            BLINKER_ERR_LOG("MQTT Disconnected")
            return
        client.subscribe(self.bmqtt.subtopic)

    def on_message(self, client, userdata, msg):
        if self.bmqtt.isDebugAll() is True:
            BLINKER_LOG('Subscribe topic: ', msg.topic)
            BLINKER_LOG('payload: ', msg.payload)
        data = msg.payload
        data = data.decode('utf-8')
        # BLINKER_LOG('data: ', data)
        data = json.loads(data)
        data = data['data']
        data = json.dumps(data)
        self.bmqtt.msgBuf = data
        self.bmqtt.isRead = True
        self.bmqtt.isAlive = True
        self.bmqtt.kaTime = millis()

    def start(self, auth):
        self.auth = auth
        self.bmqtt = BlinkerMQTT.getInfo(auth)
        self.client = mqtt.Client(client_id=self.bmqtt.clientID)
        self.client.username_pw_set(self.bmqtt.userName, self.bmqtt.password)
        self.client.on_connect = self.on_connect
        self.client.on_message = self.on_message
        self.client.connect(self.bmqtt.host, self.bmqtt.port, 60)

    def run(self):
        self.client.loop_start()

    def stop(self):
        self.client.loop_stop()

    def pub(self, msg, state=False):
        if state is False:
            if self.bmqtt.checkCanPrint() is False:
                return
        payload = {'fromDevice': self.bmqtt.deviceName, 'toDevice': self.bmqtt.uuid, 'data': msg}
        payload = json.dumps(payload)
        if self.bmqtt.isDebugAll() is True:
            BLINKER_LOG('Publish topic: ', self.bmqtt.pubtopic)
            BLINKER_LOG('payload: ', payload)
        self.client.publish(self.bmqtt.pubtopic, payload)
        self.bmqtt.printTime = millis()

    def sendSMS(self, msg):
        if self.bmqtt.checkCanSend() is False:
            return
        payload = json.dumps({'authKey': self.auth, 'msg': msg})
        response = requests.post('https://iotdev.clz.me/api/v1/user/device/sms',
                                 data=payload, headers={'Content-Type': 'application/json'})

        self.bmqtt.sendTime = millis()
        data = response.json()
        if self.bmqtt.isDebugAll() is True:
            BLINKER_LOG('response: ', data)
        if data[BLINKER_CMD_MESSAGE] != 1000:
            BLINKER_ERR_LOG(data[BLINKER_CMD_DETAIL])
