from typing import Optional
from .song import Song  # <-- IMPORT RELATIF YANG BENAR

class Node:
    def __init__(self, data: Song):
        self.data: Song = data
        self.prev: Optional[Node] = None
        self.next: Optional[Node] = None

class DoublyLinkedList:
    def __init__(self):
        self.head: Optional[Node] = None
        self.tail: Optional[Node] = None
        self.size = 0
        self.id_map: dict[str, Song] = {}

    def _generate_id(self) -> str:
        return f"S{self.size + 1:04d}"

    def add_song(self, title: str, artist: str, genre: str, year: str, duration: str, file_path: str = "") -> bool:
        song_id = self._generate_id()
        new_song = Song(song_id, title, artist, genre, year, duration, file_path) 
        new_node = Node(new_song)
        if not self.head:
            self.head = self.tail = new_node
        else:
            self.tail.next = new_node
            new_node.prev = self.tail
            self.tail = new_node
        self.size += 1
        self.id_map[song_id] = new_song
        return True

    def get_all_songs(self) -> list[Song]:
        songs = []
        current = self.head
        while current:
            songs.append(current.data)
            current = current.next
        return songs

    def edit_song(self, song_id: str, title: str, artist: str, genre: str, year: str, duration: str, file_path: str = "") -> bool:
        if song_id in self.id_map:
            song_to_edit = self.id_map[song_id]
            song_to_edit.title = title
            song_to_edit.artist = artist
            song_to_edit.genre = genre
            song_to_edit.year = year
            song_to_edit.duration = duration
            if file_path:  # Only update if provided
                song_to_edit.file_path = file_path
            return True
        return False

    def delete_song(self, song_id: str) -> bool:
        if song_id not in self.id_map: 
            return False
        current = self.head
        node_to_delete: Optional[Node] = None
        while current:
            if current.data.id == song_id:
                node_to_delete = current
                break
            current = current.next
        if node_to_delete:
            if node_to_delete.prev: 
                node_to_delete.prev.next = node_to_delete.next
            else: 
                self.head = node_to_delete.next
            if node_to_delete.next: 
                node_to_delete.next.prev = node_to_delete.prev
            else: 
                self.tail = node_to_delete.prev
            del self.id_map[song_id]
            self.size -= 1
            return True
        return False