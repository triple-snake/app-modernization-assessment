const app = document.getElementById("app");

const state = {
    view: "login",
    systems: [],
    selectedSystemId: null,
    lastRefreshAt: null,
    reportPrompt: "",
    createDraft: {
        name: "",
        description: "",
        difficulty: 50,
        value: 50,
        risk: 50,
    },
};

const groupColors = [
    "#ff5a5f",
    "#5b7cff",
    "#00b5b8",
    "#f59e0b",
];

function nowDateString() {
    return new Date().toISOString().slice(0, 10);
}

function loadPersisted() {
    const cached = localStorage.getItem("ama-demo");
    if (!cached) return;
    try {
        const parsed = JSON.parse(cached);
        state.systems = parsed.systems || [];
        state.selectedSystemId = parsed.selectedSystemId || null;
        state.lastRefreshAt = parsed.lastRefreshAt || null;
    } catch (error) {
        console.warn("Failed to restore state", error);
    }
}

function persist() {
    localStorage.setItem(
        "ama-demo",
        JSON.stringify({
            systems: state.systems,
            selectedSystemId: state.selectedSystemId,
            lastRefreshAt: state.lastRefreshAt,
        })
    );
}

function ensureDailyRefresh() {
    const today = nowDateString();
    if (state.lastRefreshAt !== today) {
        generateSystems();
        state.lastRefreshAt = today;
    }
}

function generateSystems() {
    const names = [
        "물류정산",
        "주문허브",
        "정기결제",
        "고객CRM",
        "입출고",
        "메시징",
        "ERP연동",
        "프로모션",
        "정산API",
        "데이터레이크",
        "품질관리",
        "파트너포털",
    ];

    state.systems = names.map((name, idx) => {
        const difficulty = 20 + Math.round(Math.random() * 70);
        const value = 25 + Math.round(Math.random() * 70);
        const risk = 10 + Math.round(Math.random() * 80);
        return {
            id: `sys-${idx}`,
            name,
            difficulty,
            value,
            risk,
            lastUpdated: nowDateString(),
        };
    });

    assignGroups();
    state.selectedSystemId = state.systems[0]?.id || null;
    persist();
}

function assignGroups() {
    const scored = state.systems.map((item) => ({
        ...item,
        score: item.value - item.difficulty * 0.6 - item.risk * 0.2,
    }));

    const sorted = [...scored].sort((a, b) => b.score - a.score);
    const groupSize = Math.ceil(sorted.length / 4);

    const grouped = sorted.map((item, index) => {
        const group = Math.min(4, Math.floor(index / groupSize) + 1);
        return { ...item, group };
    });

    state.systems = state.systems.map((item) =>
        grouped.find((g) => g.id === item.id)
    );
}

function setView(view) {
    state.view = view;
    render();
}

function selectSystem(id) {
    state.selectedSystemId = id;
    persist();
    render();
}

function refreshSystems() {
    generateSystems();
    state.lastRefreshAt = nowDateString();
    persist();
    render();
}

function openModal(id) {
    document.getElementById(id)?.classList.add("show");
}

function closeModal(id) {
    document.getElementById(id)?.classList.remove("show");
}

function handleLogin(event) {
    event.preventDefault();
    // TODO: 인증 서버 템플릿과 연동
    setView("project-choice");
}

function handleNewProject(event) {
    event.preventDefault();
    setView("dashboard");
}

function handleReportSubmit(event) {
    event.preventDefault();
    const tokens = state.reportPrompt.trim().split(/\s+/).filter(Boolean).length;
    alert(`보고서 생성 요청 완료 (약 ${tokens} 토큰)`);
    closeModal("report-modal");
}

function handleCreateSubmit(event) {
    event.preventDefault();
    const newSystem = {
        id: `sys-${Date.now()}`,
        name: state.createDraft.name || `신규 시스템 ${state.systems.length + 1}`,
        description: state.createDraft.description,
        difficulty: Number(state.createDraft.difficulty),
        value: Number(state.createDraft.value),
        risk: Number(state.createDraft.risk),
        lastUpdated: nowDateString(),
    };

    state.systems = [newSystem, ...state.systems].slice(0, 12);
    assignGroups();
    state.selectedSystemId = newSystem.id;
    persist();
    closeModal("create-modal");
    render();
}

function handleSystemUpdate() {
    alert("시스템 정보 업데이트: 질의서 형식으로 입력을 받는 API 연동 예정");
}

function renderLogin() {
    return `
    <div class="page">
      <div class="brand"><span class="dot"></span> App Modernization Assessment</div>
      <div class="hero">
        <div>
          <h1 style="font-size:32px; margin-bottom:12px;">AI 기반 현대화 적합도 진단</h1>
          <p class="muted" style="line-height:1.6;">로그인 후 기존 프로젝트 대시보드로 이동하거나 신규 프로젝트를 연결할 수 있습니다.</p>
        </div>
        <form class="card pad" onsubmit="handleLogin(event)">
          <h3>로그인</h3>
          <div class="field">
            <label>아이디</label>
            <input name="username" placeholder="user@company.com" required />
          </div>
          <div class="field">
            <label>비밀번호</label>
            <input name="password" type="password" placeholder="********" required />
          </div>
          <div class="button-row">
            <button class="button" type="submit">로그인</button>
            <button class="button ghost" type="button">계정 생성</button>
          </div>
          <div class="helper">인증 서버 템플릿 연동 예정</div>
        </form>
      </div>
    </div>
  `;
}

function renderProjectChoice() {
    return `
    <div class="page">
      <div class="brand"><span class="dot"></span> App Modernization Assessment</div>
      <div class="card pad" style="margin-top:24px;">
        <h2>프로젝트 선택</h2>
        <p class="muted" style="margin-top:8px;">기존 연결 프로젝트로 이동하거나 신규 프로젝트를 등록합니다.</p>
        <div class="choice-grid">
          <div class="choice" onclick="setView('dashboard')">
            <h4>기존 프로젝트</h4>
            <p class="muted" style="margin-top:8px;">바로 메인 대시보드로 전환</p>
          </div>
          <div class="choice" onclick="setView('project-new')">
            <h4>새 프로젝트 연결</h4>
            <p class="muted" style="margin-top:8px;">초기 문서 입력 후 진행</p>
          </div>
        </div>
      </div>
    </div>
  `;
}

function renderProjectNew() {
    return `
    <div class="page">
      <div class="brand"><span class="dot"></span> App Modernization Assessment</div>
      <form class="card pad" style="margin-top:24px;" onsubmit="handleNewProject(event)">
        <h2>초기 문서 입력</h2>
        <div class="field">
          <label>프로젝트명</label>
          <input required placeholder="프로젝트명을 입력하세요" />
        </div>
        <div class="field">
          <label>업무 설명</label>
          <textarea placeholder="업무 개요 및 목표"></textarea>
        </div>
        <div class="field">
          <label>현재 시스템 스택</label>
          <input placeholder="예: Java 8, Oracle, On-prem" />
        </div>
        <div class="button-row">
          <button class="button" type="submit">대시보드로 이동</button>
          <button class="button ghost" type="button" onclick="setView('project-choice')">뒤로</button>
        </div>
      </form>
    </div>
  `;
}

function renderDashboard() {
    ensureDailyRefresh();
    const selected = state.systems.find((sys) => sys.id === state.selectedSystemId) || state.systems[0];
    const selectedGroup = selected?.group || 1;

    return `
    <div class="page">
      <div class="brand"><span class="dot"></span> App Modernization Assessment <span class="badge">데모</span></div>
      <div class="dashboard" style="margin-top:24px;">
        <div class="card">
          <div class="panel-header">
            <div>
              <div style="font-weight:600;">전환 포지셔닝</div>
              <div class="muted" style="font-size:13px; margin-top:4px;">x축: 전환 난이도 / y축: 전환 가치</div>
            </div>
            <button class="button secondary" onclick="refreshSystems()">갱신</button>
          </div>
          <div class="panel-body">
            <div class="chart-wrap">
              <div>
                ${renderChart()}
                <div class="legend">
                  ${groupColors
            .map(
                (color, idx) =>
                    `<div><span class="dot" style="background:${color}"></span>${idx + 1}그룹</div>`
            )
            .join("")}
                </div>
              </div>
              <div>
                <div style="font-weight:600; margin-bottom:10px;">시스템 리스트</div>
                <div class="system-list">
                  ${state.systems
            .map(
                (sys) => `
                        <div class="system-item ${sys.id === selected?.id ? "active" : ""}" onclick="selectSystem('${sys.id}')">
                          <span>${sys.name}</span>
                          <span class="badge">${sys.group}그룹</span>
                        </div>
                      `
            )
            .join("")}
                </div>
              </div>
            </div>
            <div class="helper">데이터는 1일마다 갱신되며, 갱신 버튼을 누르면 즉시 반영됩니다.</div>
          </div>
        </div>

        <div class="card">
          <div class="panel-header">
            <div>
              <div style="font-weight:600;">시스템 상세</div>
              <div class="muted" style="font-size:13px; margin-top:4px;">선택된 시스템의 적합도 및 설명</div>
            </div>
            <div class="muted" style="font-size:12px;">마지막 갱신: ${selected?.lastUpdated || "-"}</div>
          </div>
          <div class="panel-body">
            <div class="detail-title">
              <button class="button ghost" style="padding:6px 10px;" onclick="openModal('create-modal')">
                ${selected?.name || "시스템 선택"}
              </button>
              <span class="helper" style="margin-left:8px;">시스템명 클릭 시 생성 모달</span>
            </div>
            <div class="score">현재 적합도 ${calculateFitness(selected)}점</div>
            <div class="detail-section">
              ${describeSystem(selected)}
            </div>
            <div class="detail-section">
              <span class="tag">${selectedGroup}그룹 특징</span>
              <span class="muted">${groupDescription(selectedGroup)}</span>
            </div>
            <div class="detail-section">
              <div class="stat-card">전환 가치 ${selected?.value ?? "-"} / 전환 난이도 ${selected?.difficulty ?? "-"} / 리스크 ${selected?.risk ?? "-"}</div>
            </div>
            <div class="footer-actions">
              <button class="button" onclick="openModal('create-modal')">시스템 생성</button>
              <button class="button ghost" onclick="handleSystemUpdate()">시스템 정보 update</button>
              <button class="button secondary" onclick="openModal('report-modal')">보고서 생성</button>
            </div>
          </div>
        </div>
      </div>
    </div>

    ${renderReportModal()}
    ${renderCreateModal()}
  `;
}

function calculateFitness(system) {
    if (!system) return "--";
    const raw = system.value * 1.2 - system.difficulty * 0.7 - system.risk * 0.4;
    const normalized = Math.max(0, Math.min(100, Math.round(raw)));
    return normalized;
}

function describeSystem(system) {
    if (!system) return "시스템을 선택하면 상세 정보가 표시됩니다.";
    return `현재 ${system.name}은(는) 전환 가치가 ${system.value}점으로 높고, 난이도는 ${system.difficulty}점입니다. 리스크 ${system.risk}점을 고려하면 단계적 전환이 적합합니다.`;
}

function groupDescription(group) {
    const descriptions = {
        1: "고가치 · 저난이도. 빠른 전환 및 ROI 선점.",
        2: "중간 가치 · 중간 난이도. 안정적 단계 전환 권장.",
        3: "높은 가치 · 높은 난이도. 집중 투자 또는 분할 전환.",
        4: "낮은 가치 · 높은 난이도. 유지보수 중심 전략.",
    };
    return descriptions[group] || "그룹 정보 없음";
}

function renderChart() {
    const width = 460;
    const height = 320;
    const padding = 40;

    const points = state.systems.map((sys) => ({
        x: padding + ((width - padding * 2) * sys.difficulty) / 100,
        y: height - padding - ((height - padding * 2) * sys.value) / 100,
        color: groupColors[(sys.group || 1) - 1],
        label: sys.name,
    }));

    return `
    <svg width="${width}" height="${height}" viewBox="0 0 ${width} ${height}" style="background:#fff;border:1px solid var(--border);border-radius:14px;">
      <line x1="${padding}" y1="${height - padding}" x2="${width - padding}" y2="${height - padding}" stroke="#d1d5db" />
      <line x1="${padding}" y1="${padding}" x2="${padding}" y2="${height - padding}" stroke="#d1d5db" />
      <text x="${width / 2}" y="${height - 8}" text-anchor="middle" font-size="12" fill="#6b7280">전환 난이도</text>
      <text x="14" y="${height / 2}" text-anchor="middle" font-size="12" fill="#6b7280" transform="rotate(-90 14 ${height / 2})">전환 가치</text>
      ${points
            .map(
                (p) => `
        <g>
          <circle cx="${p.x}" cy="${p.y}" r="6" fill="${p.color}" />
        </g>
      `
            )
            .join("")}
    </svg>
  `;
}

function renderReportModal() {
    return `
    <div class="modal-backdrop" id="report-modal" onclick="if (event.target.id === 'report-modal') closeModal('report-modal')">
      <div class="modal">
        <div class="modal-header">
          <div style="font-weight:600;">보고서 생성</div>
          <button class="button ghost" onclick="closeModal('report-modal')">닫기</button>
        </div>
        <form onsubmit="handleReportSubmit(event)">
          <div class="modal-body">
            <div class="field">
              <label>프롬프트</label>
              <textarea placeholder="예) 미래의 적합도, 현재 적합도, 개발자 관점, CEO 관점" oninput="state.reportPrompt = this.value">${state.reportPrompt || ""}</textarea>
            </div>
            <div class="helper">입력된 프롬프트를 토큰 계산 후 전송합니다.</div>
          </div>
          <div class="modal-actions">
            <button type="button" class="button ghost" onclick="closeModal('report-modal')">취소</button>
            <button type="submit" class="button">생성</button>
          </div>
        </form>
      </div>
    </div>
  `;
}

function renderCreateModal() {
    return `
    <div class="modal-backdrop" id="create-modal" onclick="if (event.target.id === 'create-modal') closeModal('create-modal')">
      <div class="modal">
        <div class="modal-header">
          <div style="font-weight:600;">시스템 생성</div>
          <button class="button ghost" onclick="closeModal('create-modal')">닫기</button>
        </div>
        <form onsubmit="handleCreateSubmit(event)">
          <div class="modal-body">
            <div class="field">
              <label>시스템명</label>
              <input placeholder="시스템명 입력" value="${state.createDraft.name}" oninput="state.createDraft.name = this.value" />
            </div>
            <div class="field">
              <label>설명 (질의서 형식)</label>
              <textarea placeholder="업무 목적, 사용자, 핵심 기능" oninput="state.createDraft.description = this.value">${state.createDraft.description || ""}</textarea>
            </div>
            <div class="range-grid">
              <div class="field">
                <label>전환 난이도</label>
                <input type="range" min="0" max="100" value="${state.createDraft.difficulty}" oninput="state.createDraft.difficulty = this.value" />
                <div class="helper">${state.createDraft.difficulty}</div>
              </div>
              <div class="field">
                <label>전환 가치</label>
                <input type="range" min="0" max="100" value="${state.createDraft.value}" oninput="state.createDraft.value = this.value" />
                <div class="helper">${state.createDraft.value}</div>
              </div>
              <div class="field">
                <label>리스크</label>
                <input type="range" min="0" max="100" value="${state.createDraft.risk}" oninput="state.createDraft.risk = this.value" />
                <div class="helper">${state.createDraft.risk}</div>
              </div>
            </div>
            <div class="stat-card">그래프 미리보기: 난이도 ${state.createDraft.difficulty} / 가치 ${state.createDraft.value}</div>
          </div>
          <div class="modal-actions">
            <button type="button" class="button ghost" onclick="closeModal('create-modal')">취소</button>
            <button type="submit" class="button">생성</button>
          </div>
        </form>
      </div>
    </div>
  `;
}

function render() {
    if (state.view === "login") {
        app.innerHTML = renderLogin();
        return;
    }
    if (state.view === "project-choice") {
        app.innerHTML = renderProjectChoice();
        return;
    }
    if (state.view === "project-new") {
        app.innerHTML = renderProjectNew();
        return;
    }
    if (state.view === "dashboard") {
        app.innerHTML = renderDashboard();
    }
}

loadPersisted();
if (!state.systems.length) {
    generateSystems();
}
render();
