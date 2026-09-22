(function () {
  const C = window.StudentPageCommon;
  if (!C) return;
  if (!C.initPage()) return;

  const el = {
    noticeStoreFilter: document.getElementById("noticeStoreFilter"),
    loadNoticeListBtn: document.getElementById("loadNoticeListBtn"),
    noticeListMeta: document.getElementById("noticeListMeta"),
    noticeList: document.getElementById("noticeList"),
    noticeDetailTitle: document.getElementById("noticeDetailTitle"),
    noticeDetailStore: document.getElementById("noticeDetailStore"),
    noticeDetailMeta: document.getElementById("noticeDetailMeta"),
    noticeDetailBody: document.getElementById("noticeDetailBody"),
  };

  const state = {
    stores: [],
    notices: [],
    selectedNoticeId: null,
  };

  function fillStoreOptions() {
    const options = ['<option value="">全部门店</option>'].concat(
      state.stores.map((store) => `<option value="${store.id}">${C.escapeHtml(store.name)}</option>`),
    );
    el.noticeStoreFilter.innerHTML = options.join("");
  }

  function storeName(storeId) {
    if (!storeId) return "全校公告";
    const store = state.stores.find((item) => Number(item.id) === Number(storeId));
    return store?.name || `门店#${storeId}`;
  }

  function renderDetail(notice) {
    if (!notice) {
      el.noticeDetailTitle.textContent = "请选择公告";
      el.noticeDetailStore.textContent = "-";
      el.noticeDetailMeta.innerHTML = "";
      el.noticeDetailBody.className = "detail-empty";
      el.noticeDetailBody.textContent = "请在左侧选择一条已发布公告查看详情。";
      return;
    }

    el.noticeDetailTitle.textContent = notice.title || "-";
    el.noticeDetailStore.textContent = storeName(notice.store_id);
    el.noticeDetailMeta.innerHTML = `
      <span>发布时间：${C.escapeHtml(C.fmtDate(notice.published_at))}</span>
      <span>所属门店：${C.escapeHtml(storeName(notice.store_id))}</span>
    `;
    el.noticeDetailBody.className = "notice-detail-body";
    el.noticeDetailBody.textContent = notice.content || "";
  }

  function renderNotices() {
    if (!state.notices.length) {
      el.noticeListMeta.textContent = "暂无公告";
      el.noticeList.innerHTML = '<div class="notification-empty">暂无公告</div>';
      renderDetail(null);
      return;
    }

    el.noticeListMeta.textContent = `当前共 ${state.notices.length} 条已发布公告`;
    el.noticeList.innerHTML = state.notices.map((notice) => {
      const activeClass = Number(notice.id) === Number(state.selectedNoticeId) ? " active" : "";
      return `
        <article class="notice-item${activeClass}" data-notice-id="${notice.id}">
          <h3>${C.escapeHtml(notice.title || "-")}</h3>
          <p>${C.escapeHtml((notice.content || "").slice(0, 80) || "暂无内容")}</p>
          <div class="notice-meta">
            <span>${C.escapeHtml(storeName(notice.store_id))}</span>
            <span>${C.escapeHtml(C.fmtDate(notice.published_at))}</span>
          </div>
        </article>
      `;
    }).join("");
  }

  async function loadStores() {
    const stores = await C.request("/stores");
    state.stores = Array.isArray(stores) ? stores : [];
    fillStoreOptions();
  }

  async function loadNoticeDetail(noticeId) {
    const notice = await C.request(`/notices/${noticeId}`);
    state.selectedNoticeId = notice.id;
    renderNotices();
    renderDetail(notice);
  }

  async function loadNotices() {
    const query = new URLSearchParams();
    if (el.noticeStoreFilter.value) {
      query.set("store_id", el.noticeStoreFilter.value);
    }
    query.set("limit", "50");
    const notices = await C.request(`/notices?${query.toString()}`);
    state.notices = Array.isArray(notices) ? notices : [];
    if (!state.notices.length) {
      state.selectedNoticeId = null;
      renderNotices();
      return;
    }

    const selectedExists = state.notices.some((item) => Number(item.id) === Number(state.selectedNoticeId));
    state.selectedNoticeId = selectedExists ? state.selectedNoticeId : state.notices[0].id;
    renderNotices();
    await loadNoticeDetail(state.selectedNoticeId);
  }

  (async () => {
    await loadStores();
    await loadNotices();
    el.loadNoticeListBtn?.addEventListener("click", () => loadNotices().catch((error) => {
      window.alert(error.message);
    }));
    el.noticeStoreFilter?.addEventListener("change", () => loadNotices().catch((error) => {
      window.alert(error.message);
    }));
    el.noticeList?.addEventListener("click", (event) => {
      const target = event.target instanceof HTMLElement ? event.target.closest("[data-notice-id]") : null;
      if (!target) return;
      const noticeId = Number(target.getAttribute("data-notice-id") || 0);
      if (!noticeId) return;
      loadNoticeDetail(noticeId).catch((error) => window.alert(error.message));
    });
  })().catch((error) => {
    window.alert(error.message);
  });
})();
