const API_BASE = '/api';

async function fetchAPI(endpoint, options = {}) {
    try {
        const response = await fetch(`${API_BASE}${endpoint}`, options);
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        return await response.json();
    } catch (error) {
        console.error('API Error:', error);
        throw error;
    }
}

async function loadGenres() {
    try {
        const data = await fetchAPI('/genres');
        const genreSelect = document.getElementById('genre');
        data.genres.forEach(genre => {
            const option = document.createElement('option');
            option.value = genre;
            option.textContent = genre;
            genreSelect.appendChild(option);
        });
    } catch (error) {
        console.error('Failed to load genres:', error);
    }
}

async function loadSongs() {
    try {
        const data = await fetchAPI('/songs');
        const container = document.getElementById('songListContainer');
        
        if (data.songs.length === 0) {
            container.innerHTML = '<p class="placeholder">暂无歌曲数据</p>';
            return;
        }
        
        container.innerHTML = data.songs.map(song => `
            <div class="song-item">
                <h4>${song.title}</h4>
                <p>艺术家：${song.artist} | 类型：${song.type}</p>
                ${song.genre ? `<p>流派：${song.genre}</p>` : ''}
            </div>
        `).join('');
    } catch (error) {
        console.error('Failed to load songs:', error);
        document.getElementById('songListContainer').innerHTML = 
            '<p class="placeholder">加载失败，请刷新重试</p>';
    }
}

async function selectSongs(event) {
    event.preventDefault();
    
    const formData = {
        difficulty: document.getElementById('difficulty').value || null,
        min_level: parseFloat(document.getElementById('minLevel').value) || null,
        max_level: parseFloat(document.getElementById('maxLevel').value) || null,
        song_type: document.getElementById('songType').value || null,
        genre: document.getElementById('genre').value || null,
        count: parseInt(document.getElementById('count').value) || 1
    };
    
    try {
        const result = await fetchAPI('/select', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(formData)
        });
        
        displayResults(result);
    } catch (error) {
        console.error('Selection failed:', error);
        document.getElementById('resultContainer').innerHTML = 
            '<p class="placeholder">选歌失败，请重试</p>';
    }
}

function displayResults(result) {
    const container = document.getElementById('resultContainer');
    
    if (result.songs.length === 0) {
        container.innerHTML = '<p class="placeholder">没有找到符合条件的歌曲</p>';
        return;
    }
    
    container.innerHTML = `
        <p style="margin-bottom: 15px; color: #666;">
            共找到 ${result.total_available} 首符合条件的歌曲
        </p>
        ${result.songs.map(song => `
            <div class="result-card">
                <h3>🎵 ${song.title}</h3>
                <p><strong>艺术家：</strong>${song.artist}</p>
                <p><strong>类型：</strong>${song.type}</p>
                ${song.genre ? `<p><strong>流派：</strong>${song.genre}</p>` : ''}
                ${song.bpm ? `<p><strong>BPM：</strong>${song.bpm}</p>` : ''}
                <div style="margin-top: 10px;">
                    <strong>难度：</strong>
                    ${Object.entries(song.difficulties).map(([diff, level]) => 
                        `<span style="margin-right: 10px;">${diff}: ${level}</span>`
                    ).join('')}
                </div>
            </div>
        `).join('')}
    `;
}

document.addEventListener('DOMContentLoaded', () => {
    loadGenres();
    loadSongs();
    
    document.getElementById('selectionForm').addEventListener('submit', selectSongs);
});
