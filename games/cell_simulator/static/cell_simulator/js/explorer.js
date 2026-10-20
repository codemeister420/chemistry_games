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

  function roughErMembraneFeaturesSvg() {

    // Three major protein systems embedded in
    // or associated with the rough ER membrane.

    const proteins = [
      {
        id: "protein_translocon",
        label: "Sec61",
        x: 240,
        color: "#8a70b0",
        width: 68,
        pore: true
      },
      {
        id: "er_srp_receptor",
        label: "SRP RECEPTOR",
        x: 450,
        color: "#538c9b",
        width: 76,
        pore: false
      },
      {
        id: "er_ost",
        label: "OST",
        x: 665,
        color: "#b38355",
        width: 92,
        pore: false
      }
    ];

    const proteinMarkup = proteins.map((protein) => {

      const left = protein.x - protein.width / 2;

      const body = `
        <rect
          x="${left}"
          y="230"
          width="${protein.width}"
          height="161"
          rx="20"
          fill="${protein.color}"
          stroke="#344054"
          stroke-width="2"
        />
      `;

      const pore = protein.pore
        ? `
          <rect
            x="${protein.x - 9}"
            y="244"
            width="18"
            height="132"
            rx="9"
            fill="#daeaf2"
            stroke="#344054"
            stroke-width="1.5"
          />
          <path
            d="M${protein.x - 9} 308h18"
            stroke="#344054"
            stroke-width="3"
          />
        `
        : "";

      const details = protein.id === "er_srp_receptor"
        ? `
          <ellipse
            cx="${protein.x}"
            cy="215"
            rx="42"
            ry="29"
            fill="${protein.color}"
            stroke="#344054"
            stroke-width="2"
          />
        `
        : protein.id === "er_ost"
          ? `
            <ellipse
              cx="${protein.x}"
              cy="217"
              rx="50"
              ry="28"
              fill="${protein.color}"
              stroke="#344054"
              stroke-width="2"
            />
          `
          : "";

      return `
        <g
          class="diagram-action er-membrane-protein"
          data-target="${protein.id}"
          role="button"
          tabindex="0"
          aria-label="Explore ${protein.label}"
          style="cursor:pointer"
        >

          <rect
            x="${left - 9}"
            y="182"
            width="${protein.width + 18}"
            height="250"
            fill="transparent"
          />

          ${body}
          ${pore}
          ${details}

          <text
            x="${protein.x}"
            y="451"
            text-anchor="middle"
            font-size="15"
            font-weight="bold"
            fill="#64748b"
          >
            ${protein.label}
          </text>

        </g>
      `;
    }).join("");

    return `
      <g class="rough-er-membrane-features">

        <text
          x="450"
          y="146"
          text-anchor="middle"
          font-size="17"
          font-weight="bold"
          fill="#64748b"
        >
          ROUGH ER · MEMBRANE PROTEINS
        </text>

        <text
          x="450"
          y="174"
          text-anchor="middle"
          font-size="13"
          fill="#64748b"
        >
          PROTEIN TRANSLOCATION · TARGETING · GLYCOSYLATION
        </text>

        ${proteinMarkup}

      </g>
    `;
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

  function cytosolicRibosomeSvg() {
    const proteins = [
      [287, 245], [316, 208], [353, 185], [391, 211], [421, 174],
      [470, 190], [513, 177], [551, 205], [590, 222], [618, 258],
      [302, 386], [339, 425], [391, 442], [499, 438], [552, 420], [595, 390],
    ].map(([x, y]) => `<circle class="ribosome-protein-bead" cx="${x}" cy="${y}" r="7"/>`).join("");
    const trnas = [
      { site: "E", x: 360, anticodon: "CGA", state: "uncharged" },
      { site: "P", x: 450, anticodon: "AAA", state: "peptidyl" },
      { site: "A", x: 540, anticodon: "CUU", state: "aminoacyl" },
    ].map(({ site, x, anticodon, state }) => `<g class="ribosome-trna diagram-action" data-target="${site === 'E' ? 'trna_e_site' : site === 'P' ? 'trna_p_site' : 'trna_a_site'}" role="button" tabindex="0" aria-label="Inspect transfer RNA at the ${site} site, anticodon ${anticodon}">
      <path class="trna-backbone ${state}" d="M${x} 386v-35c-20-8-22-27-9-34 6-4 13-1 18 4 10 11 4 24-9 30m0-20-20-14m20 14 21-15m-21 15v-28m-7 2 7-8 7 8"/>
      <ellipse class="trna-hit" cx="${x}" cy="354" rx="28" ry="46"/>
      <text class="ribosome-site-label" x="${x}" y="302">${site} SITE</text>
      <text class="trna-anticodon" x="${x}" y="387">${anticodon}</text>
      ${state === "aminoacyl" ? `<circle class="trna-amino-acid" cx="${x}" cy="311" r="8"/><text class="trna-state-label" x="${x}" y="289">AMINO ACID</text>` : ""}
    </g>`).join("");
    return `<g class="cytosolic-ribosome-visual">
      <text class="ribosome-view-label" x="450" y="122">EUKARYOTIC CYTOSOLIC RIBOSOME · TRANSLATION ELONGATION</text>

      <g class="ribosome-subunit diagram-action" data-target="large_subunit" role="button" tabindex="0" aria-label="Inspect the 60S large ribosomal subunit">
        <path class="ribosome-large-body" d="M255 315C230 286 238 245 264 222c1-37 37-67 75-64 25-38 78-47 111-22 35-30 87-19 105 15 42-8 79 20 80 58 31 26 35 65 8 94-22 24-58 34-92 22-32 28-73 30-108 12-34 24-76 22-105 3-30 11-63 2-83-25Z"/>
        <text class="ribosome-subunit-label" x="450" y="216">60S LARGE SUBUNIT</text>
      </g>
      <g class="ribosome-subunit diagram-action" data-target="small_subunit" role="button" tabindex="0" aria-label="Inspect the 40S small ribosomal subunit">
        <path class="ribosome-small-body" d="M291 368c20-31 60-40 95-31 28-20 72-22 101-3 32-18 72-13 96 10 37-1 69 18 77 48 5 24-10 47-34 57-40 18-89 6-128 8-54 2-115 23-164 5-44-16-62-59-43-94Z"/>
        <text class="ribosome-subunit-label" x="450" y="456">40S SMALL SUBUNIT</text>
      </g>


      <g class="ribosome-mrna diagram-action" data-target="messenger_rna" role="button" tabindex="0" aria-label="Inspect messenger RNA threaded through the decoding channel, read 5 prime to 3 prime">
        <path class="mrna-backbone" d="M290 401H612"/>
        <path class="mrna-codon-divider" d="M405 390v22m90-22v22m90-22v22"/>
        <text class="mrna-codon" x="360" y="415">GCU</text>
        <text class="mrna-codon" x="450" y="415">UUU</text>
        <text class="mrna-codon" x="540" y="415">GAA</text>
        <text class="mrna-direction" x="285" y="430">5′</text>
        <text class="mrna-direction" x="617" y="430">3′</text>
        <text class="ribosome-feature-label mrna-label" x="450" y="478">mRNA · CODONS READ 5′ → 3′</text>
      </g>

      ${trnas}
      <path class="nascent-peptide-bond" d="M450 319v-64"/>
      <g class="nascent-peptide" aria-hidden="true">
        <circle cx="450" cy="252" r="7"/><circle cx="450" cy="234" r="7"/><circle cx="450" cy="216" r="7"/>
        <path d="M450 209v-21"/>
      </g>
      <text class="nascent-peptide-label" x="484" y="193">GROWING PEPTIDE</text>
      <text class="ribosome-model-note" x="450" y="509">E · EXIT (UNCHARGED)  /  P · PEPTIDYL-tRNA  /  A · INCOMING AMINOACYL-tRNA</text>
      <text class="diagram-note" x="450" y="536">SCHEMATIC 80S MACHINE · SUBUNIT SILHOUETTES AND MOLECULAR POSITIONS SIMPLIFIED</text>
    </g>`;
  }

  // Display only the selected ribosome subunit, enlarged.
  function ribosomeSubunitSvg(targetId) {
    const isLarge = targetId === "large_subunit";

    const zoom = isLarge ? 1.55 : 1.75;
    const translateY = isLarge ? 245 : 400;

    const subunitShape = isLarge
      ? `<path class="ribosome-large-body" d="M255 315C230 286 238 245 264 222c1-37 37-67 75-64 25-38 78-47 111-22 35-30 87-19 105 15 42-8 79 20 80 58 31 26 35 65 8 94-22 24-58 34-92 22-32 28-73 30-108 12-34 24-76 22-105 3-30 11-63 2-83-25Z"/>`
      : `<path class="ribosome-small-body" d="M291 368c20-31 60-40 95-31 28-20 72-22 101-3 32-18 72-13 96 10 37-1 69 18 77 48 5 24-10 47-34 57-40 18-89 6-128 8-54 2-115 23-164 5-44-16-62-59-43-94Z"/>`;

    const rrna = isLarge
      ? `
        <path class="ribosome-rrna-large" d="M278 280c21-34 40 28 63-4s39-44 60-4 41 35 63 2 37-28 58 6 44 28 73-15"/>
        <path class="ribosome-rrna-large" d="M305 302c17-22 34 24 51 5s38-35 55-3 37 29 55 1 34-24 53 6 38 19 57-7"/>
      `
      : `
        <path class="ribosome-rrna-small" d="M309 384c21-17 31 27 51 10s34-20 51 3 36 18 53-4 34-17 50 4 34 12 53-7"/>
        <path class="ribosome-rrna-small" d="M331 413c17-14 29 18 45 8s28-17 43 1 30 14 45-2 31-13 47 3 28 7 41-4"/>
      `;

    const proteinPositions = isLarge
      ? [
          [287, 245], [316, 208], [353, 185], [391, 211],
          [421, 174], [470, 190], [513, 177],
          [551, 205], [590, 222], [618, 258]
        ]
      : [
          [302, 386], [339, 425], [391, 442],
          [499, 438], [552, 420], [595, 390]
        ];

    const proteins = proteinPositions
      .map(([x, y]) =>
        `<circle class="ribosome-protein-bead" cx="${x}" cy="${y}" r="7"/>`
      )
      .join("");

    const name = isLarge
      ? "60S LARGE SUBUNIT"
      : "40S SMALL SUBUNIT";

    const labelY = isLarge ? 216 : 456;

    const description = isLarge
      ? "60S · rRNA AND RIBOSOMAL PROTEINS · PEPTIDE-BOND CATALYSIS"
      : "40S · rRNA AND RIBOSOMAL PROTEINS · mRNA DECODING";

    return `
      <g class="cytosolic-ribosome-visual ribosome-isolated-view">

        <text class="ribosome-view-label" x="450" y="121">
          ${name} · ISOLATED VIEW
        </text>

        <g transform="translate(450 322) scale(${zoom}) translate(-450 -${translateY})">

          <g class="ribosome-subunit">
            ${subunitShape}
            <text class="ribosome-subunit-label"
                  x="450" y="${labelY}">
              ${name}
            </text>
          </g>

         
           <g
          class="ribosome-rna-feature diagram-action"
          data-target="${isLarge ? 'large_subunit_rrna' : 'small_subunit_rrna'}"
          role="button"
          tabindex="0"
          aria-label="Inspect ribosomal RNA"
        >
          ${rrna}
          <text
            class="ribosome-feature-label rrna-label"
            x="${isLarge ? 315 : 335}"
            y="${isLarge ? 274 : 380}"
          >
            rRNA CORE
          </text>
        </g>


         
          <g
            class="ribosome-protein-feature diagram-action"
            data-target="${isLarge ? 'large_subunit_proteins' : 'small_subunit_proteins'}"
            role="button"
            tabindex="0"
            aria-label="Inspect ribosomal proteins"
          >
            ${proteins}

            <text
              class="ribosome-feature-label protein-label"
              x="${isLarge ? 575 : 560}"
              y="${isLarge ? 310 : 430}"
            >
              RIBOSOMAL PROTEINS
            </text>
          </g>


        <text class="diagram-note" x="450" y="560">
          ${description}
        </text>

        <text class="diagram-note" x="450" y="585">
          USE THE NAVIGATION TRAIL TO RETURN TO THE 80S RIBOSOME
        </text>

      </g>
    `;
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
    
    // Golgi transport carriers
    if (targetId === "golgi_transport_carriers") {
      return golgiTransportCarriersSvg();
    }

    
    // Trans-Golgi network cargo sorting
    if (targetId === "trans_golgi_network") {
      return transGolgiNetworkSvg();
    }

    
    // Trans-Golgi terminal glycosylation
    if (targetId === "trans_golgi") {
      return transGolgiSvg();
    }

    
    // Medial-Golgi glycan processing
    if (targetId === "medial_golgi") {
      return medialGolgiSvg();
    }

    
    // Cis-Golgi: cargo arrival, tethering and glycan processing
    if (targetId === "cis_golgi") {
      return cisGolgiSvg();
    }

    
    // Golgi membrane: existing lipid bilayer
    // with Golgi-associated proteins.
    if (targetId === "golgi_membrane") {
      return `
        ${membraneLipidsSvg(target.molecules || [], false)}
        ${golgiMembraneFeaturesSvg()}
      `;
    }


     // Golgi apparatus overview
    if (targetId === "golgi") {
      return golgiOverviewSvg();
    }
    
    // Smooth ER lumen
    if (targetId === "smooth_er_lumen") {
      return smoothErLumenSvg();
    }

    
    // Smooth ER CYP450 metabolism
    if (targetId === "detoxification") {
      return serDetoxificationSvg();
    }


    // Smooth ER calcium regulation
    if (targetId === "calcium_store") {
      return serCalciumRegulationSvg();
    }

    // Smooth ER lipid metabolism overview
    if (targetId === "lipid_synthesis") {
      return serLipidSynthesisSvg();
    }

      if (targetId === "smooth_er") {
    return smoothErOverviewSvg();
  }
    
    // Dedicated COPII ER exit site overview
    if (targetId === "rough_er_exit_sites") {
      return copiiExitSiteSvg();
    }

    
    // ER N-linked glycosylation overview
    if (targetId === "er_n_glycosylation") {
      return erGlycosylationSvg();
    }

    
    // Dedicated Rough ER lumen exploration
    if (targetId === "rough_er_lumen") {
      return roughErLumenSvg();
    }

    
    // Dedicated rough ER overview
    if (targetId === "rough_er") {
      return roughErOverviewSvg();
    }


    // Display only the selected ribosome subunit, enlarged.
    if (targetId === "large_subunit" || targetId === "small_subunit") {
      return ribosomeSubunitSvg(targetId);
    }

    switch (visual) {
      
     
      case "membrane":
        return `
          ${membraneLipidsSvg(
            target.molecules || [],
            targetId === "plasma_membrane"
          )}

          ${targetId === "plasma_membrane"
            ? plasmaMembraneFeaturesSvg()
            : ""}

          ${targetId === "rough_er_membrane"
            ? roughErMembraneFeaturesSvg()
            : ""}

          ${targetId === "smooth_er_membrane"
            ? smoothErMembraneFeaturesSvg()
            : ""}
        `;


      case "cytosol":
        return cytosolSceneSvg(target, targetId);
      case "cytosolic_ribosome":
        return cytosolicRibosomeSvg();
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
  
  function golgiTransportCarriersSvg() {

    const carriers = [
      {
        id: "golgi_copii_transport",
        x: 244,
        y: 228,
        title: "COPII TRANSPORT",
        subtitle: "ER → ERGIC → CIS-GOLGI",
        color: "#649cc4",
        type: "copii"
      },
      {
        id: "golgi_copi_recycling",
        x: 656,
        y: 228,
        title: "COPI RECYCLING",
        subtitle: "GOLGI → ER / EARLIER GOLGI",
        color: "#ab85bd",
        type: "copi"
      },
      {
        id: "golgi_post_export",
        x: 244,
        y: 433,
        title: "POST-GOLGI EXPORT",
        subtitle: "TGN → DOWNSTREAM TARGETS",
        color: "#c18e64",
        type: "export"
      },
      {
        id: "golgi_carrier_fusion",
        x: 656,
        y: 433,
        title: "TETHERING & FUSION",
        subtitle: "RAB · TETHERS · SNAREs",
        color: "#65a28b",
        type: "fusion"
      }
    ];

    // A basic membrane-enclosed carrier.
    function vesicle(x, y, radius, fill, stroke) {
      return `
        <circle cx="${x}" cy="${y}"
                r="${radius}"
                fill="${fill}"
                stroke="${stroke}"
                stroke-width="3"/>

        <circle cx="${x}" cy="${y}"
                r="${radius - 9}"
                fill="none"
                stroke="${stroke}"
                stroke-width="2"
                opacity="0.6"/>
      `;
    }

    // COPII protein coat:
    // Sar1, Sec23/24 and Sec13/31.
    function copiiIcon(x, y) {

      const coat = Array.from({ length: 12 }, (_, i) => {

        const angle = (i * Math.PI * 2) / 12;
        const px = x + Math.cos(angle) * 43;
        const py = y + Math.sin(angle) * 43;

        return `
          <circle cx="${px}" cy="${py}"
                  r="5"
                  fill="#5d94bc"
                  stroke="#ffffff"
                  stroke-width="1"/>
        `;
      }).join("");

      return `
        ${vesicle(x, y, 36, "#d7e9f5", "#629cc5")}
        ${coat}

        <text x="${x}" y="${y + 5}"
              text-anchor="middle"
              font-size="12"
              font-weight="bold"
              fill="#456f91">
          COPII
        </text>
      `;
    }

    // COPI carrier with a stylized coatomer.
    function copiIcon(x, y) {

      const coat = Array.from({ length: 10 }, (_, i) => {

        const angle = (i * Math.PI * 2) / 10;
        const px = x + Math.cos(angle) * 43;
        const py = y + Math.sin(angle) * 43;

        return `
          <rect x="${px - 5}" y="${py - 5}"
                width="10" height="10"
                rx="2"
                fill="#9c78b3"
                stroke="#ffffff"
                stroke-width="1"/>
        `;
      }).join("");

      return `
        ${vesicle(x, y, 36, "#e8dbf1", "#9c78b3")}
        ${coat}

        <text x="${x}" y="${y + 5}"
              text-anchor="middle"
              font-size="12"
              font-weight="bold"
              fill="#74558e">
          COPI
        </text>
      `;
    }

    // Post-Golgi carriers have diverse shapes and coats.
    function exportIcon(x, y) {
      return `
        ${vesicle(x - 18, y, 31, "#f2dfcc", "#b9865e")}

        <circle cx="${x + 41}" cy="${y - 16}"
                r="20"
                fill="#e8bd98"
                stroke="#b9865e"
                stroke-width="3"/>

        <path d="M${x + 4} ${y}
                 H${x + 17}"
              stroke="#b9865e"
              stroke-width="3"
              fill="none"/>

        <path d="M${x + 11} ${y - 7}
                 L${x + 19} ${y}
                 L${x + 11} ${y + 7}"
              stroke="#b9865e"
              stroke-width="3"
              fill="none"/>

        <text x="${x - 18}" y="${y + 5}"
              text-anchor="middle"
              font-size="10"
              font-weight="bold"
              fill="#966443">
          CARGO
        </text>
      `;
    }

    // Tethering followed by membrane fusion.
    function fusionIcon(x, y) {
      return `
        <path d="M${x - 78} ${y + 42}
                 Q${x} ${y + 15}
                 ${x + 78} ${y + 42}"
              fill="none"
              stroke="#70a78e"
              stroke-width="12"
              stroke-linecap="round"/>

        <circle cx="${x}" cy="${y - 20}"
                r="26"
                fill="#c9e6d5"
                stroke="#599579"
                stroke-width="3"/>

        <path d="M${x - 9} ${y + 7}
                 L${x - 9} ${y + 29}
                 M${x + 9} ${y + 7}
                 L${x + 9} ${y + 29}"
              fill="none"
              stroke="#447e64"
              stroke-width="5"
              stroke-linecap="round"/>

        <path d="M${x - 20} ${y + 7}
                 L${x - 5} ${y + 25}
                 M${x + 20} ${y + 7}
                 L${x + 5} ${y + 25}"
              fill="none"
              stroke="#8c75b2"
              stroke-width="4"
              stroke-linecap="round"/>
      `;
    }

    function drawIcon(type, x, y) {

      switch (type) {
        case "copii":
          return copiiIcon(x, y);
        case "copi":
          return copiIcon(x, y);
        case "export":
          return exportIcon(x, y);
        case "fusion":
          return fusionIcon(x, y);
        default:
          return "";
      }
    }

    const cards = carriers.map((item) => `
      <g class="diagram-action"
         data-target="${item.id}"
         role="button"
         tabindex="0"
         aria-label="Explore ${item.title}"
         style="cursor:pointer">

        <rect x="${item.x - 185}"
              y="${item.y - 90}"
              width="370"
              height="178"
              rx="21"
              fill="${item.color}"
              fill-opacity="0.09"
              stroke="${item.color}"
              stroke-width="2"/>

        <text x="${item.x}"
              y="${item.y - 62}"
              text-anchor="middle"
              font-size="16"
              font-weight="bold"
              fill="${item.color}">
          ${item.title}
        </text>

        ${drawIcon(item.type, item.x, item.y)}

        <text x="${item.x}"
              y="${item.y + 72}"
              text-anchor="middle"
              font-size="12"
              font-weight="bold"
              fill="#475569">
          ${item.subtitle}
        </text>
      </g>
    `).join("");

    return `
      <g class="golgi-transport-carriers-visual">

        <text x="450" y="88"
              text-anchor="middle"
              font-size="20"
              font-weight="bold"
              fill="#64748b">
          GOLGI TRANSPORT CARRIERS
        </text>

        <text x="450" y="117"
              text-anchor="middle"
              font-size="13"
              fill="#64748b">
          CARGO TRANSPORT · RECYCLING · MEMBRANE FUSION
        </text>

        ${cards}

        <text x="450" y="549"
              text-anchor="middle"
              font-size="12"
              fill="#64748b">
          SELECT A TRANSPORT SYSTEM TO EXPLORE ITS MOLECULES
        </text>

        <text x="450" y="571"
              text-anchor="middle"
              font-size="11"
              fill="#64748b">
          SCHEMATIC CARRIERS · COAT STRUCTURES ARE SIMPLIFIED
        </text>

      </g>
    `;
  }

  
  function transGolgiNetworkSvg() {

    // Four selectable pathways associated with TGN sorting.
    // Each card represents a different trafficking process.

    const pathways = [
      {
        id: "tgn_constitutive_secretion",
        x: 245,
        y: 235,
        color: "#629abb",
        title: "CONSTITUTIVE SECRETION",
        subtitle: "PLASMA MEMBRANE DELIVERY",
        type: "constitutive"
      },
      {
        id: "tgn_regulated_secretion",
        x: 655,
        y: 235,
        color: "#ad83bc",
        title: "REGULATED SECRETION",
        subtitle: "STORED SECRETORY GRANULES",
        type: "regulated"
      },
      {
        id: "tgn_lysosomal_sorting",
        x: 245,
        y: 425,
        color: "#c18c61",
        title: "ENDOSOMAL SORTING",
        subtitle: "M6P RECEPTOR · LYSOSOMES",
        type: "lysosomal"
      },
      {
        id: "tgn_coat_adaptors",
        x: 655,
        y: 425,
        color: "#6d9d88",
        title: "COAT & ADAPTORS",
        subtitle: "ARF1 · AP-1 · CLATHRIN",
        type: "coat"
      }
    ];

    function pathwayIcon(type, x, y) {

      if (type === "constitutive") {
        return `
          <g>
            <!-- Secretory transport carrier -->
            <circle cx="${x - 43}" cy="${y - 12}"
                    r="26"
                    fill="#a8cce2"
                    stroke="#5689ab"
                    stroke-width="3"/>

            <circle cx="${x - 43}" cy="${y - 12}"
                    r="8"
                    fill="#5689ab"/>

            <!-- Direction of movement -->
            <path d="M${x - 10} ${y - 12}
                     H${x + 52}"
                  fill="none"
                  stroke="#5689ab"
                  stroke-width="3"
                  stroke-dasharray="6 4"/>

            <path d="M${x + 42} ${y - 20}
                     L${x + 54} ${y - 12}
                     L${x + 42} ${y - 4}"
                  fill="none"
                  stroke="#5689ab"
                  stroke-width="3"/>

            <!-- Plasma membrane -->
            <path d="M${x + 68} ${y - 50}
                     V${y + 27}"
                  stroke="#6d9d88"
                  stroke-width="12"
                  stroke-linecap="round"/>

            <path d="M${x + 83} ${y - 50}
                     V${y + 27}"
                  stroke="#a1c5b5"
                  stroke-width="8"
                  stroke-linecap="round"/>
          </g>
        `;
      }

      if (type === "regulated") {
        return `
          <g>
            <!-- Dense-core secretory granule -->
            <circle cx="${x}" cy="${y - 14}"
                    r="37"
                    fill="#dfcbe7"
                    stroke="#9872ac"
                    stroke-width="4"/>

            <circle cx="${x}" cy="${y - 14}"
                    r="20"
                    fill="#a47ab7"/>

            <g fill="#714e8e">
              <circle cx="${x - 7}" cy="${y - 20}" r="4"/>
              <circle cx="${x + 8}" cy="${y - 14}" r="4"/>
              <circle cx="${x - 2}" cy="${y - 4}" r="4"/>
            </g>

            <!-- Calcium-dependent release cue -->
            <circle cx="${x + 65}" cy="${y - 23}"
                    r="12"
                    fill="#7bbce5"
                    stroke="#4c8eb7"
                    stroke-width="2"/>

            <text x="${x + 65}" y="${y - 19}"
                  text-anchor="middle"
                  font-size="10"
                  font-weight="bold"
                  fill="#ffffff">
              Ca
            </text>
          </g>
        `;
      }

      if (type === "lysosomal") {
        return `
          <g>
            <!-- Transport carrier -->
            <circle cx="${x - 45}" cy="${y - 12}"
                    r="28"
                    fill="#ecd1b6"
                    stroke="#ad7c52"
                    stroke-width="3"/>

            <!-- M6P-tagged cargo symbol -->
            <circle cx="${x - 50}" cy="${y - 15}"
                    r="10"
                    fill="#78ad83"/>

            <text x="${x - 45}" y="${y + 5}"
                  text-anchor="middle"
                  font-size="10"
                  fill="#805a38">
              M6P
            </text>

            <path d="M${x - 12} ${y - 12}
                     H${x + 49}"
                  fill="none"
                  stroke="#ad7c52"
                  stroke-width="3"
                  stroke-dasharray="6 4"/>

            <path d="M${x + 39} ${y - 20}
                     L${x + 52} ${y - 12}
                     L${x + 39} ${y - 4}"
                  fill="none"
                  stroke="#ad7c52"
                  stroke-width="3"/>

            <!-- Endosome -->
            <ellipse cx="${x + 75}" cy="${y - 12}"
                     rx="24" ry="29"
                     fill="#f0d5a9"
                     stroke="#b58a4f"
                     stroke-width="3"/>
          </g>
        `;
      }

      if (type === "coat") {
        return `
          <g>
            <!-- Simplified coated carrier -->
            <circle cx="${x}" cy="${y - 12}"
                    r="34"
                    fill="#b5d8c5"
                    stroke="#568b72"
                    stroke-width="3"/>

            <circle cx="${x}" cy="${y - 12}"
                    r="24"
                    fill="#dcece3"
                    stroke="#568b72"
                    stroke-width="2"/>

            <!-- Coat lattice -->
            <g stroke="#568b72"
               stroke-width="3"
               fill="none">
              <path d="M${x - 29} ${y - 29}
                       L${x - 10} ${y - 44}
                       L${x + 12} ${y - 43}
                       L${x + 30} ${y - 26}"/>

              <path d="M${x - 30} ${y + 3}
                       L${x - 13} ${y + 17}
                       L${x + 12} ${y + 17}
                       L${x + 30} ${y + 2}"/>

              <path d="M${x - 34} ${y - 12}
                       L${x - 24} ${y - 27}
                       M${x + 34} ${y - 12}
                       L${x + 24} ${y - 27}"/>
            </g>
          </g>
        `;
      }

      return "";
    }

    const cards = pathways.map((item) => `
      <g class="diagram-action"
         data-target="${item.id}"
         role="button"
         tabindex="0"
         aria-label="Explore ${item.title}"
         style="cursor:pointer">

        <rect x="${item.x - 186}"
              y="${item.y - 86}"
              width="372"
              height="169"
              rx="20"
              fill="${item.color}"
              fill-opacity="0.09"
              stroke="${item.color}"
              stroke-width="2"/>

        <text x="${item.x}"
              y="${item.y - 59}"
              text-anchor="middle"
              font-size="15"
              font-weight="bold"
              fill="${item.color}">
          ${item.title}
        </text>

        ${pathwayIcon(item.type, item.x, item.y)}

        <text x="${item.x}"
              y="${item.y + 59}"
              text-anchor="middle"
              font-size="12"
              fill="#475569">
          ${item.subtitle}
        </text>
      </g>
    `).join("");

    return `
      <g class="trans-golgi-network-visual">

        <text x="450" y="90"
              text-anchor="middle"
              font-size="20"
              font-weight="bold"
              fill="#64748b">
          TRANS-GOLGI NETWORK
        </text>

        <text x="450" y="119"
              text-anchor="middle"
              font-size="13"
              fill="#64748b">
          CARGO SORTING · SECRETORY PATHWAYS · ENDOSOMAL TRANSPORT
        </text>

        ${cards}

        <text x="450" y="546"
              text-anchor="middle"
              font-size="12"
              fill="#64748b">
          SELECT A SORTING OR TRANSPORT PATHWAY
        </text>

        <text x="450" y="570"
              text-anchor="middle"
              font-size="11"
              fill="#64748b">
          PATHWAYS AND CARRIER TYPES VARY AMONG CELL TYPES
        </text>

      </g>
    `;
  }

  
  function transGolgiSvg() {

    // Simplified glycan notation:
    // Blue square = GlcNAc
    // Yellow circle = Galactose
    // Purple diamond = Neu5Ac

    function glycanSymbol(stage) {

      const terminal = stage >= 1;
      const sialylated = stage >= 2;

      return `
        <g transform="translate(0 0)">

          <!-- Core of representative glycan arm -->
          <path d="M0 90 V60"
                stroke="#64748b"
                stroke-width="3"/>

          <rect x="-11" y="79"
                width="22" height="22"
                rx="3"
                fill="#6298c8"
                stroke="#3b719c"
                stroke-width="2"/>

          <circle cx="0" cy="52"
                  r="12"
                  fill="#75aa81"
                  stroke="#508060"
                  stroke-width="2"/>

          <path d="M0 40 V14"
                stroke="#64748b"
                stroke-width="3"/>

          <rect x="-11" y="2"
                width="22" height="22"
                rx="3"
                fill="#6298c8"
                stroke="#3b719c"
                stroke-width="2"/>

          ${terminal ? `
            <path d="M0 2 V-25"
                  stroke="#64748b"
                  stroke-width="3"/>

            <circle cx="0" cy="-36"
                    r="13"
                    fill="#efc454"
                    stroke="#bb9333"
                    stroke-width="2"/>
          ` : ""}

          ${sialylated ? `
            <path d="M0 -49 V-74"
                  stroke="#64748b"
                  stroke-width="3"/>

            <polygon
              points="0,-100 15,-85 0,-70 -15,-85"
              fill="#b38bcd"
              stroke="#8665a4"
              stroke-width="2"/>
          ` : ""}

        </g>
      `;
    }

    const processes = [
      {
        id: "trans_galactosylation",
        x: 162,
        title: "B4GALT1",
        subtitle: "GALACTOSE ADDITION",
        color: "#c49b40",
        stage: 1
      },
      {
        id: "trans_sialylation",
        x: 450,
        title: "ST6GAL1",
        subtitle: "SIALIC ACID ADDITION",
        color: "#9373b6",
        stage: 2
      },
      {
        id: "trans_mature_glycan",
        x: 738,
        title: "MATURE GLYCAN",
        subtitle: "TERMINAL SUGAR PATTERN",
        color: "#649c8d",
        stage: 2
      }
    ];

    const cards = processes.map((item) => `
      <g class="diagram-action"
         data-target="${item.id}"
         role="button"
         tabindex="0"
         aria-label="Explore ${item.title}"
         style="cursor:pointer">

        <rect x="${item.x - 126}"
              y="165"
              width="252"
              height="274"
              rx="20"
              fill="${item.color}"
              fill-opacity="0.09"
              stroke="${item.color}"
              stroke-width="2"/>

        <text x="${item.x}" y="201"
              text-anchor="middle"
              font-size="17"
              font-weight="bold"
              fill="${item.color}">
          ${item.title}
        </text>

        <g transform="translate(${item.x} 320)">
          ${glycanSymbol(item.stage)}
        </g>

        <text x="${item.x}" y="416"
              text-anchor="middle"
              font-size="12"
              font-weight="bold"
              fill="#475569">
          ${item.subtitle}
        </text>

      </g>
    `).join("");

    return `
      <g class="trans-golgi-visual">

        <text x="450" y="98"
              text-anchor="middle"
              font-size="20"
              font-weight="bold"
              fill="#64748b">
          TRANS-GOLGI · TERMINAL GLYCOSYLATION
        </text>

        <text x="450" y="129"
              text-anchor="middle"
              font-size="13"
              fill="#64748b">
          GALACTOSE ADDITION · SIALYLATION · GLYCAN MATURATION
        </text>

        ${cards}

        <!-- Progression arrows -->
        <path d="M293 298H315
                 M306 290L317 298L306 306"
              fill="none"
              stroke="#64748b"
              stroke-width="3"/>

        <path d="M581 298H603
                 M594 290L605 298L594 306"
              fill="none"
              stroke="#64748b"
              stroke-width="3"/>

        <!-- Glycan symbol legend -->
        <g transform="translate(157 486)">

          <rect x="-9" y="-9"
                width="18" height="18"
                fill="#6298c8"
                stroke="#3b719c"/>

          <text x="20" y="5"
                font-size="13"
                fill="#64748b">
            GlcNAc
          </text>

          <circle cx="184" cy="0"
                  r="10"
                  fill="#efc454"
                  stroke="#bb9333"/>

          <text x="205" y="5"
                font-size="13"
                fill="#64748b">
            Galactose
          </text>

          <polygon points="399,-12 411,0 399,12 387,0"
                   fill="#b38bcd"
                   stroke="#8665a4"/>

          <text x="425" y="5"
                font-size="13"
                fill="#64748b">
            Sialic acid
          </text>

        </g>

        <text x="450" y="545"
              text-anchor="middle"
              font-size="12"
              fill="#64748b">
          SELECT AN ENZYME OR A MATURE GLYCAN TO EXPLORE
        </text>

        <text x="450" y="569"
              text-anchor="middle"
              font-size="11"
              fill="#64748b">
          SCHEMATIC TERMINAL GLYCAN ARM · NOT A COMPLETE GLYCAN STRUCTURE
        </text>

      </g>
    `;
  }

  
  function medialGolgiSvg() {

    // Schematic glycan symbols:
    // Blue squares = N-acetylglucosamine (GlcNAc)
    // Green circles = mannose (Man)
    //
    // This shows reaction types and residue changes,
    // not the complete molecular connectivity of a glycan.

    const steps = [
      {
        id: "medial_mgat1",
        title: "MGAT1",
        subtitle: "ADD FIRST GlcNAc",
        x: 162,
        color: "#6597c2"
      },
      {
        id: "medial_mannosidase_ii",
        title: "MAN2A1",
        subtitle: "REMOVE TWO MANNOSE",
        x: 450,
        color: "#70a58d"
      },
      {
        id: "medial_mgat2",
        title: "MGAT2",
        subtitle: "ADD SECOND GlcNAc",
        x: 738,
        color: "#ae8bb9"
      }
    ];

    // Each card contains a glycan-processing symbol.
    // The visual stages highlight a reaction, not a
    // chemically complete oligosaccharide formula.

    function glycanIcon(index, cx) {

      const blueSquare = (x, y) => `
        <rect x="${x - 10}" y="${y - 10}"
              width="20" height="20"
              rx="3"
              fill="#5e91c4"
              stroke="#426c9b"
              stroke-width="1.5"/>
      `;

      const greenCircle = (x, y, opacity = 1) => `
        <circle cx="${x}" cy="${y}" r="10"
                fill="#68ae80"
                fill-opacity="${opacity}"
                stroke="#3d8255"
                stroke-width="1.5"/>
      `;

      const line = (x1,y1,x2,y2) => `
        <path d="M${x1} ${y1}L${x2} ${y2}"
              fill="none"
              stroke="#64748b"
              stroke-width="3"/>
      `;

      let symbol = `
        ${line(cx, 331, cx, 302)}
        ${blueSquare(cx, 331)}
        ${blueSquare(cx, 306)}
        ${line(cx, 293, cx, 272)}
        ${greenCircle(cx, 265)}
        ${line(cx, 255, cx - 31, 236)}
        ${line(cx, 255, cx + 31, 236)}
        ${greenCircle(cx - 39, 230)}
        ${greenCircle(cx + 39, 230)}
      `;

      if (index === 0) {
        // GlcNAc addition (MGAT1).
        symbol += `
          ${line(cx + 47, 230, cx + 68, 217)}
          ${blueSquare(cx + 79, 209)}

          <text x="${cx}" y="363"
                text-anchor="middle"
                font-size="12"
                fill="#426c9b">
            + GlcNAc
          </text>
        `;
      }

      if (index === 1) {
        // Two mannose residues removed.
        symbol += `
          <circle cx="${cx - 61}" cy="204" r="11"
                  fill="#68ae80"
                  fill-opacity="0.30"
                  stroke="#c76e6e"
                  stroke-width="2"
                  stroke-dasharray="4 3"/>

          <circle cx="${cx + 61}" cy="204" r="11"
                  fill="#68ae80"
                  fill-opacity="0.30"
                  stroke="#c76e6e"
                  stroke-width="2"
                  stroke-dasharray="4 3"/>

          <text x="${cx}" y="363"
                text-anchor="middle"
                font-size="12"
                fill="#3d8255">
            − 2 Man
          </text>
        `;
      }

      if (index === 2) {
        // Additional GlcNAc produces a second antenna.
        symbol += `
          ${line(cx - 47, 230, cx - 68, 217)}
          ${blueSquare(cx - 79, 209)}
          ${line(cx + 47, 230, cx + 68, 217)}
          ${blueSquare(cx + 79, 209)}

          <text x="${cx}" y="363"
                text-anchor="middle"
                font-size="12"
                fill="#805b95">
            + GlcNAc
          </text>
        `;
      }

      return symbol;
    }

    const cards = steps.map((step, index) => `
      <g class="diagram-action"
         data-target="${step.id}"
         role="button"
         tabindex="0"
         aria-label="Explore ${step.title}"
         style="cursor:pointer">

        <rect x="${step.x - 126}"
              y="160"
              width="252"
              height="270"
              rx="20"
              fill="${step.color}"
              fill-opacity="0.09"
              stroke="${step.color}"
              stroke-width="2"/>

        <text x="${step.x}" y="193"
              text-anchor="middle"
              font-size="17"
              font-weight="bold"
              fill="${step.color}">
          ${step.title}
        </text>

        ${glycanIcon(index, step.x)}

        <text x="${step.x}" y="398"
              text-anchor="middle"
              font-size="12"
              font-weight="bold"
              fill="#475569">
          ${step.subtitle}
        </text>
      </g>
    `).join("");

    return `
      <g class="medial-golgi-visual">

        <text x="450" y="103"
              text-anchor="middle"
              font-size="20"
              font-weight="bold"
              fill="#64748b">
          MEDIAL-GOLGI · GLYCAN MATURATION
        </text>

        <text x="450" y="132"
              text-anchor="middle"
              font-size="13"
              fill="#64748b">
          SELECT AN ENZYME TO EXPLORE ITS REACTION
        </text>

        ${cards}

        <!-- Direction of glycan processing -->
        <path d="M292 300H317"
              stroke="#64748b"
              stroke-width="3"
              fill="none"/>

        <path d="M309 293L319 300L309 307"
              stroke="#64748b"
              stroke-width="3"
              fill="none"/>

        <path d="M580 300H605"
              stroke="#64748b"
              stroke-width="3"
              fill="none"/>

        <path d="M597 293L607 300L597 307"
              stroke="#64748b"
              stroke-width="3"
              fill="none"/>

        <g font-size="12" fill="#64748b">
          <text x="450" y="475" text-anchor="middle">
            BLUE SQUARE = N-ACETYLGLUCOSAMINE (GlcNAc)
          </text>

          <text x="450" y="498" text-anchor="middle">
            GREEN CIRCLE = MANNOSE (Man)
          </text>
        </g>

        <text x="450" y="549"
              text-anchor="middle"
              font-size="12"
              fill="#64748b">
          PROCESSING SEQUENCE FOR A REPRESENTATIVE COMPLEX N-GLYCAN PATHWAY
        </text>

        <text x="450" y="571"
              text-anchor="middle"
              font-size="11"
              fill="#64748b">
          SIMPLIFIED GLYCAN SCHEMATICS · NOT COMPLETE LINKAGE STRUCTURES
        </text>

      </g>
    `;
  }

  
  function cisGolgiSvg() {

    // Three molecular processes of the receiving Golgi region.
    const targets = [
      {
        id: "cis_cargo_arrival",
        x: 165,
        title: "CARGO ARRIVAL",
        subtitle: "ER → ERGIC → cis-Golgi",
        color: "#689bc1"
      },
      {
        id: "cis_tether_fusion",
        x: 450,
        title: "TETHERING & FUSION",
        subtitle: "GM130 · SNARE proteins",
        color: "#8c75b2"
      },
      {
        id: "cis_glycan_processing",
        x: 735,
        title: "GLYCAN PROCESSING",
        subtitle: "MAN1A1 · Mannose removal",
        color: "#61a18b"
      }
    ];

    const carriers = `
      <g>
        <circle cx="115" cy="259" r="24"
                fill="#a6cce5"
                stroke="#5d90b6"
                stroke-width="3"/>
        <circle cx="143" cy="295" r="15"
                fill="#a6cce5"
                stroke="#5d90b6"
                stroke-width="2"/>

        <path d="M157 250 L221 250"
              stroke="#5d90b6"
              stroke-width="4"
              stroke-dasharray="7 5"/>

        <path d="M210 242 L222 250 L210 258"
              fill="none"
              stroke="#5d90b6"
              stroke-width="3"/>
      </g>
    `;

    const tethering = `
      <g>
        <!-- Incoming membrane carrier -->
        <circle cx="419" cy="258" r="29"
                fill="#b7a7d5"
                stroke="#7b629f"
                stroke-width="3"/>

        <!-- Golgi-associated tether -->
        <path d="M442 268
                 C459 286 454 305 469 319"
              fill="none"
              stroke="#7b629f"
              stroke-width="7"
              stroke-linecap="round"/>

        <!-- Stylized SNARE pairing -->
        <path d="M452 327 L463 357
                 M474 327 L463 357"
              fill="none"
              stroke="#7b629f"
              stroke-width="6"
              stroke-linecap="round"/>
      </g>
    `;

    const glycan = `
      <g stroke="#ffffff" stroke-width="2">
        <rect x="699" y="241" width="19" height="19"
              rx="4" fill="#739ac5"/>
        <rect x="699" y="265" width="19" height="19"
              rx="4" fill="#739ac5"/>

        <circle cx="740" cy="251" r="12"
                fill="#66aa83"/>
        <circle cx="766" cy="236" r="12"
                fill="#66aa83"/>
        <circle cx="766" cy="267" r="12"
                fill="#66aa83"/>

        <path d="M718 251H729
                 M718 274L730 256
                 M751 245L755 239
                 M751 256L755 263"
              fill="none" stroke="#587f9a"
              stroke-width="3"/>
      </g>
    `;

    const cards = targets.map((item, index) => `
      <g class="diagram-action"
         data-target="${item.id}"
         role="button"
         tabindex="0"
         aria-label="Explore ${item.title}"
         style="cursor:pointer">

        <rect x="${item.x - 125}"
              y="186"
              width="250"
              height="245"
              rx="21"
              fill="${item.color}"
              fill-opacity="0.10"
              stroke="${item.color}"
              stroke-width="2"/>

        ${index === 0
          ? carriers
          : index === 1
            ? tethering
            : glycan}

        <text x="${item.x}"
              y="383"
              text-anchor="middle"
              font-size="14"
              font-weight="bold"
              fill="#334155">
          ${item.title}
        </text>

        <text x="${item.x}"
              y="406"
              text-anchor="middle"
              font-size="12"
              fill="#64748b">
          ${item.subtitle}
        </text>
      </g>
    `).join("");

    return `
      <g class="cis-golgi-visual">

        <text x="450" y="106"
              text-anchor="middle"
              font-size="20"
              font-weight="bold"
              fill="#64748b">
          CIS-GOLGI · RECEIVING FACE
        </text>

        <text x="450" y="136"
              text-anchor="middle"
              font-size="13"
              fill="#64748b">
          ER CARGO ARRIVAL · MEMBRANE FUSION · EARLY GLYCAN PROCESSING
        </text>

        ${cards}

        <text x="450" y="464"
              text-anchor="middle"
              font-size="12"
              fill="#64748b">
          SELECT A PROCESS TO EXPLORE ITS MOLECULAR MACHINERY
        </text>

        <text x="450" y="487"
              text-anchor="middle"
              font-size="11"
              fill="#64748b">
          SCHEMATIC: DIFFERENT PROCESSES MAY OVERLAP IN LOCATION AND TIME
        </text>

      </g>
    `;
  }

  
  function golgiMembraneFeaturesSvg() {

    const gm130 = `
      <g class="diagram-action"
         data-target="golgi_gm130"
         role="button"
         tabindex="0"
         aria-label="Explore GM130"
         style="cursor:pointer">

        <rect x="138" y="153"
              width="185" height="242"
              rx="15"
              fill="transparent"/>

        <!-- Peripheral coiled-coil protein -->
        <path d="M204 248
                 C191 230 218 216 205 198
                 S224 171 211 153"
              stroke="#8e77b3"
              stroke-width="10"
              stroke-linecap="round"
              fill="none"/>

        <path d="M225 248
                 C238 229 209 211 229 193
                 S211 166 227 153"
              stroke="#b19bd3"
              stroke-width="9"
              stroke-linecap="round"
              fill="none"/>

        <ellipse cx="214" cy="255"
                 rx="30" ry="12"
                 fill="#c5b6de"
                 stroke="#8e77b3"
                 stroke-width="2"/>

        <text x="215" y="135"
              text-anchor="middle"
              font-size="17"
              font-weight="bold"
              fill="#79649e">
          GM130
        </text>

        <text x="215" y="151"
              text-anchor="middle"
              font-size="11"
              fill="#64748b">
          CIS-GOLGI TETHER
        </text>
      </g>
    `;

    const tmem165 = `
      <g class="diagram-action"
         data-target="golgi_tmem165"
         role="button"
         tabindex="0"
         aria-label="Explore TMEM165"
         style="cursor:pointer">

        <rect x="347" y="166"
              width="205" height="243"
              rx="15"
              fill="transparent"/>

        <!-- Stylized multipass protein -->
        <path d="M395 244
                 L395 378
                 Q417 408 438 378
                 L438 244
                 Q458 214 479 244
                 L479 378
                 Q494 400 510 378
                 L510 244"
              fill="none"
              stroke="#568eab"
              stroke-width="15"
              stroke-linejoin="round"
              stroke-linecap="round"/>

        <text x="452" y="139"
              text-anchor="middle"
              font-size="17"
              font-weight="bold"
              fill="#426f91">
          TMEM165
        </text>

        <text x="452" y="156"
              text-anchor="middle"
              font-size="11"
              fill="#64748b">
          GOLGI ION HOMEOSTASIS
        </text>

        <text x="452" y="421"
              text-anchor="middle"
              font-size="13"
              fill="#426f91">
          Mn²⁺ · Ca²⁺
        </text>
      </g>
    `;

    const tgn46 = `
      <g class="diagram-action"
         data-target="golgi_tgn46"
         role="button"
         tabindex="0"
         aria-label="Explore TGN46"
         style="cursor:pointer">

        <rect x="593" y="162"
              width="190" height="258"
              rx="16"
              fill="transparent"/>

        <!-- Single transmembrane anchor -->
        <path d="M684 246 L684 379"
              fill="none"
              stroke="#63a48b"
              stroke-width="17"
              stroke-linecap="round"/>

        <!-- Large luminal domain, schematized -->
        <path d="M652 390
                 C621 413 631 438 658 445
                 C689 461 728 440 722 409
                 C717 386 695 383 684 379"
              fill="#a7d3bc"
              stroke="#598e77"
              stroke-width="3"/>

        <text x="683" y="139"
              text-anchor="middle"
              font-size="17"
              font-weight="bold"
              fill="#477f67">
          TGN46
        </text>

        <text x="683" y="156"
              text-anchor="middle"
              font-size="11"
              fill="#64748b">
          TRANS-GOLGI NETWORK
        </text>
      </g>
    `;

    return `
      <g class="golgi-membrane-features">

        <text x="450" y="102"
              text-anchor="middle"
              font-size="18"
              font-weight="bold"
              fill="#64748b">
          GOLGI MEMBRANE · PROTEIN SPECIALIZATION
        </text>

        ${gm130}
        ${tmem165}
        ${tgn46}

      </g>
    `;
  }

  
  function golgiOverviewSvg() {

    // Individual Golgi cisternae.
    // Each region has its own clickable target.
    const cisternae = [
      {
        id: "cis_golgi",
        label: "CIS-GOLGI",
        color: "#6ea4ca",
        y: 182,
        width: 160
      },
      {
        id: "medial_golgi",
        label: "MEDIAL-GOLGI",
        color: "#7db9a9",
        y: 259,
        width: 195
      },
      {
        id: "trans_golgi",
        label: "TRANS-GOLGI",
        color: "#d4a276",
        y: 336,
        width: 170
      }
    ];

    const stackMarkup = cisternae.map((part) => {
      const left = 450 - part.width;
      const right = 450 + part.width;

      return `
        <g class="diagram-action"
           data-target="${part.id}"
           role="button"
           tabindex="0"
           aria-label="Explore ${part.label}"
           style="cursor:pointer">

          <rect x="${left - 22}"
                y="${part.y - 24}"
                width="${part.width * 2 + 44}"
                height="69"
                rx="14"
                fill="transparent"/>

          <path
            d="M${left} ${part.y}
               Q450 ${part.y - 42}
               ${right} ${part.y}"
            fill="none"
            stroke="${part.color}"
            stroke-width="15"
            stroke-linecap="round"/>

          <path
            d="M${left + 12} ${part.y + 25}
               Q450 ${part.y - 17}
               ${right - 12} ${part.y + 25}"
            fill="none"
            stroke="${part.color}"
            stroke-width="15"
            stroke-linecap="round"
            opacity="0.8"/>

          <text
            x="450"
            y="${part.y + 52}"
            text-anchor="middle"
            font-size="13"
            font-weight="bold"
            fill="#475569">
            ${part.label}
          </text>
        </g>
      `;
    }).join("");

    return `
      <g class="golgi-overview">

        <text x="450" y="105"
              text-anchor="middle"
              font-size="20"
              font-weight="bold"
              fill="#64748b">
          GOLGI APPARATUS
        </text>

        <text x="450" y="130"
              text-anchor="middle"
              font-size="13"
              fill="#64748b">
          CARGO MODIFICATION · SORTING · TRANSPORT
        </text>

        <!-- Incoming ER-derived carriers -->
        <g class="diagram-action"
           data-target="golgi_transport_carriers"
           role="button"
           tabindex="0"
           aria-label="Explore incoming Golgi carriers"
           style="cursor:pointer">

          <circle cx="143" cy="194" r="19"
                  fill="#92bbdc"
                  stroke="#568ab5"
                  stroke-width="3"/>

          <circle cx="104" cy="225" r="12"
                  fill="#92bbdc"
                  stroke="#568ab5"
                  stroke-width="2"/>

          <circle cx="159" cy="239" r="10"
                  fill="#92bbdc"
                  stroke="#568ab5"
                  stroke-width="2"/>

          <path d="M174 211 L258 195"
                fill="none"
                stroke="#568ab5"
                stroke-width="3"
                stroke-dasharray="7 5"/>

          <path d="M247 187 L261 195 L250 204"
                fill="none"
                stroke="#568ab5"
                stroke-width="3"/>

          <text x="143" y="156"
                text-anchor="middle"
                font-size="13"
                font-weight="bold"
                fill="#568ab5">
            ER CARGO
          </text>

          <rect x="75" y="144"
                width="190" height="122"
                fill="transparent"/>
        </g>

        <!-- Cis, medial and trans cisternae -->
        ${stackMarkup}

        <!-- Trans-Golgi network -->
        <g class="diagram-action"
           data-target="trans_golgi_network"
           role="button"
           tabindex="0"
           aria-label="Explore trans-Golgi network"
           style="cursor:pointer">

          <rect x="270" y="408"
                width="360" height="112"
                rx="18"
                fill="transparent"/>

          <path d="M333 438
                   C377 425 420 444 466 440
                   C511 435 554 446 575 457"
                fill="none"
                stroke="#c78376"
                stroke-width="11"
                stroke-linecap="round"/>

          <path d="M440 440
                   C418 461 396 467 369 482"
                fill="none"
                stroke="#c78376"
                stroke-width="8"
                stroke-linecap="round"/>

          <path d="M495 440
                   C519 468 551 472 589 481"
                fill="none"
                stroke="#c78376"
                stroke-width="8"
                stroke-linecap="round"/>

          <circle cx="361" cy="488" r="9"
                  fill="#dfa28a"/>

          <circle cx="599" cy="483" r="9"
                  fill="#dfa28a"/>

          <text x="450" y="515"
                text-anchor="middle"
                font-size="15"
                font-weight="bold"
                fill="#986257">
            TRANS-GOLGI NETWORK
          </text>
        </g>

        <!-- Outgoing Golgi carriers -->
        <g class="diagram-action"
           data-target="golgi_transport_carriers"
           role="button"
           tabindex="0"
           aria-label="Explore outgoing Golgi carriers"
           style="cursor:pointer">

          <circle cx="747" cy="440" r="19"
                  fill="#dfab90"
                  stroke="#ad765c"
                  stroke-width="3"/>

          <circle cx="782" cy="477" r="12"
                  fill="#dfab90"
                  stroke="#ad765c"
                  stroke-width="2"/>

          <circle cx="717" cy="489" r="10"
                  fill="#dfab90"
                  stroke="#ad765c"
                  stroke-width="2"/>

          <path d="M624 456 L716 443"
                fill="none"
                stroke="#ad765c"
                stroke-width="3"
                stroke-dasharray="7 5"/>

          <path d="M704 435 L718 443 L707 453"
                fill="none"
                stroke="#ad765c"
                stroke-width="3"/>

          <text x="749" y="408"
                text-anchor="middle"
                font-size="13"
                font-weight="bold"
                fill="#ad765c">
            EXPORT
          </text>

          <rect x="638" y="396"
                width="174" height="113"
                fill="transparent"/>
        </g>
        
        <!-- Clickable Golgi membrane sample -->
        <g class="diagram-action"
           data-target="golgi_membrane"
           role="button"
           tabindex="0"
           aria-label="Explore the Golgi membrane"
           style="cursor:pointer">

          <rect x="76" y="351"
                width="177" height="153"
                rx="16"
                fill="#eef2f7"
                stroke="#9aabba"
                stroke-width="2"/>

          <!-- Phospholipid bilayer sample -->
          <g fill="#8aa3bb">
            <circle cx="98" cy="400" r="6"/>
            <circle cx="121" cy="400" r="6"/>
            <circle cx="144" cy="400" r="6"/>
            <circle cx="167" cy="400" r="6"/>
            <circle cx="190" cy="400" r="6"/>
            <circle cx="213" cy="400" r="6"/>

            <circle cx="98" cy="438" r="6"/>
            <circle cx="121" cy="438" r="6"/>
            <circle cx="144" cy="438" r="6"/>
            <circle cx="167" cy="438" r="6"/>
            <circle cx="190" cy="438" r="6"/>
            <circle cx="213" cy="438" r="6"/>
          </g>

          <g stroke="#9aabba"
             stroke-width="2">
            <path d="M98 407v24 M121 407v24 M144 407v24
                     M167 407v24 M190 407v24 M213 407v24"/>
          </g>

          <text x="164" y="374"
                text-anchor="middle"
                font-size="13"
                font-weight="bold"
                fill="#64748b">
            GOLGI MEMBRANE
          </text>

          <text x="164" y="481"
                text-anchor="middle"
                font-size="11"
                fill="#64748b">
            EXPLORE LIPIDS
          </text>

        </g>


        <text x="450" y="563"
              text-anchor="middle"
              font-size="12"
              fill="#64748b">
          SELECT A GOLGI REGION OR TRANSPORT CARRIER
        </text>

        <text x="450" y="584"
              text-anchor="middle"
              font-size="11"
              fill="#64748b">
          CARGO MATURATION INVOLVES CHANGING CISTERNAL IDENTITY
        </text>

      </g>
    `;
  }

  
  function smoothErLumenSvg() {

    // Free calcium ions dispersed within the ER lumen.
    const calciumPositions = [
      [155, 245], [255, 310], [350, 255],
      [565, 260], [670, 320], [745, 240],
      [185, 410], [285, 465], [390, 430],
      [530, 445], [630, 410], [735, 465]
    ];

    const calciumIons = calciumPositions.map(([x, y]) => `
      <circle cx="${x}" cy="${y}"
              r="8"
              fill="#76b9ec"
              stroke="#377eaf"
              stroke-width="1.5"/>
    `).join("");

    return `
      <g class="smooth-er-lumen">

        <text x="450" y="110"
              text-anchor="middle"
              font-size="19"
              font-weight="bold"
              fill="#64748b">
          SMOOTH ER · INTERNAL LUMEN
        </text>

        <text x="450" y="137"
              text-anchor="middle"
              font-size="13"
              fill="#64748b">
          AQUEOUS COMPARTMENT · CALCIUM RESERVOIR
        </text>

        <!-- Simplified membrane surrounding the lumen -->
        <rect x="65" y="175"
              width="770" height="350"
              rx="90"
              fill="#e0eff8"
              stroke="#c28f66"
              stroke-width="15"/>

        <rect x="76" y="186"
              width="748" height="328"
              rx="80"
              fill="none"
              stroke="#ebbb8c"
              stroke-width="5"/>

        ${calciumIons}

        <!-- Clickable calcium pool -->
        <g class="diagram-action"
           data-target="ser_lumen_calcium_pool"
           role="button"
           tabindex="0"
           aria-label="Explore the luminal calcium pool"
           style="cursor:pointer">

          <ellipse cx="260" cy="345"
                   rx="135" ry="70"
                   fill="#a9d5f2"
                   fill-opacity="0.5"
                   stroke="#629ec7"
                   stroke-width="2"/>

          <g fill="#76b9ec"
             stroke="#377eaf"
             stroke-width="2">
            <circle cx="215" cy="325" r="13"/>
            <circle cx="270" cy="309" r="13"/>
            <circle cx="309" cy="343" r="13"/>
            <circle cx="246" cy="365" r="13"/>
          </g>

          <text x="260" y="408"
                text-anchor="middle"
                font-size="15"
                font-weight="bold"
                fill="#397ba4">
            LUMINAL Ca²⁺ POOL
          </text>

          <rect x="128" y="270"
                width="267" height="147"
                fill="transparent"/>
        </g>

        <!-- Calreticulin protein -->
        <g class="diagram-action"
           data-target="ser_calcium_buffer"
           role="button"
           tabindex="0"
           aria-label="Explore calcium-binding luminal proteins"
           style="cursor:pointer">

          <path d="M503 293
                   C532 267 588 279 605 311
                   C620 338 601 377 565 382
                   C524 390 494 364 490 337
                   C486 320 488 306 503 293Z"
                fill="#e0b077"
                stroke="#b48045"
                stroke-width="3"/>

          <text x="552" y="337"
                text-anchor="middle"
                font-size="17"
                font-weight="bold"
                fill="#75491d">
            CALR
          </text>

          <g fill="#76b9ec"
             stroke="#377eaf"
             stroke-width="1.5">
            <circle cx="489" cy="285" r="9"/>
            <circle cx="624" cy="328" r="9"/>
            <circle cx="596" cy="397" r="9"/>
          </g>

          <text x="555" y="423"
                text-anchor="middle"
                font-size="15"
                font-weight="bold"
                fill="#93632f">
            CALCIUM BUFFERING
          </text>

          <rect x="475" y="258"
                width="166" height="172"
                fill="transparent"/>
        </g>

        <!-- Continuous ER lumen -->
        <g class="diagram-action"
           data-target="ser_lumen_continuity"
           role="button"
           tabindex="0"
           aria-label="Explore ER lumen continuity"
           style="cursor:pointer">

          <path d="M710 282
                   C760 264 804 284 808 322
                   C812 361 777 382 732 370"
                fill="none"
                stroke="#6d9f8d"
                stroke-width="10"
                stroke-linecap="round"/>

          <path d="M733 357l-12 12 17 8"
                fill="none"
                stroke="#6d9f8d"
                stroke-width="4"/>

          <text x="737" y="406"
                text-anchor="middle"
                font-size="13"
                font-weight="bold"
                fill="#4b8270">
            ER CONTINUITY
          </text>

          <rect x="680" y="260"
                width="148" height="160"
                fill="transparent"/>
        </g>

        <text x="450" y="561"
              text-anchor="middle"
              font-size="12"
              fill="#64748b">
          SELECT A LUMINAL STRUCTURE TO EXPLORE
        </text>

        <text x="450" y="582"
              text-anchor="middle"
              font-size="11"
              fill="#64748b">
          THE SER AND RER SHARE A CONTINUOUS INTERNAL SPACE
        </text>

      </g>
    `;
  }

  
  function serDetoxificationSvg() {
    return `
      <g class="ser-detoxification-visual">

        <text x="450" y="112"
              text-anchor="middle"
              font-size="19"
              font-weight="bold"
              fill="#64748b">
          SMOOTH ER · CYTOCHROME P450 METABOLISM
        </text>

        <text x="450" y="141"
              text-anchor="middle"
              font-size="13"
              fill="#64748b">
          ELECTRON TRANSFER · OXYGEN ACTIVATION · SUBSTRATE OXIDATION
        </text>

        <!-- ER membrane cross-section -->
        <rect x="60" y="290"
              width="780" height="58"
              rx="12"
              fill="#f2d8b5"
              fill-opacity="0.7"/>

        <path d="M60 297 H840 M60 341 H840"
              stroke="#b8946b"
              stroke-width="8"
              stroke-linecap="round"/>

        <text x="76" y="381"
              font-size="13"
              font-weight="bold"
              fill="#986c4b">
          ER MEMBRANE
        </text>

        <text x="76" y="185"
              font-size="13"
              font-weight="bold"
              fill="#64748b">
          CYTOSOL
        </text>

        <!-- CYP450 protein -->
        <g class="diagram-action"
           data-target="ser_cyp450_enzyme"
           role="button"
           tabindex="0"
           aria-label="Explore cytochrome P450"
           style="cursor:pointer">

          <rect x="315" y="205"
                width="140" height="164"
                rx="28"
                fill="#8d75b2"
                stroke="#67518d"
                stroke-width="3"/>

          <ellipse cx="385" cy="218"
                   rx="87" ry="58"
                   fill="#a994cb"
                   stroke="#67518d"
                   stroke-width="3"/>

          <!-- Heme center -->
          <circle cx="385" cy="213"
                  r="25"
                  fill="#d9a96a"
                  stroke="#926331"
                  stroke-width="3"/>

          <text x="385" y="219"
                text-anchor="middle"
                font-size="16"
                font-weight="bold"
                fill="#633b19">
            Fe
          </text>

          <text x="385" y="162"
                text-anchor="middle"
                font-size="17"
                font-weight="bold"
                fill="#67518d">
            CYP450
          </text>

          <rect x="298" y="153"
                width="177" height="221"
                fill="transparent"/>
        </g>

        <!-- P450 reductase -->
        <g class="diagram-action"
           data-target="ser_p450_reductase"
           role="button"
           tabindex="0"
           aria-label="Explore P450 reductase"
           style="cursor:pointer">

          <rect x="93" y="244"
                width="112" height="125"
                rx="22"
                fill="#5d9aa2"
                stroke="#34727d"
                stroke-width="3"/>

          <ellipse cx="149" cy="216"
                   rx="68" ry="50"
                   fill="#83bfc4"
                   stroke="#34727d"
                   stroke-width="3"/>

          <text x="149" y="212"
                text-anchor="middle"
                font-size="17"
                font-weight="bold"
                fill="#245d64">
            POR
          </text>

          <text x="149" y="230"
                text-anchor="middle"
                font-size="11"
                fill="#245d64">
            FAD / FMN
          </text>

          <text x="149" y="148"
                text-anchor="middle"
                font-size="16"
                font-weight="bold"
                fill="#34727d">
            P450 REDUCTASE
          </text>

          <rect x="77" y="156"
                width="148" height="219"
                fill="transparent"/>
        </g>

        <!-- Electron flow from POR to CYP -->
        <path d="M224 217 H291"
              stroke="#db9851"
              stroke-width="4"
              stroke-dasharray="7 5"/>

        <path d="M279 208 L293 217 L279 226"
              fill="none"
              stroke="#db9851"
              stroke-width="4"/>

        <text x="260" y="196"
              text-anchor="middle"
              font-size="12"
              font-weight="bold"
              fill="#9b6a37">
          e-
        </text>

        <!-- Substrate oxidation -->
        <g class="diagram-action"
           data-target="ser_cyp_reaction"
           role="button"
           tabindex="0"
           aria-label="Explore CYP450 oxidation reaction"
           style="cursor:pointer">

          <rect x="530" y="172"
                width="293" height="198"
                rx="24"
                fill="#d8ebd5"
                fill-opacity="0.85"
                stroke="#72a36e"
                stroke-width="2"/>

          <text x="676" y="205"
                text-anchor="middle"
                font-size="17"
                font-weight="bold"
                fill="#417644">
            OXIDATION REACTION
          </text>

          <text x="676" y="251"
                text-anchor="middle"
                font-size="20"
                font-weight="bold"
                fill="#417644">
            RH + O2
          </text>

          <path d="M623 269 H729"
                stroke="#417644"
                stroke-width="3"/>

          <path d="M718 261 L730 269 L718 277"
                fill="none"
                stroke="#417644"
                stroke-width="3"/>

          <text x="676" y="307"
                text-anchor="middle"
                font-size="22"
                font-weight="bold"
                fill="#417644">
            ROH
          </text>

          <text x="676" y="339"
                text-anchor="middle"
                font-size="12"
                fill="#417644">
            CYP-CATALYZED HYDROXYLATION
          </text>
        </g>

        <!-- NADPH supplies electrons through POR -->
        <text x="450" y="440"
              text-anchor="middle"
              font-size="17"
              font-weight="bold"
              fill="#64748b">
          NADPH → POR → CYP450
        </text>

        <text x="450" y="470"
              text-anchor="middle"
              font-size="14"
              fill="#64748b">
          ELECTRONS SUPPORT OXYGEN ACTIVATION
        </text>

        <!-- Illustrative example -->
        <text x="450" y="513"
              text-anchor="middle"
              font-size="15"
              font-weight="bold"
              fill="#64748b">
          EXAMPLE: BENZENE → PHENOL
        </text>

        <text x="450" y="540"
              text-anchor="middle"
              font-size="12"
              fill="#996b56">
          CYP METABOLISM CAN ALSO PRODUCE TOXIC INTERMEDIATES
        </text>

        <text x="450" y="586"
              text-anchor="middle"
              font-size="12"
              fill="#64748b">
          CLICK AN ENZYME OR REACTION TO EXPLORE
        </text>

      </g>
    `;
  }

  
  function serCalciumRegulationSvg() {

    const calciumIon = (x, y, r = 11) => `
      <g>
        <circle cx="${x}" cy="${y}" r="${r}"
                fill="#75b7eb"
                stroke="#377dad"
                stroke-width="2"/>
        <text x="${x}" y="${y + 4}"
              text-anchor="middle"
              font-size="${r > 10 ? 10 : 8}"
              font-weight="bold"
              fill="#ffffff">Ca</text>
      </g>
    `;

    const cytosolCalcium = [
      [145, 183], [340, 197], [555, 181], [750, 201]
    ].map(([x, y]) => calciumIon(x, y, 9)).join("");

    const lumenCalcium = [
      [116, 466], [181, 504], [261, 454],
      [344, 485], [419, 520], [492, 467],
      [585, 509], [652, 458], [738, 486],
      [804, 518]
    ].map(([x, y]) => calciumIon(x, y, 10)).join("");

    return `
      <g class="ser-calcium-regulation">

        <text x="450" y="105"
              text-anchor="middle"
              font-size="19"
              font-weight="bold"
              fill="#64748b">
          CALCIUM REGULATION IN THE SMOOTH ER
        </text>

        <!-- Cytosolic compartment -->
        <text x="70" y="155"
              font-size="15"
              font-weight="bold"
              fill="#64748b">
          CYTOSOL
        </text>

        ${cytosolCalcium}

        <!-- ER membrane bilayer -->
        <rect x="56" y="285"
              width="788" height="55"
              rx="10"
              fill="#f1d4ad"
              fill-opacity="0.65"/>

        <path d="M56 290h788"
              stroke="#bd976c"
              stroke-width="8"
              stroke-linecap="round"/>

        <path d="M56 335h788"
              stroke="#bd976c"
              stroke-width="8"
              stroke-linecap="round"/>

        <!-- ER lumen compartment -->
        <rect x="55" y="350"
              width="790" height="200"
              rx="26"
              fill="#dcedf8"
              fill-opacity="0.85"
              stroke="#b4cfdf"
              stroke-width="2"/>

        <text x="80" y="387"
              font-size="15"
              font-weight="bold"
              fill="#47728a">
          ER LUMEN
        </text>

        ${lumenCalcium}

        <!-- SERCA pump -->
        <g class="diagram-action"
           data-target="ser_serca_pump"
           role="button"
           tabindex="0"
           aria-label="Explore SERCA calcium pump"
           style="cursor:pointer">

          <rect x="158" y="258"
                width="121" height="116"
                rx="21"
                fill="#8c73b4"
                stroke="#674f91"
                stroke-width="3"/>

          <ellipse cx="218" cy="244"
                   rx="57" ry="35"
                   fill="#a995cb"
                   stroke="#674f91"
                   stroke-width="2"/>

          <text x="218" y="249"
                text-anchor="middle"
                font-size="18"
                font-weight="bold"
                fill="white">
            SERCA
          </text>

          <path d="M218 277v83"
                stroke="#ffffff"
                stroke-width="5"
                stroke-linecap="round"/>

          <path d="M204 344l14 17 14-17"
                fill="none"
                stroke="#ffffff"
                stroke-width="4"/>

          <text x="218" y="195"
                text-anchor="middle"
                font-size="14"
                font-weight="bold"
                fill="#674f91">
            ATP → ADP + Pi
          </text>

          <rect x="155" y="202"
                width="129" height="174"
                fill="transparent"/>
        </g>

        <!-- IP3 receptor -->
        <g class="diagram-action"
           data-target="ser_ip3_receptor"
           role="button"
           tabindex="0"
           aria-label="Explore IP3 calcium release channel"
           style="cursor:pointer">

          <rect x="389" y="260"
                width="124" height="110"
                rx="20"
                fill="#63a59b"
                stroke="#3a8177"
                stroke-width="3"/>

          <rect x="443" y="266"
                width="16" height="96"
                rx="8"
                fill="#dcedf8"/>

          <text x="451" y="245"
                text-anchor="middle"
                font-size="17"
                font-weight="bold"
                fill="#3a8177">
            IP3R
          </text>

          <!-- Direction of calcium release -->
          <path d="M451 265v-63"
                stroke="#3a8177"
                stroke-width="5"
                stroke-linecap="round"/>

          <path d="M438 217l13-17 13 17"
                fill="none"
                stroke="#3a8177"
                stroke-width="4"/>

          <text x="451" y="185"
                text-anchor="middle"
                font-size="13"
                font-weight="bold"
                fill="#3a8177">
            Ca RELEASE
          </text>

          <rect x="383" y="176"
                width="137" height="198"
                fill="transparent"/>
        </g>

        <!-- Calreticulin -->
        <g class="diagram-action"
           data-target="ser_calcium_buffer"
           role="button"
           tabindex="0"
           aria-label="Explore ER calcium buffering"
           style="cursor:pointer">

          <path d="M615 411
                   C644 385 686 398 692 429
                   C702 470 653 482 632 462
                   C605 447 597 427 615 411Z"
                fill="#e1aa67"
                stroke="#b88243"
                stroke-width="3"/>

          <text x="653" y="441"
                text-anchor="middle"
                font-size="14"
                font-weight="bold"
                fill="#634321">
            CALR
          </text>

          <text x="653" y="396"
                text-anchor="middle"
                font-size="13"
                font-weight="bold"
                fill="#90612f">
            CALCIUM BUFFERING
          </text>

          <rect x="590" y="380"
                width="129" height="101"
                fill="transparent"/>
        </g>

        <text x="450" y="581"
              text-anchor="middle"
              font-size="12"
              fill="#64748b">
          SELECT A PROTEIN OR CALCIUM-HANDLING PROCESS TO EXPLORE
        </text>

      </g>
    `;
  }

  
  function smoothErMembraneFeaturesSvg() {

    // Protein illustrations use the same coordinates
    // as the existing phospholipid bilayer.

    const reticulon = `
      <g class="diagram-action"
         data-target="ser_reticulon"
         role="button"
         tabindex="0"
         aria-label="Explore Reticulon-4"
         style="cursor:pointer">

        <rect x="145" y="236" width="175" height="158"
              rx="16" fill="transparent"/>

        <!-- Hairpin-shaped membrane insertion -->
        <path d="M191 246
                 C190 273 188 315 206 328
                 C225 340 237 313 237 286
                 L237 248"
              fill="none"
              stroke="#8874b4"
              stroke-width="17"
              stroke-linecap="round"/>

        <path d="M251 246
                 C250 277 248 318 268 329
                 C283 336 292 307 291 277
                 L291 248"
              fill="none"
              stroke="#a28bc6"
              stroke-width="12"
              stroke-linecap="round"/>

        <text x="236" y="189"
              text-anchor="middle"
              font-size="17"
              font-weight="bold"
              fill="#78629e">
          RETICULON-4
        </text>

        <text x="236" y="207"
              text-anchor="middle"
              font-size="12"
              fill="#64748b">
          MEMBRANE CURVATURE
        </text>
      </g>
    `;

    const atlastin = `
      <g class="diagram-action"
         data-target="ser_atlastin"
         role="button"
         tabindex="0"
         aria-label="Explore Atlastin GTPase"
         style="cursor:pointer">

        <rect x="353" y="191"
              width="192" height="208"
              rx="18" fill="transparent"/>

        <!-- Membrane anchors -->
        <path d="M420 255v77m60-77v77"
              stroke="#5489a3"
              stroke-width="15"
              stroke-linecap="round"/>

        <!-- Cytosolic GTPase domains -->
        <ellipse cx="420" cy="224" rx="30" ry="26"
                 fill="#74a8c1"
                 stroke="#416f87"
                 stroke-width="2"/>

        <ellipse cx="480" cy="224" rx="30" ry="26"
                 fill="#74a8c1"
                 stroke="#416f87"
                 stroke-width="2"/>

        <path d="M450 223h1"
              stroke="#416f87"
              stroke-width="5"/>

        <text x="450" y="171"
              text-anchor="middle"
              font-size="17"
              font-weight="bold"
              fill="#416f87">
          ATLASTIN
        </text>

        <text x="450" y="189"
              text-anchor="middle"
              font-size="12"
              fill="#64748b">
          GTP-DEPENDENT FUSION
        </text>
      </g>
    `;

    const vapb = `
      <g class="diagram-action"
         data-target="ser_vapb"
         role="button"
         tabindex="0"
         aria-label="Explore VAPB"
         style="cursor:pointer">

        <rect x="591" y="176"
              width="170" height="218"
              rx="16" fill="transparent"/>

        <!-- ER membrane anchor -->
        <path d="M674 248v84"
              stroke="#64a68a"
              stroke-width="17"
              stroke-linecap="round"/>

        <!-- Cytosolic domain -->
        <path d="M674 248v-20"
              stroke="#487f6a"
              stroke-width="7"/>

        <ellipse cx="674" cy="211"
                 rx="36" ry="25"
                 fill="#8ac5a8"
                 stroke="#487f6a"
                 stroke-width="2"/>

        <text x="674" y="155"
              text-anchor="middle"
              font-size="17"
              font-weight="bold"
              fill="#487f6a">
          VAPB
        </text>

        <text x="674" y="173"
              text-anchor="middle"
              font-size="12"
              fill="#64748b">
          MEMBRANE CONTACTS
        </text>
      </g>
    `;

    return `
      <g class="smooth-er-membrane-features">

        ${reticulon}
        ${atlastin}
        ${vapb}

      </g>
    `;
  }
  
  function serLipidSynthesisSvg() {

    const pathways = [
      {
        id: "ser_phospholipid_synthesis",
        title: "PHOSPHOLIPID SYNTHESIS",
        x: 165,
        color: "#668bb1",
        type: "phospholipid"
      },
      {
        id: "ser_tag_synthesis",
        title: "TRIACYLGLYCEROL SYNTHESIS",
        x: 450,
        color: "#be9956",
        type: "tag"
      },
      {
        id: "ser_cholesterol_synthesis",
        title: "CHOLESTEROL SYNTHESIS",
        x: 735,
        color: "#8c75af",
        type: "cholesterol"
      }
    ];

    const lipidDrawing = (type, x, color) => {

      if (type === "phospholipid") {
        return `
          <g transform="translate(${x} 270)">
            <circle cx="0" cy="-34" r="17"
                    fill="${color}"/>
            <path d="M-6 -15
                     C-20 10 -4 22 -15 50
                     M6 -15
                     C20 10 4 22 15 50"
                  stroke="${color}"
                  stroke-width="7"
                  fill="none"
                  stroke-linecap="round"/>
          </g>
        `;
      }

      if (type === "tag") {
        return `
          <g transform="translate(${x} 260)"
             stroke="${color}"
             stroke-width="6"
             stroke-linecap="round"
             fill="none">

            <path d="M-26 -36v76"/>

            <path d="M-26 -30
                     C10 -45 13 -5 42 -19"/>

            <path d="M-26 0
                     C10 -15 13 25 42 11"/>

            <path d="M-26 30
                     C10 15 13 55 42 41"/>
          </g>
        `;
      }

      return `
        <g transform="translate(${x} 281)"
           stroke="${color}"
           stroke-width="5"
           fill="none"
           stroke-linejoin="round">

          <polygon points="-54,-8 -24,-26 5,-9 5,25 -25,41 -54,23"/>
          <polygon points="5,-9 34,-26 61,-8 61,24 33,41 5,25"
                   transform="translate(-3 -1)"/>
          <polygon points="-24,-26 5,-44 34,-26 5,-9"/>
          <polygon points="33,41 61,24 79,45 58,66 33,55"
                   transform="translate(-6 -23)"/>
        </g>
      `;
    };

    const cards = pathways.map((p) => `
      <g class="diagram-action"
         data-target="${p.id}"
         role="button"
         tabindex="0"
         aria-label="Explore ${p.title}"
         style="cursor:pointer">

        <rect x="${p.x - 126}"
              y="195"
              width="252"
              height="230"
              rx="20"
              fill="${p.color}"
              fill-opacity="0.09"
              stroke="${p.color}"
              stroke-width="2"/>

        ${lipidDrawing(p.type, p.x, p.color)}

        <text x="${p.x}"
              y="366"
              text-anchor="middle"
              font-size="13"
              font-weight="bold"
              fill="#334155">
          ${p.title}
        </text>

        <text x="${p.x}"
              y="392"
              text-anchor="middle"
              font-size="12"
              fill="#64748b">
          ${p.type === "phospholipid"
            ? "PC · PE · MEMBRANE LIPIDS"
            : p.type === "tag"
              ? "DAG · DGAT · LIPID STORAGE"
              : "HMGCR · MEVALONATE"}
        </text>
      </g>
    `).join("");

    return `
      <g class="ser-lipid-synthesis">

        <text x="450" y="122"
              text-anchor="middle"
              font-size="19"
              font-weight="bold"
              fill="#64748b">
          SMOOTH ER · LIPID METABOLISM
        </text>

        <text x="450" y="152"
              text-anchor="middle"
              font-size="13"
              fill="#64748b">
          MEMBRANE LIPIDS · NEUTRAL LIPIDS · STEROLS
        </text>

        ${cards}

        <text x="450" y="460"
              text-anchor="middle"
              font-size="12"
              fill="#64748b">
          SELECT A LIPID PATHWAY TO EXPLORE
        </text>

        <text x="450" y="486"
              text-anchor="middle"
              font-size="11"
              fill="#64748b">
          SCHEMATIC STRUCTURES · EXACT MOLECULES SHOWN BELOW
        </text>

      </g>
    `;
  }


  function smoothErOverviewSvg() {
  return `
    <g class="smooth-er-overview">

      <text x="450" y="108"
            text-anchor="middle"
            font-size="19"
            font-weight="bold"
            fill="#64748b">
        SMOOTH ENDOPLASMIC RETICULUM
      </text>

      <text x="450" y="132"
            text-anchor="middle"
            font-size="13"
            fill="#64748b">
        LIPID SYNTHESIS · CALCIUM REGULATION · DETOXIFICATION
      </text>

      <text x="450" y="154"
            text-anchor="middle"
            font-size="11"
            fill="#64748b">
        Functions vary by cell type: hepatocytes emphasize detoxification,
      </text>

      <text x="450" y="171"
            text-anchor="middle"
            font-size="11"
            fill="#64748b">
        muscle uses the specialized sarcoplasmic reticulum for calcium handling.
      </text>

      <!-- Central tubular SER network -->
      <g class="diagram-action"
         data-target="smooth_er_membrane"
         role="button"
         tabindex="0"
         aria-label="Explore the smooth ER membrane"
         style="cursor:pointer">

        <path d="M170 285
                 C220 230 290 230 345 280
                 S455 330 505 280
                 S620 225 690 270
                 S760 335 725 382
                 S615 435 545 395
                 S430 340 360 390
                 S235 445 185 390
                 S115 325 170 285Z"
              fill="none"
              stroke="#d1a072"
              stroke-width="24"
              stroke-linecap="round"
              stroke-linejoin="round"/>

        <path d="M170 285
                 C220 230 290 230 345 280
                 S455 330 505 280
                 S620 225 690 270
                 S760 335 725 382
                 S615 435 545 395
                 S430 340 360 390
                 S235 445 185 390
                 S115 325 170 285Z"
              fill="none"
              stroke="#efc294"
              stroke-width="8"
              stroke-linecap="round"
              stroke-linejoin="round"/>

        <path d="M260 282
                 C300 250 355 250 393 286"
              fill="none"
              stroke="#ffffff"
              stroke-opacity="0.45"
              stroke-width="4"
              stroke-linecap="round"/>

        <path d="M500 282
                 C545 247 610 248 652 283"
              fill="none"
              stroke="#ffffff"
              stroke-opacity="0.45"
              stroke-width="4"
              stroke-linecap="round"/>

        <path d="M272 388
                 C321 352 387 352 430 390"
              fill="none"
              stroke="#ffffff"
              stroke-opacity="0.45"
              stroke-width="4"
              stroke-linecap="round"/>

        <text x="173" y="443"
              font-size="13"
              font-weight="bold"
              fill="#9a6d44">
          SER MEMBRANE
        </text>
      </g>

      <!-- Lumen -->
      <g class="diagram-action"
         data-target="smooth_er_lumen"
         role="button"
         tabindex="0"
         aria-label="Explore the smooth ER lumen"
         style="cursor:pointer">

        <ellipse cx="450" cy="334"
                 rx="150" ry="70"
                 fill="#dcecf5"
                 fill-opacity="0.85"
                 stroke="#aac7d8"
                 stroke-width="2"/>

        <text x="450" y="330"
              text-anchor="middle"
              font-size="21"
              font-weight="bold"
              fill="#47728a">
          SER LUMEN
        </text>

        <text x="450" y="351"
              text-anchor="middle"
              font-size="12"
              fill="#47728a">
          INTERNAL ER SPACE
        </text>
      </g>

      <!-- Lipid synthesis -->
      <g class="diagram-action"
         data-target="lipid_synthesis"
         role="button"
         tabindex="0"
         aria-label="Explore lipid synthesis"
         style="cursor:pointer">

        <circle cx="210" cy="220" r="42"
                fill="#f1dd8a"
                stroke="#be9f36"
                stroke-width="3"/>

        <text x="210" y="215"
              text-anchor="middle"
              font-size="14"
              font-weight="bold"
              fill="#6f5a12">
          LIPID
        </text>

        <text x="210" y="233"
              text-anchor="middle"
              font-size="14"
              font-weight="bold"
              fill="#6f5a12">
          SYNTHESIS
        </text>
      </g>

      <!-- Calcium regulation -->
      <g class="diagram-action"
         data-target="calcium_store"
         role="button"
         tabindex="0"
         aria-label="Explore calcium regulation"
         style="cursor:pointer">

        <circle cx="694" cy="215" r="42"
                fill="#b9dbf5"
                stroke="#5a94bd"
                stroke-width="3"/>

        <text x="694" y="221"
              text-anchor="middle"
              font-size="22"
              font-weight="bold"
              fill="#2f6990">
          Ca²⁺
        </text>
      </g>

      <!-- Detoxification -->
      <g class="diagram-action"
         data-target="detoxification"
         role="button"
         tabindex="0"
         aria-label="Explore detoxification"
         style="cursor:pointer">

        <circle cx="698" cy="450" r="42"
                fill="#bfe4cc"
                stroke="#5f9b74"
                stroke-width="3"/>

        <text x="698" y="444"
              text-anchor="middle"
              font-size="13"
              font-weight="bold"
              fill="#2e6743">
          DETOX
        </text>

        <text x="698" y="462"
              text-anchor="middle"
              font-size="13"
              font-weight="bold"
              fill="#2e6743">
          CYP
        </text>
      </g>

      <text x="450" y="565"
            text-anchor="middle"
            font-size="12"
            fill="#64748b">
        SELECT A STRUCTURE TO EXPLORE
      </text>

      <text x="450" y="585"
            text-anchor="middle"
            font-size="11"
            fill="#64748b">
        THE DEPICTED SMOOTH ER REGION LACKS BOUND RIBOSOMES
      </text>

    </g>
  `;
}

  function copiiExitSiteSvg() {
    const features = [
      {
        id: "copii_sar1",
        name: "Sar1",
        note: "GTPase initiation",
        x: 140,
        y: 220,
        color: "#668ab5"
      },
      {
        id: "copii_inner_coat",
        name: "Sec23 / Sec24",
        note: "Inner coat",
        x: 340,
        y: 220,
        color: "#9571b0"
      },
      {
        id: "copii_outer_coat",
        name: "Sec13 / Sec31",
        note: "Outer coat",
        x: 540,
        y: 220,
        color: "#b88755"
      },
      {
        id: "copii_cargo",
        name: "Cargo sorting",
        note: "Protein selection",
        x: 740,
        y: 220,
        color: "#5b998b"
      }
    ];

    const cards = features.map((f) => `
      <g class="diagram-action"
         data-target="${f.id}"
         role="button"
         tabindex="0"
         aria-label="Explore ${f.name}"
         style="cursor:pointer">

        <rect
          x="${f.x - 89}"
          y="${f.y - 57}"
          width="178"
          height="109"
          rx="16"
          fill="${f.color}"
          fill-opacity="0.13"
          stroke="${f.color}"
          stroke-width="2"
        />

        <circle cx="${f.x}" cy="${f.y - 20}"
                r="18" fill="${f.color}"/>

        <text x="${f.x}" y="${f.y - 15}"
              text-anchor="middle"
              font-size="12"
              font-weight="bold"
              fill="white">+</text>

        <text x="${f.x}" y="${f.y + 13}"
              text-anchor="middle"
              font-size="14"
              font-weight="bold"
              fill="#334155">
          ${f.name}
        </text>

        <text x="${f.x}" y="${f.y + 34}"
              text-anchor="middle"
              font-size="11"
              fill="#64748b">
          ${f.note}
        </text>
      </g>
    `).join("");

    return `
      <g class="copii-exit-site">

        <text x="450" y="112"
              text-anchor="middle"
              font-size="19"
              font-weight="bold"
              fill="#64748b">
          ER EXIT SITE · COPII MACHINERY
        </text>

        ${cards}

        <!-- ER membrane, budding toward cytosol -->
        <path
          d="M105 420
             H286
             C335 420 335 342 450 342
             C565 342 565 420 614 420
             H795"
          fill="none"
          stroke="#b88664"
          stroke-width="18"
          stroke-linecap="round"
        />

        <path
          d="M105 420
             H286
             C335 420 335 342 450 342
             C565 342 565 420 614 420
             H795"
          fill="none"
          stroke="#e7b98d"
          stroke-width="6"
          stroke-linecap="round"
        />

        <!-- Cargo within the forming bud -->
        <g fill="#5b998b">
          <circle cx="419" cy="378" r="8"/>
          <circle cx="451" cy="370" r="8"/>
          <circle cx="481" cy="382" r="8"/>
        </g>

        <!-- Stylized cytosolic COPII coat -->
        <path
          d="M342 350
             Q450 281 558 350"
          fill="none"
          stroke="#9571b0"
          stroke-width="9"
          stroke-linecap="round"
        />

        <path
          d="M329 331
             Q450 250 571 331"
          fill="none"
          stroke="#b88755"
          stroke-width="8"
          stroke-dasharray="15 7"
          stroke-linecap="round"
        />

        <text x="450" y="317"
              text-anchor="middle"
              font-size="12"
              font-weight="bold"
              fill="#64748b">
          COAT ASSEMBLY
        </text>

        <!-- Clickable final transport carrier -->
        <g class="diagram-action"
           data-target="copii_carrier"
           role="button"
           tabindex="0"
           aria-label="Explore the COPII transport carrier"
           style="cursor:pointer">

          <circle cx="450" cy="505"
                  r="40"
                  fill="#d9edf5"
                  stroke="#b88755"
                  stroke-width="7"
                  stroke-dasharray="8 4"/>

          <circle cx="440" cy="500"
                  r="6" fill="#5b998b"/>
          <circle cx="459" cy="512"
                  r="7" fill="#5b998b"/>

          <text x="540" y="506"
                font-size="14"
                font-weight="bold"
                fill="#64748b">
            TRANSPORT CARRIER
          </text>

          <text x="540" y="526"
                font-size="11"
                fill="#64748b">
            Toward ERGIC
          </text>

          <rect x="405" y="462"
                width="330" height="90"
                fill="transparent"/>
        </g>

        <text x="450" y="592"
              text-anchor="middle"
              font-size="12"
              fill="#64748b">
          SELECT A COPII COMPONENT TO EXPLORE
        </text>
      </g>
    `;
  }


function erGlycosylationSvg() {

    const steps = [
      {
        id: "er_glycan_assembly",
        x: 175,
        title: "GLYCAN ASSEMBLY",
        note: "Dolichol-linked donor",
        color: "#628aaa"
      },
      {
        id: "er_glycan_transfer",
        x: 450,
        title: "OST TRANSFER",
        note: "Glycan attaches to Asn",
        color: "#9571b5"
      },
      {
        id: "er_glycan_trimming",
        x: 725,
        title: "GLYCAN TRIMMING",
        note: "Glucose removal",
        color: "#5c987e"
      }
    ];

    const cards = steps.map((step, index) => `
      <g class="diagram-action"
         data-target="${step.id}"
         role="button"
         tabindex="0"
         aria-label="Explore ${step.title}">

        <rect x="${step.x - 113}" y="211"
              width="226" height="154"
              rx="18" fill="${step.color}"
              fill-opacity="0.13"
              stroke="${step.color}"
              stroke-width="2"/>

        <circle cx="${step.x}" cy="253" r="25"
                fill="${step.color}"/>

        <text x="${step.x}" y="261"
              text-anchor="middle"
              font-size="21"
              font-weight="bold"
              fill="white">${index + 1}</text>

        <text x="${step.x}" y="306"
              text-anchor="middle"
              font-size="15"
              font-weight="bold"
              fill="${step.color}">
          ${step.title}
        </text>

        <text x="${step.x}" y="332"
              text-anchor="middle"
              font-size="12"
              fill="#64748b">
          ${step.note}
        </text>
      </g>

      ${index < steps.length - 1
        ? `<path d="M${step.x + 118} 282h39"
                 fill="none"
                 stroke="#94a3b8"
                 stroke-width="3"/>
           <path d="M${step.x + 148} 274l10 8-10 8"
                 fill="none"
                 stroke="#94a3b8"
                 stroke-width="3"/>`
        : ""}
    `).join("");

    return `
      <g class="er-glycosylation-visual">

        <text x="450" y="120"
              text-anchor="middle"
              class="ribosome-view-label">
          N-LINKED GLYCOSYLATION
        </text>

        <text x="450" y="157"
              text-anchor="middle"
              font-size="17"
              font-weight="bold"
              fill="#64748b">
          Glc3Man9GlcNAc2
        </text>

        <text x="450" y="181"
              text-anchor="middle"
              font-size="13"
              fill="#64748b">
          3 GLUCOSE · 9 MANNOSE · 2 N-ACETYLGLUCOSAMINE
        </text>

        ${cards}

        <text x="450" y="417"
              text-anchor="middle"
              class="diagram-note">
          SELECT A STAGE TO EXPLORE THE BIOCHEMISTRY
        </text>

      </g>
    `;
  }
  function roughErLumenSvg() {
    const features = [
      {
        id: "protein_folding",
        title: "PROTEIN FOLDING",
        subtitle: "BiP · ATP-dependent chaperone",
        x: 160,
        y: 218,
        color: "#8873b1",
        symbol: "F"
      },
      {
        id: "er_disulfide",
        title: "DISULFIDE BONDS",
        subtitle: "PDI · Cysteine · S-S",
        x: 450,
        y: 218,
        color: "#b98658",
        symbol: "S-S"
      },
      {
        id: "er_calnexin_cycle",
        title: "GLYCOPROTEIN FOLDING",
        subtitle: "Calnexin · Calreticulin",
        x: 740,
        y: 218,
        color: "#63958a",
        symbol: "G"
      },
      {
        id: "er_quality_control",
        title: "QUALITY CONTROL",
        subtitle: "Folding check · ERAD",
        x: 305,
        y: 363,
        color: "#ba7382",
        symbol: "QC"
      },
      {
        id: "er_lumen_calcium",
        title: "CALCIUM STORAGE",
        subtitle: "Ca²⁺ · Calreticulin",
        x: 595,
        y: 363,
        color: "#638cb1",
        symbol: "Ca"
      },
      
      {
        id: "er_n_glycosylation",
        title: "N-LINKED GLYCOSYLATION",
        subtitle: "OST · Glycans · Asparagine",
        x: 450,
        y: 510,
        color: "#9271ae",
        symbol: "N"
      }

    ];

    const markup = features.map((feature) => `
      <g class="diagram-action"
         data-target="${feature.id}"
         role="button"
         tabindex="0"
         aria-label="Explore ${feature.title}"
         style="cursor:pointer">

        <rect
          x="${feature.x - 127}"
          y="${feature.y - 55}"
          width="254"
          height="116"
          rx="18"
          fill="#ffffff"
          fill-opacity="0.94"
          stroke="${feature.color}"
          stroke-width="2"
        />

        <circle
          cx="${feature.x}"
          cy="${feature.y - 18}"
          r="21"
          fill="${feature.color}"
        />

        <text
          x="${feature.x}"
          y="${feature.y - 12}"
          text-anchor="middle"
          font-size="13"
          font-weight="bold"
          fill="#ffffff">
          ${feature.symbol}
        </text>

        <text
          x="${feature.x}"
          y="${feature.y + 17}"
          text-anchor="middle"
          font-size="13"
          font-weight="bold"
          fill="#334155">
          ${feature.title}
        </text>

        <text
          x="${feature.x}"
          y="${feature.y + 39}"
          text-anchor="middle"
          font-size="11"
          fill="#64748b">
          ${feature.subtitle}
        </text>
      </g>
    `).join("");

    return `
      <g class="rough-er-lumen-visual">

        <rect
          x="18" y="130"
          width="864" height="310"
          rx="50"
          fill="#e8f1f7"
          stroke="#b2cddd"
          stroke-width="3"
        />

        <text
          x="450" y="152"
          text-anchor="middle"
          font-size="15"
          font-weight="bold"
          fill="#4b7390">
          ER LUMEN · PROTEIN MATURATION ENVIRONMENT
        </text>

        ${markup}

        <text
          x="450" y="430"
          text-anchor="middle"
          font-size="12"
          fill="#64748b">
          SELECT A PROCESS TO EXPLORE ITS MOLECULAR MACHINERY
        </text>

      </g>
    `;
  }

  
  function roughErOverviewSvg() {

    const ribosomePositions = [
      [180, 178], [270, 171], [360, 176],
      [450, 171], [540, 178], [625, 188]
    ];

    const ribosomes = ribosomePositions.map(([x, y]) => `
      <g transform="translate(${x} ${y})">
        <ellipse cx="0" cy="-10" rx="20" ry="15"
                 fill="#9472af" stroke="#684e86"
                 stroke-width="2"/>
        <ellipse cx="0" cy="8" rx="15" ry="10"
                 fill="#c5a3da" stroke="#684e86"
                 stroke-width="2"/>
      </g>
    `).join("");

    const upperMembrane = `
      M110 220
      C200 200 285 218 370 212
      S540 199 635 215
      S740 235 770 220
    `;

    const lowerMembrane = `
      M110 385
      C200 365 285 383 370 377
      S540 364 635 380
      S740 400 770 385
    `;

    return `
      <g class="rough-er-overview">

        <text x="450" y="115"
              text-anchor="middle"
              font-size="16"
              font-weight="bold"
              fill="#64748b">
          ROUGH ENDOPLASMIC RETICULUM
        </text>

        <!-- ER lumen: enclosed between two membrane sheets -->
        <g class="diagram-action"
           data-target="rough_er_lumen"
           role="button"
           tabindex="0"
           aria-label="Explore the rough ER lumen">

          <path
            d="${upperMembrane}
               L770 385
               C735 399 680 382 635 380
               S455 366 370 377
               S200 365 110 385 Z"
            fill="#daeaf2"
            stroke="none"
          />

          <text x="450" y="306"
                text-anchor="middle"
                font-size="24"
                font-weight="bold"
                fill="#47728a">
            ER LUMEN
          </text>

          <text x="450" y="330"
                text-anchor="middle"
                font-size="13"
                fill="#47728a">
            PROTEIN FOLDING · MODIFICATION
          </text>

          <rect x="160" y="245"
                width="565" height="115"
                rx="22"
                fill="transparent"/>
        </g>

        <!-- ER membranes -->
        <g class="diagram-action"
           data-target="rough_er_membrane"
           role="button"
           tabindex="0"
           aria-label="Explore the rough ER membrane">

          <path d="${upperMembrane}"
                fill="none"
                stroke="#c78f64"
                stroke-width="19"
                stroke-linecap="round"/>

          <path d="${lowerMembrane}"
                fill="none"
                stroke="#c78f64"
                stroke-width="19"
                stroke-linecap="round"/>

          <path d="${upperMembrane}"
                fill="none"
                stroke="#e9bb8e"
                stroke-width="6"
                stroke-linecap="round"/>

          <path d="${lowerMembrane}"
                fill="none"
                stroke="#e9bb8e"
                stroke-width="6"
                stroke-linecap="round"/>

          <text x="205" y="410"
                font-size="13"
                font-weight="bold"
                fill="#986744">
            ER MEMBRANE
          </text>
        </g>

        <!-- ER-bound ribosomes -->
        <g class="diagram-action"
           data-target="bound_ribosomes"
           role="button"
           tabindex="0"
           aria-label="Explore ER-bound ribosomes">

          ${ribosomes}

          <text x="338" y="144"
                text-anchor="middle"
                font-size="16"
                font-weight="bold"
                fill="#8863a5">
            ER-BOUND RIBOSOMES
          </text>

          <rect x="150" y="155"
                width="510" height="55"
                fill="transparent"/>
        </g>

        <!-- COPII exit-site region -->
        <g class="diagram-action"
           data-target="rough_er_exit_sites"
           role="button"
           tabindex="0"
           aria-label="Explore ER exit sites">

          <path
            d="M685 235 C728 225 758 249 756 285"
            fill="none"
            stroke="#648fa3"
            stroke-width="13"
            stroke-linecap="round"/>

          <circle cx="752" cy="279" r="32"
                  fill="#c4dce8"
                  stroke="#648fa3"
                  stroke-width="5"/>

          <circle cx="741" cy="272" r="5"
                  fill="#648fa3"/>

          <circle cx="761" cy="283" r="5"
                  fill="#648fa3"/>

          <text x="748" y="345"
                text-anchor="middle"
                font-size="15"
                font-weight="bold"
                fill="#47728a">
            COPII
          </text>

          <text x="748" y="364"
                text-anchor="middle"
                font-size="12"
                fill="#47728a">
            EXIT SITE
          </text>

          <rect x="708" y="242"
                width="78" height="127"
                fill="transparent"/>
        </g>

        <text x="450" y="440"
              text-anchor="middle"
              font-size="13"
              fill="#64748b">
          SELECT A STRUCTURE TO EXPLORE
        </text>

      </g>
    `;
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
      <text class="diagram-note" x="450" y="395">
        ${molecule.id.startsWith("protein_")
          ? "PROTEIN SCHEMATIC · ATOMIC STRUCTURE NOT YET LOADED"
          : "2D STRUCTURE GENERATED FROM ITS SMILES WITH RDKIT"}
      </text>
      ${context}</svg>`;
  }

  function genericScene(targetId) {
    const target = data[targetId];
    const childIds = target.children || [];
    const moleculeIds = (target.molecules || []).filter((id) => moleculeCards.has(id));
    if (target.visual === "molecule" && moleculeCards.has(targetId)) return moleculeScene(targetId);
    if (target.visual === "molecule" && moleculeIds.length) return moleculeScene(moleculeIds[0]);

   
    const embeddedPlasmaFeatures = targetId === "plasma_membrane";
    const embeddedCytosolFeatures = target.visual === "cytosol";
    const embeddedRibosomeFeatures = target.visual === "cytosolic_ribosome";
    
    const moleculeRowY = childIds.length ? 560 : 457;
    const moleculeMarkup = target.visual !== "membrane" && target.visual !== "nachr_pentamer" && !embeddedCytosolFeatures && !embeddedRibosomeFeatures
      ? moleculeIds.map((id, index) => moleculeActionSvg(id, index, moleculeIds.length, moleculeRowY)).join("")
      : "";
    const showChildren = childIds.length > 0;
    const showMolecules = moleculeIds.length > 0;
    const pathwayView = ["respiration", "pathway", "gradient"].includes(target.visual);
    const customProteinView = ["aquaporin_tetramer", "nachr_pentamer", "glut1_transporter"].includes(target.visual);
    const secondaryMarkup = showChildren && showMolecules && !pathwayView && target.visual !== "membrane" && !embeddedCytosolFeatures && !embeddedRibosomeFeatures
      ? `<g class="secondary-label"><text x="450" y="519">MOLECULES IN THIS STRUCTURE</text></g>${moleculeMarkup}`
      : moleculeMarkup;
    return `<svg class="detail-svg" viewBox="0 0 900 620" role="group" aria-label="${escapeHtml(target.name)} composition">
      <text class="detail-title" x="56" y="55">${escapeHtml(target.name)}</text>
      <text class="detail-subtitle" x="58" y="80">${escapeHtml(target.kind)}</text>
      <g class="focus-art">${focusGraphic(target.visual || "protein_complex", target, targetId)}</g>
      ${target.visual === "membrane" && !embeddedPlasmaFeatures ? `<g class="secondary-label"><text x="450" y="449">SELECT A LIPID TO VIEW ITS MOLECULAR STRUCTURE</text></g>` : ""}
      ${embeddedPlasmaFeatures ? `<g class="secondary-label"><text x="450" y="482">SELECT A NAMED LIPID OR EMBEDDED FEATURE TO ZOOM IN</text></g>` : ""}
     
      ${embeddedRibosomeFeatures ? `<g class="secondary-label"><text x="450" y="565">SELECT A SUBUNIT TO EXPLORE ITS INTERNAL RNA AND PROTEINS</text></g>` : ""}

      
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