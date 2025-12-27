// --- 配置 ---
const API_BASE = 'http://127.0.0.1:8000/api';
// 从 LocalStorage 获取 Token，如果不存在则为 null
let accessToken = localStorage.getItem('access_token');
let currentUser = localStorage.getItem('username');

// --- 1. 页面导航与初始化 ---

// 页面加载完成后执行
document.addEventListener('DOMContentLoaded', () => {
    updateNav();
    showHome(); // 默认显示首页
    loadCategoriesAndTags(); // 预加载分类和标签供编辑器使用
});

// 切换页面显示
function switchSection(sectionId) {
    document.querySelectorAll('.page-section').forEach(el => el.classList.remove('active-section'));
    document.getElementById(sectionId).classList.add('active-section');
}

function showHome() {
    switchSection('list-view');
    loadPosts();
}

function showLogin() {
    switchSection('login-view');
}

function showEditor(isEdit = false, postData = null) {
    if (!accessToken) {
        alert("请先登录！");
        return showLogin();
    }
    switchSection('editor-view');

    // 重置或填充表单
    if (isEdit && postData) {
        document.getElementById('editor-title').innerText = "修改文章";
        document.getElementById('edit-post-id').value = postData.id;
        document.getElementById('post-title').value = postData.title;
        document.getElementById('post-body').value = postData.body;
        document.getElementById('post-category').value = postData.category ? postData.category.id : '';
        // 简单的标签回显处理（高级处理需要遍历）
        // 暂时留空标签，用户需重新选择
    } else {
        document.getElementById('editor-title').innerText = "发布新文章";
        document.getElementById('edit-post-id').value = '';
        document.getElementById('post-title').value = '';
        document.getElementById('post-body').value = '';
    }
}

// --- 2. 认证逻辑 (Auth) ---

function updateNav() {
    const nav = document.getElementById('nav-auth');
    if (accessToken) {
        nav.innerHTML = `
            <span>欢迎, <b>${currentUser}</b></span>
            <button class="btn-primary" onclick="showEditor()">✍️ 写文章</button>
            <button class="btn-outline" onclick="handleLogout()">退出</button>
        `;
    } else {
        nav.innerHTML = `<button class="btn-primary" onclick="showLogin()">登录</button>`;
    }
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
            // 保存 Token 到本地
            localStorage.setItem('access_token', data.access);
            localStorage.setItem('refresh_token', data.refresh);
            localStorage.setItem('username', username);

            accessToken = data.access;
            currentUser = username;

            alert('登录成功！');
            updateNav();
            showHome();
        } else {
            alert('登录失败，请检查账号密码');
        }
    } catch (error) {
        console.error('Login Error:', error);
        alert('网络错误，请检查后端是否启动');
    }
}

function handleLogout() {
    localStorage.removeItem('access_token');
    localStorage.removeItem('refresh_token');
    localStorage.removeItem('username');
    accessToken = null;
    currentUser = null;
    updateNav();
    showHome();
}

// --- 3. 核心业务逻辑 (API Calls) ---

// 通用 Fetch 封装 (自动带上 Token)
async function authFetch(url, options = {}) {
    if (accessToken) {
        options.headers = {
            ...options.headers,
            'Authorization': `Bearer ${accessToken}`
        };
    }
    return fetch(url, options);
}

// 加载文章列表
async function loadPosts(search = '') {
    const container = document.getElementById('posts-container');
    container.innerHTML = '<p>加载中...</p>';

    let url = `${API_BASE}/articles/?ordering=-created_at`;
    if (search) {
        url += `&search=${search}`;
    }

    try {
        const response = await fetch(url); // GET 列表不需要权限，所有人可看
        const data = await response.json();

        // 注意：如果你开启了分页，data.results 才是数据；如果是列表，data 就是数据
        const posts = data.results ? data.results : data;

        if (posts.length === 0) {
            container.innerHTML = '<p>暂无文章。</p>';
            return;
        }

        container.innerHTML = posts.map(post => `
            <div class="post-card">
                <div class="post-meta">
                    <span>👤 ${post.author ? post.author.username : '未知用户'}</span>
                    <span>📂 ${post.category ? post.category.name : '未分类'}</span>
                </div>
                <h3 class="post-title"><a onclick="loadPostDetail(${post.id})">${post.title}</a></h3>
                <p class="post-summary">${post.summary}</p>
                <div class="tags">
                    ${post.tags.map(tag => `<span>#${tag.name}</span>`).join('')}
                </div>
                <div style="margin-top: 10px; font-size: 0.8rem; color: #aaa;">
                    发布于: ${new Date(post.created_at).toLocaleString()} | 👁️ ${post.views || 0} 阅读
                </div>
            </div>
        `).join('');

    } catch (error) {
        console.error('Load Posts Error:', error);
        container.innerHTML = '<p style="color:red">加载失败，请检查后端服务。</p>';
    }
}

// 加载文章详情
async function loadPostDetail(id) {
    try {
        const response = await authFetch(`${API_BASE}/articles/${id}/`);
        const post = await response.json();

        switchSection('detail-view');

        // 判断当前用户是不是作者
        const isAuthor = currentUser && post.author && (post.author.username === currentUser);

        const actionButtons = isAuthor ? `
            <div class="action-buttons">
                <button class="btn-primary" onclick='showEditor(true, ${JSON.stringify(post)})'>编辑文章</button>
                <button class="btn-danger" onclick="deletePost(${post.id})">删除文章</button>
            </div>
        ` : '';

        document.getElementById('article-content').innerHTML = `
            <div class="detail-header">
                <h1>${post.title}</h1>
                <p style="color: #666;">
                    作者: ${post.author.username} | 分类: ${post.category?.name || '-'} | 时间: ${new Date(post.created_at).toLocaleString()}
                </p>
            </div>
            <div class="detail-body">${post.body}</div>
            ${actionButtons}
        `;

    } catch (error) {
        alert("无法加载文章详情");
    }
}

// 加载分类和标签 (供编辑器下拉框使用)
async function loadCategoriesAndTags() {
    try {
        // 假设你有 /api/categories/ 接口
        const catRes = await fetch(`${API_BASE}/categories/`);
        const categories = await catRes.json();
        // 如果有分页
        const catList = categories.results ? categories.results : categories;

        const catSelect = document.getElementById('post-category');
        catSelect.innerHTML = catList.map(c => `<option value="${c.id}">${c.name}</option>`).join('');

        // 假设这里暂时没有 /api/tags/ 接口，可以手动造几个或者从文章里提取
        // 这里为了演示，我们假设后端没有独立的 tags 列表接口，先写死几个测试
        // 实际开发中你需要写一个 TagViewSet
        const tagSelect = document.getElementById('post-tags');
        tagSelect.innerHTML = `<option value="1">Python</option><option value="2">Django</option>`;

    } catch (e) {
        console.log("加载辅助数据失败", e);
    }
}

// 提交文章 (新建 POST 或 修改 PATCH)
async function submitPost() {
    const id = document.getElementById('edit-post-id').value;
    const title = document.getElementById('post-title').value;
    const body = document.getElementById('post-body').value;
    const category = document.getElementById('post-category').value;

    // 获取多选标签
    const tagsSelect = document.getElementById('post-tags');
    const tags_ids = Array.from(tagsSelect.selectedOptions).map(option => option.value);

    const payload = { title, body, category, tags_ids, status: 'published' };

    const method = id ? 'PATCH' : 'POST';
    const url = id ? `${API_BASE}/articles/${id}/` : `${API_BASE}/articles/`;

    try {
        const response = await authFetch(url, {
            method: method,
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(payload)
        });

        if (response.ok) {
            alert(id ? '修改成功' : '发布成功');
            showHome();
        } else {
            const err = await response.json();
            alert('提交失败: ' + JSON.stringify(err));
        }
    } catch (error) {
        alert('提交出错');
    }
}

// 删除文章
async function deletePost(id) {
    if (!confirm('确定要删除这篇文章吗？')) return;

    try {
        const response = await authFetch(`${API_BASE}/articles/${id}/`, {
            method: 'DELETE'
        });

        if (response.ok) {
            alert('已删除');
            showHome();
        } else {
            alert('删除失败，可能没有权限');
        }
    } catch (error) {
        alert('网络错误');
    }
}