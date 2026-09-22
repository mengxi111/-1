(function () {
  const C = window.AdminCommon;
  if (!C) return;
  if (!C.initPage()) return;

  const el = {
    noticeFilterStoreId: document.getElementById("noticeFilterStoreId"),
    noticeFilterStatus: document.getElementById("noticeFilterStatus"),
    searchNoticesBtn: document.getElementById("searchNoticesBtn"),
    resetNoticesBtn: document.getElementById("resetNoticesBtn"),
    loadNoticesBtn: document.getElementById("loadNoticesBtn"),
    noticeListMeta: document.getElementById("noticeListMeta"),
    noticeTableBody: document.getElementById("noticeTableBody"),
    noticeEditorTitle: document.getElementById("noticeEditorTitle"),
    noticeEditorMode: document.getElementById("noticeEditorMode"),
    noticeStoreId: document.getElementById("noticeStoreId"),
    noticeTitleInput: document.getElementById("noticeTitleInput"),
    noticeStatusSelect: document.getElementById("noticeStatusSelect"),
    noticeContentInput: document.getElementById("noticeContentInput"),
    saveNoticeBtn: document.getElementById("saveNoticeBtn"),
    resetNoticeFormBtn: document.getElementById("resetNoticeFormBtn"),
    noticeDetailDialog: document.getElementById("noticeDetailDialog"),
    closeNoticeDetailBtn: document.getElementById("closeNoticeDetailBtn"),
    noticeDetailContent: document.getElementById("noticeDetailContent"),
    editNoticeFromDetailBtn: document.getElementById("editNoticeFromDetailBtn"),
    publishNoticeFromDetailBtn: document.getElementById("publishNoticeFromDetailBtn"),
    offlineNoticeFromDetailBtn: document.getElementById("offlineNoticeFromDetailBtn"),
    deleteNoticeFromDetailBtn: document.getElementById("deleteNoticeFromDetailBtn"),
  };

  const state = {
    notices: [],
    editingNoticeId: null,
    detailNoticeId: null,
  };

  function storeName(storeId) {
    if (!storeId) return "全校公告";
    const store = (C.state.stores || []).find((item) => Number(item.id) === Number(storeId));
    return store?.name || `门店#${storeId}`;
  }

  function detailDialog() {
    return el.noticeDetailDialog;
  }

  function closeDetailDialog() {
    detailDialog()?.close();
  }

  function openDetailDialog() {
    if (detailDialog() && !detailDialog().open) {
      detailDialog().showModal();
    }
  }

  function resetForm() {
    state.editingNoticeId = null;
    el.noticeEditorTitle.textContent = "新建公告";
    el.noticeEditorMode.textContent = "未选择公告时默认为新建";
    el.noticeStoreId.value = "";
    el.noticeTitleInput.value = "";
    el.noticeStatusSelect.value = "draft";
    el.noticeContentInput.value = "";
  }

  function fillStoreSelects() {
    C.fillStoreSelect(el.noticeFilterStoreId, C.state.stores || [], {
      includeAll: true,
      allLabel: "全部门店",
      selectedValue: el.noticeFilterStoreId.value || "",
    });

    const editorOptions = [`<option value="">全校公告</option>`].concat(
      (C.state.stores || []).map((store) => `<option value="${store.id}">${C.escapeHtml(store.name)}</option>`),
    );
    el.noticeStoreId.innerHTML = editorOptions.join("");
  }

  function noticeQuery() {
    const query = new URLSearchParams();
    const storeId = C.selectedStoreId(el.noticeFilterStoreId);
    if (storeId) query.set("store_id", String(storeId));
    if (el.noticeFilterStatus.value) query.set("status", el.noticeFilterStatus.value);
    query.set("limit", "100");
    return query.toString();
  }

  function formPayload() {
    return {
      store_id: el.noticeStoreId.value ? Number(el.noticeStoreId.value) : null,
      title: el.noticeTitleInput.value.trim(),
      content: el.noticeContentInput.value.trim(),
      status: el.noticeStatusSelect.value,
    };
  }

  function validateForm(payload) {
    if (!payload.title) throw new Error("请输入公告标题");
    if (!payload.content) throw new Error("请输入公告内容");
  }

  function renderNotices() {
    const items = Array.isArray(state.notices) ? state.notices : [];
    el.noticeListMeta.textContent = items.length ? `当前共 ${items.length} 条公告` : "暂无公告数据";
    if (!items.length) {
      el.noticeTableBody.innerHTML = '<tr><td colspan="6">暂无公告数据</td></tr>';
      return;
    }

    el.noticeTableBody.innerHTML = items.map((item) => {
      const actions = [
        `<button type="button" class="btn btn-inline" data-action="detail" data-id="${item.id}">查看详情</button>`,
        `<button type="button" class="btn btn-inline" data-action="edit" data-id="${item.id}">编辑</button>`,
      ];
      if (item.status !== "published") {
        actions.push(`<button type="button" class="btn btn-inline" data-action="publish" data-id="${item.id}">发布</button>`);
      }
      if (item.status === "published") {
        actions.push(`<button type="button" class="btn btn-inline" data-action="offline" data-id="${item.id}">下线</button>`);
      }
      actions.push(`<button type="button" class="btn btn-inline" data-action="delete" data-id="${item.id}">删除</button>`);

      return `
        <tr>
          <td>${item.id}</td>
          <td>${C.escapeHtml(storeName(item.store_id))}</td>
          <td>${C.escapeHtml(item.title || "-")}</td>
          <td>${C.noticeStatusTag(item.status)}</td>
          <td>${C.escapeHtml(C.fmtDate(item.published_at))}</td>
          <td class="table-actions">${actions.join("")}</td>
        </tr>
      `;
    }).join("");
  }

  function fillFormByNotice(notice) {
    state.editingNoticeId = notice.id;
    el.noticeEditorTitle.textContent = "编辑公告";
    el.noticeEditorMode.textContent = `当前编辑：公告#${notice.id}`;
    el.noticeStoreId.value = notice.store_id ? String(notice.store_id) : "";
    el.noticeTitleInput.value = notice.title || "";
    el.noticeStatusSelect.value = notice.status || "draft";
    el.noticeContentInput.value = notice.content || "";
    el.noticeTitleInput.focus();
    el.noticeTitleInput.scrollIntoView({ behavior: "smooth", block: "center" });
  }

  function renderDetail(notice) {
    state.detailNoticeId = notice.id;
    el.noticeDetailContent.innerHTML = `
      <div><span>公告编号</span><strong>${notice.id}</strong></div>
      <div><span>所属门店</span><strong>${C.escapeHtml(storeName(notice.store_id))}</strong></div>
      <div><span>公告标题</span><strong>${C.escapeHtml(notice.title || "-")}</strong></div>
      <div><span>公告状态</span><strong>${C.escapeHtml(notice.status || "-")}</strong></div>
      <div><span>发布时间</span><strong>${C.escapeHtml(C.fmtDate(notice.published_at))}</strong></div>
      <div><span>创建人</span><strong>${C.escapeHtml(notice.created_by_name || "-")}</strong></div>
      <div><span>创建时间</span><strong>${C.escapeHtml(C.fmtDate(notice.created_at))}</strong></div>
      <div><span>更新时间</span><strong>${C.escapeHtml(C.fmtDate(notice.updated_at))}</strong></div>
      <div class="dialog-full"><span>公告内容</span><pre class="dialog-pre">${C.escapeHtml(notice.content || "-")}</pre></div>
    `;
    openDetailDialog();
  }

  async function loadNotices() {
    const query = noticeQuery();
    const items = await C.request(`/notices${query ? `?${query}` : ""}`);
    state.notices = Array.isArray(items) ? items : [];
    renderNotices();
  }

  async function loadNoticeDetail(noticeId) {
    const notice = await C.request(`/notices/${noticeId}`);
    renderDetail(notice);
    return notice;
  }

  async function saveNotice() {
    const payload = formPayload();
    validateForm(payload);
    if (state.editingNoticeId) {
      await C.request(`/notices/${state.editingNoticeId}`, {
        method: "PUT",
        body: JSON.stringify(payload),
      });
      C.setSuccess("公告更新成功");
    } else {
      await C.request("/notices", {
        method: "POST",
        body: JSON.stringify(payload),
      });
      C.setSuccess(payload.status === "published" ? "公告创建并发布成功" : "公告创建成功");
    }
    resetForm();
    await loadNotices();
  }

  async function publishNotice(noticeId) {
    await C.request(`/notices/${noticeId}/publish`, { method: "POST" });
    C.setSuccess("公告已发布");
    await loadNotices();
    if (state.detailNoticeId === noticeId) {
      await loadNoticeDetail(noticeId);
    }
  }

  async function offlineNotice(noticeId) {
    await C.request(`/notices/${noticeId}/offline`, { method: "POST" });
    C.setSuccess("公告已下线");
    await loadNotices();
    if (state.detailNoticeId === noticeId) {
      await loadNoticeDetail(noticeId);
    }
  }

  async function deleteNotice(noticeId) {
    await C.request(`/notices/${noticeId}`, { method: "DELETE" });
    C.setSuccess("公告删除成功");
    if (state.detailNoticeId === noticeId) {
      closeDetailDialog();
      state.detailNoticeId = null;
    }
    if (state.editingNoticeId === noticeId) {
      resetForm();
    }
    await loadNotices();
  }

  async function onAction(action, noticeId) {
    const local = state.notices.find((item) => Number(item.id) === Number(noticeId));
    if (action === "detail") {
      await loadNoticeDetail(noticeId);
      return;
    }
    if (action === "edit") {
      const notice = local || await C.request(`/notices/${noticeId}`);
      fillFormByNotice(notice);
      return;
    }
    if (action === "publish") {
      if (!window.confirm("确认发布该公告吗？发布后学生端可见，并会生成公告通知。")) return;
      await publishNotice(noticeId);
      return;
    }
    if (action === "offline") {
      if (!window.confirm("确认下线该公告吗？下线后学生端将不再显示。")) return;
      await offlineNotice(noticeId);
      return;
    }
    if (action === "delete") {
      if (!window.confirm("确认删除该公告吗？删除后无法恢复。")) return;
      await deleteNotice(noticeId);
    }
  }

  (async () => {
    await C.loadStores(true);
    fillStoreSelects();
    resetForm();
    await loadNotices();

    el.searchNoticesBtn?.addEventListener("click", () => loadNotices().catch(C.setError));
    el.loadNoticesBtn?.addEventListener("click", () => loadNotices().catch(C.setError));
    el.resetNoticesBtn?.addEventListener("click", () => {
      el.noticeFilterStoreId.value = "";
      el.noticeFilterStatus.value = "";
      loadNotices().catch(C.setError);
    });
    el.saveNoticeBtn?.addEventListener("click", () => saveNotice().catch(C.setError));
    el.resetNoticeFormBtn?.addEventListener("click", () => resetForm());
    el.noticeTableBody?.addEventListener("click", (event) => {
      const button = event.target instanceof HTMLElement ? event.target.closest("button[data-action]") : null;
      if (!button) return;
      const action = button.dataset.action;
      const noticeId = Number(button.dataset.id || 0);
      if (!action || !noticeId) return;
      onAction(action, noticeId).catch(C.setError);
    });
    el.closeNoticeDetailBtn?.addEventListener("click", () => closeDetailDialog());
    el.editNoticeFromDetailBtn?.addEventListener("click", async () => {
      if (!state.detailNoticeId) return;
      const notice = await C.request(`/notices/${state.detailNoticeId}`);
      closeDetailDialog();
      fillFormByNotice(notice);
    });
    el.publishNoticeFromDetailBtn?.addEventListener("click", async () => {
      if (!state.detailNoticeId) return;
      if (!window.confirm("确认发布该公告吗？发布后学生端可见，并会生成公告通知。")) return;
      await publishNotice(state.detailNoticeId);
    });
    el.offlineNoticeFromDetailBtn?.addEventListener("click", async () => {
      if (!state.detailNoticeId) return;
      if (!window.confirm("确认下线该公告吗？下线后学生端将不再显示。")) return;
      await offlineNotice(state.detailNoticeId);
    });
    el.deleteNoticeFromDetailBtn?.addEventListener("click", async () => {
      if (!state.detailNoticeId) return;
      if (!window.confirm("确认删除该公告吗？删除后无法恢复。")) return;
      await deleteNotice(state.detailNoticeId);
    });
  })().catch(C.setError);
})();
