#!/usr/bin/env python

#Author: George Patterson
#Purpose: Provide a one-way gateway between mqtt and

from twisted.python import log
from twisted.application.service import Service
from twisted.internet import reactor
from twisted.internet.protocol import ClientFactory

from MQTT import MQTTProtocol

from twisted.web.server import Site
from twisted.web.resource import Resource

import sys
log.startLogging(sys.stdout)

class webMQTT(Resource):
    isLeaf = True
    """ Get the matching MQTT entries from the MessageBuffer"""
    def render_GET(self, request):
        #msg= "<html><body>%s</body></html>" % (time.ctime(),)

        result= self.processRequest(request)
        return "%s" % (result,)


    def processRequest(self, response):
        #Split the string (expecting three chunks)
        response = str(response)
        self.chunks=response.split()
        # With the second chunk (index 1), find the required element
        resource= str(self.chunks[1])[1:]



        if resource.find("?") == -1:
            # Assume that we are looking for a static file..
            print "Question mark not found:", resource

            if resource=="help.html":
                filecontents=open("/var/www/mqttajax/help.html", "r").read()
                bufstr=self._stringMessageBuffer()

                filecontents=filecontents.replace('{MessageBuffer}', bufstr)
            else:
                filecontents=open("/var/www/mqttajax/ajax.html", "r").read()

            return filecontents

        else:

            resource=resource[1:]
            if mqttMessageBuffer.has_key(resource):
                result=mqttMessageBuffer[resource]
            else:
                result="N/A"

            msg= "document.getElementById('%s').innerHTML=%s;" % (resource ,result)
            return msg

    def _stringMessageBuffer(self):
        bufstr=""
        for bufkey, bufvalue in  mqttMessageBuffer.iteritems():
            bufstr += "%s<br/>\n" % bufkey

        return bufstr


class MQTTListener(MQTTProtocol):
    pingPeriod = 60000

    def connectionMade(self):
        log.msg('MQTT Connected')
        self.connect("TwistedMQTT", keepalive=self.pingPeriod)
        # TODO: make these constants configurable
        reactor.callLater(self.pingPeriod//1000, self.pingreq)
        reactor.callLater(5, self.processMessages)

    def pingrespReceived(self):
        log.msg('Ping received from MQTT broker')
        print "DEBUG: Ping: ", mqttMessageBuffer
        reactor.callLater(self.pingPeriod//1000, self.pingreq)

    def connackReceived(self, status):
        if status == 0:
            self.subscribe("#")
        else:
            log.msg('Connecting to MQTT broker failed')

    def processMessages(self):
        #log.msg(self)
        reactor.callLater(5, self.processMessages)

    def publishReceived(self, topic, message, qos, dup, retain, messageId):
        # Received a publish on an output topic
        log.msg('RECV Topic: %s, Message: %s' % (topic, message))

        mqttMessageBuffer[topic]= message

class MQTTListenerFactory(ClientFactory):
    protocol = MQTTListener

    def __init__(self, service = None):
        self.service = service

mqttMessageBuffer = {}
topicIdx=0
messageIdx=1

mqttFactory = MQTTListenerFactory()

if __name__ == '__main__':
    #reactor.connectTCP("test.mosquitto.org", 1883, mqttFactory)
    #reactor.listenTCP(1025, )
    resource = webMQTT()
    factory = Site(resource)
    reactor.listenTCP(8880, factory)

    reactor.connectTCP("localhost", 1883, mqttFactory)
    reactor.run()
