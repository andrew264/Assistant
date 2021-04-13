def check_urls(url):
	badstuff=['dQw4w9WgXcQ','eYq7WapuDLU', 'enjoy enjami', 'enjami', 'rick roll', 'never gonna give you up'] #songs i don't like
	for badurl in badstuff:
		if badurl in url:
			return True

import youtube_dl.YoutubeDL as YDL
def yt_download(url):
	ydl_opts = {
    'format': 'bestaudio/best',
    'noplaylist': True,
    'nocheckcertificate': True,
    'ignoreerrors': False,
    'logtostderr': False,
	'quiet': True,
    'no_warnings': True,
    'postprocessors': [{
        'key': 'FFmpegExtractAudio',
        'preferredcodec': 'mp3',
        'preferredquality': '192',
    }],
}
	with YDL(ydl_opts) as ydl:
		ydl.download([url])

from os import system
def spotify(name):
	print('Searching in spotify...')
	song=name.replace(' ','_')
	system('spotdl -o D:\DiscordBOt\Assistant '+ f'{song}')

def listToString(s):
	s[0]=f'👉\t' + s[0]
	str1='\n👉\t'
	return (str1.join(s))