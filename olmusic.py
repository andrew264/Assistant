def check_urls(url):
	badstuff=['dQw4w9WgXcQ','eYq7WapuDLU', 'enjami', 'enjaami', 'rick roll', 'never gonna give'] #songs i don't like
	if any(word in url.lower().split() for word in badstuff):
		return True

def listToString(s):
	s[0]=f'👉\t' + s[0]
	str1='\n👉\t'
	return (str1.join(s))