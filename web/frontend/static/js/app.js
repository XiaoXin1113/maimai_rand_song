const API_BASE = '/api';
const COVER_BASE_URL = 'https://shama.dxrating.net/images/cover/v2';

function getCoverUrl(imageName) {
    return `${COVER_BASE_URL}/${imageName}.jpg`;
}

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
        const data = await fetchAPI('/stats');
        const container = document.getElementById('songListContainer');
        
        container.innerHTML = `
            <div class="song-stats">
                <p><strong>总歌曲数：</strong>${data.total_songs}</p>
                <p><strong>总谱面数：</strong>${data.total_charts}</p>
                <p class="hint">使用上方选歌功能随机选择歌曲</p>
            </div>
        `;
    } catch (error) {
        console.error('Failed to load stats:', error);
        document.getElementById('songListContainer').innerHTML = 
            '<p class="placeholder">加载失败，请刷新重试</p>';
    }
}

async function selectSongs(event) {
    event.preventDefault();
    
    const difficultyMap = {
        'Easy': 'easy',
        'Basic': 'basic',
        'Advanced': 'advanced',
        'Expert': 'expert',
        'Master': 'master',
        'Re:Master': 'remaster'
    };
    
    const typeMap = {
        '': null,
        'std': 'std',
        'DX': 'dx'
    };
    
    const diffValue = document.getElementById('difficulty').value;
    const typeValue = document.getElementById('songType').value;
    
    const formData = {
        difficulty: difficultyMap[diffValue] || null,
        min_level: parseFloat(document.getElementById('minLevel').value) || null,
        max_level: parseFloat(document.getElementById('maxLevel').value) || null,
        song_type: typeMap[typeValue] || null,
        genre: document.getElementById('genre').value || null,
        count: parseInt(document.getElementById('count').value) || 1,
        utage_only: document.getElementById('utage').checked
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
        ${result.songs.map(song => {
            const chartsByType = {};
            song.charts.forEach(chart => {
                const typeKey = chart.type;
                if (!chartsByType[typeKey]) chartsByType[typeKey] = [];
                chartsByType[typeKey].push(chart);
            });
            
            let chartsHtml = '';
            for (const [type, charts] of Object.entries(chartsByType)) {
                chartsHtml += `<div style="margin-top: 5px;"><strong>${type}:</strong> `;
                chartsHtml += charts.map(c => {
                    const levelDisplay = c.internal_level ? `${c.level} (${c.internal_level})` : c.level;
                    // 使用谱面ID（优先使用真实ID，没有时使用计算的ID）
                    const chartId = c.id || (c.type === 'dx' ? song.id + 10000 : song.id);
                    return `${c.difficulty} ${levelDisplay} (ID: ${chartId})`;
                }).join(' | ');
                chartsHtml += '</div>';
            }
            
            const coverUrl = song.image_url ? getCoverUrl(song.image_url) : '';
            
            return `
            <div class="result-card" style="display: flex; gap: 15px;">
                <div class="cover-container" style="flex-shrink: 0;">
                    <img src="${coverUrl}" alt="${song.title}" 
                         style="width: 120px; height: 120px; object-fit: cover; border-radius: 8px; box-shadow: 0 2px 8px rgba(0,0,0,0.1);"
                         onerror="this.onerror=null; this.src='data:image/svg+xml,<svg xmlns=%22http://www.w3.org/2000/svg%22 width=%22120%22 height=%22120%22><rect fill=%22%23333%22 width=%22120%22 height=%22120%22/><text x=%2250%%22 y=%2250%%22 fill=%22%23666%22 text-anchor=%22middle%22 dy=%22.3em%22>No Image</text></svg>'">
                </div>
                <div class="song-info" style="flex: 1;">
                    <h3>🎵 ${song.title}</h3>
                    <p><strong>艺术家：</strong>${song.artist}</p>
                    <p><strong>类型：</strong>${song.type}</p>
                    ${song.genre ? `<p><strong>流派：</strong>${song.genre}</p>` : ''}
                    ${song.bpm ? `<p><strong>BPM：</strong>${song.bpm}</p>` : ''}
                    <div style="margin-top: 10px;">
                        <strong>谱面：</strong>
                        ${chartsHtml}
                    </div>
                </div>
            </div>
        `}).join('')}
    `;
}

document.addEventListener('DOMContentLoaded', () => {
    loadGenres();
    loadSongs();
    
    document.getElementById('selectionForm').addEventListener('submit', selectSongs);
});
