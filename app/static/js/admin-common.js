(function () {
  const ADMIN_API_BASE = "/api/admin";
  const state = {
    stores: null,
    charts: {},
  };

  function parseJson(text) {
    try {
      return text ? JSON.parse(text) : null;
    } catch {
      return null;
    }
  }

  function authHeaders(withJson = true) {
    const headers = {
      Authorization: `Bearer ${window.getToken()}`,
    };
    if (withJson) {
      headers["Content-Type"] = "application/json";
    }
    return headers;
  }

  async function request(path, options = {}) {
    let response;
    try {
      response = await fetch(`${ADMIN_API_BASE}${path}`, {
        ...options,
        headers: {
          ...authHeaders(!(options.body instanceof FormData)),
          ...(options.headers || {}),
        },
      });
    } catch {
      throw new Error(window.t("errors.network"));
    }

    const text = await response.text();
    const payload = parseJson(text);

    if (!response.ok) {
      if (response.status === 401) {
        window.clearSession();
        window.location.replace("/auth/login");
        throw new Error(window.t("errors.loginExpired"));
      }
      throw new Error(payload?.message || payload?.detail?.message || payload?.detail || window.parseApiError(response.status));
    }

    if (payload && typeof payload === "object" && Object.prototype.hasOwnProperty.call(payload, "code")) {
      return payload.data;
    }
    return payload;
  }

  function escapeHtml(value) {
    return String(value ?? "")
      .replaceAll("&", "&amp;")
      .replaceAll("<", "&lt;")
      .replaceAll(">", "&gt;")
      .replaceAll('"', "&quot;")
      .replaceAll("'", "&#39;");
  }

  function fmtDate(value) {
    if (!value) return "-";
    const date = new Date(value);
    return Number.isNaN(date.getTime()) ? "-" : date.toLocaleString("zh-CN", { hour12: false });
  }

  function fmtMoney(value) {
    return `￥${Number(value || 0).toFixed(2)}`;
  }

  function today() {
    const now = new Date();
    const y = now.getFullYear();
    const m = String(now.getMonth() + 1).padStart(2, "0");
    const d = String(now.getDate()).padStart(2, "0");
    return `${y}-${m}-${d}`;
  }

  function toIso(value) {
    if (!value) return null;
    const date = new Date(value);
    return Number.isNaN(date.getTime()) ? null : date.toISOString();
  }

  function setFeedback(message, type = "info") {
    const node = document.getElementById("pageFeedback");
    if (!node) return;
    node.textContent = typeof message === "string" ? message : JSON.stringify(message, null, 2);
    node.className = `result result-${type}`;
  }

  function setSuccess(message) {
    setFeedback(message, "success");
  }

  function setError(error) {
    setFeedback(error?.message || window.t("errors.requestFailed"), "error");
  }

  function statusTag(text, cls) {
    return `<span class="status-tag status-${cls}">${escapeHtml(text)}</span>`;
  }

  function bookingStatusTag(status) {
    const mapping = {
      booked: ["normal", window.statusText("booked")],
      confirmed: ["normal", window.statusText("confirmed")],
      checked_in: ["active", window.statusText("checked_in")],
      completed: ["paid", window.statusText("completed")],
      cancelled: ["cancelled", window.statusText("cancelled")],
      expired: ["danger", window.statusText("expired")],
    };
    const [cls, label] = mapping[status] || ["normal", status || "-"];
    return statusTag(label, cls);
  }

  function noticeStatusTag(status) {
    const mapping = {
      draft: ["normal", "草稿"],
      published: ["active", "已发布"],
      offline: ["cancelled", "已下线"],
    };
    const [cls, label] = mapping[status] || ["normal", status || "-"];
    return statusTag(label, cls);
  }

  function userStatusText(status) {
    if (Number(status) === 1) return "正常";
    if (Number(status) === 0) return "冻结";
    return "已删除";
  }

  function userStatusTag(status) {
    if (Number(status) === 1) return statusTag("正常", "active");
    if (Number(status) === 0) return statusTag("冻结", "cancelled");
    return statusTag("已删除", "deleted");
  }

  function blacklistTag(isBlacklisted, endAt = null) {
    if (!isBlacklisted) return statusTag("正常", "normal");
    const suffix = endAt ? ` 至 ${fmtDate(endAt)}` : "";
    return statusTag(`已在黑名单${suffix}`, "blacklisted");
  }

  function currentUser() {
    return window.getUser();
  }

  function isSuperAdmin() {
    return currentUser()?.role === "super_admin";
  }

  function canEditStore() {
    return ["admin", "super_admin"].includes(currentUser()?.role || "");
  }

  function highlightNav() {
    const page = document.body.dataset.page || "";
    document.querySelectorAll("[data-admin-nav]").forEach((node) => {
      node.classList.toggle("active", node.getAttribute("data-admin-nav") === page);
    });
  }

  function renderCurrentUser() {
    const user = currentUser();
    const userNode = document.getElementById("currentUserText");
    const roleNode = document.getElementById("currentRoleText");
    if (userNode) userNode.textContent = user ? `${user.nickname || user.name || "-"} #${user.id}` : "-";
    if (roleNode) roleNode.textContent = user ? window.roleText(user.role) : "-";
  }

  function bindShell() {
    const logoutBtn = document.getElementById("logoutBtn");
    const refreshBtn = document.getElementById("refreshPageBtn");
    logoutBtn?.addEventListener("click", () => {
      window.clearSession();
      window.location.replace("/auth/login");
    });
    refreshBtn?.addEventListener("click", () => window.location.reload());
  }

  function showPage() {
    document.body.classList.remove("page-hidden");
    document.getElementById("authChecking")?.remove();
  }

  async function loadStores(force = false) {
    if (!force && Array.isArray(state.stores)) {
      return state.stores;
    }
    const data = await request("/stores");
    state.stores = Array.isArray(data) ? data : [];
    return state.stores;
  }

  function fillStoreSelect(selectNode, stores, options = {}) {
    if (!selectNode) return;
    const includeAll = options.includeAll ?? true;
    const allLabel = options.allLabel ?? "全部门店";
    const selectedValue = options.selectedValue;
    const html = [];
    if (includeAll) {
      html.push(`<option value="">${escapeHtml(allLabel)}</option>`);
    }
    html.push(...stores.map((store) => `<option value="${store.id}">${escapeHtml(store.name)}</option>`));
    selectNode.innerHTML = html.join("");
    if (selectedValue !== null && selectedValue !== undefined && selectedValue !== "") {
      selectNode.value = String(selectedValue);
    } else if (!includeAll && Array.isArray(stores) && stores.length) {
      selectNode.value = String(stores[0].id);
    }
    if (!selectNode.value && !includeAll && Array.isArray(stores) && stores.length) {
      selectNode.value = String(stores[0].id);
    }
  }

  function selectedStoreId(selectNode) {
    const value = Number(selectNode?.value || 0);
    return Number.isFinite(value) && value > 0 ? value : null;
  }

  function ensureChart(key, node) {
    if (!node || typeof window.echarts === "undefined") return null;
    if (!state.charts[key]) {
      state.charts[key] = window.echarts.init(node);
    }
    return state.charts[key];
  }

  function emptyChart(chart, text = "暂无统计数据") {
    if (!chart) return;
    chart.setOption({
      xAxis: { show: false, type: "category", data: [] },
      yAxis: { show: false, type: "value" },
      series: [],
      graphic: {
        type: "text",
        left: "center",
        top: "middle",
        style: { text, fill: "#7d4a37", fontSize: 14 },
      },
    }, true);
  }

  function initPage() {
    window.applyI18n(document);
    if (!window.ensureAdminPageGuard()) return false;
    highlightNav();
    renderCurrentUser();
    bindShell();
    showPage();
    return true;
  }

  window.AdminCommon = {
    state,
    request,
    escapeHtml,
    fmtDate,
    fmtMoney,
    toIso,
    today,
    setFeedback,
    setSuccess,
    setError,
    statusTag,
    bookingStatusTag,
    noticeStatusTag,
    userStatusText,
    userStatusTag,
    blacklistTag,
    currentUser,
    isSuperAdmin,
    canEditStore,
    highlightNav,
    renderCurrentUser,
    loadStores,
    fillStoreSelect,
    selectedStoreId,
    ensureChart,
    emptyChart,
    initPage,
  };
})();
