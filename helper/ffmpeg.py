import time
import os
import asyncio
from PIL import Image
from hachoir.metadata import extractMetadata
from hachoir.parser import createParser

async def fix_thumb(thumb):
    width = 0
    height = 0
    try:
        if thumb != None:
            parser = createParser(thumb)
            metadata = extractMetadata(parser)
            if metadata.has("width"):
                width = metadata.get("width")
            if metadata.has("height"):
                height = metadata.get("height")
                
            # Open the image file
            with Image.open(thumb) as img:
                # Convert the image to RGB format and save it back to the same file
                img.convert("RGB").save(thumb)
            
                # Resize the image
                resized_img = img.resize((width, height))
                
                # Save the resized image in JPEG format
                resized_img.save(thumb, "JPEG")
            parser.close()
    except Exception as e:
        print(e)
        thumb = None 
       
    return width, height, thumb
    
async def take_screen_shot(video_file, output_directory, ttl):
    out_put_file_name = f"{output_directory}/{time.time()}.jpg"
    file_genertor_command = [
        "ffmpeg",
        "-ss",
        str(ttl),
        "-i",
        video_file,
        "-vframes",
        "1",
        out_put_file_name
    ]
    process = await asyncio.create_subprocess_exec(
        *file_genertor_command,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )
    stdout, stderr = await process.communicate()
    e_response = stderr.decode().strip()
    t_response = stdout.decode().strip()
    if os.path.lexists(out_put_file_name):
        return out_put_file_name
    return None

import subprocess

async def add_last_six_seconds(video_path, output_path):
    """ Extracts the last 6 seconds of a video and appends it to the original video """
    # Extract the last 6 seconds
    temp_clip = "last_6_sec.mp4"
    extract_command = [
        "ffmpeg", "-sseof", "-6", "-i", video_path, "-c", "copy", temp_clip
    ]
    subprocess.run(extract_command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

    # Merge the original video with the extracted clip
    concat_list = "concat_list.txt"
    with open(concat_list, "w") as f:
        f.write(f"file '{video_path}'\nfile '{temp_clip}'\n")

    merge_command = [
        "ffmpeg", "-f", "concat", "-safe", "0", "-i", concat_list, "-c", "copy", output_path
    ]
    subprocess.run(merge_command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

    # Cleanup temp files
    os.remove(temp_clip)
    os.remove(concat_list)

    return output_path

import subprocess
import os

async def add_last_six_seconds(video_path, clip_path, output_path):
    """ Appends either the last 6 seconds of a video or a custom clip """
    if not os.path.exists(clip_path):
        # Extract last 6 seconds if no custom clip exists
        temp_clip = "last_6_sec.mp4"
        extract_command = ["ffmpeg", "-sseof", "-6", "-i", video_path, "-c", "copy", temp_clip]
        subprocess.run(extract_command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        clip_path = temp_clip

    # Merge the original video with the selected clip
    concat_list = "concat_list.txt"
    with open(concat_list, "w") as f:
        f.write(f"file '{video_path}'\nfile '{clip_path}'\n")

    merge_command = ["ffmpeg", "-f", "concat", "-safe", "0", "-i", concat_list, "-c", "copy", output_path]
    subprocess.run(merge_command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

    # Cleanup temp files
    if os.path.exists("last_6_sec.mp4"):
        os.remove("last_6_sec.mp4")
    os.remove(concat_list)

    return output_path
