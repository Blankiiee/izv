const app = document.getElementById("app");
const modalRoot = document.getElementById("modal-root");
const toastRegion = document.getElementById("toast-region");
const today = new Date();
const isoToday = `${today.getFullYear()}-${String(today.getMonth() + 1).padStart(2, "0")}-${String(today.getDate()).padStart(2, "0")}`;
const firstOfMonth = `${isoToday.slice(0, 7)}-01`;
const views = { dashboard: "Огляд", schedule: "Афіша й сеанси", movies: "Фільмотека", tickets: "Квитки", halls: "Кінозали", queries: "Конструктор SQL", reports: "Звіти", guide: "Практикум" };
const state = { view: "dashboard", day: isoToday, query: "schedule", queryFields: ["m.Title", "g.GenreName", "h.HallName", "s.StartTime", "s.TicketPrice"], filters: [{ field: "h.IsVIP", operator: "=", value: "0" }], results: null, report: "revenue", start: firstOfMonth, end: isoToday, movieSearch: "", ticketSearch: "", ticketStatus: "all" };
const fieldNames = { "m.Title": "Назва фільму", "m.AgeRating": "Віковий рейтинг", "g.GenreName": "Жанр", "h.HallName": "Кінозал", "h.Capacity": "Місткість", "h.IsVIP": "VIP-зала", "s.StartTime": "Час сеансу", "s.TicketPrice": "Ціна квитка", "s.SessionID": "№ сеансу", "t.TicketID": "№ квитка", "t.CustomerName": "Покупець", "t.PurchaseDate": "Дата покупки", "t.IsPaid": "Оплачено" };
const fields = Object.keys(fieldNames);
const presets = {
    schedule: { label: "Розклад сеансів", sql: "SELECT m.Title, m.AgeRating, g.GenreName AS Genre,\n       h.HallName AS Hall, h.Capacity,\n       s.StartTime, s.TicketPrice\nFROM Genres g JOIN Movies m ON m.GenreID = g.GenreID\nJOIN Sessions s ON s.MovieID = m.MovieID\nJOIN Halls h ON h.HallID = s.HallID\nWHERE h.IsVIP = 0\nORDER BY s.StartTime ASC;", sqlKind: "schedule" },
    revenue: { label: "Збори й продажі", sql: "SELECT m.Title, COUNT(t.TicketID) AS TicketsSold,\n       SUM(s.TicketPrice) AS Revenue\nFROM Movies m JOIN Sessions s ON s.MovieID = m.MovieID\nJOIN Tickets t ON t.SessionID = s.SessionID\nGROUP BY m.MovieID\nHAVING SUM(s.TicketPrice) > 300\nORDER BY Revenue DESC;", sqlKind: "revenue" },
    occupancy: { label: "Завантаженість залів", sql: "SELECT s.SessionID, m.Title, s.StartTime,\n       h.HallName, h.Capacity,\n       COUNT(t.TicketID) AS TicketsSold,\n       ROUND(COUNT(t.TicketID)*100.0/h.Capacity,1) AS Occupancy\nFROM Sessions s JOIN Movies m ON m.MovieID = s.MovieID\nJOIN Halls h ON h.HallID = s.HallID\nLEFT JOIN Tickets t ON t.SessionID = s.SessionID\nGROUP BY s.SessionID\nORDER BY Occupancy DESC;", sqlKind: "occupancy" },
    client: { label: "Пошук покупця", sql: "SELECT t.TicketID, t.CustomerName, t.SeatNumber,\n       t.PurchaseDate, t.IsPaid, s.StartTime,\n       s.TicketPrice, m.Title, h.HallName\nFROM Tickets t JOIN Sessions s ON s.SessionID = t.SessionID\nJOIN Movies m ON m.MovieID = s.MovieID\nJOIN Halls h ON h.HallID = s.HallID\nWHERE t.CustomerName LIKE ?\n  AND date(t.PurchaseDate) BETWEEN ? AND ?\nORDER BY t.PurchaseDate DESC;", sqlKind: "client" },
    customers: { label: "Активні клієнти", sql: "SELECT t.CustomerName,\n       COUNT(t.TicketID) AS TicketsBought\nFROM Tickets t WHERE t.IsPaid = 1\nGROUP BY t.CustomerName\nHAVING COUNT(t.TicketID) > 2\nORDER BY TicketsBought DESC;", sqlKind: "customers" },
    custom: { label: "Свій запит", sqlKind: "custom" },
};

function esc(value) {
    return String(value ?? "").replace(/[&<>"']/g, char => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" })[char]);
}
function money(value) { return `${new Intl.NumberFormat("uk-UA", { maximumFractionDigits: 0 }).format(Number(value) || 0)} ₴`; }
function fmtDate(value, options = { day: "2-digit", month: "short" }) {
    if (!value) return "—";
    const d = new Date(String(value).replace(" ", "T"));
    return Number.isNaN(d.getTime()) ? String(value) : new Intl.DateTimeFormat("uk-UA", options).format(d);
}
function fmtTime(value) {
    if (!value) return "—";
    const d = new Date(String(value).replace(" ", "T"));
    return Number.isNaN(d.getTime()) ? String(value).slice(11, 16) : new Intl.DateTimeFormat("uk-UA", { hour: "2-digit", minute: "2-digit" }).format(d);
}
function dateTime(value) {
    if (!value) return "—";
    const d = new Date(String(value).replace(" ", "T"));
    return Number.isNaN(d.getTime()) ? String(value) : new Intl.DateTimeFormat("uk-UA", { day: "2-digit", month: "2-digit", year: "numeric", hour: "2-digit", minute: "2-digit" }).format(d);
}
function safeColor(color) { return /^#[\da-f]{6}$/i.test(color || "") ? color : "#947052"; }
async function api(url, options = {}) {
    const response = await fetch(url, { ...options, headers: { "Content-Type": "application/json", ...options.headers } });
    const body = await response.json();
    if (!response.ok) throw Error(body.error || `Помилка запиту (${response.status}).`);
    return body;
}
function toast(message, type = "success") {
    const node = document.createElement("div");
    node.className = `toast ${type}`;
    node.textContent = message;
    toastRegion.append(node);
    setTimeout(() => node.remove(), 3500);
}
function heading(kicker, title, subtitle, actions = "") {
    return `<div class="page-heading"><div><p class="eyebrow">${esc(kicker)}</p><h1>${esc(title)}</h1><p class="page-subtitle">${esc(subtitle)}</p></div>${actions ? `<div class="button-row">${actions}</div>` : ""}</div>`;
}
function panel(title, body, opts = {}) {
    return `<section class="panel ${opts.className || ""}"><div class="panel-header"><div><h2 class="panel-title">${esc(title)}</h2>${opts.note ? `<div class="panel-note">${esc(opts.note)}</div>` : ""}</div>${opts.action || ""}</div>${opts.raw ? body : `<div class="panel-body">${body}</div>`}</section>`;
}
function table(headers, rows, width = "640px") {
    if (!rows.length) return '<div class="empty-state"><strong>Записів поки немає</strong>Змініть фільтр або додайте дані.</div>';
    return `<div class="table-wrap"><table class="data-table" style="min-width:${width}"><thead><tr>${headers.map(h => `<th>${esc(h)}</th>`).join("")}</tr></thead><tbody>${rows.join("")}</tbody></table></div>`;
}
function badge(text, kind = "gray") { return `<span class="badge badge-${kind}">${esc(text)}</span>`; }
function paid(isPaid) { return Number(isPaid) === 1 ? badge("Оплачено", "green") : badge("Очікує оплати", "amber"); }
function occupancy(value) {
    const percent = Math.max(0, Math.min(100, Number(value) || 0));
    return `<span class="occupancy-bar"><span style="width:${percent}%"></span></span>${Number(value) || 0}%`;
}
function render() {
    state.view = views[location.hash.slice(1)] ? location.hash.slice(1) : "dashboard";
    document.getElementById("breadcrumb-current").textContent = views[state.view];
    document.getElementById("topbar-date").textContent = new Intl.DateTimeFormat("uk-UA", { weekday: "long", day: "numeric", month: "long" }).format(today);
    document.querySelectorAll("[data-view]").forEach(link => link.classList.toggle("active", link.dataset.view === state.view));
    document.getElementById("sidebar").classList.remove("open");
    const tasks = { dashboard: dashboard, schedule: schedule, movies: movies, tickets: tickets, halls: halls, queries: queries, reports: reports, guide: guide };
    app.innerHTML = '<div class="empty-state">Завантажуємо дані…</div>';
    tasks[state.view]().catch(error => {
        app.innerHTML = `<section class="panel"><div class="empty-state"><strong>Не вдалося завантажити сторінку</strong>${esc(error.message)}</div></section>`;
        toast(error.message, "error");
    });
}
async function dashboard() {
    const data = await api("/api/overview");
    const m = data.metrics;
    const max = Math.max(1, ...data.bestSellers.map(x => Number(x.Sold)));
    const sessions = data.sessions.length ? `<div class="session-list">${data.sessions.map(x => `<div class="session-row"><div class="session-time">${fmtTime(x.StartTime)}</div><div class="session-film"><strong>${esc(x.Title)}</strong><small>${esc(x.HallName)} · ${x.DurationMinutes} хв</small></div><div class="session-price">${money(x.TicketPrice)}</div><div class="occupancy-mini"><strong>${x.Occupancy}%</strong><small>${x.Sold} місць</small></div></div>`).join("")}</div>` : '<div class="empty-state">Сьогодні без сеансів.</div>';
    const ranking = data.bestSellers.map((x, i) => `<div class="rank-item"><span class="rank-number">${String(i + 1).padStart(2, "0")}</span><div class="rank-copy"><span class="rank-title">${esc(x.Title)}</span><span class="rank-track"><span class="rank-fill" style="width:${Math.max(3, x.Sold / max * 100)}%;background:${safeColor(x.Accent)}"></span></span></div><span class="rank-count">${x.Sold} кв.</span></div>`).join("") || '<div class="empty-state">Ще немає продажів.</div>';
    app.innerHTML = `${heading(`${new Intl.DateTimeFormat("uk-UA", { weekday: "long" }).format(today)} · CinemaHub`, "Добрий день", "Ось як проходить робота кінотеатру сьогодні.", '<button class="button button-primary" data-action="new-ticket">＋ Продати квиток</button>')}
    <div class="metric-grid">${[[ "Фільмів у каталозі", m.movie_count, "активна фільмотека", "▤" ], [ "Сеансів сьогодні", m.today_sessions, "у всіх кінозалах", "▦" ], [ "Оплачених квитків", m.paid_tickets, "всього продано", "▧" ], [ "Касові збори", money(m.revenue), "за оплачені квитки", "₴" ]].map(([label, value, foot, icon]) => `<div class="metric-card"><div class="metric-header"><span class="metric-label">${label}</span><span class="metric-icon">${icon}</span></div><div class="metric-value">${value}</div><div class="metric-foot">${foot}</div></div>`).join("")}</div>
    <div class="dashboard-grid">${panel("Розклад на сьогодні", sessions, { note: fmtDate(isoToday, { day: "numeric", month: "long", year: "numeric" }), raw: true, action: '<a class="link-arrow" href="#schedule">Усі сеанси ↗</a>' })}${panel("Найпопулярніші фільми", `<div class="rank-list">${ranking}</div>`, { note: "за оплаченими квитками" })}</div>
    ${panel("Робочий стіл", '<div class="button-row"><button class="button" data-navigate="movies">Перейти до фільмотеки</button><button class="button" data-navigate="queries">Відкрити конструктор SQL</button><button class="button" data-navigate="reports">Сформувати звіт</button></div>', { note: "Зручні розділи CinemaHub" })}`;
}
async function schedule() {
    const [rows, allMovies, hallsList] = await Promise.all([api(`/api/sessions?date=${encodeURIComponent(state.day)}`), api("/api/movies"), api("/api/halls")]);
    const body = rows.map(x => `<tr><td class="tabular">${fmtTime(x.StartTime)}<span class="table-subtitle">${fmtDate(x.StartTime)}</span></td><td class="table-title">${esc(x.Title)}<span class="table-subtitle">${esc(x.GenreName)} · ${x.DurationMinutes} хв · ${esc(x.AgeRating)}</span></td><td>${esc(x.HallName)}${x.IsVIP ? '<span class="table-subtitle">VIP Lounge</span>' : ""}</td><td>${x.Sold} / ${x.Capacity}<span class="table-subtitle">${occupancy(x.Occupancy)}</span></td><td>${money(x.TicketPrice)}</td><td><button class="button button-small" data-action="new-ticket" data-session-id="${x.SessionID}">Продати</button> <button class="button button-small button-danger" data-action="delete-session" data-id="${x.SessionID}">Видалити</button></td></tr>`);
    app.innerHTML = `${heading("Щоденний розклад", "Афіша й сеанси", "Завантаженість залів, покази й продаж квитків.", '<button class="button button-primary" data-action="new-session">＋ Додати сеанс</button>')}
    <div class="table-controls"><div class="control-group"><label class="form-label" for="schedule-date">Дата показів</label><input id="schedule-date" class="date-field" type="date" value="${state.day}"></div><span class="badge badge-gray">${rows.length} сеансів</span></div>
    ${panel("Сеанси", table(["Час початку", "Фільм", "Зала", "Місця", "Ціна", "Дії"], body, "830px"), { note: `${fmtDate(state.day, { day: "numeric", month: "long", year: "numeric" })} · ${hallsList.length} залів` })}
    <div class="panel" style="margin-top:14px"><div class="panel-header"><h2 class="panel-title">Швидкий перехід до дати</h2></div><div class="panel-body"><div class="button-row">${[-1, 0, 1, 2, 3].map(offset => { const d = new Date(`${isoToday}T12:00:00`); d.setDate(d.getDate() + offset); const value = d.toISOString().slice(0, 10); return `<button class="button button-small ${state.day === value ? "button-warm" : ""}" data-action="set-date" data-date="${value}">${offset === 0 ? "Сьогодні" : offset === -1 ? "Вчора" : fmtDate(value, { weekday: "short", day: "numeric", month: "short" })}</button>`; }).join("")}</div></div></div>`;
    document.getElementById("schedule-date").addEventListener("change", event => { state.day = event.target.value || isoToday; render(); });
    window.cinemaMovies = allMovies;
}
async function movies() {
    const [list, genresList] = await Promise.all([api("/api/movies"), api("/api/genres")]);
    const filtered = list.filter(x => `${x.Title} ${x.GenreName}`.toLowerCase().includes(state.movieSearch.toLowerCase()));
    const cards = filtered.map((x, i) => `<article class="film-card"><div class="poster" style="background:linear-gradient(160deg,${safeColor(x.Accent)},#191c20)"><span class="poster-wordmark">CINEMAHUB · ${String(i + 1).padStart(2, "0")}</span><div><div class="poster-title">${esc(x.Title)}</div><div class="poster-meta">${esc(x.GenreName)} · ${x.DurationMinutes} ХВ</div></div></div><div class="film-body"><div class="film-title-row"><div class="film-title">${esc(x.Title)}</div><span class="rating-label">${esc(x.AgeRating)}</span></div><div class="film-meta">${esc(x.GenreName)} · ${x.DurationMinutes} хв · ${x.Sessions} сеансів</div><p class="film-synopsis">${esc(x.Synopsis || "Опис ще не додано.")}</p><div class="film-footer"><span class="film-price">${money(x.BasePrice)} <small>від</small></span><span class="button-row"><button class="button button-small" data-action="edit-movie" data-id="${x.MovieID}">Редагувати</button><button class="button button-small button-danger" data-action="delete-movie" data-id="${x.MovieID}">Видалити</button></span></div></div></article>`).join("");
    app.innerHTML = `${heading("Колекція CinemaHub", "Фільмотека", "Каталог фільмів, жанрів, тривалості й цін.", '<button class="button button-primary" data-action="new-movie">＋ Додати фільм</button>')}
    <div class="table-controls"><span class="panel-note">${list.length} фільмів · ${genresList.length} жанрів</span><input class="search-field" id="movie-search" type="search" placeholder="Знайти фільм або жанр" value="${esc(state.movieSearch)}"></div>
    ${cards ? `<div class="film-grid">${cards}</div>` : '<div class="panel empty-state">Фільмів не знайдено.</div>'}`;
    document.getElementById("movie-search").addEventListener("input", event => {
        state.movieSearch = event.target.value;
        const position = event.target.selectionStart;
        movies().then(() => {
            const input = document.getElementById("movie-search");
            input.focus();
            input.setSelectionRange(position, position);
        });
    });
}
async function tickets() {
    const params = new URLSearchParams({ status: state.ticketStatus, search: state.ticketSearch });
    const rows = await api(`/api/tickets?${params}`);
    const rendered = rows.map(x => `<tr><td class="table-title">#${String(x.TicketID).padStart(5, "0")}<span class="table-subtitle">місце ${x.SeatNumber}</span></td><td class="table-title">${esc(x.CustomerName)}<span class="table-subtitle">${esc(x.CustomerPhone || "Телефон не вказаний")}</span></td><td>${esc(x.Title)}<span class="table-subtitle">${esc(x.HallName)} · ${fmtDate(x.StartTime)} ${fmtTime(x.StartTime)}</span></td><td>${paid(x.IsPaid)}</td><td>${money(x.TicketPrice)}</td><td><button class="button button-small" data-action="print-ticket" data-id="${x.TicketID}">Квиток</button>${Number(x.IsPaid) ? "" : ` <button class="button button-small" data-action="mark-paid" data-id="${x.TicketID}">Оплатити</button>`} <button class="button button-small button-danger" data-action="delete-ticket" data-id="${x.TicketID}">×</button></td></tr>`);
    const countPaid = rows.filter(x => Number(x.IsPaid)).length;
    app.innerHTML = `${heading("Операційна звітність", "Продаж квитків", "Покупці, оплати й готові до друку квитанції.", '<button class="button button-primary" data-action="new-ticket">＋ Продати квиток</button>')}
    <div class="table-controls"><div class="control-group"><select class="filter-select" id="ticket-status"><option value="all" ${state.ticketStatus === "all" ? "selected" : ""}>Усі · ${rows.length}</option><option value="paid" ${state.ticketStatus === "paid" ? "selected" : ""}>Оплачені · ${countPaid}</option><option value="pending" ${state.ticketStatus === "pending" ? "selected" : ""}>Броні · ${rows.length - countPaid}</option></select><input id="ticket-search" class="search-field" type="search" placeholder="Клієнт, фільм або № квитка" value="${esc(state.ticketSearch)}"></div><span class="panel-note">${rows.length} записів</span></div>
    ${panel("Реєстр продажів", table(["Квиток", "Покупець", "Сеанс", "Статус", "Вартість", "Дії"], rendered, "900px"), { note: "Квитанцію можна відкрити та роздрукувати." })}`;
    document.getElementById("ticket-status").addEventListener("change", e => { state.ticketStatus = e.target.value; tickets(); });
    let timer;
    document.getElementById("ticket-search").addEventListener("input", e => {
        state.ticketSearch = e.target.value;
        clearTimeout(timer);
        timer = setTimeout(() => {
            const position = document.getElementById("ticket-search").selectionStart;
            tickets().then(() => {
                const input = document.getElementById("ticket-search");
                input.focus();
                input.setSelectionRange(position, position);
            });
        }, 200);
    });
}
async function halls() {
    const [hallList, genresList] = await Promise.all([api("/api/halls"), api("/api/genres")]);
    const cards = hallList.map(x => {
        const occupied = Math.round(48 * Number(x.Occupancy) / 100);
        return `<article class="panel hall-card"><div class="hall-title-row"><h2 class="hall-title">${esc(x.HallName)}</h2>${x.IsVIP ? badge("VIP", "amber") : badge("Стандарт")}</div><div class="hall-illustration" aria-label="Схема розміщення місць">${Array.from({ length: 6 }, (_, row) => `<div class="seat-row">${Array.from({ length: 8 }, (_, col) => `<span class="seat-dot ${row * 8 + col < occupied ? "occupied" : ""}"></span>`).join("")}</div>`).join("")}</div><div class="hall-facts"><div><strong>${x.Capacity}</strong><small>місць</small></div><div><strong>${x.Sessions}</strong><small>сеансів</small></div><div><strong>${x.TicketsSold}</strong><small>продано</small></div></div><div class="hall-progress"><span style="width:${Math.min(100, x.Occupancy)}%"></span></div><div class="panel-note">Завантаженість · ${x.Occupancy}%</div><div class="button-row" style="margin-top:12px"><button class="button button-small button-danger" data-action="delete-hall" data-id="${x.HallID}">Видалити зал</button></div></article>`;
    }).join("");
    app.innerHTML = `${heading("Зали й місткість", "Кінозали", "Місткість, VIP-статус і завантаженість.", '<button class="button" data-action="new-genre">＋ Жанр</button><button class="button button-primary" data-action="new-hall">＋ Додати зал</button>')}
    <div class="hall-grid">${cards}</div>
    <div class="panel" style="margin-top:14px"><div class="panel-header"><h2 class="panel-title">Жанри фільмотеки · ${genresList.length}</h2></div><div class="panel-body"><div class="button-row">${genresList.map(x => `<span class="badge badge-gray">${esc(x.GenreName)}<button class="mini-remove" data-action="delete-genre" data-id="${x.GenreID}" aria-label="Видалити жанр">×</button></span>`).join("")}</div></div></div>
    <div class="panel" style="margin-top:14px"><div class="panel-header"><div><h2 class="panel-title">Зв’язок залів із розкладом</h2><div class="panel-note">${hallList.reduce((n, x) => n + Number(x.Sessions), 0)} сеансів</div></div><a class="link-arrow" href="#schedule">Відкрити розклад ↗</a></div><div class="panel-body"><p class="page-subtitle">Застосунок перевіряє місткість залу та унікальність місця для кожного квитка.</p></div></div>`;
}
function diagram(kind) {
    const names = kind === "client" ? ["Tickets", "Sessions", "Movies", "Halls"] : kind === "revenue" ? ["Movies", "Sessions", "Tickets"] : kind === "customers" ? ["Tickets"] : ["Genres", "Movies", "Sessions", "Halls", "Tickets"];
    return `<div class="diagram">${names.map((x, i) => `${i ? '<span class="diagram-link">⟷</span>' : ""}<div class="diagram-table"><strong>${x}</strong><small>${x === "Tickets" ? "TicketID · SessionID · IsPaid" : x === "Sessions" ? "SessionID · MovieID · HallID" : x === "Movies" ? "MovieID · GenreID · Title" : x === "Halls" ? "HallID · Capacity · IsVIP" : "GenreID · GenreName"}</small></div>`).join("")}</div>`;
}
function customSql() {
    const selected = state.queryFields.length ? state.queryFields : ["m.Title"];
    const filters = state.filters.filter(x => x.value !== "");
    const where = filters.length ? `\nWHERE ${filters.map(x => `${x.field} ${x.operator === "contains" ? "LIKE" : x.operator} ?`).join("\n  AND ")}` : "";
    return `SELECT\n    ${selected.join(",\n    ")}\nFROM Genres g JOIN Movies m ON m.GenreID = g.GenreID\nJOIN Sessions s ON s.MovieID = m.MovieID\nJOIN Halls h ON h.HallID = s.HallID\nLEFT JOIN Tickets t ON t.SessionID = s.SessionID${where}\nORDER BY ${selected[0]} ASC\nLIMIT 200;`;
}
function queryGrid() {
    const rows = state.filters.map((x, index) => `<div class="criteria-row"><select class="form-select" data-filter-index="${index}" data-key="field">${fields.map(f => `<option value="${f}" ${x.field === f ? "selected" : ""}>${esc(fieldNames[f])}</option>`).join("")}</select><select class="form-select" data-filter-index="${index}" data-key="operator">${["=", "!=", ">", ">=", "<", "<=", "contains"].map(op => `<option value="${op}" ${x.operator === op ? "selected" : ""}>${op === "contains" ? "містить" : op}</option>`).join("")}</select><input class="form-input" data-filter-index="${index}" data-key="value" value="${esc(x.value)}"><span class="criteria-head">умова ${index + 1}</span><button class="mini-remove" data-action="remove-filter" data-index="${index}">×</button></div>`).join("");
    return `<div class="criteria-grid"><div class="criteria-head">Поле</div><div class="criteria-head">Оператор</div><div class="criteria-head">Значення</div><div class="criteria-head">Умова</div><span></span>${rows}</div>`;
}
async function queries() {
    const data = state.results;
    const result = data ? table(data.columns, data.rows.map(row => `<tr>${data.columns.map(key => `<td>${esc(row[key] ?? "—")}</td>`).join("")}</tr>`)) : '<div class="empty-state"><strong>Результати запиту з’являться тут</strong>Оберіть шаблон і виконайте запит.</div>';
    const form = state.query === "custom"
        ? `<div class="check-list">${fields.map(f => `<label class="check-field"><input type="checkbox" data-column="${f}" ${state.queryFields.includes(f) ? "checked" : ""}>${esc(fieldNames[f])}</label>`).join("")}</div><div class="panel-header" style="padding:12px 0"><h2 class="panel-title">Умови відбору</h2><button class="button button-small" data-action="add-filter">＋ Умова</button></div>${queryGrid()}`
        : state.query === "client"
            ? `<div class="form-grid" style="padding:0"><label class="form-field"><span class="form-label">Ім’я покупця містить</span><input class="form-input" id="client-name" placeholder="Наприклад, Олександр"></label><label class="form-field"><span class="form-label">Придбано з</span><input class="form-input" id="client-start" type="date" value="${state.start}"></label><label class="form-field"><span class="form-label">до</span><input class="form-input" id="client-end" type="date" value="${state.end}"></label></div>`
            : '<p class="page-subtitle">Шаблон виконує справжній запит до бази CinemaHub.</p>';
    app.innerHTML = `${heading("Query Builder · чотири панелі", "Конструктор запитів", "Таблиці, поля, SQL-код і результат виконання в одному місці.")}
    <div class="query-presets" style="margin-bottom:14px">${Object.entries(presets).map(([key, value]) => `<button class="preset-chip ${state.query === key ? "active" : ""}" data-preset="${key}">${value.label}</button>`).join("")}</div>
    <div class="query-layout"><div>${panel("1 · Діаграма таблиць", diagram(state.query), { note: "Зв’язки зовнішніми ключами" })}<div style="height:12px"></div>${panel("2 · Сітка полів і критеріїв", form)}<div style="height:12px"></div>${panel("3 · Згенерований SQL", `<pre class="sql-preview" id="sql-preview">${esc(presets[state.query].sql || customSql())}</pre><div class="button-row" style="margin-top:10px"><button class="button button-small" data-action="copy-sql">Копіювати SQL</button><button class="button button-small button-primary" data-action="run-query">▶ Виконати запит</button><span class="panel-note">До 200 рядків</span></div>`)}<div style="height:12px"></div>${panel("4 · Результати виконання", `<div id="query-results">${result}</div>`, { note: data ? `${data.rows.length} рядків · SQLite` : "Очікується запит" })}</div>
    <div>${panel("Компоненти генератора", `<div class="check-list">${["Diagram Pane · таблиці й JOIN", "Grid / Criteria Pane · поля й фільтри", "SQL Pane · запит T-SQL", "Results Pane · дані", "GROUP BY, COUNT, SUM, HAVING"].map(x => `<div class="check-field">${badge("✓", "green")}${esc(x)}</div>`).join("")}</div>`)}<div style="height:12px"></div>${panel("Методичний матеріал", '<p class="page-subtitle">Розділ відтворює логіку Query Builder та DataSet Designer з практикуму. Динамічні умови передаються параметрами.</p><a class="link-arrow" href="#guide">Переглянути практикум ↗</a>')}</div></div>`;
    document.querySelectorAll("[data-preset]").forEach(btn => btn.addEventListener("click", () => { state.query = btn.dataset.preset; state.results = null; if (state.query === "schedule") state.filters = [{ field: "h.IsVIP", operator: "=", value: "0" }]; if (state.query === "custom") state.queryFields = ["m.Title", "g.GenreName", "s.StartTime", "s.TicketPrice"]; render(); }));
    document.querySelectorAll("[data-column]").forEach(input => input.addEventListener("change", () => { state.queryFields = [...document.querySelectorAll("[data-column]:checked")].map(x => x.dataset.column); const preview = document.getElementById("sql-preview"); if (preview) preview.textContent = customSql(); }));
    document.querySelectorAll("[data-key]").forEach(input => input.addEventListener("input", () => { state.filters[Number(input.dataset.filterIndex)][input.dataset.key] = input.value; const preview = document.getElementById("sql-preview"); if (preview) preview.textContent = customSql(); }));
}
async function reports() {
    const data = await api(`/api/reports?start=${encodeURIComponent(state.start)}&end=${encodeURIComponent(state.end)}`);
    const tabs = [["revenue", "Виручка за фільмами"], ["halls", "Заповненість залів"], ["matrix", "Дні й часи"]];
    let content;
    if (state.report === "halls") {
        content = panel("Завантаження залів", table(["Кінозал", "Місткість", "Продано", "Заповненість", "Виручка"], data.halls.map(x => `<tr><td class="table-title">${esc(x.HallName)}</td><td>${x.Capacity}</td><td>${x.TicketsSold}</td><td>${occupancy(x.Occupancy)}</td><td>${money(x.Revenue)}</td></tr>`)));
    } else if (state.report === "matrix") {
        const days = ["Понеділок", "Вівторок", "Середа", "Четвер", "П’ятниця", "Субота", "Неділя"];
        const slots = ["10:00–13:00", "13:00–17:00", "17:00–21:00", "21:00+"];
        const lookup = new Map(data.timeSlots.map(x => [`${x.Day}|${x.TimeSlot}`, x]));
        const maximum = Math.max(1, ...data.timeSlots.map(x => Number(x.Revenue)));
        const rows = days.map(day => `<tr><td class="table-title">${day}</td>${slots.map(slot => { const item = lookup.get(`${day}|${slot}`); if (!item) return "<td>—</td>"; const shade = Math.round(245 - item.Revenue / maximum * 50); return `<td style="background:rgb(245,${shade},${shade - 11})">${money(item.Revenue)}<span class="table-subtitle">${item.TicketsSold} кв.</span></td>`; }).join("")}</tr>`);
        content = panel("Матриця продажів · день і час", table(["День тижня", ...slots], rows, "700px"), { note: "Виручка за часом початку сеансу" });
    } else {
        const maximum = Math.max(1, ...data.revenue.map(x => Number(x.Revenue)));
        const chart = data.revenue.filter(x => Number(x.Revenue)).map(x => `<div class="chart-column"><span class="chart-value">${money(x.Revenue)}</span><span class="chart-bar" style="height:${Math.max(5, x.Revenue / maximum * 92)}px"></span><span class="chart-label">${esc(x.Title.slice(0, 12))}</span></div>`).join("");
        content = `<div>${panel("Виручка за фільмами", `<div class="bar-chart">${chart || "За цей період немає продажів."}</div>`, { note: "Оплачені квитки у гривнях" })}<div style="height:12px"></div>${panel("Деталізація", table(["Фільм", "Продано квитків", "Касові збори"], data.revenue.map(x => `<tr><td class="table-title">${esc(x.Title)}</td><td>${x.TicketsSold}</td><td>${money(x.Revenue)}</td></tr>`)))}</div>`;
    }
    app.innerHTML = `${heading("Аналітична звітність", "Звіти та аналітика", "Виручка, продажі та завантаженість кінозалу.", '<button class="button" data-action="export-report">↓ Експорт CSV</button><button class="button button-primary" data-action="print-report">Друкувати</button>')}
    <div class="table-controls"><div class="control-group"><label class="form-label">Період</label><input class="date-field" type="date" id="report-start" value="${state.start}"> — <input class="date-field" type="date" id="report-end" value="${state.end}"><button class="button button-small" id="apply-report">Оновити</button></div><span class="panel-note">За датою купівлі</span></div>
    <div class="report-stats">${[[ "Оплачені квитки", data.totals.tickets ], [ "Зібрано", money(data.totals.revenue) ], [ "Середній чек", money(data.totals.average_price) ]].map(([label, value]) => `<div class="report-stat"><small>${label}</small><strong>${value}</strong></div>`).join("")}</div>
    <div class="select-tabs">${tabs.map(([key, label]) => `<button class="select-tab ${state.report === key ? "active" : ""}" data-report="${key}">${label}</button>`).join("")}</div>${content}`;
    document.getElementById("apply-report").addEventListener("click", () => { state.start = document.getElementById("report-start").value; state.end = document.getElementById("report-end").value; render(); });
    document.querySelectorAll("[data-report]").forEach(btn => btn.addEventListener("click", () => { state.report = btn.dataset.report; render(); }));
    window.cinemaReport = data;
}
function guide() {
    const cards = [
        ["МОДУЛЬ 01 · БАЗА ДАНИХ", "Схема й зв’язки таблиць", "Схема CinemaHub_DB складається з п’яти реляційних таблиць.", ["Genres → Movies: жанри й каталог.", "Movies + Halls → Sessions: розклад і ціна.", "Sessions → Tickets: місце, покупець і оплата.", "PRIMARY KEY, FOREIGN KEY та перевірки місткості, ціни й місця."]],
        ["МОДУЛЬ 02 · QUERY BUILDER", "Візуальний конструктор SQL", "Працюйте з чотирма панелями генератора запитів.", ["Diagram Pane: таблиці та зв’язки.", "Grid / Criteria Pane: поля, псевдоніми, умови.", "SQL Pane: згенерований запит.", "Results Pane: дані після виконання."]],
        ["МОДУЛЬ 03 · ГЕНЕРАТОРИ Й ОПТИМІЗАЦІЯ", "JOIN, групування та SQL", "Готові сценарії показують інструменти з методички.", ["Розклад: INNER JOIN, IsVIP = 0 та сортування.", "Каса: GROUP BY, SUM, COUNT і HAVING.", "Місткість: LEFT JOIN та облік порожніх сеансів.", "Клієнт: параметризований пошук і індекси."]],
        ["МОДУЛЬ 04 · REPORTS", "Квитки й звіти", "Операційна й аналітична звітність кінотеатру.", ["Квиток: фільм, час, зал, місце, оплата й друк.", "RDLC: оперативні чеки й табличні звіти.", "Crystal Reports: групування й підзвіти.", "Виручка, діаграма та матриця дня і часу."]],
    ];
    app.innerHTML = `${heading("Навчальні матеріали · CinemaHub", "Практикум", "Чотири лабораторні модулі: база даних, SQL-генератор і звітність.")}
    <section class="guide-banner"><div><p class="eyebrow">Навчальний проєкт</p><h2>Від структури БД до звіту для керівника</h2><p>CinemaHub — інформаційна система онлайн-кінотеатру для обліку фільмів, показів, квитків та касових зборів.</p></div><a class="button button-warm" href="/schema.sql" download="cinemahub.sql">SQL-схема ↓</a></section>
    <div class="guide-grid">${cards.map(([number, title, description, items]) => `<article class="panel guide-card"><span class="guide-number">${number}</span><h2>${title}</h2><p>${description}</p><ul>${items.map(item => `<li>${esc(item)}</li>`).join("")}</ul></article>`).join("")}</div>
    <div class="guide-detail" style="margin-top:13px"><section class="panel"><h3>Push Model — рекомендована модель</h3><p>Застосунок читає й перевіряє дані перед передаванням їх до звіту.</p></section><section class="panel"><h3>Cross-Tab та підзвіти</h3><p>Матриця показує виручку за днями й часом; квитанцію можна відкрити для кожного проданого квитка.</p></section></div>`;
}
function formField(field) {
    const common = `id="${esc(field.name)}" name="${esc(field.name)}" ${field.required === false ? "" : "required"} ${field.min !== undefined ? `min="${field.min}"` : ""} ${field.step ? `step="${field.step}"` : ""}`;
    if (field.type === "select") return `<select class="form-select" ${common}>${field.options.map(x => `<option value="${esc(x.value)}" ${String(x.value) === String(field.value) ? "selected" : ""}>${esc(x.label)}</option>`).join("")}</select>`;
    if (field.type === "textarea") return `<textarea class="form-textarea" ${common}>${esc(field.value || "")}</textarea>`;
    return `<input class="form-input" ${common} type="${field.type || "text"}" value="${esc(field.value ?? "")}" placeholder="${esc(field.placeholder || "")}">`;
}
function showForm(title, subtitle, fieldList, submit, options = {}) {
    modalRoot.innerHTML = `<div class="modal-backdrop" data-action="close-modal"><section class="modal" role="dialog" aria-modal="true"><div class="modal-head"><div><h2>${esc(title)}</h2><p>${esc(subtitle)}</p></div><button class="modal-close" data-action="close-modal">×</button></div><form id="edit-form"><div class="form-grid">${fieldList.map(x => `<label class="form-field ${x.full ? "full" : ""}"><span class="form-label">${esc(x.label)}</span>${formField(x)}</label>`).join("")}</div><div class="form-footer"><button type="button" class="button" data-action="close-modal">Скасувати</button><button type="submit" class="button button-primary">${esc(options.label || "Зберегти")}</button></div></form></section></div>`;
    document.getElementById("edit-form").addEventListener("submit", async event => {
        event.preventDefault();
        const button = event.currentTarget.querySelector('[type="submit"]');
        button.disabled = true;
        const payload = Object.fromEntries(new FormData(event.currentTarget));
        try {
            const result = await submit(payload);
            modalRoot.innerHTML = "";
            toast(options.success || "Зміни збережено.");
            if (options.after) await options.after(result); else render();
        } catch (error) { button.disabled = false; toast(error.message, "error"); }
    });
    document.querySelector("#edit-form input, #edit-form select")?.focus();
}
async function movieForm(existing = null) {
    const genreList = await api("/api/genres");
    if (!genreList.length) return toast("Спочатку додайте жанр.", "error");
    const data = [
        { name: "title", label: "Назва фільму", value: existing?.Title || "" },
        { name: "genreId", label: "Жанр", type: "select", value: existing?.GenreID || genreList[0].GenreID, options: genreList.map(x => ({ value: x.GenreID, label: x.GenreName })) },
        { name: "durationMinutes", label: "Тривалість, хв", type: "number", min: 1, value: existing?.DurationMinutes || 100 },
        { name: "ageRating", label: "Віковий рейтинг", type: "select", value: existing?.AgeRating || "12+", options: ["0+", "6+", "12+", "16+", "18+"].map(x => ({ value: x, label: x })) },
        { name: "basePrice", label: "Базова ціна, ₴", type: "number", min: 0, step: "0.01", value: existing?.BasePrice ?? 180 },
        { name: "accent", label: "Колір афіші", type: "color", value: safeColor(existing?.Accent || "#947052") },
        { name: "synopsis", label: "Короткий опис", type: "textarea", full: true, required: false, value: existing?.Synopsis || "" },
    ];
    showForm(existing ? "Редагувати фільм" : "Додати фільм", "Картка у каталозі CinemaHub.", data, body => api(existing ? `/api/movies/${existing.MovieID}` : "/api/movies", { method: existing ? "PUT" : "POST", body: JSON.stringify(body) }), { label: existing ? "Зберегти зміни" : "Додати фільм", success: "Фільмотеку оновлено." });
}
async function sessionForm() {
    const [allMovies, hallList] = await Promise.all([api("/api/movies"), api("/api/halls")]);
    const data = [
        { name: "movieId", label: "Фільм", type: "select", value: allMovies[0].MovieID, options: allMovies.map(x => ({ value: x.MovieID, label: `${x.Title} · ${x.DurationMinutes} хв` })) },
        { name: "hallId", label: "Кінозал", type: "select", value: hallList[0].HallID, options: hallList.map(x => ({ value: x.HallID, label: `${x.HallName} · ${x.Capacity} місць` })) },
        { name: "startTime", label: "Дата й час", type: "datetime-local", value: `${state.day}T17:00` },
        { name: "ticketPrice", label: "Ціна квитка, ₴", type: "number", min: 0, step: "0.01", value: allMovies[0].BasePrice },
    ];
    showForm("Додати сеанс", "Перевіримо перетинання показів у кінозалі.", data, body => api("/api/sessions", { method: "POST", body: JSON.stringify(body) }), { success: "Сеанс додано." });
    document.getElementById("movieId").addEventListener("change", e => { document.getElementById("ticketPrice").value = allMovies.find(x => x.MovieID === Number(e.target.value)).BasePrice; });
}
async function hallForm() {
    showForm("Додати кінозал", "Унікальна назва й місткість.", [{ name: "hallName", label: "Назва кінозалу", placeholder: 'Зал «Зелений»' }, { name: "capacity", label: "Кількість місць", type: "number", min: 1, value: 60 }, { name: "isVip", label: "Тип", type: "select", value: "false", options: [{ value: "false", label: "Звичайний" }, { value: "true", label: "VIP" }] }], body => api("/api/halls", { method: "POST", body: JSON.stringify({ ...body, isVip: body.isVip === "true" }) }), { success: "Зал додано." });
}
async function genreForm() {
    showForm("Додати жанр", "Жанр буде доступний при створенні фільму.", [{ name: "genreName", label: "Назва жанру" }, { name: "description", label: "Опис", type: "textarea", full: true, required: false }], body => api("/api/genres", { method: "POST", body: JSON.stringify(body) }), { success: "Жанр додано." });
}
async function ticketForm(sessionId) {
    const all = await api("/api/sessions");
    const upcoming = all.filter(x => new Date(x.StartTime.replace(" ", "T")) >= new Date());
    const choices = upcoming.length ? upcoming : all;
    if (!choices.length) return toast("Спочатку додайте сеанс.", "error");
    const selected = choices.find(x => x.SessionID === Number(sessionId)) || choices[0];
    const data = [
        { name: "sessionId", label: "Сеанс", type: "select", value: selected.SessionID, options: choices.map(x => ({ value: x.SessionID, label: `${fmtDate(x.StartTime)} · ${fmtTime(x.StartTime)} · ${x.Title}` })) },
        { name: "customerName", label: "Ім’я покупця", placeholder: "Ім’я та прізвище" },
        { name: "customerPhone", label: "Телефон", type: "tel", required: false },
        { name: "seatNumber", label: "Місце", type: "number", min: 1, max: selected.Capacity, value: selected.Capacity - selected.AvailableSeats + 1 },
    ];
    showForm("Продати квиток", "Місце резервується за покупцем.", data, body => api("/api/tickets", { method: "POST", body: JSON.stringify(body) }), { label: "Продати й відкрити квиток", success: "Квиток продано.", after: x => previewTicket(x.TicketID) });
    document.getElementById("sessionId").addEventListener("change", e => { const x = choices.find(s => s.SessionID === Number(e.target.value)); document.getElementById("seatNumber").max = x.Capacity; document.getElementById("seatNumber").value = x.Capacity - x.AvailableSeats + 1; });
}
async function previewTicket(id) {
    const x = await api(`/api/ticket?id=${id}`);
    modalRoot.innerHTML = `<div class="modal-backdrop" data-action="close-modal"><section class="modal" role="dialog" aria-modal="true"><div class="modal-head"><div><h2>Квиток #${String(x.TicketID).padStart(5, "0")}</h2><p>Електронна квитанція CinemaHub</p></div><button class="modal-close" data-action="close-modal">×</button></div><div class="ticket-print"><div class="ticket-brand">CINEMAHUB / КВИТКОВА КАСА</div><h2>${esc(x.Title)}</h2><p class="ticket-sub">${esc(x.GenreName)} · ${x.DurationMinutes} хв · ${esc(x.AgeRating)}</p><div class="ticket-rule"></div>${[["Дата й час", dateTime(x.StartTime)], ["Кінозал", x.HallName], ["Місце", x.SeatNumber], ["Гість", x.CustomerName], ["Вартість", money(x.TicketPrice)], ["Статус", Number(x.IsPaid) ? "ОПЛАЧЕНО" : "БРОНЬ"]].map(([k, v]) => `<div class="ticket-row"><span>${k}</span><strong>${esc(v)}</strong></div>`).join("")}<div class="ticket-rule"></div><div class="ticket-code">CH · ${String(x.TicketID).padStart(8, "0")}</div><p class="ticket-sub">Пред’явіть квиток контролеру.</p></div><div class="ticket-print-actions"><button class="button" data-action="close-modal">Закрити</button><button class="button button-primary" data-action="print-now">Друкувати квиток</button></div></section></div>`;
}
function downloadCsv(name, rows) {
    if (!rows.length) return toast("Немає даних для експорту.", "error");
    const keys = Object.keys(rows[0]);
    const csv = "\uFEFF" + [keys, ...rows.map(x => keys.map(k => x[k]))].map(row => row.map(v => `"${String(v ?? "").replace(/"/g, '""')}"`).join(";")).join("\r\n");
    const url = URL.createObjectURL(new Blob([csv], { type: "text/csv;charset=utf-8" }));
    const a = document.createElement("a"); a.href = url; a.download = name; a.click(); URL.revokeObjectURL(url);
}
async function action(name, target) {
    const id = target.dataset.id;
    if (name === "new-movie") await movieForm();
    if (name === "edit-movie") await movieForm((await api("/api/movies")).find(x => x.MovieID === Number(id)));
    if (name === "new-session") await sessionForm();
    if (name === "new-ticket") await ticketForm(target.dataset.sessionId);
    if (name === "new-hall") await hallForm();
    if (name === "new-genre") await genreForm();
    if (name === "close-modal") modalRoot.innerHTML = "";
    if (name === "delete-movie") await remove(`/api/movies/${id}`, "Видалити фільм і всі його сеанси з квитками?");
    if (name === "delete-session") await remove(`/api/sessions/${id}`, "Видалити сеанс і квитки?");
    if (name === "delete-ticket") await remove(`/api/tickets/${id}`, "Видалити квиток?");
    if (name === "delete-hall") await remove(`/api/halls/${id}`, "Видалити зал? Спочатку видаліть його сеанси.");
    if (name === "delete-genre") await remove(`/api/genres/${id}`, "Видалити жанр? Переконайтеся, що його не використовують фільми.");
    if (name === "mark-paid") { await api(`/api/tickets/${id}`, { method: "PATCH", body: JSON.stringify({ isPaid: 1 }) }); toast("Оплату підтверджено."); render(); }
    if (name === "print-ticket") await previewTicket(id);
    if (name === "print-now" || name === "print-report") window.print();
    if (name === "copy-sql") { await navigator.clipboard.writeText(presets[state.query].sql || customSql()); toast("SQL скопійовано."); }
    if (name === "run-query") {
        try {
            const payload = { kind: presets[state.query].sqlKind };
            if (state.query === "custom") {
                if (!state.queryFields.length) throw Error("Виберіть щонайменше одне поле.");
                payload.fields = state.queryFields; payload.filters = state.filters; payload.sort = state.queryFields[0];
            }
            if (state.query === "client") { payload.client = document.getElementById("client-name").value; payload.start = document.getElementById("client-start").value; payload.end = document.getElementById("client-end").value; }
            state.results = await api("/api/query", { method: "POST", body: JSON.stringify(payload) });
            render(); toast(`Запит виконано: ${state.results.rows.length} рядків.`);
        } catch (error) { toast(error.message, "error"); }
    }
    if (name === "add-filter") { if (state.filters.length >= 8) return toast("Не більше восьми умов.", "error"); state.filters.push({ field: "s.StartTime", operator: ">=", value: "" }); render(); }
    if (name === "remove-filter") { state.filters.splice(Number(target.dataset.index), 1); render(); }
    if (name === "set-date") { state.day = target.dataset.date; render(); }
    if (name === "export-report") { const rows = state.report === "halls" ? window.cinemaReport.halls : state.report === "matrix" ? window.cinemaReport.timeSlots : window.cinemaReport.revenue; downloadCsv(`cinemahub-${state.report}-${state.start}-${state.end}.csv`, rows); }
}
async function remove(url, message) {
    if (!confirm(message)) return;
    await api(url, { method: "DELETE" }); toast("Запис видалено."); render();
}
document.addEventListener("click", async event => {
    const button = event.target.closest("[data-action]");
    if (button) {
        if (button.dataset.action === "close-modal") { if (event.target.closest(".modal") === null || button.classList.contains("modal-close")) modalRoot.innerHTML = ""; return; }
        try { await action(button.dataset.action, button); } catch (error) { toast(error.message, "error"); }
        return;
    }
    const preset = event.target.closest("[data-preset]");
    if (preset) { state.query = preset.dataset.preset; state.results = null; if (state.query === "schedule") state.filters = [{ field: "h.IsVIP", operator: "=", value: "0" }]; if (state.query === "custom") state.queryFields = ["m.Title", "g.GenreName", "s.StartTime", "s.TicketPrice"]; render(); return; }
    const reportTab = event.target.closest("[data-report]");
    if (reportTab) { state.report = reportTab.dataset.report; render(); return; }
    const navigate = event.target.closest("[data-navigate]");
    if (navigate) { location.hash = navigate.dataset.navigate; return; }
    const link = event.target.closest("[data-view]");
    if (link) { event.preventDefault(); location.hash = link.dataset.view; }
});
document.addEventListener("change", event => {
    const column = event.target.closest("[data-column]");
    if (column) { state.queryFields = [...document.querySelectorAll("[data-column]:checked")].map(x => x.dataset.column); const sql = document.getElementById("sql-preview"); if (sql) sql.textContent = customSql(); }
});
document.addEventListener("input", event => {
    const filter = event.target.closest("[data-key]");
    if (filter) { state.filters[Number(filter.dataset.filterIndex)][filter.dataset.key] = filter.value; const sql = document.getElementById("sql-preview"); if (sql) sql.textContent = customSql(); }
});
document.getElementById("mobile-menu").addEventListener("click", () => document.getElementById("sidebar").classList.toggle("open"));
document.getElementById("quick-refresh").addEventListener("click", render);
window.addEventListener("hashchange", render);
render();
