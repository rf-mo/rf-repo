const STORAGE_KEYS = {
  profile: "pm-profile",
  projects: "pm-projects",
  weekly: "pm-weekly",
  monthly: "pm-monthly",
};

const profileFields = {
  name: document.getElementById("profileName"),
  role: document.getElementById("profileRole"),
  company: document.getElementById("profileCompany"),
  focusMonth: document.getElementById("focusMonth"),
};

const lists = {
  projects: document.getElementById("projectList"),
  weekly: document.getElementById("weeklyList"),
  monthly: document.getElementById("monthlyList"),
};

const template = document.getElementById("itemTemplate");

function readState(key, fallback) {
  try {
    const raw = localStorage.getItem(key);
    return raw ? JSON.parse(raw) : fallback;
  } catch {
    return fallback;
  }
}

function saveState(key, value) {
  localStorage.setItem(key, JSON.stringify(value));
}

function loadProfile() {
  const profile = readState(STORAGE_KEYS.profile, {
    name: "",
    role: "Google Cloud Solution Consultant",
    company: "Softchoice",
    focusMonth: "",
  });

  profileFields.name.value = profile.name;
  profileFields.role.value = profile.role;
  profileFields.company.value = profile.company;
  profileFields.focusMonth.value = profile.focusMonth;
}

function renderList(type, items) {
  const list = lists[type];
  list.innerHTML = "";

  if (!items.length) {
    const empty = document.createElement("li");
    empty.className = "item-row";
    empty.textContent = "No entries yet.";
    list.appendChild(empty);
    return;
  }

  items.forEach((item, index) => {
    const clone = template.content.firstElementChild.cloneNode(true);
    const content = clone.querySelector(".item-content");
    const removeButton = clone.querySelector(".danger");

    if (type === "projects") {
      content.innerHTML = `<strong>${item.name}</strong> (${item.stage})<br>${item.client}<br>Milestone: ${item.date}<br>${item.notes || "No notes"}`;
    }

    if (type === "weekly") {
      content.innerHTML = `<strong>${item.task}</strong><br>Week: ${item.weekStart}<br>Priority: ${item.priority}`;
    }

    if (type === "monthly") {
      content.innerHTML = `<strong>${item.outcome}</strong><br>Month: ${item.month}<br>Status: ${item.status}`;
    }

    removeButton.addEventListener("click", () => {
      const next = readState(STORAGE_KEYS[type], []);
      next.splice(index, 1);
      saveState(STORAGE_KEYS[type], next);
      renderList(type, next);
    });

    list.appendChild(clone);
  });
}

function initializeLists() {
  renderList("projects", readState(STORAGE_KEYS.projects, []));
  renderList("weekly", readState(STORAGE_KEYS.weekly, []));
  renderList("monthly", readState(STORAGE_KEYS.monthly, []));
}

function setupForm(formId, storageKey, mapper, listType) {
  const form = document.getElementById(formId);

  form.addEventListener("submit", (event) => {
    event.preventDefault();
    const entry = mapper();
    const current = readState(storageKey, []);
    current.push(entry);
    saveState(storageKey, current);
    renderList(listType, current);
    form.reset();
  });
}

document.getElementById("saveProfile").addEventListener("click", () => {
  saveState(STORAGE_KEYS.profile, {
    name: profileFields.name.value.trim(),
    role: profileFields.role.value.trim(),
    company: profileFields.company.value.trim(),
    focusMonth: profileFields.focusMonth.value,
  });
});

setupForm(
  "projectForm",
  STORAGE_KEYS.projects,
  () => ({
    name: document.getElementById("projectName").value.trim(),
    client: document.getElementById("projectClient").value.trim(),
    stage: document.getElementById("projectStage").value,
    date: document.getElementById("projectDate").value,
    notes: document.getElementById("projectNotes").value.trim(),
  }),
  "projects"
);

setupForm(
  "weeklyForm",
  STORAGE_KEYS.weekly,
  () => ({
    weekStart: document.getElementById("weekStart").value,
    priority: document.getElementById("weekPriority").value,
    task: document.getElementById("weekTask").value.trim(),
  }),
  "weekly"
);

setupForm(
  "monthlyForm",
  STORAGE_KEYS.monthly,
  () => ({
    month: document.getElementById("monthLabel").value,
    status: document.getElementById("monthStatus").value,
    outcome: document.getElementById("monthOutcome").value.trim(),
  }),
  "monthly"
);

loadProfile();
initializeLists();
