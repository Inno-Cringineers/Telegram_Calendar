"""This service is responsible for uploading files to the server.
It can upload ics file from user chat.
Or it can pulling ics file from url.
And then it gives this file to the import service.
"""

import os

from aiogram import Bot
from aiogram.types import Message

from store.store import Store


class UploadService:
    def __init__(self, store: Store) -> None:
        self.store = store

    async def subscribe_to_ical_url(self, url: str) -> None:
        pass

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
        user_id = message.from_user.id  # type: ignore[attr-defined]
        if user_id is None:
            raise ValueError("User id is None")

        # import file
        await self.store.get_import_service.import_local_calendar_from_file(save_path, user_id)

        # remove file
        os.remove(save_path)
