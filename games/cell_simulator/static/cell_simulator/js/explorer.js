(() => {
  const data = window.CELL_EXPLORATION_DATA || {};
  const scenes = {
    cell: document.getElementById("scene-cell"),
    mitochondrion: document.getElementById("scene-mitochondrion"),
    respiration: document.getElementById("scene-membrane"),
    detail: document.getElementById("scene-detail"),
  };
  const elements = {
    levelNav: document.getElementById("level-nav"),
    name: document.getElementById("target-name"),
    kind: document.getElementById("target-kind"),
    summary: document.getElementById("target-summary"),
    function: document.getElementById("target-function"),
    functionBlock: document.getElementById("target-function").closest(".detail-block"),
    components: document.getElementById("target-components"),
    moleculeSection: document.querySelector(".molecule-section"),
    moleculeList: document.getElementById("molecule-list"),
    moleculeCount: document.getElementById("molecule-count"),
    moleculeIntro: document.getElementById("molecule-intro"),
    zoomAction: document.getElementById("zoom-action"),
    stageInstruction: document.getElementById("stage-instruction"),
    sceneKicker: document.getElementById("scene-kicker"),
    sceneIndex: document.getElementById("scene-index"),
    detailContent: document.getElementById("dynamic-scene"),
  };
  const moleculeCards = new Map(
    [...elements.moleculeList.querySelectorAll("[data-molecule]")].map((card) => [
      card.dataset.molecule,
      {
        id: card.dataset.molecule,
        name: card.querySelector(".molecule-name").textContent,
        formula: card.querySelector(".molecule-formula").textContent,
        role: card.querySelector(".molecule-role").textContent,
        image: card.querySelector("img").getAttribute("src"),
      },
    ]),
  );
  const cellChildren = new Set(data.cell_overview.children || []);
  let path = ["cell_overview"];

  function escapeHtml(value) {
    return String(value).replace(/[&<>"']/g, (character) => ({
      "&": "&amp;", "<": "&lt;", ">": "&gt;", "\"": "&quot;", "'": "&#39;",
    })[character]);
  }

  function currentId() {
    return path[path.length - 1];
  }

  function moleculeActionSvg(moleculeId, index, total, y = 457) {
    const molecule = moleculeCards.get(moleculeId);
    if (!molecule) return "";
    const x = 90 + (720 / Math.max(total - 1, 1)) * index;
    const shortName = molecule.name.length > 19 ? `${molecule.name.slice(0, 17)}…` : molecule.name;
    return `<g class="diagram-action molecule-action" data-target="${escapeHtml(moleculeId)}" role="button" tabindex="0" aria-label="Zoom into ${escapeHtml(molecule.name)}">
      <rect class="molecule-thumb" x="${x - 62}" y="${y - 30}" width="124" height="60" rx="4"/>
      <image class="molecule-preview" href="${escapeHtml(molecule.image)}" x="${x - 58}" y="${y - 27}" width="116" height="54" preserveAspectRatio="xMidYMid meet"/>
      <text class="node-label" x="${x}" y="${y + 43}">${escapeHtml(shortName)}</text></g>`;
  }

  function childActionSvg(childId, index, total, y = 457) {
    const child = data[childId];
    if (!child) return "";
    const x = 90 + (720 / Math.max(total - 1, 1)) * index;
    const shortName = child.name.length > 20 ? `${child.name.slice(0, 18)}…` : child.name;
    return `<g class="diagram-action child-action" data-target="${escapeHtml(childId)}" role="button" tabindex="0" aria-label="Zoom into ${escapeHtml(child.name)}">
      <circle class="child-node" cx="${x}" cy="${y}" r="23"/><path class="node-glyph" d="M${x - 7} ${y}h14M${x} ${y - 7}v14"/>
      <text class="node-label" x="${x}" y="${y + 36}">${escapeHtml(shortName)}</text></g>`;
  }

  function membraneLipidsSvg(moleculeIds, showLeafletAsymmetry = false) {
    const knownLipids = moleculeIds.filter((id) => moleculeCards.has(id));
    if (!knownLipids.length) return "";

    const plasmaOuter = [
      "phosphatidylcholine", "sphingomyelin", "phosphatidylcholine", "cholesterol",
      "sphingomyelin", "phosphatidylcholine", "phosphatidylethanolamine", "sphingomyelin",
      "cholesterol", "phosphatidylcholine", "sphingomyelin", "phosphatidylcholine",
      "sphingomyelin", "cholesterol", "phosphatidylcholine", "sphingomyelin",
      "phosphatidylcholine", "sphingomyelin",
    ];
    const plasmaInner = [
      "phosphatidylethanolamine", "phosphatidylserine", "phosphatidylethanolamine", "phosphatidylinositol",
      "phosphatidylethanolamine", "cholesterol", "phosphatidylserine", "phosphatidylethanolamine",
      "pip2", "phosphatidylethanolamine", "phosphatidylinositol", "phosphatidylserine",
      "phosphatidylethanolamine", "cholesterol", "phosphatidylserine", "phosphatidylethanolamine",
      "pip2", "phosphatidylserine",
    ];
    const genericLeaflet = Array.from({ length: 18 }, (_, index) => knownLipids[index % knownLipids.length]);
    const outerLeaflet = showLeafletAsymmetry ? plasmaOuter : genericLeaflet;
    const innerLeaflet = showLeafletAsymmetry ? plasmaInner : genericLeaflet;
    const labels = {
      phosphatidylcholine: "PC",
      phosphatidylethanolamine: "PE",
      sphingomyelin: "SM",
      phosphatidylserine: "PS",
      phosphatidylinositol: "PI",
      pip2: "PIP₂",
      cardiolipin: "CL",
    };

    function drawLeaflet(composition, leaflet) {
      const outer = leaflet === "outer";
      return composition.map((moleculeId, index) => {
        if (!moleculeCards.has(moleculeId)) return "";
        const molecule = moleculeCards.get(moleculeId);
        const x = 64 + index * 45;
        const headY = outer ? 250 : 377;
        const isCholesterol = moleculeId === "cholesterol";
        const isCardiolipin = moleculeId === "cardiolipin";
        const direction = outer ? 1 : -1;
        const label = labels[moleculeId];
        const tails = isCardiolipin
          ? `<circle class="bilayer-head" cx="${x - 4}" cy="${headY}" r="7"/><circle class="bilayer-head" cx="${x + 5}" cy="${headY}" r="7"/><path class="bilayer-tail" d="M${x - 7} ${headY + direction * 7}l-6 ${direction * 22} 5 ${direction * 17}-7 ${direction * 23}m8-61 4 22-5 17 5 22m5-62 6 22-5 17 7 23m-5-61-4 22 5 17-5 22"/>`
          : isCholesterol
            ? `<circle class="sterol-hydroxyl" cx="${x}" cy="${headY}" r="4"/><path class="sterol-ring" d="M${x - 7} ${headY + direction * 12}l8-7 9 5 1 11-8 7-9-5Zm9 16 9-5 9 6-1 11-9 4-8-6Zm-8 0-9 5 1 11 9 4 8-6Z"/>`
            : `<circle class="bilayer-head ${outer ? "" : "lower"}" cx="${x}" cy="${headY}" r="10"/><path class="bilayer-tail" d="M${x - 3} ${headY + direction * 10}l-4 ${direction * 24} 5 ${direction * 15}-5 ${direction * 25}M${x + 3} ${headY + direction * 10}l5 ${direction * 23}-4 ${direction * 16} 5 ${direction * 25}"/>`;
        return `<g class="bilayer-lipid" data-target="${escapeHtml(moleculeId)}" role="button" tabindex="0" aria-label="Select ${escapeHtml(molecule.name)} in the ${leaflet} leaflet">
          <rect class="lipid-hit-area" x="${x - 21}" y="${outer ? 234 : 270}" width="42" height="130"/>
          ${tails}
          ${label ? `<text class="lipid-type" x="${x}" y="${headY + 3}">${label}</text>` : ""}
        </g>`;
      }).join("");
    }

    const outerLipids = drawLeaflet(outerLeaflet, "outer");
    const innerLipids = drawLeaflet(innerLeaflet, "inner");
    const outerLabel = showLeafletAsymmetry ? "EXTRACELLULAR LEAFLET" : "WATER-FACING SURFACE";
    const innerLabel = showLeafletAsymmetry ? "CYTOSOLIC LEAFLET" : "WATER-FACING SURFACE";
    return `<g class="bilayer-visual"><rect class="bilayer-water" x="36" y="225" width="828" height="175" rx="22"/>
      <path class="bilayer-center" d="M49 313h802"/>${outerLipids}${innerLipids}
      <text class="diagram-small-label" x="55" y="211">${outerLabel}</text>
      <text class="diagram-small-label" x="55" y="425">${innerLabel}</text>
      ${showLeafletAsymmetry ? "" : `<text class="diagram-note" x="450" y="313">HYDROPHOBIC CORE</text>`}</g>`;
  }

  function plasmaMembraneFeaturesSvg() {
    const glycocalyx = `<g class="hit-target glycocalyx-feature" data-target="glycocalyx" role="button" tabindex="0" aria-label="Explore the extracellular glycocalyx">
      <rect class="glycocalyx-hit-area" x="145" y="116" width="490" height="124"/>
      <text class="membrane-feature-label glycocalyx-label" x="450" y="111">GLYCOCALYX · EXTRACELLULAR SUGAR CHAINS</text>
      <path class="glycocalyx-branch" d="M195 238v-30l-18-18m18 18 18-18m100 48v-40l-18-18m18 18 18-18m102 48v-36l-18-18m18 18 18-18m101 54v-42l-18-18m18 18 18-18m105 48v-34l-18-18m18 18 18-18"/>
      <path class="glycocalyx-branch secondary" d="M195 208v-20l-13-13m13 13 14-13m100 13v-21l-13-13m13 13 14-13m102 13v-18l-13-13m13 13 14-13m101 18v-21l-13-13m13 13 14-13m105 13v-18l-13-13m13 13 14-13"/>
      <circle class="glycocalyx-sugar sugar-one" cx="177" cy="190" r="6"/><circle class="glycocalyx-sugar sugar-two" cx="213" cy="190" r="6"/>
      <circle class="glycocalyx-sugar sugar-one" cx="277" cy="168" r="6"/><circle class="glycocalyx-sugar sugar-two" cx="313" cy="168" r="6"/>
      <circle class="glycocalyx-sugar sugar-one" cx="379" cy="172" r="6"/><circle class="glycocalyx-sugar sugar-two" cx="415" cy="172" r="6"/>
      <circle class="glycocalyx-sugar sugar-one" cx="480" cy="168" r="6"/><circle class="glycocalyx-sugar sugar-two" cx="516" cy="168" r="6"/>
      <circle class="glycocalyx-sugar sugar-one" cx="585" cy="176" r="6"/><circle class="glycocalyx-sugar sugar-two" cx="621" cy="176" r="6"/>
    </g>`;
    const proteins = [
      `<g class="hit-target membrane-protein-feature aquaporin-feature" data-target="aquaporin_1" role="button" tabindex="0" aria-label="Explore aquaporin-1 water channel">
        <rect class="protein-body aquaporin-body" x="239" y="228" width="46" height="164" rx="19"/><rect class="protein-pore" x="255" y="238" width="14" height="145" rx="7"/><path class="protein-gate" d="M255 308h14"/>
        <text class="membrane-feature-label protein-label" x="262" y="451">AQP1</text>
      </g>`,
      `<g class="hit-target membrane-protein-feature nachr-feature" data-target="nicotinic_acetylcholine_receptor" role="button" tabindex="0" aria-label="Explore nicotinic acetylcholine receptor ion channel">
        <circle class="protein-body nachr-body" cx="463" cy="310" r="58"/><circle class="protein-subunit" cx="463" cy="260" r="21"/><circle class="protein-subunit" cx="510" cy="294" r="21"/><circle class="protein-subunit" cx="492" cy="349" r="21"/><circle class="protein-subunit" cx="434" cy="349" r="21"/><circle class="protein-subunit" cx="416" cy="294" r="21"/><circle class="protein-pore nachr-pore" cx="463" cy="310" r="18"/>
        <text class="membrane-feature-label protein-label" x="463" y="451">nAChR</text>
      </g>`,
      `<g class="hit-target membrane-protein-feature glut1-feature" data-target="glut1" role="button" tabindex="0" aria-label="Explore GLUT1 glucose transporter">
        <path class="protein-body glut1-body" d="M637 242c0-13 12-20 25-15l22 9 22-9c13-5 25 2 25 15v133c0 13-12 20-25 15l-22-9-22 9c-13 5-25-2-25-15Z"/>
        <path class="protein-pore glut1-cleft" d="M677 251c-13 23-13 88 0 116m12-116c13 23 13 88 0 116"/>
        <text class="membrane-feature-label protein-label" x="678" y="451">GLUT1</text>
      </g>`,
    ].join("");
    return `${glycocalyx}${proteins}`;
  }

  function cytosolSceneSvg(target, targetId) {
    const moleculeIds = (target.molecules || []).filter((id) => moleculeCards.has(id));
    const nameOverrides = {
      water: "H₂O",
      glucose: "Glucose",
      pyruvate: "Pyruvate",
      adp: "ADP",
      atp: "ATP",
      phosphate: "Pi",
      sodium: "Na⁺",
      potassium: "K⁺",
      magnesium: "Mg²⁺",
      chloride: "Cl⁻",
    };
    function moleculeNode(id, label, x, y, width = 80, height = 46) {
      const molecule = moleculeCards.get(id);
      if (!molecule) return "";
      return `<g class="cytosol-molecule flow-molecule" data-target="${escapeHtml(id)}" role="button" tabindex="0" aria-label="Inspect ${escapeHtml(molecule.name)}">
        <rect class="flow-molecule-bg" x="${x - width / 2 - 5}" y="${y - height / 2 - 5}" width="${width + 10}" height="${height + 10}" rx="5"/>
        <image class="cytosol-structure" href="${escapeHtml(molecule.image)}" x="${x - width / 2}" y="${y - height / 2}" width="${width}" height="${height}" preserveAspectRatio="xMidYMid meet"/>
        <text class="flow-molecule-label" x="${x}" y="${y + height / 2 + 15}">${escapeHtml(label || nameOverrides[id] || molecule.name)}</text>
      </g>`;
    }

    if (targetId !== "cytoplasm") {
      const nodes = moleculeIds.map((id, index) => moleculeNode(id, nameOverrides[id], 180 + index * (540 / Math.max(moleculeIds.length - 1, 1)), 295, 96, 58)).join("");
      return `<g class="cytosol-scene"><path class="cytosol-fluid" d="M93 224c36-90 167-121 283-84 99-48 244-28 324 39 81 68 61 170-17 221-83 55-221 34-318 50-107 17-228-15-272-87-28-45-25-98 0-139Z"/><text class="cytosol-scene-label" x="450" y="142">DISSOLVED IN CYTOSOL</text>${nodes}<text class="cytosol-note lower" x="450" y="440">CONCENTRATIONS VARY THROUGH THE CELL</text></g>`;
    }

    const steps = [
      {
        substrate: [{ id: "glucose", label: "Glucose" }],
        product: [{ id: "glucose_6_phosphate", label: "Glucose-6-P" }],
        enzyme: ["Hexokinase"],
        carriers: [["atp", "ATP"], ["→", "arrow"], ["adp", "ADP"]],
      },
      {
        substrate: [{ id: "glucose_6_phosphate", label: "Glucose-6-P" }],
        product: [{ id: "fructose_6_phosphate", label: "Fructose-6-P" }],
        enzyme: ["Phosphoglucose", "isomerase"],
      },
      {
        substrate: [{ id: "fructose_6_phosphate", label: "Fructose-6-P" }],
        product: [{ id: "fructose_1_6_bisphosphate", label: "Fructose-1,6-BP" }],
        enzyme: ["Phosphofructokinase-1"],
        carriers: [["atp", "ATP"], ["→", "arrow"], ["adp", "ADP"]],
      },
      {
        substrate: [{ id: "fructose_1_6_bisphosphate", label: "Fructose-1,6-BP" }],
        product: [
          { id: "dihydroxyacetone_phosphate", label: "DHAP" },
          { id: "glyceraldehyde_3_phosphate", label: "G3P" },
        ],
        enzyme: ["Aldolase"],
      },
      {
        substrate: [{ id: "dihydroxyacetone_phosphate", label: "DHAP" }],
        product: [{ id: "glyceraldehyde_3_phosphate", label: "2nd G3P" }],
        enzyme: ["Triose phosphate", "isomerase"],
      },
      {
        substrate: [{ id: "glyceraldehyde_3_phosphate", label: "2 × G3P" }],
        product: [{ id: "1_3_bisphosphoglycerate", label: "2 × 1,3-BPG" }],
        enzyme: ["Glyceraldehyde-3-P", "dehydrogenase"],
        carriers: [
          ["nad_plus", "2 NAD⁺"], ["+", "operator"], ["phosphate", "2 Pi"],
          ["→", "arrow"], ["nadh", "2 NADH"], ["+", "operator"], ["2 H⁺", "text"],
        ],
      },
      {
        substrate: [{ id: "1_3_bisphosphoglycerate", label: "2 × 1,3-BPG" }],
        product: [{ id: "3_phosphoglycerate", label: "2 × 3-PG" }],
        enzyme: ["Phosphoglycerate", "kinase"],
        carriers: [["adp", "2 ADP"], ["→", "arrow"], ["atp", "2 ATP"]],
      },
      {
        substrate: [{ id: "3_phosphoglycerate", label: "2 × 3-PG" }],
        product: [{ id: "2_phosphoglycerate", label: "2 × 2-PG" }],
        enzyme: ["Phosphoglycerate", "mutase"],
      },
      {
        substrate: [{ id: "2_phosphoglycerate", label: "2 × 2-PG" }],
        product: [
          { id: "phosphoenolpyruvate", label: "2 × PEP" },
          { id: "water", label: "2 × H₂O" },
        ],
        enzyme: ["Enolase"],
      },
      {
        substrate: [{ id: "phosphoenolpyruvate", label: "2 × PEP" }],
        product: [{ id: "pyruvate", label: "2 × Pyruvate" }],
        enzyme: ["Pyruvate kinase"],
        carriers: [["adp", "2 ADP"], ["→", "arrow"], ["atp", "2 ATP"]],
      },
    ];

    function carrierEquation(carriers, centerX, y) {
      if (!carriers) return "";
      const widths = carriers.map(([id, label]) => {
        if (label === "operator" || label === "arrow") return 9;
        return Math.max(17, (label === "text" ? id : label).length * 3.7);
      });
      const totalWidth = widths.reduce((sum, width) => sum + width, 0);
      let x = centerX - totalWidth / 2;
      return carriers.map(([id, label], index) => {
        const width = widths[index];
        const itemX = x + width / 2;
        x += width;
        if (label === "operator" || label === "arrow" || label === "text") {
          const mark = label === "operator" ? "+" : label === "arrow" ? "→" : id;
          return `<text class="carrier-equation-mark" x="${itemX}" y="${y + 3}">${escapeHtml(mark)}</text>`;
        }
        const molecule = moleculeCards.get(id);
        const accessibleName = molecule ? molecule.name : label;
        return `<g class="carrier-equation-token" data-target="${escapeHtml(id)}" role="button" tabindex="0" aria-label="Inspect ${escapeHtml(accessibleName)}">
          <text x="${itemX}" y="${y + 3}">${escapeHtml(label)}</text>
        </g>`;
      }).join("");
    }

    function reactionCard(step, index) {
      const row = index < 5 ? 0 : 1;
      const column = row === 0 ? index : 9 - index;
      const centerX = 124 + column * 162;
      const top = row === 0 ? 160 : 368;
      const moleculeNodes = (molecules, y) => molecules.map((molecule, moleculeIndex) => {
        const paired = molecules.length > 1;
        const x = centerX + (moleculeIndex - (molecules.length - 1) / 2) * (paired ? 66 : 0);
        return moleculeNode(
          molecule.id,
          molecule.label,
          x,
          y,
          paired ? 54 : 104,
          paired ? 30 : 40,
        );
      }).join("");
      const textLines = (lines, y, className) => lines.map((line, lineIndex) =>
        `<text class="${className}" x="${centerX}" y="${y + lineIndex * 10}">${escapeHtml(line)}</text>`
      ).join("");
      return `<g class="glycolysis-step">
        <rect class="reaction-step-bg" x="${centerX - 69}" y="${top}" width="138" height="204" rx="9"/>
        <circle class="reaction-step-badge" cx="${centerX - 55}" cy="${top + 17}" r="8"/>
        <text class="reaction-step-number" x="${centerX - 55}" y="${top + 17}">${index + 1}</text>
        <text class="reaction-step-heading" x="${centerX + 8}" y="${top + 20}">STEP ${index + 1}</text>
        ${moleculeNodes(step.substrate, top + 53)}
        <text class="reaction-step-direction" x="${centerX}" y="${top + 105}">↓</text>
        ${moleculeNodes(step.product, top + 119)}
        ${textLines(step.enzyme, top + 170, "reaction-step-enzyme-full")}
        ${carrierEquation(step.carriers, centerX, top + 191)}
      </g>`;
    }

    const cards = steps.map(reactionCard).join("");
    const connectors = Array.from({ length: 4 }, (_, index) => {
      const rightX = 124 + index * 162 + 70;
      const leftX = 124 + (4 - index) * 162 - 70;
      const topY = 262;
      const bottomY = 470;
      return `<path class="glycolysis-connector forward" d="M${rightX} ${topY}h17m-5-4 5 4-5 4"/>
        <path class="glycolysis-connector reverse" d="M${leftX} ${bottomY}h-17m5-4-5 4 5 4"/>`;
    }).join("");

    return `<g class="cytosol-scene glycolysis-scene">
      <path class="cytosol-fluid" d="M45 171c86-74 212-54 322-54 111 0 242-26 320 46 56 51 44 253-12 302-86 69-221 54-336 48-131-7-250 18-306-58-39-53-35-232 12-284Z"/>
      <text class="cytosol-scene-label" x="450" y="135">GLYCOLYSIS · CYTOSOL</text>
      <text class="cytosol-note" x="450" y="155">ONE GLUCOSE · TEN ENZYME-CATALYZED REACTIONS · FOLLOW THE NUMBERED PATH</text>
      ${connectors}
      <path class="glycolysis-connector turn" d="M846 349v16m-4-5 4 5 4-5"/>
      ${cards}
      <text class="net-yield" x="450" y="582">NET PER GLUCOSE · 2 PYRUVATE · 2 ATP · 2 NADH · 2 H₂O</text>
      <text class="cytosol-note lower" x="450" y="603">SELECT ANY MOLECULE TO ZOOM INTO ITS STRUCTURE · ATP SPENT IN STEPS 1 &amp; 3, MADE IN STEPS 7 &amp; 10</text>
    </g>`;
  }

  function focusGraphic(visual, target, targetId) {
    switch (visual) {
      case "membrane":
        return `${membraneLipidsSvg(target.molecules || [], targetId === "plasma_membrane")}${targetId === "plasma_membrane" ? plasmaMembraneFeaturesSvg() : ""}`;
      case "cytosol":
        return cytosolSceneSvg(target, targetId);
      case "double_membrane":
        return `<g class="double-membrane-visual"><ellipse class="membrane-outer" cx="450" cy="282" rx="238" ry="126"/><ellipse class="membrane-inner" cx="450" cy="282" rx="215" ry="105"/><path class="double-membrane-dna" d="M375 277c20-41 40 42 61 0s40-42 60 0 40 42 60 0"/><text class="diagram-note" x="450" y="440">TWO SEPARATE LIPID BILAYERS</text></g>`;
      case "mitochondrion":
        return `<g class="mitochondrion-visual"><path class="mito-shell" d="M201 281c30-115 183-156 307-98 96-36 208 26 205 105 22 91-80 150-185 119-120 40-307 8-327-67-16-20-14-39 0-59Z"/><path class="mito-folds" d="M230 276c32-47 51 59 88 9s56-50 90 0 57 55 94 1 59-33 87 12m-346 29c35-38 54 55 91 13s57-48 91-1 58 47 91 2 56-33 81 4"/><text class="diagram-note" x="450" y="456">COMPARTMENTS · CRISTAE · ENERGY-CONVERSION MACHINERY</text></g>`;
      case "aquaporin_tetramer": {
        const protomers = [
          { name: "AQP1-A", x: 353, y: 245 },
          { name: "AQP1-B", x: 547, y: 245 },
          { name: "AQP1-C", x: 353, y: 375 },
          { name: "AQP1-D", x: 547, y: 375 },
        ].map((subunit) => `<g class="aqp-protomer"><rect x="${subunit.x - 76}" y="${subunit.y - 48}" width="152" height="96" rx="34"/><circle class="aqp-pore" cx="${subunit.x}" cy="${subunit.y}" r="21"/><circle class="aqp-water" cx="${subunit.x}" cy="${subunit.y}" r="8"/><text class="subunit-label" x="${subunit.x}" y="${subunit.y + 68}">${subunit.name}</text></g>`).join("");
        return `<g class="aqp-tetramer"><text class="protein-view-label" x="450" y="121">TOP VIEW · EXTRACELLULAR SIDE</text>${protomers}<text class="diagram-note" x="450" y="493">HOMOTETRAMER · FOUR PROTOMERS · FOUR INDEPENDENT WATER PORES</text></g>`;
      }
      case "nachr_pentamer": {
        const subunits = [
          { name: "α1", type: "alpha", x: 450, y: 247 },
          { name: "ε", type: "epsilon", x: 545, y: 313 },
          { name: "α1", type: "alpha", x: 509, y: 424 },
          { name: "δ", type: "delta", x: 391, y: 424 },
          { name: "β1", type: "beta", x: 355, y: 313 },
        ].map((subunit) => `<g class="nachr-subunit ${subunit.type}"><circle cx="${subunit.x}" cy="${subunit.y}" r="49"/><text class="subunit-label" x="${subunit.x}" y="${subunit.y + 5}">${subunit.name}</text></g>`).join("");
        const acetylcholineSites = [
          { x: 539, y: 232, label: "α1–ε SITE" },
          { x: 450, y: 490, label: "α1–δ SITE" },
        ].map((site) => `<g class="nachr-ligand diagram-action" data-target="acetylcholine" role="button" tabindex="0" aria-label="Inspect acetylcholine at the ${site.label}"><rect x="${site.x - 50}" y="${site.y - 16}" width="100" height="32" rx="16"/><text class="ligand-label" x="${site.x}" y="${site.y + 4}">ACh</text><text class="binding-site-label" x="${site.x}" y="${site.y + 29}">${site.label}</text></g>`).join("");
        return `<g class="nachr-pentamer-visual"><text class="protein-view-label" x="450" y="121">EXTRACELLULAR VIEW · ADULT SKELETAL-MUSCLE RECEPTOR</text>${subunits}<circle class="nachr-channel" cx="450" cy="341" r="29"/><circle class="nachr-channel-core" cx="450" cy="341" r="13"/><text class="channel-label" x="450" y="348">CATION</text>${acetylcholineSites}<text class="diagram-note" x="450" y="548">HETEROPENTAMER · (α1)₂β1δε · SUBUNITS SHOWN, NOT DRILL-DOWN TARGETS</text></g>`;
      }
      case "glut1_transporter": {
        const helices = Array.from({ length: 12 }, (_, index) => {
          const angle = (-90 + index * 30) * Math.PI / 180;
          const centerX = 450 + Math.cos(angle) * 126;
          const centerY = 327 + Math.sin(angle) * 126;
          const labelX = 450 + Math.cos(angle) * 174;
          const labelY = 327 + Math.sin(angle) * 174 + 4;
          const domain = index < 6 ? "n-domain" : "c-domain";
          return `<g class="glut1-helix ${domain}"><circle cx="${centerX}" cy="${centerY}" r="22"/><text class="helix-label" x="${labelX}" y="${labelY}">TM${index + 1}</text></g>`;
        }).join("");
        return `<g class="glut1-transporter-visual"><text class="protein-view-label" x="450" y="121">TOP VIEW · TWELVE TRANSMEMBRANE HELICES</text><ellipse class="glut1-cavity" cx="450" cy="327" rx="67" ry="88"/><text class="cavity-label" x="450" y="322">SUBSTRATE</text><text class="cavity-label" x="450" y="340">CAVITY</text>${helices}<text class="domain-label n-domain-label" x="283" y="535">N-TERMINAL BUNDLE · TM1–TM6</text><text class="domain-label c-domain-label" x="617" y="535">C-TERMINAL BUNDLE · TM7–TM12</text><text class="diagram-note" x="450" y="572">ONE POLYPEPTIDE · FACILITATED DIFFUSION, NOT A PUMP</text></g>`;
      }
      case "nucleus":
      case "chromatin":
      case "nucleic_acid":
        return `<g class="nucleus-visual"><ellipse class="nucleus-shell" cx="450" cy="278" rx="205" ry="123"/><path class="helix-line" d="M342 235c35-57 67 68 102 0s67-57 102 0 68 67 103 0m-307 78c35 57 67-68 102 0s67 57 102 0 68-67 103 0"/><path class="helix-rungs" d="M354 231l-12 80m43-39l-10 4m42-47l-9 70m42-24l-10-22m42-41l-9 80m43-39l-10 2m42-43l-8 68"/><text class="diagram-note" x="450" y="437">DNA · RNA · DNA-ASSOCIATED PROTEINS</text></g>`;
      case "ribosome":
        return `<g class="ribosome-visual"><path class="ribosome-large" d="M330 298c-34-41 0-116 89-135 85-18 177 16 192 90 16 69-47 99-119 88-60 25-125 14-162-43Z"/><path class="ribosome-small" d="M361 325c-9-42 33-70 94-64 57 5 99 34 91 71-8 36-73 54-126 37-35-11-54-22-59-44Z"/><path class="rna-thread" d="M362 274c26 28 43-27 69 0s46 25 65-1 43-25 62 1m-169 48c25 26 42-23 67 0s45 21 62-2 42-21 61 2"/><text class="diagram-note" x="450" y="440">RIBOSOMAL RNA + PROTEINS</text></g>`;
      case "network":
        return `<g class="network-visual"><path d="M245 250c78-84 102 58 175-5s95-52 138 4 75 72 144-3M245 288c77-77 111 48 181-7s94-45 134 10 75 53 142-7M264 328c70-48 93 44 157-5s103-32 143 10 73 35 120-6"/><circle cx="292" cy="220" r="8"/><circle cx="646" cy="329" r="9"/><text class="diagram-note" x="450" y="440">CONNECTED MEMBRANE NETWORK</text></g>`;
      case "stack":
        return `<g class="stack-visual"><path d="M283 226c86-34 251-34 336 0-85 34-250 34-336 0Zm-19 43c95-34 276-34 371 0-95 34-276 34-371 0Zm-11 43c102-35 291-35 393 0-102 35-291 35-393 0Zm16 43c91-33 260-33 351 0-91 33-260 33-351 0Z"/><text class="diagram-note" x="450" y="440">STACKED, MEMBRANE-BOUND COMPARTMENTS</text></g>`;
      case "vesicle":
      case "compartment":
        return `<g class="vesicle-visual"><circle class="vesicle-shell" cx="450" cy="282" r="132"/><circle class="vesicle-core" cx="450" cy="282" r="114"/><circle class="cargo-dot" cx="407" cy="255" r="15"/><circle class="cargo-dot" cx="474" cy="231" r="10"/><circle class="cargo-dot" cx="493" cy="303" r="18"/><circle class="cargo-dot" cx="427" cy="333" r="8"/><circle class="cargo-dot" cx="474" cy="357" r="11"/><text class="diagram-note" x="450" y="447">ENCLOSED SPACE · SELECT A COMPONENT</text></g>`;
      case "filament_network":
      case "filament":
        return `<g class="filament-visual"><path d="M220 339 333 217l104 113 120-139 123 105M256 202l97 161 91-178 98 188 120-143M226 284l455 0m-303-83v174m171-155v148"/><circle cx="333" cy="217" r="7"/><circle cx="437" cy="330" r="7"/><circle cx="557" cy="191" r="7"/><text class="diagram-note" x="450" y="440">FILAMENTS BUILT FROM PROTEIN SUBUNITS</text></g>`;
      case "centrosome":
        return `<g class="centrosome-visual"><path class="centrosome-spokes" d="M450 284 450 142m0 142 120-80m-120 80 143 24m-143-24 108 99m-108-99-13 143m13-143-108 97m108-97-142 15m142-15-90-111"/><rect x="427" y="267" width="50" height="14" rx="7" transform="rotate(-30 452 274)"/><rect x="429" y="287" width="50" height="14" rx="7" transform="rotate(55 454 294)"/><text class="diagram-note" x="450" y="447">MICROTUBULE-ORGANIZING CENTER</text></g>`;
      case "respiration":
      case "pathway":
      case "gradient": {
        const steps = target.children || [];
        const stepMarkup = steps.map((id, index) => {
          const child = data[id];
          const x = 105 + index * (690 / Math.max(steps.length - 1, 1));
          return `<g class="pathway-step diagram-action" data-target="${escapeHtml(id)}" role="button" tabindex="0" aria-label="Open ${escapeHtml(child.name)}"><circle cx="${x}" cy="282" r="31"/><text x="${x}" y="287">${index + 1}</text><text class="pathway-label" x="${x}" y="338">${escapeHtml(child.name)}</text></g>${index < steps.length - 1 ? `<path class="pathway-arrow" d="M${x + 36} 282h${690 / Math.max(steps.length - 1, 1) - 72}"/>` : ""}`;
        }).join("");
        return `<g class="pathway-visual">${stepMarkup}<text class="diagram-note" x="450" y="425">SELECT A STEP TO EXPLORE ITS MOLECULAR ROLE</text></g>`;
      }
      case "carbohydrate_layer":
        return `<g class="carbohydrate-visual"><path d="M198 326h505M245 326v-50l-22-18m22 18 22-18m71 68v-53l-22-18m22 18 22-18m71 71v-58l-22-18m22 18 22-18m71 76v-52l-22-18m22 18 22-18m71 52v-47l-22-18m22 18 22-18"/><text class="diagram-note" x="450" y="425">SUGARS PROJECT FROM THE CELL SURFACE</text></g>`;
      default:
        return `<g class="protein-visual"><path d="M323 290c-54-35-19-111 42-93 23-75 108-73 127-16 68-18 109 47 68 88 35 60-17 111-74 87-38 57-114 38-124-15-45 12-79-8-39-51Z"/><circle cx="395" cy="268" r="16"/><circle cx="470" cy="231" r="13"/><circle cx="520" cy="294" r="18"/><circle cx="422" cy="326" r="11"/></g>`;
    }
  }

  function contextualMembrane(target, selectedMoleculeId) {
    const ids = [...new Set([...(target.molecules || []), selectedMoleculeId])];
    if (!ids.some((id) => moleculeCards.has(id))) return "";
    return `<g class="context-strip"><rect x="142" y="365" width="616" height="47" rx="23"/><path d="M170 388h560"/>${ids.slice(0, 7).map((id, index) => {
      const x = 207 + index * 77;
      const selected = id === selectedMoleculeId;
      const marker = id === "cholesterol"
        ? `<path class="context-sterol" d="M${x - 8} 383l7-5 8 4 1 9-7 5-8-4Zm8 12 8-4 7 5-1 9-8 3-7-5Z"/>`
        : id === "coq"
          ? `<circle class="context-quinone" cx="${x}" cy="388" r="8"/><path class="context-tail" d="M${x + 7} 388h19"/>`
          : id === "cardiolipin"
            ? `<circle cx="${x - 3}" cy="388" r="7"/><circle cx="${x + 4}" cy="388" r="7"/><path d="M${x - 7} 395l-4 9m9-9 3 9m5-9 4 9m-1-9-3 9"/>`
            : `<circle cx="${x}" cy="388" r="9"/><path d="M${x - 3} 397l-5 9m11-9 5 9"/>`;
      return `<g class="context-lipid ${selected ? "is-selected" : ""}">${marker}</g>`;
    }).join("")}<text class="context-caption" x="450" y="438">THIS MOLECULE IS PART OF ${escapeHtml(target.name.toUpperCase())}</text></g>`;
  }

  function moleculeScene(moleculeId) {
    const molecule = moleculeCards.get(moleculeId);
    const membraneId = path.slice(0, -1).reverse().find((id) => data[id].visual === "membrane");
    const context = membraneId ? contextualMembrane(data[membraneId], molecule.id) : "";
    return `<svg class="detail-svg molecule-svg" viewBox="0 0 900 560" role="group" aria-label="Molecular structure of ${escapeHtml(molecule.name)}">
      <text class="detail-title" x="56" y="55">${escapeHtml(molecule.name)}</text>
      <text class="detail-subtitle" x="58" y="80">${escapeHtml(molecule.formula)}</text>
      <rect class="molecule-viewer" x="115" y="105" width="670" height="264" rx="8"/>
      <image href="${escapeHtml(molecule.image)}" x="132" y="113" width="636" height="247" preserveAspectRatio="xMidYMid meet"/>
      <text class="diagram-note" x="450" y="395">2D STRUCTURE GENERATED FROM ITS SMILES WITH RDKIT</text>
      ${context}</svg>`;
  }

  function genericScene(targetId) {
    const target = data[targetId];
    const childIds = target.children || [];
    const moleculeIds = (target.molecules || []).filter((id) => moleculeCards.has(id));
    if (target.visual === "molecule" && moleculeCards.has(targetId)) return moleculeScene(targetId);
    if (target.visual === "molecule" && moleculeIds.length) return moleculeScene(moleculeIds[0]);

    const childRowY = target.visual === "membrane" ? 505 : 457;
    const embeddedPlasmaFeatures = targetId === "plasma_membrane";
    const embeddedCytosolFeatures = target.visual === "cytosol";
    const childMarkup = embeddedPlasmaFeatures || embeddedCytosolFeatures
      ? ""
      : childIds.map((id, index) => childActionSvg(id, index, childIds.length, childRowY)).join("");
    const moleculeRowY = childIds.length ? 560 : 457;
    const moleculeMarkup = target.visual !== "membrane" && target.visual !== "nachr_pentamer" && !embeddedCytosolFeatures
      ? moleculeIds.map((id, index) => moleculeActionSvg(id, index, moleculeIds.length, moleculeRowY)).join("")
      : "";
    const showChildren = childIds.length > 0;
    const showMolecules = moleculeIds.length > 0;
    const pathwayView = ["respiration", "pathway", "gradient"].includes(target.visual);
    const customProteinView = ["aquaporin_tetramer", "nachr_pentamer", "glut1_transporter"].includes(target.visual);
    const secondaryMarkup = showChildren && showMolecules && !pathwayView && target.visual !== "membrane" && !embeddedCytosolFeatures
      ? `<g class="secondary-label"><text x="450" y="519">MOLECULES IN THIS STRUCTURE</text></g>${moleculeMarkup}`
      : moleculeMarkup;
    return `<svg class="detail-svg" viewBox="0 0 900 620" role="group" aria-label="${escapeHtml(target.name)} composition">
      <text class="detail-title" x="56" y="55">${escapeHtml(target.name)}</text>
      <text class="detail-subtitle" x="58" y="80">${escapeHtml(target.kind)}</text>
      <g class="focus-art">${focusGraphic(target.visual || "protein_complex", target, targetId)}</g>
      ${target.visual === "membrane" && !embeddedPlasmaFeatures ? `<g class="secondary-label"><text x="450" y="449">SELECT A LIPID TO VIEW ITS MOLECULAR STRUCTURE</text></g>` : ""}
      ${embeddedPlasmaFeatures ? `<g class="secondary-label"><text x="450" y="482">SELECT A NAMED LIPID OR EMBEDDED FEATURE TO ZOOM IN</text></g>` : ""}
      ${showChildren && !pathwayView && !embeddedPlasmaFeatures && !embeddedCytosolFeatures ? `<g class="component-actions"><text class="component-caption" x="450" y="${target.visual === "membrane" ? 477 : 420}">${showMolecules && target.visual !== "membrane" ? "SELECT A COMPONENT · MOLECULES BELOW" : "SELECT A COMPONENT TO ZOOM IN"}</text>${childMarkup}</g>` : ""}
      ${secondaryMarkup}
      ${!showChildren && !showMolecules && !customProteinView ? `<text class="diagram-note" x="450" y="505">DEEPEST CURRENT VIEW · USE THE TRAIL ABOVE TO ZOOM OUT</text>` : ""}
    </svg>`;
  }

  function renderInspector(targetId) {
    const target = data[targetId] || data.cell_overview;
    elements.name.textContent = target.name;
    elements.kind.textContent = target.kind;
    elements.summary.textContent = target.summary;
    elements.function.textContent = target.function;
    elements.functionBlock.hidden = target.function === target.summary;
    elements.components.textContent = target.components;
    elements.moleculeSection.hidden = target.visual === "cytosol";

    const moleculeIds = target.molecules || [];
    const cards = [...elements.moleculeList.querySelectorAll("[data-molecule]")];
    let visibleCount = 0;
    for (const card of cards) {
      const visible = moleculeIds.includes(card.dataset.molecule);
      card.hidden = !visible;
      card.classList.toggle("is-selected", card.dataset.molecule === targetId);
      visibleCount += Number(visible);
    }
    elements.moleculeCount.textContent = String(visibleCount).padStart(2, "0");
    elements.moleculeIntro.textContent = visibleCount
      ? "Select a molecule to zoom into its structure in the scene."
      : "Molecular views appear as you explore a structure's composition.";
    elements.zoomAction.hidden = true;
  }

  function renderBreadcrumbs() {
    elements.levelNav.innerHTML = path.map((id, index) => {
      const target = data[id];
      const current = index === path.length - 1;
      return `${index ? '<span class="level-arrow" aria-hidden="true">/</span>' : ""}<button class="level-step ${current ? "is-current" : ""}" type="button" data-breadcrumb="${index}" ${current ? 'aria-current="step"' : ""}><span class="step-number">${index === 0 ? "01" : String(index + 1).padStart(2, "0")}</span><span class="step-name">${escapeHtml(target.name)}</span></button>`;
    }).join("");
  }

  function render() {
    const targetId = currentId();
    const target = data[targetId] || data.cell_overview;
    let activeScene = "detail";
    if (targetId === "cell_overview") activeScene = "cell";
    else if (targetId === "mitochondrion") activeScene = "mitochondrion";
    else if (targetId === "respiratory_chain") activeScene = "respiration";

    for (const [name, scene] of Object.entries(scenes)) {
      scene.hidden = name !== activeScene;
      scene.classList.toggle("is-visible", name === activeScene);
    }
    scenes.detail.classList.toggle("molecule-detail", target.visual === "molecule");
    if (activeScene === "detail") elements.detailContent.innerHTML = genericScene(targetId);
    elements.sceneKicker.textContent = target.kind;
    elements.sceneIndex.textContent = `LEVEL ${String(path.length).padStart(2, "0")}`;
    elements.stageInstruction.textContent = target.children?.length
      ? "Select a visible component to continue zooming in."
      : "Select a molecule or use the trail to zoom back out.";
    renderBreadcrumbs();
    renderInspector(targetId);
  }

  function openTarget(targetId) {
    if (!data[targetId]) return;
    const ancestorIndex = path.indexOf(targetId);
    if (ancestorIndex >= 0) {
      path = path.slice(0, ancestorIndex + 1);
      render();
      return;
    }
    const parent = data[currentId()];
    if (currentId() === "cell_overview" && cellChildren.has(targetId)) {
      path = ["cell_overview", targetId];
    } else if ((parent.children || []).includes(targetId) || (parent.molecules || []).includes(targetId)) {
      path = [...path, targetId];
    } else {
      let ancestorWithTarget = -1;
      for (let index = path.length - 1; index >= 0; index -= 1) {
        const ancestor = data[path[index]];
        if ((ancestor.children || []).includes(targetId) || (ancestor.molecules || []).includes(targetId)) {
          ancestorWithTarget = index;
          break;
        }
      }
      if (ancestorWithTarget < 0) return;
      path = [...path.slice(0, ancestorWithTarget + 1), targetId];
    }
    render();
  }

  elements.levelNav.addEventListener("click", (event) => {
    const breadcrumb = event.target.closest("[data-breadcrumb]");
    if (!breadcrumb) return;
    path = path.slice(0, Number(breadcrumb.dataset.breadcrumb) + 1);
    render();
  });

  document.addEventListener("click", (event) => {
    const moleculeButton = event.target.closest("[data-molecule]");
    if (moleculeButton) {
      openTarget(moleculeButton.dataset.molecule);
      return;
    }
    const targetButton = event.target.closest("[data-target]");
    if (targetButton) openTarget(targetButton.dataset.target);
  });

  document.addEventListener("keydown", (event) => {
    if ((event.key === "Enter" || event.key === " ") && event.target.matches(".hit-target, .diagram-action, .bilayer-lipid, .atp-reaction, .cytosol-molecule, .cytosol-structure-hit, .carrier-equation-token")) {
      event.preventDefault();
      openTarget(event.target.dataset.target);
    }
  });

  render();
})();