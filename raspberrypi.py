#!/usr/bin/python3

import sys, os
# Add relative paths for the directory where the adapter is located as well as the parent
sys.path.append(os.path.dirname(__file__))
sys.path.append(os.path.join(os.path.dirname(__file__),'../../base'))

from sofabase import sofabase, adapterbase, configbase
import devices

import math
import random
from collections import namedtuple

import json
import asyncio
import copy
import platform

class raspberrypi(sofabase):

    
    class EndpointHealth(devices.EndpointHealth):

        @property            
        def connectivity(self):
            return 'OK'


    class TemperatureSensor(devices.TemperatureSensor):

        @property            
        def temperature(self):
            return self.nativeObject['temperature']
            
        @property
        def proactivelyReported(self):
            return False


    class adapterProcess(adapterbase):
    
        def __init__(self, log=None, loop=None, dataset=None, notify=None, request=None, config=None, **kwargs):
            self.config=config
            self.dataset=dataset
            self.dataset.nativeDevices['device']={}
            self.log=log
            self.notify=notify
            self.polltime=10
            self.loop=loop
            self.inuse=False
            
        async def start(self):
            self.log.info('.. Starting Raspberry Pi monitoring')
            await self.poll_pi()

        async def poll_pi(self):
            while True:
                try:
                    #self.log.info("Polling bridge data")
                    pitemp=self.get_temperature()
                    await self.dataset.ingest({ "device" : { platform.uname()[1] : {"name": "Sofa Host", "ok": self.ok, "temperature": pitemp }}})
                    await asyncio.sleep(self.polltime)
                    
                except:
                    self.log.error('Error fetching Hue Bridge Data', exc_info=True)

        def get_temperature(self):
            try:
                temp = os.popen("vcgencmd measure_temp").readline()
                self.ok=True
                return int(temp.replace("temp=","")[:-5]) 
            except:
                self.log.error('Error fetching temperature', exc_info=True)
                self.ok=False
                return 0
            
        # Adapter Overlays that will be called from dataset
        async def addSmartDevice(self, path):
            
            #self.log.info('Path: %s' % path)
            try:
                device_id=path.split("/")[2]
                device_type=path.split("/")[1]
                endpointId="%s:%s:%s" % ("raspberrypi", "device", device_id)
                if endpointId not in self.dataset.localDevices:  # localDevices/friendlyNam                
                    nativeObject=self.dataset.nativeDevices['device'][device_id]
                    device=devices.alexaDevice('raspberrypi/device/%s' % platform.uname()[1], nativeObject['name'], displayCategories=['TEMPERATURE_SENSOR'], adapter=self)
                    device.TemperatureSensor=raspberrypi.TemperatureSensor(device=device)
                    device.EndpointHealth=raspberrypi.EndpointHealth(device=device)
                    return self.dataset.add_device(device)                    

            except:
                self.log.error('Error defining smart device', exc_info=True)
                return False


if __name__ == '__main__':
    adapter=raspberrypi(name='raspberrypi')
    adapter.start()
