from flask import Flask, request, jsonify, session, render_template_string
from werkzeug.security import generate_password_hash, check_password_hash
import sqlite3
from datetime import datetime
import os
import time
import uuid

from payos import PayOS
from payos.types import CreatePaymentLinkRequest

app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY", "dev-secret-key-change-me")

DB_NAME = "store.db"

# =========================
# CHI SUA 4 DONG NAY
# =========================
PAYOS_CLIENT_ID = "1e604dec-ae1a-4aba-99a1-a49fc4ccb3f3"
PAYOS_API_KEY = "102e4d15-991c-4f4c-822c-fb892aa410b3"
PAYOS_CHECKSUM_KEY = "b7996ff7ccd8857e49d282aaa0b1cf559e6489ec6c23b1bc58676286eb0f95f1"
# NOTE: PUBLIC_BASE_URL must be public and support HTTPS (e.g. https://xxxx.ngrok.io/)
PUBLIC_BASE_URL = os.getenv("PUBLIC_BASE_URL", "https://your-ngrok-domain.ngrok.io/")
# =========================

WEBHOOK_PATH = "/api/payos/webhook"
WEBHOOK_URL = f"{PUBLIC_BASE_URL.rstrip('/')}{WEBHOOK_PATH}"

payos = PayOS(
    client_id=PAYOS_CLIENT_ID,
    api_key=PAYOS_API_KEY,
    checksum_key=PAYOS_CHECKSUM_KEY
)

TELEGRAM_GROUP_LINK = "https://t.me/+EGNDhYoGHFwxMWVl"
ZALO_CONTACT = "0907574776"

HTML_PAGE = r"""
<!DOCTYPE html>
<html lang="vi">
<head>
    <meta charset="UTF-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1" />
    <title>Vũ Quốc Khánh Store</title>
    <style>
        :root{
            --bg:#f5f9ff;
            --bg2:#eef5ff;
            --card:#ffffff;
            --line:#dbe7f5;
            --text:#0f172a;
            --muted:#64748b;
            --primary:#2563eb;
            --primary2:#60a5fa;
            --success:#16a34a;
            --danger:#e11d48;
            --warning:#d97706;
            --shadow:0 10px 30px rgba(15,23,42,.08);
            --radius:18px;
        }

        *{box-sizing:border-box}
        html{scroll-behavior:smooth}
        body{
            margin:0;
            font-family:Arial,sans-serif;
            color:var(--text);
            background:
                radial-gradient(circle at top left, rgba(96,165,250,.18), transparent 24%),
                radial-gradient(circle at bottom right, rgba(37,99,235,.08), transparent 24%),
                linear-gradient(180deg, #f8fbff 0%, #f3f7fc 100%);
        }
        a{text-decoration:none;color:inherit}
        button,input,select,textarea{font:inherit}

        .container{
            max-width:1140px;
            margin:0 auto;
            padding:0 16px;
        }

        header{
            position:sticky;
            top:0;
            z-index:1000;
            background:rgba(255,255,255,.88);
            backdrop-filter:blur(12px);
            border-bottom:1px solid var(--line);
        }

        .topbar{
            display:flex;
            justify-content:space-between;
            align-items:center;
            gap:12px;
            flex-wrap:wrap;
            padding:14px 0 10px;
            position:relative;
        }

        .menu-toggle{
            display:none;
            width:44px;
            height:44px;
            border:1px solid var(--line);
            background:#fff;
            border-radius:12px;
            cursor:pointer;
            font-size:22px;
            font-weight:700;
            align-items:center;
            justify-content:center;
            box-shadow:var(--shadow);
        }

        .brand-badge{
            display:inline-flex;
            align-items:center;
            gap:6px;
            padding:7px 12px;
            border-radius:999px;
            background:linear-gradient(135deg, rgba(37,99,235,.10), rgba(96,165,250,.16));
            color:var(--primary);
            border:1px solid rgba(37,99,235,.12);
            font-size:11px;
            font-weight:800;
            letter-spacing:.3px;
        }

        .brand h1{
            margin:10px 0 4px;
            font-size:30px;
            line-height:1.05;
        }

        .brand p{
            margin:0;
            color:var(--muted);
            font-size:15px;
            line-height:1.6;
            max-width:760px;
        }

        .user-box{
            min-width:240px;
            background:linear-gradient(180deg,#fff,#f8fbff);
            border:1px solid var(--line);
            border-radius:16px;
            padding:12px 14px;
            box-shadow:var(--shadow);
        }

        .user-box .small{
            font-size:12px;
            color:var(--muted);
        }

        .user-box .money{
            font-size:16px;
            font-weight:800;
            color:var(--success);
            margin-top:4px;
        }

        .menu-overlay{
            display:none;
        }

        nav{
            display:flex;
            gap:8px;
            flex-wrap:wrap;
            padding:0 0 12px;
        }

        nav button{
            border:1px solid var(--line);
            background:#fff;
            border-radius:12px;
            padding:10px 14px;
            cursor:pointer;
            font-weight:700;
            transition:.2s ease;
        }

        nav button:hover,
        nav button.active{
            background:var(--primary);
            color:#fff;
            border-color:var(--primary);
            transform:translateY(-1px);
        }

        .notice{
            display:none;
            margin:18px 0 6px;
            padding:14px 16px;
            border-radius:14px;
            background:#ecfdf3;
            border:1px solid #bbf7d0;
            color:#166534;
            box-shadow:var(--shadow);
        }

        .section{
            display:none;
            padding:26px 0 40px;
        }

        .section.active{
            display:block;
        }

        .hero{
            display:grid;
            grid-template-columns:1.15fr .85fr;
            gap:20px;
            align-items:stretch;
        }

        .hero-main,
        .card,
        .product-card{
            background:linear-gradient(180deg, #ffffff, #f8fbff);
            border:1px solid var(--line);
            border-radius:24px;
            box-shadow:var(--shadow);
        }

        .hero-main{
            padding:34px;
            position:relative;
            overflow:hidden;
        }

        .hero-main::after{
            content:'';
            position:absolute;
            right:-50px;
            top:-50px;
            width:180px;
            height:180px;
            border-radius:50%;
            background:radial-gradient(circle, rgba(37,99,235,.12), transparent 70%);
        }

        .hero-main h2{
            font-size:46px;
            line-height:1.05;
            margin:14px 0 14px;
            max-width:740px;
        }

        .hero-main p{
            color:var(--muted);
            font-size:16px;
            line-height:1.8;
            max-width:720px;
        }

        .hero-actions{
            display:flex;
            gap:12px;
            flex-wrap:wrap;
            margin-top:24px;
        }

        .btn{
            border:0;
            border-radius:14px;
            padding:13px 18px;
            cursor:pointer;
            font-weight:800;
            display:inline-flex;
            align-items:center;
            justify-content:center;
            gap:8px;
            transition:.2s ease;
        }

        .btn:hover{
            transform:translateY(-1px);
        }

        .btn-primary{
            background:linear-gradient(135deg,#2563eb,#3b82f6);
            color:#fff;
        }

        .btn-green{
            background:linear-gradient(135deg,#22c55e,#16a34a);
            color:#fff;
        }

        .btn-dark{
            background:#e2e8f0;
            color:#0f172a;
            border:1px solid #cbd5e1;
        }

        .btn-danger{
            background:#fff1f2;
            color:#be123c;
            border:1px solid #fecdd3;
        }

        .stats{
            display:grid;
            grid-template-columns:repeat(2,1fr);
            gap:16px;
        }

        .stat{
            padding:22px;
            position:relative;
            overflow:hidden;
        }

        .stat::before{
            content:'';
            position:absolute;
            right:-10px;
            bottom:-10px;
            width:60px;
            height:60px;
            border-radius:50%;
            background:radial-gradient(circle, rgba(37,99,235,.10), transparent 70%);
        }

        .stat .label{
            font-size:13px;
            color:var(--muted);
        }

        .stat .value{
            font-size:32px;
            font-weight:800;
            margin-top:10px;
            color:#0b1220;
        }

        .home-grid{
            display:grid;
            grid-template-columns:1fr 1fr 1fr;
            gap:16px;
            margin-top:20px;
        }

        .feature{
            padding:20px;
        }

        .feature h3{
            margin:0 0 10px;
            font-size:20px;
        }

        .feature p{
            margin:0;
            color:var(--muted);
            line-height:1.7;
            font-size:14px;
        }

        .grid-2{
            display:grid;
            grid-template-columns:1fr 1fr;
            gap:20px;
        }

        .card{
            padding:20px;
        }

        .products{
            display:grid;
            grid-template-columns:repeat(2, 1fr);
            gap:14px;
        }

        .product-card{
            padding:18px;
        }

        .product-card h3{
            margin:0 0 10px;
            font-size:20px;
        }

        .product-card p{
            color:var(--muted);
            line-height:1.6;
            min-height:50px;
        }

        .badge{
            display:inline-flex;
            align-items:center;
            padding:6px 10px;
            border-radius:999px;
            background:#eff6ff;
            border:1px solid #bfdbfe;
            color:#1d4ed8;
            font-size:12px;
            font-weight:700;
        }

        .muted{
            color:var(--muted);
            font-size:13px;
        }

        .price{
            font-size:26px;
            color:var(--success);
            font-weight:800;
            margin:12px 0;
        }

        input, textarea, select{
            width:100%;
            padding:13px 14px;
            border-radius:12px;
            border:1px solid var(--line);
            margin-bottom:12px;
            background:#fff;
            color:var(--text);
            outline:none;
        }

        input:focus, textarea:focus, select:focus{
            border-color:rgba(37,99,235,.45);
            box-shadow:0 0 0 4px rgba(37,99,235,.08);
        }

        .list{
            display:grid;
            gap:12px;
        }

        .item{
            background:#fff;
            border:1px solid var(--line);
            border-radius:16px;
            padding:14px;
        }

        .status{
            display:inline-block;
            margin-top:8px;
            padding:6px 10px;
            border-radius:999px;
            font-size:12px;
            font-weight:700;
        }

        .success{background:#ecfdf3;color:#15803d;border:1px solid #bbf7d0}
        .warning{background:#fff7ed;color:#b45309;border:1px solid #fed7aa}
        .danger{background:#fff1f2;color:#be123c;border:1px solid #fecdd3}

        .empty{
            padding:18px;
            text-align:center;
            color:var(--muted);
            border:1px dashed #cbd5e1;
            border-radius:14px;
            background:#f8fafc;
        }

        .row{
            display:flex;
            gap:10px;
            flex-wrap:wrap;
        }

        .row > div{
            flex:1;
            min-width:180px;
        }

        .key{
            display:block;
            margin-top:10px;
            padding:10px 12px;
            border-radius:10px;
            background:#f0fdf4;
            border:1px solid #bbf7d0;
            color:#166534;
            word-break:break-all;
            font-family:monospace;
            white-space:pre-wrap;
        }

        img.qr{
            width:260px;
            max-width:100%;
            background:#fff;
            padding:10px;
            border-radius:12px;
            border:1px solid var(--line);
        }

        .highlight{
            background:linear-gradient(180deg,#f8fbff,#f1f7ff);
            border:1px solid #dbeafe;
            border-radius:18px;
            padding:16px;
        }

        @media (max-width: 980px){
            .hero,
            .grid-2,
            .home-grid{
                grid-template-columns:1fr;
            }
            .products{
                grid-template-columns:1fr;
            }
        }

        @media (max-width: 680px){
            .container{
                padding:0 12px;
            }

            .topbar{
                gap:8px;
                padding:10px 0 8px;
                align-items:flex-start;
            }

            .menu-toggle{
                display:flex;
                position:fixed;
                top:14px;
                left:14px;
                z-index:1202;
            }

            .brand{
                width:100%;
                padding-left:58px;
            }

            .brand h1{
                font-size:22px;
                margin:6px 0 3px;
            }

            .brand p{
                font-size:13px;
                line-height:1.45;
                max-width:100%;
            }

            .user-box{
                width:100%;
                min-width:0;
                padding:8px 10px;
                border-radius:12px;
            }

            .user-box .small{font-size:11px}
            .user-box .money{font-size:15px}

            .menu-overlay{
                display:block;
                position:fixed;
                inset:0;
                background:rgba(0,0,0,.22);
                opacity:0;
                visibility:hidden;
                transition:.25s ease;
                z-index:1198;
            }

            .menu-overlay.show{
                opacity:1;
                visibility:visible;
            }

            nav{
                position:fixed;
                top:0;
                left:0;
                width:280px;
                max-width:84vw;
                height:100vh;
                background:#fff;
                border-right:1px solid var(--line);
                box-shadow:0 16px 40px rgba(0,0,0,.12);
                padding:78px 14px 20px;
                display:flex;
                flex-direction:column;
                flex-wrap:nowrap;
                gap:8px;
                overflow-y:auto;
                transform:translateX(-100%);
                transition:transform .28s ease;
                z-index:1200;
            }

            nav.show{
                transform:translateX(0);
            }

            nav button{
                width:100%;
                text-align:left;
                padding:12px 14px;
                border-radius:12px;
            }

            .hero-main{
                padding:24px;
            }

            .hero-main h2{
                font-size:34px;
            }

            .stats{
                grid-template-columns:1fr;
            }
        }
    </style>
</head>
<body>
<header>
    <div class="container">
        <div class="topbar">
            <button class="menu-toggle" id="menuToggle" onclick="toggleMobileMenu()">☰</button>

            <div class="brand">
                <div class="brand-badge">PREMIUM Key STORE</div>
                <h1>Vũ Quốc Khánh Store</h1>
                <p>Mua hàng trên 5 key hack tháng được giảm giá 20%</p>
            </div>

            <div class="user-box">
                <div class="small" id="userInfoTop">Chưa đăng nhập</div>
                <div class="money" id="userInfoMoney">Số dư: 0đ</div>
            </div>
        </div>

        <div class="menu-overlay" id="menuOverlay" onclick="closeMobileMenu()"></div>
        <nav id="menu"></nav>
    </div>
</header>

<main class="container">
    <div class="notice" id="notice"></div>

    <section id="home" class="section active">
        <div class="hero">
            <div class="hero-main">
                <div class="brand-badge">HỆ THỐNG TỰ ĐỘNG</div>
                <h2>Mua Key hỗ trợ ngay 24/24 </h2>
                <p>
                    Cung cấp key và gói dịch vụ với quy trình thanh toán đơn giản, nạp tiền QR nhanh chóng,
                     xử lý đơn hàng tự động và hỗ trợ trực tiếp khi cần.
                     Tối ưu cho cả điện thoại và máy tính.
                </p>

                <div class="hero-actions">
                    <button class="btn btn-primary" onclick="showSection('shop')">Xem sản phẩm</button>
                    <button class="btn btn-green" onclick="showSection('wallet')">Nạp tiền ngay</button>
                </div>
            </div>

            <div class="stats">
                <div class="card stat">
                    <div class="label">Sản phẩm</div>
                    <div class="value" id="statProducts">0</div>
                </div>
                <div class="card stat">
                    <div class="label">Người dùng</div>
                    <div class="value" id="statUsers">0</div>
                </div>
                <div class="card stat">
                    <div class="label">Đơn hàng</div>
                    <div class="value" id="statOrders">0</div>
                </div>
                <div class="card stat">
                    <div class="label">Yêu cầu nạp</div>
                    <div class="value" id="statDeposits">0</div>
                </div>
            </div>
        </div>

        <div class="home-grid">
            <div class="card feature">
                <h3>⚡ Mua nhanh</h3>
                <p>Chọn sản phẩm, thêm giỏ hàng, thanh toán trong vài giây mà không phải nhắn tin thủ công.</p>
            </div>

            <div class="card feature">
                <h3>💳 Nạp tiền QR</h3>
                <p>Quét QR payOS và web tự kiểm tra, tự cộng tiền khi thanh toán thành công.</p>
            </div>

            <div class="card feature">
                <h3>🎯 Hỗ trợ nhận key</h3>
                <p>Sau khi mua xong có thể mở Telegram hoặc Zalo ngay để nhận key và được hỗ trợ nhanh hơn.</p>
            </div>
        </div>
    </section>

    <section id="shop" class="section">
        <div class="grid-2">
            <div class="card">
                <h2>Danh sách sản phẩm</h2>
                <input id="searchInput" placeholder="Tìm sản phẩm..." oninput="renderProducts()">
                <select id="categoryFilter" onchange="renderProducts()"></select>
                <div class="products" id="productsList"></div>
            </div>

            <div class="card">
                <h2>Giỏ hàng</h2>
                <div id="cartQuickList"></div>
                <div class="highlight" style="margin-top:14px;">
                    <div class="muted">Tổng thanh toán</div>
                    <div class="price" id="cartTotal">0đ</div>
                    <div class="row">
                        <div><button class="btn btn-dark" style="width:100%" onclick="showSection('cart')">Xem giỏ hàng</button></div>
                        <div><button class="btn btn-green" style="width:100%" onclick="checkout()">Thanh toán</button></div>
                    </div>
                </div>
            </div>
        </div>
    </section>

    <section id="cart" class="section">
        <div class="card">
            <h2>Chi tiết giỏ hàng</h2>
            <div id="cartPageList"></div>
        </div>
    </section>

    <section id="wallet" class="section">
        <div class="grid-2">
            <div class="card">
                <h2>Nạp tiền</h2>
                <div class="highlight">
                    <p>Nhập số tiền cần nạp rồi bấm tạo lệnh nạp.</p>
                    <p>Quét mã QR</p>
                    <p class="muted">Nếu chưa thấy cộng tiền ngay, bấm “Kiểm tra ngay”.</p>
                </div>

                <form onsubmit="createDeposit(event)" style="margin-top:16px;">
                    <input id="depositAmount" type="number" value="50000" placeholder="Số tiền nạp">
                    <input id="depositNote" placeholder="Ghi chú">
                    <button class="btn btn-green" type="submit">Tạo lệnh nạp</button>
                </form>

                <div id="qrArea" style="display:none; margin-top:16px;" class="highlight">
                    <p><b>Mã QR thanh toán</b></p>
                    <img id="qrImage" class="qr" />
                    <div class="row" style="margin-top:12px;">
                        <div><a id="checkoutLink" target="_blank" class="btn btn-primary" style="width:100%;">Mở trang thanh toán</a></div>
                        <div><button type="button" class="btn btn-dark" style="width:100%" onclick="checkDepositNow()">Kiểm tra ngay</button></div>
                    </div>
                    <div id="depositStatusText" class="muted" style="margin-top:10px;">Đang chờ thanh toán...</div>
                </div>
            </div>

            <div class="card">
                <h2>Lịch sử nạp</h2>
                <div class="list" id="myDepositsList"></div>
            </div>
        </div>
    </section>

    <section id="orders" class="section">
        <div class="grid-2">
            <div class="card">
                <h2>Đơn hàng</h2>
                <div class="list" id="ordersList"></div>
            </div>
            <div class="card">
                <h2>Lịch sử mua</h2>
                <div class="list" id="historyList"></div>
            </div>
        </div>
    </section>

    <section id="profile" class="section">
        <div class="grid-2">
            <div class="card">
                <h2>Thông tin tài khoản</h2>
                <div id="profileInfo"></div>
            </div>
            <div class="card">
                <h2>Tóm tắt</h2>
                <div id="profileSummary"></div>
            </div>
        </div>
    </section>

    <section id="login" class="section">
        <div class="card" style="max-width:520px; margin:0 auto;">
            <h2>Đăng nhập</h2>
            <form onsubmit="login(event)">
                <input id="loginUsername" placeholder="Tên đăng nhập">
                <input id="loginPassword" type="password" placeholder="Mật khẩu">
                <button class="btn btn-primary" type="submit">Đăng nhập</button>
            </form>
        </div>
    </section>

    <section id="register" class="section">
        <div class="card" style="max-width:520px; margin:0 auto;">
            <h2>Đăng ký</h2>
            <form onsubmit="register(event)">
                <input id="registerUsername" placeholder="Tên đăng nhập">
                <input id="registerPassword" type="password" placeholder="Mật khẩu">
                <input id="registerConfirm" type="password" placeholder="Nhập lại mật khẩu">
                <button class="btn btn-primary" type="submit">Đăng ký</button>
            </form>
        </div>
    </section>

    <section id="contact" class="section">
        <div class="card">
            <h2>Liên hệ</h2>
            <p>Telegram:
                <a href="{{ telegram_group_link }}" target="_blank" style="color:#2563eb;">{{ telegram_group_link }}</a>
            </p>
            <p>Zalo:
                <a href="https://zalo.me/{{ zalo_contact }}" target="_blank" style="color:#2563eb;">{{ zalo_contact }}</a>
            </p>
        </div>
    </section>

    <section id="admin" class="section">
        <div id="adminContent"></div>
    </section>
</main>

<script>
const TELEGRAM_GROUP_LINK = "{{ telegram_group_link }}";
const ZALO_CONTACT = "{{ zalo_contact }}";

let state = {
    me: null,
    products: [],
    stats: {},
    deposits: [],
    orders: [],
    history: [],
    cart: []
};

let currentDepositId = null;
let depositPoller = null;
let lastPaidDepositId = null;

function money(n){
    return Number(n || 0).toLocaleString('vi-VN') + 'đ';
}

function escapeHtml(str){
    return String(str ?? '')
        .replace(/&/g, '&amp;')
        .replace(/</g, '&lt;')
        .replace(/>/g, '&gt;')
        .replace(/"/g, '&quot;')
        .replace(/'/g, '&#039;');
}

function showNotice(text){
    const box = document.getElementById('notice');
    box.innerText = text;
    box.style.display = 'block';
    clearTimeout(window.noticeTimer);
    window.noticeTimer = setTimeout(() => {
        box.style.display = 'none';
    }, 3000);
}

async function api(url, method='GET', data=null){
    const options = {
        method,
        headers: {'Content-Type':'application/json'}
    };
    if(data) options.body = JSON.stringify(data);
    const res = await fetch(url, options);
    const json = await res.json();
    if(!res.ok) throw new Error(json.message || 'Có lỗi xảy ra');
    return json;
}

function menuItems(){
    const items = [
        ['home', 'Trang chủ'],
        ['shop', 'Mua hàng'],
        ['cart', 'Giỏ hàng'],
        ['wallet', 'Nạp tiền'],
        ['orders', 'Đơn hàng'],
        ['contact', 'Liên hệ']
    ];

    if(!state.me){
        items.push(['login', 'Đăng nhập']);
        items.push(['register', 'Đăng ký']);
    } else {
        items.push(['profile', 'Tài khoản']);
        if(state.me.role === 'admin') items.push(['admin', 'Quản trị']);
        items.push(['logout', 'Đăng xuất']);
    }
    return items;
}

function renderMenu(active='home'){
    const menu = document.getElementById('menu');
    menu.innerHTML = '';

    menuItems().forEach(([id, label]) => {
        const btn = document.createElement('button');
        btn.textContent = label;
        if(id === active) btn.classList.add('active');
        btn.onclick = () => {
            if(id === 'logout') logout();
            else showSection(id);
        };
        menu.appendChild(btn);
    });
}

function toggleMobileMenu(){
    const menu = document.getElementById('menu');
    const overlay = document.getElementById('menuOverlay');
    menu.classList.toggle('show');
    overlay.classList.toggle('show');
}

function closeMobileMenu(){
    document.getElementById('menu').classList.remove('show');
    document.getElementById('menuOverlay').classList.remove('show');
}

function showSection(id){
    document.querySelectorAll('.section').forEach(s => s.classList.remove('active'));
    document.getElementById(id).classList.add('active');
    renderMenu(id);
    closeMobileMenu();
}

function updateUserBox(){
    const user = state.me;
    document.getElementById('userInfoTop').innerText = user ? `Xin chào, ${user.username}` : 'Chưa đăng nhập';
    document.getElementById('userInfoMoney').innerText = 'Số dư: ' + money(user ? user.balance : 0);
}

function renderStats(){
    document.getElementById('statProducts').innerText = state.stats.products || 0;
    document.getElementById('statUsers').innerText = state.stats.users || 0;
    document.getElementById('statOrders').innerText = state.stats.orders || 0;
    document.getElementById('statDeposits').innerText = state.stats.deposits || 0;
}

function renderCategoryFilter(){
    const select = document.getElementById('categoryFilter');
    const oldValue = select.value || 'all';
    const categories = ['all', ...new Set(state.products.map(p => p.category))];

    select.innerHTML = categories.map(c => `
        <option value="${escapeHtml(c)}">
            ${c === 'all' ? 'Tất cả danh mục' : escapeHtml(c)}
        </option>
    `).join('');

    select.value = categories.includes(oldValue) ? oldValue : 'all';
}

function renderProducts(){
    renderCategoryFilter();

    const key = (document.getElementById('searchInput').value || '').toLowerCase();
    const cat = document.getElementById('categoryFilter').value || 'all';
    const list = document.getElementById('productsList');

    const filtered = state.products.filter(p => {
        const searchText = `${p.name} ${p.category} ${p.description || ''}`.toLowerCase();
        const okKey = !key || searchText.includes(key);
        const okCat = cat === 'all' || p.category === cat;
        return okKey && okCat;
    });

    list.innerHTML = filtered.length ? filtered.map(p => `
        <div class="product-card">
            <span class="badge">${escapeHtml(p.badge || 'Mới')}</span>
            <h3>${escapeHtml(p.name)}</h3>
            <p>${escapeHtml(p.description || '')}</p>
            <div class="muted">Danh mục: ${escapeHtml(p.category)}</div>
            <div class="muted">Thời hạn: ${escapeHtml(p.duration)}</div>
            <div class="price">${money(p.price)}</div>
            <button class="btn btn-primary" onclick="addToCart(${p.id})">Thêm giỏ hàng</button>
        </div>
    `).join('') : '<div class="empty">Không có sản phẩm.</div>';
}

function addToCart(id){
    const p = state.products.find(x => x.id === id);
    if(!p) return;
    const found = state.cart.find(x => x.id === id);
    if(found) found.qty += 1;
    else state.cart.push({...p, qty:1});
    renderCart();
    showNotice('Đã thêm vào giỏ hàng');
}

function changeQty(id, delta){
    const item = state.cart.find(x => x.id === id);
    if(!item) return;
    item.qty += delta;
    if(item.qty <= 0){
        state.cart = state.cart.filter(x => x.id !== id);
    }
    renderCart();
}

function removeCart(id){
    state.cart = state.cart.filter(x => x.id !== id);
    renderCart();
}

function renderCart(){
    const total = state.cart.reduce((s, x) => s + x.price * x.qty, 0);
    document.getElementById('cartTotal').innerText = money(total);

    const html = state.cart.length ? state.cart.map(item => `
        <div class="item">
            <b>${escapeHtml(item.name)}</b>
            <div class="muted">${money(item.price)} / gói</div>
            <div class="row" style="margin-top:10px;">
                <div><button class="btn btn-dark" onclick="changeQty(${item.id}, -1)">-</button></div>
                <div style="padding-top:10px;">${item.qty}</div>
                <div><button class="btn btn-dark" onclick="changeQty(${item.id}, 1)">+</button></div>
                <div><button class="btn btn-danger" onclick="removeCart(${item.id})">Xóa</button></div>
            </div>
        </div>
    `).join('') : '<div class="empty">Giỏ hàng trống.</div>';

    document.getElementById('cartQuickList').innerHTML = html;
    document.getElementById('cartPageList').innerHTML = html + `
        <div class="highlight" style="margin-top:12px;">
            <div class="muted">Tổng cộng</div>
            <div class="price">${money(total)}</div>
            <div class="row">
                <div><button class="btn btn-dark" style="width:100%" onclick="showSection('shop')">Mua thêm</button></div>
                <div><button class="btn btn-green" style="width:100%" onclick="checkout()">Thanh toán</button></div>
            </div>
        </div>
    `;
}

async function register(event){
    event.preventDefault();
    const username = document.getElementById('registerUsername').value.trim();
    const password = document.getElementById('registerPassword').value.trim();
    const confirm = document.getElementById('registerConfirm').value.trim();

    if(!username || !password || !confirm){
        return showNotice('Nhập đầy đủ thông tin');
    }
    if(password !== confirm){
        return showNotice('Mật khẩu nhập lại chưa khớp');
    }

    try{
        await api('/api/register', 'POST', {username, password});
        await api('/api/login', 'POST', {username, password});
        document.querySelector('#register form').reset();
        await loadAll();
        showNotice('Đăng ký thành công');
        showSection('shop');
    }catch(err){
        showNotice(err.message);
    }
}

async function login(event){
    event.preventDefault();
    const username = document.getElementById('loginUsername').value.trim();
    const password = document.getElementById('loginPassword').value.trim();

    try{
        await api('/api/login', 'POST', {username, password});
        document.querySelector('#login form').reset();
        await loadAll();
        showNotice('Đăng nhập thành công');
        showSection(state.me && state.me.role === 'admin' ? 'admin' : 'shop');
    }catch(err){
        showNotice(err.message);
    }
}

async function logout(){
    try{
        await api('/api/logout', 'POST');
    } catch (_) {}

    state.me = null;
    state.deposits = [];
    state.orders = [];
    state.history = [];
    state.cart = [];
    currentDepositId = null;
    lastPaidDepositId = null;

    if(depositPoller) clearInterval(depositPoller);
    depositPoller = null;

    await loadPublic();
    updateUserBox();
    renderMenu('home');
    renderStats();
    renderCart();
    renderDeposits();
    renderOrders();
    renderHistory();
    renderProfile();
    renderAdmin();
    showNotice('Đã đăng xuất');
    showSection('home');
}

async function createDeposit(event){
    event.preventDefault();

    if(!state.me) return showNotice('Bạn cần đăng nhập');

    const amount = Number(document.getElementById('depositAmount').value || 0);
    const note = document.getElementById('depositNote').value.trim() || ('NAPTIEN ' + state.me.username);

    if(amount < 10000) return showNotice('Tối thiểu 10.000đ');

    try{
        const res = await api('/api/deposits/create', 'POST', {amount, note});
        document.querySelector('#wallet form').reset();
        document.getElementById('depositAmount').value = 50000;

        currentDepositId = res.depositId;
        lastPaidDepositId = null;

        if(res.qrCode){
            let qrUrl = res.qrCode;

            if(
                !String(qrUrl).startsWith('http://') &&
                !String(qrUrl).startsWith('https://') &&
                !String(qrUrl).startsWith('data:image/')
            ){
                qrUrl = 'https://api.qrserver.com/v1/create-qr-code/?size=260x260&data=' + encodeURIComponent(res.qrCode);
            }

            document.getElementById('qrImage').src = qrUrl;
            document.getElementById('checkoutLink').href = res.checkoutUrl || '#';
            document.getElementById('qrArea').style.display = 'block';
            document.getElementById('depositStatusText').innerText = 'Đã tạo QR. Quét mã để thanh toán.';
        }

        await loadAll();
        startDepositPolling();
        showNotice('Đã tạo lệnh nạp');
    }catch(err){
        showNotice(err.message);
    }
}

function startDepositPolling(){
    if(!currentDepositId) return;
    if(depositPoller) clearInterval(depositPoller);

    depositPoller = setInterval(async () => {
        await checkDepositNow(false);
    }, 3000);
}

async function checkDepositNow(showMsg = true){
    if(!currentDepositId) return;

    try{
        const res = await api('/api/deposits/' + currentDepositId + '/status', 'GET');

        document.getElementById('depositStatusText').innerText =
            'Trạng thái nạp: ' + (res.status || 'pending') + ' | payOS: ' + (res.payosStatus || 'PENDING');

        if(res.qrCode){
            let qrUrl = res.qrCode;
            if(
                !String(qrUrl).startsWith('http://') &&
                !String(qrUrl).startsWith('https://') &&
                !String(qrUrl).startsWith('data:image/')
            ){
                qrUrl = 'https://api.qrserver.com/v1/create-qr-code/?size=260x260&data=' + encodeURIComponent(res.qrCode);
            }
            document.getElementById('qrImage').src = qrUrl;
            document.getElementById('qrArea').style.display = 'block';
        }

        if(res.checkoutUrl){
            document.getElementById('checkoutLink').href = res.checkoutUrl;
        }

        if(res.status === 'paid'){
            if(depositPoller) clearInterval(depositPoller);
            depositPoller = null;

            await loadAll();

            if(lastPaidDepositId !== currentDepositId){
                lastPaidDepositId = currentDepositId;
                showNotice('Đã cộng tiền vào tài khoản');
            }

            document.getElementById('depositStatusText').innerText = 'Thanh toán thành công. Tiền đã cộng vào tài khoản.'; 
        } else if(showMsg){
            showNotice('Đơn vẫn đang chờ thanh toán');
        }
    }catch(err){
        if(showMsg) showNotice(err.message);
    }
}

function renderDeposits(){
    const list = document.getElementById('myDepositsList');
    if(!state.me){
        list.innerHTML = '<div class="empty">Vui lòng đăng nhập</div>';
        return;
    }

    list.innerHTML = state.deposits.length ? state.deposits.map(d => `
        <div class="item">
            <b>${money(d.amount)}</b>
            <div class="muted">Mã nạp: ${escapeHtml(d.code)}</div>
            <div class="muted">${escapeHtml(d.created_at || '')}</div>
            <div class="muted">${escapeHtml(d.note || '')}</div>
            <div class="status ${d.status === 'paid' ? 'success' : d.status === 'failed' ? 'danger' : 'warning'}">${escapeHtml(d.status)}</div>
        </div>
    `).join('') : '<div class="empty">Chưa có lịch sử nạp</div>';
}

function resumePendingDepositFromHistory(){
    if(!state.me || !Array.isArray(state.deposits)) return;

    const pending = state.deposits.find(d => d.status === 'pending' && d.id);
    if(!pending) return;

    currentDepositId = pending.id;

    if(pending.qr_code || pending.qrCode){
        let qrUrl = pending.qr_code || pending.qrCode;

        if(
            !String(qrUrl).startsWith('http://') &&
            !String(qrUrl).startsWith('https://') &&
            !String(qrUrl).startsWith('data:image/')
        ){
            qrUrl = 'https://api.qrserver.com/v1/create-qr-code/?size=260x260&data=' + encodeURIComponent(qrUrl);
        }

        document.getElementById('qrImage').src = qrUrl;
        document.getElementById('qrArea').style.display = 'block';
    }

    if(pending.checkout_url || pending.checkoutUrl){
        document.getElementById('checkoutLink').href = pending.checkout_url || pending.checkoutUrl;
    }

    document.getElementById('depositStatusText').innerText =
        'Trạng thái nạp: ' + (pending.status || 'pending') + ' | payOS: ' + (pending.payos_status || pending.payosStatus || 'PENDING');

    startDepositPolling();
}

async function checkout(){
    if(!state.me) return showNotice('Bạn cần đăng nhập');
    if(!state.cart.length) return showNotice('Giỏ hàng trống');

    try{
        await api('/api/checkout', 'POST', {
            items: state.cart.map(item => ({
                product_id: item.id,
                qty: item.qty
            }))
        });

        state.cart = [];
        await loadAll();
        renderCart();
        showNotice('Thanh toán thành công');
        showSection('orders');
        setTimeout(() => {
            window.open(TELEGRAM_GROUP_LINK, '_blank');
        }, 500);
    }catch(err){
        showNotice(err.message);
    }
}

function renderOrders(){
    const list = document.getElementById('ordersList');
    if(!state.me){
        list.innerHTML = '<div class="empty">Vui lòng đăng nhập</div>';
        return;
    }

    list.innerHTML = state.orders.length ? state.orders.map(o => `
        <div class="item">
            <b>${escapeHtml(o.product_name)}</b>
            <div class="muted">Mã đơn: ${escapeHtml(o.code)} · ${escapeHtml(o.created_at)}</div>
            <div class="muted">Số lượng: ${o.qty} · Tổng: ${money(o.total_price)}</div>
            <div class="status ${o.status === 'ready' ? 'success' : 'warning'}">${escapeHtml(o.status)}</div>
            <div class="muted" style="margin-top:8px;">${escapeHtml(o.note || '')}</div>
            <div style="margin-top:10px;">
                <a href="${TELEGRAM_GROUP_LINK}" target="_blank" class="btn btn-primary">Telegram</a>
                <a href="https://zalo.me/${ZALO_CONTACT}" target="_blank" class="btn btn-green" style="margin-left:8px;">Zalo</a>
            </div>
            ${o.manual_key ? `<span class="key">${escapeHtml(o.manual_key)}</span>` : ''}
        </div>
    `).join('') : '<div class="empty">Chưa có đơn hàng</div>';
}

function renderHistory(){
    const list = document.getElementById('historyList');
    if(!state.me){
        list.innerHTML = '<div class="empty">Vui lòng đăng nhập</div>';
        return;
    }

    list.innerHTML = state.history.length ? state.history.map(h => `
        <div class="item">
            <b>${escapeHtml(h.product_name)}</b>
            <div class="muted">${escapeHtml(h.created_at)}</div>
            <div class="muted">Số lượng: ${h.qty} · Tổng: ${money(h.total_price)}</div>
            <div class="status success">Hoàn tất</div>
        </div>
    `).join('') : '<div class="empty">Chưa có lịch sử mua</div>';
}

function renderProfile(){
    const info = document.getElementById('profileInfo');
    const summary = document.getElementById('profileSummary');

    if(!state.me){
        info.innerHTML = '<div class="empty">Vui lòng đăng nhập</div>';
        summary.innerHTML = '<div class="empty">Không có dữ liệu</div>';
        return;
    }

    info.innerHTML = `
        <p><b>Tên đăng nhập:</b> ${escapeHtml(state.me.username)}</p>
        <p><b>Vai trò:</b> ${escapeHtml(state.me.role)}</p>
        <p><b>Số dư:</b> ${money(state.me.balance || 0)}</p>
        <p><b>Ngày tạo:</b> ${escapeHtml(state.me.created_at || '')}</p>
    `;

    summary.innerHTML = `
        <p><b>Số đơn hàng:</b> ${state.orders.length}</p>
        <p><b>Lịch sử mua:</b> ${state.history.length}</p>
        <p><b>Yêu cầu nạp:</b> ${state.deposits.length}</p>
    `;
}

async function addProduct(event){
    event.preventDefault();

    const payload = {
        name: document.getElementById('adminName').value.trim(),
        category: document.getElementById('adminCategory').value.trim(),
        duration: document.getElementById('adminDuration').value.trim(),
        price: Number(document.getElementById('adminPrice').value || 0),
        badge: document.getElementById('adminBadge').value.trim() || 'Mới',
        description: document.getElementById('adminDescription').value.trim()
    };

    try{
        await api('/api/admin/products', 'POST', payload);
        event.target.reset();
        await loadAll();
        showNotice('Đã thêm sản phẩm');
    }catch(err){
        showNotice(err.message);
    }
}

async function deleteProduct(id){
    if(!confirm('Xóa sản phẩm này?')) return;

    try{
        await api('/api/admin/products/' + id, 'DELETE');
        await loadAll();
        showNotice('Đã xóa sản phẩm');
    }catch(err){
        showNotice(err.message);
    }
}

async function approveDeposit(id){
    try{
        await api('/api/admin/deposits/' + id + '/approve', 'POST');
        await loadAll();
        showNotice('Đã xác nhận nạp tiền');
    }catch(err){
        showNotice(err.message);
    }
}

async function saveManualKey(id){
    const key = document.getElementById('manualKey_' + id).value.trim();

    try{
        await api('/api/admin/orders/' + id + '/key', 'POST', {manual_key: key});
        await loadAll();
        showNotice('Đã lưu key');
    }catch(err){
        showNotice(err.message);
    }
}

async function confirmWebhookNow(){
    try{
        const res = await api('/api/admin/payos/confirm-webhook', 'POST');
        showNotice(res.message || 'Đã confirm webhook');
    }catch(err){
        showNotice(err.message);
    }
}

function renderAdmin(){
    const box = document.getElementById('adminContent');

    if(!state.me || state.me.role !== 'admin'){
        box.innerHTML = '<div class="card"><div class="empty">Bạn cần đăng nhập admin</div></div>';
        return;
    }

    const adminDeposits = window.adminDeposits || [];
    const adminOrders = window.adminOrders || [];
    const adminStats = window.adminStats || {};

    box.innerHTML = `
        <div class="card" style="margin-bottom:16px;">
            <h2>Thiết lập payOS</h2>
            <p class="muted">Sau khi đổi PUBLIC_BASE_URL thành link public, bấm nút dưới để confirm webhook.</p>
            <button class="btn btn-primary" onclick="confirmWebhookNow()">Confirm webhook payOS</button>
        </div>

        <div class="grid-2">
            <div class="card">
                <h2>Thêm sản phẩm</h2>
                <form onsubmit="addProduct(event)">
                    <input id="adminName" placeholder="Tên sản phẩm">
                    <input id="adminCategory" placeholder="Danh mục">
                    <input id="adminDuration" placeholder="Thời hạn">
                    <input id="adminPrice" type="number" placeholder="Giá">
                    <input id="adminBadge" value="Mới" placeholder="Nhãn">
                    <textarea id="adminDescription" rows="4" placeholder="Mô tả"></textarea>
                    <button class="btn btn-primary" type="submit">Thêm sản phẩm</button>
                </form>
            </div>

            <div class="card">
                <h2>Thống kê</h2>
                <p><b>Người dùng:</b> ${adminStats.users || 0}</p>
                <p><b>Đơn hàng:</b> ${adminStats.orders || 0}</p>
                <p><b>Doanh thu:</b> ${money(adminStats.revenue || 0)}</p>
            </div>
        </div>

        <div class="card" style="margin-top:16px;">
            <h2>Lịch sử nạp</h2>
            <div class="list">
                ${adminDeposits.length ? adminDeposits.map(d => `
                    <div class="item">
                        <b>${escapeHtml(d.username)}</b>
                        <div class="muted">${money(d.amount)} · ${escapeHtml(d.created_at)}</div>
                        <div class="muted">${escapeHtml(d.note || '')}</div>
                        <div class="status ${d.status === 'paid' ? 'success' : d.status === 'failed' ? 'danger' : 'warning'}">${escapeHtml(d.status)}</div>
                        ${d.status === 'pending' ? `<button class="btn btn-green" style="margin-top:10px;" onclick="approveDeposit(${d.id})">Xác nhận nạp</button>` : ''}
                    </div>
                `).join('') : '<div class="empty">Chưa có yêu cầu nạp</div>'}
            </div>
        </div>

        <div class="card" style="margin-top:16px;">
            <h2>Nhập key đơn hàng</h2>
            <div class="list">
                ${adminOrders.length ? adminOrders.map(o => `
                    <div class="item">
                        <b>${escapeHtml(o.product_name)}</b>
                        <div class="muted">Đơn: ${escapeHtml(o.code)} · User: ${escapeHtml(o.username)} · ${escapeHtml(o.created_at)}</div>
                        <div class="muted">Số lượng: ${o.qty} · Tổng: ${money(o.total_price)}</div>
                        <textarea id="manualKey_${o.id}" rows="3" placeholder="Nhập key...">${escapeHtml(o.manual_key || '')}</textarea>
                        <button class="btn btn-green" onclick="saveManualKey(${o.id})">Lưu key</button>
                    </div>
                `).join('') : '<div class="empty">Chưa có đơn hàng</div>'}
            </div>
        </div>

        <div class="card" style="margin-top:16px;">
            <h2>Danh sách sản phẩm</h2>
            <div class="list">
                ${state.products.map(p => `
                    <div class="item">
                        <b>${escapeHtml(p.name)}</b>
                        <div class="muted">${escapeHtml(p.category)} · ${escapeHtml(p.duration)} · ${money(p.price)}</div>
                        <div class="muted">${escapeHtml(p.description || '')}</div>
                        <button class="btn btn-danger" style="margin-top:10px;" onclick="deleteProduct(${p.id})">Xóa</button>
                    </div>
                `).join('')}
            </div>
        </div>
    `;
}

async function loadPublic(){
    const res = await api('/api/public');
    state.products = res.products || [];
    state.stats = res.stats || {};
    renderStats();
    renderProducts();
}

async function loadAll(){
    await loadPublic();

    try{
        const meRes = await api('/api/me');
        state.me = meRes.user;
    }catch{
        state.me = null;
    }

    if(state.me){
        const dash = await api('/api/dashboard');
        state.deposits = dash.deposits || [];
        state.orders = dash.orders || [];
        state.history = dash.history || [];
        state.me.balance = dash.balance || 0;

        if(state.me.role === 'admin'){
            const admin = await api('/api/admin/dashboard');
            window.adminDeposits = admin.deposits || [];
            window.adminOrders = admin.orders || [];
            window.adminStats = admin.stats || {};
        } else {
            window.adminDeposits = [];
            window.adminOrders = [];
            window.adminStats = {};
        }
    } else {
        state.deposits = [];
        state.orders = [];
        state.history = [];
        window.adminDeposits = [];
        window.adminOrders = [];
        window.adminStats = {};
    }

    updateUserBox();
    renderMenu(document.querySelector('.section.active')?.id || 'home');
    renderStats();
    renderProducts();
    renderCart();
    renderDeposits();
    renderOrders();
    renderHistory();
    renderProfile();
    renderAdmin();
    resumePendingDepositFromHistory();
}

loadAll();
</script>
</body>
</html>
"""

def get_conn():
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    return conn

def now_vn():
    return datetime.now().strftime("%d/%m/%Y %H:%M:%S")

def to_int(value, default=0):
    try:
        return int(value)
    except (TypeError, ValueError):
        return default

def obj_to_dict(obj):
    if obj is None:
        return {}
    if isinstance(obj, dict):
        return obj
    if hasattr(obj, "model_dump"):
        try:
            return obj.model_dump()
        except Exception:
            pass
    if hasattr(obj, "dict"):
        try:
            return obj.dict()
        except Exception:
            pass
    if hasattr(obj, "__dict__"):
        try:
            return dict(obj.__dict__)
        except Exception:
            pass
    return {}

def get_value(obj, *keys, default=None):
    if obj is None:
        return default

    if isinstance(obj, dict):
        for key in keys:
            if key in obj and obj[key] is not None:
                return obj[key]
        return default

    for key in keys:
        if hasattr(obj, key):
            value = getattr(obj, key)
            if value is not None:
                return value

    dumped = obj_to_dict(obj)
    if dumped:
        for key in keys:
            if key in dumped and dumped[key] is not None:
                return dumped[key]

    return default

def make_code(prefix, number):
    return f"{prefix}{number:06d}"

def generate_order_code():
    # Trả về string để tránh overflow/kiểu
    base = int(time.time() * 1000)
    rand = uuid.uuid4().int % 1000
    return f"{base}{rand:03d}"

def is_public_url(url: str) -> bool:
    if not url:
        return False
    u = url.lower().strip()
    # Kiểm tra localhost/ngrok http => không hợp lệ
    if "127.0.0.1" in u or "localhost" in u or u.startswith("http://0.0.0.0"):
        return False
    # Yêu cầu https để webhook an toàn
    return u.startswith("https://")

def confirm_payos_webhook():
    if not is_public_url(WEBHOOK_URL):
        print(f"[payOS] Bo qua confirm webhook vi URL chua public hoac khong la HTTPS: {WEBHOOK_URL}")
        return

    try:
        try:
            result = payos.confirm_webhook(WEBHOOK_URL)
        except Exception:
            result = payos.webhooks.confirm(WEBHOOK_URL)
        print(f"[payOS] Confirm webhook OK: {result}")
    except Exception as e:
        print(f"[payOS] Confirm webhook that bai: {e}")

def sync_paid_deposit_by_order_code(order_code, payos_amount=None, payos_status=None, payment_link_id=None):
    conn = get_conn()
    cur = conn.cursor()

    cur.execute("""
        SELECT
            p.deposit_id,
            p.order_code,
            p.payment_link_id,
            p.status AS link_status,
            d.user_id,
            d.amount,
            d.status AS deposit_status
        FROM payos_links p
        JOIN deposits d ON d.id = p.deposit_id
        WHERE p.order_code = ?
        LIMIT 1
    """, (str(order_code),))
    row = cur.fetchone()

    if not row:
        conn.close()
        return {"ok": False, "message": "Khong tim thay order_code"}

    current_link_status = (payos_status or row["link_status"] or "").upper()
    deposit_status = (row["deposit_status"] or "").lower()

    if payment_link_id:
        cur.execute(
            "UPDATE payos_links SET payment_link_id = COALESCE(payment_link_id, ?) WHERE order_code = ?",
            (payment_link_id, str(order_code))
        )

    if current_link_status:
        cur.execute(
            "UPDATE payos_links SET status = ? WHERE order_code = ?",
            (current_link_status, str(order_code))
        )

    if deposit_status == "paid":
        conn.commit()
        conn.close()
        return {"ok": True, "message": "Da xu ly truoc do", "already_paid": True}

    if payos_amount is not None and to_int(payos_amount) != to_int(row["amount"]):
        conn.commit()
        conn.close()
        return {"ok": False, "message": "So tien khong khop"}

    if current_link_status == "PAID":
        cur.execute("UPDATE deposits SET status = 'paid' WHERE id = ? AND status != 'paid'", (row["deposit_id"],))
        if cur.rowcount > 0:
            cur.execute("UPDATE users SET balance = balance + ? WHERE id = ?", (to_int(row["amount"]), row["user_id"]))
            conn.commit()
            conn.close()
            return {"ok": True, "message": "Da cong tien", "paid": True}

        conn.commit()
        conn.close()
        return {"ok": True, "message": "Da xu ly truoc do", "already_paid": True}

    if current_link_status in ("CANCELLED", "EXPIRED", "FAILED"):
        cur.execute("UPDATE deposits SET status = 'failed' WHERE id = ? AND status != 'paid'", (row["deposit_id"],))
        conn.commit()
        conn.close()
        return {"ok": True, "message": "That bai", "failed": True}

    conn.commit()
    conn.close()
    return {"ok": True, "message": "Dang cho thanh toan", "pending": True}

def query_payos_payment_status(order_code):
    try:
        try:
            result = payos.get_payment_link_information(str(order_code))
        except Exception:
            result = payos.payment_requests.get(str(order_code))

        data = obj_to_dict(result)

        if "data" in data and isinstance(data["data"], dict):
            data = data["data"]

        status = get_value(data, "status", default="PENDING")
        payment_link_id = get_value(data, "id", "paymentLinkId", "payment_link_id")
        amount = get_value(data, "amount")

        return {
            "ok": True,
            "status": (status or "PENDING").upper(),
            "payment_link_id": payment_link_id,
            "amount": amount,
            "raw": data
        }
    except Exception as e:
        return {"ok": False, "message": str(e)}

def init_db():
    conn = get_conn()
    cur = conn.cursor()

    cur.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            role TEXT NOT NULL DEFAULT 'user',
            balance INTEGER NOT NULL DEFAULT 0,
            created_at TEXT NOT NULL
        )
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS products (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            category TEXT NOT NULL,
            duration TEXT NOT NULL,
            price INTEGER NOT NULL,
            badge TEXT NOT NULL,
            description TEXT
        )
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS deposits (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            code TEXT UNIQUE NOT NULL,
            user_id INTEGER NOT NULL,
            username TEXT NOT NULL,
            amount INTEGER NOT NULL,
            note TEXT,
            status TEXT NOT NULL DEFAULT 'pending',
            created_at TEXT NOT NULL
        )
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS orders (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            code TEXT UNIQUE NOT NULL,
            user_id INTEGER NOT NULL,
            username TEXT NOT NULL,
            product_name TEXT NOT NULL,
            qty INTEGER NOT NULL,
            total_price INTEGER NOT NULL,
            status TEXT NOT NULL DEFAULT 'pending_key',
            manual_key TEXT,
            note TEXT,
            created_at TEXT NOT NULL
        )
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS purchase_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            product_name TEXT NOT NULL,
            qty INTEGER NOT NULL,
            total_price INTEGER NOT NULL,
            created_at TEXT NOT NULL
        )
    """)

    # payos_links.order_code -> TEXT (not integer)
    cur.execute("""
        CREATE TABLE IF NOT EXISTS payos_links (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            deposit_id INTEGER NOT NULL,
            order_code TEXT NOT NULL UNIQUE,
            payment_link_id TEXT,
            checkout_url TEXT,
            qr_code TEXT,
            status TEXT NOT NULL DEFAULT 'PENDING',
            created_at TEXT NOT NULL
        )
    """)

    cur.execute("SELECT id FROM users WHERE username = ?", ("vukhanh",))
    admin_user = cur.fetchone()

    if not admin_user:
        cur.execute(
            "INSERT INTO users (username, password_hash, role, balance, created_at) VALUES (?, ?, ?, ?, ?)",
            ("vukhanh", generate_password_hash("khanh3082006"), "admin", 0, now_vn())
        )
    else:
        cur.execute(
            "UPDATE users SET password_hash = ?, role = 'admin' WHERE username = ?",
            (generate_password_hash("khanh3082006"), "vukhanh")
        )

    cur.execute("DELETE FROM users WHERE username = ?", ("admin",))

    cur.execute("SELECT COUNT(*) AS c FROM products")
    count = cur.fetchone()["c"]

    if count == 0:
        products = [
            ("Gói Premium 31 ngày", "Premium", "31 ngày", 450000, "Premium", "Gói cao cấp cho người dùng dài hạn."),
            ("Gói Premium 7 ngày", "Premium", "7 ngày", 260000, "Hot", "Gói ngắn hạn để trải nghiệm."),
            ("Gói Premium 1 ngày", "Premium", "1 ngày", 100000, "Trial", "Gói sử dụng nhanh trong ngày."),
            ("Gói Desktop 15 ngày", "Desktop", "15 ngày", 100000, "Pro", "Gói dùng trên máy tính 15 ngày."),
            ("Gói Desktop 30 ngày", "Desktop", "30 ngày", 180000, "PC", "Gói dùng máy tính 30 ngày."),
            ("Gói Android 30 ngày", "Android", "30 ngày", 200000, "Android", "Gói dành cho Android theo tháng.")
        ]
        cur.executemany(
            "INSERT INTO products (name, category, duration, price, badge, description) VALUES (?, ?, ?, ?, ?, ?)",
            products
        )

    conn.commit()
    conn.close()

def current_user():
    user_id = session.get("user_id")
    if not user_id:
        return None

    conn = get_conn()
    cur = conn.cursor()
    cur.execute("SELECT id, username, role, balance, created_at FROM users WHERE id = ?", (user_id,))
    user = cur.fetchone()
    conn.close()
    return user

def require_login():
    user = current_user()
    if not user:
        return None, (jsonify({"message": "Bạn cần đăng nhập"}), 401)
    return user, None

def require_admin():
    user = current_user()
    if not user:
        return None, (jsonify({"message": "Bạn cần đăng nhập"}), 401)
    if user["role"] != "admin":
        return None, (jsonify({"message": "Chỉ admin mới dùng được"}), 403)
    return user, None

@app.route("/")
def index():
    return render_template_string(
        HTML_PAGE,
        telegram_group_link=TELEGRAM_GROUP_LINK,
        zalo_contact=ZALO_CONTACT,
    )

@app.route("/api/public")
def api_public():
    conn = get_conn()
    cur = conn.cursor()

    cur.execute("SELECT * FROM products ORDER BY id DESC")
    products = [dict(row) for row in cur.fetchall()]

    cur.execute("SELECT COUNT(*) AS c FROM users")
    users_count = cur.fetchone()["c"]

    cur.execute("SELECT COUNT(*) AS c FROM orders")
    orders_count = cur.fetchone()["c"]

    cur.execute("SELECT COUNT(*) AS c FROM deposits")
    deposits_count = cur.fetchone()["c"]

    conn.close()

    return jsonify({
        "products": products,
        "stats": {
            "products": len(products),
            "users": users_count,
            "orders": orders_count,
            "deposits": deposits_count
        }
    })

@app.route("/api/register", methods=["POST"])
def api_register():
    data = request.get_json() or {}
    username = (data.get("username") or "").strip()
    password = (data.get("password") or "").strip()

    if len(username) < 3:
        return jsonify({"message": "Tên đăng nhập phải từ 3 ký tự"}), 400
    if len(password) < 4:
        return jsonify({"message": "Mật khẩu phải từ 4 ký tự"}), 400

    conn = get_conn()
    cur = conn.cursor()

    cur.execute("SELECT id FROM users WHERE username = ?", (username,))
    if cur.fetchone():
        conn.close()
        return jsonify({"message": "Tên đăng nhập đã tồn tại"}), 400

    cur.execute(
        "INSERT INTO users (username, password_hash, role, balance, created_at) VALUES (?, ?, ?, ?, ?)",
        (username, generate_password_hash(password), "user", 0, now_vn())
    )

    conn.commit()
    conn.close()
    return jsonify({"message": "Đăng ký thành công"})

@app.route("/api/login", methods=["POST"])
def api_login():
    data = request.get_json() or {}
    username = (data.get("username") or "").strip()
    password = (data.get("password") or "").strip()

    conn = get_conn()
    cur = conn.cursor()
    cur.execute("SELECT * FROM users WHERE username = ?", (username,))
    user = cur.fetchone()
    conn.close()

    if not user or not check_password_hash(user["password_hash"], password):
        return jsonify({"message": "Sai tài khoản hoặc mật khẩu"}), 401

    session["user_id"] = user["id"]
    return jsonify({"message": "Đăng nhập thành công"})

@app.route("/api/logout", methods=["POST"])
def api_logout():
    session.clear()
    return jsonify({"message": "Đăng xuất thành công"})

@app.route("/api/me")
def api_me():
    user = current_user()
    if not user:
        return jsonify({"message": "Chưa đăng nhập"}), 401
    return jsonify({"user": dict(user)})

@app.route("/api/dashboard")
def api_dashboard():
    user, error = require_login()
    if error:
        return error

    conn = get_conn()
    cur = conn.cursor()

    cur.execute(
        """
        SELECT d.id, d.code, d.amount, d.note, d.status, d.created_at,
               p.order_code, p.checkout_url, p.qr_code, p.payment_link_id,
               p.status AS payos_status
        FROM deposits d
        LEFT JOIN payos_links p ON p.deposit_id = d.id
        WHERE d.user_id = ?
        ORDER BY d.id DESC
        """,
        (user["id"],)
    )
    deposits = [dict(row) for row in cur.fetchall()]

    cur.execute("""
        SELECT id, code, product_name, qty, total_price, status, manual_key, note, created_at
        FROM orders
        WHERE user_id = ?
        ORDER BY id DESC
    """, (user["id"],))
    orders = [dict(row) for row in cur.fetchall()]

    cur.execute("""
        SELECT product_name, qty, total_price, created_at
        FROM purchase_history
        WHERE user_id = ?
        ORDER BY id DESC
    """, (user["id"],))
    history = [dict(row) for row in cur.fetchall()]

    cur.execute("SELECT balance FROM users WHERE id = ?", (user["id"],))
    balance = cur.fetchone()["balance"]

    conn.close()

    return jsonify({
        "deposits": deposits,
        "orders": orders,
        "history": history,
        "balance": balance
    })

@app.route("/api/deposits/create", methods=["POST"])
def api_create_deposit():
    user, error = require_login()
    if error:
        return error

    data = request.get_json() or {}
    amount = to_int(data.get("amount"))
    note = (data.get("note") or "").strip()

    if amount < 10000:
        return jsonify({"message": "Số tiền nạp tối thiểu là 10.000đ"}), 400

    if not is_public_url(PUBLIC_BASE_URL):
        return jsonify({"message": "Bạn chưa đổi PUBLIC_BASE_URL sang link public HTTPS (vd: https://xxxxx.ngrok.io/)"}), 400

    conn = get_conn()
    cur = conn.cursor()

    next_id = cur.execute("SELECT COALESCE(MAX(id), 0) + 1 AS next_id FROM deposits").fetchone()["next_id"]
    code = make_code("NAP", next_id)
    order_code = str(generate_order_code())

    cur.execute("""
        INSERT INTO deposits (code, user_id, username, amount, note, status, created_at)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (
        code,
        user["id"],
        user["username"],
        amount,
        note if note else code,
        "pending",
        now_vn()
    ))
    deposit_id = cur.lastrowid

    try:
        payment_request = CreatePaymentLinkRequest(
            order_code=order_code,
            amount=amount,
            description=code[:25],
            cancel_url=PUBLIC_BASE_URL,
            return_url=PUBLIC_BASE_URL
        )

        try:
            payment_link = payos.createPaymentLink(payment_request)
        except Exception:
            payment_link = payos.payment_requests.create(payment_request)

    except Exception as e:
        cur.execute("DELETE FROM deposits WHERE id = ?", (deposit_id,))
        conn.commit()
        conn.close()
        return jsonify({"message": f"Tạo link payOS thất bại: {e}"}), 500

    payment_link_id = get_value(payment_link, "payment_link_id", "paymentLinkId", "id")
    checkout_url = get_value(payment_link, "checkout_url", "checkoutUrl")
    qr_code = get_value(payment_link, "qr_code", "qrCode")
    link_status = (get_value(payment_link, "status", default="PENDING") or "PENDING").upper()

    cur.execute("""
        INSERT INTO payos_links (deposit_id, order_code, payment_link_id, checkout_url, qr_code, status, created_at)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (
        deposit_id,
        str(order_code),
        payment_link_id,
        checkout_url,
        qr_code,
        link_status,
        now_vn()
    ))

    conn.commit()
    conn.close()

    return jsonify({
        "message": "Tạo lệnh nạp thành công",
        "code": code,
        "depositId": deposit_id,
        "amount": amount,
        "orderCode": order_code,
        "checkoutUrl": checkout_url,
        "qrCode": qr_code,
        "status": link_status
    })

@app.route("/api/deposits/<int:deposit_id>/status", methods=["GET"])
def api_deposit_status(deposit_id):
    user, error = require_login()
    if error:
        return error

    conn = get_conn()
    cur = conn.cursor()

    cur.execute("""
        SELECT
            d.id, d.code, d.amount, d.status,
            p.order_code, p.checkout_url, p.qr_code, p.payment_link_id,
            p.status AS payos_status
        FROM deposits d
        LEFT JOIN payos_links p ON p.deposit_id = d.id
        WHERE d.id = ? AND d.user_id = ?
    """, (deposit_id, user["id"]))
    row = cur.fetchone()

    if not row:
        conn.close()
        return jsonify({"message": "Không tìm thấy lệnh nạp"}), 404

    result = dict(row)
    conn.close()

    payos_check = None

    if result["status"] != "paid" and result.get("order_code"):
        payos_check = query_payos_payment_status(result["order_code"])

        if payos_check["ok"]:
            sync_paid_deposit_by_order_code(
                order_code=result["order_code"],
                payos_amount=payos_check.get("amount"),
                payos_status=payos_check.get("status"),
                payment_link_id=payos_check.get("payment_link_id")
            )

            conn = get_conn()
            cur = conn.cursor()
            cur.execute("""
                SELECT
                    d.id, d.code, d.amount, d.status,
                    p.order_code, p.checkout_url, p.qr_code, p.payment_link_id,
                    p.status AS payos_status
                FROM deposits d
                LEFT JOIN payos_links p ON p.deposit_id = d.id
                WHERE d.id = ? AND d.user_id = ?
            """, (deposit_id, user["id"]))
            row = cur.fetchone()
            result = dict(row)

            cur.execute("SELECT balance FROM users WHERE id = ?", (user["id"],))
            balance = cur.fetchone()["balance"]
            conn.close()

            return jsonify({
                "depositId": result["id"],
                "code": result["code"],
                "amount": result["amount"],
                "status": result["status"],
                "payosStatus": result.get("payos_status"),
                "checkoutUrl": result.get("checkout_url"),
                "qrCode": result.get("qr_code"),
                "balance": balance
            })

    conn = get_conn()
    cur = conn.cursor()
    cur.execute("SELECT balance FROM users WHERE id = ?", (user["id"],))
    balance = cur.fetchone()["balance"]
    conn.close()

    response = {
        "depositId": result["id"],
        "code": result["code"],
        "amount": result["amount"],
        "status": result["status"],
        "payosStatus": result.get("payos_status"),
        "checkoutUrl": result.get("checkout_url"),
        "qrCode": result.get("qr_code"),
        "balance": balance
    }

    if payos_check and not payos_check["ok"]:
        response["message"] = f"Chưa đối soát được payOS: {payos_check.get('message', 'unknown')}"

    return jsonify(response)

@app.route("/api/payos/webhook", methods=["POST"])
def api_payos_webhook():
    # Webhook handler: verify signature if possible, parse payload và sync.
    try:
        body_json = request.get_json(silent=True) or {}
        raw_body = request.get_data(as_text=True)
        sig_header = request.headers.get("X-Payos-Signature") or request.headers.get("x-payos-signature") or request.headers.get("X-PAYOS-SIGNATURE")
        webhook_data = None

        try:
            # SDK verify (try normal verify first)
            webhook_data = payos.verifyPaymentWebhookData(body_json)
        except Exception:
            try:
                # Fallback: some SDK versions provide webhooks.verify(raw_body, signature)
                webhook_data = payos.webhooks.verify(raw_body, sig_header) if hasattr(payos.webhooks, "verify") else payos.webhooks.verify(raw_body)
            except Exception:
                # Last fallback: if verify not available, try to accept the parsed body (not recommended)
                webhook_data = body_json

    except Exception as e:
        return jsonify({"message": f"Invalid webhook: {e}"}), 400

    # Debug log
    try:
        print("[payOS webhook] payload:", webhook_data)
    except Exception:
        pass

    payload = get_value(webhook_data, "data", default=webhook_data)
    order_code = get_value(payload, "order_code", "orderCode")
    amount = get_value(payload, "amount")
    code = get_value(payload, "code", default="00")
    desc = get_value(payload, "desc", "description", default="")
    payment_link_id = get_value(payload, "payment_link_id", "paymentLinkId", "id")
    status_field = get_value(payload, "status", "status_code", default=None)

    if not order_code:
        return jsonify({"message": "Missing orderCode"}), 200

    # Determine success: if SDK provides status use it, otherwise use code/desc heuristics
    is_success = False
    if status_field:
        try:
            if str(status_field).upper() in ("PAID", "SUCCESS", "COMPLETED"):
                is_success = True
        except:
            pass
    else:
        if str(code) == "00" or str(desc).upper() in ("SUCCESS", "THANH CONG", "THANH CÔNG"):
            is_success = True

    if not is_success:
        # Not a success event -> ignore
        return jsonify({"message": "Ignored non-success payment"}), 200

    sync_result = sync_paid_deposit_by_order_code(
        order_code=str(order_code),
        payos_amount=amount,
        payos_status="PAID",
        payment_link_id=payment_link_id
    )
    return jsonify(sync_result), 200

@app.route("/api/checkout", methods=["POST"])
def api_checkout():
    user, error = require_login()
    if error:
        return error

    data = request.get_json() or {}
    items = data.get("items") or []

    if not items:
        return jsonify({"message": "Giỏ hàng đang trống"}), 400

    conn = get_conn()
    cur = conn.cursor()

    total = 0
    final_items = []

    for item in items:
        product_id = to_int(item.get("product_id"))
        qty = to_int(item.get("qty"))

        if qty <= 0:
            continue

        cur.execute("SELECT * FROM products WHERE id = ?", (product_id,))
        product = cur.fetchone()
        if not product:
            conn.close()
            return jsonify({"message": f"Sản phẩm ID {product_id} không tồn tại"}), 400

        line_total = product["price"] * qty
        total += line_total
        final_items.append((product, qty, line_total))

    if not final_items:
        conn.close()
        return jsonify({"message": "Không có sản phẩm hợp lệ"}), 400

    cur.execute("SELECT balance FROM users WHERE id = ?", (user["id"],))
    balance = cur.fetchone()["balance"]

    if balance < total:
        conn.close()
        return jsonify({"message": "Số dư không đủ, vui lòng nạp thêm tiền"}), 400

    new_balance = balance - total
    cur.execute("UPDATE users SET balance = ? WHERE id = ?", (new_balance, user["id"]))

    for product, qty, line_total in final_items:
        next_id = cur.execute("SELECT COALESCE(MAX(id), 0) + 1 AS next_id FROM orders").fetchone()["next_id"]
        code = make_code("DH", next_id)

        cur.execute("""
            INSERT INTO orders (code, user_id, username, product_name, qty, total_price, status, manual_key, note, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            code,
            user["id"],
            user["username"],
            product["name"],
            qty,
            line_total,
            "pending_key",
            "",
            "Đơn hàng đã tạo. Vui lòng liên hệ Telegram hoặc Zalo để nhận key.",
            now_vn()
        ))

        cur.execute("""
            INSERT INTO purchase_history (user_id, product_name, qty, total_price, created_at)
            VALUES (?, ?, ?, ?, ?)
        """, (
            user["id"],
            product["name"],
            qty,
            line_total,
            now_vn()
        ))

    conn.commit()
    conn.close()

    return jsonify({"message": "Thanh toán thành công"})

@app.route("/api/admin/dashboard")
def api_admin_dashboard():
    user, error = require_admin()
    if error:
        return error

    conn = get_conn()
    cur = conn.cursor()

    cur.execute("SELECT id, code, username, amount, note, status, created_at FROM deposits ORDER BY id DESC")
    deposits = [dict(row) for row in cur.fetchall()]

    cur.execute("""
        SELECT id, code, username, product_name, qty, total_price, status, manual_key, note, created_at
        FROM orders
        ORDER BY id DESC
    """)
    orders = [dict(row) for row in cur.fetchall()]

    cur.execute("SELECT COUNT(*) AS c FROM users WHERE role = 'user'")
    users_count = cur.fetchone()["c"]

    cur.execute("SELECT COUNT(*) AS c FROM orders")
    orders_count = cur.fetchone()["c"]

    cur.execute("SELECT COALESCE(SUM(total_price), 0) AS revenue FROM orders")
    revenue = cur.fetchone()["revenue"]

    conn.close()

    return jsonify({
        "deposits": deposits,
        "orders": orders,
        "stats": {
            "users": users_count,
            "orders": orders_count,
            "revenue": revenue
        }
    })

@app.route("/api/admin/deposits/<int:deposit_id>/approve", methods=["POST"])
def api_admin_approve_deposit(deposit_id):
    user, error = require_admin()
    if error:
        return error

    conn = get_conn()
    cur = conn.cursor()

    cur.execute("SELECT * FROM deposits WHERE id = ?", (deposit_id,))
    deposit = cur.fetchone()

    if not deposit:
        conn.close()
        return jsonify({"message": "Không tìm thấy lệnh nạp"}), 404

    if deposit["status"] == "paid":
        conn.close()
        return jsonify({"message": "Lệnh nạp này đã được duyệt trước đó"}), 400

    cur.execute("UPDATE deposits SET status = 'paid' WHERE id = ?", (deposit_id,))
    cur.execute("UPDATE users SET balance = balance + ? WHERE id = ?", (deposit["amount"], deposit["user_id"]))

    conn.commit()
    conn.close()

    return jsonify({"message": "Đã cộng tiền thành công"})

@app.route("/api/admin/orders/<int:order_id>/key", methods=["POST"])
def api_admin_order_key(order_id):
    user, error = require_admin()
    if error:
        return error

    data = request.get_json() or {}
    manual_key = (data.get("manual_key") or "").strip()

    conn = get_conn()
    cur = conn.cursor()

    cur.execute("SELECT id FROM orders WHERE id = ?", (order_id,))
    order = cur.fetchone()

    if not order:
        conn.close()
        return jsonify({"message": "Không tìm thấy đơn hàng"}), 404

    status = "ready" if manual_key else "pending_key"
    note = (
        "Admin đã thêm key thủ công. Nếu cần hỗ trợ thêm hãy liên hệ Telegram hoặc Zalo."
        if manual_key else
        "Đơn hàng đã tạo. Vui lòng liên hệ Telegram hoặc Zalo để nhận key."
    )

    cur.execute(
        "UPDATE orders SET manual_key = ?, status = ?, note = ? WHERE id = ?",
        (manual_key, status, note, order_id)
    )

    conn.commit()
    conn.close()

    return jsonify({"message": "Đã cập nhật key"})

@app.route("/api/admin/products", methods=["POST"])
def api_admin_add_product():
    user, error = require_admin()
    if error:
        return error

    data = request.get_json() or {}
    name = (data.get("name") or "").strip()
    category = (data.get("category") or "").strip()
    duration = (data.get("duration") or "").strip()
    price = to_int(data.get("price"))
    badge = (data.get("badge") or "Mới").strip()
    description = (data.get("description") or "").strip()

    if not name or not category or not duration or price <= 0:
        return jsonify({"message": "Vui lòng nhập đầy đủ thông tin sản phẩm"}), 400

    conn = get_conn()
    cur = conn.cursor()

    cur.execute("""
        INSERT INTO products (name, category, duration, price, badge, description)
        VALUES (?, ?, ?, ?, ?, ?)
    """, (name, category, duration, price, badge, description))

    conn.commit()
    conn.close()

    return jsonify({"message": "Đã thêm sản phẩm"})

@app.route("/api/admin/products/<int:product_id>", methods=["DELETE"])
def api_admin_delete_product(product_id):
    user, error = require_admin()
    if error:
        return error

    conn = get_conn()
    cur = conn.cursor()

    cur.execute("SELECT id FROM products WHERE id = ?", (product_id,))
    product = cur.fetchone()

    if not product:
        conn.close()
        return jsonify({"message": "Không tìm thấy sản phẩm"}), 404

    cur.execute("DELETE FROM products WHERE id = ?", (product_id,))
    conn.commit()
    conn.close()

    return jsonify({"message": "Đã xóa sản phẩm"})

@app.route("/api/admin/payos/confirm-webhook", methods=["POST"])
def api_admin_confirm_webhook():
    user, error = require_admin()
    if error:
        return error

    if not is_public_url(WEBHOOK_URL):
        return jsonify({
            "message": "Webhook URL chưa public hoặc không phải HTTPS. Hãy đổi PUBLIC_BASE_URL sang domain/ngrok public https trước.",
            "webhookUrl": WEBHOOK_URL
        }), 400

    try:
        try:
            result = payos.confirm_webhook(WEBHOOK_URL)
        except Exception:
            result = payos.webhooks.confirm(WEBHOOK_URL)

        return jsonify({
            "message": "Confirm webhook thành công",
            "webhookUrl": WEBHOOK_URL,
            "result": obj_to_dict(result)
        })
    except Exception as e:
        return jsonify({
            "message": f"Confirm webhook thất bại: {e}",
            "webhookUrl": WEBHOOK_URL
        }), 500

if __name__ == "__main__":
    init_db()
    confirm_payos_webhook()
    app.run(host="0.0.0.0", port=5000, debug=False)