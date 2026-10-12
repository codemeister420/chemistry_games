import os, uuid, glob, random
from rdkit import Chem
from rdkit.Chem import Draw, rdMolDescriptors, rdDepictor


# ============================================================
# STARTERS
# ============================================================

STARTERS = [
    {
        "id": "ps_mini",
        "name": "Phosphatidylserine (mini tails)",
        "category": "phospholipid",
        "smiles": "CCCCCC(=O)OCC(COP(=O)(O)OCC(N)C(=O)O)OC(=O)CCCCCC",
        "site_smarts": {
            "methylation": "[N;H1,H2;!$(NC=O)]",
            "acetylation": "[N;H1,H2;!$(NC=O)]",
            "phosphorylation": "[O;H1]-[C]",
            "dephosphorylation": "OP(=O)(O)O",
            "glycosylation": "[O;H1]-[C]",
            "lipidation": "[N;H1,H2;!$(NC=O)]",
            "ubiquitination": "[N;H1,H2;!$(NC=O)]",
            "metal_cu": "[N,O,S]",
            "metal_fe2": "[N,O,S]",
            "metal_fe3": "[N,O,S]",
            "protonate": "[N;!$([N+])]",
            "deprotonate": "[O;H1]-C(=O)",
            "hydroxylation": "[CH,CH2,CH3]",
            "adenylation": "[O;H1]-C(=O)",
        },
    },
    {
        "id": "pe_mini",
        "name": "Phosphatidylethanolamine (mini tails)",
        "category": "phospholipid",
        "smiles": "CCCCCC(=O)OCC(COP(=O)(O)OCCN)OC(=O)CCCCCC",
        "site_smarts": {
            "methylation": "[N;H1,H2;!$(NC=O)]",
            "acetylation": "[N;H1,H2;!$(NC=O)]",
            "phosphorylation": "[O;H1]-[C]",
            "dephosphorylation": "OP(=O)(O)O",
            "glycosylation": "[O;H1]-[C]",
            "lipidation": "[N;H1,H2;!$(NC=O)]",
            "ubiquitination": "[N;H1,H2;!$(NC=O)]",
            "metal_cu": "[N,O,S]",
            "metal_fe2": "[N,O,S]",
            "metal_fe3": "[N,O,S]",
            "protonate": "[N;!$([N+])]",
            "hydroxylation": "[CH,CH2,CH3]",
        },
    },
    {
        "id": "glycerol",
        "name": "Glycerol",
        "category": "glycerol",
        "smiles": "OCC(O)CO",
        "site_smarts": {
            "phosphorylation": "[O;H1]-[C]",
            "glycosylation": "[O;H1]-[C]",
            "lipidation": "[O;H1]-[C]",
            "hydroxylation": "[CH,CH2,CH3]",
            "metal_cu": "[O;H1]",
            "metal_fe2": "[O;H1]",
            "metal_fe3": "[O;H1]",
        },
    },
    {
        "id": "serine",
        "name": "Serine",
        "category": "amino_acid",
        "smiles": "N[C@@H](CO)C(=O)O",
        "site_smarts": {
            "phosphorylation": "[O;H1]-[C]",
            "methylation": "[N;H1,H2;!$(NC=O)]",
            "acetylation": "[N;H1,H2;!$(NC=O)]",
            "glycosylation": "[O;H1]-[C]",
            "lipidation": "[N;H1,H2;!$(NC=O)]",
            "ubiquitination": "[N;H1,H2;!$(NC=O)]",
            "metal_cu": "[N,O,S]",
            "metal_fe2": "[N,O,S]",
            "metal_fe3": "[N,O,S]",
            "protonate": "[N;!$([N+])]",
            "deprotonate": "[O;H1]-C(=O)",
            "hydroxylation": "[CH,CH2,CH3]",
            "adenylation": "[O;H1]-C(=O)",
        },
    },
    {
        "id": "lysine",
        "name": "Lysine",
        "category": "amino_acid",
        "smiles": "NCCCC[C@H](N)C(=O)O",
        "site_smarts": {
            "methylation": "[N;H1,H2;!$(NC=O)]",
            "acetylation": "[N;H1,H2;!$(NC=O)]",
            "ubiquitination": "[N;H1,H2;!$(NC=O)]",
            "lipidation": "[N;H1,H2;!$(NC=O)]",
            "metal_cu": "[N,O]",
            "metal_fe2": "[N,O]",
            "metal_fe3": "[N,O]",
            "protonate": "[N;!$([N+])]",
            "deprotonate": "[O;H1]-C(=O)",
            "hydroxylation": "[CH,CH2,CH3]",
            "adenylation": "[O;H1]-C(=O)",
        },
    },
    {
        "id": "cysteine",
        "name": "Cysteine",
        "category": "amino_acid",
        "smiles": "N[C@@H](CS)C(=O)O",
        "site_smarts": {
            "lipidation": "[S;H1]",
            "metal_cu": "[N,O,S]",
            "metal_fe2": "[N,O,S]",
            "metal_fe3": "[N,O,S]",
            "methylation": "[N;H1,H2;!$(NC=O)]",
            "acetylation": "[N;H1,H2;!$(NC=O)]",
            "ubiquitination": "[N;H1,H2;!$(NC=O)]",
            "protonate": "[N;!$([N+])]",
            "deprotonate": "[O;H1]-C(=O)",
            "hydroxylation": "[CH,CH2,CH3]",
            "adenylation": "[O;H1]-C(=O)",
        },
    },
    {
        "id": "pep_cys_gly_cys",
        "name": "Peptide: Cys-Gly-Cys",
        "category": "peptide",
        "smiles": "N[C@@H](CS)C(=O)NCC(=O)N[C@@H](CS)C(=O)O",
        "site_smarts": {
            "disulfide": "[S;H1]",
            "lipidation": "[S;H1]",
            "metal_cu": "[N,O,S]",
            "metal_fe2": "[N,O,S]",
            "metal_fe3": "[N,O,S]",
            "methylation": "[N;H1,H2;!$(NC=O)]",
            "acetylation": "[N;H1,H2;!$(NC=O)]",
            "ubiquitination": "[N;H1,H2;!$(NC=O)]",
            "protonate": "[N;!$([N+])]",
            "deprotonate": "[O;H1]-C(=O)",
            "hydroxylation": "[CH,CH2,CH3]",
            "adenylation": "[O;H1]-C(=O)",
        },
    },
    {
        "id": "pep_tyr_ser_lys",
        "name": "Peptide: Tyr-Ser-Lys",
        "category": "peptide",
        "smiles": "N[C@@H](CC1=CC=C(O)C=C1)C(=O)N[C@@H](CO)C(=O)N[C@@H](CCCCN)C(=O)O",
        "site_smarts": {
            "phosphorylation": "[O;H1]-[C],[O;H1]-[c]",
            "glycosylation": "[O;H1]-[C],[O;H1]-[c]",
            "acetylation": "[N;H1,H2;!$(NC=O)]",
            "methylation": "[N;H1,H2;!$(NC=O)]",
            "ubiquitination": "[N;H1,H2;!$(NC=O)]",
            "lipidation": "[N;H1,H2;!$(NC=O)]",
            "metal_cu": "[N,O,S,n]",
            "metal_fe2": "[N,O,S,n]",
            "metal_fe3": "[N,O,S,n]",
            "protonate": "[N;!$([N+])]",
            "deprotonate": "[O;H1]-C(=O)",
            "hydroxylation": "[CH,CH2,CH3]",
            "adenylation": "[O;H1]-C(=O)",
        },
    },
    {
        "id": "glucose",
        "name": "Glucose",
        "category": "monosaccharide",
        "smiles": "OC[C@H]1O[C@@H](O)[C@H](O)[C@@H](O)[C@H]1O",
        "site_smarts": {
            "phosphorylation": "[O;H1]-[C]",
            "glycosylation": "[O;H1]-[C]",
            "lipidation": "[O;H1]-[C]",
            "metal_cu": "[O;H1]",
            "metal_fe2": "[O;H1]",
            "metal_fe3": "[O;H1]",
            "hydroxylation": "[CH,CH2,CH3]",
        },
    },
    {
        "id": "glucose_6_phosphate",
        "name": "Glucose-6-phosphate",
        "category": "sugar_phosphate",
        "smiles": "OP(=O)(O)OCC1OC(O)C(O)C(O)C1O",
        "site_smarts": {
            "dephosphorylation": "OP(=O)(O)O",
            "phosphorylation": "[O;H1]-[C]",
            "glycosylation": "[O;H1]-[C]",
            "lipidation": "[O;H1]-[C]",
            "metal_cu": "[O,N,S]",
            "metal_fe2": "[O,N,S]",
            "metal_fe3": "[O,N,S]",
            "hydroxylation": "[CH,CH2,CH3]",
        },
    },
    {
        "id": "cholesterol",
        "name": "Cholesterol",
        "category": "sterol",
        "smiles": "CC(C)CCCC(C)C1CCC2C1(CCC3C2CC=C4C3(CCC(C4)O)C)C",
        "site_smarts": {
            "phosphorylation": "[O;H1]",
            "glycosylation": "[O;H1]",
            "lipidation": "[O;H1]",
            "hydroxylation": "[CH,CH2,CH3]",
        },
    },
]


# ============================================================
# MODS / GOALS
# ============================================================

MODS = [
    ("methylation", "Methylation"),
    ("acetylation", "Acetylation"),
    ("phosphorylation", "Phosphorylation"),
    ("dephosphorylation", "Dephosphorylation"),
    ("glycosylation", "Glycosylation"),
    ("lipidation", "Lipidation"),
    ("ubiquitination", "Ubiquitination (tag)"),
    ("disulfide", "Disulfide Bond (Cys–Cys)"),
    ("hydroxylation", "Hydroxylation (add –OH)"),
    ("adenylation", "Adenylation (AMP-tag, model)"),
    ("metal_cu", "Cu²⁺ Complexation"),
    ("metal_fe2", "Fe²⁺ Complexation"),
    ("metal_fe3", "Fe³⁺ Complexation"),
    ("protonate", "Protonate (pH effect)"),
    ("deprotonate", "Deprotonate (pH effect)"),
]

GOALS = [
    ("add_negative", "Goal: Add negative charge / increase polarity", "phosphorylation"),
    ("remove_phosphate", "Goal: Remove phosphate (reset signaling)", "dephosphorylation"),
    ("activate_signal", "Goal: Signaling switch (classic PTM)", "phosphorylation"),
    ("reduce_positive", "Goal: Reduce amine reactivity / change interaction", "acetylation"),
    ("fine_tune", "Goal: Fine-tune regulation (subtle tag)", "methylation"),
    ("membrane_anchor", "Goal: Increase membrane association", "lipidation"),
    ("add_sugar", "Goal: Add a sugar tag (glyco)", "glycosylation"),
    ("tag_degrade", "Goal: Mark for degradation (proteasome tag)", "ubiquitination"),
    ("stabilize_fold", "Goal: Stabilize structure via disulfide bond", "disulfide"),
    ("increase_polarity", "Goal: Increase polarity with an extra –OH", "hydroxylation"),
    ("activate_carboxyl", "Goal: Activate carboxylate for coupling", "adenylation"),
    ("bind_cu", "Goal: Form a Cu²⁺ coordination complex", "metal_cu"),
    ("bind_fe2", "Goal: Bind Fe²⁺ (metal coordination)", "metal_fe2"),
    ("bind_fe3", "Goal: Bind Fe³⁺ (stronger coordination)", "metal_fe3"),
    ("more_basic", "Goal: Make it more positively charged (protonate)", "protonate"),
    ("more_acidic", "Goal: Make it more negatively charged (deprotonate)", "deprotonate"),
]


# ============================================================
# RENDERING / HELPERS
# ============================================================

def _prepare_mol_for_drawing(mol):
    mol = Chem.Mol(mol)
    try:
        rdDepictor.Compute2DCoords(mol)
    except Exception:
        pass
    return mol

def _render_png(mol, out_path, highlight_atoms=None):
    mol = _prepare_mol_for_drawing(mol)

    try:
        drawer = Draw.MolDraw2DCairo(520, 360)
        opts = drawer.drawOptions()
        opts.clearBackground = False
        opts.padding = 0.08

        if highlight_atoms:
            drawer.DrawMolecule(mol, highlightAtoms=list(highlight_atoms))
        else:
            drawer.DrawMolecule(mol)

        drawer.FinishDrawing()

        with open(out_path, "wb") as f:
            f.write(drawer.GetDrawingText())

        return True
    except Exception:
        try:
            Draw.MolToFile(mol, out_path, size=(520, 360), highlightAtoms=list(highlight_atoms or []))
            return True
        except Exception:
            return False

def cleanup_old_images(gen_dir, keep=160):
    os.makedirs(gen_dir, exist_ok=True)
    files = glob.glob(os.path.join(gen_dir, "rxn_*.png"))
    if len(files) <= keep:
        return

    files.sort(key=lambda p: os.path.getmtime(p))
    for f in files[:-keep]:
        try:
            os.remove(f)
        except Exception:
            pass

def _first_match_atom(mol, smarts):
    if not smarts:
        return None

    patt = Chem.MolFromSmarts(smarts)
    if patt is None:
        return None

    matches = mol.GetSubstructMatches(patt)
    if not matches:
        return None

    return int(random.choice(matches)[0])

def _all_match_atoms(mol, smarts):
    if not smarts:
        return []

    patt = Chem.MolFromSmarts(smarts)
    if patt is None:
        return []

    return [int(m[0]) for m in mol.GetSubstructMatches(patt)]

def _safe_sanitize(mol):
    try:
        Chem.SanitizeMol(mol)
        return mol, None
    except Exception as e:
        try:
            Chem.SanitizeMol(mol, catchErrors=True)
            return mol, None
        except Exception:
            return None, str(e)


# ============================================================
# EDITING FRAGMENTS
# ============================================================

def _attach_methyl(rw, atom_idx):
    c = rw.AddAtom(Chem.Atom(6))
    rw.AddBond(atom_idx, c, Chem.BondType.SINGLE)
    return {atom_idx, c}

def _attach_acetyl(rw, atom_idx):
    c = rw.AddAtom(Chem.Atom(6))
    o = rw.AddAtom(Chem.Atom(8))
    m = rw.AddAtom(Chem.Atom(6))
    rw.AddBond(atom_idx, c, Chem.BondType.SINGLE)
    rw.AddBond(c, o, Chem.BondType.DOUBLE)
    rw.AddBond(c, m, Chem.BondType.SINGLE)
    return {atom_idx, c, o, m}

def _attach_phosphate(rw, atom_idx):
    p = rw.AddAtom(Chem.Atom(15))
    o1 = rw.AddAtom(Chem.Atom(8))
    o2 = rw.AddAtom(Chem.Atom(8))
    o3 = rw.AddAtom(Chem.Atom(8))
    rw.AddBond(atom_idx, p, Chem.BondType.SINGLE)
    rw.AddBond(p, o1, Chem.BondType.DOUBLE)
    rw.AddBond(p, o2, Chem.BondType.SINGLE)
    rw.AddBond(p, o3, Chem.BondType.SINGLE)
    return {atom_idx, p, o1, o2, o3}

def _attach_sugar_tag(rw, atom_idx):
    c1 = rw.AddAtom(Chem.Atom(6))
    c2 = rw.AddAtom(Chem.Atom(6))
    c3 = rw.AddAtom(Chem.Atom(6))
    o2 = rw.AddAtom(Chem.Atom(8))
    o3 = rw.AddAtom(Chem.Atom(8))
    rw.AddBond(atom_idx, c1, Chem.BondType.SINGLE)
    rw.AddBond(c1, c2, Chem.BondType.SINGLE)
    rw.AddBond(c2, c3, Chem.BondType.SINGLE)
    rw.AddBond(c2, o2, Chem.BondType.SINGLE)
    rw.AddBond(c3, o3, Chem.BondType.SINGLE)
    return {atom_idx, c1, c2, c3, o2, o3}

def _attach_fatty_chain(rw, atom_idx, chain_len=10):
    prev = atom_idx
    atoms = [atom_idx]

    for _ in range(chain_len):
        c = rw.AddAtom(Chem.Atom(6))
        rw.AddBond(prev, c, Chem.BondType.SINGLE)
        atoms.append(c)
        prev = c

    return set(atoms[:5])

def _attach_ub_tag(rw, atom_idx):
    c1 = rw.AddAtom(Chem.Atom(6))
    o1 = rw.AddAtom(Chem.Atom(8))
    n2 = rw.AddAtom(Chem.Atom(7))
    c2 = rw.AddAtom(Chem.Atom(6))
    c3 = rw.AddAtom(Chem.Atom(6))
    o2 = rw.AddAtom(Chem.Atom(8))
    n3 = rw.AddAtom(Chem.Atom(7))

    rw.AddBond(atom_idx, c1, Chem.BondType.SINGLE)
    rw.AddBond(c1, o1, Chem.BondType.DOUBLE)
    rw.AddBond(c1, n2, Chem.BondType.SINGLE)
    rw.AddBond(n2, c2, Chem.BondType.SINGLE)
    rw.AddBond(c2, c3, Chem.BondType.SINGLE)
    rw.AddBond(c3, o2, Chem.BondType.DOUBLE)
    rw.AddBond(c3, n3, Chem.BondType.SINGLE)

    return {atom_idx, c1, o1, n2, c2, c3, o2, n3}

def _add_metal_complex(rw, metal_atomic_num, charge, donor_atoms, max_bonds):
    metal = Chem.Atom(metal_atomic_num)
    metal.SetFormalCharge(charge)
    m = rw.AddAtom(metal)

    donors = list(dict.fromkeys(donor_atoms))[:max_bonds]

    for d in donors:
        try:
            rw.AddBond(d, m, Chem.BondType.DATIVE)
        except Exception:
            rw.AddBond(d, m, Chem.BondType.SINGLE)

    return set([m] + donors)

def _remove_phosphate_group(mol):
    patt = Chem.MolFromSmarts("[O:1]-[P:2](=[O:3])([O:4])[O:5]")
    matches = mol.GetSubstructMatches(patt)

    if not matches:
        return None, [], "No phosphate group found to remove."

    anchor, p, o1, o2, o3 = [int(x) for x in random.choice(matches)]

    rw = Chem.RWMol(mol)
    for idx in sorted([p, o1, o2, o3], reverse=True):
        rw.RemoveAtom(idx)

    new_mol, err = _safe_sanitize(rw.GetMol())
    if err:
        return None, [], err

    return new_mol, [anchor], None

def _hydroxylate(mol):
    patt = Chem.MolFromSmarts("[CH,CH2,CH3]")
    matches = mol.GetSubstructMatches(patt)

    if not matches:
        return None, [], "No suitable carbon found for hydroxylation."

    c = int(random.choice(matches)[0])
    rw = Chem.RWMol(mol)
    o = rw.AddAtom(Chem.Atom(8))
    rw.AddBond(c, o, Chem.BondType.SINGLE)

    new_mol, err = _safe_sanitize(rw.GetMol())
    if err:
        return None, [], err

    return new_mol, [c, o], None

def _adenylate_carboxylate(mol):
    patt = Chem.MolFromSmarts("[O;H1]-C(=O)")
    matches = mol.GetSubstructMatches(patt)

    if not matches:
        return None, [], "No carboxyl oxygen found for adenylation."

    o_idx = int(random.choice(matches)[0])

    rw = Chem.RWMol(mol)
    p = rw.AddAtom(Chem.Atom(15))
    o1 = rw.AddAtom(Chem.Atom(8))
    o2 = rw.AddAtom(Chem.Atom(8))
    o3 = rw.AddAtom(Chem.Atom(8))
    c_tag = rw.AddAtom(Chem.Atom(6))
    n_tag = rw.AddAtom(Chem.Atom(7))

    rw.AddBond(o_idx, p, Chem.BondType.SINGLE)
    rw.AddBond(p, o1, Chem.BondType.DOUBLE)
    rw.AddBond(p, o2, Chem.BondType.SINGLE)
    rw.AddBond(p, o3, Chem.BondType.SINGLE)
    rw.AddBond(o3, c_tag, Chem.BondType.SINGLE)
    rw.AddBond(c_tag, n_tag, Chem.BondType.SINGLE)

    new_mol, err = _safe_sanitize(rw.GetMol())
    if err:
        return None, [], err

    return new_mol, [o_idx, p, o1, o2, o3, c_tag, n_tag], None


# ============================================================
# APPLY MOD
# ============================================================

def apply_mod(mol, mod_key, starter):
    mol = Chem.Mol(mol)

    if mod_key == "dephosphorylation":
        return _remove_phosphate_group(mol)

    if mod_key == "hydroxylation":
        return _hydroxylate(mol)

    if mod_key == "adenylation":
        return _adenylate_carboxylate(mol)

    if mod_key == "disulfide":
        s_atoms = _all_match_atoms(mol, starter.get("site_smarts", {}).get("disulfide"))
        if len(s_atoms) < 2:
            return None, [], "Need two thiol sulfurs for disulfide formation."

        a, b = random.sample(s_atoms, 2)
        rw = Chem.RWMol(mol)
        rw.AddBond(a, b, Chem.BondType.SINGLE)

        new_mol, err = _safe_sanitize(rw.GetMol())
        if err:
            return None, [], err

        return new_mol, [a, b], None

    smarts = starter.get("site_smarts", {}).get(mod_key)
    atom_idx = _first_match_atom(mol, smarts)

    if atom_idx is None:
        return None, [], f"{mod_key} is not possible on {starter['name']}."

    rw = Chem.RWMol(mol)
    highlight = set()

    try:
        atom = rw.GetAtomWithIdx(atom_idx)

        if mod_key == "methylation":
            if atom.GetAtomicNum() != 7:
                return None, [], "Methylation requires nitrogen."
            highlight |= _attach_methyl(rw, atom_idx)

        elif mod_key == "acetylation":
            if atom.GetAtomicNum() != 7:
                return None, [], "Acetylation requires nitrogen."
            highlight |= _attach_acetyl(rw, atom_idx)

        elif mod_key == "phosphorylation":
            if atom.GetAtomicNum() != 8:
                return None, [], "Phosphorylation requires oxygen."
            highlight |= _attach_phosphate(rw, atom_idx)

        elif mod_key == "glycosylation":
            if atom.GetAtomicNum() != 8:
                return None, [], "Glycosylation requires oxygen."
            highlight |= _attach_sugar_tag(rw, atom_idx)

        elif mod_key == "lipidation":
            if atom.GetAtomicNum() not in (7, 8, 16):
                return None, [], "Lipidation requires N/O/S."
            highlight |= _attach_fatty_chain(rw, atom_idx)

        elif mod_key == "ubiquitination":
            if atom.GetAtomicNum() != 7:
                return None, [], "Ubiquitination requires nitrogen."
            highlight |= _attach_ub_tag(rw, atom_idx)

        elif mod_key == "metal_cu":
            donors = _all_match_atoms(mol, "[N,O,S,n]")
            if len(donors) < 2:
                return None, [], "Need at least two donor atoms."
            highlight |= _add_metal_complex(rw, 29, +2, donors, 3)

        elif mod_key == "metal_fe2":
            donors = _all_match_atoms(mol, "[N,O,S,n]")
            if len(donors) < 2:
                return None, [], "Need at least two donor atoms."
            highlight |= _add_metal_complex(rw, 26, +2, donors, 4)

        elif mod_key == "metal_fe3":
            donors = _all_match_atoms(mol, "[N,O,S,n]")
            if len(donors) < 2:
                return None, [], "Need at least two donor atoms."
            highlight |= _add_metal_complex(rw, 26, +3, donors, 4)

        elif mod_key == "protonate":
            if atom.GetAtomicNum() != 7:
                return None, [], "Protonation requires nitrogen."
            atom.SetFormalCharge(+1)
            highlight.add(atom_idx)

        elif mod_key == "deprotonate":
            if atom.GetAtomicNum() != 8:
                return None, [], "Deprotonation requires oxygen."
            atom.SetFormalCharge(-1)
            atom.SetNumExplicitHs(0)
            highlight.add(atom_idx)

        else:
            return None, [], "Unknown modification."

        new_mol, err = _safe_sanitize(rw.GetMol())
        if err:
            return None, [], err

        return new_mol, list(highlight), None

    except Exception as e:
        return None, [], str(e)


# ============================================================
# ROUND GENERATION
# ============================================================

def _mod_is_feasible(starter, mod_key):
    mol = Chem.MolFromSmiles(starter["smiles"])
    if mol is None:
        return False

    product, _, err = apply_mod(mol, mod_key, starter)
    return product is not None and err is None

def _feasible_mods(starter):
    return [key for key, _ in MODS if _mod_is_feasible(starter, key)]

def pick_options(starter, correct_mod):
    feasible = _feasible_mods(starter)

    distractors = [m for m in feasible if m != correct_mod]
    if len(distractors) < 2:
        distractors = [m for m, _ in MODS if m != correct_mod]

    opts = [correct_mod] + random.sample(distractors, 2)
    random.shuffle(opts)
    return opts

def make_round(gen_dir):
    os.makedirs(gen_dir, exist_ok=True)
    cleanup_old_images(gen_dir, keep=160)

    for _ in range(200):
        starter = random.choice(STARTERS)
        feasible = _feasible_mods(starter)

        possible_goals = [g for g in GOALS if g[2] in feasible]
        if not possible_goals:
            continue

        goal_id, goal_text, correct_mod = random.choice(possible_goals)

        mol = Chem.MolFromSmiles(starter["smiles"])
        if mol is None:
            continue

        starter_img = f"rxn_{uuid.uuid4().hex}_start.png"
        starter_path = os.path.join(gen_dir, starter_img)

        if not _render_png(mol, starter_path):
            continue

        return {
            "starter_id": starter["id"],
            "starter_name": starter["name"],
            "starter_category": starter["category"],
            "goal_id": goal_id,
            "goal_text": goal_text,
            "correct_mod": correct_mod,
            "options": pick_options(starter, correct_mod),
            "starter_img": starter_img,
        }

    # fallback
    starter = next(s for s in STARTERS if s["id"] == "serine")
    mol = Chem.MolFromSmiles(starter["smiles"])
    starter_img = f"rxn_{uuid.uuid4().hex}_start.png"
    starter_path = os.path.join(gen_dir, starter_img)
    _render_png(mol, starter_path)

    return {
        "starter_id": starter["id"],
        "starter_name": starter["name"],
        "starter_category": starter["category"],
        "goal_id": "fallback",
        "goal_text": "Goal: Add negative charge / increase polarity",
        "correct_mod": "phosphorylation",
        "options": ["phosphorylation", "acetylation", "methylation"],
        "starter_img": starter_img,
    }

def render_product(gen_dir, starter_id, mod_key):
    starter = next((s for s in STARTERS if s["id"] == starter_id), None)
    if not starter:
        return None, None, "Starter not found."

    mol = Chem.MolFromSmiles(starter["smiles"])
    if mol is None:
        return None, None, "Starter SMILES invalid."

    new_mol, highlight, err = apply_mod(mol, mod_key, starter)
    if err or new_mol is None:
        return None, None, err or "Could not generate product."

    product_img = f"rxn_{uuid.uuid4().hex}_prod.png"
    product_path = os.path.join(gen_dir, product_img)

    if not _render_png(new_mol, product_path, highlight_atoms=highlight):
        return None, None, "Could not draw product image."

    formula = rdMolDescriptors.CalcMolFormula(new_mol)
    return product_img, formula, None