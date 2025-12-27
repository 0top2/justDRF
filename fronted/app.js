// --- 配置 ---
const API_BASE = 'http://127.0.0.1:8000/api';
let accessToken = localStorage.getItem('access_token');

// 存储当前用户的完整信息
let currentUserInfo = null;

// 默认头像
const DEFAULT_AVATAR = 'https://ui-avatars.com/api/?background=0D8ABC&color=fff&name=User';

// --- 1. 初始化 ---

document.addEventListener('DOMContentLoaded', async () => {
    // 页面加载时：
    // 1. 如果有token，尝试获取用户信息
    if (accessToken) {
        await fetchUserInfo();
    }
    // 2. 更新导航栏 (显示登录按钮还是头像)
    updateNav();
    // 3. 默认显示首页 (文章列表)，无论是游客还是登录用户
    showHome();
    // 4. 预加载分类信息
    loadCategoriesAndTags();
});

// 获取当前用户信息
async function fetchUserInfo() {
    try {
        const response = await authFetch(`${API_BASE}/users/me/`);
        if (response.ok) {
            currentUserInfo = await response.json();
        } else {
            // Token 过期或无效
            handleLogout();
        }
    } catch (e) {
        console.error("获取用户信息失败", e);
    }
}

function switchSection(sectionId) {
    document.querySelectorAll('.page-section').forEach(el => el.classList.remove('active-section'));
    document.getElementById(sectionId).classList.add('active-section');
    const dropdown = document.querySelector('.dropdown');
    if(dropdown) dropdown.classList.remove('show-dropdown');
}

// --- 2. 导航栏与认证 ---

function updateNav() {
    const nav = document.getElementById('nav-auth');

    if (accessToken && currentUserInfo) {
        // 已登录：显示写文章按钮 + 头像
        const avatarUrl = currentUserInfo.avatar || `https://ui-avatars.com/api/?background=0D8ABC&color=fff&name=${currentUserInfo.username}`;

        nav.innerHTML = `
            <button class="btn-primary btn-small" onclick="showEditor()">✍️ 写文章</button>
            
            <div class="dropdown" id="user-dropdown">
                <img src="${avatarUrl}" class="user-avatar-nav" onclick="toggleDropdown()" title="${currentUserInfo.username}">
                <div class="dropdown-content">
                    <div style="padding: 10px 16px; border-bottom: 1px solid #eee; color: #888; font-size: 0.8rem;">
                        ${currentUserInfo.username}
                    </div>
                    <a onclick="showProfile()">👤 个人中心</a>
                    <a onclick="handleLogout()" style="color: #dc3545;">🚪 退出登录</a>
                </div>
            </div>
        `;
    } else {
        // 未登录：显示登录按钮
        nav.innerHTML = `<button class="btn-primary btn-small" onclick="showLogin()">登录</button>`;
    }
}

function toggleDropdown() {
    const dropdown = document.getElementById("user-dropdown");
    dropdown.classList.toggle("show-dropdown");
}

async function handleLogin() {
    const username = document.getElementById('username').value;
    const password = document.getElementById('password').value;

    try {
        const response = await fetch(`${API_BASE}/token/login/`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ username, password })
        });

        if (response.ok) {
            const data = await response.json();
            localStorage.setItem('access_token', data.access);
            localStorage.setItem('refresh_token', data.refresh);
            accessToken = data.access;

            await fetchUserInfo();

            alert('登录成功！');
            updateNav();
            showHome();
        } else {
            alert('登录失败，请检查账号密码');
        }
    } catch (error) {
        alert('登录出错');
    }
}

// 退出登录：清空信息并留在首页(变成游客状态)
function handleLogout() {
    localStorage.removeItem('access_token');
    localStorage.removeItem('refresh_token');
    accessToken = null;
    currentUserInfo = null;
    updateNav();
    showHome();
}

// --- 3. 个人中心逻辑 ---

function showProfile() {
    if (!currentUserInfo) return;
    switchSection('profile-view');

    document.getElementById('profile-username-display').innerText = currentUserInfo.username;
    document.getElementById('profile-id-display').innerText = currentUserInfo.id;

    document.getElementById('profile-avatar-input').value = currentUserInfo.avatar || '';
    document.getElementById('profile-bio-input').value = currentUserInfo.bio || '';
    document.getElementById('profile-email-input').value = currentUserInfo.email || '';

    updateAvatarPreview(currentUserInfo.avatar);
}

function updateAvatarPreview(url) {
    const img = document.getElementById('profile-avatar-preview');
    img.src = url || `https://ui-avatars.com/api/?background=0D8ABC&color=fff&name=${currentUserInfo?.username}`;
}

async function updateProfile() {
    const avatar = document.getElementById('profile-avatar-input').value;
    const bio = document.getElementById('profile-bio-input').value;
    const email = document.getElementById('profile-email-input').value;

    try {
        const response = await authFetch(`${API_BASE}/users/me/`, {
            method: 'PATCH',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ avatar, bio, email })
        });

        if (response.ok) {
            alert('修改成功！');
            await fetchUserInfo();
            updateNav();
            showProfile();
        } else {
            alert('修改失败');
        }
    } catch (e) {
        alert('网络错误');
    }
}


// --- 4. 博客核心业务逻辑 ---

// 封装 fetch，自动添加 Token
async function authFetch(url, options = {}) {
    if (accessToken) {
        options.headers = {
            ...options.headers,
            'Authorization': `Bearer ${accessToken}`
        };
    }
    return fetch(url, options);
}

function showHome() { switchSection('list-view'); loadPosts(); }
function showLogin() { switchSection('login-view'); }

async function loadPosts(search = '') {
    const container = document.getElementById('posts-container');
    container.innerHTML = '<p>加载中...</p>';
    let url = `${API_BASE}/articles/?ordering=-created_at`;
    if (search) url += `&search=${search}`;

    try {
        // 游客也可以调用这个接口 (后端 IsAuthenticatedOrReadOnly)
        const response = await fetch(url);
        const data = await response.json();
        const posts = data.results ? data.results : data;

        if (posts.length === 0) { container.innerHTML = '<p>暂无文章。</p>'; return; }

        container.innerHTML = posts.map(post => {
            const authorAvatar = post.author && post.author.avatar
                ? post.author.avatar
                : `https://ui-avatars.com/api/?background=eee&color=333&name=${post.author ? post.author.username : 'U'}`;

            return `
            <div class="post-card">
                <div class="post-meta">
                    <div style="display:flex; align-items:center; gap:5px;">
                        <img src="${authorAvatar}" style="width:20px; height:20px; border-radius:50%;">
                        <span>${post.author ? post.author.username : '未知用户'}</span>
                    </div>
                    <span>📂 ${post.category ? post.category.name : '未分类'}</span>
                </div>
                <h3 class="post-title"><a onclick="loadPostDetail(${post.id})">${post.title}</a></h3>
                <p class="post-summary">${post.summary}</p>
                <div class="tags">${post.tags.map(tag => `<span>#${tag.name}</span>`).join('')}</div>
                <div style="margin-top: 10px; font-size: 0.8rem; color: #aaa;">
                    ${new Date(post.created_at).toLocaleString()} | 👁️ ${post.views || 0} 阅读
                </div>
            </div>
        `}).join('');
    } catch (error) { container.innerHTML = '<p>加载失败</p>'; }
}

async function loadPostDetail(id) {
    try {
        const response = await authFetch(`${API_BASE}/articles/${id}/`);
        const post = await response.json();
        switchSection('detail-view');

        const isAuthor = currentUserInfo && post.author && (post.author.username === currentUserInfo.username);
        const actionButtons = isAuthor ? `
            <div class="action-buttons">
                <button class="btn-primary btn-small" onclick='showEditor(true, ${JSON.stringify(post)})'>编辑文章</button>
                <button class="btn-danger btn-small" onclick="deletePost(${post.id})">删除文章</button>
            </div>` : '';

        document.getElementById('article-content').innerHTML = `
            <div class="detail-header">
                <h1>${post.title}</h1>
                <p>分类: ${post.category?.name || '-'} | 时间: ${new Date(post.created_at).toLocaleString()}</p>
            </div>
            <div class="detail-body">${post.body}</div>
            ${actionButtons}
        `;
    } catch (error) { alert("无法加载详情"); }
}

function showEditor(isEdit = false, postData = null) {
    if (!currentUserInfo) { alert("请先登录"); return showLogin(); }
    switchSection('editor-view');
    if(isEdit && postData) {
        document.getElementById('edit-post-id').value = postData.id;
        document.getElementById('post-title').value = postData.title;
        document.getElementById('post-body').value = postData.body;
        document.getElementById('post-category').value = postData.category?.id || '';
    } else {
        document.getElementById('edit-post-id').value = '';
        document.getElementById('post-title').value = '';
        document.getElementById('post-body').value = '';
    }
}

async function submitPost() {
    const id = document.getElementById('edit-post-id').value;
    const title = document.getElementById('post-title').value;
    const body = document.getElementById('post-body').value;
    const category = document.getElementById('post-category').value;
    const tagsSelect = document.getElementById('post-tags');
    const tags_ids = Array.from(tagsSelect.selectedOptions).map(o => o.value);

    const payload = { title, body, category, tags_ids, status: 'published' };
    const method = id ? 'PATCH' : 'POST';
    const url = id ? `${API_BASE}/articles/${id}/` : `${API_BASE}/articles/`;

    const res = await authFetch(url, { method, headers:{'Content-Type':'application/json'}, body: JSON.stringify(payload)});
    if(res.ok) { alert('成功'); showHome(); } else { alert('失败'); }
}

async function deletePost(id) {
    if(confirm('删除?')) {
        const res = await authFetch(`${API_BASE}/articles/${id}/`, { method: 'DELETE' });
        if(res.ok) { alert('已删除'); showHome(); }
    }
}

async function loadCategoriesAndTags() {
    try {
        const res = await fetch(`${API_BASE}/categories/`);
        const data = await res.json();
        const cats = data.results || data;
        document.getElementById('post-category').innerHTML = cats.map(c => `<option value="${c.id}">${c.name}</option>`).join('');
        document.getElementById('post-tags').innerHTML = `<option value="1">Python</option><option value="2">Django</option>`;
    } catch(e){}
}