from typing import Optional

class PlaylistNode:
    def __init__(self, song_ref: str):
        self.song_id: str = song_ref
        self.next: Optional['PlaylistNode'] = None
        self.prev: Optional['PlaylistNode'] = None  # Added for Doubly Linked List

class Playlist:
    def __init__(self, name: str):
        self.name = name
        self.head: Optional[PlaylistNode] = None
        self.tail: Optional[PlaylistNode] = None  # Track tail for O(1) append
        self.size = 0
        self.current_play: Optional[PlaylistNode] = None

    def add_song(self, song_id: str) -> bool:
        # Check uniqueness (optional, but good for playlist)
        current = self.head
        while current:
            if current.song_id == song_id:
                return False
            current = current.next
            
        new_node = PlaylistNode(song_id)
        if not self.head:
            self.head = new_node
            self.tail = new_node
        else:
            self.tail.next = new_node
            new_node.prev = self.tail
            self.tail = new_node
        self.size += 1
        return True

    def set_current_song(self, song_id: str) -> bool:
        """Find node by song_id and set as current_play"""
        current = self.head
        while current:
            if current.song_id == song_id:
                self.current_play = current
                return True
            current = current.next
        return False

    def remove_song_by_id(self, song_id: str) -> bool:
        current = self.head
        while current:
            if current.song_id == song_id:
                # Update next pointer of prev node
                if current.prev:
                    current.prev.next = current.next
                else:
                    self.head = current.next
                
                # Update prev pointer of next node
                if current.next:
                    current.next.prev = current.prev
                else:
                    self.tail = current.prev
                
                # If current_play was this node, unset it or move it
                if self.current_play == current:
                    self.current_play = None
                
                self.size -= 1
                return True
            current = current.next
        return False

    def remove_all_references(self, deleted_song_id: str) -> int:
        count = 0
        current = self.head
        while current:
            next_node = current.next # Save next because current might be deleted
            if current.song_id == deleted_song_id:
                # Delete logic safely
                if current.prev:
                    current.prev.next = current.next
                else:
                    self.head = current.next
                
                if current.next:
                    current.next.prev = current.prev
                else:
                    self.tail = current.prev
                
                if self.current_play == current:
                    self.current_play = None
                    
                self.size -= 1
                count += 1
            current = next_node
        return count

    def to_list(self) -> list[str]:
        result = []
        current = self.head
        while current:
            result.append(current.song_id)
            current = current.next
        return result

    def move_song_up(self, song_id: str) -> bool:
        if not self.head or not self.head.next:
            return False
            
        current = self.head
        while current:
            if current.song_id == song_id:
                if not current.prev: # Sudah paling atas
                    return False
                
                prev_node = current.prev
                
                # Swap logic for DLL
                # ... [prev_prev] <-> [prev_node] <-> [current] <-> [next_node] ...
                prev_prev = prev_node.prev
                next_node = current.next
                
                # 1. Update prev_prev's next to current
                if prev_prev:
                    prev_prev.next = current
                else:
                    self.head = current
                
                # 2. Update next_node's prev to prev_node
                if next_node:
                    next_node.prev = prev_node
                else:
                    self.tail = prev_node
                
                # 3. Link current and prev_node
                current.prev = prev_prev
                current.next = prev_node
                
                prev_node.prev = current
                prev_node.next = next_node
                
                return True
            current = current.next
        return False

    def move_song_down(self, song_id: str) -> bool:
        if not self.head or not self.head.next:
            return False
            
        current = self.head
        while current:
            if current.song_id == song_id:
                if not current.next: # Sudah paling bawah
                    return False
                
                next_node = current.next
                
                # Swap logic is just inverse of move up
                # Call move_up on the next_node effectively swaps them
                return self.move_song_up(next_node.song_id)
                
            current = current.next
        return False