import requests
from moviepy.editor import VideoFileClip, TextClip, CompositeVideoClip
import tempfile
import io

def generate_signature_gif(data):
    gif_response = requests.get(data.image_url, stream=True)
    temp_gif = tempfile.NamedTemporaryFile(delete=False, suffix=".gif")
    temp_gif.write(gif_response.content)
    temp_gif.close()

    clip = VideoFileClip(temp_gif.name)
    text = f"{data.name}\n{data.title}\n{data.phone}"
    txt_clip = TextClip(text, fontsize=18, color='white', bg_color='black', method='caption', size=(200, 215)).set_position((435, 0)).set_duration(clip.duration)
    final_clip = CompositeVideoClip([clip.set_position(("left","top")), txt_clip])

    output = tempfile.NamedTemporaryFile(delete=False, suffix=".gif")
    final_clip.write_gif(output.name, fps=clip.fps)
    output.seek(0)
    return output.read()
