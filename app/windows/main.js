const { app, BrowserWindow, ipcMain } = require('electron');
const path = require('path');
const fs = require('fs');

let mainWindow;

function createWindow() {
    mainWindow = new BrowserWindow({
        width: 1000,
        height: 700,
        webPreferences: {
            nodeIntegration: true,
            contextIsolation: false
        },
        icon: path.join(__dirname, 'assets/icon.png'),
        title: 'maimai随机选歌工具 - Alpha-0.0.2'
    });

    mainWindow.loadFile('index.html');
    
    mainWindow.setMenuBarVisibility(false);
}

app.whenReady().then(createWindow);

app.on('window-all-closed', () => {
    if (process.platform !== 'darwin') {
        app.quit();
    }
});

app.on('activate', () => {
    if (BrowserWindow.getAllWindows().length === 0) {
        createWindow();
    }
});

const SONGS_PATH = path.join(__dirname, '../../data/songs.json');

function loadSongs() {
    try {
        if (fs.existsSync(SONGS_PATH)) {
            const data = fs.readFileSync(SONGS_PATH, 'utf-8');
            return JSON.parse(data);
        }
        return [];
    } catch (error) {
        console.error('Error loading songs:', error);
        return [];
    }
}

function saveSongs(songs) {
    try {
        fs.writeFileSync(SONGS_PATH, JSON.stringify(songs, null, 2), 'utf-8');
        return true;
    } catch (error) {
        console.error('Error saving songs:', error);
        return false;
    }
}

ipcMain.handle('get-songs', () => {
    return loadSongs();
});

ipcMain.handle('select-random', (event, criteria) => {
    const songs = loadSongs();
    let filtered = [...songs];
    
    if (criteria.song_type) {
        filtered = filtered.filter(s => s.type === criteria.song_type);
    }
    
    if (criteria.genre) {
        filtered = filtered.filter(s => s.genre === criteria.genre);
    }
    
    if (criteria.min_level && criteria.difficulty) {
        filtered = filtered.filter(s => 
            (s.difficulties[criteria.difficulty] || 0) >= criteria.min_level
        );
    }
    
    if (criteria.max_level && criteria.difficulty) {
        filtered = filtered.filter(s => 
            (s.difficulties[criteria.difficulty] || 15) <= criteria.max_level
        );
    }
    
    const count = Math.min(criteria.count || 1, filtered.length);
    const selected = [];
    const tempFiltered = [...filtered];
    
    for (let i = 0; i < count && tempFiltered.length > 0; i++) {
        const index = Math.floor(Math.random() * tempFiltered.length);
        selected.push(tempFiltered.splice(index, 1)[0]);
    }
    
    return {
        songs: selected,
        total_available: filtered.length
    };
});

ipcMain.handle('add-song', (event, song) => {
    const songs = loadSongs();
    if (!songs.find(s => s.id === song.id)) {
        songs.push(song);
        saveSongs(songs);
        return true;
    }
    return false;
});
