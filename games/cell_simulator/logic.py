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
        "summary": "Ribosomes assemble amino acids into proteins by reading messenger RNA.",
        "function": "They are built from ribosomal RNA and proteins; some float in the cytoplasm and others attach to rough ER.",
        "components": "Ribosomal RNA · proteins · messenger RNA · transfer RNA",
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
        "visual": "ribosome",
        "children": ["small_subunit", "large_subunit", "ribosomal_rna", "ribosomal_proteins"],
    },
    "rough_er": {
        "visual": "network",
        "children": ["rough_er_membrane", "bound_ribosomes", "rough_er_lumen", "protein_folding"],
    },
    "smooth_er": {
        "visual": "network",
        "children": ["smooth_er_membrane", "lipid_synthesis", "calcium_store", "detoxification"],
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
    "protein_translocon": _component("Protein translocon", "MEMBRANE CHANNEL", "A protein-conducting channel allows selected newly made proteins to enter the ER lumen.", "protein_complex"),
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
    "small_subunit": _component("Small ribosomal subunit", "RNA + PROTEINS", "The small subunit binds messenger RNA and helps decode its sequence.", "ribosome", ["ribosomal_rna", "ribosomal_proteins"], ["alanine"]),
    "large_subunit": _component("Large ribosomal subunit", "RNA + PROTEINS", "The large subunit contains the catalytic center that forms peptide bonds during protein synthesis.", "ribosome", ["ribosomal_rna", "ribosomal_proteins"], ["glycine", "alanine"]),
    "ribosomal_rna": _component("Ribosomal RNA", "NUCLEIC ACID", "RNA forms much of the ribosome's structure and participates directly in protein synthesis.", "nucleic_acid", (), ["adenine", "cytosine", "guanine", "uracil"]),
    "ribosomal_proteins": _component("Ribosomal proteins", "PROTEINS", "Proteins stabilize ribosomal RNA and help the ribosome assemble and function.", "protein_complex", (), ["glycine", "alanine", "serine"]),
    "rough_er_membrane": _component("Rough-ER membrane", "LIPID BILAYER", "The ER membrane anchors ribosomes and contains channels that feed new proteins into the ER lumen.", "membrane", ["bound_ribosomes", "protein_translocon"], ["phosphatidylcholine", "phosphatidylethanolamine"]),
    "bound_ribosomes": _component("ER-bound ribosomes", "RNA + PROTEINS", "Ribosomes attached to the ER synthesize proteins destined for membranes, secretion, or the endomembrane system.", "ribosome", ["ribosomal_rna", "ribosomal_proteins"]),
    "rough_er_lumen": _component("Rough-ER lumen", "COMPARTMENT", "Newly made proteins fold and receive early processing inside this enclosed space.", "compartment", ["protein_folding"], ["water"]),
    "protein_folding": _component("Protein folding", "PROTEIN PROCESSING", "Chaperone proteins help new polypeptide chains reach stable shapes and identify proteins that need quality control.", "protein_complex", (), ["glycine", "alanine", "serine"]),
    "smooth_er_membrane": _component("Smooth-ER membrane", "LIPID BILAYER", "Membrane enzymes synthesize lipids and help metabolize certain compounds.", "membrane", ["lipid_synthesis"], ["phosphatidylcholine", "phosphatidylethanolamine", "cholesterol"]),
    "lipid_synthesis": _component("Lipid synthesis", "BIOSYNTHETIC PROCESS", "Enzymes assemble fatty acids, glycerol, and other building blocks into cellular lipids.", "pathway", (), ["phosphatidylcholine", "phosphatidylethanolamine"]),
    "calcium_store": _component("Calcium store", "ION STORAGE", "The ER can store and release calcium ions that act as signals in many cell types.", "compartment"),
    "detoxification": _component("Detoxification enzymes", "ENZYME SYSTEM", "Enzymes in the smooth ER modify some drugs and other compounds, often making them easier to process.", "protein_complex"),
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
        "id": "oxygen",
        "name": "Molecular oxygen",
        "role": "The terminal electron acceptor in the mitochondrial respiratory chain.",
        "smiles": "O=O",
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
        molecule = Chem.MolFromSmiles(item["smiles"])
        if molecule is None:
            continue

        image = Draw.MolToImage(molecule, size=(420, 250))
        buffer = BytesIO()
        image.save(buffer, format="PNG")
        item_image = base64.b64encode(buffer.getvalue()).decode("ascii")

        gallery.append({
            "id": item["id"],
            "name": item["name"],
            "role": item["role"],
            "formula": rdMolDescriptors.CalcMolFormula(molecule),
            "image": f"data:image/png;base64,{item_image}",
        })

    return gallery