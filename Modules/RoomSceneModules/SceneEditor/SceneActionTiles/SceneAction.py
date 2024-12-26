import os

from PyQt6.QtWidgets import QLabel

from Modules.RoomSceneModules.SceneEditor.SceneActionTiles.BaseAction import BaseAction
from loguru import logger as logging

if os.path.exists("Modules/RoomSceneModules/SceneEditor/SceneActionTiles"):
    for file in os.listdir("Modules/RoomSceneModules/SceneEditor/SceneActionTiles"):
        if file.endswith(".py") and not file.startswith("__"):
            __import__(f"Modules.RoomSceneModules.SceneEditor.SceneActionTiles.{file[:-3]}")


class SceneAction:

    @staticmethod
    def supported_actions() -> list:
        actions = []
        for action_class in BaseAction.__subclasses__():
            actions.extend(action_class.supported_action)
        return actions

    @staticmethod
    def get_action_default_payload(action: str):
        for action_class in BaseAction.__subclasses__():
            for supported_action in action_class.supported_action:
                if supported_action[0] == action:
                    return supported_action[2]
        logging.error(f"Could not find a default payload for {action}")
        return None

    @classmethod
    def create_action(cls, parent, enabled, action: tuple):
        for action_class in BaseAction.__subclasses__():
            if action[0] in [a[0] for a in action_class.supported_action]:
                return action_class(parent, enabled, action)
        logging.error(f"Could not find a matching action class for {action[0]}")
        return BaseAction(parent, enabled, action)

