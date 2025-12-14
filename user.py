from typing import Optional
from .playlist import Playlist
from .doubly_linked_list import DoublyLinkedList
from .song import Song

class User:
    def __init__(self, user_id: str, username: str):
        self.id = user_id
        self.username = username
        self.playlists: dict[str, Playlist] = {}

class UserManager:
    def __init__(self):
        self.users: dict[str, User] = {}
        self.user_counter = 1

    def add_user(self, username: str) -> User:
        user_id = f"U{self.user_counter:03d}"
        new_user = User(user_id, username)
        self.users[user_id] = new_user
        self.user_counter += 1
        return new_user

    def add_playlist(self, user_id: str, playlist_name: str) -> bool:
        user = self.users.get(user_id)
        if user and playlist_name not in user.playlists:
            user.playlists[playlist_name] = Playlist(playlist_name)
            return True
        return False

    def remove_playlist(self, user_id: str, playlist_name: str) -> bool:
        user = self.users.get(user_id)
        if user and playlist_name in user.playlists:
            del user.playlists[playlist_name]
            return True
        return False

class PlayerStack:
    def __init__(self):
        self.stack: list[str] = []

    def push(self, song_id: str):
        self.stack.append(song_id)

    def pop(self) -> Optional[str]:
        if self.stack: 
            return self.stack.pop()
        return None

    def peek(self) -> Optional[str]:
        if self.stack: 
            return self.stack[-1]
        return None

class QueueNode:
    def __init__(self, song: Song):
        self.song = song
        self.prev: Optional['QueueNode'] = None
        self.next: Optional['QueueNode'] = None

class SmartQueue:
    def __init__(self):
        self.head: Optional[QueueNode] = None
        self.tail: Optional[QueueNode] = None
        self.size = 0
        self.undo_stack: list[Song] = []

    def add_next(self, song: Song):
        self.undo_stack.append(song)
        new_node = QueueNode(song)
        if not self.head:
            self.head = self.tail = new_node
        else:
            new_node.next = self.head
            self.head.prev = new_node
            self.head = new_node
        self.size += 1

    def add_later(self, song: Song):
        self.undo_stack.append(song)
        new_node = QueueNode(song)
        if not self.tail:
            self.head = self.tail = new_node
        else:
            self.tail.next = new_node
            new_node.prev = self.tail
            self.tail = new_node
        self.size += 1

    def pop_next(self) -> Optional[Song]:
        if not self.head:
            return None
        song = self.head.song
        if self.head == self.tail:
            self.head = self.tail = None
        else:
            self.head = self.head.next
            self.head.prev = None
        self.size -= 1
        return song

    def clear(self):
        self.head = self.tail = None
        self.size = 0
        self.undo_stack.clear()

    def to_list(self) -> list[Song]:
        result = []
        current = self.head
        while current:
            result.append(current.song)
            current = current.next
        return result

    def undo_last_add(self) -> bool:
        if not self.undo_stack:
            return False
        last_song = self.undo_stack.pop()
        current = self.head
        prev_node = None
        while current:
            if current.song.id == last_song.id:
                if prev_node:
                    prev_node.next = current.next
                else:
                    self.head = current.next
                if current.next:
                    current.next.prev = prev_node
                else:
                    self.tail = prev_node
                self.size -= 1
                return True
            prev_node = current
            current = current.next
        return False