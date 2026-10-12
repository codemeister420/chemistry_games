from rdkit import Chem
from rdkit.Chem import Draw, rdMolDescriptors
import os, uuid, random, glob

ANSWER_OPTIONS = [
    "Enantiomers",
    "Diastereomers",
    "Cis-trans isomerism",
    "Chain isomerism",
    "Functional isomerism",
    "Positional isomerism",
    "Not isomers",
]

PAIRS = []

def add(answer, pairs):
    for i, item in enumerate(pairs):
        s1, s2, name1, name2, explanation = item
        PAIRS.append({
            "id": f"{answer}_{i}_{name1}_vs_{name2}".replace(" ", "_").replace("/", "_"),
            "answer": answer,
            "smiles1": s1,
            "smiles2": s2,
            "name1": name1,
            "name2": name2,
            "explanation": explanation,
        })

# -------------------------
# CHAIN ISOMERISM
# -------------------------
add("Chain isomerism", [
    ("CCCC", "CC(C)C", "n-butane", "isobutane",
     "Both molecules have formula C4H10. They are both alkanes, but the carbon skeleton is different: straight-chain versus branched."),

    ("CCCCC", "CC(C)CC", "n-pentane", "2-methylbutane",
     "Both molecules have formula C5H12. The functional group type is unchanged; the carbon skeleton is branched differently."),

    ("CCCCC", "CC(C)(C)C", "n-pentane", "neopentane",
     "Both are C5H12 alkanes. One is straight-chain and the other is highly branched."),

    ("CCCCCC", "CC(C)CCC", "n-hexane", "2-methylpentane",
     "Both are C6H14 alkanes. The difference is branching of the carbon backbone."),

    ("CCCCCC", "CCC(C)CC", "n-hexane", "3-methylpentane",
     "Both molecules are C6H14. One is straight-chain and the other has a methyl branch."),

    ("CCCCCCC", "CC(C)CCCC", "n-heptane", "2-methylhexane",
     "Both are C7H16. The main difference is the carbon skeleton."),

    ("CCCCCCC", "CCC(C)CCC", "n-heptane", "3-methylhexane",
     "Both are alkanes with the same formula C7H16, but their carbon skeletons are different."),

    ("CCCCCCCC", "CC(C)CCCCC", "n-octane", "2-methylheptane",
     "Both are C8H18. One is straight-chain and the other is branched."),

    ("CCCCCCCC", "CCCC(C)CCC", "n-octane", "4-methylheptane",
     "Same formula, same alkane family, different carbon-chain skeleton."),

    ("CCCCCCCC", "CC(C)(C)CCCC", "n-octane", "2,2-dimethylhexane",
     "Both are C8H18. The carbon skeleton changes, so this is chain isomerism."),
])

# -------------------------
# FUNCTIONAL ISOMERISM
# -------------------------
add("Functional isomerism", [
    ("CCO", "COC", "ethanol", "dimethyl ether",
     "Both have formula C2H6O. Ethanol is an alcohol; dimethyl ether is an ether. Same formula, different functional group."),

    ("CCCO", "CCOC", "1-propanol", "methoxyethane",
     "Both have formula C3H8O. One is an alcohol, the other is an ether."),

    ("CCCCO", "CCOCC", "1-butanol", "diethyl ether",
     "Both have formula C4H10O. The first contains an alcohol group, the second contains an ether group."),

    ("CC(=O)C", "CCC=O", "propanone", "propanal",
     "Both are C3H6O. Propanone is a ketone; propanal is an aldehyde."),

    ("CCCC=O", "CCC(=O)C", "butanal", "2-butanone",
     "Both are C4H8O. Butanal is an aldehyde; 2-butanone is a ketone."),

    ("CC(=O)O", "COC=O", "acetic acid", "methyl formate",
     "Both are C2H4O2. Acetic acid is a carboxylic acid; methyl formate is an ester."),

    ("CCC(=O)O", "CCOC=O", "propionic acid", "ethyl formate",
     "Both are C3H6O2. One is a carboxylic acid and the other is an ester."),

    ("CCCC(=O)O", "CCOC(=O)C", "butyric acid", "ethyl acetate",
     "Both are C4H8O2. Butyric acid has a carboxylic acid group; ethyl acetate has an ester group."),
])

# -------------------------
# POSITIONAL ISOMERISM
# -------------------------
add("Positional isomerism", [
    ("CCCO", "CC(O)C", "1-propanol", "2-propanol",
     "Both are alcohols with formula C3H8O. The carbon skeleton is propane, but the -OH group moves from carbon 1 to carbon 2."),

    ("CCCCO", "CCC(O)C", "1-butanol", "2-butanol",
     "Both are butanols with formula C4H10O. The alcohol group is attached at a different carbon."),

    ("CCCCl", "CC(Cl)C", "1-chloropropane", "2-chloropropane",
     "Both are chloropropanes with formula C3H7Cl. Chlorine is attached to carbon 1 in one molecule and carbon 2 in the other."),

    ("CCCCCl", "CCC(Cl)C", "1-chlorobutane", "2-chlorobutane",
     "Both have the same butane skeleton and the same chloro substituent, but chlorine is in a different position."),

    ("CCCCBr", "CCC(Br)C", "1-bromobutane", "2-bromobutane",
     "Both are bromobutanes. The same bromine substituent is attached at a different carbon."),

    ("Oc1ccccc1C", "Cc1ccc(O)cc1", "o-cresol", "p-cresol",
     "Both are cresols. The -OH and -CH3 groups are attached to the same benzene ring, but their relative positions differ."),

    ("Clc1ccccc1Cl", "Clc1ccc(Cl)cc1", "o-dichlorobenzene", "p-dichlorobenzene",
     "Both are dichlorobenzenes. The same two chlorine atoms are on the benzene ring, but their positions are different."),

    ("Clc1cccc(Cl)c1", "Clc1ccc(Cl)cc1", "m-dichlorobenzene", "p-dichlorobenzene",
     "Both are dichlorobenzenes. The difference is meta versus para positioning on the aromatic ring."),

    ("Nc1ccccc1O", "Nc1ccc(O)cc1", "o-aminophenol", "p-aminophenol",
     "Both have an amino group and a hydroxyl group on benzene. The functional groups are the same; only their positions change."),
])

# -------------------------
# CIS-TRANS / E-Z ISOMERISM
# -------------------------
add("Cis-trans isomerism", [
    ("C/C=C/C", "C/C=C\\C", "2-butene", "2-butene",
     "Both have the same connectivity and formula. The difference is arrangement around the C=C double bond."),

    ("CC/C=C/CC", "CC/C=C\\CC", "3-hexene", "3-hexene",
     "Both molecules are 3-hexene. The double bond prevents free rotation, so different spatial arrangements are possible."),

    ("Cl/C=C/Cl", "Cl/C=C\\Cl", "2-dichloroethene", "2-dichloroethene",
     "The same atoms are connected in the same order. The difference is the spatial arrangement across the double bond."),

    ("Br/C=C/Br", "Br/C=C\\Br", "2-dibromoethene", "2-dibromoethene",
     "The bromine atoms are arranged differently around the double bond."),

    ("C/C=C/Cl", "C/C=C\\Cl", "chloropropene", "chloropropene",
     "The C=C bond restricts rotation. The two structures differ in alkene geometry."),

    ("C/C=C/C(=O)O", "C/C=C\\C(=O)O", "crotonic acid", "crotonic acid",
     "The carboxyl group and methyl group have different arrangements around the double bond."),

    ("C/C=C/CN", "C/C=C\\CN", "alkenyl amine", "alkenyl amine",
     "Same connectivity, different geometry around a double bond."),

    ("CC/C=C/C", "CC/C=C\\C", "2-pentene", "2-pentene",
     "Both are pentene isomers with the same double-bond position. The difference is E/Z geometry."),

    ("C/C=C/CBr", "C/C=C\\CBr", "bromoalkene", "bromoalkene",
     "The same molecular skeleton is present, but the groups around C=C are arranged differently."),
])

# -------------------------
# ENANTIOMERS
# Names are neutral; no giveaway like "mirror".
# -------------------------
add("Enantiomers", [
    ("F[C@H](Cl)Br", "F[C@@H](Cl)Br", "bromochlorofluoromethane A", "bromochlorofluoromethane B",
     "These molecules have one stereocenter. The configuration is opposite, so they are non-superimposable mirror images: enantiomers."),

    ("C[C@H](O)CC", "C[C@@H](O)CC", "2-butanol A", "2-butanol B",
     "2-butanol has one chiral carbon. The two structures have opposite configuration at that carbon, so they are enantiomers."),

    ("C[C@H](Cl)CC", "C[C@@H](Cl)CC", "2-chlorobutane A", "2-chlorobutane B",
     "There is one stereocenter. Reversing that stereocenter gives the enantiomer."),

    ("C[C@H](Br)CC", "C[C@@H](Br)CC", "2-bromobutane A", "2-bromobutane B",
     "Both have the same connectivity and one stereocenter. The stereocenter is inverted, giving enantiomers."),

    ("N[C@H](C)C(=O)O", "N[C@@H](C)C(=O)O", "alanine A", "alanine B",
     "Alanine has one chiral alpha carbon. Opposite configuration at that carbon gives enantiomers."),

    ("N[C@H](CO)C(=O)O", "N[C@@H](CO)C(=O)O", "serine A", "serine B",
     "Serine has one stereocenter in this model. The pair have opposite configuration at that center."),

    ("N[C@H](CS)C(=O)O", "N[C@@H](CS)C(=O)O", "cysteine A", "cysteine B",
     "The chiral center is inverted. Because there is only one stereocenter, the pair are enantiomers."),

    ("C[C@H](O)C(=O)O", "C[C@@H](O)C(=O)O", "lactic acid A", "lactic acid B",
     "Lactic acid has one stereocenter. The two forms have opposite configuration at that center."),
])

# -------------------------
# DIASTEREOMERS
# -------------------------
add("Diastereomers", [
    ("C[C@H](O)[C@H](O)C", "C[C@H](O)[C@@H](O)C", "2,3-butanediol A", "2,3-butanediol B",
     "These molecules have more than one stereocenter. Only one stereocenter changes, so they are stereoisomers but not mirror-image pairs: diastereomers."),

    ("O=C(O)[C@H](O)[C@H](O)C(=O)O", "O=C(O)[C@H](O)[C@@H](O)C(=O)O", "tartaric acid A", "tartaric acid B",
     "Tartaric acid has multiple stereocenters. These structures differ at one center but not all centers, so they are diastereomers."),

    ("C[C@H](Cl)[C@H](Br)C", "C[C@H](Cl)[C@@H](Br)C", "haloalkane A", "haloalkane B",
     "Same connectivity and multiple stereocenters. One stereocenter is inverted, but not all are inverted, so the pair are diastereomers."),

    ("N[C@H](C)[C@H](O)C(=O)O", "N[C@H](C)[C@@H](O)C(=O)O", "amino hydroxy acid A", "amino hydroxy acid B",
     "They have the same atoms connected in the same order, but differ at one stereocenter. This makes them diastereomers."),

    ("C[C@H](N)[C@H](O)C", "C[C@H](N)[C@@H](O)C", "amino alcohol A", "amino alcohol B",
     "These are not mirror images because only one stereocenter changes. Therefore they are diastereomers."),

    ("O[C@H](CO)[C@H](O)CO", "O[C@H](CO)[C@@H](O)CO", "polyol A", "polyol B",
     "This is an epimer-like pair. Epimers differ at one stereocenter, and epimers are a specific type of diastereomer."),

    ("OC[C@H](O)[C@H](O)CO", "OC[C@H](O)[C@@H](O)CO", "sugar alcohol A", "sugar alcohol B",
     "They differ at one stereocenter. Because epimers are diastereomers, the correct broader answer is Diastereomers."),

    ("OC[C@H](O)[C@H](O)[C@H](O)CO", "OC[C@H](O)[C@@H](O)[C@H](O)CO", "hexitol A", "hexitol B",
     "Only one stereocenter changes. That makes the pair epimers, which belong under diastereomers in this quiz."),

    ("O[C@H]1CO[C@H](O)[C@H]1O", "O[C@H]1CO[C@@H](O)[C@H]1O", "ribose-like sugar A", "ribose-like sugar B",
     "The ring structures have the same connectivity and differ at one stereocenter. This is a diastereomeric relationship."),
])

# -------------------------
# NOT ISOMERS
# -------------------------
add("Not isomers", [
    ("CCO", "CCCC", "ethanol", "butane",
     "These are not isomers because their molecular formulas are different. Ethanol is C2H6O, while butane is C4H10."),

    ("CCO", "CC(=O)O", "ethanol", "acetic acid",
     "Not isomers: ethanol and acetic acid do not have the same molecular formula."),

    ("CCCC", "CCOCC", "butane", "diethyl ether",
     "Not isomers because the formulas are different. Isomers must have the same molecular formula."),

    ("CCN", "CCO", "ethylamine", "ethanol",
     "Not isomers: one contains nitrogen and the other contains oxygen, so their formulas differ."),

    ("CCCl", "CCBr", "chloroethane", "bromoethane",
     "Not isomers: chlorine and bromine are different atoms, so the formulas are not the same."),

    ("c1ccccc1", "C1CCCCC1", "benzene", "cyclohexane",
     "Not isomers: benzene is C6H6 and cyclohexane is C6H12. Same number of carbons, but different number of hydrogens."),

    ("CC(=O)O", "CC(=O)N", "acetic acid", "acetamide",
     "Not isomers because oxygen and nitrogen content differs."),

    ("CCCO", "CCCCO", "propanol", "butanol",
     "Not isomers: butanol has one more carbon than propanol."),

    ("CC(C)C", "CCCCC", "isobutane", "pentane",
     "Not isomers: isobutane is C4H10 and pentane is C5H12."),

    ("CC#N", "CCO", "acetonitrile", "ethanol",
     "Not isomers because the atoms and formulas are different."),
])

# -------------------------
# CARBON NUMBERING HELPERS
# -------------------------

def _carbon_priority_atoms(mol):
    priority_patterns = [
        "[CX3](=O)[OX2H1,OX1-]",
        "[CX3](=O)O[#6]",
        "[CX3](=O)N",
        "[CX3H1](=O)",
        "[#6][CX3](=O)[#6]",
        "[C;!$(C=O)][O;H1]",
        "[C][N;H1,H2,H0]",
        "[C][F,Cl,Br,I]",
        "[C]=[C]",
        "[C]#[C]",
    ]

    for smarts in priority_patterns:
        patt = Chem.MolFromSmarts(smarts)
        if patt is None:
            continue

        atoms = set()
        for match in mol.GetSubstructMatches(patt):
            for idx in match:
                atom = mol.GetAtomWithIdx(idx)
                if atom.GetAtomicNum() == 6:
                    atoms.add(idx)

        if atoms:
            return atoms

    return set()

def _carbon_graph(mol):
    carbons = [a.GetIdx() for a in mol.GetAtoms() if a.GetAtomicNum() == 6]
    carbon_set = set(carbons)

    adj = {idx: [] for idx in carbons}
    for bond in mol.GetBonds():
        a = bond.GetBeginAtomIdx()
        b = bond.GetEndAtomIdx()
        if a in carbon_set and b in carbon_set:
            adj[a].append(b)
            adj[b].append(a)

    for k in adj:
        adj[k].sort()

    return carbons, adj

def _all_simple_carbon_paths(adj):
    paths = []

    def dfs(path):
        paths.append(path[:])
        last = path[-1]
        for nb in adj[last]:
            if nb not in path:
                path.append(nb)
                dfs(path)
                path.pop()

    for start in adj:
        dfs([start])

    unique = {}
    for p in paths:
        key = tuple(p)
        rkey = tuple(reversed(p))
        if rkey not in unique:
            unique[key] = p

    return list(unique.values())

def _path_unsaturation_locs(mol, path):
    locs = []
    for i in range(len(path) - 1):
        bond = mol.GetBondBetweenAtoms(path[i], path[i + 1])
        if bond and bond.GetBondType() in (Chem.BondType.DOUBLE, Chem.BondType.TRIPLE):
            locs.append(i + 1)
    return locs or [999]

def _path_substituent_locs(mol, path):
    path_set = set(path)
    locs = []

    for i, atom_idx in enumerate(path):
        atom = mol.GetAtomWithIdx(atom_idx)
        for nb in atom.GetNeighbors():
            nb_idx = nb.GetIdx()
            if nb_idx not in path_set and nb.GetAtomicNum() > 1:
                locs.append(i + 1)
                break

    return sorted(locs) or [999]

def _best_direction_for_path(mol, path, priority_atoms):
    candidates = [path, list(reversed(path))]

    def score(order):
        pos = {atom: i + 1 for i, atom in enumerate(order)}
        priority_locs = sorted(pos[a] for a in priority_atoms if a in pos) or [999]
        return (
            priority_locs,
            _path_unsaturation_locs(mol, order),
            _path_substituent_locs(mol, order),
            order,
        )

    return min(candidates, key=score)

def _ring_parent_order(mol, priority_atoms):
    rings = mol.GetRingInfo().AtomRings()
    carbon_rings = []

    for ring in rings:
        if all(mol.GetAtomWithIdx(i).GetAtomicNum() == 6 for i in ring):
            carbon_rings.append(list(ring))

    if not carbon_rings:
        return None

    ring = max(carbon_rings, key=len)
    n = len(ring)
    candidates = []

    for start_pos in range(n):
        forward = ring[start_pos:] + ring[:start_pos]
        backward = list(reversed(forward))
        candidates.append(forward)
        candidates.append(backward)

    def score(order):
        pos = {atom: i + 1 for i, atom in enumerate(order)}
        priority_locs = sorted(pos[a] for a in priority_atoms if a in pos) or [999]

        ring_set = set(order)
        subst_locs = []
        for atom_idx in order:
            atom = mol.GetAtomWithIdx(atom_idx)
            for nb in atom.GetNeighbors():
                if nb.GetIdx() not in ring_set and nb.GetAtomicNum() > 1:
                    subst_locs.append(pos[atom_idx])
                    break

        return (priority_locs, sorted(subst_locs) or [999], order)

    return min(candidates, key=score)

def _choose_parent_carbon_order(mol):
    priority_atoms = _carbon_priority_atoms(mol)

    ring_order = _ring_parent_order(mol, priority_atoms)
    if ring_order:
        return ring_order

    carbons, adj = _carbon_graph(mol)
    if not carbons:
        return []

    paths = _all_simple_carbon_paths(adj)

    if priority_atoms:
        priority_paths = [p for p in paths if any(a in priority_atoms for a in p)]
        if priority_paths:
            paths = priority_paths

    max_len = max(len(p) for p in paths)
    paths = [p for p in paths if len(p) == max_len]

    oriented = [_best_direction_for_path(mol, p, priority_atoms) for p in paths]

    def final_score(order):
        pos = {atom: i + 1 for i, atom in enumerate(order)}
        priority_locs = sorted(pos[a] for a in priority_atoms if a in pos) or [999]
        return (
            priority_locs,
            _path_unsaturation_locs(mol, order),
            _path_substituent_locs(mol, order),
            order,
        )

    return min(oriented, key=final_score)

def _number_branch_carbons(mol, parent_order):
    labels = {}
    next_num = 1

    for atom_idx in parent_order:
        labels[atom_idx] = next_num
        next_num += 1

    visited = set(parent_order)

    for parent_idx in parent_order:
        parent_atom = mol.GetAtomWithIdx(parent_idx)
        branch_starts = []

        for nb in parent_atom.GetNeighbors():
            nb_idx = nb.GetIdx()
            if nb.GetAtomicNum() == 6 and nb_idx not in visited:
                branch_starts.append(nb_idx)

        branch_starts.sort()

        for start in branch_starts:
            queue = [(start, parent_idx)]

            while queue:
                current, came_from = queue.pop(0)
                if current in visited:
                    continue

                visited.add(current)
                labels[current] = next_num
                next_num += 1

                atom = mol.GetAtomWithIdx(current)
                next_carbons = []
                for nb in atom.GetNeighbors():
                    nb_idx = nb.GetIdx()
                    if nb_idx == came_from:
                        continue
                    if nb.GetAtomicNum() == 6 and nb_idx not in visited:
                        next_carbons.append(nb_idx)

                next_carbons.sort()
                for nb_idx in next_carbons:
                    queue.append((nb_idx, current))

    for atom in mol.GetAtoms():
        idx = atom.GetIdx()
        if atom.GetAtomicNum() == 6 and idx not in labels:
            labels[idx] = next_num
            next_num += 1

    return labels

def _carbon_numbered_copy(mol):
    mol = Chem.Mol(mol)

    for atom in mol.GetAtoms():
        if atom.HasProp("atomNote"):
            atom.ClearProp("atomNote")

    parent_order = _choose_parent_carbon_order(mol)
    labels = _number_branch_carbons(mol, parent_order)

    for atom_idx, number in labels.items():
        mol.GetAtomWithIdx(atom_idx).SetProp("atomNote", str(number))

    return mol

# -------------------------
# ROUND GENERATION
# -------------------------

def cleanup_generated_images(base_dir=None, keep=0):
    if base_dir is None:
        base_dir = os.path.dirname(__file__)

    out_dir = os.path.join(base_dir, "static", "generated")
    os.makedirs(out_dir, exist_ok=True)

    files = sorted(glob.glob(os.path.join(out_dir, "*.png")), key=os.path.getmtime)
    if keep < 0:
        keep = 0

    if keep == 0:
        files_to_delete = files
    else:
        files_to_delete = files[:-keep] if len(files) > keep else []

    for file_path in files_to_delete:
        try:
            os.remove(file_path)
        except OSError:
            pass


def _save_molecule_image_to_blueprint_static(mol, prefix="mol", numbered=False):
    if mol is None:
        return None

    base_dir = os.path.dirname(__file__)
    out_dir = os.path.join(base_dir, "static", "generated")
    os.makedirs(out_dir, exist_ok=True)

    filename = f"{prefix}_{uuid.uuid4().hex}.png"
    out_path = os.path.join(out_dir, filename)

    try:
        draw_mol = _carbon_numbered_copy(mol) if numbered else mol
        Draw.MolToFile(draw_mol, out_path, size=(360, 300))
    except Exception:
        return None

    return f"generated/{filename}"

def generate_isomer_pair(target_answer=None, seen_ids=None):
    seen_ids = set(seen_ids or [])

    pool = PAIRS
    if target_answer:
        pool = [p for p in PAIRS if p["answer"] == target_answer]

    pool = [p for p in pool if p["id"] not in seen_ids] or pool
    pair = random.choice(pool)

    mol1 = Chem.MolFromSmiles(pair["smiles1"])
    mol2 = Chem.MolFromSmiles(pair["smiles2"])

    return mol1, mol2, pair

def generate_isomer_round(seen_ids=None):
    target_answer = random.choice(ANSWER_OPTIONS)

    for _ in range(40):
        mol1, mol2, pair = generate_isomer_pair(target_answer, seen_ids)
        if mol1 is not None and mol2 is not None:
            break
    else:
        mol1 = Chem.MolFromSmiles("CCCC")
        mol2 = Chem.MolFromSmiles("CC(C)C")
        pair = {
            "id": "fallback_butane_isobutane",
            "answer": "Chain isomerism",
            "name1": "n-butane",
            "name2": "isobutane",
            "explanation": "Both are C4H10 alkanes. The difference is the carbon skeleton: straight-chain versus branched.",
        }

    mol1_img = _save_molecule_image_to_blueprint_static(mol1, "mol1")
    mol2_img = _save_molecule_image_to_blueprint_static(mol2, "mol2")

    mol1_numbered_img = _save_molecule_image_to_blueprint_static(mol1, "mol1_numbered", numbered=True)
    mol2_numbered_img = _save_molecule_image_to_blueprint_static(mol2, "mol2_numbered", numbered=True)

    formula1 = rdMolDescriptors.CalcMolFormula(mol1) if mol1 else "?"
    formula2 = rdMolDescriptors.CalcMolFormula(mol2) if mol2 else "?"

    return {
        "mol1_img": mol1_img,
        "mol2_img": mol2_img,
        "mol1_numbered_img": mol1_numbered_img,
        "mol2_numbered_img": mol2_numbered_img,
        "correct_answer": pair["answer"],
        "pair_id": pair["id"],
        "name1": pair["name1"],
        "name2": pair["name2"],
        "formula1": formula1,
        "formula2": formula2,
        "explanation": pair["explanation"],
        "options": ANSWER_OPTIONS,
        "total_pairs": len(PAIRS),
    }