import base64
from functools import lru_cache
from io import BytesIO

from rdkit import Chem
from rdkit.Chem import Draw, rdMolDescriptors


EXPLORATION_DATA = {
    "cell_overview": {
        "kind": "CELL OVERVIEW",
        "name": "A eukaryotic cell",
        "summary": "A living cell is an organized system of membranes, compartments, molecular machines, and fluid space.",
        "function": "Select any labeled structure to inspect its role. Choose the mitochondrion to explore its compartments and inner-membrane chemistry.",
        "components": "13 selectable structures",
        "molecules": [],
    },
    "nucleus": {
        "kind": "ORGANELLE",
        "name": "Nucleus",
        "summary": "The nucleus stores most of the cell's DNA inside a double-membrane envelope.",
        "function": "DNA is transcribed into RNA, which carries instructions used to make proteins.",
        "components": "Nuclear envelope · chromatin · nucleolus · pores",
        "molecules": [],
    },
    "mitochondrion": {
        "kind": "ORGANELLE",
        "name": "Mitochondrion",
        "summary": "A membrane-bound organelle that converts energy from fuel molecules into a proton gradient and ATP.",
        "function": "Explore its outer membrane, intermembrane space, folded inner membrane, matrix, DNA, and respiratory machinery.",
        "components": "Outer membrane · inner membrane · cristae · matrix · mitochondrial DNA · ribosomes",
        "molecules": ["oxygen", "adp", "atp"],
    },
    "ribosomes": {
        "kind": "MOLECULAR MACHINE",
        "name": "Ribosomes",
        "summary": "Eukaryotic 80S ribosomes translate mRNA into protein using a 40S small subunit and a 60S large subunit.",
        "function": "See mRNA codons read 5′ to 3′, tRNAs moving through the E, P, and A sites, and the growing peptide chain. Select a subunit, rRNA, ribosomal proteins, mRNA, or tRNA to explore it.",
        "components": "40S small subunit · 60S large subunit · rRNA · ribosomal proteins · mRNA · tRNA",
        "molecules": [],
    },
    "rough_er": {
        "kind": "ORGANELLE",
        "name": "Rough endoplasmic reticulum",
        "summary": "A folded membrane network covered with ribosomes.",
        "function": "New proteins enter the ER, where they begin folding and processing before transport.",
        "components": "Membrane · ribosomes · newly made proteins",
        "molecules": ["phosphatidylcholine", "phosphatidylethanolamine"],
    },
    "smooth_er": {
        "kind": "ORGANELLE",
        "name": "Smooth endoplasmic reticulum",
        "summary": "A membrane network without attached ribosomes.",
        "function": "Its roles include lipid synthesis, detoxification, and calcium storage; the balance varies by cell type.",
        "components": "Membrane · lipid-synthesis enzymes · calcium stores",
        "molecules": ["phosphatidylcholine", "cholesterol"],
    },
    "golgi": {
        "kind": "ORGANELLE",
        "name": "Golgi apparatus",
        "summary": "A stack of membrane-bound compartments that modifies and sorts cell products.",
        "function": "Proteins and lipids arrive in vesicles, are processed, and leave in packages for specific destinations.",
        "components": "Cisternae · processing enzymes · transport vesicles",
        "molecules": ["phosphatidylcholine"],
    },
    "lysosome": {
        "kind": "ORGANELLE",
        "name": "Lysosome",
        "summary": "An acidic compartment containing enzymes that break down material.",
        "function": "Its enzymes recycle cellular components and digest material brought into the cell.",
        "components": "Lipid membrane · acid hydrolases · recycled building blocks",
        "molecules": ["phosphatidylcholine"],
    },
    "peroxisome": {
        "kind": "ORGANELLE",
        "name": "Peroxisome",
        "summary": "A small compartment for oxidation reactions and peroxide management.",
        "function": "Peroxisomal enzymes help break down certain fatty acids and convert hydrogen peroxide to water and oxygen.",
        "components": "Oxidative enzymes · catalase · lipid membrane",
        "molecules": ["oxygen", "water", "phosphatidylcholine"],
    },
    "vesicles": {
        "kind": "TRANSPORT",
        "name": "Vesicles",
        "summary": "Small membrane-bound carriers that move materials between cell compartments.",
        "function": "Vesicles bud from one membrane and fuse with another, delivering proteins, lipids, or other cargo.",
        "components": "Phospholipid membrane · cargo · coat proteins",
        "molecules": ["phosphatidylcholine", "cholesterol"],
    },
    "cytoskeleton": {
        "kind": "CELL STRUCTURE",
        "name": "Cytoskeleton",
        "summary": "A dynamic network of protein filaments that gives the cell shape and supports movement.",
        "function": "Filaments help organize the interior and provide tracks for moving cargo.",
        "components": "Actin filaments · microtubules · intermediate filaments",
        "molecules": [],
    },
    "centrosome": {
        "kind": "CELL STRUCTURE",
        "name": "Centrosome",
        "summary": "A major microtubule-organizing center in many animal cells.",
        "function": "It helps organize microtubules and form the spindle during cell division.",
        "components": "Centrioles · pericentriolar material · microtubules",
        "molecules": [],
    },
    "plasma_membrane": {
        "kind": "CELL BOUNDARY",
        "name": "Plasma membrane",
        "summary": "A selective boundary separating the cell interior from its surroundings.",
        "function": "Its lipid bilayer and embedded proteins regulate transport, signaling, and cell recognition.",
        "components": "Asymmetric lipid bilayer · cholesterol · transport proteins · glycocalyx",
        "children": ["glycocalyx", "aquaporin_1", "nicotinic_acetylcholine_receptor", "glut1"],
        "molecules": ["phosphatidylcholine", "phosphatidylethanolamine", "sphingomyelin", "phosphatidylserine", "phosphatidylinositol", "pip2", "cholesterol"],
    },
    "cytoplasm": {
        "kind": "CELL COMPARTMENT",
        "name": "Cytoplasm",
        "summary": "A water-rich cell interior where dissolved compounds diffuse and glycolysis converts glucose into pyruvate while transferring energy to ATP and NADH.",
        "function": "Follow the ten cytosolic glycolysis reactions from glucose to pyruvate. Select a molecule in any reaction to zoom in on its structure.",
        "components": "Glycolysis · dissolved ions · cytosol",
        "molecules": ["water", "glucose", "glucose_6_phosphate", "fructose_6_phosphate", "fructose_1_6_bisphosphate", "dihydroxyacetone_phosphate", "glyceraldehyde_3_phosphate", "1_3_bisphosphoglycerate", "3_phosphoglycerate", "2_phosphoglycerate", "phosphoenolpyruvate", "pyruvate", "adp", "atp", "phosphate", "nad_plus", "nadh", "sodium", "potassium", "magnesium", "chloride"],
    },
    "outer_membrane": {
        "kind": "MITOCHONDRION",
        "name": "Outer membrane",
        "summary": "The outer boundary of the mitochondrion, separating it from the cytoplasm.",
        "function": "Transport proteins allow many small molecules to pass, while other proteins control import and signaling.",
        "components": "Phospholipids · porins · import machinery",
        "molecules": ["phosphatidylcholine", "phosphatidylethanolamine"],
    },
    "intermembrane_space": {
        "kind": "MITOCHONDRION",
        "name": "Intermembrane space",
        "summary": "The narrow region between the outer and inner mitochondrial membranes.",
        "function": "Respiratory complexes pump protons here, building the electrochemical gradient used to make ATP.",
        "components": "Protons · cytochrome c · soluble proteins",
        "molecules": ["oxygen", "water"],
    },
    "inner_membrane": {
        "kind": "MITOCHONDRION",
        "name": "Inner membrane",
        "summary": "A protein-rich membrane folded into cristae. Its lipid environment includes phosphatidylcholine, phosphatidylethanolamine, and cardiolipin.",
        "function": "The electron-transport chain pumps protons across this membrane. ATP synthase uses their return flow to make ATP.",
        "components": "Phospholipid bilayer · respiratory complexes · ATP synthase",
        "molecules": ["phosphatidylcholine", "phosphatidylethanolamine", "cardiolipin", "cholesterol"],
    },
    "cristae": {
        "kind": "MITOCHONDRION",
        "name": "Cristae",
        "summary": "Folds of the inner membrane that increase the surface available for respiratory proteins.",
        "function": "Cristae architecture helps organize the machinery for oxidative phosphorylation.",
        "components": "Inner-membrane folds · respiratory complexes · ATP synthase",
        "molecules": ["cardiolipin", "phosphatidylcholine"],
    },
    "matrix": {
        "kind": "MITOCHONDRION",
        "name": "Matrix",
        "summary": "The compartment enclosed by the inner mitochondrial membrane.",
        "function": "Pyruvate oxidation and the citric acid cycle produce electron carriers used by the respiratory chain.",
        "components": "Enzymes · metabolites · mitochondrial DNA · ribosomes",
        "molecules": ["pyruvate", "oxygen", "adp", "atp"],
    },
    "mitochondrial_dna": {
        "kind": "MITOCHONDRION",
        "name": "Mitochondrial DNA",
        "summary": "A small circular genome inside the mitochondrial matrix.",
        "function": "It encodes a subset of mitochondrial proteins and RNAs; most mitochondrial proteins are encoded in the nucleus.",
        "components": "DNA nucleotides · RNA transcripts · DNA-binding proteins",
        "molecules": [],
    },
    "mitochondrial_ribosomes": {
        "kind": "MITOCHONDRION",
        "name": "Mitochondrial ribosomes",
        "summary": "Ribosomes in the matrix that translate proteins encoded by mitochondrial DNA.",
        "function": "Their protein products are incorporated into mitochondrial membranes and energy-conversion machinery.",
        "components": "Ribosomal RNA · proteins · messenger RNA",
        "molecules": [],
    },
    "oxidative_phosphorylation": {
        "kind": "ENERGY CONVERSION",
        "name": "Oxidative phosphorylation",
        "summary": "Electrons from fuel-derived carriers flow through respiratory complexes to oxygen, while proton pumping stores usable energy.",
        "function": "The proton gradient drives ATP synthase as protons return to the matrix, coupling electron transfer to ATP production.",
        "components": "Complexes I-IV · CoQ · cytochrome c · oxygen · ATP synthase",
        "molecules": ["oxygen", "water", "adp", "phosphate", "atp"],
    },
    "complex_i": {
        "kind": "RESPIRATORY COMPLEX",
        "name": "Complex I",
        "summary": "NADH:ubiquinone oxidoreductase accepts electrons from NADH and transfers them to CoQ.",
        "function": "Electron transfer is coupled to proton pumping from the matrix into the intermembrane space.",
        "components": "Flavins · iron-sulfur centers · membrane proton pumps",
        "molecules": [],
    },
    "coq": {
        "kind": "ELECTRON CARRIER",
        "name": "Coenzyme Q",
        "summary": "A mobile, lipid-soluble electron carrier within the inner membrane.",
        "function": "CoQ collects electrons from Complex I and II and delivers them to Complex III.",
        "components": "Quinone head group · hydrophobic isoprenoid tail",
        "molecules": [],
    },
    "complex_iii": {
        "kind": "RESPIRATORY COMPLEX",
        "name": "Complex III",
        "summary": "Cytochrome bc1 transfers electrons from reduced CoQ to cytochrome c.",
        "function": "Its Q cycle contributes to proton movement across the inner membrane.",
        "components": "Cytochromes · iron-sulfur protein · membrane subunits",
        "molecules": [],
    },
    "cytochrome_c": {
        "kind": "ELECTRON CARRIER",
        "name": "Cytochrome c",
        "summary": "A small heme protein that carries electrons along the outer face of the inner membrane.",
        "function": "It transfers electrons from Complex III to Complex IV.",
        "components": "Protein · heme group · iron atom",
        "molecules": [],
    },
    "complex_iv": {
        "kind": "RESPIRATORY COMPLEX",
        "name": "Complex IV",
        "summary": "Cytochrome c oxidase receives electrons and uses them to reduce oxygen to water.",
        "function": "It also pumps protons into the intermembrane space, helping sustain the gradient.",
        "components": "Heme groups · copper centers · oxygen-binding site",
        "molecules": ["oxygen", "water"],
    },
    "atp_synthase": {
        "kind": "MOLECULAR MACHINE",
        "name": "ATP synthase",
        "summary": "A rotary enzyme embedded in the inner membrane.",
        "function": "Proton flow through its membrane motor drives conformational changes that join ADP and phosphate to form ATP.",
        "components": "F₀ membrane motor · F₁ catalytic head · proton channel",
        "molecules": ["adp", "phosphate", "atp"],
    },
    "oxygen": {
        "kind": "MOLECULE",
        "name": "Oxygen",
        "summary": "Molecular oxygen is the terminal electron acceptor in aerobic respiration.",
        "function": "At Complex IV, oxygen accepts electrons and protons to form water.",
        "components": "Two oxygen atoms joined by a double bond",
        "molecules": ["oxygen"],
    },
}


CELL_STRUCTURE_IDS = [
    "nucleus", "mitochondrion", "ribosomes", "rough_er", "smooth_er",
    "golgi", "lysosome", "peroxisome", "vesicles", "cytoskeleton",
    "centrosome", "plasma_membrane", "cytoplasm",
]


def _component(name, kind, description, visual, children=(), molecules=()):
    return {
        "kind": kind.upper(),
        "name": name,
        "summary": description,
        "function": description,
        "components": name,
        "visual": visual,
        "children": list(children),
        "molecules": list(molecules),
    }


ORGANCELLE_CONTENT = {
    "nucleus": {
        "visual": "nucleus",
        "children": ["nuclear_envelope", "chromatin", "nucleolus", "nuclear_pores"],
    },
    "mitochondrion": {
        "visual": "mitochondrion",
        "children": ["outer_membrane", "intermembrane_space", "inner_membrane", "cristae", "matrix", "mitochondrial_dna", "mitochondrial_ribosomes"],
    },
    "ribosomes": {
        "visual": "cytosolic_ribosome",
        "children": ["small_subunit", "large_subunit", "messenger_rna", "transfer_rna", "ribosomal_rna", "ribosomal_proteins","trna_e_site", "trna_p_site", "trna_a_site",],
    },
    
    "rough_er": {
        "visual": "network",
        "children": [
            "rough_er_membrane",
            "bound_ribosomes",
            "rough_er_lumen",
            "rough_er_exit_sites",
        ],
    },

    "smooth_er": {
        "visual": "network",
        "children": ["smooth_er_membrane", "lipid_synthesis", "calcium_store", "detoxification","smooth_er_lumen"],
    },
    "golgi": {
        "visual": "stack",
        "children": ["cis_cisternae", "medial_cisternae", "trans_cisternae", "golgi_vesicles"],
    },
    "lysosome": {
        "visual": "vesicle",
        "children": ["lysosome_membrane", "lysosome_lumen", "acid_hydrolases", "lysosome_cargo"],
    },
    "peroxisome": {
        "visual": "vesicle",
        "children": ["peroxisome_membrane", "peroxisome_matrix", "catalase", "fatty_acid_oxidation"],
    },
    "vesicles": {
        "visual": "vesicle",
        "children": ["vesicle_membrane", "vesicle_cargo", "coat_proteins", "fusion_proteins"],
    },
    "cytoskeleton": {
        "visual": "filament_network",
        "children": ["actin_filament", "microtubule", "intermediate_filament", "motor_proteins"],
    },
    "centrosome": {
        "visual": "centrosome",
        "children": ["centriole_pair", "centrosome_microtubules", "pericentriolar_material"],
    },
    "plasma_membrane": {
        "visual": "membrane",
        "children": ["glycocalyx", "aquaporin_1", "nicotinic_acetylcholine_receptor", "glut1"],
    },
    "cytoplasm": {
        "visual": "cytosol",
        "children": [],
    },
}


COMPONENT_DATA = {
    "dna": _component("DNA", "NUCLEIC ACID", "DNA is a polymer of nucleotide units carrying genetic information in its sequence.", "nucleic_acid", (), ["adenine", "cytosine", "guanine", "thymine"]),
    "histones": _component("Histone proteins", "DNA-PACKAGING PROTEINS", "Histone proteins help package and organize DNA into chromatin.", "protein_complex", (), ["glycine", "alanine", "serine"]),

    "protein_translocon": _component(
        "Sec61 protein translocon",
        "ER PROTEIN-CONDUCTING CHANNEL",
        "The Sec61 translocon is a membrane-embedded protein "
        "complex composed of Sec61 alpha, beta and gamma "
        "subunits. Its alpha subunit forms the main channel "
        "through which newly synthesized polypeptides can "
        "enter the ER lumen. A lateral gate also permits "
        "hydrophobic segments of membrane proteins to "
        "partition into the lipid bilayer. Sec61 can interact "
        "with translating ribosomes during cotranslational "
        "protein translocation. It is not a permanently "
        "open pore; its gating is regulated by interacting "
        "proteins and nascent-chain signals.",
        "protein_complex",
        (),
        ["protein_sec61_alpha"]
    ),

    "nuclear_envelope": _component("Nuclear envelope", "DOUBLE MEMBRANE", "Two lipid membranes surround the nucleus. Nuclear pores control traffic between nucleus and cytoplasm.", "double_membrane", ["nuclear_pores", "nuclear_membrane_lipids"], ["phosphatidylcholine", "phosphatidylethanolamine"]),
    "chromatin": _component("Chromatin", "DNA + PROTEINS", "DNA is packaged with histone proteins. Its organization changes as genes are accessed or compacted.", "chromatin", ["dna", "histones"], ["adenine", "cytosine", "guanine", "thymine"]),
    "nucleolus": _component("Nucleolus", "RNA + PROTEINS", "Ribosomal RNA is produced and combined with proteins to assemble ribosome subunits.", "ribosome", ["ribosomal_rna", "ribosomal_proteins"]),
    "nuclear_pores": _component("Nuclear pores", "PROTEIN COMPLEX", "Large protein assemblies form selective channels through the nuclear envelope.", "protein_complex", ["nuclear_pore_proteins"]),
    "mitochondrial_dna": _component("Mitochondrial DNA", "NUCLEIC ACID", "A small circular genome in the matrix encodes a subset of mitochondrial proteins and RNAs.", "nucleic_acid", (), ["adenine", "cytosine", "guanine", "thymine"]),
    "mitochondrial_ribosomes": _component("Mitochondrial ribosomes", "RNA + PROTEINS", "These ribosomes translate proteins encoded by mitochondrial DNA.", "ribosome", ["ribosomal_rna", "ribosomal_proteins"]),
    "nuclear_membrane_lipids": _component("Nuclear-envelope lipids", "LIPID BILAYER", "Phospholipids form the inner and outer nuclear-envelope membranes.", "membrane", (), ["phosphatidylcholine", "phosphatidylethanolamine", "cholesterol"]),
    "nuclear_pore_proteins": _component("Nucleoporins", "PROTEIN COMPLEX", "Nucleoporins assemble into a selective pore that gates transport through the envelope.", "protein_complex"),
    "inner_membrane": _component("Inner membrane", "LIPID BILAYER + PROTEINS", "The folded inner membrane carries the respiratory chain and ATP synthase. Its local lipid composition includes cardiolipin, phosphatidylcholine, and phosphatidylethanolamine.", "membrane", ["lipid_bilayer", "respiratory_chain", "atp_synthase"], ["phosphatidylcholine", "phosphatidylethanolamine", "cardiolipin"]),
    "outer_membrane": _component("Outer membrane", "LIPID BILAYER + PROTEINS", "The outer mitochondrial membrane separates the organelle from cytoplasm and contains channels and import machinery.", "membrane", ["outer_membrane_porins", "mitochondrial_import"], ["phosphatidylcholine", "phosphatidylethanolamine"]),
    "intermembrane_space": _component("Intermembrane space", "COMPARTMENT", "Protons pumped from the matrix accumulate here, creating part of the gradient that drives ATP synthesis.", "compartment", ["proton_gradient", "cytochrome_c"]),
    "cristae": _component("Cristae", "INNER-MEMBRANE FOLDS", "Cristae increase inner-membrane surface area and organize respiratory machinery.", "membrane", ["lipid_bilayer", "respiratory_chain", "atp_synthase"], ["cardiolipin", "phosphatidylcholine"]),
    "matrix": _component("Matrix", "MITOCHONDRIAL COMPARTMENT", "The matrix contains enzymes for pyruvate oxidation and the citric acid cycle, along with mitochondrial DNA and ribosomes.", "compartment", ["citric_acid_cycle", "mitochondrial_dna", "mitochondrial_ribosomes"], ["pyruvate", "adp", "atp"]),
    "lipid_bilayer": _component("Phospholipid bilayer", "MEMBRANE COMPOSITION", "Two leaflets of amphipathic lipids create a selective barrier. Select a lipid to see its actual molecular structure alongside the bilayer.", "membrane", (), ["phosphatidylcholine", "phosphatidylethanolamine", "cardiolipin"]),
    "respiratory_chain": _component("Respiratory chain", "ELECTRON-TRANSFER SYSTEM", "Electrons pass from NADH through Complex I, CoQ, Complex III, cytochrome c, and Complex IV to oxygen. Complexes pump protons across the membrane.", "respiration", ["complex_i", "coq", "complex_iii", "cytochrome_c", "complex_iv"], ["oxygen", "water"]),
    "atp_synthase": _component("ATP synthase", "ROTARY MOLECULAR MACHINE", "Proton flow through the membrane motor drives rotation and conformational changes that join ADP and inorganic phosphate to form ATP.", "protein_complex", ["atp_synthase_f0", "atp_synthase_f1"], ["adp", "phosphate", "atp"]),
    "outer_membrane_porins": _component("Outer-membrane porins", "CHANNEL PROTEINS", "Porin channels allow many small metabolites and ions to cross the outer mitochondrial membrane.", "protein_complex"),
    "mitochondrial_import": _component("Protein import machinery", "PROTEIN COMPLEX", "Import complexes recognize targeting signals and move nuclear-encoded proteins into mitochondria.", "protein_complex"),
    "proton_gradient": _component("Proton gradient", "ELECTROCHEMICAL GRADIENT", "Respiratory complexes move protons out of the matrix. Their return through ATP synthase releases usable free energy.", "gradient", ["atp_synthase"], ["water"]),
    "cytochrome_c": _component("Cytochrome c", "ELECTRON-CARRIER PROTEIN", "This mobile heme protein carries electrons from Complex III to Complex IV along the intermembrane-space side of the inner membrane.", "protein_complex"),
    "citric_acid_cycle": _component("Citric acid cycle", "METABOLIC PATHWAY", "Matrix enzymes oxidize acetyl-CoA and load electrons onto NADH and FADH₂ for delivery to the respiratory chain.", "pathway", ["pyruvate_oxidation"], ["pyruvate", "atp"]),
    
    "small_subunit": _component(
    "Small ribosomal subunit · 40S",
    "RNA + PROTEINS",
    "The eukaryotic 40S subunit binds mRNA and checks codon–anticodon pairing as tRNAs enter the decoding center.",
    "cytosolic_ribosome",
    ["small_subunit_rrna", "small_subunit_proteins", "messenger_rna", "transfer_rna"]
),
    
"large_subunit": _component(
    "Large ribosomal subunit · 60S",
    "RNA + PROTEINS",
    "The eukaryotic 60S subunit contains the peptidyl-transferase center, where rRNA catalyzes peptide-bond formation.",
    "cytosolic_ribosome",
    ["large_subunit_rrna", "large_subunit_proteins", "messenger_rna", "transfer_rna"]
),

    
    "messenger_rna": _component(
        "Messenger RNA (mRNA)",
        "PROTEIN-CODING RNA · TRANSLATION TEMPLATE",
        "Messenger RNA (mRNA) carries genetic instructions from DNA "
        "to ribosomes, where its nucleotide sequence is translated "
        "into a protein. The ribosome reads mRNA codons in the "
        "5' to 3' direction, with each codon containing three "
        "nucleotides. The four standard RNA bases are adenine, "
        "uracil, guanine and cytosine. Mature eukaryotic mRNAs "
        "typically possess a 5' cap containing 7-methylguanosine "
        "(m7G), connected to the RNA through an unusual 5'-5' "
        "triphosphate bridge. The cap helps protect mRNA and "
        "supports translation initiation through the cap-binding "
        "protein eIF4E. Many mRNAs also contain internal chemical "
        "modifications such as N6-methyladenosine (m6A), which can "
        "influence RNA stability, localization and translation. "
        "At the 3' end, a poly(A) tail composed of repeated "
        "adenosine residues helps regulate RNA stability and "
        "translation. Poly(A)-binding proteins such as PABPC1 "
        "associate with this tail. These proteins bind mRNA "
        "but are not chemically part of the RNA polymer.",
        "nucleic_acid",
        (),
        [
            "m7_guanosine",
            "m6_adenosine",
            "adenosine",
            "protein_eif4e",
            "protein_pabpc1",
        ]
    ),

    "transfer_rna": _component("Transfer RNA (tRNA)", "AMINO-ACID ADAPTER", "A tRNA pairs its anticodon with an mRNA codon and delivers its attached amino acid to the ribosome's A site.", "nucleic_acid", (), ["adenine", "cytosine", "guanine", "uracil"]),

    "trna_e_site": _component(
        "E-site tRNA",
        "EXIT SITE · DEACYLATED tRNA",
        "The E site is the exit site of the ribosome. During "
        "translation elongation, a tRNA that has already donated "
        "its amino acid moves from the P site into the E site "
        "after translocation. It is now deacylated, meaning "
        "that its terminal 3'-CCA end no longer carries an "
        "amino acid. The tRNA generally leaves the ribosome "
        "from this position and can later be recharged by "
        "its corresponding aminoacyl-tRNA synthetase. "
        "A key structural feature to examine is the "
        "terminal adenosine (A76), whose 3'-hydroxyl "
        "normally serves as an amino-acid attachment site.",
        "trna_site",
        (),
        ["adenosine","protein_eef2"]
    ),

    "trna_p_site": _component(
        "P-site tRNA",
        "PEPTIDYL SITE · GROWING PROTEIN",
        "The P site holds the peptidyl-tRNA during translation "
        "elongation. Its terminal adenosine is connected "
        "through an ester bond to the growing polypeptide. "
        "During peptide-bond formation, the nascent peptide "
        "is transferred from the P-site tRNA to the amino "
        "acid on the A-site tRNA. The 60S peptidyl-transferase "
        "center catalyzes this reaction. "
        "Following translocation, the newly deacylated "
        "P-site tRNA moves toward the E site. "
        "The alanyl-phenylalanine molecule shown below "
        "is a simplified example of a short peptide, "
        "not the complete tRNA-linked growing chain.",
        "trna_site",
        (),
        ["nascent_peptide_ala_phe", "adenosine","protein_eif5a"]
    ),

    "trna_a_site": _component(
        "A-site tRNA",
        "AMINOACYL SITE · INCOMING AMINO ACID",
        "The A site accepts an incoming aminoacyl-tRNA "
        "whose anticodon matches the mRNA codon. "
        "During eukaryotic elongation, eEF1A-GTP helps "
        "deliver the charged tRNA. Correct codon-anticodon "
        "recognition allows accommodation into the ribosome. "
        "The amino acid is attached to the terminal "
        "adenosine of the tRNA by an ester linkage. "
        "The peptidyl-transferase center then transfers "
        "the growing peptide from the P-site tRNA "
        "to this A-site amino acid. "
        "In our displayed example, the mRNA codon GAA "
        "specifies glutamate, and its matching tRNA "
        "has the anticodon CUU.",
        "trna_site",
        (),
        ["glutamate", "adenosine", "protein_eef1a", "protein_ears1"]
    ),

    "ribosomal_rna": _component(
    "Ribosomal RNA (rRNA)",
    "STRUCTURAL + CATALYTIC RNA",
    "Ribosomal RNA (rRNA) is a long, highly folded RNA polymer "
    "that forms the structural and functional core of the ribosome. "
    "Unlike messenger RNA, which carries protein-coding information, "
    "rRNA directly participates in the machinery of protein synthesis. "
    "In eukaryotic cytosolic ribosomes, the 40S small subunit contains "
    "18S rRNA, which helps form the decoding center and monitors "
    "codon–anticodon interactions between mRNA and tRNA. "
    "The 60S large subunit contains 28S, 5.8S and 5S rRNAs. "
    "The 28S rRNA forms the catalytic peptidyl-transferase center "
    "responsible for peptide-bond formation. This makes the ribosome "
    "a ribozyme: an RNA-based catalyst. "
    "rRNA folds into complex secondary and tertiary structures through "
    "intramolecular base pairing, including helices, loops, bulges "
    "and junctions. Ribosomal proteins stabilize and organize these "
    "structures. rRNA also contains chemically modified nucleotides, "
    "including pseudouridine and 2'-O-methylated residues, which "
    "contribute to ribosome structure and function.",
    "nucleic_acid",
    (),
    ["adenine", "cytosine", "guanine", "uracil"]
),


    "large_subunit_rrna": _component(
        "Large-subunit ribosomal RNA (rRNA)",
        "60S · STRUCTURAL + CATALYTIC RNA",
        "The eukaryotic 60S ribosomal subunit contains 28S, 5.8S and 5S "
        "ribosomal RNAs. These highly folded RNA molecules form the "
        "structural core of the large subunit. The 28S rRNA contributes "
        "the peptidyl-transferase center, where peptide bonds are formed "
        "during translation. Ribosomal RNA therefore performs the central "
        "catalytic reaction of protein synthesis. Chemical modifications "
        "such as pseudouridylation and 2'-O-methylation help regulate "
        "local RNA structure, stability and ribosome function. "
        "Pseudouridine (Psi) is formed by isomerization of uridine, "
        "whereas 2'-O-methylguanosine contains a methyl group attached "
        "to the ribose 2'-oxygen.",
        "nucleic_acid",
        (),
        ["pseudouridine", "o2_methylguanosine"]
    ),

    "small_subunit_rrna": _component(
        "Small-subunit ribosomal RNA (rRNA)",
        "40S · DECODING RNA",
        "The eukaryotic 40S ribosomal subunit contains 18S rRNA, which "
        "forms the structural and functional basis of the decoding center. "
        "This region helps monitor correct codon-anticodon pairing between "
        "messenger RNA and transfer RNA. The 18S rRNA contains numerous "
        "post-transcriptional modifications. A particularly interesting "
        "example is N6,N6-dimethyladenosine (m6,6A), found at two adjacent "
        "conserved positions near the 3' end of eukaryotic 18S rRNA. "
        "Another modification type is 2'-O-methylcytidine (Cm), in which "
        "the ribose 2'-hydroxyl is methylated. These modifications can "
        "influence RNA folding, ribosome maturation and function.",
        "nucleic_acid",
        (),
        ["dimethyladenosine_m66", "o2_methylcytidine"]
    ),

    "ribosomal_proteins": _component("Ribosomal proteins", "RIBOSOME-ASSOCIATED PROTEINS", "Ribosomal proteins assemble around rRNA, stabilize the subunits, and help support translation and ribosome dynamics.", "protein_complex", (), ["glycine", "alanine", "serine"]),
    
    "large_subunit_proteins": _component(
        "Large-subunit ribosomal proteins",
        "60S · RIBOSOMAL PROTEIN COMPLEX",
        "The eukaryotic 60S subunit contains a distinct collection of "
        "ribosomal proteins assembled around 28S, 5.8S and 5S rRNAs. "
        "These proteins stabilize the complex architecture of the "
        "large subunit, support ribosome assembly, and help organize "
        "the peptide exit tunnel and translation machinery. "
        "The peptidyl-transferase center itself is formed primarily "
        "by rRNA. Explore four representative 60S proteins below.",
        "protein_complex",
        (),
        ["protein_ul3", "protein_ul4",
         "protein_ul22", "protein_el24"]
    ),

    "small_subunit_proteins": _component(
        "Small-subunit ribosomal proteins",
        "40S · RIBOSOMAL PROTEIN COMPLEX",
        "The eukaryotic 40S subunit contains proteins associated "
        "with 18S rRNA. Together they support mRNA binding, "
        "codon recognition, small-subunit assembly and translation "
        "accuracy. Several proteins contribute to the architecture "
        "of the mRNA entry channel, while others have important "
        "roles in ribosome maturation and cellular regulation. "
        "Explore four representative 40S proteins below.",
        "protein_complex",
        (),
        ["protein_us3", "protein_us5",
         "protein_us7", "protein_es6"]
    ),

    
    "rough_er_exit_sites": _component(
        "ER exit sites · COPII transport",
        "SECRETORY PATHWAY · ER EXPORT",
        "ER exit sites are specialized, usually ribosome-poor "
        "regions of the endoplasmic reticulum membrane where "
        "export cargo is concentrated and COPII transport "
        "carriers form. Sar1 activation initiates recruitment "
        "of the COPII coat. Sec23/Sec24 forms the inner coat, "
        "participating in cargo selection and regulation of "
        "Sar1. Sec13/Sec31 forms the outer coat, contributing "
        "to membrane deformation and carrier formation. "
        "Transport carriers deliver cargo toward the ER-Golgi "
        "intermediate compartment, from which proteins "
        "can move onward through the secretory pathway.",
        "vesicle",
        [
            "copii_sar1",
            "copii_inner_coat",
            "copii_outer_coat",
            "copii_cargo",
            "copii_carrier",
        ],
        ["gtp", "gdp", "phosphatidylcholine"]
    ),

    "copii_sar1": _component(
        "Sar1 · COPII initiation",
        "SMALL GTPASE · MEMBRANE RECRUITMENT",
        "Sar1 is a small GTP-binding protein that initiates "
        "COPII assembly. The ER membrane protein Sec12 acts "
        "as a guanine nucleotide exchange factor, promoting "
        "exchange of GDP for GTP on Sar1. GTP binding exposes "
        "an amphipathic N-terminal helix that inserts into "
        "the cytosolic leaflet of the ER membrane and helps "
        "deform it. Active Sar1 recruits Sec23/Sec24. "
        "GTP hydrolysis participates in regulation and "
        "disassembly of the COPII coat.",
        "protein_complex",
        (),
        ["protein_sar1", "protein_sec12", "gtp", "gdp"]
    ),

    "copii_inner_coat": _component(
        "COPII inner coat · Sec23/Sec24",
        "CARGO RECOGNITION · COAT ASSEMBLY",
        "Sec23 and Sec24 form the inner layer of the COPII "
        "coat. Sec24 helps recognize export signals on "
        "selected cargo proteins or their cargo receptors. "
        "Sec23 interacts with Sar1 and has GTPase-activating "
        "activity that contributes to control of Sar1's "
        "nucleotide cycle. The inner coat helps couple "
        "cargo selection to transport carrier formation.",
        "protein_complex",
        (),
        ["protein_sec23", "protein_sec24", "protein_sar1"]
    ),

    "copii_outer_coat": _component(
        "COPII outer coat · Sec13/Sec31",
        "MEMBRANE SHAPING · COAT SCAFFOLD",
        "Sec13 and Sec31 assemble the outer COPII coat. "
        "Their protein complexes form a flexible scaffold "
        "that helps organize and stabilize curvature "
        "during the development of ER export carriers. "
        "The outer coat also regulates the Sar1 GTPase "
        "cycle through interactions with Sec23. "
        "COPII carrier geometry can vary depending "
        "on the cargo and cellular conditions.",
        "protein_complex",
        (),
        ["protein_sec13", "protein_sec31"]
    ),

    "copii_cargo": _component(
        "Protein cargo selection",
        "ER EXPORT SIGNALS · CARGO RECEPTORS",
        "COPII transport is selective. Some membrane "
        "proteins display cytosolic export signals "
        "that can be recognized by COPII components. "
        "Soluble luminal cargo generally requires "
        "membrane-associated cargo receptors or "
        "other packaging mechanisms. The receptor "
        "LMAN1, together with MCFD2, helps export "
        "certain glycoprotein cargoes. Correct "
        "protein folding and ER quality control "
        "influence which proteins are permitted "
        "to proceed through the secretory pathway.",
        "protein_complex",
        (),
        ["protein_lman1", "protein_mcfd2"]
    ),

    "copii_carrier": _component(
        "COPII transport carrier",
        "ER TO ER-GOLGI INTERMEDIATE COMPARTMENT",
        "COPII machinery drives the formation of carriers "
        "containing selected membrane and soluble cargo. "
        "After formation, the coat is remodeled or "
        "released and transport proceeds toward the "
        "ER-Golgi intermediate compartment (ERGIC). "
        "Further trafficking carries cargo toward "
        "the cis-Golgi. Not all COPII carriers have "
        "the same size or morphology, and cargo "
        "delivery involves additional tethering "
        "and membrane-fusion proteins.",
        "vesicle",
        (),
        ["phosphatidylcholine", "phosphatidylethanolamine"]
    ),


    
    "rough_er_membrane": _component(
        "Rough ER membrane",
        "PHOSPHOLIPID BILAYER + MEMBRANE PROTEINS",
        "The rough endoplasmic reticulum is surrounded by a "
        "phospholipid bilayer continuous with the outer nuclear "
        "membrane. Its membrane contains relatively little "
        "cholesterol compared with the plasma membrane and "
        "includes phosphatidylcholine, phosphatidylethanolamine, "
        "phosphatidylinositol and phosphatidylserine. "
        "Specialized membrane proteins transport newly "
        "synthesized polypeptides, recognize targeting signals "
        "and modify proteins as they enter the ER. "
        "The Sec61 translocon forms the central protein "
        "conducting channel. The SRP receptor assists "
        "targeting of ribosome-nascent-chain complexes, "
        "while oligosaccharyltransferase attaches N-linked "
        "oligosaccharides to suitable nascent proteins.",
        "membrane",
        [
            "protein_translocon",
            "er_srp_receptor",
            "er_ost",
        ],
        [
            "phosphatidylcholine",
            "phosphatidylethanolamine",
            "phosphatidylinositol",
            "phosphatidylserine",
        ]
    ),

    "er_srp_receptor": _component(
        "Signal recognition particle receptor",
        "ER MEMBRANE · PROTEIN TARGETING",
        "The signal recognition particle receptor helps "
        "bring ribosome-nascent-chain complexes to the "
        "endoplasmic reticulum membrane. The receptor "
        "contains SRalpha and SRbeta subunits. SRP recognizes "
        "appropriate signal sequences emerging from a "
        "translating ribosome, and interactions involving "
        "GTP help coordinate delivery to the Sec61 "
        "translocon. This system directs many secretory "
        "and membrane proteins into the ER pathway.",
        "protein_complex",
        (),
        ["protein_sr_alpha", "protein_sr_beta"]
    ),

    "er_ost": _component(
        "Oligosaccharyltransferase (OST)",
        "ER MEMBRANE · N-LINKED GLYCOSYLATION",
        "Oligosaccharyltransferase catalyzes transfer "
        "of a preassembled oligosaccharide from "
        "dolichol-linked donor molecules onto suitable "
        "asparagine residues of proteins entering "
        "the endoplasmic reticulum. Mammalian OST "
        "complexes contain either STT3A or STT3B "
        "as their catalytic subunit. The two forms "
        "have overlapping but distinct functions "
        "during and after protein translocation.",
        "protein_complex",
        ["er_n_glycosylation"],
        ["protein_stt3a", "protein_stt3b"]

    ),

    "bound_ribosomes": _component("ER-bound ribosomes", "80S RNA + PROTEIN MACHINE", "Eukaryotic 80S ribosomes docked at the rough ER translate proteins destined for secretion, membranes, or the endomembrane system.", "cytosolic_ribosome", ["small_subunit", "large_subunit", "messenger_rna", "transfer_rna", "ribosomal_rna", "ribosomal_proteins"]),

    "rough_er_lumen": _component(
        "Rough ER lumen",
        "PROTEIN MATURATION · CALCIUM-RICH COMPARTMENT",
        "The endoplasmic reticulum lumen is the aqueous interior "
        "of the ER membrane network. Newly synthesized secretory "
        "proteins and luminal domains of membrane proteins enter "
        "this compartment through protein translocation machinery. "
        "The lumen provides a specialized chemical environment "
        "for protein folding, disulfide-bond formation and "
        "glycoprotein maturation. Chaperones such as BiP help "
        "proteins fold while protein disulfide isomerases "
        "catalyze the formation and rearrangement of disulfide "
        "bonds. Calnexin and calreticulin assist glycoprotein "
        "quality control. Proteins that cannot achieve an "
        "acceptable conformation may be directed toward "
        "ER-associated degradation. The ER lumen also serves "
        "as an important intracellular calcium reservoir. "
        "Its environment and protein composition differ "
        "substantially from the surrounding cytosol.",
        "compartment",
        [
            "protein_folding",
            "er_disulfide",
            "er_calnexin_cycle",
            "er_quality_control",
            "er_lumen_calcium",
            "er_n_glycosylation"
        ],
        ["water", "calcium"]
    ),
    
    "er_n_glycosylation": _component(
        "N-linked protein glycosylation",
        "ER GLYCOPROTEIN MATURATION",
        "N-linked glycosylation is a major protein modification "
        "that begins in the endoplasmic reticulum. "
        "A complex oligosaccharide is assembled on a "
        "dolichol-pyrophosphate lipid carrier in the ER membrane. "
        "The mature donor typically contains three glucose, "
        "nine mannose and two N-acetylglucosamine residues "
        "(Glc3Man9GlcNAc2). Oligosaccharyltransferase "
        "(OST) transfers this preassembled sugar chain "
        "to the side-chain nitrogen of a suitable asparagine "
        "residue in a nascent protein. The usual recognition "
        "sequence is Asn-X-Ser or Asn-X-Thr, where X is "
        "not proline. Following transfer, glucose residues "
        "are removed during ER glycoprotein maturation. "
        "The glycan helps regulate protein folding, "
        "quality control and transport through the "
        "secretory pathway.",
        "er_glycosylation",
        [
            "er_glycan_assembly",
            "er_glycan_transfer",
            "er_glycan_trimming",
        ],
        [
            "n_acetylglucosamine",
            "mannose",
            "glucose",
            "asparagine",
        ]
    ),

    "er_glycan_assembly": _component(
        "Assembly of the N-linked glycan",
        "DOLICHOL-LINKED OLIGOSACCHARIDE",
        "The N-linked glycan precursor is assembled "
        "stepwise on a dolichol-phosphate-derived "
        "lipid carrier in the ER membrane. "
        "N-acetylglucosamine and mannose residues "
        "are initially added on the cytosolic side. "
        "The growing lipid-linked glycan is then "
        "translocated to the luminal side, "
        "where additional mannose and glucose "
        "residues are incorporated. "
        "The completed donor contains 14 sugar "
        "residues with the composition Glc3Man9GlcNAc2. "
        "The sugar residues are connected by "
        "specific glycosidic bonds, forming "
        "a branched oligosaccharide rather "
        "than a simple linear chain.",
        "protein_complex",
        (),
        [
            "n_acetylglucosamine",
            "mannose",
            "glucose",
        ]
    ),

    "er_glycan_transfer": _component(
        "Transfer of the glycan to protein",
        "OST · ASPARAGINE GLYCOSYLATION",
        "Oligosaccharyltransferase transfers "
        "the preassembled Glc3Man9GlcNAc2 glycan "
        "from its dolichol-pyrophosphate carrier "
        "to the side-chain amide nitrogen of "
        "a suitable asparagine residue. "
        "This creates an N-glycosidic linkage "
        "between the first N-acetylglucosamine "
        "residue and the protein. "
        "In mammals, complexes containing STT3A "
        "perform much of the cotranslational "
        "glycosylation, while STT3B-containing "
        "complexes can modify certain sites "
        "missed by the first machinery. "
        "Not every potential glycosylation "
        "sequence is necessarily modified.",
        "protein_complex",
        (),
        [
            "asparagine",
            "n_acetylglucosamine",
            "protein_stt3a",
            "protein_stt3b",
        ]
    ),

    "er_glycan_trimming": _component(
        "ER glycan trimming",
        "GLUCOSE REMOVAL · FOLDING QUALITY CONTROL",
        "After the oligosaccharide is transferred "
        "to a protein, ER glucosidases begin "
        "removing its terminal glucose residues. "
        "Glucosidase I first removes the outermost "
        "glucose, and glucosidase II can remove "
        "the remaining glucose residues in "
        "subsequent steps. A monoglucosylated "
        "glycan can interact with the lectin "
        "chaperones calnexin and calreticulin. "
        "The UGGT quality-control machinery "
        "can reglucosylate certain incompletely "
        "folded glycoproteins, allowing "
        "additional folding attempts. "
        "Glycan processing therefore helps "
        "determine whether proteins continue "
        "maturation or enter quality-control "
        "and degradation pathways.",
        "protein_complex",
        (),
        [
            "glucose",
            "protein_glucosidase_i",
            "protein_glucosidase_ii",
            "protein_calreticulin",
        ]
    ),


   
    "protein_folding": _component(
        "Protein folding · BiP chaperone",
        "ER CHAPERONE · ATP-DEPENDENT FOLDING",
        "Proteins entering the ER lumen must acquire appropriate "
        "three-dimensional conformations. BiP, also known as "
        "GRP78 or HSPA5, is a member of the Hsp70 chaperone "
        "family. It binds exposed hydrophobic regions of "
        "unfolded or incompletely folded proteins, reducing "
        "inappropriate aggregation. BiP uses an ATP-dependent "
        "binding and release cycle regulated by co-chaperones. "
        "ATP binding favors substrate exchange, while ATP "
        "hydrolysis promotes tighter substrate binding. "
        "Chaperones assist folding but do not necessarily "
        "determine a protein's final structure.",
        "protein_complex",
        (),
        ["protein_bip", "atp", "adp"]
    ),

    "er_disulfide": _component(
        "Disulfide-bond formation",
        "OXIDATIVE PROTEIN FOLDING",
        "The ER lumen supports formation of disulfide bonds "
        "between pairs of cysteine residues in proteins. "
        "Oxidation links their sulfur atoms to create a "
        "covalent S-S bond, helping stabilize many secretory "
        "and extracellular proteins. Protein disulfide "
        "isomerase, including PDI/P4HB, catalyzes disulfide "
        "formation, reduction and rearrangement. "
        "The small molecule cystine illustrates two cysteine "
        "units joined by a disulfide bond, although real "
        "protein disulfides connect residues within or "
        "between polypeptide chains. Glutathione also "
        "participates in the ER redox environment.",
        "protein_complex",
        (),
        ["protein_pdi", "cysteine", "cystine", "glutathione"]
    ),

    "er_calnexin_cycle": _component(
        "Calnexin-calreticulin cycle",
        "GLYCOPROTEIN FOLDING QUALITY CONTROL",
        "Calnexin and calreticulin are lectin chaperones "
        "that recognize specific monoglucosylated N-linked "
        "glycans on newly synthesized glycoproteins. "
        "Calnexin is associated with the ER membrane, "
        "whereas calreticulin is a soluble luminal protein. "
        "They cooperate with additional folding factors, "
        "including ERp57. Removal and readdition of terminal "
        "glucose residues help control repeated folding "
        "attempts. This cycle connects protein folding "
        "to the chemical structure of N-linked glycans.",
        "protein_complex",
        (),
        [
            "protein_calnexin",
            "protein_calreticulin",
            "glucose",
        ]
    ),

    "er_quality_control": _component(
        "ER protein quality control",
        "MISFOLDED PROTEINS · ERAD",
        "The ER contains a surveillance network that "
        "distinguishes proteins undergoing normal folding "
        "from those that remain persistently misfolded. "
        "BiP and other chaperones can support further "
        "folding attempts. Some defective glycoproteins "
        "undergo mannose trimming and recognition by "
        "quality-control factors such as EDEM1. "
        "Proteins selected for ER-associated degradation "
        "(ERAD) can be transported toward the cytosol, "
        "ubiquitinated and degraded by proteasomes. "
        "The unfolded protein response helps cells "
        "adapt when folding demand exceeds ER capacity.",
        "protein_complex",
        (),
        ["protein_bip", "protein_edem1", "protein_pdi"]
    ),

    "er_lumen_calcium": _component(
        "ER luminal calcium storage",
        "CALCIUM RESERVOIR · CELLULAR SIGNALING",
        "The endoplasmic reticulum maintains a substantial "
        "store of calcium ions. ATP-driven SERCA pumps "
        "transport calcium from the cytosol into the "
        "ER lumen, while channels such as IP3 receptors "
        "can release calcium during cell signaling. "
        "The soluble luminal protein calreticulin "
        "binds calcium and contributes to its buffering. "
        "Luminal calcium also supports the activity "
        "of several ER folding and processing proteins.",
        "compartment",
        (),
        ["calcium", "protein_calreticulin", "atp"]
    ),

        
    "smooth_er_lumen": _component(
        "Smooth ER lumen",
        "AQUEOUS COMPARTMENT · CALCIUM HOMEOSTASIS",
        "The smooth endoplasmic reticulum lumen is the "
        "aqueous space enclosed by the ER membrane. "
        "It is physically continuous with the rough "
        "ER lumen and forms part of the same internal "
        "membrane network. The ER stores calcium at "
        "much higher free concentrations than the "
        "resting cytosol. Calcium is accumulated by "
        "ATP-dependent SERCA pumps, released through "
        "channels such as IP3 receptors and buffered "
        "by calcium-binding proteins including "
        "calreticulin. The lumen also contains water, "
        "ions and proteins involved in maintaining "
        "the internal environment of the ER. "
        "Smooth and rough ER share many functions, "
        "but the prominence of calcium handling, "
        "lipid metabolism and protein processing "
        "varies among ER regions and cell types.",
        "compartment",
        [
            "ser_lumen_calcium_pool",
            "ser_calcium_buffer",
            "ser_lumen_continuity",
        ],
        [
            "water",
            "calcium",
            "protein_calreticulin",
        ]
    ),
    
    "ser_lumen_calcium_pool": _component(
        "Luminal calcium pool",
        "FREE AND BUFFERED CALCIUM · ER RESERVOIR",
        "The ER lumen contains both free calcium ions "
        "and calcium bound to luminal proteins. "
        "The concentration of free calcium in the ER "
        "is normally far greater than in the resting "
        "cytosol, allowing the ER to function as a "
        "reservoir for intracellular signaling. "
        "SERCA pumps actively transport calcium "
        "into the lumen using ATP. When calcium "
        "release channels open, free calcium can "
        "move into the cytosol down its "
        "electrochemical gradient. Calcium-binding "
        "proteins buffer the store and help regulate "
        "changes in free luminal calcium.",
        "compartment",
        [
            "ser_serca_pump",
            "ser_ip3_receptor",
        ],
        ["calcium", "atp", "adp"]
    ),

    "ser_lumen_continuity": _component(
        "Continuous ER lumen",
        "SMOOTH ER · ROUGH ER CONNECTION",
        "The smooth and rough endoplasmic reticulum "
        "are interconnected regions of the same "
        "membrane-bound organelle. Their luminal "
        "spaces communicate through the continuous "
        "ER network. The rough ER is typically "
        "enriched in ribosome-associated membrane "
        "sheets and protein-processing machinery, "
        "while smooth ER regions often form "
        "tubules enriched in lipid-metabolic "
        "or calcium-handling functions. "
        "These are functional and structural "
        "specializations, not completely "
        "separate organelles. The ER lumen "
        "is also continuous with the "
        "perinuclear space between the "
        "two nuclear membranes.",
        "compartment",
        (),
        ["water", "calcium"]
    ),



        
    "smooth_er_membrane": _component(
        "Smooth ER membrane",
        "PHOSPHOLIPID BILAYER · TUBULAR MEMBRANE NETWORK",
        "The smooth endoplasmic reticulum consists largely "
        "of interconnected membrane tubules. Its phospholipid "
        "bilayer is continuous with the rough ER and contains "
        "relatively little cholesterol compared with the "
        "plasma membrane. Reticulon proteins help stabilize "
        "high membrane curvature, while atlastin GTPases "
        "promote fusion between ER tubules. VAP proteins "
        "help establish membrane contact sites with other "
        "organelles. The ER membrane also contains enzymes "
        "for lipid synthesis, calcium transport and metabolic "
        "reactions. The relative importance of these "
        "activities varies between cell types.",
        "membrane",
        [
            "ser_reticulon",
            "ser_atlastin",
            "ser_vapb",
        ],
        [
            "phosphatidylcholine",
            "phosphatidylethanolamine",
            "phosphatidylinositol",
            "phosphatidylserine",
        ]
    ),
    
    "ser_reticulon": _component(
        "Reticulon-4 (RTN4)",
        "ER MEMBRANE CURVATURE",
        "Reticulon proteins are membrane-shaping proteins "
        "that are enriched in highly curved ER tubules "
        "and sheet edges. Their hydrophobic membrane-embedded "
        "segments form a hairpin-like arrangement that "
        "partially inserts into the bilayer, helping "
        "generate and stabilize membrane curvature. "
        "Reticulon-4, also called Nogo, is one member "
        "of this family. Different cell types express "
        "different reticulon isoforms.",
        "protein_complex",
        (),
        ["protein_rtn4"]
    ),

    "ser_atlastin": _component(
        "Atlastin GTPase",
        "ER TUBULE FUSION",
        "Atlastins are ER membrane-anchored dynamin-like "
        "GTPases. They help fuse adjacent ER membrane "
        "tubules, establishing and maintaining the "
        "interconnected tubular ER network. "
        "Atlastin molecules associated with opposing "
        "membranes interact, and their GTPase cycle "
        "helps drive membrane fusion. Mammals possess "
        "three atlastin isoforms, ATL1, ATL2 and ATL3, "
        "whose expression varies by tissue.",
        "protein_complex",
        (),
        ["protein_atl3", "gtp", "gdp"]
    ),

    "ser_vapb": _component(
        "VAPB membrane contact protein",
        "ER-ORGANELLE CONTACT SITES",
        "VAPB is a tail-anchored protein of the ER membrane. "
        "Its cytosol-facing domain binds partner proteins "
        "that help form close contacts between the ER "
        "and other organelles, including mitochondria, "
        "endosomes and the plasma membrane. "
        "These contact sites support lipid exchange "
        "and cellular signaling without requiring "
        "the two organelle membranes to fuse.",
        "protein_complex",
        (),
        ["protein_vapb"]
    ),


   
    "lipid_synthesis": _component(
        "Lipid synthesis in the Smooth ER",
        "PHOSPHOLIPID · TRIACYLGLYCEROL · STEROL METABOLISM",
        "The endoplasmic reticulum is a major site of cellular "
        "lipid synthesis and metabolism. ER-associated enzymes "
        "produce many membrane phospholipids and neutral lipids "
        "and participate in cholesterol biosynthesis. "
        "Phosphatidylcholine and phosphatidylethanolamine "
        "are important structural membrane lipids. "
        "Triacylglycerols can be assembled through acylation "
        "of diacylglycerol and subsequently stored in lipid "
        "droplets that originate from the ER. "
        "The cholesterol biosynthetic pathway includes the "
        "ER membrane enzyme HMG-CoA reductase, although "
        "different reactions take place in different "
        "cellular locations. These metabolic activities "
        "are regulated according to cellular needs.",
        "lipid_metabolism",
        [
            "ser_phospholipid_synthesis",
            "ser_tag_synthesis",
            "ser_cholesterol_synthesis",
        ],
        [
            "phosphatidylcholine",
            "phosphatidylethanolamine",
            "cholesterol",
        ]
    ),
    
    "ser_phospholipid_synthesis": _component(
        "Phospholipid synthesis",
        "MEMBRANE LIPID BIOSYNTHESIS",
        "The ER is a major location for phospholipid "
        "biosynthesis. Phosphatidylcholine (PC) and "
        "phosphatidylethanolamine (PE) can be produced "
        "through the Kennedy pathway. Choline or "
        "ethanolamine is activated through phosphorylation "
        "and reaction with CTP to form a CDP-linked "
        "headgroup. ER-associated phosphotransferases "
        "then transfer the headgroup to diacylglycerol, "
        "producing PC or PE. These molecules contribute "
        "to membrane structure, curvature and function. "
        "Individual biosynthetic routes and their "
        "importance vary across tissues.",
        "protein_complex",
        (),
        [
            "choline",
            "ethanolamine",
            "diacylglycerol_example",
            "phosphatidylcholine",
            "phosphatidylethanolamine",
            "protein_chpt1",
        ]
    ),

    "ser_tag_synthesis": _component(
        "Triacylglycerol synthesis",
        "NEUTRAL LIPID STORAGE · LIPID DROPLETS",
        "Triacylglycerols consist of a glycerol backbone "
        "esterified to three fatty acid chains. "
        "A major synthesis pathway begins with "
        "glycerol-3-phosphate and proceeds through "
        "lysophosphatidic acid and phosphatidic acid "
        "to diacylglycerol. DGAT enzymes catalyze "
        "the addition of a third fatty acyl group "
        "from fatty acyl-CoA to produce triacylglycerol. "
        "Neutral lipids accumulate between ER membrane "
        "leaflets and can contribute to the formation "
        "of cytosolic lipid droplets. Triolein is "
        "one representative triacylglycerol.",
        "protein_complex",
        (),
        [
            "glycerol_3_phosphate",
            "oleic_acid",
            "diacylglycerol_example",
            "triolein",
            "protein_dgat1",
        ]
    ),

    "ser_cholesterol_synthesis": _component(
        "Cholesterol biosynthesis",
        "STEROL METABOLISM · MEVALONATE PATHWAY",
        "Cholesterol is synthesized through a multistep "
        "pathway beginning with acetyl-CoA-derived "
        "intermediates. HMG-CoA reductase, an integral "
        "ER membrane protein with a cytosol-facing "
        "catalytic domain, reduces HMG-CoA to mevalonate "
        "using NADPH. Later reactions generate activated "
        "isoprenoid units, squalene, lanosterol and "
        "ultimately cholesterol. The pathway involves "
        "enzymes associated with both the ER and other "
        "cellular compartments. Cholesterol synthesis "
        "is tightly regulated by sterol availability "
        "and cellular metabolic demand.",
        "protein_complex",
        (),
        [
            "cholesterol",
            "protein_hmgcr",
        ]
    ),


   
    "calcium_store": _component(
        "Calcium regulation in the Smooth ER",
        "CALCIUM STORAGE · TRANSPORT · CELLULAR SIGNALING",
        "The endoplasmic reticulum is a major intracellular "
        "calcium reservoir. SERCA pumps use energy from ATP "
        "hydrolysis to transport calcium from the cytosol "
        "into the ER lumen, against its electrochemical "
        "gradient. IP3 receptors form calcium-release "
        "channels in the ER membrane. When activated by "
        "inositol 1,4,5-trisphosphate and appropriately "
        "regulated by cytosolic calcium, they allow calcium "
        "to flow from the ER into the cytosol. "
        "ER luminal proteins, including calreticulin, "
        "bind calcium and help buffer the stored pool. "
        "Transient changes in cytosolic calcium control "
        "many processes such as secretion, metabolism "
        "and cellular signaling. In muscle cells, the "
        "specialized sarcoplasmic reticulum uses related "
        "calcium-handling machinery with a major role "
        "for ryanodine receptors.",
        "calcium_regulation",
        [
            "ser_serca_pump",
            "ser_ip3_receptor",
            "ser_calcium_buffer",
        ],
        ["calcium", "atp", "adp"]
    ),
    
    "ser_serca_pump": _component(
        "SERCA calcium pump",
        "ATP-DEPENDENT CALCIUM TRANSPORT",
        "SERCA is a P-type ATPase embedded in the "
        "endoplasmic reticulum membrane. It uses "
        "ATP hydrolysis to transport calcium ions "
        "from the cytosol into the ER lumen. "
        "In its transport cycle, calcium binds "
        "to the pump, ATP-dependent phosphorylation "
        "drives conformational changes, and calcium "
        "is released on the luminal side. "
        "The pump then returns to its initial state. "
        "The canonical transport stoichiometry is "
        "two calcium ions per ATP hydrolyzed, with "
        "countertransport of protons. "
        "SERCA activity helps restore low resting "
        "cytosolic calcium concentrations after "
        "a signaling event.",
        "protein_complex",
        (),
        ["protein_serca2", "calcium", "atp", "adp", "phosphate"]
    ),

    "ser_ip3_receptor": _component(
        "IP3 receptor calcium channel",
        "SECOND-MESSENGER-ACTIVATED CALCIUM RELEASE",
        "Inositol 1,4,5-trisphosphate receptors "
        "(IP3Rs) are large tetrameric calcium "
        "channels embedded in the ER membrane. "
        "IP3 is a soluble second messenger "
        "generated from membrane phosphoinositides "
        "during signaling. Binding of IP3, together "
        "with regulation by calcium and other factors, "
        "controls channel opening. When an IP3 receptor "
        "opens, calcium can move down its electrochemical "
        "gradient from the ER lumen into the cytosol. "
        "The resulting cytosolic calcium signal "
        "can activate downstream cellular processes.",
        "protein_complex",
        (),
        ["protein_itpr1", "inositol_trisphosphate", "calcium"]
    ),

    "ser_calcium_buffer": _component(
        "Calcium buffering in the ER lumen",
        "LUMINAL CALCIUM RESERVOIR",
        "The ER lumen stores calcium in both free "
        "and protein-bound forms. Calreticulin is "
        "a soluble ER protein that can bind "
        "substantial amounts of calcium. "
        "Luminal buffering helps maintain the "
        "calcium reservoir while allowing free "
        "calcium concentrations to change during "
        "signaling and transport. The specialized "
        "sarcoplasmic reticulum of muscle cells "
        "also contains calcium-binding proteins "
        "such as calsequestrin.",
        "compartment",
        (),
        ["calcium", "protein_calreticulin"]
    ),


   
    "detoxification": _component(
        "Smooth ER detoxification",
        "CYTOCHROME P450 · OXIDATIVE METABOLISM",
        "The smooth endoplasmic reticulum contains enzymes "
        "that metabolize drugs, environmental chemicals "
        "and endogenous compounds. Many cytochrome P450 "
        "enzymes are anchored in the ER membrane, with "
        "their catalytic domains facing the cytosol. "
        "They contain a heme group and use electrons "
        "supplied by NADPH through cytochrome P450 "
        "oxidoreductase (POR). These electrons help "
        "activate molecular oxygen and catalyze "
        "oxidation reactions including hydroxylation "
        "and dealkylation. Such reactions often alter "
        "a compound's solubility and biological activity. "
        "They do not necessarily reduce toxicity: "
        "some metabolites are more reactive or toxic "
        "than their parent compounds. CYP metabolism "
        "is particularly prominent in hepatocytes.",
        "ser_detoxification",
        [
            "ser_cyp450_enzyme",
            "ser_p450_reductase",
            "ser_cyp_reaction",
        ],
        ["nadph", "oxygen"]
    ),
    
    "ser_cyp450_enzyme": _component(
        "Cytochrome P450 enzyme",
        "HEME MONOOXYGENASE · SUBSTRATE OXIDATION",
        "Cytochrome P450 enzymes are heme-containing "
        "monooxygenases. Many mammalian CYP enzymes "
        "are associated with the endoplasmic reticulum "
        "and catalyze metabolism of drugs and other "
        "small molecules. Their catalytic iron changes "
        "oxidation state as electrons and oxygen "
        "participate in the reaction cycle. "
        "The heme prosthetic group is essential for "
        "oxygen activation. CYP3A4 is one important "
        "human enzyme that metabolizes numerous drugs. "
        "Different CYP isoforms have overlapping "
        "but distinct substrate preferences.",
        "protein_complex",
        (),
        [
            "protein_cyp3a4",
            "heme_b",
            "oxygen",
        ]
    ),

    "ser_p450_reductase": _component(
        "NADPH-cytochrome P450 reductase",
        "POR · ELECTRON TRANSFER",
        "NADPH-cytochrome P450 reductase (POR) is an "
        "ER membrane-associated flavoprotein that "
        "transfers electrons from NADPH to many "
        "microsomal cytochrome P450 enzymes. "
        "The electrons pass through FAD and FMN "
        "cofactors in the reductase before "
        "reaching the CYP heme iron. "
        "These electron-transfer steps support "
        "oxygen activation and substrate oxidation. "
        "POR is distinct from the CYP enzyme itself.",
        "protein_complex",
        (),
        [
            "protein_por",
            "nadph",
            "fad",
            "fmn",
        ]
    ),

    "ser_cyp_reaction": _component(
        "Cytochrome P450 oxidation reaction",
        "PHASE I METABOLISM · HYDROXYLATION",
        "Many CYP enzymes catalyze monooxygenation: "
        "one oxygen atom from molecular oxygen is "
        "incorporated into a substrate, while the "
        "other is reduced to water. "
        "The reaction consumes reducing equivalents "
        "supplied by NADPH. As an illustrative "
        "reaction, CYP2E1 can oxidize benzene "
        "through a reactive benzene oxide "
        "intermediate, yielding phenol among "
        "its products. This example demonstrates "
        "why CYP metabolism is not always "
        "detoxifying, because benzene metabolism "
        "can also generate harmful intermediates. "
        "Different substrates and CYP enzymes "
        "produce many other types of products.",
        "protein_complex",
        (),
        [
            "protein_cyp2e1",
            "benzene",
            "phenol",
            "oxygen",
            "nadph",
        ]
    ),


    "cis_cisternae": _component("Cis Golgi cisternae", "MEMBRANE COMPARTMENT", "The receiving side of the Golgi accepts cargo from the ER.", "stack", ["golgi_membrane"], ["phosphatidylcholine"]),
    "medial_cisternae": _component("Medial Golgi cisternae", "MEMBRANE COMPARTMENT", "Middle Golgi compartments perform additional processing, including steps in glycan modification.", "stack", ["golgi_membrane"]),
    "trans_cisternae": _component("Trans Golgi cisternae", "MEMBRANE COMPARTMENT", "The shipping side of the Golgi sorts processed cargo into transport vesicles.", "stack", ["golgi_vesicles"], ["phosphatidylcholine"]),
    "golgi_vesicles": _component("Golgi transport vesicles", "TRANSPORT VESICLES", "Vesicles carry processed cargo from the Golgi to destinations such as the plasma membrane or lysosome.", "vesicle", ["vesicle_membrane", "vesicle_cargo"], ["phosphatidylcholine"]),
    "golgi_membrane": _component("Golgi membrane", "LIPID BILAYER", "Golgi cisternae are enclosed by membranes that support cargo processing and transport.", "membrane", (), ["phosphatidylcholine", "phosphatidylethanolamine", "cholesterol"]),
    "lysosome_membrane": _component("Lysosome membrane", "LIPID BILAYER + PUMPS", "A membrane separates digestive enzymes from the cytosol and pumps protons into the lumen to maintain acidity.", "membrane", ["lysosome_lumen"], ["phosphatidylcholine", "cholesterol"]),
    "lysosome_lumen": _component("Lysosome lumen", "ACIDIC COMPARTMENT", "The low-pH interior is optimized for lysosomal digestive enzymes.", "compartment", ["acid_hydrolases"], ["water"]),
    "acid_hydrolases": _component("Acid hydrolases", "DIGESTIVE ENZYMES", "These enzymes break down proteins, nucleic acids, lipids, and carbohydrates in the acidic lysosome.", "protein_complex", (), ["glycine", "alanine"]),
    "lysosome_cargo": _component("Recycling cargo", "MOLECULAR BREAKDOWN", "Cell material is broken down into reusable building blocks.", "pathway", (), ["glucose", "glycine", "adenine"]),
    "peroxisome_membrane": _component("Peroxisome membrane", "LIPID BILAYER", "A single membrane encloses peroxisomal oxidative enzymes.", "membrane", (), ["phosphatidylcholine", "phosphatidylethanolamine"]),
    "peroxisome_matrix": _component("Peroxisome matrix", "ENZYME COMPARTMENT", "The lumen contains enzymes for oxidation and peroxide handling.", "compartment", ["catalase", "fatty_acid_oxidation"], ["oxygen", "water"]),
    "catalase": _component("Catalase", "ENZYME", "Catalase converts hydrogen peroxide into water and oxygen, helping protect the cell from oxidative damage.", "protein_complex", (), ["oxygen", "water"]),
    "fatty_acid_oxidation": _component("Fatty-acid oxidation", "METABOLIC PROCESS", "Peroxisomal enzymes shorten certain very-long-chain fatty acids through oxidation reactions.", "pathway", (), ["oxygen", "water"]),
    "vesicle_membrane": _component("Vesicle membrane", "LIPID BILAYER", "A closed phospholipid bilayer packages cargo and controls fusion with target membranes.", "membrane", ["membrane_cholesterol"], ["phosphatidylcholine", "phosphatidylethanolamine", "cholesterol"]),
    "vesicle_cargo": _component("Vesicle cargo", "TRANSPORTED MATERIAL", "Cargo may include proteins, membrane lipids, signaling molecules, or material being delivered for digestion.", "compartment", (), ["glucose", "water"]),
    "coat_proteins": _component("Coat proteins", "PROTEIN ASSEMBLY", "Coat proteins help deform a donor membrane and select cargo during vesicle budding.", "protein_complex"),
    "fusion_proteins": _component("Membrane-fusion proteins", "PROTEIN MACHINERY", "Specific fusion proteins help a vesicle recognize and merge with the correct target membrane.", "protein_complex"),
    "actin_filament": _component("Actin filament", "PROTEIN POLYMER", "Actin subunits assemble into dynamic filaments that support cell shape and movement.", "filament", ["actin_subunit"], ["glycine", "alanine"]),
    "microtubule": _component("Microtubule", "PROTEIN TUBE", "Tubulin proteins assemble into hollow tracks used for cell organization and cargo transport.", "filament", ["tubulin_subunit"], ["glycine", "alanine"]),
    "intermediate_filament": _component("Intermediate filament", "PROTEIN CABLE", "Rope-like protein polymers provide mechanical strength to cells and tissues.", "filament", ["intermediate_filament_proteins"], ["glycine", "serine"]),
    "motor_proteins": _component("Motor proteins", "MOLECULAR MOTORS", "Motor proteins use chemical energy to move cargo along cytoskeletal filaments.", "protein_complex", (), ["atp"]),
    "actin_subunit": _component("Actin subunit", "PROTEIN SUBUNIT", "Globular actin monomers assemble into a helical filament.", "protein_complex", (), ["glycine", "alanine", "serine"]),
    "tubulin_subunit": _component("Tubulin subunit", "PROTEIN SUBUNIT", "Alpha- and beta-tubulin form repeating dimers that build a microtubule wall.", "protein_complex", (), ["glycine", "alanine", "serine"]),
    "intermediate_filament_proteins": _component("Intermediate-filament proteins", "PROTEIN SUBUNITS", "Long fibrous proteins assemble into strong, rope-like filaments.", "protein_complex", (), ["glycine", "alanine", "serine"]),
    "centriole_pair": _component("Centriole pair", "MICROTUBULE ARRANGEMENT", "Two barrel-shaped centrioles help organize microtubules in many animal cells.", "centrosome", ["centrosome_microtubules", "tubulin_subunit"]),
    "centrosome_microtubules": _component("Centrosomal microtubules", "PROTEIN POLYMERS", "Microtubules are nucleated and organized around the centrosome.", "filament", ["tubulin_subunit"], ["glycine", "alanine"]),
    "pericentriolar_material": _component("Pericentriolar material", "PROTEIN MATRIX", "A protein-rich matrix around centrioles helps nucleate and anchor microtubules.", "protein_complex", (), ["glycine", "serine"]),
    "plasma_bilayer": _component("Plasma-membrane bilayer", "MEMBRANE COMPOSITION", "Amphipathic lipids arrange with water-facing heads and inward-facing tails. Select a lipid to inspect its actual structure within the bilayer.", "membrane", (), ["phosphatidylcholine", "phosphatidylethanolamine", "cholesterol"]),
    "membrane_proteins": _component("Membrane proteins", "PROTEIN MACHINERY", "Membrane proteins form channels, receptors, pumps, and anchors within the lipid bilayer.", "protein_complex", ["membrane_channel", "membrane_receptor"]),
    "glycocalyx": _component("Glycocalyx", "EXTRACELLULAR SUGAR LAYER", "The cell's outward-facing sugar coat consists of carbohydrate chains attached to membrane proteins and lipids. It supports cell recognition, adhesion, and protection.", "carbohydrate_layer", (), ["glucose"]),
    "aquaporin_1": _component("Aquaporin-1 (AQP1)", "HOMOTETRAMERIC WATER CHANNEL", "AQP1 assembles from four identical protomers. Each subunit forms its own water-selective pore; water moves passively down its osmotic gradient.", "aquaporin_tetramer"),
    "nicotinic_acetylcholine_receptor": _component("Adult muscle nicotinic acetylcholine receptor", "LIGAND-GATED CATION CHANNEL", "The adult skeletal-muscle receptor is a heteropentamer containing two alpha-1 subunits plus beta-1, delta, and epsilon subunits. Acetylcholine binds at two alpha-subunit interfaces to open the central cation channel.", "nachr_pentamer", (), ["acetylcholine"]),
    "glut1": _component("GLUT1 (SLC2A1)", "12-HELIX GLUCOSE TRANSPORTER", "GLUT1 is a single polypeptide with 12 transmembrane alpha helices arranged as two six-helix bundles. It carries glucose by alternating-access facilitated diffusion; it is not a pump or an open channel.", "glut1_transporter"),
    "membrane_cholesterol": _component("Membrane cholesterol", "STEROID LIPID", "Cholesterol fits between lipid tails and affects membrane packing and fluidity.", "molecule", (), ["cholesterol"]),
    "membrane_channel": _component("Membrane channel", "TRANSPORT PROTEIN", "A selective protein pore allows particular ions or molecules to cross the membrane.", "protein_complex"),
    "membrane_receptor": _component("Membrane receptor", "SIGNALING PROTEIN", "Receptors bind external signals and transmit information to the cell interior.", "protein_complex"),
    "cytosol_water": _component("Water in cytosol", "SOLVENT", "Water is the main solvent in which ions, metabolites, and proteins move and react.", "molecule", (), ["water"]),
    "cytosol_ions": _component("Dissolved cytosolic ions", "IONS IN SOLUTION", "Potassium, sodium, magnesium, and chloride ions remain dissolved in water. Their concentrations contribute to osmotic balance, electrical properties, and enzyme activity.", "cytosol", (), ["sodium", "potassium", "magnesium", "chloride"]),
    "cytosol_metabolites": _component("Cytosolic metabolites", "SMALL MOLECULES", "Small molecules such as glucose, pyruvate, ADP, ATP, and phosphate diffuse through cytosol and participate in cellular reactions.", "cytosol", (), ["glucose", "pyruvate", "adp", "atp", "phosphate"]),
    "glycolysis": _component("Glycolysis", "METABOLIC PATHWAY", "In the cytosol, glucose is converted through a series of reactions to pyruvate, producing ATP and NADH.", "pathway", (), ["glucose", "pyruvate", "atp"]),
    "atp_synthase_f0": _component("F₀ membrane motor", "PROTON CHANNEL", "The membrane-embedded F₀ portion provides a proton path and rotates as protons flow through.", "protein_complex"),
    "atp_synthase_f1": _component("F₁ catalytic head", "ATP-FORMING ENZYME", "The F₁ head changes shape during rotation and catalyzes ATP formation from ADP and phosphate.", "protein_complex", (), ["adp", "phosphate", "atp"]),
    "complex_i": _component("Complex I", "RESPIRATORY COMPLEX", "NADH transfers electrons to Complex I, which passes them to CoQ and pumps protons across the inner membrane.", "protein_complex", (), ["coq"]),
    "coq": _component("Coenzyme Q", "MOBILE ELECTRON CARRIER", "Lipid-soluble CoQ carries electrons from Complex I and II to Complex III within the membrane.", "molecule", (), ["oxygen"]),
    "complex_iii": _component("Complex III", "RESPIRATORY COMPLEX", "Complex III transfers electrons from reduced CoQ to cytochrome c and contributes to proton translocation.", "protein_complex", (), ["coq"]),
    "complex_iv": _component("Complex IV", "RESPIRATORY COMPLEX", "Complex IV transfers electrons to oxygen, forming water, and pumps protons across the inner membrane.", "protein_complex", (), ["oxygen", "water"]),
    "pyruvate_oxidation": _component("Pyruvate oxidation", "METABOLIC PATHWAY", "Pyruvate is converted to acetyl-CoA, releasing carbon dioxide and producing NADH.", "pathway", (), ["pyruvate"]),
}


MOLECULES = [
    {
        "id": "phosphatidylcholine",
        "name": "Phosphatidylcholine",
        "role": "A common phospholipid that contributes to membrane structure.",
        "smiles": "CCCCCCCCCCCCCCCC(=O)OCC(COP(=O)([O-])OCC[N+](C)(C)C)OC(=O)CCCCCCCCCCCCCCC",
    },
    {
        "id": "phosphatidylethanolamine",
        "name": "Phosphatidylethanolamine",
        "role": "A phospholipid found in cellular membranes, including the inner mitochondrial membrane.",
        "smiles": "CCCCCCCCCCCCCCCC(=O)OCC(COP(=O)([O-])OCCN)OC(=O)CCCCCCCCCCCCCCC",
    },
    {
        "id": "sphingomyelin",
        "name": "Sphingomyelin",
        "role": "A sphingophospholipid enriched in the outer leaflet of many animal-cell plasma membranes.",
        "smiles": "CCCCCCCCCCCCCCCC(=O)N[C@@H](CO[P](=O)([O-])OCC[N+](C)(C)C)[C@H](O)/C=C/CCCCCCCCCCCCC",
    },
    {
        "id": "phosphatidylserine",
        "name": "Phosphatidylserine",
        "role": "An anionic phospholipid enriched on the cytosolic leaflet of the plasma membrane.",
        "smiles": "CCCCCCCCCCCCCCCC(=O)OCC(COP(=O)([O-])OC[C@@H]([NH3+])C(=O)[O-])OC(=O)CCCCCCCCCCCCCCC",
    },
    {
        "id": "phosphatidylinositol",
        "name": "Phosphatidylinositol",
        "role": "A low-abundance inner-leaflet phospholipid that is the precursor of signaling phosphoinositides.",
        "smiles": "CCCCCCCCCCCCCCCC(=O)OCC(COP(=O)(O)OC1C(O)C(O)C(O)C(O)C1O)OC(=O)CCCCCCCCCCCCCCC",
    },
    {
        "id": "pip2",
        "name": "Phosphatidylinositol 4,5-bisphosphate (PIP₂)",
        "role": "A signaling phosphoinositide concentrated on the inner leaflet of the plasma membrane.",
        "smiles": "CCCCCCCCCCCCCCCC(=O)OCC(COP(=O)(O)OC1C(O)C(OP(=O)(O)O)C(OP(=O)(O)O)C(O)C1O)OC(=O)CCCCCCCCCCCCCCC",
    },
    {
        "id": "cardiolipin",
        "name": "Cardiolipin",
        "role": "A distinctive mitochondrial phospholipid with four acyl chains that helps organize inner-membrane proteins.",
        "smiles": "CCCCCCCCCCCCCCC(=O)OCC(OC(=O)CCCCCCCCCCCCCCC)COP(=O)(O)OCC(O)COP(=O)(O)OCC(OC(=O)CCCCCCCCCCCCCCC)COC(=O)CCCCCCCCCCCCCCC",
    },
    {
        "id": "cholesterol",
        "name": "Cholesterol",
        "role": "A sterol that tunes membrane packing; it is much less abundant in the inner mitochondrial membrane than in the plasma membrane.",
        "smiles": "CC(C)CCCC(C)C1CCC2C3CCC4=CC(CCC4(C3CCC12C)C)O",
    },
    {
        "id": "glucose",
        "name": "Glucose",
        "role": "A six-carbon sugar that can be broken down through glycolysis to help supply cellular energy.",
        "smiles": "C([C@@H]1[C@H]([C@@H]([C@H](C(O1)O)O)O)O)O",
    },
    {
        "id": "glucose_6_phosphate",
        "name": "Glucose-6-phosphate",
        "role": "The first phosphorylated intermediate in glycolysis, formed when glucose receives a phosphate from ATP.",
        "smiles": "C([C@@H]1[C@H]([C@@H]([C@H](C(O1)O)O)O)O)OP(=O)(O)O",
    },
    {
        "id": "fructose_6_phosphate",
        "name": "Fructose-6-phosphate",
        "role": "A six-carbon sugar phosphate formed from glucose-6-phosphate before the second ATP-investment step of glycolysis.",
        "smiles": "OCC(=O)C(O)C(O)C(O)COP(=O)(O)O",
    },
    {
        "id": "fructose_1_6_bisphosphate",
        "name": "Fructose-1,6-bisphosphate",
        "role": "The six-carbon bisphosphate formed when phosphofructokinase uses ATP; aldolase splits it into two three-carbon molecules.",
        "smiles": "OP(=O)(O)OCC(=O)C(O)C(O)C(O)COP(=O)(O)O",
    },
    {
        "id": "dihydroxyacetone_phosphate",
        "name": "Dihydroxyacetone phosphate (DHAP)",
        "role": "A three-carbon glycolysis intermediate converted into glyceraldehyde-3-phosphate.",
        "smiles": "OCC(=O)COP(=O)(O)O",
    },
    {
        "id": "glyceraldehyde_3_phosphate",
        "name": "Glyceraldehyde-3-phosphate (G3P)",
        "role": "A three-carbon glycolysis intermediate oxidized to help produce NADH and ATP.",
        "smiles": "O=C[C@H](O)COP(=O)(O)O",
    },
    {
        "id": "1_3_bisphosphoglycerate",
        "name": "1,3-Bisphosphoglycerate",
        "role": "A high-energy three-carbon intermediate that transfers phosphate to ADP to make ATP during glycolysis.",
        "smiles": "O=C(OP(=O)(O)O)C(O)COP(=O)(O)O",
    },
    {
        "id": "3_phosphoglycerate",
        "name": "3-Phosphoglycerate",
        "role": "A three-carbon glycolysis intermediate formed when 1,3-bisphosphoglycerate transfers phosphate to ADP.",
        "smiles": "O=C(O)C(O)COP(=O)(O)O",
    },
    {
        "id": "2_phosphoglycerate",
        "name": "2-Phosphoglycerate",
        "role": "A three-carbon glycolysis intermediate formed from 3-phosphoglycerate before water is released.",
        "smiles": "O=C(O)C(OP(=O)(O)O)CO",
    },
    {
        "id": "phosphoenolpyruvate",
        "name": "Phosphoenolpyruvate (PEP)",
        "role": "A high-energy glycolysis intermediate that transfers phosphate to ADP to make ATP and pyruvate.",
        "smiles": "O=C(O)C(=C)OP(=O)(O)O",
    },
    {
        "id": "acetylcholine",
        "name": "Acetylcholine",
        "role": "A neurotransmitter that binds nicotinic acetylcholine receptors and opens their cation channel.",
        "smiles": "CC(=O)OCC[N+](C)(C)C",
    },
    {
        "id": "pyruvate",
        "name": "Pyruvate",
        "role": "The product of glycolysis that can be converted to acetyl-CoA before the citric acid cycle.",
        "smiles": "CC(=O)C(=O)[O-]",
    },

    {
        "id": "water",
        "name": "Water",
        "role": "A product released when enolase converts 2-phosphoglycerate to phosphoenolpyruvate, and the main solvent of the cell interior.",
        "smiles": "O",
    },
    {"id": "sodium", "name": "Sodium ion", "role": "A dissolved extracellularly enriched cation that contributes to membrane potential and transport gradients.", "smiles": "[Na+]"},
    {"id": "potassium", "name": "Potassium ion", "role": "The principal intracellular cation in many animal cells; its gradient is maintained by membrane transporters.", "smiles": "[K+]"},
    {"id": "magnesium", "name": "Magnesium ion", "role": "A common cytosolic ion that associates with ATP and supports the activity of many enzymes.", "smiles": "[Mg+2]"},
    {"id": "chloride", "name": "Chloride ion", "role": "A dissolved anion involved in charge balance, cell volume, and membrane transport.", "smiles": "[Cl-]"},
    {
        "id": "adp",
        "name": "Adenosine diphosphate (ADP)",
        "role": "The lower-energy nucleotide that gains a phosphate group during ATP synthesis.",
        "smiles": "Nc1ncnc2c1ncn2[C@@H]1O[C@H](COP(=O)(O)OP(=O)(O)O)[C@@H](O)[C@H]1O",
    },
    {
        "id": "phosphate",
        "name": "Inorganic phosphate (Pi)",
        "role": "The phosphate group joined to ADP to form ATP.",
        "smiles": "OP(=O)(O)O",
    },
    {
        "id": "atp",
        "name": "Adenosine triphosphate (ATP)",
        "role": "A widely used cellular energy-transfer molecule made by ATP synthase.",
        "smiles": "Nc1ncnc2c1ncn2[C@@H]1O[C@H](COP(=O)(O)OP(=O)(O)OP(=O)(O)O)[C@@H](O)[C@H]1O",
    },
    {
        "id": "nad_plus",
        "name": "Nicotinamide adenine dinucleotide (NAD⁺)",
        "role": "The oxidized electron carrier that accepts electrons during glycolysis to form NADH.",
        "smiles": "C1=CC(=C[N+](=C1)[C@H]2[C@@H]([C@@H]([C@H](O2)COP(=O)([O-])OP(=O)(O)OC[C@@H]3[C@H]([C@H]([C@@H](O3)N4C=NC5=C(N=CN=C54)N)O)O)O)O)C(=O)N",
    },
    {
        "id": "nadh",
        "name": "Reduced NAD (NADH)",
        "role": "The reduced electron carrier produced when NAD⁺ accepts electrons during glycolysis.",
        "smiles": "C1C=CN(C=C1C(=O)N)[C@H]2[C@@H]([C@@H]([C@H](O2)COP(=O)(O)OP(=O)(O)OC[C@@H]3[C@H]([C@H]([C@@H](O3)N4C=NC5=C(N=CN=C54)N)O)O)O)O",
    },
    {"id": "coq", "name": "Ubiquinone-0 (CoQ head-group model)", "role": "This short-chain ubiquinone model shows the redox-active quinone head group. Mitochondrial coenzyme Q also has a long isoprenoid tail that anchors it in the membrane.", "smiles": "COC1=C(OC)C(=O)C(C)=CC1=O"},
    {"id": "adenine", "name": "Adenine", "role": "A purine nucleobase found in DNA and RNA.", "smiles": "Nc1ncnc2[nH]cnc12"},
    {"id": "guanine", "name": "Guanine", "role": "A purine nucleobase found in DNA and RNA.", "smiles": "Nc1nc2[nH]cnc2c(=O)[nH]1"},
    {"id": "cytosine", "name": "Cytosine", "role": "A pyrimidine nucleobase found in DNA and RNA.", "smiles": "Nc1ncc(=O)[nH]c1"},
    {"id": "thymine", "name": "Thymine", "role": "A pyrimidine nucleobase used in DNA.", "smiles": "CC1=CNC(=O)NC1=O"},
    {"id": "uracil", "name": "Uracil", "role": "A pyrimidine nucleobase used in RNA in place of thymine.", "smiles": "O=c1cc[nH]c(=O)[nH]1"},
    {"id": "glycine", "name": "Glycine", "role": "The smallest amino acid and one of the building blocks of proteins.", "smiles": "NCC(=O)O"},
    {"id": "alanine", "name": "Alanine", "role": "A protein-building amino acid with a methyl side chain.", "smiles": "C[C@H](N)C(=O)O"},
    {"id": "serine", "name": "Serine", "role": "A protein-building amino acid with a hydroxymethyl side chain.", "smiles": "N[C@@H](CO)C(=O)O"},
        {
        "id": "pseudouridine",
        "name": "Pseudouridine (Ψ)",
        "role": "A modified uridine isomer that is especially important in ribosomal RNA. Pseudouridine helps stabilize local RNA structure and can improve hydrogen-bonding interactions within folded rRNA.",
        "smiles": "C1=C(C(=O)NC(=O)N1)[C@H]2[C@@H]([C@@H]([C@H](O2)CO)O)O",
    },
    {
        "id": "o2_methylguanosine",
        "name": "2′-O-Methylguanosine (Gm)",
        "role": "A guanosine residue modified by methylation at the ribose 2′-oxygen. In rRNA, 2′-O-methylation helps tune RNA folding, stability, and ribosome function.",
        "smiles": "CO[C@@H]1[C@@H]([C@H](O[C@H]1N2C=NC3=C2N=C(NC3=O)N)CO)O",
    },
    {
        "id": "dimethyladenosine_m66",
        "name": "N6,N6-Dimethyladenosine (m6,6A)",
        "role": "A dimethylated adenosine found in eukaryotic small-subunit rRNA. This modification is associated with 18S rRNA maturation and the functional organization of the decoding subunit.",
        "smiles": "CN(C)C1=NC=NC2=C1N=CN2[C@H]3[C@@H]([C@@H]([C@H](O3)CO)O)O",
    },
    {
        "id": "o2_methylcytidine",
        "name": "2′-O-Methylcytidine (Cm)",
        "role": "A cytidine residue with methylation at the ribose 2′-oxygen. In ribosomal RNA, this type of modification helps stabilize local structure and supports correct ribosome assembly and function.",
        "smiles": "CO[C@@H]1[C@@H]([C@H](O[C@H]1N2C=CC(=NC2=O)N)CO)O",
    },
    
    {
        "id": "protein_ul3",
        "name": "uL3 (RPL3)",
        "role": "A conserved large-subunit ribosomal protein with extensive contacts to 28S rRNA. It contributes to the structural organization of the peptidyl-transferase-center region and supports large-subunit function.",
        "type": "protein",
    },
    {
        "id": "protein_ul4",
        "name": "uL4 (RPL4)",
        "role": "A conserved protein of the 60S subunit that helps form the architecture of the nascent polypeptide exit tunnel. Its extended regions interact with the large-subunit rRNA.",
        "type": "protein",
    },
    {
        "id": "protein_ul22",
        "name": "uL22 (RPL17)",
        "role": "A conserved 60S ribosomal protein associated with the polypeptide exit tunnel. Together with other proteins and rRNA, it contributes to the environment through which newly synthesized polypeptides pass.",
        "type": "protein",
    },
    {
        "id": "protein_el24",
        "name": "eL24 (RPL24)",
        "role": "A eukaryote-specific 60S ribosomal protein that participates in large-subunit architecture and ribosome biogenesis. It associates with the rRNA-protein framework of the mature large subunit.",
        "type": "protein",
    },
    {
        "id": "protein_us3",
        "name": "uS3 (RPS3)",
        "role": "A conserved small-subunit ribosomal protein located near the mRNA entry channel. It contributes to mRNA interactions and the structural organization of the 40S subunit.",
        "type": "protein",
    },
    {
        "id": "protein_us5",
        "name": "uS5 (RPS2)",
        "role": "A conserved 40S ribosomal protein that interacts with small-subunit rRNA and contributes to the architecture needed for accurate translation.",
        "type": "protein",
    },
    {
        "id": "protein_us7",
        "name": "uS7 (RPS5)",
        "role": "A conserved small-subunit ribosomal protein involved in organizing the ribosomal head region and supporting interactions important for mRNA decoding.",
        "type": "protein",
    },
    {
        "id": "protein_es6",
        "name": "eS6 (RPS6)",
        "role": "A eukaryote-specific 40S ribosomal protein that undergoes regulated phosphorylation and is linked to signaling pathways controlling cellular growth and protein synthesis.",
        "type": "protein",
    },


    {
        "id": "m7_guanosine",
        "name": "7-Methylguanosine (m7G)",
        "role": "A guanosine modified by methylation at nitrogen 7. "
                "It forms the characteristic modified nucleoside "
                "of the eukaryotic mRNA 5' cap. The complete cap "
                "contains a 5'-5' triphosphate linkage connecting "
                "m7G to the RNA chain. This drawing shows the "
                "modified nucleoside, not the entire cap.",
        "smiles": "CN1C=[N+](C2=C1C(=O)NC(=N2)N)[C@H]3[C@@H]([C@@H]([C@H](O3)CO)O)O",
    },
    {
        "id": "m6_adenosine",
        "name": "N6-Methyladenosine (m6A)",
        "role": "An adenosine modified by a single methyl group "
                "on the exocyclic nitrogen at position 6 of adenine. "
                "It is a common internal mRNA modification that can "
                "affect RNA stability, processing and translation "
                "through interactions with specialized reader proteins.",
        "smiles": "CNC1=C2C(=NC=N1)N(C=N2)[C@H]3[C@@H]([C@@H]([C@H](O3)CO)O)O",
    },
    {
        "id": "adenosine",
        "name": "Adenosine",
        "role": "A ribonucleoside composed of adenine attached "
                "to ribose. Repeated adenosine residues form "
                "the poly(A) tail found at the 3' end of many "
                "eukaryotic mRNAs. The actual poly(A) tail contains "
                "nucleotides connected by phosphodiester bonds.",
        "smiles": "C1=NC(=C2C(=N1)N(C=N2)[C@H]3[C@@H]([C@@H]([C@H](O3)CO)O)O)N",
    },

    {
        "id": "protein_eif4e",
        "name": "eIF4E · Cap-binding protein",
        "role": "Eukaryotic translation initiation factor 4E "
                "(eIF4E) recognizes the 7-methylguanosine-containing "
                "cap at the 5' end of many eukaryotic mRNAs. "
                "It forms part of the eIF4F initiation complex "
                "and helps recruit translation initiation machinery "
                "to the mRNA.",
        "type": "protein",
    },
    {
        "id": "protein_pabpc1",
        "name": "PABPC1 · Poly(A)-binding protein",
        "role": "Cytoplasmic poly(A)-binding protein 1 "
                "(PABPC1) binds the polyadenylated 3' tail "
                "of many eukaryotic mRNAs. It helps regulate "
                "mRNA stability and translation. Through "
                "interactions involving eIF4G, it can contribute "
                "to functional communication between the "
                "5' cap and 3' poly(A) tail.",
        "type": "protein",
    },

    {
        "id": "glutamate",
        "name": "L-Glutamate",
        "role": "The amino acid specified by the mRNA codon GAA. "
                "Before delivery to the ribosome, glutamate is "
                "attached to the terminal adenosine of its "
                "corresponding tRNA by glutamyl-tRNA synthetase. "
                "The structure shown represents the free amino acid, "
                "not the complete charged tRNA.",
        "smiles": "N[C@@H](CCC(=O)O)C(=O)O",
    },
    {
        "id": "nascent_peptide_ala_phe",
        "name": "Alanyl-phenylalanine (Ala-Phe)",
        "role": "A short dipeptide illustrating a fragment of a "
                "nascent polypeptide. During translation, the growing "
                "chain remains ester-linked to the terminal adenosine "
                "of peptidyl-tRNA until transfer to the A-site "
                "amino acid. This structure shows the isolated peptide.",
        "smiles": "C[C@@H](N)C(=O)N[C@@H](Cc1ccccc1)C(=O)O",
    },
    {
        "id": "protein_eef2",
        "name": "eEF2 · Elongation Factor 2",
        "role": "A GTP-dependent elongation factor that promotes "
                "ribosomal translocation. It facilitates movement "
                "of peptidyl-tRNA toward the P site and deacylated "
                "tRNA toward the E site. It interacts transiently "
                "with the ribosome rather than remaining permanently "
                "bound to the E site.",
        "type": "protein",
    },
    {
        "id": "protein_eif5a",
        "name": "eIF5A · Translation Factor",
        "role": "A translation factor that assists difficult "
                "peptide-bond formation events, particularly during "
                "polyproline synthesis. It binds near the E-site "
                "region and contains the unusual modified "
                "amino acid hypusine.",
        "type": "protein",
    },
    {
        "id": "protein_eef1a",
        "name": "eEF1A · Elongation Factor 1A",
        "role": "A GTP-binding elongation factor that delivers "
                "aminoacyl-tRNA to the ribosomal A site. Correct "
                "codon-anticodon recognition promotes GTP hydrolysis "
                "and accommodation of the charged tRNA.",
        "type": "protein",
    },
    {
        "id": "protein_ears1",
        "name": "EARS1 · Glutamyl-tRNA Synthetase",
        "role": "An enzyme that uses ATP to attach glutamate to "
                "its corresponding cytosolic tRNA before translation. "
                "The resulting glutamyl-tRNA can subsequently "
                "be delivered to the ribosomal A site.",
        "type": "protein",
    },
    
    {
        "id": "protein_sec61_alpha",
        "name": "Sec61 alpha (SEC61A1)",
        "role": "The pore-forming subunit of the Sec61 "
                "translocon. It contains ten transmembrane "
                "helices and provides a regulated pathway "
                "for nascent polypeptides to cross the "
                "ER membrane. Its lateral gate allows "
                "hydrophobic protein segments to enter "
                "the surrounding lipid bilayer.",
        "type": "protein",
    },
    {
        "id": "protein_sr_alpha",
        "name": "SRalpha (SRPR)",
        "role": "The alpha subunit of the signal recognition "
                "particle receptor. It is a GTP-binding "
                "protein that interacts with SRP during "
                "targeting of nascent proteins to the "
                "endoplasmic reticulum membrane.",
        "type": "protein",
    },
    {
        "id": "protein_sr_beta",
        "name": "SRbeta (SRPRB)",
        "role": "The membrane-anchored beta subunit of the "
                "signal recognition particle receptor. "
                "It is a GTP-binding protein that helps "
                "associate the receptor with the ER membrane "
                "and participates in protein targeting.",
        "type": "protein",
    },
    {
        "id": "protein_stt3a",
        "name": "STT3A",
        "role": "A catalytic subunit of one form of the "
                "oligosaccharyltransferase complex. "
                "STT3A-containing OST operates closely "
                "with the protein translocation machinery "
                "and transfers N-linked oligosaccharides "
                "to suitable sites during translation.",
        "type": "protein",
    },
    {
        "id": "protein_stt3b",
        "name": "STT3B",
        "role": "A catalytic subunit of an alternative "
                "oligosaccharyltransferase complex. "
                "STT3B-containing OST can glycosylate "
                "certain protein sites missed during "
                "the initial cotranslational process.",
        "type": "protein",
    },
    
    {
        "id": "calcium",
        "name": "Calcium ion (Ca²⁺)",
        "role": "A divalent calcium ion stored at relatively high "
                "concentrations in the ER lumen compared with "
                "the resting cytosol. Calcium supports "
                "intracellular signaling and the functions "
                "of several ER proteins.",
        "smiles": "[Ca+2]",
    },
    {
        "id": "cysteine",
        "name": "L-Cysteine",
        "role": "A sulfur-containing amino acid with a reactive "
                "thiol (-SH) group. Pairs of cysteine residues "
                "can undergo oxidation to form stabilizing "
                "disulfide bonds within or between proteins.",
        "smiles": "N[C@@H](CS)C(=O)O",
    },
    {
        "id": "cystine",
        "name": "L-Cystine",
        "role": "Two cysteine molecules connected by a "
                "disulfide (S-S) bond. It provides a simple "
                "chemical model for disulfide linkages "
                "in folded proteins.",
        "smiles": "N[C@@H](CSSC[C@H](N)C(=O)O)C(=O)O",
    },
    {
        "id": "glutathione",
        "name": "Reduced glutathione (GSH)",
        "role": "A tripeptide made from glutamate, cysteine "
                "and glycine. Its cysteine thiol participates "
                "in cellular redox chemistry. Reduced and "
                "oxidized glutathione are involved in "
                "the redox environment associated with "
                "protein folding in the ER.",
        "smiles": "N[C@@H](CCC(=O)N[C@@H](CS)C(=O)NCC(=O)O)C(=O)O",
    },
    {
        "id": "protein_bip",
        "name": "BiP (HSPA5 / GRP78)",
        "role": "An ATP-dependent Hsp70-family molecular "
                "chaperone of the ER lumen. BiP recognizes "
                "exposed regions of incompletely folded "
                "proteins and helps prevent aggregation.",
        "type": "protein",
    },
    {
        "id": "protein_pdi",
        "name": "Protein disulfide isomerase (P4HB)",
        "role": "An ER oxidoreductase that catalyzes "
                "formation, reduction and rearrangement "
                "of disulfide bonds during oxidative "
                "protein folding.",
        "type": "protein",
    },
    {
        "id": "protein_calnexin",
        "name": "Calnexin (CANX)",
        "role": "An ER membrane-associated lectin "
                "chaperone that recognizes specific "
                "monoglucosylated N-linked glycans "
                "and assists glycoprotein folding.",
        "type": "protein",
    },
    {
        "id": "protein_calreticulin",
        "name": "Calreticulin (CALR)",
        "role": "A soluble ER luminal lectin chaperone "
                "that assists glycoprotein folding "
                "and also functions as a major "
                "calcium-binding protein.",
        "type": "protein",
    },
    {
        "id": "protein_edem1",
        "name": "EDEM1",
        "role": "An ER quality-control protein involved "
                "in processing and recognition of "
                "certain misfolded glycoproteins "
                "for ER-associated degradation.",
        "type": "protein",
    },
    
    {
        "id": "n_acetylglucosamine",
        "name": "N-Acetyl-D-glucosamine (GlcNAc)",
        "role": "An amino sugar containing an acetylated "
                "amino group at carbon 2. Two GlcNAc "
                "residues form the conserved core "
                "linking an N-linked glycan to a "
                "protein's asparagine residue. "
                "This RDKit image shows the free "
                "monosaccharide, not the complete "
                "protein-bound glycan.",
        "smiles": "CC(=O)N[C@@H]1[C@H]([C@@H]([C@H](OC1O)CO)O)O",
    },
    {
        "id": "mannose",
        "name": "D-Mannose (Man)",
        "role": "A six-carbon monosaccharide and "
                "C-2 epimer of glucose. "
                "The initial eukaryotic N-linked "
                "glycan precursor contains nine "
                "mannose residues arranged in "
                "a branched oligosaccharide. "
                "Mannose trimming also contributes "
                "to glycoprotein maturation "
                "and ER quality control.",
        "smiles": "C([C@@H]1[C@H]([C@@H]([C@@H](C(O1)O)O)O)O)O",
    },
    {
        "id": "asparagine",
        "name": "L-Asparagine (Asn)",
        "role": "An amino acid with a carboxamide "
                "side chain. During N-linked "
                "glycosylation, the nitrogen "
                "of this side-chain amide "
                "forms a covalent N-glycosidic "
                "bond with the first GlcNAc "
                "residue of the transferred glycan.",
        "smiles": "N[C@@H](CC(=O)N)C(=O)O",
    },
    {
        "id": "protein_glucosidase_i",
        "name": "ER glucosidase I (MOGS)",
        "role": "An ER glycoprotein-processing enzyme "
                "that removes the outermost "
                "glucose residue from the "
                "newly transferred N-linked "
                "oligosaccharide.",
        "type": "protein",
    },
    {
        "id": "protein_glucosidase_ii",
        "name": "ER glucosidase II (GANAB complex)",
        "role": "An ER glycan-processing enzyme "
                "complex whose catalytic alpha "
                "subunit is encoded by GANAB. "
                "It removes additional glucose "
                "residues during glycoprotein "
                "maturation and the "
                "calnexin-calreticulin cycle.",
        "type": "protein",
    },
    
    {
        "id": "protein_sar1",
        "name": "Sar1 GTPase (SAR1A / SAR1B)",
        "role": "A small GTPase that initiates COPII coat assembly. "
                "In its GTP-bound state, its N-terminal "
                "amphipathic helix associates with the ER "
                "membrane and assists membrane curvature.",
        "type": "protein",
    },
    {
        "id": "protein_sec12",
        "name": "Sec12 (PREB)",
        "role": "An ER membrane-associated guanine nucleotide "
                "exchange factor that promotes replacement "
                "of GDP with GTP on Sar1.",
        "type": "protein",
    },
    {
        "id": "protein_sec23",
        "name": "Sec23 (SEC23A / SEC23B)",
        "role": "An inner COPII coat subunit. It binds Sar1 "
                "and has GTPase-activating activity that "
                "regulates coat assembly and turnover.",
        "type": "protein",
    },
    {
        "id": "protein_sec24",
        "name": "Sec24 (SEC24A-D)",
        "role": "An inner COPII coat subunit that helps "
                "recognize cargo export signals and "
                "recruit selected membrane proteins "
                "or cargo receptors into carriers.",
        "type": "protein",
    },
    {
        "id": "protein_sec13",
        "name": "Sec13 (SEC13)",
        "role": "An outer COPII coat protein that forms "
                "a complex with Sec31 and contributes "
                "to the coat scaffold.",
        "type": "protein",
    },
    {
        "id": "protein_sec31",
        "name": "Sec31 (SEC31A / SEC31B)",
        "role": "An outer COPII coat protein that interacts "
                "with Sec13, helps organize coat structure "
                "and contributes to regulation of Sar1.",
        "type": "protein",
    },
    {
        "id": "protein_lman1",
        "name": "LMAN1 (ERGIC-53)",
        "role": "A cycling lectin cargo receptor involved "
                "in ER export of certain glycoproteins, "
                "including coagulation factors V and VIII.",
        "type": "protein",
    },
    {
        "id": "protein_mcfd2",
        "name": "MCFD2",
        "role": "A calcium-binding protein that associates "
                "with LMAN1 to support trafficking of "
                "specific cargo proteins.",
        "type": "protein",
    },
    {
        "id": "gtp",
        "name": "Guanosine triphosphate (GTP)",
        "role": "A guanine nucleotide containing three "
                "phosphate groups. Sar1 binds GTP to "
                "enter its membrane-associated active "
                "state during COPII coat initiation.",
        "smiles": "Nc1nc2c(ncn2[C@@H]2O[C@H](COP(=O)(O)OP(=O)(O)OP(=O)(O)O)[C@@H](O)[C@H]2O)c(=O)[nH]1",
    },
    {
        "id": "gdp",
        "name": "Guanosine diphosphate (GDP)",
        "role": "A guanine nucleotide containing two "
                "phosphate groups. Sar1 returns to "
                "a GDP-bound state following GTP "
                "hydrolysis, which helps regulate "
                "COPII coat disassembly.",
        "smiles": "Nc1nc2c(ncn2[C@@H]2O[C@H](COP(=O)(O)OP(=O)(O)O)[C@@H](O)[C@H]2O)c(=O)[nH]1",
    },
    
    {
        "id": "protein_rtn4",
        "name": "Reticulon-4 (RTN4 / Nogo)",
        "role": "An ER membrane-shaping protein whose "
                "hydrophobic hairpin-like membrane "
                "segments help generate and stabilize "
                "the high curvature of ER tubules "
                "and sheet edges.",
        "type": "protein",
    },
    {
        "id": "protein_atl3",
        "name": "Atlastin-3 (ATL3)",
        "role": "An ER membrane-anchored dynamin-like "
                "GTPase that participates in homotypic "
                "fusion of ER membrane tubules. "
                "GTP binding and hydrolysis are "
                "coupled to conformational changes "
                "during membrane fusion.",
        "type": "protein",
    },
    {
        "id": "protein_vapb",
        "name": "Vesicle-associated membrane protein-associated protein B (VAPB)",
        "role": "An ER membrane protein with a "
                "cytosol-facing domain that binds "
                "partner proteins involved in "
                "membrane contact sites and "
                "interorganellar lipid exchange.",
        "type": "protein",
    },
    
    {
        "id": "glycerol_3_phosphate",
        "name": "Glycerol-3-phosphate",
        "role": "A phosphorylated glycerol intermediate that "
                "provides the backbone for synthesis of "
                "glycerophospholipids and triacylglycerols. "
                "Sequential acylation produces lysophosphatidic "
                "acid and then phosphatidic acid.",
        "smiles": "OCC(O)COP(=O)(O)O",
    },
    {
        "id": "choline",
        "name": "Choline",
        "role": "A quaternary ammonium alcohol used to "
                "synthesize phosphatidylcholine. "
                "In the Kennedy pathway, choline is "
                "phosphorylated and converted into "
                "a CDP-choline intermediate before "
                "incorporation into a phospholipid.",
        "smiles": "C[N+](C)(C)CCO",
    },
    {
        "id": "ethanolamine",
        "name": "Ethanolamine",
        "role": "A small amino alcohol used as the "
                "headgroup precursor for "
                "phosphatidylethanolamine synthesis.",
        "smiles": "NCCO",
    },
    {
        "id": "oleic_acid",
        "name": "Oleic acid",
        "role": "A monounsaturated C18 fatty acid "
                "containing a cis double bond. "
                "After activation to oleoyl-CoA, "
                "its acyl group can be incorporated "
                "into phospholipids and "
                "triacylglycerols.",
        "smiles": "CCCCCCCC/C=C\\CCCCCCCC(=O)O",
    },
    {
        "id": "diacylglycerol_example",
        "name": "1,2-Dioleoylglycerol",
        "role": "A representative diacylglycerol (DAG) "
                "containing two oleoyl chains. "
                "DAG is a precursor for the synthesis "
                "of several phospholipids and "
                "triacylglycerols. Actual cellular "
                "DAG molecules have diverse fatty "
                "acyl compositions.",
        "smiles": "CCCCCCCC/C=C\\CCCCCCCC(=O)OCC(CO)OC(=O)CCCCCCC/C=C\\CCCCCCCC",
    },
    {
        "id": "triolein",
        "name": "Triolein (Glyceryl trioleate)",
        "role": "A triacylglycerol containing three "
                "oleoyl chains esterified to glycerol. "
                "It illustrates neutral lipid storage "
                "and the chemical product of a "
                "final DGAT-catalyzed acylation.",
        "smiles": "O=C(CCCCCCC/C=C\\CCCCCCCC)OCC(COC(=O)CCCCCCC/C=C\\CCCCCCCC)OC(=O)CCCCCCC/C=C\\CCCCCCCC",
    },
    {
        "id": "protein_chpt1",
        "name": "Choline phosphotransferase 1 (CHPT1)",
        "role": "An ER-associated enzyme that catalyzes "
                "transfer of phosphocholine from "
                "CDP-choline to diacylglycerol, "
                "forming phosphatidylcholine.",
        "type": "protein",
    },
    {
        "id": "protein_dgat1",
        "name": "Diacylglycerol O-acyltransferase 1 (DGAT1)",
        "role": "An ER membrane enzyme that catalyzes "
                "the final acylation of diacylglycerol "
                "using fatty acyl-CoA to form "
                "triacylglycerol.",
        "type": "protein",
    },
    {
        "id": "protein_hmgcr",
        "name": "HMG-CoA reductase (HMGCR)",
        "role": "An integral ER membrane enzyme that "
                "catalyzes the NADPH-dependent "
                "reduction of HMG-CoA to mevalonate. "
                "It is a major regulatory enzyme "
                "of cholesterol biosynthesis.",
        "type": "protein",
    },
    
    {
        "id": "protein_serca2",
        "name": "SERCA2 (ATP2A2)",
        "role": "An ATP-dependent calcium pump located "
                "in the ER membrane. SERCA2 is encoded "
                "by ATP2A2; different splice isoforms "
                "occur in different tissues. "
                "It transports Ca2+ from the cytosol "
                "into the ER or sarcoplasmic reticulum "
                "using energy from ATP hydrolysis.",
        "type": "protein",
    },
    {
        "id": "protein_itpr1",
        "name": "IP3 receptor type 1 (ITPR1)",
        "role": "A subunit of a tetrameric "
                "inositol 1,4,5-trisphosphate-regulated "
                "calcium-release channel in the ER "
                "membrane. Its activity responds "
                "to IP3 and calcium, allowing "
                "intracellular calcium signaling.",
        "type": "protein",
    },
    {
        "id": "inositol_trisphosphate",
        "name": "D-myo-inositol 1,4,5-trisphosphate (IP3)",
        "role": "A soluble second messenger produced "
                "when phospholipase C cleaves "
                "phosphatidylinositol 4,5-bisphosphate "
                "(PIP2). IP3 binds receptors on the "
                "ER membrane and can trigger calcium "
                "release into the cytosol. "
                "This drawing represents the "
                "free molecule, not receptor-bound IP3.",
        "smiles": "O[C@@H]1[C@H](O)[C@@H](O[P](O)(O)=O)[C@H](O[P](O)(O)=O)[C@@H](O)[C@@H]1O[P](O)(O)=O",
    },
    
    {
        "id": "protein_cyp3a4",
        "name": "Cytochrome P450 3A4 (CYP3A4)",
        "role": "A human ER-associated heme monooxygenase "
                "responsible for metabolism of many drugs. "
                "Its substrate preferences differ from "
                "those of other CYP enzymes.",
        "type": "protein",
    },
    {
        "id": "protein_por",
        "name": "NADPH-cytochrome P450 reductase (POR)",
        "role": "An ER membrane-associated enzyme containing "
                "FAD and FMN cofactors. It transfers "
                "electrons from NADPH to many microsomal "
                "cytochrome P450 enzymes.",
        "type": "protein",
    },
    {
        "id": "protein_cyp2e1",
        "name": "Cytochrome P450 2E1 (CYP2E1)",
        "role": "An ER-associated monooxygenase that can "
                "oxidize small compounds including "
                "ethanol and benzene. Some of its "
                "reactions generate harmful metabolites.",
        "type": "protein",
    },
    {
        "id": "nadph",
        "name": "NADPH",
        "role": "Reduced nicotinamide adenine dinucleotide "
                "phosphate. It supplies reducing equivalents "
                "to POR, supporting CYP-catalyzed oxidation.",
        "smiles": "C1C=CN(C=C1C(=O)N)[C@H]2[C@@H]([C@@H]([C@H](O2)COP(=O)(O)OP(=O)(O)OC[C@@H]3[C@H]([C@H]([C@@H](O3)N4C=NC5=C(N=CN=C54)N)OP(=O)(O)O)O)O)O",
    },
    {
        "id": "oxygen",
        "name": "Molecular oxygen (O2)",
        "role": "The oxygen molecule activated by CYP enzymes. "
                "In a typical monooxygenation reaction, "
                "one oxygen atom is incorporated into "
                "the substrate and the other becomes water."
                "The terminal electron acceptor in the mitochondrial respiratory chain.",
        "smiles": "O=O",
    },
    {
        "id": "heme_b",
        "name": "Heme b (iron protoporphyrin IX)",
        "role": "An iron-containing porphyrin prosthetic "
                "group at the catalytic center of CYP "
                "enzymes. The iron participates in "
                "electron transfer and oxygen activation. "
                "The chemical drawing omits protein "
                "coordination and axial ligands.",
        "smiles": "CC1=C(C2=CC3=NC(=CC4=C(C(=C([N-]4)C=C5C(=C(C(=N5)C=C1[N-]2)C)C=C)C)C=C)C(=C3CCC(=O)[O-])C)CCC(=O)[O-].[Fe+2]",
    },
    {
        "id": "fad",
        "name": "Flavin adenine dinucleotide (FAD)",
        "role": "A flavin cofactor of cytochrome P450 "
                "reductase. FAD accepts electrons "
                "originating from NADPH and transfers "
                "them within the reductase.",
        "smiles": "CC1=CC2=C(C=C1C)N(C3=NC(=O)NC(=O)C3=N2)C[C@@H]([C@@H]([C@@H](COP(=O)(O)OP(=O)(O)OC[C@@H]4[C@H]([C@H]([C@@H](O4)N5C=NC6=C(N=CN=C65)N)O)O)O)O)O",
    },
    {
        "id": "fmn",
        "name": "Flavin mononucleotide (FMN)",
        "role": "A flavin cofactor of cytochrome P450 "
                "reductase. FMN transfers electrons "
                "from the reductase to CYP enzymes.",
        "smiles": "CC1=CC2=C(C=C1C)N(C3=NC(=O)NC(=O)C3=N2)C[C@@H]([C@@H]([C@@H](COP(=O)(O)O)O)O)O",
    },
    {
        "id": "benzene",
        "name": "Benzene",
        "role": "An aromatic hydrocarbon used here as "
                "an educational example of CYP metabolism. "
                "Its oxidation can generate reactive "
                "intermediates and toxic products.",
        "smiles": "c1ccccc1",
    },
    {
        "id": "phenol",
        "name": "Phenol",
        "role": "A hydroxylated aromatic compound that "
                "can arise during CYP-mediated benzene "
                "metabolism. Its formation illustrates "
                "oxygen incorporation into a substrate, "
                "not necessarily safe detoxification.",
        "smiles": "Oc1ccccc1",
    },







]


def build_exploration_data():
    data = dict(EXPLORATION_DATA)
    data["cell_overview"]["children"] = CELL_STRUCTURE_IDS

    for organelle_id, content in ORGANCELLE_CONTENT.items():
        data[organelle_id]["children"] = content["children"]
        data[organelle_id]["visual"] = content["visual"]

    data.update(COMPONENT_DATA)

    for molecule in MOLECULES:
        data[molecule["id"]] = {
            "kind": "MOLECULE",
            "name": molecule["name"],
            "summary": molecule["role"],
            "function": molecule["role"],
            "components": "2D molecular structure · formula shown on the card",
            "visual": "molecule",
            "children": [],
            "molecules": [molecule["id"]],
        }
    return data

@lru_cache(maxsize=1)
def molecule_gallery():
    gallery = []

    for item in MOLECULES:

        # Large proteins are handled separately from
        # small molecules drawn by RDKit.
        if item.get("type") == "protein":

            protein_name = item["name"]

            # This is intentionally a labeled placeholder,
            # not a fabricated molecular structure.
            svg = f"""
            <svg xmlns="http://www.w3.org/2000/svg"
                 width="420" height="250"
                 viewBox="0 0 420 250">
              <rect width="420" height="250" fill="#f7f9fc"/>

              <path
                d="M100 135 C130 55 180 65 190 120
                   S255 215 280 135
                   S340 75 330 150
                   S240 200 210 145
                   S125 185 100 135"
                fill="none"
                stroke="#697d9b"
                stroke-width="13"
                stroke-linecap="round"
              />

              <text x="210" y="45"
                    text-anchor="middle"
                    font-family="Arial"
                    font-size="24"
                    font-weight="bold"
                    fill="#253247">
                {protein_name}
              </text>

              <text x="210" y="229"
                    text-anchor="middle"
                    font-family="Arial"
                    font-size="16"
                    fill="#526276">
                PROTEIN SCHEMATIC - NOT ATOMIC STRUCTURE
              </text>
            </svg>
            """

            encoded = base64.b64encode(
                svg.encode("utf-8")
            ).decode("ascii")

            gallery.append({
                "id": item["id"],
                "name": item["name"],
                "role": item["role"],
                "formula": "Ribosomal protein",
                "image": f"data:image/svg+xml;base64,{encoded}",
            })

            continue

        # Existing RDKit molecule generation
        molecule = Chem.MolFromSmiles(item["smiles"])

        if molecule is None:
            continue

        image = Draw.MolToImage(
            molecule,
            size=(420, 250)
        )

        buffer = BytesIO()
        image.save(buffer, format="PNG")

        item_image = base64.b64encode(
            buffer.getvalue()
        ).decode("ascii")

        gallery.append({
            "id": item["id"],
            "name": item["name"],
            "role": item["role"],
            "formula": rdMolDescriptors.CalcMolFormula(molecule),
            "image": f"data:image/png;base64,{item_image}",
        })

    return gallery
