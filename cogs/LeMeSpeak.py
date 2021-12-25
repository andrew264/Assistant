# Imports
import sounddevice as sd
from disnake import Client, PCMAudio
from disnake.ext import commands


# Gets audio from the microphone
class MicrophoneAudioSource(PCMAudio):
    def __init__(self, duration_ms=20):
        self.SAMP_RATE_HZ = 48000.0
        self.SAMP_PERIOD_SEC = 1.0 / self.SAMP_RATE_HZ
        self.NUM_SAMPLES = int((duration_ms / 1000.0) / self.SAMP_PERIOD_SEC)
        self.audioStream = sd.RawInputStream(samplerate=self.SAMP_RATE_HZ, channels=2, dtype="int16",
                                             blocksize=self.NUM_SAMPLES, )
        self.audioStream.start()

    def read(self) -> bytes:
        retVal = self.audioStream.read(self.NUM_SAMPLES)
        rawData = bytes(retVal[0])
        return rawData


class LeMeSpeak(commands.Cog):
    def __init__(self, client: Client):
        self.client = client
        self.mikeAudioSource = MicrophoneAudioSource()

    @commands.command()
    @commands.is_owner()
    async def join(self, ctx: commands.Context, *, vc=None) -> None:
        if vc is None and ctx.author.voice:
            vc = ctx.author.voice.channel
        else:
            for voice_channel in ctx.guild.voice_channels:
                if vc.lower() in voice_channel.name.lower():
                    vc = voice_channel
                    break
        if vc is None:
            await ctx.send("VC not found")
            return
        voice_client = await vc.connect()
        voice_client.play(self.mikeAudioSource)


def setup(client):
    client.add_cog(LeMeSpeak(client))
