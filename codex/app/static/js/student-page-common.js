(function () {
  const STUDENT_API_BASE = "/api/student";

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

  function escapeHtml(value) {
    return String(value ?? "")
      .replaceAll("&", "&amp;")
      .replaceAll("<", "&lt;")
      .replaceAll(">", "&gt;")
      .replaceAll('"', "&quot;")
      .replaceAll("'", "&#39;");
  }

  async function request(path, options = {}) {
    let response;
    try {
      response = await fetch(`${STUDENT_API_BASE}${path}`, {
        ...options,
        headers: {
          ...authHeaders(!(options.body instanceof FormData)),
          ...(options.headers || {}),
        },
      });
    } catch {
      throw new Error("网络异常，请检查服务是否可用");
    }

    const text = await response.text();
    const payload = parseJson(text);

    if (!response.ok) {
      if (response.status === 401) {
        window.clearSession();
        window.location.replace("/auth/login");
        throw new Error("登录已过期，请重新登录");
      }
      throw new Error(payload?.message || payload?.detail?.message || payload?.detail || window.parseApiError(response.status));
    }

    if (payload && typeof payload === "object" && Object.prototype.hasOwnProperty.call(payload, "code")) {
      return payload.data;
    }
    return payload;
  }

  function fmtDate(value) {
    if (!value) return "-";
    const date = new Date(value);
    return Number.isNaN(date.getTime()) ? "-" : date.toLocaleString("zh-CN", { hour12: false });
  }

  function showPage() {
    document.body.classList.remove("page-hidden");
    document.getElementById("authChecking")?.remove();
  }

  function bindCommonActions() {
    document.querySelectorAll("[data-student-refresh]").forEach((node) => {
      node.addEventListener("click", () => window.location.reload());
    });
    document.querySelectorAll("[data-student-logout]").forEach((node) => {
      node.addEventListener("click", () => {
        window.clearSession();
        window.location.replace("/auth/login");
      });
    });
  }

  function highlightNav() {
    const path = window.location.pathname;
    document.querySelectorAll("[data-student-nav]").forEach((node) => {
      const href = node.getAttribute("href") || "";
      node.classList.toggle("active", href === path);
    });
  }

  function renderCurrentUser() {
    const user = window.getUser();
    document.querySelectorAll("[data-student-user]").forEach((node) => {
      if (!user) {
        node.textContent = "-";
        return;
      }
      const name = user.nickname || user.name || "学生";
      node.textContent = `${name} #${user.id}`;
    });
  }

  function initPage() {
    window.applyI18n(document);
    if (!window.ensureStudentPageGuard()) return false;
    bindCommonActions();
    highlightNav();
    renderCurrentUser();
    showPage();
    return true;
  }

  window.StudentPageCommon = {
    request,
    escapeHtml,
    fmtDate,
    initPage,
  };
})();
