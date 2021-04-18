def check_urls(url):
	badstuff=['dQw4w9WgXcQ','eYq7WapuDLU', 'enjami', 'enjaami', 'rick roll', 'never gonna give'] #songs i don't like
	if any(word in url.lower().split() for word in badstuff):
		return True

def human_format(num):
    num = float('{:.3g}'.format(num))
    magnitude = 0
    while abs(num) >= 1000:
        magnitude += 1
        num /= 1000.0
    return '{}{}'.format('{:f}'.format(num).rstrip('0').rstrip('.'), ['', 'K', 'M', 'B', 'T'][magnitude])

def listToString(s):
	s[0]=f'👉\t' + s[0]
	str1='\n👉\t'
	return (str1.join(s))