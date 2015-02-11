from serial import Serial

serial = None

class Haptic(object):

	def __init__(self, port):
		#try:
			self.serial = Serial(port, 57600)
			self.serial.flushInput()
			self.intensity = -1
			#self.serial.close()
			#self.serial.open()
		#except serial.SerialException:
		#	print("ERROR in Serial Init")

	#	Pulse: Pulses the vibrator one time with intensity between 1-10 and duration represented in milisec.  
	def pulse(self, i, time):
		self.serial.write('p%d%d' %(i, time))
	
	#	Set: Set the intensity of the vibrator 0-10 where 0 is off.
	def set(self, i):
		if i == self.intensity: return
		self.intensity = i
		self.serial.write(i)
	#	If ther is an error during init, try and change port using this function.	
	def setPort(self, port):
		try:
			self.serial = serial.Serial(port, 9600, timeout=1)
			self.serial.close()
			self.serial.open()
		except serial.SerialException:
			print("ERROR in Serial Init")