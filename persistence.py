import json
import os
from ..models.song import Song
from ..models.doubly_linked_list import DoublyLinkedList
from ..models.user import UserManager

DATA_FILE = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "data.json")

class PersistenceManager:
    @staticmethod
    def ensure_data_dir():
        os.makedirs(os.path.dirname(DATA_FILE), exist_ok=True)

    @staticmethod
    def save_data(library: DoublyLinkedList, user_manager: UserManager):
        PersistenceManager.ensure_data_dir()
        
        # Serialize Library
        songs_data = [song.to_dict() for song in library.get_all_songs()]
        
        # Serialize Users & Playlists
        users_data = {}
        for user_id, user in user_manager.users.items():
            playlists_data = {}
            for name, playlist in user.playlists.items():
                playlists_data[name] = playlist.to_list() # List of IDs
            
            users_data[user_id] = {
                "username": user.username,
                "playlists": playlists_data
            }
            
        data = {
            "library": songs_data,
            "users": users_data,
            "user_counter": user_manager.user_counter
        }
        
        try:
            with open(DATA_FILE, 'w') as f:
                json.dump(data, f, indent=4)
            # print("DEBUG: Data saved successfully.")
        except Exception as e:
            print(f"Error saving data: {e}")

    @staticmethod
    def load_data(library: DoublyLinkedList, user_manager: UserManager) -> bool:
        if not os.path.exists(DATA_FILE):
            return False
            
        try:
            with open(DATA_FILE, 'r') as f:
                data = json.load(f)
                
            # Load Library
            library.head = None
            library.tail = None
            library.size = 0
            library.id_map = {}
            
            for song_data in data.get("library", []):
                song = Song.from_dict(song_data)
                # Manually add to avoid ID regeneration if possible, BUT add_song generates ID.
                # We need to respect the saved ID. 
                # Linked List doesn't have "add_existing_song_node".
                # FIX: We should probably just use internal method or modify add_song?
                # BETTER: Just reconstruction manually.
                from ..models.doubly_linked_list import Node
                new_node = Node(song)
                if not library.head:
                    library.head = library.tail = new_node
                else:
                    library.tail.next = new_node
                    new_node.prev = library.tail
                    library.tail = new_node
                library.size += 1
                library.id_map[song.id] = song
            
            # Load Users
            user_manager.users = {}
            user_manager.user_counter = data.get("user_counter", 1)
            
            users_raw = data.get("users", {})
            for user_id, u_data in users_raw.items():
                # Recreate User
                # user_manager.add_user generates ID. We need custom reconstruction.
                from ..models.user import User
                restored_user = User(user_id, u_data["username"])
                
                # Restore Playlists
                for pl_name, song_ids in u_data.get("playlists", {}).items():
                    from ..models.playlist import Playlist
                    pl = Playlist(pl_name)
                    for sid in song_ids:
                        if sid in library.id_map: # Validate existence
                            pl.add_song(sid)
                    restored_user.playlists[pl_name] = pl
                
                user_manager.users[user_id] = restored_user
                
            return True
        except Exception as e:
            print(f"Error loading data: {e}")
            return False
