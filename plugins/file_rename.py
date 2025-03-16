import random
from helper.ffmpeg import fix_thumb, take_screen_shot
from pyrogram import Client, filters
from pyrogram.enums import MessageMediaType
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup, ForceReply
from hachoir.metadata import extractMetadata
from hachoir.parser import createParser
from helper.utils import progress_for_pyrogram, convert, humanbytes
from helper.database import db
from PIL import Image
import asyncio
import os
import time
from helper.utils import add_prefix_suffix
from config import Config


app = Client("test", api_id=Config.STRING_API_ID,
             api_hash=Config.STRING_API_HASH, session_string=Config.STRING_SESSION)

# Define a function to handle the 'rename' callback


@Client.on_callback_query(filters.regex('rename'))
async def rename(bot, update):
    await update.message.delete()
    await update.message.reply_text("__𝙿𝚕𝚎𝚊𝚜𝚎 𝙴𝚗𝚝𝚎𝚛 𝙽𝚎𝚠 𝙵𝚒𝚕𝚎𝙽𝚊𝚖𝚎...__",
                                    reply_to_message_id=update.message.reply_to_message.id,
                                    reply_markup=ForceReply(True))

# Define the main message handler for private messages with replies


@Client.on_message(filters.private & filters.reply)
async def refunc(client, message):
    reply_message = message.reply_to_message
    if isinstance(reply_message.reply_markup, ForceReply):
        new_name = message.text
        await message.delete()
        msg = await client.get_messages(message.chat.id, reply_message.id)
        file = msg.reply_to_message
        media = getattr(file, file.media.value)
        if not "." in new_name:
            if "." in media.file_name:
                extn = media.file_name.rsplit('.', 1)[-1]
            else:
                extn = "mkv"
            new_name = new_name + "." + extn
        await reply_message.delete()

        # Use a list to store the inline keyboard buttons
        button = [
            [InlineKeyboardButton(
                "📁 Dᴏᴄᴜᴍᴇɴᴛ", callback_data="upload_document")]
        ]
        if file.media in [MessageMediaType.VIDEO, MessageMediaType.DOCUMENT]:
            button.append([InlineKeyboardButton(
                "🎥 Vɪᴅᴇᴏ", callback_data="upload_video")])
        elif file.media == MessageMediaType.AUDIO:
            button.append([InlineKeyboardButton(
                "🎵 Aᴜᴅɪᴏ", callback_data="upload_audio")])

        # Use a single call to reply with both text and inline keyboard
        await message.reply(
            text=f"**Sᴇʟᴇᴄᴛ Tʜᴇ Oᴜᴛᴩᴜᴛ Fɪʟᴇ Tyᴩᴇ**\n**• Fɪʟᴇ Nᴀᴍᴇ :-**  `{new_name}`",
            reply_to_message_id=file.id,
            reply_markup=InlineKeyboardMarkup(button)
        )

# Define the callback for the 'upload' buttons


@Client.on_callback_query(filters.regex("upload"))
async def doc(bot, update):

    # Creating Directory for Metadata
    if not os.path.isdir("Metadata"):
        os.mkdir("Metadata")

    # Extracting necessary information
    prefix = await db.get_prefix(update.message.chat.id)
    suffix = await db.get_suffix(update.message.chat.id)
    new_name = update.message.text
    new_filename_ = new_name.split(":-")[1]

    try:
        # adding prefix and suffix
        new_filename = add_prefix_suffix(new_filename_, prefix, suffix)

    except Exception as e:
        return await update.message.edit(f"⚠️ Something went wrong can't able to set Prefix or Suffix ☹️ \n\n❄Contact My Creator -> @c0nt4ct_bot\nError: {e}")

    file_path = f"downloads/{new_filename}"
    file = update.message.reply_to_message

    ms = await update.message.edit("⚠️ __**Please wait...**__\n\n**Tʀyɪɴɢ Tᴏ Dᴏᴡɴʟᴏᴀᴅɪɴɢ....**")
    try:
        path = await bot.download_media(message=file, file_name=file_path, progress=progress_for_pyrogram, progress_args=("\n⚠️ __**Please wait...**__\n\n❄️ **Dᴏᴡɴʟᴏᴀᴅ Sᴛᴀʀᴛᴇᴅ....**", ms, time.time()))
    except Exception as e:
        return await ms.edit(e)

    _bool_metadata = await db.get_metadata(update.message.chat.id)

    if (_bool_metadata):
        metadata_path = f"Metadata/{new_filename}"
        metadata = await db.get_metadata_code(update.message.chat.id)
        if metadata:

            await ms.edit("I Fᴏᴜɴᴅ Yᴏᴜʀ Mᴇᴛᴀᴅᴀᴛᴀ\n\n__**Pʟᴇᴀsᴇ Wᴀɪᴛ...**__\n**Aᴅᴅɪɴɢ Mᴇᴛᴀᴅᴀᴛᴀ Tᴏ Fɪʟᴇ....**")
            cmd = f"""ffmpeg -i "{path}" {metadata} "{metadata_path}" """

            process = await asyncio.create_subprocess_shell(
                cmd, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE
            )

            stdout, stderr = await process.communicate()
            er = stderr.decode()

            try:
                if er:
                    return await ms.edit(str(er) + "\n\n**Error**")
            except BaseException:
                pass
        await ms.edit("**Metadata added to the file successfully ✅**\n\n⚠️ __**Please wait...**__\n\n**Tʀyɪɴɢ Tᴏ Uᴩʟᴏᴀᴅɪɴɢ....**")
    else:
        await ms.edit("⚠️  __**Please wait...**__\n\n\n**Tʀyɪɴɢ Tᴏ Uᴩʟᴏᴀᴅɪɴɢ....**")

    duration = 0
    try:
        parser = createParser(file_path)
        metadata = extractMetadata(parser)
        if metadata.has("duration"):
            duration = metadata.get('duration').seconds
        parser.close()

    except:
        pass
    ph_path = None
    media = getattr(file, file.media.value)
    c_caption = await db.get_caption(update.message.chat.id)
    c_thumb = await db.get_thumbnail(update.message.chat.id)

    if c_caption:
        try:
            caption = c_caption.format(filename=new_filename, filesize=humanbytes(
                media.file_size), duration=convert(duration))
        except Exception as e:
            return await ms.edit(text=f"Yᴏᴜʀ Cᴀᴩᴛɪᴏɴ Eʀʀᴏʀ Exᴄᴇᴩᴛ Kᴇyᴡᴏʀᴅ Aʀɢᴜᴍᴇɴᴛ ●> ({e})")
    else:
        caption = f"**{new_filename}**"

    if (media.thumbs or c_thumb):
        if c_thumb:
            ph_path = await bot.download_media(c_thumb)
            width, height, ph_path = await fix_thumb(ph_path)
        else:
            try:
                ph_path_ = await take_screen_shot(file_path, os.path.dirname(os.path.abspath(file_path)), random.randint(0, duration - 1))
                width, height, ph_path = await fix_thumb(ph_path_)
            except Exception as e:
                ph_path = None
                print(e)

    type = update.data.split("_")[1]

    if media.file_size > 2000 * 1024 * 1024:
        try:
            if type == "document":

                filw = await app.send_document(
                    Config.LOG_CHANNEL,
                    document=metadata_path if _bool_metadata else file_path,
                    thumb=ph_path,
                    caption=caption,
                    progress=progress_for_pyrogram,
                    progress_args=("⚠️ __**Please wait...**__\n\n🌨️ **Uᴩʟᴏᴅ Sᴛᴀʀᴛᴇᴅ....**", ms, time.time()))

                from_chat = filw.chat.id
                mg_id = filw.id
                time.sleep(2)
                await bot.copy_message(update.from_user.id, from_chat, mg_id)
                await ms.delete()
                await bot.delete_messages(from_chat, mg_id)

            elif type == "video":
                filw = await app.send_video(
                    update.message.chat.id,
                    video=metadata_path if _bool_metadata else file_path,
                    caption=caption,
                    thumb=ph_path,
                    width=width,
                    height=height,
                    duration=duration,
                    progress=progress_for_pyrogram,
                    progress_args=("⚠️ __**Please wait...**__\n\n🌨️ **Uᴩʟᴏᴅ Sᴛᴀʀᴛᴇᴅ....**", ms, time.time()))

                from_chat = filw.chat.id
                mg_id = filw.id
                time.sleep(2)
                await bot.copy_message(update.from_user.id, from_chat, mg_id)
                await ms.delete()
                await bot.delete_messages(from_chat, mg_id)
            elif type == "audio":
                filw = await app.send_audio(
                    update.message.chat.id,
                    audio=metadata_path if _bool_metadata else file_path,
                    caption=caption,
                    thumb=ph_path,
                    duration=duration,
                    progress=progress_for_pyrogram,
                    progress_args=("⚠️ __**Please wait...**__\n\n🌨️ **Uᴩʟᴏᴅ Sᴛᴀʀᴛᴇᴅ....**", ms, time.time()))

                from_chat = filw.chat.id
                mg_id = filw.id
                time.sleep(2)
                await bot.copy_message(update.from_user.id, from_chat, mg_id)
                await ms.delete()
                await bot.delete_messages(from_chat, mg_id)

        except Exception as e:
            os.remove(file_path)
            if ph_path:
                os.remove(ph_path)
            if metadata_path:
                os.remove(metadata_path)
            if path:
                os.remove(path)
            return await ms.edit(f" Eʀʀᴏʀ {e}")

    else:

        try:
            if type == "document":
                await bot.send_document(
                    update.message.chat.id,
                    document=metadata_path if _bool_metadata else file_path,
                    thumb=ph_path,
                    caption=caption,
                    progress=progress_for_pyrogram,
                    progress_args=("⚠️ __**Please wait...**__\n\n🌨️ **Uᴩʟᴏᴅ Sᴛᴀʀᴛᴇᴅ....**", ms, time.time()))
            elif type == "video":
                await bot.send_video(
                    update.message.chat.id,
                    video=metadata_path if _bool_metadata else file_path,
                    caption=caption,
                    thumb=ph_path,
                    width=width,
                    height=height,
                    duration=duration,
                    progress=progress_for_pyrogram,
                    progress_args=("⚠️ __**Please wait...**__\n\n🌨️ **Uᴩʟᴏᴅ Sᴛᴀʀᴛᴇᴅ....**", ms, time.time()))
            elif type == "audio":
                await bot.send_audio(
                    update.message.chat.id,
                    audio=metadata_path if _bool_metadata else file_path,
                    caption=caption,
                    thumb=ph_path,
                    duration=duration,
                    progress=progress_for_pyrogram,
                    progress_args=("⚠️ __**Please wait...**__\n\n🌨️ **Uᴩʟᴏᴅ Sᴛᴀʀᴛᴇᴅ....**", ms, time.time()))
        except Exception as e:
            os.remove(file_path)
            if ph_path:
                os.remove(ph_path)
            if metadata_path:
                os.remove(metadata_path)
            if path:
                os.remove(path)
            return await ms.edit(f" Eʀʀᴏʀ {e}")

    await ms.delete()

    if ph_path:
        os.remove(ph_path)
    if file_path:
        os.remove(file_path)
    if metadata_path:
        os.remove(metadata_path)

from helper.ffmpeg import add_last_six_seconds

@Client.on_message(filters.command("setlast6") & filters.private)
async def set_last_six(client, message):
    """ Toggle the last 6 seconds merge feature """
    user_id = message.chat.id
    setting = await db.get_user_setting(user_id, "last_6_sec", False)
    new_setting = not setting
    await db.update_user_setting(user_id, "last_6_sec", new_setting)
    await message.reply_text(f"Last 6 seconds merge {'enabled' if new_setting else 'disabled'}")

@Client.on_message(filters.private & filters.reply)
async def refunc(client, message):
    reply_message = message.reply_to_message
    if isinstance(reply_message.reply_markup, ForceReply):
        new_name = message.text
        await message.delete()
        msg = await client.get_messages(message.chat.id, reply_message.id)
        file = msg.reply_to_message
        media = getattr(file, file.media.value)

        if not "." in new_name:
            extn = media.file_name.rsplit('.', 1)[-1] if "." in media.file_name else "mkv"
            new_name = f"{new_name}.{extn}"

        # Check if last 6 seconds merge is enabled
        user_id = message.chat.id
        last_6_sec_enabled = await db.get_user_setting(user_id, "last_6_sec", False)

        output_path = f"downloads/{new_name}"
        if last_6_sec_enabled:
            temp_path = f"downloads/temp_{new_name}"
            await file.download(file_name=temp_path)
            output_path = await add_last_six_seconds(temp_path, output_path)

        await client.send_document(message.chat.id, output_path, caption="Here is your renamed file!")

from helper.ffmpeg import add_last_six_seconds
import os

@Client.on_message(filters.command("set6secvideo") & filters.private & filters.video)
async def set_custom_six_sec(client, message):
    """ Allow users to set a custom 6-second clip """
    user_id = message.chat.id
    file_path = f"downloads/{user_id}_6sec.mp4"
    await message.video.download(file_path)
    await db.update_user_setting(user_id, "custom_6_sec", file_path)
    await message.reply_text("Custom 6-second video saved!")

@Client.on_message(filters.private & filters.reply)
async def refunc(client, message):
    reply_message = message.reply_to_message
    if isinstance(reply_message.reply_markup, ForceReply):
        new_name = message.text
        await message.delete()
        msg = await client.get_messages(message.chat.id, reply_message.id)
        file = msg.reply_to_message
        media = getattr(file, file.media.value)

        if not "." in new_name:
            extn = media.file_name.rsplit('.', 1)[-1] if "." in media.file_name else "mkv"
            new_name = f"{new_name}.{extn}"

        # Check if last 6 seconds merge is enabled
        user_id = message.chat.id
        last_6_sec_enabled = await db.get_user_setting(user_id, "last_6_sec", False)
        custom_clip = await db.get_user_setting(user_id, "custom_6_sec", None)

        output_path = f"downloads/{new_name}"
        temp_path = f"downloads/temp_{new_name}"
        await file.download(file_name=temp_path)

        if last_6_sec_enabled:
            clip_path = custom_clip if custom_clip else temp_path
            output_path = await add_last_six_seconds(temp_path, clip_path, output_path)

        # Preserve thumbnail
        thumb_path = f"downloads/{user_id}_thumb.jpg"
        if file.video.thumbs:
            await file.video.thumbs[0].download(file_name=thumb_path)

        await client.send_document(message.chat.id, output_path, thumb=thumb_path, caption="Here is your renamed file!")
