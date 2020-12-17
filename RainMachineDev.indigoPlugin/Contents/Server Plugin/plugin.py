#! /usr/bin/env python
# -*- coding: utf-8 -*-
####################
# Rain Machine Indigo Server Plugin
#
# Copyright (c) 2018-2020 Geoff Harris
#
# All rights reserved. This program and the accompanying materials
# are made available under the terms of the Eclipse Public License v2.0
# which accompanies this distribution, and is available at
#
#
# Contributors:
# Geoff Harris
#
import time
import indigo
from client import Client


################################################################################
class Plugin(indigo.PluginBase):
################################################################################

	def __init__(self, pluginId, pluginDisplayName, pluginVersion, pluginPrefs):
		indigo.PluginBase.__init__(self, pluginId, pluginDisplayName, pluginVersion, pluginPrefs)
		self.debug = False
		self.rainmachine_accounts = {}
		self.rainmachine_devices = {}
		self.client = Client()
		self.next_update_programs = time.time()
		self.update_queue = []

################################################################################
	def __del__(self):
		indigo.PluginBase.__del__(self)

################################################################################
	def startup(self):
		self.debugLog(u"startup called")
		indigo.server.log("startup called")
		self.controllers = self.client.controllers

################################################################################
	def shutdown(self):
		self.debugLog(u"shutdown called")
		indigo.server.log("shutdown called")


################################################################################
	def deviceStartComm(self, device):

		self.debugLog("Starting device: " + device.name)
		if device.pluginProps["deviceMAC"]:
			indigo.server.log("device exists MAC: " + str(device.pluginProps["deviceMAC"]))
		else:
			indigo.server.log("new device")
		if device.id not in self.rainmachine_devices:
			indigo.server.log("Added Device id: " + str(device.id) + " to self.rainmachine_devices")
			self.mac_address = device.pluginProps["deviceMAC"]
		if device.id in self.rainmachine_devices:
			indigo.server.log("Existing Device id: " + str(device.id) + " : MAC = " + self.rainmachine_devices[device.id])
		self.rainmachine_devices[device.id] = device.pluginProps["deviceMAC"]
		#indigo.server.log("Plugin k,v: " + str(self.rainmachine_devices))
		#if device.pluginProps.has_key("connectionType"):
		#	for kd, vd in device.pluginProps.items():
		#		indigo.server.log(str(kd) + " : " + str(vd))
		indigo.server.log("Device Start Communication")
		self.user_name = device.pluginProps["username"]
		self.password = device.pluginProps["password"]
		self.connection_type = device.pluginProps["connectionType"]
		self.ip_address = device.pluginProps["ip_address"]
		self.port = device.pluginProps["port"]
		self.ssl = device.pluginProps["https"]
		self.debugLog("Started device: " + str(device.id))
		self.debugLog(str(device))
		if device.pluginProps["deviceMAC"] not in self.controllers:
			indigo.server.log("Needs to login")
			if self.connection_type == 'Local':
				self.client.load_local(self.ip_address, self.password, port=self.port, ssl=False)
			elif self.connection_type == 'Cloud':
				self.client.load_remote(self.user_name, self.password)
			else:
				indigo.server.log("No, key: does not exists in dictionary")

		self.mac_address = self.rainmachine_devices[device.id]
		self.controller = self.client.controllers[self.mac_address]
		self.program_list = self.controller.programs.all()
		self.zone_list = self.controller.zones.all()

		## Update status on server: ##
		device.updateStateImageOnServer(indigo.kStateImageSel.SensorOn)
		device.updateStateOnServer('deviceIsOnline', value=True, clearErrorState=True)

################################################################################
	def deviceStopComm(self,device):
		self.debugLog("Stopping device: " + device.name)
		indigo.server.log("Device Stop Communication")
		if device.id in self.rainmachine_devices:
			device.updateStateImageOnServer(indigo.kStateImageSel.SensorTripped)
			device.updateStateOnServer('deviceIsOnline', value=False, clearErrorState=True)
			del self.rainmachine_devices[device.id]

################################################################################
	def update(self):

		self.logger.debug("Update Called")
		if self.update_queue:
			self.debugLog("queue has update")
			deviceId = int(self.update_queue.pop(0))
			self.debugLog("device id:" + str(deviceId))

			device = indigo.devices[deviceId]
			zone_data = self.activeZone(deviceId)
			self.debugLog("device to update" + str(zone_data))
			counter = 0
			for kd in zone_data[u'zones']:
				if kd[u'state'] != 0:
					self.debugLog("zone {} is on for {} seconds".format(kd[u'name'], (kd[u'remaining'])))
					device.updateStateOnServer('zoneNumber', value=str(kd[u'name']), clearErrorState=True)
					device.updateStateOnServer('zoneMinutesLeft', value=(round(kd[u'remaining'] / 60)),
											   uiValue=(str(round(kd[u'remaining'] / 60)) + " min"),
											   clearErrorState=True)
					device.updateStateOnServer('isWatering', value='on', clearErrorState=True)
					device.updateStateImageOnServer(indigo.kStateImageSel.SprinklerOn)
					counter += 1
			if counter == 0:
				self.debugLog("no active zones")
				device.updateStateOnServer('zoneNumber', value='all off', clearErrorState=True)
				device.updateStateOnServer('zoneMinutesLeft', value=0, uiValue='0 min', clearErrorState=True)
				device.updateStateOnServer('isWatering', value='off', clearErrorState=True)
				device.updateStateImageOnServer(indigo.kStateImageSel.SensorOn)

			program_data = self.activeProgram(deviceId)
			if program_data[u'programs']:
				self.debugLog("program data : " + str(program_data))
				self.debugLog("program data available")
				for kd in program_data[u'programs']:
					device.updateStateOnServer('currentProgram', value=str(kd[u'name']), clearErrorState=True)
			else:
				device.updateStateOnServer('currentProgram', value='none', clearErrorState=True)
				self.debugLog("program data should be none")

		if time.time() > self.next_update_programs:
			counter = 0
			for key, value in self.rainmachine_devices.items():
				deviceId = key
				#deviceMAC = value
				#self.debugLog("device ID:" + str(deviceId) + " MAC : " + str(deviceMAC))
				device = indigo.devices[deviceId]

				zone_data = self.activeZone(deviceId)
				for kd in zone_data[u'zones']:
					if kd[u'state'] != 0:
						#self.debugLog("zone {} is on for {} seconds".format(kd[u'name'], (kd[u'remaining'])))
						device.updateStateOnServer('zoneNumber', value=str(kd[u'name']), clearErrorState=True)
						device.updateStateOnServer('zoneMinutesLeft', value=(round(kd[u'remaining'] / 60)),
												   uiValue=(str(round(kd[u'remaining'] / 60)) + " min"),
												   clearErrorState=True)
						device.updateStateImageOnServer(indigo.kStateImageSel.SprinklerOn)
						counter += 1
				if counter == 0:
					device.updateStateOnServer('zoneNumber', value='all off', clearErrorState=True)
					device.updateStateOnServer('zoneMinutesLeft', value='0', uiValue='0 min', clearErrorState=True)
					device.updateStateImageOnServer(indigo.kStateImageSel.SensorOn)

				program_data = self.activeProgram(deviceId)
				if program_data[u'programs']:
					self.debugLog("program data : " + str(program_data))
					for kd in program_data[u'programs']:
						device.updateStateOnServer('currentProgram', value=str(kd[u'name']), clearErrorState=True)
				else:
					device.updateStateOnServer('currentProgram', value='none', clearErrorState=True)
					self.debugLog("program data should be none: " + str(program_data))

			self.next_update_programs = time.time() + 60

################################################################################

	def runConcurrentThread(self):
		self.logger.debug(u"runConcurrentThread starting")
		try:
			while True:

				if time.time() > self.next_update_programs:
					self.update()

				self.sleep(10.0)

		except self.StopThread:
			self.logger.debug(u"runConcurrentThread ending")
			pass


	def stopConcurrentThread(self):
		self.stopThread = True
	#####################################
	############ Run Program ############
	#####################################
	def actionRunProgram(self, pluginAction):

		deviceId = int(pluginAction.props['indigo_rainmachine_controller'])
		device = indigo.devices[deviceId]
		controller = self.controllers[device.pluginProps["deviceMAC"]]
		controller.programs.start(pluginAction.props["ProgramValue"])

		self.update_queue.append(deviceId)
		self.update()

	def actionStopProgram(self, pluginAction):

		deviceId = int(pluginAction.props['indigo_rainmachine_controller'])
		device = indigo.devices[deviceId]
		controller = self.controllers[device.pluginProps["deviceMAC"]]
		controller.programs.stop(pluginAction.props["ProgramValue"])

		self.update_queue.append(deviceId)
		self.update()


	#####################################
	############ Run Zones ############
	#####################################
	def actionRunZones(self, pluginAction):

		deviceId = int(pluginAction.props['indigo_rainmachine_controller'])
		device = indigo.devices[int(pluginAction.props['indigo_rainmachine_controller'])]
		controller = self.controllers[device.pluginProps["deviceMAC"]]
		controller.zones.start(pluginAction.props["ZoneValue"], pluginAction.props["zoneDuration"])
		indigo.server.log("Zone: " + str(pluginAction.props["ZoneValue"]) + " Time: " + str(pluginAction.props["zoneDuration"]))

		self.update_queue.append(deviceId)
		self.update()

	def actionStopZones(self, pluginAction):

		deviceId = int(pluginAction.props['indigo_rainmachine_controller'])
		device = indigo.devices[int(pluginAction.props['indigo_rainmachine_controller'])]
		controller = self.controllers[device.pluginProps["deviceMAC"]]
		controller.zones.stop(pluginAction.props["ZoneValue"])
		indigo.server.log("Stopping Zone: " + str(pluginAction.props["ZoneValue"]))

		self.update_queue.append(deviceId)
		self.update()


	def actionAllOff(self, pluginAction):

		deviceId = int(pluginAction.props['indigo_rainmachine_controller'])
		device = indigo.devices[int(pluginAction.props['indigo_rainmachine_controller'])]
		controller = self.controllers[device.pluginProps["deviceMAC"]]
		controller.watering.stop_all()
		indigo.server.log("Stopping All Called")

		self.update_queue.append(deviceId)
		self.update()


	def availableSchedules(self, filter="", valuesDict=None, typeId="", targetId=0):

		passed_schedule_list = []
		if 'indigo_rainmachine_controller' in valuesDict:
			device = indigo.devices[int(valuesDict['indigo_rainmachine_controller'])]
			controller = self.controllers[device.pluginProps['deviceMAC']]
			self.program_list = controller.programs.all()
			passed_schedule_list = [(int(program_dict["uid"]), program_dict["name"]) for program_dict in self.program_list["programs"]]
			self.debugLog("indigo.device.id : " + str(valuesDict['indigo_rainmachine_controller']))
			self.debugLog("indigo.mac.id : " + str(device.pluginProps['deviceMAC']))
		return passed_schedule_list


	def availableZones(self, filter="", valuesDict=None, typeId="", targetId=0):

		passed_zone_list = []
		if 'indigo_rainmachine_controller' in valuesDict:
			device = indigo.devices[int(valuesDict['indigo_rainmachine_controller'])]
			controller = self.controllers[device.pluginProps['deviceMAC']]
			self.zone_list = controller.zones.all()
			passed_zone_list = [(int(zone_dict["uid"]), zone_dict["name"]) for zone_dict in self.zone_list["zones"]]
		return passed_zone_list

	def availableDevices(self, filter="", valuesDict=None, typeId="", targetId=0):

		controller_list = [(controller.mac, controller.name + " : "+ controller.connection_type) for controller in self.client.controllers.values()]
		return controller_list


	def loginDevices(self, valuesDict, typeId, devId):
		if valuesDict["connectionType"] == 'Local':
			self.client.load_local(valuesDict["ip_address"], valuesDict["password"], port=valuesDict["port"], ssl=False)
		elif valuesDict["connectionType"] == 'Cloud':
			self.client.load_remote(valuesDict["username"], valuesDict["password"])
		else:
			indigo.server.log("Error in login")
		pass


	def menuChanged(self, valuesDict, typeId, devId):
		return valuesDict


	######################
	## Update functions ##
	######################

	def activeZone(self, deviceId):
		device = indigo.devices[deviceId]
		controller = self.controllers[device.pluginProps['deviceMAC']]
		current_zone = controller.watering.zone()
		return current_zone

	def activeProgram(self, deviceId):
		device = indigo.devices[deviceId]
		controller = self.controllers[device.pluginProps['deviceMAC']]
		current_program = controller.watering.program()
		return current_program