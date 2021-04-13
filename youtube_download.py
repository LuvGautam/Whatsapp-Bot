from pytube import YouTube
from pytube.exceptions import VideoUnavailable, RegexMatchError
from pydub import AudioSegment
from pathlib import Path


def download_audio(q, link=None, sender_name='Luv'):
    try:
        yt = YouTube(link)
    except (VideoUnavailable, RegexMatchError):
        return None, 'Invalid youtube link.'

    ys = yt.streams.get_by_itag('140')

    if ys is None:
        q.put(([None], 'Unable to download audio. Please try different link.'))
        #return None, 'Unable to download audio. Please try different link.'
    else:
        if ys.filesize/(1024*1024) <= 20:
            file = ys.download(f'F:\PYTHON\web-automation\{sender_name}')
            sound = AudioSegment.from_file(file)
            Path(file).unlink(missing_ok=True)
            file = sound.export(fr'F:\PYTHON\web-automation\{sender_name}\audio.mp3', format="mp3")
            q.put(([Path(file.name)], 'success'))
            #return file.name, 'success'
        else:
            q.put(([None], 'File size too big to download.'))
            #return None, 'File size too big to download.'


if __name__ == '__main__':
    file, log = download_audio('https://www.youtube.com/watch?v=jEJI6Nf1aWU')
    print(file)
    print(log)

    #https://www.youtube.com/watch?v=jEJI6Nf1aWU
