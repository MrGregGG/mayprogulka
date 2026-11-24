(() => {
  const STYLES = {
    light: "https://tiles.openfreemap.org/styles/bright",
    dark: "https://tiles.openfreemap.org/styles/dark"
  };

  const ROUTE_PALETTES = {
    light: [
      "#D9FF80", "#C2FF4D", "#B5FF2A", "#A6FF00", "#98F000",
      "#89E100", "#7BD300", "#6DC500", "#60B700", "#54A900",
      "#489B00", "#3D8D00", "#327F00"
    ],
    dark: [
      "#FFD0A3", "#FFC27A", "#FFB457", "#FFA033", "#FF920F",
      "#FF8500", "#F77900", "#E96D00", "#DB6200", "#CD5700",
      "#BF4D00", "#A94200", "#933700"
    ]
  };

  const FINISH_COLORS = {
    light: "#0B0B0B",
    dark: "#FFFFFF"
  };

  function routePalette() {
    return ROUTE_PALETTES[state.theme] || ROUTE_PALETTES.light;
  }

  function finishColor() {
    return FINISH_COLORS[state.theme] || FINISH_COLORS.light;
  }

  function refreshRouteColors() {
    const palette = routePalette();
    state.colors.clear();
    state.routes.forEach((route, index) => state.colors.set(route.id, palette[index % palette.length]));
    if (state.routes.length) renderList(state.routes);
  }

  const state = {
    map: null,
    mapReady: false,
    mapFailed: false,
    theme: "light",
    styleRevision: 0,
    routeLayers: new Map(),
    routes: [],
    selected: new Set(),
    colors: new Map()
  };

  const el = (id) => document.getElementById(id);

  function escapeHtml(value) {
    return String(value ?? "").replace(/[&<>"']/g, (char) => ({
      "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;"
    }[char]));
  }

  function savedTheme() {
    try {
      const value = localStorage.getItem("mayprogulka-theme");
      return value === "dark" || value === "light" ? value : "light";
    } catch (_) {
      return "light";
    }
  }

  function setThemeButton() {
    const dark = state.theme === "dark";
    const themeMeta = document.querySelector('meta[name="theme-color"]');
    if (themeMeta) themeMeta.setAttribute("content", dark ? "#050505" : "#FFFFFF");
    const button = el("theme-toggle");
    if (button) {
      button.setAttribute("aria-pressed", String(dark));
      button.setAttribute("aria-label", dark ? "Включить светлую тему" : "Включить тёмную тему");
    }
    if (el("theme-icon")) el("theme-icon").textContent = dark ? "☀" : "☾";
    if (el("theme-label")) el("theme-label").textContent = dark ? "Светлая тема" : "Тёмная тема";
  }

  function enhanceDarkMapStyle() {
    if (!state.map || !state.mapReady || state.theme !== "dark") return;

    const style = state.map.getStyle();
    const layers = Array.isArray(style?.layers) ? style.layers : [];

    for (const layer of layers) {
      if (layer.type !== "line") continue;

      const id = String(layer.id || "").toLowerCase();
      const sourceLayer = String(layer["source-layer"] || "").toLowerCase();
      const hint = `${id} ${sourceLayer}`;

      // Only transportation/road geometry. Do not touch our GPX routes,
      // railways, ferries or administrative boundaries.
      if (id.startsWith("route-line-")) continue;
      if (!/(road|highway|motorway|trunk|primary|secondary|tertiary|street|transportation|residential|service|path|track|bridge|tunnel)/.test(hint)) continue;
      if (/(rail|railway|ferry|aerialway|boundary|admin)/.test(hint)) continue;

      let color = "#566779";
      let opacity = 0.92;

      if (/(casing|outline)/.test(hint)) {
        color = "#263541";
        opacity = 0.98;
      } else if (/(motorway|trunk|primary)/.test(hint)) {
        color = "#8493A3";
        opacity = 0.98;
      } else if (/(secondary|tertiary)/.test(hint)) {
        color = "#708091";
        opacity = 0.96;
      } else if (/(residential|service|street|minor)/.test(hint)) {
        color = "#5C6D7E";
        opacity = 0.94;
      } else if (/(path|track|pedestrian)/.test(hint)) {
        color = "#465767";
        opacity = 0.90;
      }

      try {
        state.map.setPaintProperty(layer.id, "line-color", color);
        state.map.setPaintProperty(layer.id, "line-opacity", opacity);
      } catch (error) {
        // Some style layers use patterns or unsupported paint combinations.
        // Leaving those layers unchanged is safer than failing the whole map.
      }
    }
  }

  function applyTheme(theme) {
    state.theme = theme === "dark" ? "dark" : "light";
    document.body.dataset.theme = state.theme;
    setThemeButton();
    refreshRouteColors();
    try { localStorage.setItem("mayprogulka-theme", state.theme); } catch (_) {}

    if (!state.map || !state.mapReady || state.mapFailed) return;

    state.mapReady = false;
    state.routeLayers.clear();
    const revision = ++state.styleRevision;
    try {
      state.map.setStyle(STYLES[state.theme]);
      state.map.once("style.load", () => {
        if (revision !== state.styleRevision) return;
        state.mapReady = true;
        enhanceDarkMapStyle();
        syncMap().catch(console.error);
      });
    } catch (error) {
      console.error("Theme map style error:", error);
    }
  }

  function getFilters() {
    const params = new URLSearchParams();
    params.set("year", el("filter-year").value);
    params.set("type", el("filter-type").value);
    params.set("start", el("filter-start").value);
    params.set("min_distance", el("filter-min").value);
    params.set("max_distance", el("filter-max").value);
    return params;
  }

  function fillOptions(data) {
    const yearSelect = el("filter-year");
    const startSelect = el("filter-start");
    const currentYear = yearSelect.value || "2026";
    const currentStart = startSelect.value || "all";

    yearSelect.innerHTML = '<option value="all">Все годы</option>' + data.years.map((year) => `<option value="${year}">${year}</option>`).join("");
    startSelect.innerHTML = '<option value="all">Все места</option>' + data.starts.map((start) => `<option value="${escapeHtml(start)}">${escapeHtml(start)}</option>`).join("");

    el("stat-routes").textContent = String(data.count);
    el("stat-years").textContent = String(data.years.length);
    yearSelect.value = data.years.includes(Number(currentYear)) ? currentYear : "all";
    startSelect.value = data.starts.includes(currentStart) ? currentStart : "all";
  }

  function renderList(routes) {
    const list = el("route-list");
    el("result-count").textContent = `${routes.length} найдено`;

    if (!routes.length) {
      list.innerHTML = '<div class="empty-state">По выбранным условиям маршруты не найдены.<br>Попробуйте изменить фильтры.</div>';
      return;
    }

    list.innerHTML = routes.map((route) => {
      const color = state.colors.get(route.id);
      const checked = state.selected.has(route.id) ? "checked" : "";
      return `<div class="route-item">
        <input id="route-${route.id}" type="checkbox" data-route-id="${route.id}" ${checked} aria-label="Показать маршрут ${escapeHtml(route.name)}">
        <span class="route-main">
          <label class="route-title" for="route-${route.id}">${escapeHtml(route.name)}</label>
          <span class="route-meta"><span>${route.year}</span><span>·</span><span>${escapeHtml(route.type_label)}</span></span>
          <span class="route-meta"><span>${escapeHtml(route.start_place)}</span></span>
          <span class="route-meta"><a class="route-download" href="${route.download_url}">Скачать GPX</a></span>
        </span>
        <span class="route-distance" style="border-left:3px solid ${color}">${Number(route.distance_km).toLocaleString("ru-RU")} км</span>
      </div>`;
    }).join("");

    list.querySelectorAll("input[data-route-id]").forEach((checkbox) => {
      checkbox.addEventListener("change", () => {
        const id = Number(checkbox.dataset.routeId);
        if (checkbox.checked) state.selected.add(id); else state.selected.delete(id);
        el("selected-count").textContent = `Выбрано: ${state.selected.size}`;
        syncMap().catch(console.error);
      });
    });
  }

  function getCoordinates(geometry) {
    if (!geometry) return [];
    if (geometry.type === "LineString") return geometry.coordinates || [];
    if (geometry.type === "MultiLineString") return (geometry.coordinates || []).flat();
    return [];
  }

  async function loadRouteGeometry(route) {
    if (route.geojson && route._coordinates) return route.geojson;
    const response = await fetch(route.geojson_url, { cache: "no-store" });
    if (!response.ok) throw new Error(`Не удалось загрузить геометрию маршрута ${route.name}`);
    route.geojson = await response.json();
    route._coordinates = getCoordinates(route.geojson.geometry);
    return route.geojson;
  }

  function layerIds(id) {
    return {
      lineSource: `route-line-source-${id}`, startSource: `route-start-source-${id}`, finishSource: `route-finish-source-${id}`,
      line: `route-line-${id}`, start: `route-start-${id}`, finish: `route-finish-${id}`
    };
  }

  function addRouteToMap(route) {
    if (!state.map || !state.mapReady || state.mapFailed || state.routeLayers.has(route.id)) return;
    if (!route.geojson || !route._coordinates?.length || !state.selected.has(route.id)) return;

    const ids = layerIds(route.id);
    const color = state.colors.get(route.id);
    const coords = route._coordinates;

    state.map.addSource(ids.lineSource, { type: "geojson", data: { type: "Feature", properties: { route_id: route.id }, geometry: route.geojson.geometry } });
    state.map.addLayer({ id: ids.line, type: "line", source: ids.lineSource, layout: { "line-cap": "round", "line-join": "round" }, paint: { "line-color": color, "line-width": 4.5, "line-opacity": .96 } });

    const pointFeature = (coordinates, kind) => ({ type: "Feature", properties: { route_id: route.id, kind }, geometry: { type: "Point", coordinates } });
    state.map.addSource(ids.startSource, { type: "geojson", data: pointFeature(coords[0], "start") });
    state.map.addLayer({ id: ids.start, type: "circle", source: ids.startSource, paint: { "circle-radius": 6, "circle-color": color, "circle-stroke-color": "#fff", "circle-stroke-width": 2 } });
    state.map.addSource(ids.finishSource, { type: "geojson", data: pointFeature(coords[coords.length - 1], "finish") });
    state.map.addLayer({ id: ids.finish, type: "circle", source: ids.finishSource, paint: { "circle-radius": 5, "circle-color": finishColor(), "circle-stroke-color": "#fff", "circle-stroke-width": 2 } });
    state.routeLayers.set(route.id, ids);
  }

  function removeRouteFromMap(id) {
    const ids = state.routeLayers.get(id);
    if (!ids || !state.map || !state.mapReady) { state.routeLayers.delete(id); return; }
    [ids.finish, ids.start, ids.line].forEach((layerId) => { if (state.map.getLayer(layerId)) state.map.removeLayer(layerId); });
    [ids.finishSource, ids.startSource, ids.lineSource].forEach((sourceId) => { if (state.map.getSource(sourceId)) state.map.removeSource(sourceId); });
    state.routeLayers.delete(id);
  }

  function fitSelectedRoutes() {
    if (!state.map || !state.mapReady || state.mapFailed || typeof maplibregl === "undefined") return;
    const coordinates = [];
    state.routes.forEach((route) => { if (state.selected.has(route.id) && route._coordinates) coordinates.push(...route._coordinates); });
    if (!coordinates.length) { state.map.flyTo({ center: [60.5975, 56.8389], zoom: 11, duration: 350 }); return; }
    const bounds = new maplibregl.LngLatBounds();
    coordinates.forEach((point) => bounds.extend(point));
    if (!bounds.isEmpty()) state.map.fitBounds(bounds, { padding: { top: 55, right: 55, bottom: 55, left: 55 }, maxZoom: 14, duration: 500 });
  }

  function showRoutePopup(event) {
    if (!state.map || !state.mapReady || state.mapFailed || typeof maplibregl === "undefined") return;
    const visibleLayers = [...state.routeLayers.values()].map((ids) => ids.line).filter((id) => state.map.getLayer(id));
    if (!visibleLayers.length) return;
    const features = state.map.queryRenderedFeatures(event.point, { layers: visibleLayers });
    if (!features.length) return;
    const routeId = Number(features[0].properties.route_id);
    const route = state.routes.find((item) => item.id === routeId);
    if (!route) return;
    const popupHtml = `<div class="popup-title">${escapeHtml(route.name)}</div><div class="popup-meta">${route.year} год · ${Number(route.distance_km).toLocaleString("ru-RU")} км<br>${escapeHtml(route.start_place)}</div><a class="popup-download" href="${route.download_url}">Скачать GPX</a>`;
    new maplibregl.Popup({ closeButton: true, closeOnClick: true, offset: 12 }).setLngLat(event.lngLat).setHTML(popupHtml).addTo(state.map);
  }

  function showMapFailure(message) {
    state.mapFailed = true;
    state.mapReady = false;
    const wrap = document.querySelector(".map-canvas-wrap");
    if (!wrap) return;
    if (!wrap.querySelector(".map-fallback")) {
      wrap.insertAdjacentHTML("beforeend", `<div class="map-fallback"><div class="map-fallback-inner"><div class="map-fallback-icon">!</div><strong>${escapeHtml(message)}</strong><p>Фильтры и список маршрутов продолжат работать. Проверь подключение к интернету и обнови страницу.</p></div></div>`);
    }
    wrap.classList.add("map-error");
  }

  function initMap() {
    if (typeof window.maplibregl === "undefined") {
      showMapFailure("Библиотека карты не загрузилась.");
      return Promise.resolve(false);
    }

    return new Promise((resolve) => {
      let resolved = false;
      const done = (ok) => { if (resolved) return; resolved = true; resolve(ok); };
      try {
        state.map = new maplibregl.Map({ container: "map", style: STYLES[state.theme], center: [60.5975, 56.8389], zoom: 11, minZoom: 4, maxZoom: 19, attributionControl: { compact: true }, renderWorldCopies: false });
        state.map.addControl(new maplibregl.NavigationControl({ showCompass: false, visualizePitch: false }), "top-right");
        const timeout = setTimeout(() => {
          if (!state.mapReady) { showMapFailure("Карта не смогла загрузить подложку."); done(false); }
        }, 12000);
        state.map.once("load", () => {
          clearTimeout(timeout);
          state.mapReady = true;
          state.mapFailed = false;
          enhanceDarkMapStyle();
          state.map.on("click", showRoutePopup);
          state.map.on("mousemove", (event) => {
            if (!state.mapReady) return;
            const layers = [...state.routeLayers.values()].map((ids) => ids.line).filter((id) => state.map.getLayer(id));
            if (!layers.length) { state.map.getCanvas().style.cursor = ""; return; }
            const features = state.map.queryRenderedFeatures(event.point, { layers });
            state.map.getCanvas().style.cursor = features.length ? "pointer" : "";
          });
          done(true);
        });
        state.map.on("error", (event) => { if (event?.error) console.error("MapLibre/OpenFreeMap:", event.error); });
      } catch (error) {
        console.error(error);
        showMapFailure("Не удалось запустить интерактивную карту.");
        done(false);
      }
    });
  }

  async function syncMap() {
    el("selected-count").textContent = `Выбрано: ${state.selected.size}`;
    if (!state.map || !state.mapReady || state.mapFailed) return;
    for (const id of [...state.routeLayers.keys()]) if (!state.selected.has(id)) removeRouteFromMap(id);
    for (const route of state.routes.filter((route) => state.selected.has(route.id))) {
      try { await loadRouteGeometry(route); if (state.selected.has(route.id)) addRouteToMap(route); } catch (error) { console.error(error); }
    }
    fitSelectedRoutes();
  }

  async function loadRoutes() {
    const list = el("route-list");
    list.innerHTML = '<div class="loading-state">Загружаем маршруты…</div>';
    el("result-count").textContent = "Загрузка…";
    const response = await fetch(`/api/routes/?${getFilters().toString()}`, { cache: "no-store" });
    if (!response.ok) throw new Error("Не удалось получить список маршрутов");
    const data = await response.json();

    if (state.map && state.mapReady) for (const id of [...state.routeLayers.keys()]) removeRouteFromMap(id); else state.routeLayers.clear();
    state.routes = data.routes;
    const palette = routePalette();
    state.colors.clear();
    state.routes.forEach((route, index) => state.colors.set(route.id, palette[index % palette.length]));
    state.selected = new Set(state.routes.map((route) => route.id));
    renderList(state.routes);
    el("selected-count").textContent = `Выбрано: ${state.selected.size}`;

    if (state.mapReady && !state.mapFailed) await syncMap();
  }

  function showRouteError(error) {
    console.error(error);
    el("route-list").innerHTML = '<div class="empty-state">Не удалось загрузить маршруты. Проверь, что Django-сервер запущен, и обнови страницу.</div>';
    el("result-count").textContent = "Ошибка загрузки";
  }

  function bindControls() {
    el("theme-toggle").addEventListener("click", () => applyTheme(state.theme === "dark" ? "light" : "dark"));
    ["filter-year", "filter-type", "filter-start"].forEach((id) => el(id).addEventListener("change", () => loadRoutes().catch(showRouteError)));
    ["filter-min", "filter-max"].forEach((id) => el(id).addEventListener("change", () => loadRoutes().catch(showRouteError)));
    el("reset-filters").addEventListener("click", () => {
      el("filter-year").value = "all"; el("filter-type").value = "all"; el("filter-start").value = "all"; el("filter-min").value = "0"; el("filter-max").value = "70";
      loadRoutes().catch(showRouteError);
    });
  }

  async function bootstrap() {
    state.theme = savedTheme();
    document.body.dataset.theme = state.theme;
    setThemeButton();
    bindControls();

    // Critical: data/filter initialization is independent from the map library.
    try {
      const response = await fetch("/api/routes/", { cache: "no-store" });
      if (!response.ok) throw new Error("Не удалось получить исходные данные маршрутов");
      const data = await response.json();
      fillOptions(data);
      el("filter-year").value = data.years.includes(2026) ? "2026" : "all";
      await loadRoutes();
    } catch (error) {
      showRouteError(error);
    }

    // Map starts afterwards. If it fails, filters remain functional.
    const mapOk = await initMap();
    if (mapOk) await syncMap();
  }

  if (document.readyState === "loading") document.addEventListener("DOMContentLoaded", bootstrap); else bootstrap();
})();
