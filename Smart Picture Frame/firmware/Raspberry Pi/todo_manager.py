import json
import os
import time


class TodoManager:
    def __init__(self, config):
        self.config = config["todo"]
        self.file_path = self.config.get("file_path", "/sd/todo.json")
        self.max_items = self.config.get("max_items", 20)
        self._items = []
        self._load()

    def _load(self):
        try:
            with open(self.file_path, "r") as f:
                data = json.load(f)
                self._items = data.get("items", [])
        except:
            self._items = self._default_items()

    def _save(self):
        try:
            with open(self.file_path, "w") as f:
                json.dump({"items": self._items}, f)
        except:
            pass

    def _default_items(self):
        return [
            {"id": 1, "text": "設定 WiFi", "done": False},
            {"id": 2, "text": "設定天氣 API", "done": False},
            {"id": 3, "text": "加入 SD 卡圖片", "done": False},
        ]

    def add(self, text):
        item_id = (self._items[-1]["id"] + 1) if self._items else 1
        self._items.append({
            "id": item_id,
            "text": text,
            "done": False,
        })
        if len(self._items) > self.max_items:
            self._items = self._items[-self.max_items:]
        self._save()

    def remove(self, item_id):
        self._items = [i for i in self._items if i["id"] != item_id]
        self._save()

    def toggle(self, item_id):
        for item in self._items:
            if item["id"] == item_id:
                item["done"] = not item["done"]
                break
        self._save()

    def set_done(self, item_id, done=True):
        for item in self._items:
            if item["id"] == item_id:
                item["done"] = done
                break
        self._save()

    def get_all(self):
        return self._items

    def get_pending(self):
        return [i for i in self._items if not i["done"]]

    def get_done(self):
        return [i for i in self._items if i["done"]]

    def clear_done(self):
        self._items = [i for i in self._items if not i["done"]]
        self._save()
