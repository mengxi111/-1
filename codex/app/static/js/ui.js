const ADMIN_API_BASE = "/api/admin";

const el = {
  authChecking: document.getElementById("authChecking"),
  refreshAllBtn: document.getElementById("refreshAllBtn"),
  logoutBtn: document.getElementById("logoutBtn"),
  currentUserText: document.getElementById("currentUserText"),
  currentRoleText: document.getElementById("currentRoleText"),
  statsDate: document.getElementById("statsDate"),

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

  loadStatsBtn: document.getElementById("loadStatsBtn"),
  metricBookingCount: document.getElementById("metricBookingCount"),
  metricCheckinCount: document.getElementById("metricCheckinCount"),
  metricRevenue: document.getElementById("metricRevenue"),
  metricOccupancyRate: document.getElementById("metricOccupancyRate"),
  metricNoShowCount: document.getElementById("metricNoShowCount"),
  metricIdleSeatCount: document.getElementById("metricIdleSeatCount"),
  trendBars: document.getElementById("trendBars"),
  sevenDayTrendChart: document.getElementById("sevenDayTrendChart"),
  hotSeatChart: document.getElementById("hotSeatChart"),

  loadCheckinStatsBtn: document.getElementById("loadCheckinStatsBtn"),
  metricTotalReservations: document.getElementById("metricTotalReservations"),
  metricCheckedInCount: document.getElementById("metricCheckedInCount"),
  metricMissedCheckins: document.getElementById("metricMissedCheckins"),
  metricCheckinRate: document.getElementById("metricCheckinRate"),
  checkinRateChart: document.getElementById("checkinRateChart"),

  bootstrapBtn: document.getElementById("bootstrapBtn"),
  bootstrapDemoBtn: document.getElementById("bootstrapDemoBtn"),
  loadResourceBtn: document.getElementById("loadResourceBtn"),
  resourceType: document.getElementById("resourceType"),
  resourceStatusInput: document.getElementById("resourceStatusInput"),
  resourceTableHeadRow: document.getElementById("resourceTableHeadRow"),
  resourceTableBody: document.getElementById("resourceTableBody"),

  loadOrdersBtn: document.getElementById("loadOrdersBtn"),
  exportOrdersBtn: document.getElementById("exportOrdersBtn"),
  searchOrdersBtn: document.getElementById("searchOrdersBtn"),
  resetOrdersBtn: document.getElementById("resetOrdersBtn"),
  orderStatusSelect: document.getElementById("orderStatusSelect"),
  orderStoreIdSelect: document.getElementById("orderStoreIdSelect"),
  orderKeywordInput: document.getElementById("orderKeywordInput"),
  orderDateFromInput: document.getElementById("orderDateFromInput"),
  orderDateToInput: document.getElementById("orderDateToInput"),
  orderListMeta: document.getElementById("orderListMeta"),
  orderTbody: document.getElementById("orderTbody"),
  orderDetailBox: document.getElementById("orderDetailBox"),

  loadUsersBtn: document.getElementById("loadUsersBtn"),
  searchUsersBtn: document.getElementById("searchUsersBtn"),
  resetUsersBtn: document.getElementById("resetUsersBtn"),
  userNameInput: document.getElementById("userNameInput"),
  userPhoneInput: document.getElementById("userPhoneInput"),
  userRoleSelect: document.getElementById("userRoleSelect"),
  userStatusSelect: document.getElementById("userStatusSelect"),
  userCreatedFromInput: document.getElementById("userCreatedFromInput"),
  userCreatedToInput: document.getElementById("userCreatedToInput"),
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
  adminOutput: document.getElementById("adminOutput"),
};

const state = {
  stores: [],
  config: null,
  selectedUser: null,
  userDetail: null,
  charts: {},
  orders: [],
  users: [],
  log: { skip: 0, limit: 20, total: 0 },
  storeEditMode: false,
};

const resourceConfig = {
  stores: { path: "/stores", columns: [["id", "编号"], ["name", "门店名称"], ["address", "地址"], ["status", "状态"]] },
  areas: { path: "/areas", columns: [["id", "编号"], ["store_id", "门店编号"], ["name", "区域名称"], ["code", "区域编码"]] },
  seats: { path: "/seats", columns: [["id", "编号"], ["store_id", "门店编号"], ["area_id", "区域编号"], ["seat_no", "座位号"], ["seat_type", "座位类型"], ["seat_status", "座位状态"]] },
  plans: { path: "/plans", columns: [["id", "编号"], ["store_id", "门店编号"], ["name", "方案名称"], ["billing_type", "计费方式"], ["price", "价格"], ["status", "状态"]] },
  bookings: { path: "/bookings", supportsStore: true, supportsStatus: true, columns: [["id", "预约编号"], ["user_id", "用户编号"], ["seat_no", "座位"], ["status", "状态"], ["start_time", "开始时间"], ["end_time", "结束时间"]] },
  checkins: { path: "/checkins/records", supportsStore: true, columns: [["id", "记录编号"], ["booking_id", "预约编号"], ["user_id", "用户编号"], ["seat_id", "座位编号"], ["checkin_time", "签到时间"], ["checkin_method", "签到方式"]] },
  blacklists: { path: "/blacklists", columns: [["id", "编号"], ["user_id", "用户编号"], ["reason", "原因"], ["source", "来源"], ["is_active", "生效中"], ["start_at", "开始时间"], ["end_at", "结束时间"]] },
  memberships: { path: "/memberships", columns: [["id", "编号"], ["user_id", "用户编号"], ["card_name", "会员卡"], ["card_type", "类型"], ["balance_minutes", "剩余分钟"], ["balance_times", "剩余次数"], ["status", "状态"]] },
  notices: { path: "/notices", supportsStore: true, supportsStatus: true, columns: [["id", "编号"], ["store_id", "门店编号"], ["title", "公告标题"], ["status", "状态"], ["published_at", "发布时间"], ["created_at", "创建时间"]] },
};

const authHeaders = (withJson = true) => {
  const headers = { Authorization: `Bearer ${window.getToken()}` };
  if (withJson) headers["Content-Type"] = "application/json";
  return headers;
};

const parseData = (text) => {
  try {
    return text ? JSON.parse(text) : null;
  } catch {
    return null;
  }
};

const escapeHtml = (value) => String(value ?? "")
  .replaceAll("&", "&amp;")
  .replaceAll("<", "&lt;")
  .replaceAll(">", "&gt;")
  .replaceAll('"', "&quot;")
  .replaceAll("'", "&#39;");

const fmtDate = (value) => {
  if (!value) return "-";
  const date = new Date(value);
  return Number.isNaN(date.getTime()) ? "-" : date.toLocaleString("zh-CN", { hour12: false });
};

const fmtMoney = (value) => `￥${Number(value || 0).toFixed(2)}`;

const toIso = (value) => {
  if (!value) return null;
  const date = new Date(value);
  return Number.isNaN(date.getTime()) ? null : date.toISOString();
};

const todayText = () => {
  const now = new Date();
  const y = now.getFullYear();
  const m = String(now.getMonth() + 1).padStart(2, "0");
  const d = String(now.getDate()).padStart(2, "0");
  return `${y}-${m}-${d}`;
};

const selectedStoreId = () => {
  const value = Number(el.storeId.value || 0);
  return Number.isFinite(value) && value > 0 ? value : null;
};

const selectedOrderStoreId = () => {
  const value = Number(el.orderStoreIdSelect.value || 0);
  return Number.isFinite(value) && value > 0 ? value : null;
};

const currentStore = () => state.stores.find((item) => item.id === selectedStoreId()) || null;
const currentUser = () => window.getUser();
const canEditStore = () => ["admin", "super_admin"].includes(currentUser()?.role || "");
const isSuperAdmin = () => currentUser()?.role === "super_admin";

function setResult(message, type = "info") {
  el.adminOutput.textContent = typeof message === "string" ? message : JSON.stringify(message, null, 2);
  el.adminOutput.className = `result result-${type}`;
}

function setSuccess(message) { setResult(message, "success"); }
function setError(error) { setResult(error?.message || window.t("errors.requestFailed"), "error"); }
function showPage() { document.body.classList.remove("page-hidden"); el.authChecking?.remove(); }
function statusTag(text, cls) { return `<span class="status-tag status-${cls}">${escapeHtml(text)}</span>`; }

function orderStatusTag(status) {
  const mapping = {
    pending: ["pending", window.statusText("pending")],
    paid: ["paid", window.statusText("paid")],
    cancelled: ["cancelled", window.statusText("cancelled")],
    refunded: ["refunded", window.statusText("refunded")],
  };
  const [cls, label] = mapping[status] || ["normal", status || "-"];
  return statusTag(label, cls);
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

function userStatusText(status) {
  if (Number(status) === 1) return window.t("admin.userStatusActive");
  if (Number(status) === 0) return window.t("admin.userStatusDisabled");
  return window.t("admin.userStatusDeleted");
}

function userStatusTag(status) {
  if (Number(status) === 1) return statusTag(window.t("admin.userStatusActive"), "active");
  if (Number(status) === 0) return statusTag(window.t("admin.userStatusDisabled"), "cancelled");
  return statusTag(window.t("admin.userStatusDeleted"), "deleted");
}

function blacklistTag(isBlacklisted, endAt = null) {
  if (!isBlacklisted) return statusTag(window.t("admin.userBlacklistInactive"), "normal");
  const suffix = endAt ? ` ${window.formatTemplate(window.t("admin.userBlacklistUntilTemplate"), { time: fmtDate(endAt) })}` : "";
  return statusTag(`${window.t("admin.userBlacklistActive")}${suffix}`, "blacklisted");
}

async function request(path, options = {}) {
  let response;
  try {
    response = await fetch(`${ADMIN_API_BASE}${path}`, {
      ...options,
      headers: { ...authHeaders(!(options.body instanceof FormData)), ...(options.headers || {}) },
    });
  } catch {
    throw new Error(window.t("errors.network"));
  }
  const text = await response.text();
  const payload = parseData(text);
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

function renderCurrentUser() {
  const user = currentUser();
  el.currentUserText.value = user ? `${user.nickname || user.name || "-"} #${user.id}` : window.t("errors.needLogin");
  el.currentRoleText.value = user ? window.roleText(user.role) : "-";
  el.toggleStoreEditBtn.disabled = !canEditStore() || !selectedStoreId();
  el.saveSystemConfigBtn.disabled = !isSuperAdmin();
  el.resetSystemConfigBtn.disabled = !isSuperAdmin();
  el.bootstrapBtn.disabled = !isSuperAdmin();
  el.bootstrapDemoBtn.disabled = !window.isAdminRole(user?.role || "");
}

function renderStoreOptions() {
  const options = [`<option value="">${window.t("admin.storeAll")}</option>`]
    .concat(state.stores.map((store) => `<option value="${store.id}">${escapeHtml(store.name)}</option>`))
    .join("");
  const currentStoreValue = el.storeId.value;
  const currentOrderValue = el.orderStoreIdSelect.value;
  el.storeId.innerHTML = options;
  el.orderStoreIdSelect.innerHTML = options;
  if (currentStoreValue) el.storeId.value = currentStoreValue;
  if (currentOrderValue) el.orderStoreIdSelect.value = currentOrderValue;
}

function fmtStoreHours(store) {
  return store ? `${String(store.open_time || "--:--").slice(0, 5)} - ${String(store.close_time || "--:--").slice(0, 5)}` : "-";
}

function toggleStoreEdit(enabled) {
  state.storeEditMode = enabled;
  el.storeViewMode.classList.toggle("hidden", enabled);
  el.storeEditMode.classList.toggle("hidden", !enabled);
  el.toggleStoreEditBtn.textContent = enabled ? window.t("admin.cancelStoreEdit") : window.t("admin.editStore");
}

function renderStoreDetails() {
  const store = currentStore();
  const defaultHours = state.config ? `${state.config.default_open_time} - ${state.config.default_close_time}` : "-";
  if (!store) {
    const text = state.stores.length ? window.t("admin.storeInfoAll") : window.t("admin.storeEmpty");
    el.storeSummaryBanner.textContent = text;
    el.storeDetailName.textContent = text;
    el.storeDetailDescription.textContent = state.stores.length ? window.t("admin.storeDescriptionEmpty") : window.t("admin.storeEmpty");
    el.storeDetailAddress.textContent = "-";
    el.storeDetailPhone.textContent = "-";
    el.storeDetailStatus.innerHTML = statusTag(window.t("admin.filterAll"), "normal");
    el.storeDetailHours.textContent = window.t("admin.storeAll");
    el.storeDetailHoursText.textContent = defaultHours;
    el.toggleStoreEditBtn.disabled = true;
    toggleStoreEdit(false);
    return;
  }
  el.storeSummaryBanner.textContent = store.name || "-";
  el.storeDetailName.textContent = store.name || "-";
  el.storeDetailDescription.textContent = String(store.description || "").trim() || window.t("admin.storeDescriptionEmpty");
  el.storeDetailAddress.textContent = store.address || "-";
  el.storeDetailPhone.textContent = store.contact_phone || "-";
  el.storeDetailStatus.innerHTML = Number(store.status) === 1 ? statusTag(window.t("admin.storeStatusOpen"), "active") : statusTag(window.t("admin.storeStatusClosed"), "cancelled");
  el.storeDetailHours.textContent = fmtStoreHours(store);
  el.storeDetailHoursText.textContent = fmtStoreHours(store);
  el.storeDescriptionInput.value = store.description || "";
  el.storeAddressInput.value = store.address || "";
  el.storePhoneInput.value = store.contact_phone || "";
  el.storeStatusInput.value = String(store.status ?? 1);
  el.storeOpenTimeInput.value = String(store.open_time || "").slice(0, 5);
  el.storeCloseTimeInput.value = String(store.close_time || "").slice(0, 5);
  el.toggleStoreEditBtn.disabled = !canEditStore();
}

async function loadStores() {
  const currentStoreValue = el.storeId.value;
  const currentOrderValue = el.orderStoreIdSelect.value;
  const data = await request("/stores");
  state.stores = Array.isArray(data) ? data : [];
  renderStoreOptions();
  if (currentStoreValue) el.storeId.value = currentStoreValue;
  if (currentOrderValue) el.orderStoreIdSelect.value = currentOrderValue;
  renderStoreDetails();
}

async function saveStoreInfo() {
  const store = currentStore();
  if (!store) throw new Error(window.t("admin.storeSelectFirst"));
  if (!canEditStore()) throw new Error(window.t("errors.forbidden"));
  const payload = {
    description: el.storeDescriptionInput.value.trim(),
    address: el.storeAddressInput.value.trim(),
    contact_phone: el.storePhoneInput.value.trim(),
    status: Number(el.storeStatusInput.value || 1),
    open_time: el.storeOpenTimeInput.value || state.config?.default_open_time || "08:00",
    close_time: el.storeCloseTimeInput.value || state.config?.default_close_time || "23:00",
  };
  const updated = await request(`/stores/${store.id}`, { method: "PUT", body: JSON.stringify(payload) });
  state.stores = state.stores.map((item) => (item.id === updated.id ? updated : item));
  renderStoreOptions();
  el.storeId.value = String(updated.id);
  renderStoreDetails();
  toggleStoreEdit(false);
  setSuccess(window.t("admin.storeSaveSuccess"));
}

function businessHours() {
  const store = currentStore();
  const openText = String(store?.open_time || state.config?.default_open_time || "08:00").slice(0, 5);
  const closeText = String(store?.close_time || state.config?.default_close_time || "23:00").slice(0, 5);
  const start = Number(openText.split(":")[0]);
  const end = Number(closeText.split(":")[0]);
  if (!Number.isFinite(start) || !Number.isFinite(end) || end <= start) return [];
  return Array.from({ length: end - start }, (_, index) => start + index);
}

function statsQuery() {
  const query = new URLSearchParams();
  if (selectedStoreId()) query.set("store_id", String(selectedStoreId()));
  if (el.statsDate.value) query.set("date", el.statsDate.value);
  return query.toString();
}

function ensureChart(key, node) {
  if (!node || typeof window.echarts === "undefined") return null;
  if (!state.charts[key]) state.charts[key] = window.echarts.init(node);
  return state.charts[key];
}

function emptyChart(chart) {
  chart.setOption({
    xAxis: { show: false, type: "category", data: [] },
    yAxis: { show: false, type: "value" },
    series: [],
    graphic: { type: "text", left: "center", top: "middle", style: { text: window.t("admin.statsNoData"), fill: "#7d4a37", fontSize: 14 } },
  }, true);
}

function resetOverviewMetrics() {
  el.metricBookingCount.textContent = "0";
  el.metricCheckinCount.textContent = "0";
  el.metricRevenue.textContent = fmtMoney(0);
  el.metricOccupancyRate.textContent = "0.00%";
  el.metricNoShowCount.textContent = "0";
  el.metricIdleSeatCount.textContent = "0";
}

function resetCheckinMetrics() {
  el.metricTotalReservations.textContent = "0";
  el.metricCheckedInCount.textContent = "0";
  el.metricMissedCheckins.textContent = "0";
  el.metricCheckinRate.textContent = "0.00%";
}

function renderTrend(items) {
  const list = Array.isArray(items) ? items : [];
  const hours = businessHours();
  const filtered = hours.length ? list.filter((item) => hours.includes(Number(item.hour))) : list;
  if (!filtered.length) {
    el.trendBars.innerHTML = `<div class="trend-empty">${window.t("admin.statsNoData")}</div>`;
    return;
  }
  const max = Math.max(...filtered.map((item) => Number(item.occupied_seats || 0)), 1);
  el.trendBars.innerHTML = filtered.map((item) => {
    const value = Number(item.occupied_seats || 0);
    const height = Math.max(12, Math.round((value / max) * 130));
    const hour = String(item.hour).padStart(2, "0");
    return `<div class="bar-item" title="${window.formatTemplate(window.t("admin.chartHourlyTooltip"), { hour: `${hour}:00`, value })}"><div class="bar" data-hour="${hour}" style="height:${height}px"></div></div>`;
  }).join("");
}

function renderSevenDay(items) {
  const chart = ensureChart("sevenDay", el.sevenDayTrendChart);
  if (!chart) return;
  if (!Array.isArray(items) || !items.length) return emptyChart(chart);
  chart.setOption({
    tooltip: { trigger: "axis" },
    legend: { data: [window.t("admin.chartBookingsLegend"), window.t("admin.chartRevenueLegend")] },
    grid: { left: 40, right: 40, top: 46, bottom: 28 },
    xAxis: { type: "category", data: items.map((item) => item.date?.slice(5) || item.date || "-") },
    yAxis: [{ type: "value", name: window.t("admin.chartBookingsLegend"), minInterval: 1 }, { type: "value", name: window.t("admin.chartRevenueLegend"), min: 0 }],
    series: [
      { name: window.t("admin.chartBookingsLegend"), type: "line", smooth: true, yAxisIndex: 0, data: items.map((item) => Number(item.booking_count || 0)), lineStyle: { width: 3, color: "#2563eb" }, itemStyle: { color: "#2563eb" } },
      { name: window.t("admin.chartRevenueLegend"), type: "bar", yAxisIndex: 1, data: items.map((item) => Number(item.revenue || 0)), itemStyle: { color: "#16a34a" } },
    ],
  }, true);
}

function renderHotSeat(items) {
  const chart = ensureChart("hotSeat", el.hotSeatChart);
  if (!chart) return;
  const list = Array.isArray(items) ? items.slice(0, 5) : [];
  if (!list.length) return emptyChart(chart);
  chart.setOption({
    tooltip: { trigger: "axis", axisPointer: { type: "shadow" } },
    grid: { left: 90, right: 24, top: 18, bottom: 18 },
    xAxis: { type: "value", minInterval: 1 },
    yAxis: { type: "category", data: list.map((item) => item.seat_no || `座位${item.seat_id}`) },
    series: [{ name: window.t("admin.chartHotSeatLegend"), type: "bar", data: list.map((item) => Number(item.booking_count || 0)), itemStyle: { color: "#ea580c" }, label: { show: true, position: "right" } }],
  }, true);
}

function renderCheckinChart(data) {
  const chart = ensureChart("checkin", el.checkinRateChart);
  if (!chart) return;
  const items = Array.isArray(data?.hourly_checkin_trend) ? data.hourly_checkin_trend : [];
  if (!items.length) return emptyChart(chart);
  chart.setOption({
    tooltip: { trigger: "axis" },
    legend: { data: [window.t("admin.checkinChartChecked"), window.t("admin.checkinChartRate")] },
    grid: { left: 40, right: 40, top: 46, bottom: 28 },
    xAxis: { type: "category", data: items.map((item) => `${String(item.hour).padStart(2, "0")}:00`) },
    yAxis: [{ type: "value", name: window.t("admin.checkinChartChecked"), minInterval: 1 }, { type: "value", name: window.t("admin.checkinChartRate"), min: 0, max: 100 }],
    series: [
      { name: window.t("admin.checkinChartChecked"), type: "bar", yAxisIndex: 0, data: items.map((item) => Number(item.checked_in_count || 0)), itemStyle: { color: "#0f766e" } },
      { name: window.t("admin.checkinChartRate"), type: "line", smooth: true, yAxisIndex: 1, data: items.map((item) => Number(item.checkin_rate || 0)), lineStyle: { width: 3, color: "#ea580c" }, itemStyle: { color: "#ea580c" } },
    ],
  }, true);
}

async function loadStats() {
  try {
    const data = await request(`/stats/overview?${statsQuery()}`);
    el.metricBookingCount.textContent = String(Number(data?.today_booking_count || 0));
    el.metricCheckinCount.textContent = String(Number(data?.today_checkin_count || 0));
    el.metricRevenue.textContent = fmtMoney(data?.today_revenue || 0);
    el.metricOccupancyRate.textContent = `${Number(data?.current_occupancy_rate || 0).toFixed(2)}%`;
    el.metricNoShowCount.textContent = String(Number(data?.today_no_show_count || 0));
    el.metricIdleSeatCount.textContent = String(Number(data?.current_idle_seat_count || 0));
    renderTrend(data?.hourly_occupancy_trend || []);
    renderSevenDay(data?.recent_7_day_trend || []);
    renderHotSeat(data?.hot_seat_rank || []);
  } catch (error) {
    resetOverviewMetrics();
    renderTrend([]);
    const sevenDayChart = ensureChart("sevenDay", el.sevenDayTrendChart); if (sevenDayChart) emptyChart(sevenDayChart);
    const hotSeatChart = ensureChart("hotSeat", el.hotSeatChart); if (hotSeatChart) emptyChart(hotSeatChart);
    throw error;
  }
}

async function loadCheckinStats() {
  try {
    const data = await request(`/checkins/stats?${statsQuery()}`);
    el.metricTotalReservations.textContent = String(Number(data?.total_reservations || 0));
    el.metricCheckedInCount.textContent = String(Number(data?.checked_in_count || 0));
    el.metricMissedCheckins.textContent = String(Number(data?.missed_checkin_count || 0));
    el.metricCheckinRate.textContent = `${Number(data?.checkin_rate || 0).toFixed(2)}%`;
    renderCheckinChart(data);
  } catch (error) {
    resetCheckinMetrics();
    const checkinChart = ensureChart("checkin", el.checkinRateChart); if (checkinChart) emptyChart(checkinChart);
    throw error;
  }
}
function initResourceTypeOptions() {
  const options = Object.keys(resourceConfig).map((key) => `<option value="${key}">${escapeHtml(window.resourceTypeText(key))}</option>`).join("");
  el.resourceType.innerHTML = options;
}

function formatResourceCell(key, value) {
  if (value === null || value === undefined || value === "") return "-";
  if (["created_at", "updated_at", "start_time", "end_time", "published_at", "start_at", "end_at", "checkin_time"].includes(key)) return fmtDate(value);
  if (key === "status") {
    if (["pending", "paid", "cancelled", "refunded"].includes(String(value))) return orderStatusTag(String(value));
    return bookingStatusTag(String(value));
  }
  if (key === "seat_type") return escapeHtml(window.seatTypeText(value));
  if (key === "seat_status") {
    const statusMap = { available: statusTag("可用", "active"), maintenance: statusTag("维修", "danger"), disabled: statusTag("禁用", "cancelled") };
    return statusMap[value] || escapeHtml(value);
  }
  if (key === "billing_type") {
    const billingMap = { hour: "按小时", day: "按天", month: "包月" };
    return escapeHtml(billingMap[value] || value);
  }
  if (key === "is_active" || key === "is_available") return value ? statusTag("是", "active") : statusTag("否", "cancelled");
  if (key === "price") return fmtMoney(value);
  return escapeHtml(value);
}

function renderResourceTable(items) {
  const config = resourceConfig[el.resourceType.value];
  const rows = Array.isArray(items) ? items : [];
  el.resourceTableHeadRow.innerHTML = config.columns.map(([, label]) => `<th>${escapeHtml(label)}</th>`).join("");
  if (!rows.length) {
    el.resourceTableBody.innerHTML = `<tr><td colspan="${config.columns.length}">${window.t("admin.resourceEmpty")}</td></tr>`;
    return;
  }
  el.resourceTableBody.innerHTML = rows.map((row) => `<tr>${config.columns.map(([key]) => `<td>${formatResourceCell(key, row[key])}</td>`).join("")}</tr>`).join("");
}

function resourceQuery() {
  const config = resourceConfig[el.resourceType.value];
  const query = new URLSearchParams();
  if (config.supportsStore && selectedStoreId()) query.set("store_id", String(selectedStoreId()));
  if (config.supportsStatus && el.resourceStatusInput.value.trim()) query.set("status", el.resourceStatusInput.value.trim());
  return query.toString();
}

async function loadResourceData() {
  const config = resourceConfig[el.resourceType.value];
  if (!config) return;
  const query = resourceQuery();
  const data = await request(`${config.path}${query ? `?${query}` : ""}`);
  const rows = Array.isArray(data) ? data : Array.isArray(data?.items) ? data.items : [];
  renderResourceTable(rows);
}

function orderQuery() {
  const query = new URLSearchParams();
  if (selectedOrderStoreId()) query.set("store_id", String(selectedOrderStoreId()));
  if (el.orderStatusSelect.value) query.set("status", el.orderStatusSelect.value);
  if (el.orderKeywordInput.value.trim()) query.set("keyword", el.orderKeywordInput.value.trim());
  const from = toIso(el.orderDateFromInput.value);
  const to = toIso(el.orderDateToInput.value);
  if (from) query.set("date_from", from);
  if (to) query.set("date_to", to);
  return query.toString();
}

function renderOrderDetail(item) {
  if (!item) {
    el.orderDetailBox.className = "detail-box empty";
    el.orderDetailBox.textContent = window.t("admin.orderDetailDefault");
    return;
  }
  el.orderDetailBox.className = "detail-box";
  el.orderDetailBox.innerHTML = `
    <h3>${escapeHtml(window.t("admin.orderDetailTitle"))}</h3>
    <dl class="dialog-grid">
      <div><span>${escapeHtml(window.t("admin.orderTableId"))}</span><strong>${escapeHtml(item.id)}</strong></div>
      <div><span>${escapeHtml(window.t("admin.orderTableBookingId"))}</span><strong>${escapeHtml(item.booking_id)}</strong></div>
      <div><span>${escapeHtml(window.t("admin.orderTableStore"))}</span><strong>${escapeHtml(item.store_name || "-")}</strong></div>
      <div><span>${escapeHtml(window.t("admin.orderTableSeat"))}</span><strong>${escapeHtml(item.seat_no || "-")}</strong></div>
      <div><span>${escapeHtml(window.t("admin.orderTableUser"))}</span><strong>${escapeHtml(item.user_name || item.user_id)}</strong></div>
      <div><span>${escapeHtml(window.t("admin.userTablePhone"))}</span><strong>${escapeHtml(item.user_phone || "-")}</strong></div>
      <div><span>${escapeHtml(window.t("admin.orderTableAmount"))}</span><strong>${escapeHtml(fmtMoney(item.amount || 0))}</strong></div>
      <div><span>${escapeHtml(window.t("admin.orderTableStatus"))}</span><strong>${orderStatusTag(item.status)}</strong></div>
      <div><span>${escapeHtml(window.t("common.start"))}</span><strong>${escapeHtml(fmtDate(item.start_time))}</strong></div>
      <div><span>${escapeHtml(window.t("common.end"))}</span><strong>${escapeHtml(fmtDate(item.end_time))}</strong></div>
      <div><span>${escapeHtml(window.t("admin.orderTableCreatedAt"))}</span><strong>${escapeHtml(fmtDate(item.created_at))}</strong></div>
      <div><span>${escapeHtml(window.t("admin.userBookingTableStatus"))}</span><strong>${bookingStatusTag(item.booking_status)}</strong></div>
    </dl>`;
}

function renderOrders(items, total) {
  const rows = Array.isArray(items) ? items : [];
  el.orderListMeta.textContent = window.formatTemplate(window.t("admin.orderListCountTemplate"), { count: total ?? rows.length });
  if (!rows.length) {
    el.orderTbody.innerHTML = `<tr><td colspan="8">${window.t("admin.noOrders")}</td></tr>`;
    renderOrderDetail(null);
    return;
  }
  el.orderTbody.innerHTML = rows.map((item) => {
    const actions = [`<button class="btn btn-inline" data-action="detail" data-id="${item.id}">${window.t("admin.orderActionDetail")}</button>`];
    if (item.status === "pending") {
      actions.push(`<button class="btn btn-inline" data-action="paid" data-id="${item.id}">${window.t("admin.orderActionPaid")}</button>`);
      actions.push(`<button class="btn btn-inline" data-action="cancel" data-id="${item.id}">${window.t("admin.orderActionCancel")}</button>`);
    }
    if (item.status === "paid") actions.push(`<button class="btn btn-inline" data-action="refund" data-id="${item.id}">${window.t("admin.orderActionRefund")}</button>`);
    return `<tr>
      <td>${item.id}</td>
      <td>${escapeHtml(item.store_name || "-")}</td>
      <td>${escapeHtml(item.seat_no || "-")}</td>
      <td>${escapeHtml(item.user_name || item.user_id)}</td>
      <td>${escapeHtml(fmtMoney(item.amount || 0))}</td>
      <td>${orderStatusTag(item.status)}</td>
      <td>${escapeHtml(fmtDate(item.created_at))}</td>
      <td>${actions.join("")}</td>
    </tr>`;
  }).join("");
}

async function loadOrders() {
  const query = orderQuery();
  const data = await request(`/orders${query ? `?${query}` : ""}`);
  const items = Array.isArray(data?.items) ? data.items : [];
  state.orders = items;
  renderOrders(items, Number(data?.total || 0));
}

async function showOrderDetail(orderId) {
  const detail = await request(`/orders/${orderId}`);
  renderOrderDetail(detail);
}

async function doOrderAction(orderId, action) {
  const actionMap = {
    cancel: { path: `/orders/${orderId}/cancel`, confirm: window.t("admin.orderActionCancelConfirm"), label: window.t("admin.orderActionCancel") },
    paid: { path: `/orders/${orderId}/paid`, confirm: window.t("admin.orderActionPaidConfirm"), label: window.t("admin.orderActionPaid") },
    refund: { path: `/orders/${orderId}/refund`, confirm: window.t("admin.orderActionRefundConfirm"), label: window.t("admin.orderActionRefund") },
  };
  const config = actionMap[action];
  if (!config) return;
  if (!window.confirm(config.confirm)) return;
  await request(config.path, { method: "POST" });
  await loadOrders();
  await showOrderDetail(orderId);
  setSuccess(window.formatTemplate(window.t("admin.orderActionSuccessTemplate"), { action: config.label }));
}

async function exportOrders() {
  const query = orderQuery();
  let response;
  try {
    response = await fetch(`${ADMIN_API_BASE}/orders/export${query ? `?${query}` : ""}`, { headers: authHeaders(false) });
  } catch {
    throw new Error(window.t("errors.network"));
  }
  if (!response.ok) {
    const text = await response.text();
    const payload = parseData(text);
    throw new Error(payload?.message || window.t("admin.orderLoadFailed"));
  }
  const blob = await response.blob();
  const url = URL.createObjectURL(blob);
  const link = document.createElement("a");
  link.href = url;
  link.download = `orders_${Date.now()}.csv`;
  document.body.append(link);
  link.click();
  link.remove();
  URL.revokeObjectURL(url);
  setSuccess(window.t("admin.orderExportSuccess"));
}

function userQuery() {
  const query = new URLSearchParams();
  if (el.userNameInput.value.trim()) query.set("name", el.userNameInput.value.trim());
  if (el.userPhoneInput.value.trim()) query.set("phone", el.userPhoneInput.value.trim());
  if (el.userRoleSelect.value) query.set("role", el.userRoleSelect.value);
  if (el.userStatusSelect.value) query.set("status", el.userStatusSelect.value);
  const from = toIso(el.userCreatedFromInput.value);
  const to = toIso(el.userCreatedToInput.value);
  if (from) query.set("created_from", from);
  if (to) query.set("created_to", to);
  return query.toString();
}

function findUserInState(userId) {
  return state.users.find((item) => Number(item.id) === Number(userId)) || null;
}

function renderUsers(users) {
  const rows = Array.isArray(users) ? users : [];
  el.userListMeta.textContent = window.formatTemplate(window.t("admin.userListCountTemplate"), { count: rows.length });
  if (!rows.length) {
    el.userTbody.innerHTML = `<tr><td colspan="11">${window.t("common.noData")}</td></tr>`;
    return;
  }
  el.userTbody.innerHTML = rows.map((user) => {
    const actions = [
      `<button class="btn btn-inline" data-action="detail" data-id="${user.id}">${window.t("admin.userActionViewDetail")}</button>`,
      `<button class="btn btn-inline" data-action="bookings" data-id="${user.id}">${window.t("admin.userActionViewBookings")}</button>`,
    ];
    if (Number(user.status) === 1) actions.push(`<button class="btn btn-inline" data-action="freeze" data-id="${user.id}">${window.t("admin.userActionFreeze")}</button>`);
    if (Number(user.status) === 0) actions.push(`<button class="btn btn-inline" data-action="unfreeze" data-id="${user.id}">${window.t("admin.userActionUnfreeze")}</button>`);
    actions.push(`<button class="btn btn-inline" data-action="blacklist" data-id="${user.id}">${user.is_blacklisted ? window.t("admin.userActionRemoveBlacklist") : window.t("admin.userActionBlacklist")}</button>`);
    actions.push(`<button class="btn btn-inline" data-action="delete" data-id="${user.id}">${window.t("admin.userActionDelete")}</button>`);
    return `<tr>
      <td>${user.id}</td>
      <td>${escapeHtml(user.name || "-")}</td>
      <td>${escapeHtml(user.phone || "-")}</td>
      <td>${escapeHtml(user.email || "-")}</td>
      <td>${escapeHtml(window.roleText(user.role))}</td>
      <td>${userStatusTag(user.status)}</td>
      <td>${escapeHtml(user.no_show_count || 0)}</td>
      <td>${blacklistTag(user.is_blacklisted, user.blacklist_end_at)}</td>
      <td>${escapeHtml(user.history_booking_count || 0)}</td>
      <td>${escapeHtml(fmtDate(user.created_at))}</td>
      <td>${actions.join("")}</td>
    </tr>`;
  }).join("");
}

async function loadUsers() {
  const query = userQuery();
  const users = await request(`/users${query ? `?${query}` : ""}`);
  state.users = Array.isArray(users) ? users : [];
  renderUsers(state.users);
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

function renderUserDetail(detail) {
  const blacklistStatus = detail.is_blacklisted
    ? `${window.t("admin.userBlacklistActive")}${detail.blacklist_end_at ? `（${fmtDate(detail.blacklist_end_at)}）` : ""}`
    : window.t("admin.userBlacklistInactive");
  el.userDetailContent.innerHTML = `
    <div><span>${escapeHtml(window.t("admin.userTableName"))}</span><strong>${escapeHtml(detail.name || "-")}</strong></div>
    <div><span>${escapeHtml(window.t("admin.userDetailPhone"))}</span><strong>${escapeHtml(detail.phone || "-")}</strong></div>
    <div><span>${escapeHtml(window.t("admin.userDetailEmail"))}</span><strong>${escapeHtml(detail.email || "-")}</strong></div>
    <div><span>${escapeHtml(window.t("admin.userDetailRole"))}</span><strong>${escapeHtml(window.roleText(detail.role))}</strong></div>
    <div><span>${escapeHtml(window.t("admin.userDetailStatus"))}</span><strong>${escapeHtml(userStatusText(detail.status))}</strong></div>
    <div><span>${escapeHtml(window.t("admin.userDetailCreatedAt"))}</span><strong>${escapeHtml(fmtDate(detail.created_at))}</strong></div>
    <div><span>${escapeHtml(window.t("admin.userDetailNoShow"))}</span><strong>${escapeHtml(detail.no_show_count || 0)}</strong></div>
    <div><span>${escapeHtml(window.t("admin.userDetailBlacklist"))}</span><strong>${escapeHtml(blacklistStatus)}</strong></div>
    <div><span>${escapeHtml(window.t("admin.userDetailHistoryCount"))}</span><strong>${escapeHtml(detail.history_booking_count || 0)}</strong></div>
    <div><span>${escapeHtml(window.t("admin.userDetailLastBookingAt"))}</span><strong>${escapeHtml(fmtDate(detail.last_booking_at))}</strong></div>`;
  el.toggleUserBlacklistBtn.textContent = detail.is_blacklisted ? window.t("admin.userActionRemoveBlacklist") : window.t("admin.userActionBlacklist");
}

async function openUserDetail(userId) {
  const detail = await request(`/users/${userId}/detail`);
  state.userDetail = detail;
  renderUserDetail(detail);
  openDialog(el.userDetailDialog);
}

async function loadUserBookings() {
  if (!state.selectedUser) {
    el.userBookingsMeta.textContent = window.t("admin.userBookingsSelectFirst");
    el.userBookingsTbody.innerHTML = `<tr><td colspan="6">${window.t("admin.userBookingsSelectFirst")}</td></tr>`;
    return;
  }
  const bookings = await request(`/bookings?user_id=${state.selectedUser.id}&limit=100`);
  const rows = Array.isArray(bookings) ? bookings : [];
  el.userBookingsMeta.textContent = window.formatTemplate(window.t("admin.userBookingsMetaTemplate"), { name: state.selectedUser.name || "-", id: state.selectedUser.id });
  if (!rows.length) {
    el.userBookingsTbody.innerHTML = `<tr><td colspan="6">${window.t("admin.userBookingsEmpty")}</td></tr>`;
    return;
  }
  const storeMap = new Map(state.stores.map((item) => [item.id, item]));
  el.userBookingsTbody.innerHTML = rows.map((item) => {
    const store = storeMap.get(item.store_id);
    return `<tr>
      <td>${item.id}</td>
      <td>${escapeHtml(store?.name || `门店#${item.store_id || "-"}`)}</td>
      <td>${escapeHtml(item.seat_no || "-")}</td>
      <td>${escapeHtml(fmtDate(item.start_time))}</td>
      <td>${escapeHtml(fmtDate(item.end_time))}</td>
      <td>${bookingStatusTag(item.status)}</td>
    </tr>`;
  }).join("");
}

async function setSelectedUser(userId) {
  const user = findUserInState(userId);
  state.selectedUser = user || { id: userId, name: `用户#${userId}` };
  await loadUserBookings();
  const section = el.userBookingsMeta.closest("section");
  section?.scrollIntoView({ behavior: "smooth", block: "start" });
}

async function toggleBlacklistForUser(userId, currentlyBlacklisted) {
  if (currentlyBlacklisted) {
    await request(`/blacklists/${userId}`, { method: "DELETE" });
    setSuccess(window.t("admin.userBlacklistRemoveSuccess"));
  } else {
    await request("/blacklists", { method: "POST", body: JSON.stringify({ user_id: userId, reason: "管理员手动加入黑名单" }) });
    setSuccess(window.t("admin.userBlacklistAddSuccess"));
  }
  await loadUsers();
  if (state.userDetail && Number(state.userDetail.id) === Number(userId)) await openUserDetail(userId);
}

async function doUserAction(userId, action) {
  const user = findUserInState(userId);
  if (!user) return;
  if (action === "detail") return openUserDetail(userId);
  if (action === "bookings") return setSelectedUser(userId);
  if (action === "blacklist") return toggleBlacklistForUser(userId, user.is_blacklisted);
  if (action === "freeze") {
    if (!window.confirm(window.t("admin.userFreezeConfirm"))) return;
    await request(`/users/${userId}/freeze`, { method: "POST" });
    setSuccess(window.t("admin.userFreezeSuccess"));
    return loadUsers();
  }
  if (action === "unfreeze") {
    if (!window.confirm(window.t("admin.userUnfreezeConfirm"))) return;
    await request(`/users/${userId}/unfreeze`, { method: "POST" });
    setSuccess(window.t("admin.userUnfreezeSuccess"));
    return loadUsers();
  }
  if (action === "delete") {
    if (!window.confirm(window.t("admin.userDeleteConfirm"))) return;
    await request(`/users/${userId}`, { method: "DELETE" });
    setSuccess(window.t("admin.userDeleteSuccess"));
    if (state.selectedUser && Number(state.selectedUser.id) === Number(userId)) {
      state.selectedUser = null;
      await loadUserBookings();
    }
    return loadUsers();
  }
}

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

async function loadSystemConfig() {
  const config = await request("/system-config");
  state.config = config;
  fillSystemConfigForm(config);
  renderStoreDetails();
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

async function saveSystemConfig() {
  const config = await request("/system-config", { method: "PUT", body: JSON.stringify(systemConfigPayload()) });
  state.config = config;
  fillSystemConfigForm(config);
  renderStoreDetails();
  setSuccess(window.t("admin.configSaveSuccess"));
}

async function resetSystemConfig() {
  if (!window.confirm(window.t("admin.configResetConfirm"))) return;
  const config = await request("/system-config/reset", { method: "POST" });
  state.config = config;
  fillSystemConfigForm(config);
  renderStoreDetails();
  setSuccess(window.t("admin.configResetSuccess"));
}

function logQuery() {
  const query = new URLSearchParams();
  query.set("skip", String(state.log.skip));
  query.set("limit", String(state.log.limit));
  if (el.logModuleInput.value.trim()) query.set("module", el.logModuleInput.value.trim());
  if (el.logOperatorKeywordInput.value.trim()) query.set("operator_keyword", el.logOperatorKeywordInput.value.trim());
  if (el.logMethodInput.value) query.set("method", el.logMethodInput.value);
  const from = toIso(el.logStartTimeInput.value);
  const to = toIso(el.logEndTimeInput.value);
  if (from) query.set("start_time", from);
  if (to) query.set("end_time", to);
  return query.toString();
}

function renderLogs(data) {
  const items = Array.isArray(data?.items) ? data.items : [];
  state.log.total = Number(data?.total || 0);
  const page = Math.floor(state.log.skip / state.log.limit) + 1;
  el.operationLogPageInfo.textContent = window.formatTemplate(window.t("admin.logPageInfo"), { page, total: state.log.total });
  el.prevOperationLogsBtn.disabled = state.log.skip <= 0;
  el.nextOperationLogsBtn.disabled = state.log.skip + state.log.limit >= state.log.total;
  if (!items.length) {
    el.operationLogTbody.innerHTML = `<tr><td colspan="9">${window.t("admin.logsNoData")}</td></tr>`;
    return;
  }
  el.operationLogTbody.innerHTML = items.map((item) => {
    const statusClass = Number(item.status_code) >= 400 ? "danger" : "active";
    return `<tr>
      <td>${escapeHtml(item.operator_name || (item.operator_id ? `#${item.operator_id}` : "-"))}</td>
      <td>${escapeHtml(item.operator_role ? window.roleText(item.operator_role) : "-")}</td>
      <td>${escapeHtml(item.ip || "-")}</td>
      <td>${escapeHtml(item.module || "-")}</td>
      <td>${escapeHtml(item.request_method || "-")}</td>
      <td title="${escapeHtml(item.summary || item.request_path || "-")}">${escapeHtml(item.request_path || "-")}</td>
      <td>${statusTag(String(item.status_code || "-"), statusClass)}</td>
      <td>${escapeHtml(item.duration_ms != null ? `${item.duration_ms}ms` : "-")}</td>
      <td>${escapeHtml(fmtDate(item.created_at))}</td>
    </tr>`;
  }).join("");
}

async function loadOperationLogs() {
  const data = await request(`/operation-logs?${logQuery()}`);
  renderLogs(data);
}

async function runBootstrap(path) {
  const result = await request(path, { method: "POST" });
  setSuccess(result?.message || window.t("admin.outputDefault"));
  await refreshAll();
}

function initDefaults() {
  el.statsDate.value = todayText();
  initResourceTypeOptions();
  if (!el.resourceType.value) el.resourceType.value = "stores";
}

async function refreshAll() {
  renderCurrentUser();
  const failures = [];
  try { await loadSystemConfig(); } catch (error) { failures.push(error); }
  try { await loadStores(); } catch (error) { failures.push(error); }
  const tasks = [
    loadStats().catch((error) => failures.push(new Error(window.t("admin.statsLoadFailed") || error.message))),
    loadCheckinStats().catch((error) => failures.push(error)),
    loadResourceData().catch((error) => failures.push(new Error(window.t("admin.resourceLoadFailed") || error.message))),
    loadOrders().catch((error) => failures.push(new Error(window.t("admin.orderLoadFailed") || error.message))),
    loadUsers().catch((error) => failures.push(error)),
    loadOperationLogs().catch((error) => failures.push(error)),
  ];
  if (state.selectedUser) tasks.push(loadUserBookings().catch((error) => failures.push(error))); else loadUserBookings();
  await Promise.all(tasks);
  if (failures.length) setError(failures[0]);
}
function bindEvents() {
  el.logoutBtn?.addEventListener("click", () => {
    window.clearSession();
    window.location.replace("/auth/login");
  });
  el.refreshAllBtn?.addEventListener("click", () => refreshAll().catch(setError));
  el.loadStoresBtn?.addEventListener("click", () => loadStores().catch(setError));
  el.storeId?.addEventListener("change", async () => {
    renderStoreDetails();
    await Promise.allSettled([loadStats(), loadCheckinStats(), loadResourceData(), loadOrders()]);
  });
  el.toggleStoreEditBtn?.addEventListener("click", () => {
    if (!selectedStoreId()) {
      setError(new Error(window.t("admin.storeSelectFirst")));
      return;
    }
    if (!canEditStore()) {
      setError(new Error(window.t("errors.forbidden")));
      return;
    }
    toggleStoreEdit(!state.storeEditMode);
  });
  el.cancelStoreEditBtn?.addEventListener("click", () => {
    toggleStoreEdit(false);
    renderStoreDetails();
  });
  el.saveStoreInfoBtn?.addEventListener("click", () => saveStoreInfo().catch(setError));

  el.loadStatsBtn?.addEventListener("click", () => loadStats().catch((error) => setError(new Error(window.t("admin.statsLoadFailed") || error.message))));
  el.loadCheckinStatsBtn?.addEventListener("click", () => loadCheckinStats().catch(setError));

  el.bootstrapBtn?.addEventListener("click", () => runBootstrap("/bootstrap").catch(setError));
  el.bootstrapDemoBtn?.addEventListener("click", () => runBootstrap("/bootstrap-demo").catch(setError));
  el.loadResourceBtn?.addEventListener("click", () => loadResourceData().catch(setError));
  el.resourceType?.addEventListener("change", () => loadResourceData().catch(setError));

  el.loadOrdersBtn?.addEventListener("click", () => loadOrders().catch(setError));
  el.searchOrdersBtn?.addEventListener("click", () => loadOrders().catch(setError));
  el.resetOrdersBtn?.addEventListener("click", () => {
    el.orderStatusSelect.value = "";
    el.orderStoreIdSelect.value = "";
    el.orderKeywordInput.value = "";
    el.orderDateFromInput.value = "";
    el.orderDateToInput.value = "";
    loadOrders().catch(setError);
  });
  el.exportOrdersBtn?.addEventListener("click", () => exportOrders().catch(setError));
  el.orderTbody?.addEventListener("click", async (event) => {
    const target = event.target;
    if (!(target instanceof HTMLElement)) return;
    const button = target.closest("button[data-action]");
    if (!button) return;
    const orderId = Number(button.dataset.id || 0);
    const action = button.dataset.action;
    if (!orderId || !action) return;
    try {
      if (action === "detail") await showOrderDetail(orderId);
      else await doOrderAction(orderId, action);
    } catch (error) {
      setError(error);
    }
  });

  el.loadUsersBtn?.addEventListener("click", () => loadUsers().catch(setError));
  el.searchUsersBtn?.addEventListener("click", () => loadUsers().catch(setError));
  el.resetUsersBtn?.addEventListener("click", () => {
    el.userNameInput.value = "";
    el.userPhoneInput.value = "";
    el.userRoleSelect.value = "";
    el.userStatusSelect.value = "";
    el.userCreatedFromInput.value = "";
    el.userCreatedToInput.value = "";
    loadUsers().catch(setError);
  });
  el.userTbody?.addEventListener("click", async (event) => {
    const target = event.target;
    if (!(target instanceof HTMLElement)) return;
    const button = target.closest("button[data-action]");
    if (!button) return;
    const userId = Number(button.dataset.id || 0);
    const action = button.dataset.action;
    if (!userId || !action) return;
    try {
      await doUserAction(userId, action);
    } catch (error) {
      setError(error);
    }
  });
  el.reloadUserBookingsBtn?.addEventListener("click", () => loadUserBookings().catch(setError));
  el.closeUserDetailBtn?.addEventListener("click", () => closeDialog(el.userDetailDialog));
  el.viewUserBookingsBtn?.addEventListener("click", async () => {
    if (!state.userDetail) return;
    try {
      closeDialog(el.userDetailDialog);
      await setSelectedUser(state.userDetail.id);
    } catch (error) {
      setError(error);
    }
  });
  el.toggleUserBlacklistBtn?.addEventListener("click", async () => {
    if (!state.userDetail) return;
    try {
      await toggleBlacklistForUser(state.userDetail.id, state.userDetail.is_blacklisted);
    } catch (error) {
      setError(error);
    }
  });

  el.loadSystemConfigBtn?.addEventListener("click", () => loadSystemConfig().catch(setError));
  el.saveSystemConfigBtn?.addEventListener("click", () => saveSystemConfig().catch(setError));
  el.resetSystemConfigBtn?.addEventListener("click", () => resetSystemConfig().catch(setError));

  el.loadOperationLogsBtn?.addEventListener("click", () => {
    state.log.skip = 0;
    loadOperationLogs().catch(setError);
  });
  el.prevOperationLogsBtn?.addEventListener("click", () => {
    state.log.skip = Math.max(0, state.log.skip - state.log.limit);
    loadOperationLogs().catch(setError);
  });
  el.nextOperationLogsBtn?.addEventListener("click", () => {
    state.log.skip += state.log.limit;
    loadOperationLogs().catch(setError);
  });
}

async function bootstrapPage() {
  window.applyI18n(document);
  if (!window.ensureAdminPageGuard()) return;
  initDefaults();
  renderCurrentUser();
  bindEvents();
  try {
    await refreshAll();
  } catch (error) {
    setError(error);
  } finally {
    showPage();
  }
}

bootstrapPage();
