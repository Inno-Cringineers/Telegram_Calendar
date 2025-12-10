"""This service is responsible for uploading files to the server.
It can upload ics file from user chat.
Or it can pulling ics file from url.
And then it gives this file to the import service.
"""

import os

import aiohttp
from aiogram import Bot
from aiogram.types import Message

from logger.logger import logger
from store.store import Store


class UploadService:
    def __init__(self, store: Store) -> None:
        self.store = store

    async def upload_ical_url(self, user_id: int, calendar_name: str, url: str) -> None:
        # loads .ics file from internet by url
        file_path = await self._download_ics_file(url)
        # TODO: checks diff with old version if it exists
        # if no diff, does nothing
        # if not _is_diff(file_path):
        #    return
        # imports events from ics file
        logger.debug(
            "Upload service: uploading ics file from url, user_id: %s",
            user_id,
        )
        await self.store.ImportService.import_external_calendar_from_file(file_path, user_id, calendar_name, url)

        # delete old version of file
        os.remove(file_path)  # TODO
        # saves ics file to local storage as old version

    async def _download_ics_file(self, url: str) -> str:
        # downloads .ics file from internet by url
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as response:
                if response.status != 200:
                    raise ValueError(f"Failed to download .ics file from {url}")
                file_content = await response.read()
                file_path = f"downloads/{url.split('/')[-1]}"
                os.makedirs("downloads", exist_ok=True)
                with open(file_path, "wb") as f:
                    f.write(file_content)
                return file_path

    async def upload_ics_file(self, message: Message, bot: Bot) -> None:
        # check if document is present
        if message.document is None:
            raise ValueError("Document is required in message")

        # check if file name is present
        file_name = message.document.file_name
        if file_name is None:
            raise ValueError("File name is None")

        # check if file is .ics file
        if file_name[-4:] != ".ics":
            raise ValueError("File must be .ics file")

        # get file id
        file_id = message.document.file_id
        file = await bot.get_file(file_id)

        # get file path
        file_path = file.file_path
        if file_path is None:
            raise ValueError("File path is None")

        # create save path
        save_path = f"downloads/{file_name}"

        # create save directory
        os.makedirs(save_path, exist_ok=True)

        # download file
        await bot.download_file(file_path, save_path)

        # get user id
        if message.from_user is None:
            raise ValueError("User is None")
        user_id = message.from_user.id
        if user_id is None:
            raise ValueError("User id is None")

        # import file
        await self.store.ImportService.import_local_calendar_from_file(save_path, user_id)

        # remove file
        os.remove(save_path)
