import subprocess

def checkIfProcessRunning():
	result = subprocess.run(['jps', '-l'], stdout=subprocess.PIPE).stdout.decode('utf-8')
	if 'spigot.jar' in result or 'server.jar' in result:
		return True
	else:
		return False

def check_urls(url):
	badstuff=['dQw4w9WgXcQ','eYq7WapuDLU'] #songs i don't like
	for badurl in badstuff:
		if badurl in url:
			return True
		elif url == '':
			return True
