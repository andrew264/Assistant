def check_urls(url):
	badstuff=['dQw4w9WgXcQ','eYq7WapuDLU', 'enjoy enjami', 'enjaami', 'rick roll', 'never gonna give you up'] #songs i don't like
	for badurl in badstuff:
		if badurl in url:
			return True

def listToString(s):
	s[0]=f'👉\t' + s[0]
	str1='\n👉\t'
	return (str1.join(s))