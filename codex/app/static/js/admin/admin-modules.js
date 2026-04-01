(function () {
  const C = window.AdminCommon;
  if (!C) return;

  const resourceConfig = {
    stores: { path: "/stores", columns: [["id", "编号"], ["name", "门店名称"], ["address", "位置"], ["status", "状态"]] },
    areas: { path: "/areas", columns: [["id", "编号"], ["store_id", "门店编号"], ["name", "区域名称"], ["code", "区域编码"]] },
    seats: { path: "/seats", supportsStore: true, columns: [["id", "编号"], ["store_id", "门店编号"], ["area_id", "区域编号"], ["seat_no", "座位号"], ["seat_type", "座位类型"], ["seat_status", "座位状态"]] },
    plans: { path: "/plans", supportsStore: true, columns: [["id", "编号"], ["store_id", "门店编号"], ["name", "方案名称"], ["billing_type", "计费方式"], ["price", "价格"], ["status", "状态"]] },
    bookings: { path: "/bookings", supportsStore: true, supportsStatus: true, columns: [["id", "预约编号"], ["user_id", "用户编号"], ["seat_no", "座位"], ["status", "状态"], ["start_time", "开始时间"], ["end_time", "结束时间"]] },
    checkins: { path: "/checkins/records", supportsStore: true, columns: [["id", "记录编号"], ["booking_id", "预约编号"], ["user_id", "用户编号"], ["seat_id", "座位编号"], ["checkin_time", "签到时间"], ["checkin_method", "签到方式"]] },
    blacklists: { path: "/blacklists", columns: [["id", "编号"], ["user_id", "用户编号"], ["reason", "原因"], ["source", "来源"], ["is_active", "生效中"], ["start_at", "开始时间"], ["end_at", "结束时间"]] },
    memberships: { path: "/memberships", columns: [["id", "编号"], ["user_id", "用户编号"], ["card_name", "会员卡"], ["card_type", "类型"], ["balance_minutes", "剩余分钟"], ["balance_times", "剩余次数"], ["status", "状态"]] },
    notices: { path: "/notices", supportsStore: true, supportsStatus: true, columns: [["id", "编号"], ["store_id", "门店编号"], ["title", "公告标题"], ["status", "状态"], ["published_at", "发布时间"], ["created_at", "创建时间"]] },
  };

  function currentStoreById(storeId) {
    const stores = Array.isArray(C.state.stores) ? C.state.stores : [];
    return stores.find((item) => Number(item.id) === Number(storeId)) || null;
  }

  function fmtStoreHours(store, fallbackConfig) {
    if (store) {
      return `${String(store.open_time || "--:--").slice(0, 5)} - ${String(store.close_time || "--:--").slice(0, 5)}`;
    }
    if (fallbackConfig) {
      return `${fallbackConfig.default_open_time || "08:00"} - ${fallbackConfig.default_close_time || "23:00"}`;
    }
    return "08:00 - 23:00";
  }

  async function fetchSystemConfig() {
    return C.request("/system-config");
  }

  async function runBootstrap(path) {
    const result = await C.request(path, { method: "POST" });
    C.setSuccess(result?.message || "操作成功");
    return result;
  }

  function buildBarTooltip(hour, value, rate) {
    return `${hour}:00<br/>上座数：${value}<br/>上座率：${Number(rate || 0).toFixed(2)}%`;
  }

  function renderTrendBars(node, items, businessHours) {
    const list = Array.isArray(items) ? items : [];
    const filtered = businessHours.length ? list.filter((item) => businessHours.includes(Number(item.hour))) : list;
    if (!filtered.length) {
      node.innerHTML = '<div class="trend-empty">暂无统计数据</div>';
      return;
    }
    const max = Math.max(...filtered.map((item) => Number(item.occupied_seats || 0)), 1);
    node.innerHTML = filtered.map((item) => {
      const value = Number(item.occupied_seats || 0);
      const height = Math.max(12, Math.round((value / max) * 130));
      const hour = String(item.hour).padStart(2, "0");
      return `<div class="bar-item" title="${C.escapeHtml(buildBarTooltip(hour, value, item.occupancy_rate))}"><div class="bar" data-hour="${hour}" style="height:${height}px"></div></div>`;
    }).join("");
  }

  function renderSevenDayChart(node, items) {
    const chart = C.ensureChart("dashboard-seven-day", node);
    if (!chart) return;
    const list = Array.isArray(items) ? items : [];
    if (!list.length) {
      C.emptyChart(chart);
      return;
    }
    chart.setOption({
      tooltip: { trigger: "axis" },
      legend: { data: ["预约数"] },
      grid: { left: 42, right: 24, top: 46, bottom: 28 },
      xAxis: { type: "category", data: list.map((item) => item.date?.slice(5) || item.date || "-") },
      yAxis: { type: "value", name: "预约数", minInterval: 1 },
      series: [
        { name: "预约数", type: "line", smooth: true, data: list.map((item) => Number(item.booking_count || 0)), lineStyle: { width: 3, color: "#2563eb" }, itemStyle: { color: "#2563eb" } },
      ],
    }, true);
  }

  function renderHotSeatChart(node, items) {
    const chart = C.ensureChart("dashboard-hot-seat", node);
    if (!chart) return;
    const list = Array.isArray(items) ? items.slice(0, 5) : [];
    if (!list.length) {
      C.emptyChart(chart);
      return;
    }
    chart.setOption({
      tooltip: { trigger: "axis", axisPointer: { type: "shadow" } },
      grid: { left: 90, right: 24, top: 18, bottom: 18 },
      xAxis: { type: "value", minInterval: 1 },
      yAxis: { type: "category", data: list.map((item) => item.seat_no || `座位${item.seat_id}`) },
      series: [{ name: "预约次数", type: "bar", data: list.map((item) => Number(item.booking_count || 0)), itemStyle: { color: "#ea580c" }, label: { show: true, position: "right" } }],
    }, true);
  }

  function renderCheckinChart(node, data) {
    const chart = C.ensureChart("dashboard-checkin", node);
    if (!chart) return;
    const items = Array.isArray(data?.hourly_checkin_trend) ? data.hourly_checkin_trend : [];
    if (!items.length) {
      C.emptyChart(chart);
      return;
    }
    chart.setOption({
      tooltip: { trigger: "axis" },
      legend: { data: ["签到人数", "签到率"] },
      grid: { left: 42, right: 42, top: 46, bottom: 28 },
      xAxis: { type: "category", data: items.map((item) => `${String(item.hour).padStart(2, "0")}:00`) },
      yAxis: [
        { type: "value", name: "签到人数", minInterval: 1 },
        { type: "value", name: "签到率", min: 0, max: 100 },
      ],
      series: [
        { name: "签到人数", type: "bar", yAxisIndex: 0, data: items.map((item) => Number(item.checked_in_count || 0)), itemStyle: { color: "#0f766e" } },
        { name: "签到率", type: "line", smooth: true, yAxisIndex: 1, data: items.map((item) => Number(item.checkin_rate || 0)), lineStyle: { width: 3, color: "#ea580c" }, itemStyle: { color: "#ea580c" } },
      ],
    }, true);
  }

  function formatResourceCell(key, value) {
    if (value === null || value === undefined || value === "") return "-";
    if (["created_at", "updated_at", "start_time", "end_time", "published_at", "start_at", "end_at", "checkin_time", "released_at"].includes(key)) {
      return C.escapeHtml(C.fmtDate(value));
    }
    if (key === "status") {
      if (["draft", "published", "offline"].includes(String(value))) return C.noticeStatusTag(String(value));
      return C.bookingStatusTag(String(value));
    }
    if (key === "seat_type") return C.escapeHtml(window.seatTypeText ? window.seatTypeText(value) : String(value));
    if (key === "seat_status") {
      const mapping = {
        available: C.statusTag("可用", "active"),
        maintenance: C.statusTag("维修", "danger"),
        disabled: C.statusTag("禁用", "cancelled"),
      };
      return mapping[value] || C.escapeHtml(value);
    }
    if (key === "billing_type") {
      const mapping = { hour: "按小时", day: "按天", month: "包月" };
      return C.escapeHtml(mapping[value] || value);
    }
    if (key === "is_active" || key === "is_available") {
      return value ? C.statusTag("是", "active") : C.statusTag("否", "cancelled");
    }
    if (key === "price") return C.escapeHtml(C.fmtMoney(value));
    return C.escapeHtml(value);
  }

  function initDashboard() {
    if (!C.initPage()) return;

    const el = {
      storeSelect: document.getElementById("storeSelect"),
      statsDate: document.getElementById("statsDate"),
      loadStatsBtn: document.getElementById("loadStatsBtn"),
      loadCheckinStatsBtn: document.getElementById("loadCheckinStatsBtn"),
      metricBookingCount: document.getElementById("metricBookingCount"),
      metricCheckinCount: document.getElementById("metricCheckinCount"),
      metricOccupancyRate: document.getElementById("metricOccupancyRate"),
      metricNoShowCount: document.getElementById("metricNoShowCount"),
      metricIdleSeatCount: document.getElementById("metricIdleSeatCount"),
      metricCheckinRate: document.getElementById("metricCheckinRate"),
      metricMissedCheckins: document.getElementById("metricMissedCheckins"),
      trendBars: document.getElementById("trendBars"),
      sevenDayTrendChart: document.getElementById("sevenDayTrendChart"),
      hotSeatChart: document.getElementById("hotSeatChart"),
      checkinRateChart: document.getElementById("checkinRateChart"),
    };

    let currentConfig = null;

    const selectedStoreId = () => C.selectedStoreId(el.storeSelect);
    const statsQuery = () => {
      const query = new URLSearchParams();
      if (selectedStoreId()) query.set("store_id", String(selectedStoreId()));
      if (el.statsDate.value) query.set("date", el.statsDate.value);
      return query.toString();
    };

    function resetOverview() {
      el.metricBookingCount.textContent = "0";
      el.metricCheckinCount.textContent = "0";
      el.metricOccupancyRate.textContent = "0.00%";
      el.metricNoShowCount.textContent = "0";
      el.metricIdleSeatCount.textContent = "0";
    }

    function resetCheckin() {
      el.metricCheckinRate.textContent = "0.00%";
      el.metricMissedCheckins.textContent = "0";
    }

    function businessHours() {
      const store = currentStoreById(selectedStoreId());
      const openText = String(store?.open_time || currentConfig?.default_open_time || "08:00").slice(0, 5);
      const closeText = String(store?.close_time || currentConfig?.default_close_time || "23:00").slice(0, 5);
      const start = Number(openText.split(":")[0]);
      const end = Number(closeText.split(":")[0]);
      if (!Number.isFinite(start) || !Number.isFinite(end) || end <= start) return [];
      return Array.from({ length: end - start }, (_, index) => start + index);
    }

    async function loadPageData() {
      try {
        const [stats, checkin] = await Promise.all([
          C.request(`/stats/overview?${statsQuery()}`),
          C.request(`/checkins/stats?${statsQuery()}`),
        ]);
        el.metricBookingCount.textContent = String(Number(stats?.today_booking_count || 0));
        el.metricCheckinCount.textContent = String(Number(stats?.today_checkin_count || 0));
        el.metricOccupancyRate.textContent = `${Number(stats?.current_occupancy_rate || 0).toFixed(2)}%`;
        el.metricNoShowCount.textContent = String(Number(stats?.today_no_show_count || 0));
        el.metricIdleSeatCount.textContent = String(Number(stats?.current_idle_seat_count || 0));
        el.metricCheckinRate.textContent = `${Number(checkin?.checkin_rate || 0).toFixed(2)}%`;
        el.metricMissedCheckins.textContent = String(Number(checkin?.missed_checkin_count || 0));
        renderTrendBars(el.trendBars, stats?.hourly_occupancy_trend || [], businessHours());
        renderSevenDayChart(el.sevenDayTrendChart, stats?.recent_7_day_trend || []);
        renderHotSeatChart(el.hotSeatChart, stats?.hot_seat_rank || []);
        renderCheckinChart(el.checkinRateChart, checkin);
        C.setSuccess("统计数据已刷新");
      } catch {
        resetOverview();
        resetCheckin();
        renderTrendBars(el.trendBars, [], []);
        const seven = C.ensureChart("dashboard-seven-day", el.sevenDayTrendChart); if (seven) C.emptyChart(seven, "暂无统计数据");
        const hot = C.ensureChart("dashboard-hot-seat", el.hotSeatChart); if (hot) C.emptyChart(hot, "暂无统计数据");
        const checkinChart = C.ensureChart("dashboard-checkin", el.checkinRateChart); if (checkinChart) C.emptyChart(checkinChart, "暂无统计数据");
        C.setError(new Error("统计数据加载失败，请稍后重试"));
      }
    }

    (async () => {
      try {
        currentConfig = await fetchSystemConfig();
      } catch {
        currentConfig = null;
      }
      await C.loadStores(true);
      C.fillStoreSelect(el.storeSelect, C.state.stores || [], { includeAll: true, allLabel: "全部门店" });
      el.statsDate.value = C.today();
      el.loadStatsBtn?.addEventListener("click", () => loadPageData());
      el.loadCheckinStatsBtn?.addEventListener("click", () => loadPageData());
      el.storeSelect?.addEventListener("change", () => loadPageData());
      el.statsDate?.addEventListener("change", () => loadPageData());
      await loadPageData();
    })().catch(C.setError);
  }

  function initStores() {
    if (!C.initPage()) return;

    const el = {
      loadStoresBtn: document.getElementById("loadStoresBtn"),
      toggleStoreEditBtn: document.getElementById("toggleStoreEditBtn"),
      cancelStoreEditBtn: document.getElementById("cancelStoreEditBtn"),
      saveStoreInfoBtn: document.getElementById("saveStoreInfoBtn"),
      storeId: document.getElementById("storeId"),
      storeSummaryBanner: document.getElementById("storeSummaryBanner"),
      storeViewMode: document.getElementById("storeViewMode"),
      storeEditMode: document.getElementById("storeEditMode"),
      storeDetailName: document.getElementById("storeDetailName"),
      storeDetailDescription: document.getElementById("storeDetailDescription"),
      storeDetailAddress: document.getElementById("storeDetailAddress"),
      storeDetailPhone: document.getElementById("storeDetailPhone"),
      storeDetailStatus: document.getElementById("storeDetailStatus"),
      storeDetailHours: document.getElementById("storeDetailHours"),
      storeDetailHoursText: document.getElementById("storeDetailHoursText"),
      storeDescriptionInput: document.getElementById("storeDescriptionInput"),
      storeAddressInput: document.getElementById("storeAddressInput"),
      storePhoneInput: document.getElementById("storePhoneInput"),
      storeStatusInput: document.getElementById("storeStatusInput"),
      storeOpenTimeInput: document.getElementById("storeOpenTimeInput"),
      storeCloseTimeInput: document.getElementById("storeCloseTimeInput"),
    };

    let currentConfig = null;
    let editMode = false;

    const selectedStoreId = () => C.selectedStoreId(el.storeId);
    const currentStore = () => currentStoreById(selectedStoreId());

    function toggleStoreEdit(enabled) {
      editMode = enabled;
      el.storeViewMode.classList.toggle("hidden", enabled);
      el.storeEditMode.classList.toggle("hidden", !enabled);
      el.toggleStoreEditBtn.textContent = enabled ? "取消编辑" : "编辑门店";
    }

    function renderStoreDetails() {
      const store = currentStore();
      if (!store) {
        const text = (C.state.stores || []).length ? "当前为全部门店视图" : "暂无门店信息";
        el.storeSummaryBanner.textContent = text;
        el.storeDetailName.textContent = text;
        el.storeDetailDescription.textContent = (C.state.stores || []).length ? "全部门店模式下仅展示汇总信息。" : "暂无门店信息";
        el.storeDetailAddress.textContent = "-";
        el.storeDetailPhone.textContent = "-";
        el.storeDetailStatus.innerHTML = C.statusTag("全部门店", "normal");
        el.storeDetailHours.textContent = "全部门店";
        el.storeDetailHoursText.textContent = fmtStoreHours(null, currentConfig);
        el.toggleStoreEditBtn.disabled = true;
        toggleStoreEdit(false);
        return;
      }

      el.storeSummaryBanner.textContent = store.name || "-";
      el.storeDetailName.textContent = store.name || "-";
      el.storeDetailDescription.textContent = String(store.description || "").trim() || "暂无门店简介";
      el.storeDetailAddress.textContent = store.address || "-";
      el.storeDetailPhone.textContent = store.contact_phone || "-";
      el.storeDetailStatus.innerHTML = Number(store.status) === 1 ? C.statusTag("营业中", "active") : C.statusTag("已停用", "cancelled");
      el.storeDetailHours.textContent = fmtStoreHours(store, currentConfig);
      el.storeDetailHoursText.textContent = fmtStoreHours(store, currentConfig);
      el.storeDescriptionInput.value = store.description || "";
      el.storeAddressInput.value = store.address || "";
      el.storePhoneInput.value = store.contact_phone || "";
      el.storeStatusInput.value = String(store.status ?? 1);
      el.storeOpenTimeInput.value = String(store.open_time || currentConfig?.default_open_time || "08:00").slice(0, 5);
      el.storeCloseTimeInput.value = String(store.close_time || currentConfig?.default_close_time || "23:00").slice(0, 5);
      el.toggleStoreEditBtn.disabled = !C.canEditStore();
    }

    async function loadStores() {
      const previous = el.storeId.value;
      await C.loadStores(true);
      C.fillStoreSelect(el.storeId, C.state.stores || [], { includeAll: true, allLabel: "全部门店", selectedValue: previous || "" });
      renderStoreDetails();
    }

    async function saveStoreInfo() {
      const store = currentStore();
      if (!store) throw new Error("请先选择门店");
      if (!C.canEditStore()) throw new Error("权限不足");
      const payload = {
        description: el.storeDescriptionInput.value.trim(),
        address: el.storeAddressInput.value.trim(),
        contact_phone: el.storePhoneInput.value.trim(),
        status: Number(el.storeStatusInput.value || 1),
        open_time: el.storeOpenTimeInput.value || currentConfig?.default_open_time || "08:00",
        close_time: el.storeCloseTimeInput.value || currentConfig?.default_close_time || "23:00",
      };
      const updated = await C.request(`/stores/${store.id}`, { method: "PUT", body: JSON.stringify(payload) });
      C.state.stores = (C.state.stores || []).map((item) => (item.id === updated.id ? updated : item));
      C.fillStoreSelect(el.storeId, C.state.stores || [], { includeAll: true, allLabel: "全部门店", selectedValue: updated.id });
      toggleStoreEdit(false);
      renderStoreDetails();
      C.setSuccess("门店信息保存成功");
    }

    (async () => {
      try {
        currentConfig = await fetchSystemConfig();
      } catch {
        currentConfig = null;
      }
      await loadStores();
      el.loadStoresBtn?.addEventListener("click", () => loadStores().catch(C.setError));
      el.storeId?.addEventListener("change", () => {
        toggleStoreEdit(false);
        renderStoreDetails();
      });
      el.toggleStoreEditBtn?.addEventListener("click", () => {
        if (!selectedStoreId()) {
          C.setError(new Error("请先选择具体门店"));
          return;
        }
        if (!C.canEditStore()) {
          C.setError(new Error("权限不足"));
          return;
        }
        toggleStoreEdit(!editMode);
      });
      el.cancelStoreEditBtn?.addEventListener("click", () => {
        toggleStoreEdit(false);
        renderStoreDetails();
      });
      el.saveStoreInfoBtn?.addEventListener("click", () => saveStoreInfo().catch(C.setError));
    })().catch(C.setError);
  }

  function initResources() {
    if (!C.initPage()) return;

    const el = {
      bootstrapBtn: document.getElementById("bootstrapBtn"),
      bootstrapDemoBtn: document.getElementById("bootstrapDemoBtn"),
      seatManageStoreId: document.getElementById("seatManageStoreId"),
      seatManageAreaId: document.getElementById("seatManageAreaId"),
      seatManageNoInput: document.getElementById("seatManageNoInput"),
      seatManageTypeSelect: document.getElementById("seatManageTypeSelect"),
      seatManageStatusSelect: document.getElementById("seatManageStatusSelect"),
      createSeatBtn: document.getElementById("createSeatBtn"),
      deleteSeatIdInput: document.getElementById("deleteSeatIdInput"),
      deleteSeatBtn: document.getElementById("deleteSeatBtn"),
      bookingAssistUserIdInput: document.getElementById("bookingAssistUserIdInput"),
      bookingAssistSeatIdInput: document.getElementById("bookingAssistSeatIdInput"),
      bookingAssistStartInput: document.getElementById("bookingAssistStartInput"),
      bookingAssistEndInput: document.getElementById("bookingAssistEndInput"),
      createAdminBookingBtn: document.getElementById("createAdminBookingBtn"),
      adminBookingStoreId: document.getElementById("adminBookingStoreId"),
      adminBookingStatusSelect: document.getElementById("adminBookingStatusSelect"),
      adminBookingUserIdInput: document.getElementById("adminBookingUserIdInput"),
      loadAdminBookingsBtn: document.getElementById("loadAdminBookingsBtn"),
      adminBookingTbody: document.getElementById("adminBookingTbody"),
      loadResourceBtn: document.getElementById("loadResourceBtn"),
      resourceType: document.getElementById("resourceType"),
      resourceStoreId: document.getElementById("resourceStoreId"),
      resourceStatusInput: document.getElementById("resourceStatusInput"),
      resourceTableHeadRow: document.getElementById("resourceTableHeadRow"),
      resourceTableBody: document.getElementById("resourceTableBody"),
    };

    const canWrite = () => C.canEditStore();
    const canPortal = () => ["staff", "admin", "super_admin"].includes(C.currentUser()?.role || "");

    function initResourceTypeOptions() {
      const options = Object.keys(resourceConfig)
        .map((key) => `<option value="${key}">${C.escapeHtml(window.resourceTypeText ? window.resourceTypeText(key) : key)}</option>`)
        .join("");
      el.resourceType.innerHTML = options;
      if (!el.resourceType.value) el.resourceType.value = "stores";
    }

    function fillAreaSelect(items) {
      const rows = Array.isArray(items) ? items : [];
      el.seatManageAreaId.innerHTML = [
        '<option value="">未分配区域</option>',
        ...rows.map((item) => `<option value="${item.id}">${C.escapeHtml(item.name)}（${C.escapeHtml(item.code)}）</option>`),
      ].join("");
    }

    async function loadAreasForSeatStore() {
      const storeId = C.selectedStoreId(el.seatManageStoreId);
      if (!storeId) {
        fillAreaSelect([]);
        return;
      }
      const items = await C.request(`/areas?store_id=${storeId}`);
      fillAreaSelect(Array.isArray(items) ? items : []);
    }

    function resourceQuery() {
      const config = resourceConfig[el.resourceType.value];
      const query = new URLSearchParams();
      const storeId = C.selectedStoreId(el.resourceStoreId);
      if (config?.supportsStore && storeId) query.set("store_id", String(storeId));
      if (config?.supportsStatus && el.resourceStatusInput.value.trim()) query.set("status", el.resourceStatusInput.value.trim());
      return query.toString();
    }

    function renderResourceTable(items) {
      const config = resourceConfig[el.resourceType.value];
      const rows = Array.isArray(items) ? items : [];
      el.resourceTableHeadRow.innerHTML = config.columns.map(([, label]) => `<th>${C.escapeHtml(label)}</th>`).join("");
      if (!rows.length) {
        el.resourceTableBody.innerHTML = `<tr><td colspan="${config.columns.length}">暂无数据</td></tr>`;
        return;
      }
      el.resourceTableBody.innerHTML = rows.map((row) => `<tr>${config.columns.map(([key]) => `<td>${formatResourceCell(key, row[key])}</td>`).join("")}</tr>`).join("");
    }

    async function loadResourceData() {
      const config = resourceConfig[el.resourceType.value];
      if (!config) return;
      const query = resourceQuery();
      const data = await C.request(`${config.path}${query ? `?${query}` : ""}`);
      const rows = Array.isArray(data) ? data : Array.isArray(data?.items) ? data.items : [];
      renderResourceTable(rows);
      C.setSuccess(`已加载${window.resourceTypeText ? window.resourceTypeText(el.resourceType.value) : el.resourceType.value}数据`);
    }

    function adminBookingQuery() {
      const query = new URLSearchParams();
      const storeId = C.selectedStoreId(el.adminBookingStoreId);
      const userId = Number(el.adminBookingUserIdInput.value || 0);
      if (storeId) query.set("store_id", String(storeId));
      if (el.adminBookingStatusSelect.value) query.set("status", el.adminBookingStatusSelect.value);
      if (Number.isFinite(userId) && userId > 0) query.set("user_id", String(userId));
      return query.toString();
    }

    function renderAdminBookings(items) {
      const rows = Array.isArray(items) ? items : [];
      if (!rows.length) {
        el.adminBookingTbody.innerHTML = '<tr><td colspan="8">暂无预约数据</td></tr>';
        return;
      }

      el.adminBookingTbody.innerHTML = rows.map((item) => {
        const actions = [];
        if (item.status === "booked" && canPortal()) {
          actions.push(`<button class="btn btn-inline" data-booking-action="checkin" data-id="${item.id}">帮助签到</button>`);
        }
        if (item.status === "booked" && canWrite()) {
          actions.push(`<button class="btn btn-inline" data-booking-action="cancel" data-id="${item.id}">取消预约</button>`);
        }
        if (item.status === "checked_in" && canWrite()) {
          actions.push(`<button class="btn btn-inline" data-booking-action="complete" data-id="${item.id}">标记完成</button>`);
        }
        return `<tr>
          <td>${item.id}</td>
          <td>${item.user_id}</td>
          <td>${item.store_id ?? "-"}</td>
          <td>${C.escapeHtml(item.seat_no || item.seat_id || "-")}</td>
          <td>${C.bookingStatusTag(item.status)}</td>
          <td>${C.escapeHtml(C.fmtDate(item.start_time))}</td>
          <td>${C.escapeHtml(C.fmtDate(item.end_time))}</td>
          <td>${actions.length ? actions.join("") : '<span class="hint">无可执行操作</span>'}</td>
        </tr>`;
      }).join("");
    }

    async function loadAdminBookings() {
      const query = adminBookingQuery();
      const data = await C.request(`/bookings${query ? `?${query}` : ""}`);
      renderAdminBookings(Array.isArray(data) ? data : []);
      C.setSuccess("已加载预约处理列表");
    }

    async function createSeat() {
      if (!canWrite()) throw new Error("当前账号无权新增或删除座位");
      const storeId = C.selectedStoreId(el.seatManageStoreId);
      const seatNo = el.seatManageNoInput.value.trim();
      if (!storeId) throw new Error("请先选择门店");
      if (!seatNo) throw new Error("请输入座位编号");

      const payload = {
        store_id: storeId,
        area_id: C.selectedStoreId(el.seatManageAreaId),
        seat_no: seatNo,
        seat_type: el.seatManageTypeSelect.value || "normal",
        seat_status: el.seatManageStatusSelect.value || "available",
        is_available: (el.seatManageStatusSelect.value || "available") === "available",
      };
      await C.request("/seats", {
        method: "POST",
        body: JSON.stringify(payload),
      });
      el.seatManageNoInput.value = "";
      C.setSuccess(`已新增座位 ${seatNo}`);
      if (el.resourceType.value === "seats") await loadResourceData();
    }

    async function deleteSeat() {
      if (!canWrite()) throw new Error("当前账号无权新增或删除座位");
      const seatId = Number(el.deleteSeatIdInput.value || 0);
      if (!Number.isFinite(seatId) || seatId <= 0) throw new Error("请输入有效的座位 ID");
      if (!window.confirm(`确认删除座位 #${seatId} 吗？`)) return;
      await C.request(`/seats/${seatId}`, { method: "DELETE" });
      el.deleteSeatIdInput.value = "";
      C.setSuccess(`已删除座位 #${seatId}`);
      if (el.resourceType.value === "seats") await loadResourceData();
    }

    async function createAdminBooking() {
      if (!canWrite()) throw new Error("当前账号无权代学生创建预约");
      const userId = Number(el.bookingAssistUserIdInput.value || 0);
      const seatId = Number(el.bookingAssistSeatIdInput.value || 0);
      const startTime = C.toIso(el.bookingAssistStartInput.value);
      const endTime = C.toIso(el.bookingAssistEndInput.value);
      if (!Number.isFinite(userId) || userId <= 0) throw new Error("请输入有效的学生编号");
      if (!Number.isFinite(seatId) || seatId <= 0) throw new Error("请输入有效的座位编号");
      if (!startTime || !endTime) throw new Error("请选择完整的预约时间");

      const data = await C.request("/bookings", {
        method: "POST",
        body: JSON.stringify({
          user_id: userId,
          seat_id: seatId,
          start_time: startTime,
          end_time: endTime,
        }),
      });
      C.setSuccess(`已为学生 #${userId} 创建预约，预约编号 ${data?.booking_id || "-"}`);
      await loadAdminBookings();
      if (el.resourceType.value === "bookings") await loadResourceData();
    }

    async function doAdminBookingAction(bookingId, action) {
      const actionMap = {
        checkin: { path: `/bookings/${bookingId}/force-checkin`, label: "帮助签到", confirm: "确认帮助该学生完成签到吗？" },
        cancel: { path: `/bookings/${bookingId}/cancel`, label: "取消预约", confirm: "确认取消该预约吗？" },
        complete: { path: `/bookings/${bookingId}/complete`, label: "标记完成", confirm: "确认将该预约标记为已完成吗？" },
      };
      const config = actionMap[action];
      if (!config) return;
      if (!window.confirm(config.confirm)) return;
      await C.request(config.path, { method: "POST" });
      await loadAdminBookings();
      if (el.resourceType.value === "bookings") await loadResourceData();
      C.setSuccess(`${config.label}成功`);
    }

    (async () => {
      await C.loadStores(true);
      C.fillStoreSelect(el.resourceStoreId, C.state.stores || [], { includeAll: true, allLabel: "全部门店" });
      C.fillStoreSelect(el.adminBookingStoreId, C.state.stores || [], { includeAll: true, allLabel: "全部门店" });
      C.fillStoreSelect(el.seatManageStoreId, C.state.stores || [], { includeAll: false });
      initResourceTypeOptions();
      await loadAreasForSeatStore();

      el.seatManageStoreId?.addEventListener("change", () => loadAreasForSeatStore().catch(C.setError));
      el.createSeatBtn?.addEventListener("click", () => createSeat().catch(C.setError));
      el.deleteSeatBtn?.addEventListener("click", () => deleteSeat().catch(C.setError));
      el.createAdminBookingBtn?.addEventListener("click", () => createAdminBooking().catch(C.setError));
      el.loadAdminBookingsBtn?.addEventListener("click", () => loadAdminBookings().catch(C.setError));
      el.adminBookingTbody?.addEventListener("click", (event) => {
        const target = event.target.closest("[data-booking-action]");
        if (!target) return;
        const bookingId = Number(target.dataset.id || 0);
        const action = target.dataset.bookingAction;
        if (!bookingId || !action) return;
        doAdminBookingAction(bookingId, action).catch(C.setError);
      });
      el.loadResourceBtn?.addEventListener("click", () => loadResourceData().catch(C.setError));
      el.resourceType?.addEventListener("change", () => loadResourceData().catch(C.setError));
      el.bootstrapBtn?.addEventListener("click", () => runBootstrap("/bootstrap").catch(C.setError));
      el.bootstrapDemoBtn?.addEventListener("click", () => runBootstrap("/bootstrap-demo").catch(C.setError));
      await loadResourceData();
      await loadAdminBookings();
    })().catch(C.setError);
  }

  function initOrders() {
    window.location.replace("/admin/dashboard");
  }

  function initUsers() {
    if (!C.initPage()) return;

    const el = {
      userNameInput: document.getElementById("userNameInput"),
      userPhoneInput: document.getElementById("userPhoneInput"),
      userRoleSelect: document.getElementById("userRoleSelect"),
      userStatusSelect: document.getElementById("userStatusSelect"),
      userCreatedFromInput: document.getElementById("userCreatedFromInput"),
      userCreatedToInput: document.getElementById("userCreatedToInput"),
      loadUsersBtn: document.getElementById("loadUsersBtn"),
      searchUsersBtn: document.getElementById("searchUsersBtn"),
      resetUsersBtn: document.getElementById("resetUsersBtn"),
      userListMeta: document.getElementById("userListMeta"),
      userTbody: document.getElementById("userTbody"),
      userBookingsMeta: document.getElementById("userBookingsMeta"),
      userBookingsTbody: document.getElementById("userBookingsTbody"),
      reloadUserBookingsBtn: document.getElementById("reloadUserBookingsBtn"),
      userDetailDialog: document.getElementById("userDetailDialog"),
      userDetailContent: document.getElementById("userDetailContent"),
      closeUserDetailBtn: document.getElementById("closeUserDetailBtn"),
      toggleUserBlacklistBtn: document.getElementById("toggleUserBlacklistBtn"),
      viewUserBookingsBtn: document.getElementById("viewUserBookingsBtn"),
      assignRolePanel: document.getElementById("assignRolePanel"),
      assignUserRoleSelect: document.getElementById("assignUserRoleSelect"),
      assignUserRoleBtn: document.getElementById("assignUserRoleBtn"),
    };

    const pageState = {
      users: [],
      selectedUser: null,
      userDetail: null,
    };

    function userQuery() {
      const query = new URLSearchParams();
      if (el.userNameInput.value.trim()) query.set("name", el.userNameInput.value.trim());
      if (el.userPhoneInput.value.trim()) query.set("phone", el.userPhoneInput.value.trim());
      if (el.userRoleSelect.value) query.set("role", el.userRoleSelect.value);
      if (el.userStatusSelect.value) query.set("status", el.userStatusSelect.value);
      const from = C.toIso(el.userCreatedFromInput.value);
      const to = C.toIso(el.userCreatedToInput.value);
      if (from) query.set("created_from", from);
      if (to) query.set("created_to", to);
      return query.toString();
    }

    function findUserInState(userId) {
      return pageState.users.find((item) => Number(item.id) === Number(userId)) || null;
    }

    function openDialog(dialog) {
      if (!dialog) return;
      if (typeof dialog.showModal === "function") {
        dialog.showModal();
        return;
      }
      dialog.setAttribute("open", "open");
    }

    function closeDialog(dialog) {
      if (!dialog) return;
      if (typeof dialog.close === "function") {
        dialog.close();
        return;
      }
      dialog.removeAttribute("open");
    }

    function renderUsers(users) {
      const rows = Array.isArray(users) ? users : [];
      el.userListMeta.textContent = `当前共 ${rows.length} 位注册用户`;
      if (!rows.length) {
        el.userTbody.innerHTML = '<tr><td colspan="11">暂无用户数据</td></tr>';
        return;
      }
      el.userTbody.innerHTML = rows.map((user) => {
        const actions = [
          `<button type="button" class="action-menu-item" data-action="detail" data-id="${user.id}">查看详情</button>`,
          `<button type="button" class="action-menu-item" data-action="bookings" data-id="${user.id}">查看预约</button>`,
        ];
        if (C.isSuperAdmin()) actions.push(`<button type="button" class="action-menu-item" data-action="assign-role" data-id="${user.id}">分配权限</button>`);
        if (Number(user.status) === 1) actions.push(`<button type="button" class="action-menu-item" data-action="freeze" data-id="${user.id}">冻结用户</button>`);
        if (Number(user.status) === 0) actions.push(`<button type="button" class="action-menu-item" data-action="unfreeze" data-id="${user.id}">解冻用户</button>`);
        actions.push(`<button type="button" class="action-menu-item" data-action="blacklist" data-id="${user.id}">${user.is_blacklisted ? "移出黑名单" : "加入黑名单"}</button>`);
        actions.push(`<button type="button" class="action-menu-item danger" data-action="delete" data-id="${user.id}">删除用户</button>`);
        const actionMenu = `
          <div class="action-dropdown">
            <button type="button" class="btn btn-inline action-dropdown-trigger">操作</button>
            <div class="action-dropdown-menu hidden">
              ${actions.join("")}
            </div>
          </div>`;
        return `<tr>
          <td>${user.id}</td>
          <td>${C.escapeHtml(user.name || "-")}</td>
          <td>${C.escapeHtml(user.phone || "-")}</td>
          <td>${C.escapeHtml(user.email || "-")}</td>
          <td>${C.escapeHtml(window.roleText ? window.roleText(user.role) : user.role)}</td>
          <td>${C.userStatusTag(user.status)}</td>
          <td>${C.escapeHtml(user.no_show_count || 0)}</td>
          <td>${C.blacklistTag(user.is_blacklisted, user.blacklist_end_at)}</td>
          <td>${C.escapeHtml(user.history_booking_count || 0)}</td>
          <td>${C.escapeHtml(C.fmtDate(user.created_at))}</td>
          <td>${actionMenu}</td>
        </tr>`;
      }).join("");
    }

    async function loadUsers() {
      const query = userQuery();
      const users = await C.request(`/users${query ? `?${query}` : ""}`);
      pageState.users = Array.isArray(users) ? users : [];
      renderUsers(pageState.users);
    }

    function renderUserDetail(detail) {
      const blacklistStatus = detail.is_blacklisted
        ? `已在黑名单${detail.blacklist_end_at ? `（${C.fmtDate(detail.blacklist_end_at)}）` : ""}`
        : "正常";
      el.userDetailContent.innerHTML = `
        <div><span>昵称</span><strong>${C.escapeHtml(detail.name || "-")}</strong></div>
        <div><span>手机号</span><strong>${C.escapeHtml(detail.phone || "-")}</strong></div>
        <div><span>邮箱</span><strong>${C.escapeHtml(detail.email || "-")}</strong></div>
        <div><span>角色</span><strong>${C.escapeHtml(window.roleText ? window.roleText(detail.role) : detail.role)}</strong></div>
        <div><span>状态</span><strong>${C.escapeHtml(C.userStatusText(detail.status))}</strong></div>
        <div><span>注册时间</span><strong>${C.escapeHtml(C.fmtDate(detail.created_at))}</strong></div>
        <div><span>爽约次数</span><strong>${C.escapeHtml(detail.no_show_count || 0)}</strong></div>
        <div><span>黑名单状态</span><strong>${C.escapeHtml(blacklistStatus)}</strong></div>
        <div><span>历史预约数</span><strong>${C.escapeHtml(detail.history_booking_count || 0)}</strong></div>
        <div><span>最近预约时间</span><strong>${C.escapeHtml(C.fmtDate(detail.last_booking_at))}</strong></div>`;
      el.toggleUserBlacklistBtn.textContent = detail.is_blacklisted ? "移出黑名单" : "加入黑名单";
      if (el.assignRolePanel) {
        const canAssignRole = C.isSuperAdmin();
        el.assignRolePanel.classList.toggle("hidden", !canAssignRole);
        if (canAssignRole && el.assignUserRoleSelect) {
          el.assignUserRoleSelect.value = detail.role || "student";
          el.assignUserRoleSelect.disabled = Number(detail.id) === Number(C.currentUser()?.id);
        }
        if (el.assignUserRoleBtn) {
          el.assignUserRoleBtn.disabled = !canAssignRole || Number(detail.id) === Number(C.currentUser()?.id);
        }
      }
    }

    async function openUserDetail(userId) {
      const detail = await C.request(`/users/${userId}/detail`);
      pageState.userDetail = detail;
      renderUserDetail(detail);
      openDialog(el.userDetailDialog);
    }

    async function loadUserBookings() {
      if (!pageState.selectedUser) {
        el.userBookingsMeta.textContent = "请先选择用户";
        el.userBookingsTbody.innerHTML = '<tr><td colspan="6">请先选择用户</td></tr>';
        return;
      }
      const bookings = await C.request(`/bookings?user_id=${pageState.selectedUser.id}&limit=100`);
      const rows = Array.isArray(bookings) ? bookings : [];
      el.userBookingsMeta.textContent = `当前查看：${pageState.selectedUser.name || "-"} 的预约记录`;
      if (!rows.length) {
        el.userBookingsTbody.innerHTML = '<tr><td colspan="6">该用户暂无预约记录</td></tr>';
        return;
      }
      const storeMap = new Map((C.state.stores || []).map((item) => [item.id, item]));
      el.userBookingsTbody.innerHTML = rows.map((item) => {
        const store = storeMap.get(item.store_id);
        return `<tr>
          <td>${item.id}</td>
          <td>${C.escapeHtml(store?.name || `门店#${item.store_id || "-"}`)}</td>
          <td>${C.escapeHtml(item.seat_no || "-")}</td>
          <td>${C.escapeHtml(C.fmtDate(item.start_time))}</td>
          <td>${C.escapeHtml(C.fmtDate(item.end_time))}</td>
          <td>${C.bookingStatusTag(item.status)}</td>
        </tr>`;
      }).join("");
    }

    async function setSelectedUser(userId) {
      const user = findUserInState(userId);
      pageState.selectedUser = user || { id: userId, name: `用户#${userId}` };
      await loadUserBookings();
      el.userBookingsMeta.closest("section")?.scrollIntoView({ behavior: "smooth", block: "start" });
    }

    async function toggleBlacklistForUser(userId, currentlyBlacklisted) {
      if (currentlyBlacklisted) {
        await C.request(`/blacklists/${userId}`, { method: "DELETE" });
        C.setSuccess("用户已移出黑名单");
      } else {
        await C.request("/blacklists", { method: "POST", body: JSON.stringify({ user_id: userId, reason: "管理员手动加入黑名单" }) });
        C.setSuccess("用户已加入黑名单");
      }
      await loadUsers();
      if (pageState.userDetail && Number(pageState.userDetail.id) === Number(userId)) {
        await openUserDetail(userId);
      }
    }

    async function assignRoleForUser(userId, role) {
      await C.request(`/users/${userId}/assign-role`, {
        method: "POST",
        body: JSON.stringify({ role }),
      });
      C.setSuccess("权限分配成功");
      await loadUsers();
      if (pageState.userDetail && Number(pageState.userDetail.id) === Number(userId)) {
        await openUserDetail(userId);
      }
    }

    async function doUserAction(userId, action) {
      const user = findUserInState(userId);
      if (!user) return;
      if (action === "detail") return openUserDetail(userId);
      if (action === "assign-role") return openUserDetail(userId);
      if (action === "bookings") return setSelectedUser(userId);
      if (action === "blacklist") return toggleBlacklistForUser(userId, user.is_blacklisted);
      if (action === "freeze") {
        if (!window.confirm("确认冻结该用户吗？冻结后将无法正常登录和预约。")) return;
        await C.request(`/users/${userId}/freeze`, { method: "POST" });
        C.setSuccess("用户已冻结");
        return loadUsers();
      }
      if (action === "unfreeze") {
        if (!window.confirm("确认解冻该用户吗？")) return;
        await C.request(`/users/${userId}/unfreeze`, { method: "POST" });
        C.setSuccess("用户已解冻");
        return loadUsers();
      }
      if (action === "delete") {
        if (!window.confirm("确认删除该用户吗？将执行软删除并隐藏该用户。")) return;
        await C.request(`/users/${userId}`, { method: "DELETE" });
        C.setSuccess("用户已删除");
        if (pageState.selectedUser && Number(pageState.selectedUser.id) === Number(userId)) {
          pageState.selectedUser = null;
          await loadUserBookings();
        }
        return loadUsers();
      }
    }

    (async () => {
      await C.loadStores(true);
      el.loadUsersBtn?.addEventListener("click", () => loadUsers().catch(C.setError));
      el.searchUsersBtn?.addEventListener("click", () => loadUsers().catch(C.setError));
      el.resetUsersBtn?.addEventListener("click", () => {
        el.userNameInput.value = "";
        el.userPhoneInput.value = "";
        el.userRoleSelect.value = "";
        el.userStatusSelect.value = "";
        el.userCreatedFromInput.value = "";
        el.userCreatedToInput.value = "";
        loadUsers().catch(C.setError);
      });
      el.userTbody?.addEventListener("click", async (event) => {
        const target = event.target;
        if (!(target instanceof HTMLElement)) return;
        const trigger = target.closest(".action-dropdown-trigger");
        if (trigger) {
          const dropdown = trigger.closest(".action-dropdown");
          document.querySelectorAll(".action-dropdown.open").forEach((node) => {
            if (node !== dropdown) node.classList.remove("open");
            node.querySelector(".action-dropdown-menu")?.classList.add("hidden");
          });
          dropdown?.classList.toggle("open");
          dropdown?.querySelector(".action-dropdown-menu")?.classList.toggle("hidden");
          return;
        }
        const button = target.closest("button[data-action]");
        if (!button) return;
        button.closest(".action-dropdown")?.classList.remove("open");
        button.closest(".action-dropdown")?.querySelector(".action-dropdown-menu")?.classList.add("hidden");
        const userId = Number(button.dataset.id || 0);
        const action = button.dataset.action;
        if (!userId || !action) return;
        try {
          await doUserAction(userId, action);
        } catch (error) {
          C.setError(error);
        }
      });
      document.addEventListener("click", (event) => {
        const target = event.target;
        if (target instanceof HTMLElement && target.closest(".action-dropdown")) return;
        document.querySelectorAll(".action-dropdown.open").forEach((node) => {
          node.classList.remove("open");
          node.querySelector(".action-dropdown-menu")?.classList.add("hidden");
        });
      });
      el.reloadUserBookingsBtn?.addEventListener("click", () => loadUserBookings().catch(C.setError));
      el.closeUserDetailBtn?.addEventListener("click", () => closeDialog(el.userDetailDialog));
      el.viewUserBookingsBtn?.addEventListener("click", async () => {
        if (!pageState.userDetail) return;
        closeDialog(el.userDetailDialog);
        await setSelectedUser(pageState.userDetail.id);
      });
      el.toggleUserBlacklistBtn?.addEventListener("click", async () => {
        if (!pageState.userDetail) return;
        await toggleBlacklistForUser(pageState.userDetail.id, pageState.userDetail.is_blacklisted);
      });
      el.assignUserRoleBtn?.addEventListener("click", async () => {
        if (!pageState.userDetail) return;
        const role = el.assignUserRoleSelect?.value || "student";
        const targetName = pageState.userDetail.name || `用户#${pageState.userDetail.id}`;
        if (!window.confirm(`确认将 ${targetName} 的角色调整为${window.roleText ? window.roleText(role) : role}吗？`)) return;
        await assignRoleForUser(pageState.userDetail.id, role);
      });
      await loadUsers();
      await loadUserBookings();
    })().catch(C.setError);
  }

  function initConfig() {
    if (!C.initPage()) return;

    const el = {
      loadSystemConfigBtn: document.getElementById("loadSystemConfigBtn"),
      saveSystemConfigBtn: document.getElementById("saveSystemConfigBtn"),
      resetSystemConfigBtn: document.getElementById("resetSystemConfigBtn"),
      cfgMinBookingMinutes: document.getElementById("cfgMinBookingMinutes"),
      cfgMaxBookingHours: document.getElementById("cfgMaxBookingHours"),
      cfgCancelBeforeMinutes: document.getElementById("cfgCancelBeforeMinutes"),
      cfgRescheduleBeforeMinutes: document.getElementById("cfgRescheduleBeforeMinutes"),
      cfgCheckinGraceMinutes: document.getElementById("cfgCheckinGraceMinutes"),
      cfgNoShowThreshold: document.getElementById("cfgNoShowThreshold"),
      cfgBlacklistEffectiveDays: document.getElementById("cfgBlacklistEffectiveDays"),
      cfgDefaultOpenTime: document.getElementById("cfgDefaultOpenTime"),
      cfgDefaultCloseTime: document.getElementById("cfgDefaultCloseTime"),
      bootstrapBtn: document.getElementById("bootstrapBtn"),
      bootstrapDemoBtn: document.getElementById("bootstrapDemoBtn"),
    };

    function fillSystemConfigForm(config) {
      el.cfgMinBookingMinutes.value = config.min_booking_minutes ?? 30;
      el.cfgMaxBookingHours.value = config.max_booking_hours ?? 12;
      el.cfgCancelBeforeMinutes.value = config.cancel_before_minutes ?? 30;
      el.cfgRescheduleBeforeMinutes.value = config.reschedule_before_minutes ?? 60;
      el.cfgCheckinGraceMinutes.value = config.checkin_grace_minutes ?? 30;
      el.cfgNoShowThreshold.value = config.no_show_blacklist_threshold ?? 3;
      el.cfgBlacklistEffectiveDays.value = config.blacklist_effective_days ?? 7;
      el.cfgDefaultOpenTime.value = config.default_open_time || "08:00";
      el.cfgDefaultCloseTime.value = config.default_close_time || "23:00";
    }

    function systemConfigPayload() {
      return {
        min_booking_minutes: Number(el.cfgMinBookingMinutes.value || 30),
        max_booking_hours: Number(el.cfgMaxBookingHours.value || 12),
        cancel_before_minutes: Number(el.cfgCancelBeforeMinutes.value || 30),
        reschedule_before_minutes: Number(el.cfgRescheduleBeforeMinutes.value || 60),
        checkin_grace_minutes: Number(el.cfgCheckinGraceMinutes.value || 30),
        no_show_blacklist_threshold: Number(el.cfgNoShowThreshold.value || 3),
        blacklist_effective_days: Number(el.cfgBlacklistEffectiveDays.value || 7),
        default_open_time: el.cfgDefaultOpenTime.value || "08:00",
        default_close_time: el.cfgDefaultCloseTime.value || "23:00",
      };
    }

    async function loadSystemConfig() {
      const config = await C.request("/system-config");
      fillSystemConfigForm(config);
      return config;
    }

    async function saveSystemConfig() {
      const config = await C.request("/system-config", { method: "PUT", body: JSON.stringify(systemConfigPayload()) });
      fillSystemConfigForm(config);
      C.setSuccess("配置保存成功");
    }

    async function resetSystemConfig() {
      if (!window.confirm("确认恢复默认配置吗？当前修改将被覆盖。")) return;
      const config = await C.request("/system-config/reset", { method: "POST" });
      fillSystemConfigForm(config);
      C.setSuccess("默认配置已恢复");
    }

    (async () => {
      await loadSystemConfig();
      el.loadSystemConfigBtn?.addEventListener("click", () => loadSystemConfig().catch(C.setError));
      el.saveSystemConfigBtn?.addEventListener("click", () => saveSystemConfig().catch(C.setError));
      el.resetSystemConfigBtn?.addEventListener("click", () => resetSystemConfig().catch(C.setError));
      el.bootstrapBtn?.addEventListener("click", () => runBootstrap("/bootstrap").catch(C.setError));
      el.bootstrapDemoBtn?.addEventListener("click", () => runBootstrap("/bootstrap-demo").catch(C.setError));
    })().catch(C.setError);
  }

  function initLogs() {
    if (!C.initPage()) return;

    const el = {
      loadOperationLogsBtn: document.getElementById("loadOperationLogsBtn"),
      logModuleInput: document.getElementById("logModuleInput"),
      logOperatorKeywordInput: document.getElementById("logOperatorKeywordInput"),
      logMethodInput: document.getElementById("logMethodInput"),
      logStartTimeInput: document.getElementById("logStartTimeInput"),
      logEndTimeInput: document.getElementById("logEndTimeInput"),
      prevOperationLogsBtn: document.getElementById("prevOperationLogsBtn"),
      nextOperationLogsBtn: document.getElementById("nextOperationLogsBtn"),
      operationLogPageInfo: document.getElementById("operationLogPageInfo"),
      operationLogTbody: document.getElementById("operationLogTbody"),
    };

    const state = { skip: 0, limit: 20, total: 0 };

    function logQuery() {
      const query = new URLSearchParams();
      query.set("skip", String(state.skip));
      query.set("limit", String(state.limit));
      if (el.logModuleInput.value.trim()) query.set("module", el.logModuleInput.value.trim());
      if (el.logOperatorKeywordInput.value.trim()) query.set("operator_keyword", el.logOperatorKeywordInput.value.trim());
      if (el.logMethodInput.value) query.set("method", el.logMethodInput.value);
      const from = C.toIso(el.logStartTimeInput.value);
      const to = C.toIso(el.logEndTimeInput.value);
      if (from) query.set("start_time", from);
      if (to) query.set("end_time", to);
      return query.toString();
    }

    function renderLogs(data) {
      const items = Array.isArray(data?.items) ? data.items : [];
      state.total = Number(data?.total || 0);
      const page = Math.floor(state.skip / state.limit) + 1;
      el.operationLogPageInfo.textContent = `第 ${page} 页，共 ${state.total} 条`;
      el.prevOperationLogsBtn.disabled = state.skip <= 0;
      el.nextOperationLogsBtn.disabled = state.skip + state.limit >= state.total;
      if (!items.length) {
        el.operationLogTbody.innerHTML = '<tr><td colspan="9">暂无日志数据</td></tr>';
        return;
      }
      el.operationLogTbody.innerHTML = items.map((item) => {
        const statusClass = Number(item.status_code) >= 400 ? "danger" : "active";
        return `<tr>
          <td>${C.escapeHtml(item.operator_name || (item.operator_id ? `#${item.operator_id}` : "-"))}</td>
          <td>${C.escapeHtml(item.operator_role ? (window.roleText ? window.roleText(item.operator_role) : item.operator_role) : "-")}</td>
          <td>${C.escapeHtml(item.ip || "-")}</td>
          <td>${C.escapeHtml(item.module || "-")}</td>
          <td>${C.escapeHtml(item.request_method || "-")}</td>
          <td title="${C.escapeHtml(item.summary || item.request_path || "-")}">${C.escapeHtml(item.request_path || "-")}</td>
          <td>${C.statusTag(String(item.status_code || "-"), statusClass)}</td>
          <td>${C.escapeHtml(item.duration_ms != null ? `${item.duration_ms}ms` : "-")}</td>
          <td>${C.escapeHtml(C.fmtDate(item.created_at))}</td>
        </tr>`;
      }).join("");
    }

    async function loadOperationLogs() {
      const data = await C.request(`/operation-logs?${logQuery()}`);
      renderLogs(data);
    }

    (async () => {
      el.loadOperationLogsBtn?.addEventListener("click", () => {
        state.skip = 0;
        loadOperationLogs().catch(C.setError);
      });
      el.prevOperationLogsBtn?.addEventListener("click", () => {
        state.skip = Math.max(0, state.skip - state.limit);
        loadOperationLogs().catch(C.setError);
      });
      el.nextOperationLogsBtn?.addEventListener("click", () => {
        state.skip += state.limit;
        loadOperationLogs().catch(C.setError);
      });
      await loadOperationLogs();
    })().catch(C.setError);
  }

  window.AdminModules = {
    initDashboard,
    initStores,
    initResources,
    initOrders,
    initUsers,
    initConfig,
    initLogs,
  };
})();
