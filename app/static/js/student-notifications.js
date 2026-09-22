(function () {
  const C = window.StudentPageCommon;
  if (!C) return;
  if (!C.initPage()) return;

  const el = {
    notificationMeta: document.getElementById("notificationMeta"),
    notificationList: document.getElementById("notificationList"),
    refreshNotificationsBtn: document.getElementById("refreshNotificationsBtn"),
    readAllNotificationsBtn: document.getElementById("readAllNotificationsBtn"),
    pageFeedback: document.getElementById("pageFeedback"),
  };

  const state = {
    notifications: [],
    total: 0,
    unreadCount: 0,
  };

  function setFeedback(message) {
    if (!el.pageFeedback) return;
    el.pageFeedback.textContent = message;
  }

  function notificationTypeText(type) {
    const mapping = {
      booking: "预约通知",
      notice: "公告通知",
      violation: "违规提醒",
      system: "系统通知",
    };
    return mapping[type] || "系统通知";
  }

  function emailStatusText(status) {
    const mapping = {
      pending: "待发送",
      sent: "已发送",
      failed: "发送失败",
      skipped: "未发送",
    };
    return mapping[status] || "未发送";
  }

  function relatedAction(item) {
    if (item.notification_type === "notice" && item.related_id) {
      return `<a class="row-action" href="/student/notices">查看公告</a>`;
    }
    return "";
  }

  function renderNotifications() {
    if (!state.total) {
      el.notificationMeta.textContent = "暂无通知";
      el.notificationList.innerHTML = '<div class="notification-empty">暂无通知</div>';
      return;
    }

    el.notificationMeta.textContent = state.unreadCount > 0
      ? `未读 ${state.unreadCount} 条，共 ${state.total} 条通知`
      : `共 ${state.total} 条通知`;

    el.notificationList.innerHTML = state.notifications.map((item) => {
      const unreadClass = item.is_read ? "" : " unread";
      const readText = item.is_read ? "已读" : "未读";
      const readButton = item.is_read
        ? ""
        : `<button class="row-action" data-action="read" data-id="${item.id}">标记已读</button>`;

      return `
        <article class="notification-item${unreadClass}">
          <div class="notification-head">
            <h3 class="notification-title">${C.escapeHtml(item.title || "-")}</h3>
            <div class="notification-tags">
              <span class="notification-tag">${notificationTypeText(item.notification_type)}</span>
              <span class="notification-tag${item.is_read ? "" : " unread"}">${readText}</span>
              <span class="notification-tag ${item.email_status || "skipped"}">邮箱推送：${emailStatusText(item.email_status)}</span>
            </div>
          </div>
          <p class="notification-body">${C.escapeHtml(item.content || "")}</p>
          <div class="notification-foot">
            <span class="notification-time">${C.escapeHtml(C.fmtDate(item.created_at))}</span>
            <div class="hero-actions">
              ${relatedAction(item)}
              ${readButton}
            </div>
          </div>
          ${item.email_error ? `<div class="notification-error">${C.escapeHtml(item.email_error)}</div>` : ""}
        </article>
      `;
    }).join("");
  }

  async function loadNotifications() {
    const data = await C.request("/notifications?limit=50");
    state.notifications = Array.isArray(data?.items) ? data.items : [];
    state.total = Number(data?.total || 0);
    state.unreadCount = Number(data?.unread_count || 0);
    renderNotifications();
  }

  async function markRead(notificationId) {
    await C.request(`/notifications/${notificationId}/read`, { method: "POST" });
    setFeedback("通知已标记为已读");
    await loadNotifications();
  }

  async function markAllRead() {
    await C.request("/notifications/read-all", { method: "POST" });
    setFeedback("全部通知已标记为已读");
    await loadNotifications();
  }

  (async () => {
    setFeedback("暂无操作结果");
    await loadNotifications();
    el.refreshNotificationsBtn?.addEventListener("click", () => loadNotifications().catch((error) => {
      setFeedback(error.message);
    }));
    el.readAllNotificationsBtn?.addEventListener("click", () => markAllRead().catch((error) => {
      setFeedback(error.message);
    }));
    el.notificationList?.addEventListener("click", (event) => {
      const target = event.target instanceof HTMLElement ? event.target.closest("[data-action='read']") : null;
      if (!target) return;
      const notificationId = Number(target.getAttribute("data-id") || 0);
      if (!notificationId) return;
      markRead(notificationId).catch((error) => setFeedback(error.message));
    });
  })().catch((error) => {
    setFeedback(error.message);
  });
})();
