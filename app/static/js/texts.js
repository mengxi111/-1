(function () {
  const UI_TEXT = {
    common: {
      loading: "加载中...",
      checkingAuth: "正在校验登录状态…",
      noData: "暂无数据",
      refresh: "刷新",
      submit: "提交",
      cancel: "取消",
      confirm: "确认",
      close: "关闭",
      seat: "座位",
      start: "开始时间",
      end: "结束时间",
      status: "状态",
      action: "操作",
      id: "编号",
      required: "必填",
      selectStore: "请选择门店",
    },
    errors: {
      needLogin: "需要登录，未登录无法操作",
      loginExpired: "登录已过期，请重新登录",
      network: "网络异常，请检查服务是否启动",
      requestFailed: "请求失败，请稍后重试",
      invalidRequest: "请求参数不正确，请检查后重试",
      forbidden: "无权限执行该操作",
      conflict: "请求冲突，请稍后重试",
      timeConflict: "该座位在所选时间段已被预约",
      notFound: "未找到对应数据",
      serverBusy: "服务暂时不可用，请稍后重试",
      chooseStoreFirst: "请先选择门店",
      noSeatSelected: "未选择座位",
      bookingIdRequired: "请输入预约编号",
      accountRequired: "请输入手机号或邮箱",
      phoneRequired: "请输入手机号",
      passwordRequired: "请输入密码",
      nameRequired: "请输入昵称",
      registerFailed: "注册失败，请稍后重试",
      loginFailed: "登录失败，请检查账号或密码",
      accountExists: "账号已存在，请直接登录或更换手机号/邮箱",
      roleForbiddenStudent: "仅学生可访问该页面",
      roleForbiddenAdmin: "仅员工或管理员可访问该页面",
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
    auth: {
      pageTitle: "晋中信息学院｜自习室预约",
      brandTag: "晋中信息学院",
      brandTitle: "自习室预约",
      brandDesc: "请先登录或注册，进入晋中信息学院自习室预约系统。",
      tabLogin: "登录",
      tabRegister: "注册",
      accountLabel: "手机号或邮箱",
      accountPlaceholder: "请输入手机号或邮箱",
      phoneLabel: "手机号",
      phonePlaceholder: "请输入手机号，例如 13900000002",
      emailLabel: "邮箱",
      emailPlaceholder: "请输入邮箱，例如 demo@example.com",
      passwordLabel: "密码",
      passwordPlaceholder: "请输入至少 6 位密码",
      nameLabel: "昵称",
      namePlaceholder: "请输入昵称",
      loginSubmit: "登录并进入",
      registerSubmit: "注册并进入",
      outputInit: "请输入账号信息后提交。",
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
      actionCheckin: "立即签到",
      actionSignByQr: "二维码签到",
      checkinSuccess: "签到成功",
      checkinQrReady: "二维码已生成，正在模拟扫码签到",
      bookingSuccess: "预约成功",
      cancelSuccess: "取消预约成功",
      defaultStudentName: "学生",
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
      actionNone: "-",
    },
    admin: {
      pageTitle: "晋中信息学院｜管理后台",
      badge: "晋中信息学院",
      topTitle: "自习室管理后台",
      navDashboard: "仪表盘",
      navStores: "门店管理",
      navOrders: "订单管理",
      navUsers: "用户管理",
      navConfig: "系统配置",
      navLogs: "日志中心",
      refreshAll: "刷新全部",
      logout: "退出登录",
      sectionSession: "会话信息",
      currentUser: "当前用户",
      currentRole: "当前角色",
      sectionStore: "门店视图",
      loadStores: "加载门店",
      storeLabel: "当前门店",
      storeAll: "全部门店",
      storeInfoAll: "当前为全部门店视图",
      storeInfoEmpty: "请选择门店后查看详情",
      storeDescriptionEmpty: "未选择具体门店时，将展示汇总信息。",
      storeAddress: "地址",
      storePhone: "工作人员联系方式",
      storeHours: "营业时间",
      storeStatus: "门店状态",
      storeStatusEdit: "门店状态",
      storeStatusOpen: "营业中",
      storeStatusClosed: "已停用",
      editStore: "编辑门店",
      storeDescriptionEdit: "门店简介",
      storeDescriptionPlaceholder: "请输入门店简介",
      storeAddressEdit: "地址",
      storeAddressPlaceholder: "请输入门店地址",
      storePhoneEdit: "工作人员联系方式",
      storePhonePlaceholder: "请输入工作人员联系方式",
      storeOpenTime: "开始营业时间",
      storeCloseTime: "结束营业时间",
      saveStoreInfo: "保存门店信息",
      cancelStoreEdit: "取消编辑",
      storeSelectFirst: "请先选择门店",
      storeSaveSuccess: "门店信息已更新",
      storeEditDisabled: "全部门店模式下不支持编辑，请先选择具体门店",
      storeEmpty: "暂无门店信息",
      statsDate: "统计日期",
      sectionOverview: "今日概览",
      loadStats: "加载统计",
      recent7DayTrend: "最近7天预约趋势",
      hotSeatRank: "热门座位排行",
      todayBookingCount: "今日预约数",
      todayCheckinCount: "今日签到数",
      todayOrderCount: "今日订单数",
      todayRevenue: "今日收入",
      todayOccupancy: "今日上座率",
      currentOccupancyRate: "当前上座率",
      todayNoShowCount: "今日爽约数",
      currentIdleSeatCount: "当前空闲座位数",
      hourlyTrend: "按小时上座趋势",
      sectionOrderList: "订单列表",
      refreshList: "刷新列表",
      exportOrders: "导出订单",
      filterAll: "全部",
      orderListMetaDefault: "当前展示全部订单",
      orderFilterStatus: "订单状态",
      orderFilterStore: "门店筛选",
      orderFilterKeyword: "用户编号/手机号",
      orderFilterKeywordPlaceholder: "请输入用户编号、手机号或昵称",
      orderFilterDateFrom: "开始时间",
      orderFilterDateTo: "结束时间",
      orderFilterAction: "筛选操作",
      searchOrders: "查询订单",
      resetOrders: "重置筛选",
      orderTableId: "订单编号",
      orderTableStore: "门店",
      orderTableSeat: "座位",
      orderTableBookingId: "预约编号",
      orderTableUser: "用户",
      orderTableAmount: "金额",
      orderTableStatus: "状态",
      orderTableCreatedAt: "创建时间",
      orderTableAction: "操作",
      orderActionDetail: "查看详情",
      orderActionCancel: "取消订单",
      orderActionPaid: "标记已支付",
      orderActionRefund: "标记已退款",
      orderDetailDefault: "点击“查看详情”可查看订单信息",
      orderDetailTitle: "订单详情",
      orderListCountTemplate: "当前共 {count} 条订单",
      noOrders: "暂无订单数据",
      orderExportSuccess: "订单导出成功",
      orderLoadFailed: "订单数据加载失败，请稍后重试",
      orderActionCancelConfirm: "确认取消该订单吗？",
      orderActionPaidConfirm: "确认将该订单标记为已支付吗？",
      orderActionRefundConfirm: "确认将该订单标记为已退款吗？",
      orderActionSuccessTemplate: "订单 {action}成功",
      sectionOperationLog: "操作日志",
      loadOperationLog: "查询日志",
      logModule: "模块",
      logModulePlaceholder: "例如 stores / seats / orders",
      logOperatorKeyword: "管理员",
      logOperatorKeywordPlaceholder: "请输入管理员昵称或编号",
      logMethod: "请求方法",
      logStartTime: "开始时间",
      logEndTime: "结束时间",
      logPrevPage: "上一页",
      logNextPage: "下一页",
      logPageInfo: "第 {page} 页，共 {total} 条",
      logTableOperator: "操作人",
      logTableRole: "角色",
      logTableIP: "IP",
      logTableModule: "模块",
      logTableMethod: "方法",
      logTablePath: "路径",
      logTableStatusCode: "响应码",
      logTableDuration: "耗时",
      logTableTime: "时间",
      logLoadFailed: "日志加载失败，请稍后重试",
      sectionCheckinStats: "签到率统计",
      loadCheckinStats: "加载签到统计",
      sectionResourceCenter: "数据管理台",
      bootstrapData: "初始化种子数据",
      bootstrapDemoData: "初始化演示数据",
      loadResource: "加载数据",
      sectionUserList: "注册用户信息",
      userListMetaDefault: "点击按钮加载全部注册用户信息",
      loadUsers: "加载用户信息",
      userListCountTemplate: "当前共 {count} 位注册用户",
      userFilterName: "昵称",
      userFilterNamePlaceholder: "请输入昵称",
      userFilterPhone: "手机号",
      userFilterPhonePlaceholder: "请输入手机号",
      userFilterRole: "角色",
      userFilterStatus: "状态",
      userFilterDateFrom: "注册开始时间",
      userFilterDateTo: "注册结束时间",
      searchUsers: "搜索用户",
      resetUsers: "重置筛选",
      userTableId: "用户编号",
      userTableName: "昵称",
      userTablePhone: "手机号",
      userTableEmail: "邮箱",
      userTableRole: "角色",
      userTableStatus: "状态",
      userTableNoShow: "爽约次数",
      userTableBlacklist: "黑名单",
      userTableBookingCount: "历史预约数",
      userTableCreatedAt: "注册时间",
      userTableAction: "操作",
      userActionViewDetail: "查看详情",
      userActionViewBookings: "查看预约",
      userActionFreeze: "冻结用户",
      userActionUnfreeze: "解冻用户",
      userActionDelete: "删除用户",
      userActionBlacklist: "加入黑名单",
      userActionRemoveBlacklist: "移出黑名单",
      userDeleteConfirm: "确认删除该用户吗？将执行软删除并隐藏该用户。",
      userFreezeConfirm: "确认冻结该用户吗？冻结后将无法正常登录和预约。",
      userUnfreezeConfirm: "确认解冻该用户吗？",
      userDeleteSuccess: "用户已删除",
      userFreezeSuccess: "用户已冻结",
      userUnfreezeSuccess: "用户已解冻",
      userBlacklistAddSuccess: "用户已加入黑名单",
      userBlacklistRemoveSuccess: "用户已移出黑名单",
      userDetailTitle: "用户详情",
      userDetailPhone: "手机号",
      userDetailEmail: "邮箱",
      userDetailRole: "角色",
      userDetailStatus: "状态",
      userDetailCreatedAt: "注册时间",
      userDetailNoShow: "爽约次数",
      userDetailBlacklist: "黑名单状态",
      userDetailBlacklistUntil: "黑名单截止时间",
      userDetailHistoryCount: "历史预约数",
      userDetailLastBookingAt: "最近预约时间",
      sectionUserBookings: "用户预约记录",
      userBookingsMetaDefault: "点击用户列表中的“查看预约”查看该用户预约记录",
      userBookingsMetaTemplate: "当前查看：{name}（用户 #{id}）的预约记录",
      reloadUserBookings: "刷新预约记录",
      userBookingsSelectFirst: "请先选择用户",
      userBookingsEmpty: "该用户暂无预约记录",
      userBookingTableId: "预约编号",
      userBookingTableStore: "门店",
      userBookingTableSeat: "座位",
      userBookingTableStart: "开始时间",
      userBookingTableEnd: "结束时间",
      userBookingTableStatus: "状态",
      userStatusActive: "正常",
      userStatusDisabled: "冻结",
      userStatusDeleted: "已删除",
      userBlacklistActive: "已在黑名单",
      userBlacklistInactive: "正常",
      userBlacklistUntilTemplate: "至 {time}",
      resourceTypeLabel: "数据类型",
      resourceStatusLabel: "状态筛选（可选）",
      resourceStatusPlaceholder: "例如 booked / active / published",
      resourceEmpty: "暂无数据",
      resourceLoadFailed: "数据加载失败，请稍后重试",
      todayReservations: "今日预约数",
      todayCheckins: "今日签到数",
      todayMissedCheckins: "今日爽约数",
      todayCheckinRate: "今日签到率",
      checkinChartTitle: "按小时签到率趋势",
      checkinChartChecked: "签到人数",
      checkinChartRate: "签到率(%)",
      checkinChartUnavailable: "图表库未加载，无法展示签到趋势图",
      roleStaff: "店员",
      roleAdmin: "管理员",
      roleSuperAdmin: "超级管理员",
      barTitleTemplate: "{hour}:00 占座 {occupied}（{rate}%）",
      resourceStores: "门店",
      resourceAreas: "区域",
      resourceSeats: "座位",
      resourcePlans: "价格方案",
      resourceBookings: "预约",
      resourceCheckins: "签到记录",
      resourceUsers: "用户",
      resourceBlacklists: "黑名单",
      resourceNotices: "公告",
      resourceMemberships: "会员卡",
      sectionSystemConfig: "系统配置",
      loadSystemConfig: "加载配置",
      saveSystemConfig: "保存配置",
      resetSystemConfig: "恢复默认配置",
      configResetConfirm: "确认恢复默认配置吗？当前修改将被覆盖。",
      blacklistEffectiveDays: "黑名单生效天数",
      defaultOpenTime: "默认营业开始时间",
      defaultCloseTime: "默认营业结束时间",
      configSaveSuccess: "配置保存成功",
      configResetSuccess: "默认配置已恢复",
      configLoadFailed: "配置加载失败，请稍后重试",
      sectionOutput: "操作反馈",
      outputDefault: "暂无操作结果",
      statsLoadFailed: "统计数据加载失败，请稍后重试",
      statsNoData: "暂无统计数据",
      logsNoData: "暂无日志数据",
      chartHourLabel: "{hour}:00",
      chartHourlyTooltip: "{hour}<br/>上座数：{value}",
      chartBookingsLegend: "预约数",
      chartRevenueLegend: "收入",
      chartHotSeatLegend: "预约次数",
    },
  };

  const AUTH_TOKEN_KEY = "study_room_access_token";
  const AUTH_REFRESH_KEY = "study_room_refresh_token";
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
    if (typeof value === "string") {
      return value;
    }
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

  function roleText(role) {
    if (role === "staff") return t("admin.roleStaff");
    if (role === "admin") return t("admin.roleAdmin");
    if (role === "super_admin") return t("admin.roleSuperAdmin");
    return "学生";
  }

  function resourceTypeText(type) {
    const mapping = {
      stores: t("admin.resourceStores"),
      areas: t("admin.resourceAreas"),
      seats: t("admin.resourceSeats"),
      plans: t("admin.resourcePlans"),
      bookings: t("admin.resourceBookings"),
      checkins: t("admin.resourceCheckins"),
      users: t("admin.resourceUsers"),
      blacklists: t("admin.resourceBlacklists"),
      notices: t("admin.resourceNotices"),
      memberships: t("admin.resourceMemberships"),
    };
    return mapping[type] || type;
  }

  function parseApiError(status) {
    if (status === 0) return t("errors.network");
    if (status === 400 || status === 422) return t("errors.invalidRequest");
    if (status === 401) return t("errors.needLogin");
    if (status === 403) return t("errors.forbidden");
    if (status === 404) return t("errors.notFound");
    if (status === 409) return t("errors.conflict");
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

  function saveSession({ accessToken, refreshToken, user }) {
    localStorage.setItem(AUTH_TOKEN_KEY, accessToken || "");
    if (refreshToken) {
      localStorage.setItem(AUTH_REFRESH_KEY, refreshToken);
    }
    if (user) {
      localStorage.setItem(AUTH_USER_KEY, JSON.stringify(user));
    }
  }

  function clearSession() {
    localStorage.removeItem(AUTH_TOKEN_KEY);
    localStorage.removeItem(AUTH_REFRESH_KEY);
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

  function isAdminRole(role) {
    return role === "staff" || role === "admin" || role === "super_admin";
  }

  function redirectByRole(role) {
    if (role === "student") {
      window.location.replace("/student");
      return;
    }
    if (isAdminRole(role)) {
      window.location.replace("/admin/dashboard");
      return;
    }
    window.location.replace("/auth/login");
  }

  function ensureAuthPageGuard() {
    const token = getToken();
    const user = getUser();
    if (token && user?.role) {
      redirectByRole(user.role);
      return false;
    }
    return true;
  }

  function ensureStudentPageGuard() {
    const token = getToken();
    const user = getUser();
    if (!token || !user?.role) {
      window.location.replace("/auth/login");
      return false;
    }
    if (user.role !== "student") {
      redirectByRole(user.role);
      return false;
    }
    return true;
  }

  function ensureAdminPageGuard() {
    const token = getToken();
    const user = getUser();
    if (!token || !user?.role) {
      window.location.replace("/auth/login");
      return false;
    }
    if (!isAdminRole(user.role)) {
      if (user.role === "student") {
        window.location.replace("/student");
        return false;
      }
      window.location.replace("/auth/login");
      return false;
    }
    return true;
  }

  window.UI_TEXT = UI_TEXT;
  window.t = t;
  window.formatTemplate = formatTemplate;
  window.statusText = statusText;
  window.seatTypeText = seatTypeText;
  window.roleText = roleText;
  window.resourceTypeText = resourceTypeText;
  window.parseApiError = parseApiError;
  window.applyI18n = applyI18n;
  window.saveSession = saveSession;
  window.clearSession = clearSession;
  window.getToken = getToken;
  window.getUser = getUser;
  window.isAdminRole = isAdminRole;
  window.redirectByRole = redirectByRole;
  window.ensureAuthPageGuard = ensureAuthPageGuard;
  window.ensureStudentPageGuard = ensureStudentPageGuard;
  window.ensureAdminPageGuard = ensureAdminPageGuard;
})();
