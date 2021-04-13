import subprocess
def checkIfProcessRunning():
	result = subprocess.run(['jps', '-l'], stdout=subprocess.PIPE).stdout.decode('utf-8')
	if 'spigot.jar' in result or 'server.jar' in result:
		return True
	else:
		return False