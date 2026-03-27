const el = {
  tabLogin: document.getElementById("tabLogin"),
  tabRegister: document.getElementById("tabRegister"),
  loginForm: document.getElementById("loginForm"),
  registerForm: document.getElementById("registerForm"),
  loginPhone: document.getElementById("loginPhone"),
  loginPassword: document.getElementById("loginPassword"),
  registerName: document.getElementById("registerName"),
  registerPhone: document.getElementById("registerPhone"),
  registerEmail: document.getElementById("registerEmail"),
  registerPassword: document.getElementById("registerPassword"),
  authOutput: document.getElementById("authOutput"),
};

function setOutput(value) {
  el.authOutput.textContent = typeof value === "string" ? value : JSON.stringify(value, null, 2);
}

function switchTab(mode) {
  const login = mode === "login";
  el.tabLogin.classList.toggle("active", login);
  el.tabRegister.classList.toggle("active", !login);
  el.loginForm.classList.toggle("active", login);
  el.registerForm.classList.toggle("active", !login);
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
  if (status === 409) {
    return window.t("errors.accountExists");
  }
  return window.parseApiError(status);
}

async function request(path, method, body) {
  let response;
  try {
    response = await fetch(`/api/auth${path}`, {
      method,
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify(body),
    });
  } catch {
    throw new Error(window.t("errors.network"));
  }

  const text = await response.text();
  let data = null;
  try {
    data = text ? JSON.parse(text) : null;
  } catch {
    data = null;
  }

  if (!response.ok) {
    throw new Error(parseApiErrorMessage(response.status, data));
  }
  if (data && typeof data === "object" && Object.prototype.hasOwnProperty.call(data, "code")) {
    return data.data;
  }
  return data;
}

async function login(account, password) {
  const result = await request("/login", "POST", { account, password });
  window.saveSession({
    accessToken: result.access_token,
    refreshToken: result.refresh_token,
    user: result.user,
  });
  window.redirectByRole(result.user.role);
}

async function register(name, phone, email, password) {
  const result = await request("/register", "POST", {
    nickname: name,
    phone: phone || null,
    email: email || null,
    password,
  });
  window.saveSession({
    accessToken: result.access_token,
    refreshToken: result.refresh_token,
    user: result.user,
  });
  window.redirectByRole(result.user.role);
}

function validateLoginForm() {
  if (!el.loginPhone.value.trim()) {
    throw new Error(window.t("errors.accountRequired"));
  }
  if (!el.loginPassword.value.trim()) {
    throw new Error(window.t("errors.passwordRequired"));
  }
}

function validateRegisterForm() {
  if (!el.registerName.value.trim()) {
    throw new Error(window.t("errors.nameRequired"));
  }
  if (!el.registerPhone.value.trim() && !el.registerEmail.value.trim()) {
    throw new Error(window.t("errors.accountRequired"));
  }
  if (!el.registerPassword.value.trim()) {
    throw new Error(window.t("errors.passwordRequired"));
  }
}

function bind() {
  el.tabLogin.addEventListener("click", () => switchTab("login"));
  el.tabRegister.addEventListener("click", () => switchTab("register"));

  el.loginForm.addEventListener("submit", async (event) => {
    event.preventDefault();
    try {
      validateLoginForm();
      await login(el.loginPhone.value.trim(), el.loginPassword.value.trim());
    } catch (error) {
      setOutput(error.message || window.t("errors.loginFailed"));
    }
  });

  el.registerForm.addEventListener("submit", async (event) => {
    event.preventDefault();
    try {
      validateRegisterForm();
      await register(
        el.registerName.value.trim(),
        el.registerPhone.value.trim(),
        el.registerEmail.value.trim(),
        el.registerPassword.value.trim(),
      );
    } catch (error) {
      setOutput(error.message || window.t("errors.registerFailed"));
    }
  });
}

window.applyI18n(document);
if (window.ensureAuthPageGuard()) {
  if (window.location.pathname === "/auth/register") {
    switchTab("register");
  }
  setOutput(window.t("auth.outputInit"));
  bind();
}
