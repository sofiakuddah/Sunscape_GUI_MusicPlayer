class Song:
    def __init__(self, song_id: str, title: str, artist: str, genre: str, year: str, duration: str, file_path: str = ""):
        self.id = song_id
        self.title = title
        self.artist = artist
        self.genre = genre
        self.year = year
        self.duration = duration
        self.file_path = file_path

    def __str__(self):
        return f"[{self.id}] {self.title} - {self.artist} ({self.genre}, {self.year}, {self.duration}){' 🎵' if self.file_path else ''}"

    def is_similar(self, other_song: 'Song') -> bool:
        if self.artist.lower() == other_song.artist.lower(): 
            return True
        if self.genre.lower() == other_song.genre.lower() and self.artist.lower() != other_song.artist.lower(): 
            return True
        if self.year == other_song.year: 
            return True
        return False

    def to_dict(self):
        return {
            "id": self.id,
            "title": self.title,
            "artist": self.artist,
            "genre": self.genre,
            "year": self.year,
            "duration": self.duration,
            "file_path": self.file_path
        }

    @staticmethod
    def from_dict(data):
        return Song(
            data["id"],
            data["title"],
            data["artist"],
            data["genre"],
            data["year"],
            data["duration"],
            data.get("file_path", "")
        )