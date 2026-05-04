# Sunscape Music Player

Sunscape adalah aplikasi pemutar musik desktop yang dibangun menggunakan bahasa Python dengan antarmuka Tkinter dan mesin pemutar audio Pygame. Nama Sunscape sendiri merupakan gabungan kata sunset dan soundscape yang bertujuan untuk memberikan pengalaman mendengarkan musik yang nyaman layaknya menikmati suasana senja.

Aplikasi ini tidak hanya berfokus pada antarmuka visual yang modern, tetapi juga berfokus pada efisiensi pengelolaan data. Hal ini dicapai dengan mengimplementasikan berbagai konsep struktur data dasar secara langsung dari awal.

## Fitur Utama

Sistem pada aplikasi ini dibagi menjadi dua peran utama yaitu Admin dan User.

**Mode Admin**
Berperan sebagai pengelola basis data utama. Admin memiliki akses penuh untuk melakukan operasi CRUD (Create, Read, Update, Delete) pada seluruh koleksi lagu. Setiap perubahan data yang dilakukan oleh Admin akan langsung tersinkronisasi ke sisi User.

**Mode User**
Berperan sebagai pendengar dengan beberapa fitur khusus
- **Smart Playback** - Pengguna dapat memutar musik, menghentikan sementara, melewati lagu, kembali ke lagu sebelumnya, serta mengatur antrean pemutaran.
- **Custom Playlist** - Pengguna dapat membuat dan menyusun daftar putar secara personal.
- **Smart Search dan Auto-Recommend** - Algoritma pencarian dirancang agar dapat menoleransi kesalahan ketik ringan. Apabila daftar putar telah habis, sistem akan secara otomatis mencari dan memutar lagu yang serupa berdasarkan kemiripan artis atau genre.
- **Playback History** - Pengguna dapat melacak daftar lagu yang baru saja selesai diputar.

## Implementasi Struktur Data

Untuk memastikan performa aplikasi tetap cepat dan responsif, Sunscape memanfaatkan lima struktur data yang saling terintegrasi

1. **Doubly Linked List** - Berfungsi sebagai penyimpanan utama untuk daftar lagu dan playlist. Penggunaan struktur ini memungkinkan proses navigasi maju dan mundur antar lagu berjalan dengan sangat lancar.
2. **Hash Map** - Diterapkan untuk mempercepat proses pencarian lagu berdasarkan ID.
3. **Queue** - Digunakan untuk mengelola daftar antrean lagu yang akan diputar selanjutnya.
4. **Stack** - Berperan dalam menyimpan dan menampilkan riwayat lagu yang baru saja diputar.
5. **Record atau Struct** - Menjadi kerangka dasar untuk menyimpan seluruh metadata dari setiap lagu.

## Tech Stack
- Bahasa Pemrograman Python
- Antarmuka Grafis Tkinter
- Audio Engine Pygame

---
Proyek ini dikembangkan sebagai bentuk penerapan praktis dari teori struktur data ke dalam perangkat lunak fungsional.
