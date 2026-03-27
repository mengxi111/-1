const STUDENT_API_BASE = "/api/student";

const el = {
  refreshBtn: document.getElementById("refreshBtn"),
  logoutBtn: document.getElementById("logoutBtn"),
  currentUserText: document.getElementById("currentUserText"),
  loadStoresBtn: document.getElementById("loadStoresBtn"),
  storeSelect: document.getElementById("storeSelect"),
  storeDetailName: document.getElementById("storeDetailName"),
  storeDetailDescription: document.getElementById("storeDetailDescription"),
  storeDetailAddress: document.getElementById("storeDetailAddress"),
  storeDetailPhone: document.getElementById("storeDetailPhone"),
  storeDetailHours: document.getElementById("storeDetailHours"),
  storeDetailHoursText: document.getElementById("storeDetailHoursText"),
  loadSeatsBtn: document.getElementById("loadSeatsBtn"),
  startTime: document.getElementById("startTime"),
  endTime: document.getElementById("endTime"),
  selectedSeatText: document.getElementById("selectedSeatText"),
  slotTodayBtn: document.getElementById("slotTodayBtn"),
  slotTomorrowBtn: document.getElementById("slotTomorrowBtn"),
  availableSlotsSummary: document.getElementById("availableSlotsSummary"),
  availableSlots: document.getElementById("availableSlots"),
  submitBookingBtn: document.getElementById("submitBookingBtn"),
  bookingOutput: document.getElementById("bookingOutput"),
  seatCount: document.getElementById("seatCount"),
  seatGrid: document.getElementById("seatGrid"),
  loadMyBookingsBtn: document.getElementById("loadMyBookingsBtn"),
  myBookingsBody: document.getElementById("myBookingsBody"),
  notificationMeta: document.getElementById("notificationMeta"),
  loadNotificationsBtn: document.getElementById("loadNotificationsBtn"),
  markAllNotificationsBtn: document.getElementById("markAllNotificationsBtn"),
  notificationList: document.getElementById("notificationList"),
};

const state = {
  stores: [],
  seats: [],
  selectedSeatId: null,
  selectedSlotDayOffset: 0,
  availableSlotsInfo: null,
  slotRequestSeatId: null,
  notifications: [],
  notificationUnreadCount: 0,
  notificationTotal: 0,
};

function authHeaders() {
  return {
    "Content-Type": "application/json",
    Authorization: `Bearer ${window.getToken()}`,
  };
}

function setOutput(value) {
  el.bookingOutput.textContent = typeof value === "string" ? value : JSON.stringify(value, null, 2);
}

function showErrorMessage(message) {
  setOutput(message);
  window.alert(message);
}

function parseResponseData(text) {
  try {
    return text ? JSON.parse(text) : null;
  } catch {
    return null;
  }
}

function parseApiErrorMessage(status, payload) {
  if (payload && typeof payload.message === "string") {
    return payload.message;
  }
  if (payload?.detail) {
    if (typeof payload.detail === "string") {
      return payload.detail;
    }
    if (typeof payload.detail?.message === "string") {
      return payload.detail.message;
    }
  }
  return window.parseApiError(status);
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
        ...authHeaders(),
        ...(options.headers || {}),
      },
    });
  } catch {
    throw new Error(window.t("errors.network"));
  }

  const text = await response.text();
  const data = parseResponseData(text);
  if (!response.ok) {
    if (response.status === 401) {
      window.clearSession();
      window.location.replace("/auth/login");
      throw new Error(window.t("errors.loginExpired"));
    }
    throw new Error(parseApiErrorMessage(response.status, data));
  }

  if (data && typeof data === "object" && Object.prototype.hasOwnProperty.call(data, "code")) {
    return data.data;
  }
  return data;
}

function toInputDatetimeValue(date) {
  const local = new Date(date.getTime() - date.getTimezoneOffset() * 60000);
  return local.toISOString().slice(0, 16);
}

function formatDateTime(value) {
  return new Date(value).toLocaleString("zh-CN", { hour12: false });
}

function formatHourMinute(value) {
  return new Date(value).toLocaleTimeString("zh-CN", {
    hour12: false,
    hour: "2-digit",
    minute: "2-digit",
  });
}

function getSelectedSlotDayLabel() {
  return state.selectedSlotDayOffset === 0
    ? window.t("student.availableSlotsToday")
    : window.t("student.availableSlotsTomorrow");
}

function getSelectedSlotDateIso() {
  const base = new Date();
  base.setHours(0, 0, 0, 0);
  base.setDate(base.getDate() + state.selectedSlotDayOffset);
  const year = base.getFullYear();
  const month = String(base.getMonth() + 1).padStart(2, "0");
  const day = String(base.getDate()).padStart(2, "0");
  return `${year}-${month}-${day}`;
}

function renderSlotDateSwitch() {
  el.slotTodayBtn.classList.toggle("active", state.selectedSlotDayOffset === 0);
  el.slotTomorrowBtn.classList.toggle("active", state.selectedSlotDayOffset === 1);
}

function toBusinessHoursText(openTime, closeTime) {
  const openText = String(openTime || "").slice(0, 5);
  const closeText = String(closeTime || "").slice(0, 5);
  if (!openText || !closeText) {
    return window.t("common.noData");
  }
  if (openText < closeText) {
    return `${openText} - ${closeText}`;
  }
  return `${openText} - 次日${closeText}`;
}

function toIsoDatetime(value) {
  if (!value) return null;
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return null;
  return date.toISOString();
}

function setAvailableSlotsPlaceholder(summaryText, placeholderText = summaryText) {
  el.availableSlotsSummary.textContent = summaryText;
  el.availableSlots.innerHTML = `<div class="slot-empty">${placeholderText}</div>`;
}

function buildAvailableSlotsDefaultText() {
  return window.formatTemplate(window.t("student.availableSlotsDefaultTemplate"), {
    label: getSelectedSlotDayLabel(),
  });
}

function renderCurrentUser() {
  const user = window.getUser();
  if (!user) {
    el.currentUserText.value = window.t("errors.needLogin");
    return;
  }
  const name = user.nickname || user.name || window.t("student.defaultStudentName", "学生");
  el.currentUserText.value = `${name} #${user.id}`;
}

function renderStoreOptions() {
  if (!state.stores.length) {
    el.storeSelect.innerHTML = `<option value="">${window.t("student.noStoresContactAdmin", window.t("student.noStores"))}</option>`;
    renderSelectedStoreDetails(null);
    state.seats = [];
    setSelectedSeat(null);
    renderSeats();
    return;
  }
  const availableStoreIds = new Set(state.stores.map((store) => store.id));
  const currentSelected = Number(el.storeSelect.value || 0);
  const selectedStoreId = availableStoreIds.has(currentSelected) ? currentSelected : state.stores[0].id;
  const options = state.stores.map((store) => `<option value="${store.id}">${store.name}</option>`);
  el.storeSelect.innerHTML = options.join("");
  el.storeSelect.value = String(selectedStoreId);
  renderSelectedStoreDetails(selectedStoreId);
}

function getSelectedStore() {
  const storeId = Number(el.storeSelect.value || 0);
  if (!storeId) return null;
  return state.stores.find((store) => store.id === storeId) || null;
}

function renderSelectedStoreDetails(storeId) {
  const store = storeId ? state.stores.find((item) => item.id === Number(storeId)) || null : null;
  if (!store) {
    const emptyText = window.t("student.storeInfoEmpty", window.t("student.noStores"));
    el.storeDetailName.textContent = emptyText;
    el.storeDetailDescription.textContent = emptyText;
    el.storeDetailDescription.hidden = false;
    el.storeDetailAddress.textContent = "-";
    el.storeDetailPhone.textContent = "-";
    el.storeDetailHours.textContent = "-";
    el.storeDetailHoursText.textContent = "-";
    return;
  }

  const businessHours = toBusinessHoursText(store.open_time, store.close_time);
  const description = String(store.description || "").trim();
  el.storeDetailName.textContent = store.name || "-";
  el.storeDetailDescription.textContent = description;
  el.storeDetailDescription.hidden = !description;
  el.storeDetailAddress.textContent = store.address || window.t("common.noData");
  el.storeDetailPhone.textContent = store.contact_phone || window.t("common.noData");
  el.storeDetailHours.textContent = businessHours;
  el.storeDetailHoursText.textContent = businessHours;
}

function renderSeats() {
  el.seatCount.textContent = window.formatTemplate(window.t("student.seatCountTemplate"), {
    count: state.seats.length,
  });
  if (!state.seats.length) {
    el.seatGrid.innerHTML = `<p>${window.t("student.noSeats")}</p>`;
    return;
  }

  el.seatGrid.innerHTML = state.seats
    .map((seat) => {
      const activeClass = state.selectedSeatId === seat.id ? "active" : "";
      return `
      <button class="seat-card ${activeClass}" data-seat-id="${seat.id}">
        <p class="seat-title">${window.formatTemplate(window.t("student.seatCardTitle"), { seatNo: seat.seat_no })}</p>
        <p class="seat-meta">${window.formatTemplate(window.t("student.seatCardId"), { id: seat.id })}</p>
        <p class="seat-meta">${window.formatTemplate(window.t("student.seatCardType"), { type: window.seatTypeText(seat.seat_type) })}</p>
      </button>`;
    })
    .join("");
}

function renderAvailableSlots() {
  if (!state.selectedSeatId) {
    setAvailableSlotsPlaceholder(buildAvailableSlotsDefaultText());
    return;
  }

  if (!state.availableSlotsInfo) {
    setAvailableSlotsPlaceholder(
      window.formatTemplate(window.t("student.availableSlotsLoadingTemplate"), {
        label: getSelectedSlotDayLabel(),
      }),
      window.t("common.loading"),
    );
    return;
  }

  const info = state.availableSlotsInfo;
  const slots = Array.isArray(info.available_slots) ? info.available_slots : [];
  el.availableSlotsSummary.textContent = window.formatTemplate(
    window.t("student.availableSlotsSummaryTemplate"),
    {
      label: getSelectedSlotDayLabel(),
      hours: toBusinessHoursText(info.open_time, info.close_time),
      count: slots.length,
    },
  );

  if (!slots.length) {
    el.availableSlots.innerHTML = `<div class="slot-empty">${window.formatTemplate(window.t("student.availableSlotsEmptyTemplate"), {
      label: getSelectedSlotDayLabel(),
    })}</div>`;
    return;
  }

  el.availableSlots.innerHTML = slots
    .map(
      (slot) => `
        <button
          class="available-slot"
          data-slot-start="${slot.start_time}"
          data-slot-end="${slot.end_time}"
        >
          <span class="slot-time">${formatHourMinute(slot.start_time)} - ${formatHourMinute(slot.end_time)}</span>
          <span class="slot-duration">${window.formatTemplate(window.t("student.availableSlotDurationTemplate"), {
            minutes: slot.duration_minutes,
          })}</span>
          <span class="slot-action">${window.t("student.availableSlotApply")}</span>
        </button>
      `,
    )
    .join("");
}

async function loadAvailableSlots(seatId) {
  state.slotRequestSeatId = seatId;
  state.availableSlotsInfo = null;
  renderAvailableSlots();

  const slotDate = getSelectedSlotDateIso();
  const info = await request(`/seats/${seatId}/available-slots?date=${encodeURIComponent(slotDate)}`);
  if (state.selectedSeatId !== seatId || state.slotRequestSeatId !== seatId) {
    return;
  }
  state.availableSlotsInfo = info;
  renderAvailableSlots();
}

function setSelectedSeat(seatId) {
  state.selectedSeatId = seatId;
  state.slotRequestSeatId = seatId;
  if (seatId) {
    el.selectedSeatText.textContent = window.formatTemplate(window.t("student.selectedSeatTemplate"), { seatId });
  } else {
    el.selectedSeatText.textContent = window.t("student.selectedSeatDefault");
    state.availableSlotsInfo = null;
  }
  renderSeats();
  renderAvailableSlots();
}

function setSelectedSlotDayOffset(offset) {
  state.selectedSlotDayOffset = offset;
  state.availableSlotsInfo = null;
  renderSlotDateSwitch();
  renderAvailableSlots();
  if (state.selectedSeatId) {
    loadAvailableSlots(state.selectedSeatId).catch((err) => {
      state.availableSlotsInfo = null;
      setAvailableSlotsPlaceholder(err.message, err.message);
      setOutput(err.message);
    });
  }
}

async function loadStores() {
  setOutput(window.t("common.loading"));
  const stores = await request("/stores");
  state.stores = Array.isArray(stores) ? stores : [];
  renderStoreOptions();
  if (!state.stores.length) {
    setOutput(window.t("student.noStoresContactAdmin", window.t("student.noStores")));
    return;
  }
  await loadSeats();
  setOutput({ stores: state.stores.length, message: window.t("student.storesLoaded", "门店已加载") });
}

async function loadSeats() {
  const storeId = Number(el.storeSelect.value || 0);
  if (!storeId) {
    throw new Error(window.t("errors.chooseStoreFirst"));
  }
  setOutput(window.t("common.loading"));
  const seats = await request(`/seats?store_id=${storeId}`);
  state.seats = Array.isArray(seats) ? seats : [];
  setSelectedSeat(null);
  renderSeats();
}

async function submitBooking() {
  if (!state.selectedSeatId) {
    throw new Error(window.t("errors.noSeatSelected"));
  }
  const startTime = toIsoDatetime(el.startTime.value);
  const endTime = toIsoDatetime(el.endTime.value);
  if (!startTime || !endTime) {
    throw new Error(window.t("errors.invalidRequest"));
  }
  const data = await request("/bookings", {
    method: "POST",
    body: JSON.stringify({
      seat_id: state.selectedSeatId,
      start_time: startTime,
      end_time: endTime,
    }),
  });
  setOutput({
    message: window.t("student.bookingSuccess", "预约成功"),
    booking_id: data.booking_id,
    status: data.status,
  });
  await loadMyBookings();
}

async function cancelBooking(bookingId) {
  await request(`/bookings/${bookingId}/cancel`, { method: "POST" });
  setOutput(window.t("student.cancelSuccess", "取消预约成功"));
  await loadMyBookings();
}

async function qrSignIn(bookingId) {
  const codeData = await request(`/bookings/${bookingId}/checkin/qr-code`, { method: "POST" });
  setOutput({
    message: window.t("student.checkinQrReady"),
    booking_id: bookingId,
    qr_content: codeData.qr_content,
    qr_expires_at: codeData.qr_expires_at,
  });

  const signData = await request(`/bookings/${bookingId}/checkin/qr-signin`, {
    method: "POST",
    body: JSON.stringify({ qr_token: codeData.qr_token }),
  });
  setOutput({
    message: window.t("student.checkinSuccess"),
    booking_id: bookingId,
    status: signData.status,
    checked_in_at: signData.checked_in_at,
  });
  await loadMyBookings();
}

function notificationTypeText(type) {
  const keyMap = {
    booking: "student.notificationTypeBooking",
    notice: "student.notificationTypeNotice",
    violation: "student.notificationTypeViolation",
    system: "student.notificationTypeSystem",
  };
  return window.t(keyMap[type] || "student.notificationTypeSystem");
}

function notificationEmailStatusText(status) {
  const keyMap = {
    pending: "student.notificationEmailPending",
    sent: "student.notificationEmailSent",
    failed: "student.notificationEmailFailed",
    skipped: "student.notificationEmailSkipped",
  };
  return window.t(keyMap[status] || "student.notificationEmailSkipped");
}

function renderNotifications() {
  if (!el.notificationMeta || !el.notificationList) return;

  if (!state.notificationTotal) {
    el.notificationMeta.textContent = window.t("student.notificationsMetaDefault");
    el.notificationList.innerHTML = `<div class="notification-empty">${window.t("student.notificationsEmpty")}</div>`;
    return;
  }

  if (state.notificationUnreadCount > 0) {
    el.notificationMeta.textContent = window.formatTemplate(window.t("student.notificationsUnreadTemplate"), {
      count: state.notificationUnreadCount,
      total: state.notificationTotal,
    });
  } else {
    el.notificationMeta.textContent = window.formatTemplate(window.t("student.notificationsTotalTemplate"), {
      count: state.notificationTotal,
    });
  }

  el.notificationList.innerHTML = state.notifications
    .map((item) => {
      const unreadClass = item.is_read ? "" : " unread";
      const readTagClass = item.is_read ? "" : " unread";
      const emailClass = item.email_status ? ` ${item.email_status}` : "";
      const markReadButton = item.is_read
        ? ""
        : `<button class="row-action" data-notification-action="read" data-notification-id="${item.id}">${window.t("student.notificationMarkRead")}</button>`;

      return `
        <article class="notification-item${unreadClass}">
          <div class="notification-head">
            <h3 class="notification-title">${escapeHtml(item.title)}</h3>
            <div class="notification-tags">
              <span class="notification-tag">${notificationTypeText(item.notification_type)}</span>
              <span class="notification-tag${readTagClass}">${item.is_read ? window.t("student.notificationRead") : window.t("student.notificationUnread")}</span>
              <span class="notification-tag${emailClass}">${window.t("student.notificationEmailLabel")}：${notificationEmailStatusText(item.email_status)}</span>
            </div>
          </div>
          <p class="notification-body">${escapeHtml(item.content)}</p>
          <div class="notification-foot">
            <span class="notification-time">${formatDateTime(item.created_at)}</span>
            ${markReadButton}
          </div>
          ${item.email_error ? `<div class="notification-error">${escapeHtml(item.email_error)}</div>` : ""}
        </article>
      `;
    })
    .join("");
}

function renderMyBookings(bookings = []) {
  if (!bookings.length) {
    el.myBookingsBody.innerHTML = `<tr><td colspan="6">${window.t("student.noBookings")}</td></tr>`;
    return;
  }

  el.myBookingsBody.innerHTML = bookings
    .map((item) => {
      let actionHtml = `<span>${window.t("student.actionNone")}</span>`;
      if (item.status === "booked" && item.can_checkin) {
        actionHtml = `<button class="row-action primary" data-action="qr-signin" data-id="${item.id}">${window.t("student.actionSignByQr")}</button>`;
      } else if (item.status === "booked") {
        actionHtml = `<button class="row-action" data-action="cancel" data-id="${item.id}">${window.t("student.actionCancel")}</button>`;
      }

      return `
      <tr>
        <td>${item.id}</td>
        <td>${item.seat_id}</td>
        <td>${formatDateTime(item.start_time)}</td>
        <td>${formatDateTime(item.end_time)}</td>
        <td><span class="status ${item.status}">${window.statusText(item.status)}</span></td>
        <td>${actionHtml}</td>
      </tr>`;
    })
    .join("");
}

async function loadMyBookings() {
  const data = await request("/bookings/me");
  renderMyBookings(Array.isArray(data) ? data : []);
}

async function loadNotifications() {
  const data = await request("/notifications?limit=20");
  state.notifications = Array.isArray(data?.items) ? data.items : [];
  state.notificationUnreadCount = Number(data?.unread_count || 0);
  state.notificationTotal = Number(data?.total || 0);
  renderNotifications();
}

async function markNotificationRead(notificationId) {
  await request(`/notifications/${notificationId}/read`, { method: "POST" });
  await loadNotifications();
}

async function markAllNotificationsRead() {
  await request("/notifications/read-all", { method: "POST" });
  setOutput(window.t("student.notificationReadAllSuccess"));
  await loadNotifications();
}

function applyAvailableSlot(startTime, endTime) {
  el.startTime.value = toInputDatetimeValue(new Date(startTime));
  el.endTime.value = toInputDatetimeValue(new Date(endTime));
  setOutput({
    message: window.t("student.availableSlotApplied"),
    start_time: startTime,
    end_time: endTime,
  });
}

function logout() {
  window.clearSession();
  window.location.replace("/auth/login");
}

function bindEvents() {
  el.refreshBtn.addEventListener("click", () => refreshAll());
  el.logoutBtn.addEventListener("click", logout);
  el.loadStoresBtn.addEventListener("click", () => loadStores().catch((err) => setOutput(err.message)));
  el.loadSeatsBtn.addEventListener("click", () => loadSeats().catch((err) => setOutput(err.message)));
  el.submitBookingBtn.addEventListener("click", () => submitBooking().catch((err) => showErrorMessage(err.message)));
  el.loadMyBookingsBtn.addEventListener("click", () => loadMyBookings().catch((err) => setOutput(err.message)));
  el.loadNotificationsBtn.addEventListener("click", () => loadNotifications().catch((err) => setOutput(err.message)));
  el.markAllNotificationsBtn.addEventListener("click", () => markAllNotificationsRead().catch((err) => setOutput(err.message)));
  el.slotTodayBtn.addEventListener("click", () => setSelectedSlotDayOffset(0));
  el.slotTomorrowBtn.addEventListener("click", () => setSelectedSlotDayOffset(1));

  el.storeSelect.addEventListener("change", () => {
    renderSelectedStoreDetails(getSelectedStore()?.id || null);
    loadSeats().catch((err) => setOutput(err.message));
  });

  el.seatGrid.addEventListener("click", (event) => {
    const target = event.target instanceof HTMLElement ? event.target.closest("[data-seat-id]") : null;
    if (!target) return;
    const seatId = Number(target.getAttribute("data-seat-id") || 0);
    if (!seatId) return;
    setSelectedSeat(seatId);
    loadAvailableSlots(seatId).catch((err) => {
      state.availableSlotsInfo = null;
      setAvailableSlotsPlaceholder(err.message, err.message);
      setOutput(err.message);
    });
  });

  el.availableSlots.addEventListener("click", (event) => {
    const target = event.target instanceof HTMLElement ? event.target.closest("[data-slot-start]") : null;
    if (!target) return;
    const startTime = target.getAttribute("data-slot-start");
    const endTime = target.getAttribute("data-slot-end");
    if (!startTime || !endTime) return;
    applyAvailableSlot(startTime, endTime);
  });

  el.myBookingsBody.addEventListener("click", (event) => {
    const target = event.target instanceof HTMLElement ? event.target.closest("[data-action]") : null;
    if (!target) return;
    const action = target.getAttribute("data-action");
    const bookingId = Number(target.getAttribute("data-id") || 0);
    if (!bookingId) return;

    if (action === "cancel") {
      cancelBooking(bookingId).catch((err) => setOutput(err.message));
      return;
    }
    if (action === "qr-signin") {
      qrSignIn(bookingId).catch((err) => setOutput(err.message));
    }
  });

  el.notificationList.addEventListener("click", (event) => {
    const target =
      event.target instanceof HTMLElement ? event.target.closest("[data-notification-action]") : null;
    if (!target) return;
    const action = target.getAttribute("data-notification-action");
    const notificationId = Number(target.getAttribute("data-notification-id") || 0);
    if (!notificationId) return;

    if (action === "read") {
      markNotificationRead(notificationId).catch((err) => setOutput(err.message));
    }
  });
}

async function refreshAll() {
  try {
    renderCurrentUser();
    await loadStores();
    await loadMyBookings();
    await loadNotifications();
  } catch (error) {
    setOutput(error.message || window.t("errors.requestFailed"));
  }
}

function initDefaultTimeRange() {
  const now = new Date();
  const start = new Date(now.getTime() + 5 * 60 * 1000);
  const end = new Date(start.getTime() + 2 * 60 * 60 * 1000);
  el.startTime.value = toInputDatetimeValue(start);
  el.endTime.value = toInputDatetimeValue(end);
}

window.applyI18n(document);
if (window.ensureStudentPageGuard()) {
  document.body.classList.remove("page-hidden");
  initDefaultTimeRange();
  bindEvents();
  renderSlotDateSwitch();
  setSelectedSeat(null);
  renderNotifications();
  refreshAll();
}
