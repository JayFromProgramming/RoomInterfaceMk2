import os

from PyQt6.QtWidgets import QLabel

from Modules.RoomSceneModules.SceneEditor.SceneActionTiles.BaseAction import BaseAction
from loguru import logger as logging

if os.path.exists("Modules/RoomSceneModules/SceneEditor/SceneActionTiles"):
    for file in os.listdir("Modules/RoomSceneModules/SceneEditor/SceneActionTiles"):
        if file.endswith(".py") and not file.startswith("__"):
            __import__(f"Modules.RoomSceneModules.SceneEditor.SceneActionTiles.{file[:-3]}")


class SceneAction(QLabel):

    @staticmethod
    def supported_actions() -> list:
        actions = []
        for action_class in BaseAction.__subclasses__():
            actions.extend(action_class.supported_action)
        return actions

    def __init__(self, parent, delete_callback, action: tuple):
        # This class will replace itself with the correct action class based on the action type
        super().__init__(parent)
        for action_class in BaseAction.__subclasses__():
            if action[0] in [a[0] for a in action_class.supported_action]:
                self.__class__ = action_class
                break
        if self.__class__ == SceneAction:
            logging.error(f"Could not find a matching action class for {action[0]}")
