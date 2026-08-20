(async function () {
  const canvasEl = document.getElementById("canvas");
  const boxCanvas = new BoxCanvas(canvasEl);

  const state = {
    images: [],
    classes: [],
    currentIndex: -1,
    dirty: false,
  };

  const el = {
    progress: document.getElementById("progress"),
    imageList: document.getElementById("image-list"),
    classList: document.getElementById("class-list"),
    boxList: document.getElementById("box-list"),
    imageName: document.getElementById("image-name"),
    saveStatus: document.getElementById("save-status"),
    prevBtn: document.getElementById("prev-btn"),
    nextBtn: document.getElementById("next-btn"),
    exportBtn: document.getElementById("export-btn"),
    exportModal: document.getElementById("export-modal"),
    exportConfirmBtn: document.getElementById("export-confirm-btn"),
    exportCancelBtn: document.getElementById("export-cancel-btn"),
    exportResult: document.getElementById("export-result"),
    trainPct: document.getElementById("train-pct"),
    valPct: document.getElementById("val-pct"),
    testPct: document.getElementById("test-pct"),
  };

  function setDirty(v) {
    state.dirty = v;
    el.saveStatus.textContent = v ? "Cambios sin guardar" : "Guardado";
    el.saveStatus.className = v ? "dirty" : "";
  }

  function currentImage() {
    return state.images[state.currentIndex];
  }

  async function saveCurrentIfDirty() {
    if (!state.dirty || state.currentIndex < 0) return;
    const img = currentImage();
    const boxes = boxCanvas.getBoxes();
    await api.saveAnnotations(img.filename, boxes);
    img.labeled = true;
    img.box_count = boxes.length;
    setDirty(false);
    renderImageList();
    renderProgress();
  }

  function renderProgress() {
    const labeled = state.images.filter((i) => i.labeled).length;
    el.progress.textContent = `${labeled} / ${state.images.length} etiquetadas`;
  }

  function renderImageList() {
    el.imageList.innerHTML = "";
    state.images.forEach((img, i) => {
      const li = document.createElement("li");
      li.textContent = img.filename;
      li.className = (img.labeled ? "labeled" : "pending") + (i === state.currentIndex ? " active" : "");
      li.addEventListener("click", () => goToIndex(i));
      el.imageList.appendChild(li);
    });
  }

  function renderClassList() {
    el.classList.innerHTML = "";
    state.classes.forEach((name, i) => {
      const li = document.createElement("li");
      li.textContent = `${i}: ${name}`;
      li.addEventListener("click", () => boxCanvas.setClassOfSelected(i));
      el.classList.appendChild(li);
    });
  }

  function renderBoxList() {
    el.boxList.innerHTML = "";
    boxCanvas.boxes.forEach((box, i) => {
      const li = document.createElement("li");
      const label = state.classes[box.class_id] || box.class_id;
      const swatch = document.createElement("span");
      swatch.className = "box-color-swatch";
      swatch.style.background = BOX_COLORS[box.class_id % BOX_COLORS.length];
      const text = document.createElement("span");
      text.textContent = label;
      text.style.flex = "1";
      const del = document.createElement("span");
      del.className = "box-delete";
      del.textContent = "✕";
      del.addEventListener("click", (e) => {
        e.stopPropagation();
        boxCanvas.selectIndex(i);
        boxCanvas.deleteSelected();
      });

      li.appendChild(swatch);
      li.appendChild(text);
      li.appendChild(del);
      li.className = i === boxCanvas.selectedIndex ? "active" : "";
      li.addEventListener("click", () => boxCanvas.selectIndex(i));
      el.boxList.appendChild(li);
    });
  }

  boxCanvas.onBoxesChanged = () => {
    setDirty(true);
    renderBoxList();
  };
  boxCanvas.onSelectionChanged = () => {
    renderBoxList();
  };

  async function goToIndex(i) {
    if (i < 0 || i >= state.images.length || i === state.currentIndex) return;
    await saveCurrentIfDirty();
    state.currentIndex = i;
    const img = currentImage();
    el.imageName.textContent = `${img.filename} (${i + 1}/${state.images.length})`;
    const annotations = await api.getAnnotations(img.filename);
    await boxCanvas.loadImage(`/images/${encodeURIComponent(img.filename)}`, annotations.boxes);
    setDirty(false);
    renderImageList();
    renderBoxList();
  }

  el.prevBtn.addEventListener("click", () => goToIndex(state.currentIndex - 1));
  el.nextBtn.addEventListener("click", () => goToIndex(state.currentIndex + 1));

  window.addEventListener("keydown", async (e) => {
    if (e.target.tagName === "INPUT") return;

    if (e.key >= "0" && e.key <= "9") {
      const digit = parseInt(e.key, 10);
      const classId = digit === 0 ? 9 : digit - 1;
      if (classId < state.classes.length) {
        boxCanvas.setClassOfSelected(classId);
      }
    } else if (e.key === "Delete" || e.key === "Backspace") {
      if (document.activeElement === document.body) {
        boxCanvas.deleteSelected();
      }
    } else if (e.key === "a" || e.key === "ArrowLeft") {
      goToIndex(state.currentIndex - 1);
    } else if (e.key === "d" || e.key === "ArrowRight") {
      goToIndex(state.currentIndex + 1);
    } else if (e.key === "s") {
      await saveCurrentIfDirty();
    } else if (e.key === "Escape") {
      boxCanvas.deselect();
    } else if (e.key === "[") {
      boxCanvas.cycleClassOfSelected(-1);
    } else if (e.key === "]") {
      boxCanvas.cycleClassOfSelected(1);
    }
  });

  window.addEventListener("beforeunload", (e) => {
    if (state.dirty) {
      e.preventDefault();
      e.returnValue = "";
    }
  });

  window.addEventListener("resize", () => boxCanvas.resizeCanvas());

  el.exportBtn.addEventListener("click", async () => {
    await saveCurrentIfDirty();
    el.exportResult.textContent = "";
    el.exportModal.classList.remove("hidden");
  });
  el.exportCancelBtn.addEventListener("click", () => {
    el.exportModal.classList.add("hidden");
  });
  el.exportConfirmBtn.addEventListener("click", async () => {
    const train = parseFloat(el.trainPct.value) / 100;
    const val = parseFloat(el.valPct.value) / 100;
    const test = parseFloat(el.testPct.value) / 100;
    try {
      const result = await api.exportDataset(train, val, test);
      el.exportResult.textContent = JSON.stringify(result, null, 2);
      renderImageList();
    } catch (err) {
      el.exportResult.textContent = `Error: ${err.message}`;
    }
  });

  async function init() {
    state.classes = await api.getClasses();
    state.images = await api.getImages();
    boxCanvas.setClassNames(state.classes);
    renderClassList();
    renderProgress();
    renderImageList();
    if (state.images.length > 0) {
      state.currentIndex = -1;
      await goToIndex(0);
    }
  }

  init();
})();
