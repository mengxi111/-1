(function () {
  const UI_TEXT = {
    common: {
      loading: "加载中...",
      noData: "暂无数据",
      refresh: "刷新",
      selectStore: "请选择门店",
    },
    errors: {
      needLogin: "需要登录，未登录无法操作",
      loginExpired: "登录已过期，请重新登录",
      network: "网络异常，请检查服务是否启动",
      requestFailed: "请求失败，请稍后重试",
      invalidRequest: "请求参数不正确，请检查后重试",
      forbidden: "无权限执行该操作",
      timeConflict: "该时间段已被预约，请更换时间或座位",
      notFound: "未找到对应数据",
      serverBusy: "服务暂时不可用，请稍后重试",
      chooseStoreFirst: "请先选择门店",
      noSeatSelected: "未选择座位",
    },
    status: {
      booked: "已预约",
      confirmed: "已预约",
      checked_in: "已签到",
      cancelled: "已取消",
      expired: "已过期",
      completed: "已完成",
      pending: "待支付",
      paid: "已支付",
      refunded: "已退款",
    },
    seatType: {
      normal: "普通座",
      silent: "静音座",
      booth: "隔间座",
      vip: "贵宾座",
    },
    student: {
      pageTitle: "学生预约",
      badge: "学生预约",
      heroTitle: "自习室预约",
      heroSubtitle: "需要登录，未登录无法操作",
      refresh: "刷新",
      logout: "退出登录",
      sectionSession: "会话信息",
      sectionStore: "门店",
      sectionTimeSlot: "时间段",
      sectionAvailableSlots: "今日可用时段",
      sectionSeats: "座位列表",
      sectionMyBookings: "我的预约",
      sectionNotifications: "通知中心",
      loadStores: "加载门店",
      loadSeats: "加载座位",
      submitBooking: "提交预约",
      loadMyBookings: "刷新",
      loadNotifications: "刷新通知",
      markAllNotifications: "全部标记已读",
      tipRedirect: "未登录会自动跳转到登录页。",
      currentUser: "当前用户",
      storeLabel: "门店",
      startLabel: "开始时间",
      endLabel: "结束时间",
      availableSlotsDateLabel: "查看日期",
      availableSlotsToday: "今天",
      availableSlotsTomorrow: "明天",
      availableSlotsDefaultTemplate: "选择座位后，系统将显示该座位{label}可预约时段",
      availableSlotsHint: "点击下方时段可自动填充开始和结束时间",
      availableSlotsLoadingTemplate: "正在加载该座位{label}可用时段…",
      availableSlotsEmptyTemplate: "{label}剩余营业时间内暂无可预约时段",
      availableSlotsSummaryTemplate: "{label}营业时间：{hours}，剩余 {count} 段可预约时段",
      availableSlotDurationTemplate: "可预约 {minutes} 分钟",
      availableSlotApply: "点击填充",
      availableSlotApplied: "已填入可用时段，可直接提交预约",
      selectedSeatDefault: "未选择座位",
      seatCountTemplate: "{count} 个座位",
      seatCardTitle: "座位 {seatNo}",
      seatCardId: "编号：{id}",
      seatCardType: "类型：{type}",
      selectedSeatTemplate: "已选择座位编号：{seatId}",
      noStores: "暂无门店",
      noStoresContactAdmin: "暂无门店，请联系管理员创建门店",
      storesLoaded: "门店已加载",
      noSeats: "当前门店暂无可用座位",
      noBookings: "暂无预约记录",
      bookingTableId: "编号",
      bookingTableSeat: "座位",
      bookingTableStart: "开始时间",
      bookingTableEnd: "结束时间",
      bookingTableStatus: "状态",
      bookingTableAction: "操作",
      actionCancel: "取消预约",
      actionSignByQr: "二维码签到",
      checkinSuccess: "签到成功",
      checkinQrReady: "二维码已生成，正在模拟扫码签到",
      bookingSuccess: "预约成功",
      cancelSuccess: "取消预约成功",
      defaultStudentName: "学生",
      actionNone: "-",
      notificationsMetaDefault: "暂无通知",
      notificationsEmpty: "暂无通知",
      notificationsUnreadTemplate: "未读 {count} 条，共 {total} 条通知",
      notificationsTotalTemplate: "共 {count} 条通知",
      notificationRead: "已读",
      notificationUnread: "未读",
      notificationMarkRead: "标记已读",
      notificationEmailLabel: "邮箱推送",
      notificationTypeBooking: "预约通知",
      notificationTypeNotice: "公告通知",
      notificationTypeViolation: "违规提醒",
      notificationTypeSystem: "系统通知",
      notificationEmailPending: "待发送",
      notificationEmailSent: "已发送",
      notificationEmailFailed: "发送失败",
      notificationEmailSkipped: "未发送",
      notificationReadAllSuccess: "全部通知已标记为已读",
    },
  };

  const AUTH_TOKEN_KEY = "study_room_access_token";
  const AUTH_USER_KEY = "study_room_user";

  function getByPath(obj, path) {
    return path.split(".").reduce((current, key) => {
      if (current && Object.prototype.hasOwnProperty.call(current, key)) {
        return current[key];
      }
      return undefined;
    }, obj);
  }

  function formatTemplate(template, params = {}) {
    return String(template).replace(/\{(\w+)\}/g, (_, key) => {
      if (Object.prototype.hasOwnProperty.call(params, key)) {
        return String(params[key]);
      }
      return `{${key}}`;
    });
  }

  function t(path, fallback = "") {
    const value = getByPath(UI_TEXT, path);
    if (typeof value === "string") return value;
    return fallback || path;
  }

  function statusText(status) {
    if (!status) return t("common.noData");
    return t(`status.${status}`, "未知状态");
  }

  function seatTypeText(type) {
    if (!type) return t("common.noData");
    return t(`seatType.${type}`, "其他类型");
  }

  function parseApiError(status) {
    if (status === 0) return t("errors.network");
    if (status === 400 || status === 422) return t("errors.invalidRequest");
    if (status === 401) return t("errors.needLogin");
    if (status === 403) return t("errors.forbidden");
    if (status === 404) return t("errors.notFound");
    if (status === 409) return t("errors.timeConflict");
    if (status >= 500) return t("errors.serverBusy");
    return t("errors.requestFailed");
  }

  function applyI18n(root = document) {
    root.querySelectorAll("[data-text]").forEach((node) => {
      const key = node.getAttribute("data-text");
      node.textContent = t(key || "", node.textContent || "");
    });

    root.querySelectorAll("[data-placeholder]").forEach((node) => {
      const key = node.getAttribute("data-placeholder");
      if ("placeholder" in node) {
        node.placeholder = t(key || "", node.placeholder || "");
      }
    });

    const titleEl = root.querySelector("title[data-text]");
    if (titleEl) {
      document.title = t(titleEl.getAttribute("data-text") || "", document.title);
    }
  }

  function clearSession() {
    localStorage.removeItem(AUTH_TOKEN_KEY);
    localStorage.removeItem(AUTH_USER_KEY);
  }

  function getToken() {
    return localStorage.getItem(AUTH_TOKEN_KEY);
  }

  function getUser() {
    const raw = localStorage.getItem(AUTH_USER_KEY);
    if (!raw) return null;
    try {
      return JSON.parse(raw);
    } catch {
      return null;
    }
  }

  function ensureStudentPageGuard() {
    const token = getToken();
    const user = getUser();
    if (!token || !user?.role) {
      window.location.replace("/auth/login");
      return false;
    }
    if (user.role !== "student") {
      window.location.replace("/auth/login");
      return false;
    }
    return true;
  }

  window.t = t;
  window.formatTemplate = formatTemplate;
  window.statusText = statusText;
  window.seatTypeText = seatTypeText;
  window.parseApiError = parseApiError;
  window.applyI18n = applyI18n;
  window.clearSession = clearSession;
  window.getToken = getToken;
  window.getUser = getUser;
  window.ensureStudentPageGuard = ensureStudentPageGuard;
})();
